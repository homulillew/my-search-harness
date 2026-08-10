"""Deterministic full-chain acceptance test for the local V1 runtime."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from my_search_harness.domain import (
    ArtifactKind,
    CompletionVerdict,
    LifecycleMode,
    LiteratureSource,
    PaperAnalysis,
    PaperSource,
    RunOutcome,
    SourceLocator,
    SourceRelation,
)
from my_search_harness.runtime import (
    CitationReference,
    CompletionCheckDecision,
    CreateRunRequest,
    EditorialReview,
    IntegrityDisposition,
    JsonResearchRunRepository,
    LocalAuditLog,
    LocalV1Runtime,
    NarrativePlan,
    NarrativeSection,
    PaperSearchConfigurationError,
    PaperSearchHit,
    PublishedReportPipelineResult,
    PutPaperAnalysis,
    ReportManuscript,
    ResearchIntegrityReview,
    ResearchMutationBatch,
    SourceContent,
    SourceOutline,
    SourceOutlineEntry,
    WikiDraft,
    WikiPageDraft,
    WikiProvenanceRef,
    WikiSemanticReview,
)


class FakeDeepXivSearch:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, *, limit: int) -> tuple[PaperSearchHit, ...]:
        self.calls.append((query, limit))
        return (
            PaperSearchHit(
                title="A Primary Study of Bounded Search",
                authors=("Ada Author",),
                publication_year=2026,
                arxiv_id="2608.01234",
                canonical_url="https://arxiv.org/abs/2608.01234",
                abstract="Ephemeral provider abstract",
                provider_summary="Ephemeral provider summary",
                provider_score=0.99,
                citation_count=42,
            ),
        )


class FakeDeepXivSource:
    def __init__(self) -> None:
        self.inspect_calls = 0
        self.read_calls = 0

    def validate_inspect(self, source: PaperSource) -> None:
        if source.arxiv_id is None:
            raise AssertionError("fixture expects arXiv identity")

    def validate_read(
        self,
        source: PaperSource,
        locator: SourceLocator | None,
    ) -> None:
        if source.arxiv_id is None:
            raise AssertionError("fixture expects arXiv identity")

    def inspect_source(self, paper_ref: str, source: PaperSource) -> SourceOutline:
        self.inspect_calls += 1
        return SourceOutline(
            paper_ref=paper_ref,
            sections=(
                SourceOutlineEntry(
                    title="Results",
                    locator=SourceLocator(kind="section", value="Results"),
                ),
            ),
        )

    def read_source(
        self,
        paper_ref: str,
        source: PaperSource,
        locator: SourceLocator | None,
    ) -> SourceContent:
        self.read_calls += 1
        return SourceContent(
            paper_ref=paper_ref,
            locator=locator,
            content="The primary paper reports a bounded-search improvement.",
        )


class PassingChecker:
    def __init__(self) -> None:
        self.has_broad_search: bool | None = None
        self.has_research_mutation: bool | None = None

    def evaluate(self, view, evidence):
        self.has_broad_search = hasattr(evidence, "search_papers")
        self.has_research_mutation = hasattr(evidence, "apply_research_mutation")
        evidence.inspect((view.representative_paper_refs[0],))
        return CompletionCheckDecision(
            verdict=CompletionVerdict.PASS,
            reasons=("The accepted landscape satisfies the frozen contract",),
        )


class FreshCheckerFactory:
    def __init__(self) -> None:
        self.instances: list[PassingChecker] = []

    def create(self):
        checker = PassingChecker()
        self.instances.append(checker)
        return checker


class E2EPlanner:
    def __init__(self, finding_ref: str) -> None:
        self.finding_ref = finding_ref
        self.writing_guideline: str | None = None

    def plan(self, view, writing_guideline):
        self.writing_guideline = writing_guideline
        return NarrativePlan(
            audience="Technical readers",
            reader_takeaway="Understand the accepted result and its boundary",
            sections=(
                NarrativeSection(
                    title="Result",
                    purpose="Explain the accepted landscape finding",
                    research_refs=(self.finding_ref,),
                ),
            ),
        )


class E2EComposer:
    def __init__(self, paper_ref: str) -> None:
        self.paper_ref = paper_ref

    def compose(self, view, plan, writing_guideline, evidence):
        return ReportManuscript(
            markdown=(
                "# Bounded Search\n\n"
                "The accepted study reports an improvement {{cite:primary}}."
            ),
            citations=(
                CitationReference(
                    citation_id="primary",
                    paper_ref=self.paper_ref,
                    locator=SourceLocator(kind="section", value="Results"),
                ),
            ),
        )


class PassthroughIntegrator:
    def integrate(self, view, plan, manuscript, writing_guideline, evidence):
        return manuscript


class PassingEditor:
    def review(self, deliverable, plan, writing_guideline, manuscript):
        return EditorialReview()


class FreshEditorFactory:
    def __init__(self) -> None:
        self.create_count = 0

    def create(self):
        self.create_count += 1
        return PassingEditor()


class PassthroughReviser:
    def revise(
        self,
        view,
        plan,
        manuscript,
        review,
        writing_guideline,
        evidence,
    ):
        return manuscript


class PassingIntegrityReviewer:
    def review(self, view, manuscript, evidence):
        return ResearchIntegrityReview(disposition=IntegrityDisposition.PASS)


class E2EWikiBuilder:
    def build(self, projection):
        run = projection.runs[0]
        finding = run.findings[0]
        paper = run.papers[0]
        return WikiDraft(
            pages=(
                WikiPageDraft(
                    slug="bounded-search",
                    title="Bounded Search",
                    markdown=(
                        "# Bounded Search\n\n"
                        "Accepted research reports an improvement; future runs "
                        "must return to the primary paper."
                    ),
                    contributing_refs=(
                        WikiProvenanceRef(
                            run_id=run.run_id,
                            research_ref=finding.ref,
                        ),
                        WikiProvenanceRef(
                            run_id=run.run_id,
                            research_ref=paper.ref,
                        ),
                    ),
                ),
            ),
        )


class PassingWikiValidator:
    def validate(self, projection, draft):
        return WikiSemanticReview(approved=True)


class V1EndToEndTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.workspace = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_complete_v1_chain(self) -> None:
        search_provider = FakeDeepXivSearch()
        source_provider = FakeDeepXivSource()
        runtime = LocalV1Runtime(
            self.workspace,
            paper_search_provider=search_provider,
            source_access_provider=source_provider,
        )
        repository = JsonResearchRunRepository(self.workspace / "runs")

        created = runtime.researcher.create_run(
            CreateRunRequest(
                mission="Map bounded search",
                requirements=("Explain the primary result",),
                scope="One deterministic end-to-end fixture",
                deliverable_description="A cited technical report",
                required_artifacts=frozenset({ArtifactKind.REPORT}),
            )
        )
        searched = runtime.researcher.search_papers(
            created.run_id,
            created.state_revision,
            "bounded search",
            limit=3,
        )
        self.assertEqual([], list(repository.load(created.run_id).papers))
        self.assertEqual([("bounded search", 3)], search_provider.calls)

        retained = runtime.researcher.retain_papers(
            created.run_id,
            searched.state_revision,
            searched.hits,
        )
        paper_ref = retained.paper_refs[0]
        retained_paper = repository.load(created.run_id).papers[paper_ref]
        self.assertIsNone(retained_paper.analysis)
        self.assertNotIn("Ephemeral provider summary", str(retained_paper))

        outline = runtime.researcher.inspect_source(
            created.run_id,
            retained.state_revision,
            paper_ref,
        )
        read = runtime.researcher.read_source(
            created.run_id,
            outline.state_revision,
            paper_ref,
            outline.outline.sections[0].locator,
        )
        self.assertIn("primary paper", read.source_content.content)

        analyzed = runtime.researcher.apply_research_mutation(
            created.run_id,
            read.state_revision,
            ResearchMutationBatch(
                puts=(
                    PutPaperAnalysis(
                        paper_ref=paper_ref,
                        analysis=PaperAnalysis(
                            summary="The study evaluates bounded search.",
                            relevance_to_run="It directly addresses the requirement.",
                            key_results=("A bounded-search improvement is reported.",),
                            limitations=("The evaluation scope is narrow.",),
                            key_locators=(
                                SourceLocator(kind="section", value="Results"),
                            ),
                        ),
                    ),
                )
            ),
        )
        approach = runtime.researcher.put_approach_family(
            created.run_id,
            analyzed.state_revision,
            name="Bounded Search",
            core_idea="Constrain search while preserving useful exploration.",
            representative_paper_refs=frozenset({paper_ref}),
        )
        source = frozenset(
            {
                LiteratureSource(
                    paper_ref=paper_ref,
                    relation=SourceRelation.SUPPORTS,
                    locator=SourceLocator(kind="section", value="Results"),
                )
            }
        )
        finding = runtime.researcher.put_landscape_finding(
            created.run_id,
            approach.state_revision,
            statement="Bounded search improves the evaluated task.",
            approach_refs=frozenset({approach.entity_ref}),
            sources=source,
        )
        problem = runtime.researcher.put_open_problem(
            created.run_id,
            finding.state_revision,
            statement="Generalization beyond the evaluated task remains open.",
            approach_refs=frozenset({approach.entity_ref}),
            sources=source,
        )

        checker_factory = FreshCheckerFactory()
        completion = runtime.completion.request_and_run(
            created.run_id,
            problem.state_revision,
            "The authoritative landscape covers the contract",
            checker_factory,
        )
        self.assertIs(completion.verdict, CompletionVerdict.PASS)
        self.assertEqual(1, len(checker_factory.instances))
        self.assertFalse(checker_factory.instances[0].has_broad_search)
        self.assertFalse(checker_factory.instances[0].has_research_mutation)

        editor_factory = FreshEditorFactory()
        planner = E2EPlanner(finding.entity_ref)
        writing_guide_path = (
            Path(__file__).parents[1] / ".vibe" / "REPORT_WRITING_GUIDE.md"
        )
        report = runtime.report_pipeline(
            planner=planner,
            composer=E2EComposer(paper_ref),
            integrator=PassthroughIntegrator(),
            editor_factory=editor_factory,
            reviser=PassthroughReviser(),
            integrity_reviewer=PassingIntegrityReviewer(),
            writing_guideline_path=writing_guide_path,
        ).run(created.run_id)
        self.assertIsInstance(report, PublishedReportPipelineResult)
        assert isinstance(report, PublishedReportPipelineResult)
        self.assertEqual(1, editor_factory.create_count)
        self.assertEqual(
            writing_guide_path.read_text(encoding="utf-8"),
            planner.writing_guideline,
        )
        self.assertIn("[1, section: Results]", report.artifact.path.read_text())

        validation = runtime.delivery.validate_delivery(created.run_id)
        self.assertEqual(
            frozenset({ArtifactKind.REPORT}), validation.validated_artifacts
        )
        closed = runtime.delivery.close_run(
            created.run_id,
            repository.load(created.run_id).state_revision,
        )
        self.assertIs(closed.outcome, RunOutcome.COMPLETE)

        publication = runtime.wiki_runtime(
            E2EWikiBuilder(),
            PassingWikiValidator(),
        ).rebuild()
        wiki_result = runtime.wiki_query.query("bounded search")
        self.assertEqual(1, len(wiki_result.hits))
        self.assertTrue(publication.wiki_path.is_symlink())

        final = repository.load(created.run_id)
        self.assertIs(final.lifecycle, LifecycleMode.CLOSED)
        self.assertIs(final.outcome, RunOutcome.COMPLETE)
        self.assertEqual(1, final.resources.usage["paper_search_attempts"])
        self.assertEqual(1, final.resources.usage["source_inspect_attempts"])
        self.assertEqual(1, final.resources.usage["source_read_attempts"])
        self.assertEqual(1, len(search_provider.calls))
        self.assertEqual(1, source_provider.inspect_calls)
        self.assertEqual(1, source_provider.read_calls)
        self.assertFalse(hasattr(runtime.researcher, "submit_completion_check"))
        self.assertFalse(hasattr(runtime.completion_checker, "search_papers"))
        self.assertFalse(hasattr(runtime, "repository"))
        self.assertFalse(hasattr(runtime, "artifact_store"))

        actions = tuple(
            event.action
            for event in LocalAuditLog(self.workspace / "runs").read(created.run_id)
        )
        self.assertIn("paper_search_attempt", actions)
        self.assertIn("completion_check_submitted", actions)
        self.assertIn("report_published", actions)
        self.assertEqual("run_closed", actions[-1])

    def test_deepxiv_composition_requires_environment_credential(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                PaperSearchConfigurationError,
                "DEEPXIV_TOKEN",
            ):
                LocalV1Runtime.from_deepxiv_env(self.workspace)
        self.assertFalse((self.workspace / "runs").exists())
