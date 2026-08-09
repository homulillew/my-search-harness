"""Typed command façade for the V1 core research loop."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from typing import TypeAlias

from my_search_harness.domain.model import (
    ArtifactKind,
    CompletionCheck,
    CompletionPassBasis,
    CompletionVerdict,
    ContractRevision,
    Deliverable,
    InvestigationGap,
    LandscapeFinding,
    LifecycleMode,
    LiteratureSource,
    Paper,
    PaperAnalysis,
    PaperSource,
    ResearchContract,
    ResearchRequirement,
    ResearchRun,
    VersionedResearchContract,
    utc_now,
)
from my_search_harness.domain.paper_identity import (
    PaperIdentityKey,
    normalize_arxiv_id,
    normalize_doi,
    paper_identity_keys,
)

from .paper_search import PaperSearchHit
from .persistence import JsonResearchRunRepository, RevisionConflictError


class CommandRejectedError(RuntimeError):
    """A command is invalid for the current authoritative state."""


class CompletionSubmissionConflictError(RuntimeError):
    """A retry conflicts with an already completed CompletionCheck."""


@dataclass(slots=True, frozen=True, kw_only=True)
class CreateRunRequest:
    mission: str
    requirements: tuple[str, ...]
    scope: str
    deliverable_description: str
    required_artifacts: frozenset[ArtifactKind] = field(default_factory=frozenset)


@dataclass(slots=True, frozen=True, kw_only=True)
class CreateRunResult:
    run_id: str
    state_revision: int
    requirement_refs: tuple[str, ...]


@dataclass(slots=True, frozen=True, kw_only=True)
class RetainPapersResult:
    state_revision: int
    paper_refs: tuple[str, ...]


@dataclass(slots=True, frozen=True, kw_only=True)
class PutPaperAnalysis:
    paper_ref: str
    analysis: PaperAnalysis


@dataclass(slots=True, frozen=True, kw_only=True)
class PutLandscapeFinding:
    statement: str
    approach_refs: frozenset[str] = field(default_factory=frozenset)
    sources: frozenset[LiteratureSource] = field(default_factory=frozenset)


ResearchPut: TypeAlias = PutPaperAnalysis | PutLandscapeFinding


@dataclass(slots=True, frozen=True, kw_only=True)
class ResearchMutationBatch:
    puts: tuple[ResearchPut, ...]


@dataclass(slots=True, frozen=True, kw_only=True)
class ResearchMutationResult:
    state_revision: int
    finding_refs: tuple[str, ...]


@dataclass(slots=True, frozen=True, kw_only=True)
class RequestCompletionCheckResult:
    state_revision: int
    completion_check_ref: str


@dataclass(slots=True, frozen=True, kw_only=True)
class NewBlockingGap:
    description: str
    requirement_refs: frozenset[str] = field(default_factory=frozenset)
    approach_refs: frozenset[str] = field(default_factory=frozenset)


@dataclass(slots=True, frozen=True, kw_only=True)
class ReopenBlockingGap:
    gap_ref: str


BlockingGapSpec: TypeAlias = NewBlockingGap | ReopenBlockingGap


@dataclass(slots=True, frozen=True, kw_only=True)
class CompletionSubmissionResult:
    state_revision: int
    completion_check_ref: str
    verdict: CompletionVerdict
    reasons: tuple[str, ...]
    blocking_gap_refs: frozenset[str]


class ResearchCommands:
    """Thin command boundary over the authoritative ResearchRun repository."""

    def __init__(self, repository: JsonResearchRunRepository) -> None:
        self._repository = repository

    def create_run(self, request: CreateRunRequest) -> CreateRunResult:
        self._validate_create_request(request)
        requirements = tuple(
            ResearchRequirement(statement=statement)
            for statement in request.requirements
        )
        contract = ResearchContract(
            mission=request.mission,
            requirements={requirement.id: requirement for requirement in requirements},
            scope=request.scope,
            deliverable=Deliverable(
                description=request.deliverable_description,
                required_artifacts=set(request.required_artifacts),
            ),
        )
        run = ResearchRun(
            contract=VersionedResearchContract(
                current_revision=1,
                revisions=[
                    ContractRevision(
                        revision=1,
                        contract=contract,
                        reason="Initial contract",
                    )
                ],
            )
        )
        self._repository.create(run)
        return CreateRunResult(
            run_id=run.id,
            state_revision=run.state_revision,
            requirement_refs=tuple(requirement.id for requirement in requirements),
        )

    def retain_papers(
        self,
        run_id: str,
        expected_revision: int,
        hits: tuple[PaperSearchHit, ...],
    ) -> RetainPapersResult:
        current = self._load_expected(run_id, expected_revision)
        self._require_lifecycle(current, LifecycleMode.RESEARCH, "retain_papers")
        if not isinstance(hits, tuple) or not hits:
            raise CommandRejectedError("retain_papers requires at least one search hit")

        proposed = deepcopy(current)
        identity_index = self._paper_identity_index(proposed)
        paper_refs: list[str] = []

        for hit in hits:
            source = self._source_from_hit(hit)
            incoming_keys = paper_identity_keys(source)
            self._require_nonempty_identity_values(incoming_keys)
            matching_refs = {
                identity_index[key] for key in incoming_keys if key in identity_index
            }
            if len(matching_refs) > 1:
                raise CommandRejectedError(
                    "incoming paper identities resolve to multiple persistent papers"
                )

            if matching_refs:
                paper_ref = next(iter(matching_refs))
                paper = proposed.papers[paper_ref]
                self._enrich_paper_identity(paper, source)
            else:
                paper = Paper(source=source)
                proposed.papers[paper.id] = paper
                paper_ref = paper.id

            for key in paper_identity_keys(paper.source):
                existing_ref = identity_index.get(key)
                if existing_ref is not None and existing_ref != paper_ref:
                    raise CommandRejectedError(
                        "paper identity enrichment conflicts with another paper"
                    )
                identity_index[key] = paper_ref
            paper_refs.append(paper_ref)

        state_revision = self._commit(current, proposed, expected_revision)
        return RetainPapersResult(
            state_revision=state_revision,
            paper_refs=tuple(paper_refs),
        )

    def apply_research_mutation(
        self,
        run_id: str,
        expected_revision: int,
        batch: ResearchMutationBatch,
    ) -> ResearchMutationResult:
        current = self._load_expected(run_id, expected_revision)
        self._require_lifecycle(
            current, LifecycleMode.RESEARCH, "apply_research_mutation"
        )
        if not isinstance(batch, ResearchMutationBatch) or not batch.puts:
            raise CommandRejectedError("research mutation batch must not be empty")

        proposed = deepcopy(current)
        finding_refs: list[str] = []
        for mutation in batch.puts:
            if isinstance(mutation, PutPaperAnalysis):
                paper = proposed.papers.get(mutation.paper_ref)
                if paper is None:
                    raise CommandRejectedError(
                        f"paper {mutation.paper_ref!r} does not exist"
                    )
                if not isinstance(mutation.analysis, PaperAnalysis):
                    raise CommandRejectedError("analysis must be a PaperAnalysis")
                paper.analysis = deepcopy(mutation.analysis)
                continue

            if isinstance(mutation, PutLandscapeFinding):
                self._validate_finding_refs(proposed, mutation)
                finding = LandscapeFinding(
                    statement=mutation.statement,
                    approach_refs=set(mutation.approach_refs),
                    sources=set(mutation.sources),
                )
                proposed.literature_landscape.findings[finding.id] = finding
                finding_refs.append(finding.id)
                continue

            raise CommandRejectedError("unsupported research mutation type")

        state_revision = self._commit(current, proposed, expected_revision)
        return ResearchMutationResult(
            state_revision=state_revision,
            finding_refs=tuple(finding_refs),
        )

    def request_completion_check(
        self,
        run_id: str,
        expected_revision: int,
        requester_rationale: str,
    ) -> RequestCompletionCheckResult:
        current = self._load_expected(run_id, expected_revision)
        self._require_lifecycle(
            current, LifecycleMode.RESEARCH, "request_completion_check"
        )
        if not isinstance(requester_rationale, str):
            raise CommandRejectedError("requester_rationale must be a string")

        proposed = deepcopy(current)
        resulting_revision = current.state_revision + 1
        check = CompletionCheck(
            basis_revision=resulting_revision,
            basis_contract_revision=proposed.contract.current_revision,
            requester_rationale=requester_rationale,
        )
        proposed.completion_checks[check.id] = check
        proposed.lifecycle = LifecycleMode.COMPLETION_CHECK
        state_revision = self._commit(current, proposed, expected_revision)
        return RequestCompletionCheckResult(
            state_revision=state_revision,
            completion_check_ref=check.id,
        )

    def submit_completion_check(
        self,
        run_id: str,
        expected_revision: int,
        completion_check_ref: str,
        verdict: CompletionVerdict,
        reasons: tuple[str, ...],
        blocking_gaps: tuple[BlockingGapSpec, ...] = (),
    ) -> CompletionSubmissionResult:
        self._validate_completion_payload_types(verdict, reasons, blocking_gaps)
        current = self._repository.load(run_id)
        check = current.completion_checks.get(completion_check_ref)
        if check is None:
            raise CommandRejectedError(
                f"completion check {completion_check_ref!r} does not exist"
            )

        if check.completed_at is not None:
            if check.verdict is verdict and check.reasons == reasons:
                if verdict is not CompletionVerdict.CONTINUE and blocking_gaps:
                    raise CommandRejectedError(
                        f"{verdict.value} must not include blocking gap specs"
                    )
                return self._completion_result(current, check)
            raise CompletionSubmissionConflictError(
                f"completion check {completion_check_ref!r} has a conflicting result"
            )

        if current.state_revision != expected_revision:
            raise RevisionConflictError(
                f"expected revision {expected_revision}, found "
                f"{current.state_revision}"
            )
        self._require_lifecycle(
            current, LifecycleMode.COMPLETION_CHECK, "submit_completion_check"
        )

        pending_refs = {
            item.id
            for item in current.completion_checks.values()
            if item.completed_at is None
        }
        if pending_refs != {completion_check_ref}:
            raise CommandRejectedError(
                "submit_completion_check must target the current pending check"
            )
        self._validate_blocking_gap_rules(verdict, blocking_gaps)

        proposed = deepcopy(current)
        proposed_check = proposed.completion_checks[completion_check_ref]
        blocking_refs = self._apply_blocking_gaps(proposed, verdict, blocking_gaps)
        proposed_check.verdict = verdict
        proposed_check.reasons = reasons
        proposed_check.blocking_gap_refs = blocking_refs
        proposed_check.completed_at = utc_now()

        if verdict is CompletionVerdict.PASS:
            proposed.lifecycle = LifecycleMode.DELIVERY
            proposed.delivery_basis = CompletionPassBasis(
                completion_check_ref=completion_check_ref
            )
        else:
            proposed.lifecycle = LifecycleMode.RESEARCH
            proposed.delivery_basis = None

        self._commit(current, proposed, expected_revision)
        return self._completion_result(proposed, proposed_check)

    def _load_expected(self, run_id: str, expected_revision: int) -> ResearchRun:
        run = self._repository.load(run_id)
        if run.state_revision != expected_revision:
            raise RevisionConflictError(
                f"expected revision {expected_revision}, found {run.state_revision}"
            )
        return run

    def _commit(
        self,
        current: ResearchRun,
        proposed: ResearchRun,
        expected_revision: int,
    ) -> int:
        proposed.state_revision = current.state_revision + 1
        self._repository.save(proposed, expected_revision)
        return proposed.state_revision

    @staticmethod
    def _require_lifecycle(
        run: ResearchRun, required: LifecycleMode, command_name: str
    ) -> None:
        if run.lifecycle is not required:
            raise CommandRejectedError(
                f"{command_name} requires {required.value}; found {run.lifecycle.value}"
            )

    @staticmethod
    def _validate_create_request(request: CreateRunRequest) -> None:
        if not isinstance(request, CreateRunRequest):
            raise CommandRejectedError("create_run requires a CreateRunRequest")
        for name, value in (
            ("mission", request.mission),
            ("scope", request.scope),
            ("deliverable_description", request.deliverable_description),
        ):
            if not isinstance(value, str):
                raise CommandRejectedError(f"{name} must be a string")
        if not isinstance(request.requirements, tuple) or not all(
            isinstance(statement, str) for statement in request.requirements
        ):
            raise CommandRejectedError("requirements must be a tuple of strings")
        if not isinstance(request.required_artifacts, frozenset) or not all(
            isinstance(artifact, ArtifactKind)
            for artifact in request.required_artifacts
        ):
            raise CommandRejectedError(
                "required_artifacts must be a frozenset of ArtifactKind"
            )

    @staticmethod
    def _source_from_hit(hit: PaperSearchHit) -> PaperSource:
        if not isinstance(hit, PaperSearchHit):
            raise CommandRejectedError("hits must contain PaperSearchHit values")
        if not isinstance(hit.title, str):
            raise CommandRejectedError("paper title must be a string")
        if not isinstance(hit.authors, tuple) or not all(
            isinstance(author, str) for author in hit.authors
        ):
            raise CommandRejectedError("paper authors must be a tuple of strings")
        if hit.publication_year is not None and (
            not isinstance(hit.publication_year, int)
            or isinstance(hit.publication_year, bool)
        ):
            raise CommandRejectedError("publication_year must be an integer or None")
        for name, value in (
            ("doi", hit.doi),
            ("arxiv_id", hit.arxiv_id),
            ("canonical_url", hit.canonical_url),
        ):
            if value is not None and not isinstance(value, str):
                raise CommandRejectedError(f"{name} must be a string or None")
        if not isinstance(hit.other_identifiers, Mapping) or not all(
            isinstance(kind, str) and isinstance(value, str)
            for kind, value in hit.other_identifiers.items()
        ):
            raise CommandRejectedError(
                "other_identifiers must be a string-to-string mapping"
            )
        return PaperSource(
            title=hit.title,
            authors=hit.authors,
            publication_year=hit.publication_year,
            doi=hit.doi,
            arxiv_id=hit.arxiv_id,
            canonical_url=(
                None if hit.canonical_url is None else hit.canonical_url.strip()
            ),
            other_identifiers=dict(hit.other_identifiers),
        )

    @staticmethod
    def _require_nonempty_identity_values(
        identity_keys: tuple[PaperIdentityKey, ...]
    ) -> None:
        if any(not value for _, value in identity_keys):
            raise CommandRejectedError("stable paper identifiers must not be empty")

    @staticmethod
    def _paper_identity_index(
        run: ResearchRun,
    ) -> dict[PaperIdentityKey, str]:
        index: dict[PaperIdentityKey, str] = {}
        for paper_ref, paper in run.papers.items():
            for key in paper_identity_keys(paper.source):
                index[key] = paper_ref
        return index

    @staticmethod
    def _enrich_paper_identity(paper: Paper, incoming: PaperSource) -> None:
        if incoming.doi is not None:
            if paper.source.doi is None:
                paper.source.doi = incoming.doi
            elif normalize_doi(paper.source.doi) != normalize_doi(incoming.doi):
                raise CommandRejectedError(f"paper {paper.id!r} has a conflicting DOI")

        if incoming.arxiv_id is not None:
            if paper.source.arxiv_id is None:
                paper.source.arxiv_id = incoming.arxiv_id
            elif normalize_arxiv_id(paper.source.arxiv_id) != normalize_arxiv_id(
                incoming.arxiv_id
            ):
                raise CommandRejectedError(
                    f"paper {paper.id!r} has a conflicting arXiv ID"
                )

        if paper.source.canonical_url is None and incoming.canonical_url is not None:
            paper.source.canonical_url = incoming.canonical_url

        for kind, value in incoming.other_identifiers.items():
            paper.source.other_identifiers.setdefault(kind, value)

    @staticmethod
    def _validate_finding_refs(run: ResearchRun, mutation: PutLandscapeFinding) -> None:
        if not isinstance(mutation.statement, str):
            raise CommandRejectedError("finding statement must be a string")
        if not isinstance(mutation.approach_refs, frozenset) or not all(
            isinstance(approach_ref, str) for approach_ref in mutation.approach_refs
        ):
            raise CommandRejectedError(
                "finding approach_refs must be a frozenset of references"
            )
        if not isinstance(mutation.sources, frozenset) or not all(
            isinstance(source, LiteratureSource) for source in mutation.sources
        ):
            raise CommandRejectedError(
                "finding sources must be a frozenset of LiteratureSource"
            )
        missing_approaches = set(mutation.approach_refs) - set(
            run.literature_landscape.approach_families
        )
        if missing_approaches:
            raise CommandRejectedError(
                f"finding has dangling approach refs: {sorted(missing_approaches)!r}"
            )
        missing_papers = {
            source.paper_ref
            for source in mutation.sources
            if source.paper_ref not in run.papers
        }
        if missing_papers:
            raise CommandRejectedError(
                f"finding has dangling paper refs: {sorted(missing_papers)!r}"
            )

    @staticmethod
    def _validate_completion_payload_types(
        verdict: CompletionVerdict,
        reasons: tuple[str, ...],
        blocking_gaps: tuple[BlockingGapSpec, ...],
    ) -> None:
        if not isinstance(verdict, CompletionVerdict):
            raise CommandRejectedError("verdict must be a CompletionVerdict")
        if (
            not isinstance(reasons, tuple)
            or not reasons
            or not all(isinstance(reason, str) for reason in reasons)
        ):
            raise CommandRejectedError("reasons must be a non-empty tuple of strings")
        if not isinstance(blocking_gaps, tuple):
            raise CommandRejectedError("blocking_gaps must be a tuple")

    @staticmethod
    def _validate_blocking_gap_rules(
        verdict: CompletionVerdict,
        blocking_gaps: tuple[BlockingGapSpec, ...],
    ) -> None:
        if verdict is CompletionVerdict.CONTINUE and not blocking_gaps:
            raise CommandRejectedError("CONTINUE requires at least one blocking gap")
        if verdict is not CompletionVerdict.CONTINUE and blocking_gaps:
            raise CommandRejectedError(
                f"{verdict.value} must not include blocking gap specs"
            )

    @staticmethod
    def _apply_blocking_gaps(
        run: ResearchRun,
        verdict: CompletionVerdict,
        blocking_gaps: tuple[BlockingGapSpec, ...],
    ) -> set[str]:
        if verdict is not CompletionVerdict.CONTINUE:
            return set()

        current_contract = next(
            revision.contract
            for revision in run.contract.revisions
            if revision.revision == run.contract.current_revision
        )
        requirement_refs = set(current_contract.requirements)
        approach_refs = set(run.literature_landscape.approach_families)
        result: set[str] = set()

        for spec in blocking_gaps:
            if isinstance(spec, NewBlockingGap):
                if not isinstance(spec.description, str):
                    raise CommandRejectedError("gap description must be a string")
                if not isinstance(spec.requirement_refs, frozenset) or not all(
                    isinstance(requirement_ref, str)
                    for requirement_ref in spec.requirement_refs
                ):
                    raise CommandRejectedError(
                        "gap requirement_refs must be a frozenset of references"
                    )
                if not isinstance(spec.approach_refs, frozenset) or not all(
                    isinstance(approach_ref, str) for approach_ref in spec.approach_refs
                ):
                    raise CommandRejectedError(
                        "gap approach_refs must be a frozenset of references"
                    )
                missing_requirements = set(spec.requirement_refs) - requirement_refs
                missing_approaches = set(spec.approach_refs) - approach_refs
                if missing_requirements:
                    raise CommandRejectedError(
                        "new gap has dangling requirement refs: "
                        f"{sorted(missing_requirements)!r}"
                    )
                if missing_approaches:
                    raise CommandRejectedError(
                        "new gap has dangling approach refs: "
                        f"{sorted(missing_approaches)!r}"
                    )
                gap = InvestigationGap(
                    description=spec.description,
                    requirement_refs=set(spec.requirement_refs),
                    approach_refs=set(spec.approach_refs),
                    resolution=None,
                )
                run.investigation_gaps[gap.id] = gap
                result.add(gap.id)
                continue

            if isinstance(spec, ReopenBlockingGap):
                if not isinstance(spec.gap_ref, str):
                    raise CommandRejectedError("gap_ref must be a string")
                reopened_gap = run.investigation_gaps.get(spec.gap_ref)
                if reopened_gap is None:
                    raise CommandRejectedError(f"gap {spec.gap_ref!r} does not exist")
                reopened_gap.resolution = None
                result.add(reopened_gap.id)
                continue

            raise CommandRejectedError("unsupported blocking gap spec")

        return result

    @staticmethod
    def _completion_result(
        run: ResearchRun, check: CompletionCheck
    ) -> CompletionSubmissionResult:
        if check.verdict is None:
            raise AssertionError("completion result requires a completed check")
        return CompletionSubmissionResult(
            state_revision=run.state_revision,
            completion_check_ref=check.id,
            verdict=check.verdict,
            reasons=check.reasons,
            blocking_gap_refs=frozenset(check.blocking_gap_refs),
        )
