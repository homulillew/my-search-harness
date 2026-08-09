"""Correctness tests for the remaining frozen V1 Domain Commands."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from my_search_harness.domain import (
    Deliverable,
    LifecycleMode,
    LiteratureSource,
    PaperAnalysis,
    PaperResearchStatus,
    PaperSource,
    PartialAuthorizationBasis,
    ResearchContract,
    ResearchRequirement,
    SourceRelation,
)
from my_search_harness.runtime import (
    CommandRejectedError,
    CreateRunRequest,
    JsonResearchRunRepository,
    PaperSearchHit,
    PutPaperAnalysis,
    ResearchCommands,
    ResearchMutationBatch,
)


class DomainCommandsTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.repository = JsonResearchRunRepository(Path(self.temporary.name) / "runs")
        self.commands = ResearchCommands(self.repository)
        self.created = self.commands.create_run(
            CreateRunRequest(
                mission="Map a field",
                requirements=("Explain methods", "Identify limits"),
                scope="V1 scope",
                deliverable_description="A report",
            )
        )
        self.run_id = self.created.run_id

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _retain_pair(self) -> tuple[str, str, int]:
        retained = self.commands.retain_papers(
            self.run_id,
            1,
            (
                PaperSearchHit(
                    title="DOI record",
                    doi="10.1000/shared",
                    other_identifiers={"catalog": "doi-record"},
                ),
                PaperSearchHit(
                    title="arXiv record",
                    arxiv_id="2608.00001",
                    other_identifiers={"registry": "arxiv-record"},
                ),
            ),
        )
        return retained.paper_refs[0], retained.paper_refs[1], retained.state_revision

    def test_amend_contract_appends_history_and_removes_obsolete_gap_refs(
        self,
    ) -> None:
        gap = self.commands.put_investigation_gap(
            self.run_id,
            1,
            description="Old boundary gap",
            requirement_refs=frozenset(self.created.requirement_refs),
        )
        old_contract = self.repository.load(self.run_id).contract.revisions[0].contract
        replacement = ResearchRequirement(statement="New semantic requirement")
        amended = ResearchContract(
            mission="Map a revised field",
            requirements={replacement.id: replacement},
            scope=old_contract.scope,
            deliverable=deepcopy(old_contract.deliverable),
        )

        result = self.commands.amend_contract(
            self.run_id,
            gap.state_revision,
            amended,
            "User changed the completion boundary",
        )
        run = self.repository.load(self.run_id)

        self.assertEqual(gap.state_revision + 1, result.state_revision)
        self.assertEqual(2, run.contract.current_revision)
        self.assertEqual(2, len(run.contract.revisions))
        self.assertEqual("Map a field", run.contract.revisions[0].contract.mission)
        self.assertEqual(set(), run.investigation_gaps[gap.entity_ref].requirement_refs)
        self.assertIsNone(run.investigation_gaps[gap.entity_ref].resolution)

    def test_amend_contract_from_delivery_invalidates_current_authorization(
        self,
    ) -> None:
        authorized = self.commands.authorize_partial_delivery(
            self.run_id, 1, "Budget-limited handoff"
        )
        current_contract = (
            self.repository.load(self.run_id).contract.revisions[0].contract
        )
        amended_contract = deepcopy(current_contract)
        amended_contract.scope = "Revised scope"

        amended = self.commands.amend_contract(
            self.run_id,
            authorized.state_revision,
            amended_contract,
            "Scope changed",
        )
        run = self.repository.load(self.run_id)

        self.assertEqual(authorized.state_revision + 1, amended.state_revision)
        self.assertIs(run.lifecycle, LifecycleMode.RESEARCH)
        self.assertIsNone(run.delivery_basis)

    def test_paper_merge_requires_semantic_analysis_reconciliation(self) -> None:
        primary_ref, duplicate_ref, revision = self._retain_pair()
        analysed = self.commands.apply_research_mutation(
            self.run_id,
            revision,
            ResearchMutationBatch(
                puts=(
                    PutPaperAnalysis(
                        paper_ref=primary_ref,
                        analysis=PaperAnalysis(
                            summary="DOI interpretation",
                            relevance_to_run="Relevant",
                        ),
                    ),
                    PutPaperAnalysis(
                        paper_ref=duplicate_ref,
                        analysis=PaperAnalysis(
                            summary="arXiv interpretation",
                            relevance_to_run="Relevant",
                        ),
                    ),
                )
            ),
        )

        with self.assertRaisesRegex(CommandRejectedError, "reconciled_analysis"):
            self.commands.reconcile_paper_identity(
                self.run_id,
                analysed.state_revision,
                primary_ref,
                PaperSource(
                    title="Reconciled record",
                    doi="10.1000/shared",
                    arxiv_id="2608.00001",
                ),
                duplicate_paper_ref=duplicate_ref,
            )

        self.assertEqual(
            analysed.state_revision,
            self.repository.load(self.run_id).state_revision,
        )

    def test_paper_merge_rewrites_all_structured_paper_refs_once(self) -> None:
        primary_ref, duplicate_ref, revision = self._retain_pair()
        approach = self.commands.put_approach_family(
            self.run_id,
            revision,
            name="Merged route",
            core_idea="One underlying paper",
            representative_paper_refs=frozenset({duplicate_ref}),
        )
        source = frozenset(
            {
                LiteratureSource(
                    paper_ref=duplicate_ref,
                    relation=SourceRelation.SUPPORTS,
                )
            }
        )
        finding = self.commands.put_landscape_finding(
            self.run_id,
            approach.state_revision,
            statement="Finding",
            approach_refs=frozenset({approach.entity_ref}),
            sources=source,
        )
        problem = self.commands.put_open_problem(
            self.run_id,
            finding.state_revision,
            statement="Problem",
            approach_refs=frozenset({approach.entity_ref}),
            sources=source,
        )

        merged = self.commands.reconcile_paper_identity(
            self.run_id,
            problem.state_revision,
            primary_ref,
            PaperSource(
                title="Reconciled record",
                doi="https://doi.org/10.1000/SHARED",
                arxiv_id="2608.00001v2",
                other_identifiers={"catalog": "chosen-metadata"},
            ),
            duplicate_paper_ref=duplicate_ref,
            reconciled_analysis=PaperAnalysis(
                summary="Semantic reconciliation",
                relevance_to_run="Relevant",
            ),
        )
        run = self.repository.load(self.run_id)

        self.assertEqual(problem.state_revision + 1, merged.state_revision)
        self.assertNotIn(duplicate_ref, run.papers)
        self.assertEqual(
            {
                "catalog": "chosen-metadata",
                "registry": "arxiv-record",
            },
            run.papers[primary_ref].source.other_identifiers,
        )
        self.assertEqual(
            {primary_ref},
            run.literature_landscape.approach_families[
                approach.entity_ref
            ].representative_papers,
        )
        for item in (
            run.literature_landscape.findings[finding.entity_ref],
            run.literature_landscape.open_problems[problem.entity_ref],
        ):
            self.assertEqual({primary_ref}, {entry.paper_ref for entry in item.sources})

    def test_paper_reconciliation_cannot_discard_existing_stable_identity(self) -> None:
        primary_ref, _, revision = self._retain_pair()

        with self.assertRaisesRegex(CommandRejectedError, "cannot discard"):
            self.commands.reconcile_paper_identity(
                self.run_id,
                revision,
                primary_ref,
                PaperSource(title="Incomplete identity", arxiv_id="2608.99999"),
            )

    def test_merge_approach_family_unions_papers_and_rewrites_all_refs(self) -> None:
        first_paper, second_paper, revision = self._retain_pair()
        target = self.commands.put_approach_family(
            self.run_id,
            revision,
            name="Target",
            core_idea="Target idea",
            representative_paper_refs=frozenset({first_paper}),
        )
        source = self.commands.put_approach_family(
            self.run_id,
            target.state_revision,
            name="Duplicate",
            core_idea="Duplicate idea",
            representative_paper_refs=frozenset({second_paper}),
        )
        finding = self.commands.put_landscape_finding(
            self.run_id,
            source.state_revision,
            statement="References both",
            approach_refs=frozenset({target.entity_ref, source.entity_ref}),
        )
        problem = self.commands.put_open_problem(
            self.run_id,
            finding.state_revision,
            statement="References source",
            approach_refs=frozenset({source.entity_ref}),
        )
        gap = self.commands.put_investigation_gap(
            self.run_id,
            problem.state_revision,
            description="References source",
            approach_refs=frozenset({source.entity_ref}),
        )

        merged = self.commands.merge_approach_family(
            self.run_id,
            gap.state_revision,
            target.entity_ref,
            source.entity_ref,
        )
        run = self.repository.load(self.run_id)

        self.assertEqual(gap.state_revision + 1, merged.state_revision)
        self.assertNotIn(source.entity_ref, run.literature_landscape.approach_families)
        target_family = run.literature_landscape.approach_families[target.entity_ref]
        self.assertEqual(
            {first_paper, second_paper}, target_family.representative_papers
        )
        self.assertEqual(
            {target.entity_ref},
            run.literature_landscape.findings[finding.entity_ref].approach_refs,
        )
        self.assertEqual(
            {target.entity_ref},
            run.literature_landscape.open_problems[problem.entity_ref].approach_refs,
        )
        self.assertEqual(
            {target.entity_ref}, run.investigation_gaps[gap.entity_ref].approach_refs
        )

    def test_landscape_items_support_update_and_retirement(self) -> None:
        finding = self.commands.put_landscape_finding(
            self.run_id, 1, statement="Initial finding"
        )
        updated = self.commands.put_landscape_finding(
            self.run_id,
            finding.state_revision,
            statement="Corrected finding",
            finding_ref=finding.entity_ref,
        )
        problem = self.commands.put_open_problem(
            self.run_id, updated.state_revision, statement="Open problem"
        )
        retired_finding = self.commands.retire_landscape_finding(
            self.run_id, problem.state_revision, finding.entity_ref
        )
        retired_problem = self.commands.retire_open_problem(
            self.run_id, retired_finding.state_revision, problem.entity_ref
        )
        run = self.repository.load(self.run_id)

        self.assertEqual(problem.state_revision + 2, retired_problem.state_revision)
        self.assertFalse(run.literature_landscape.findings)
        self.assertFalse(run.literature_landscape.open_problems)

    def test_gap_update_resolve_and_reopen_preserve_identity(self) -> None:
        gap = self.commands.put_investigation_gap(
            self.run_id,
            1,
            description="Initial gap",
            requirement_refs=frozenset({self.created.requirement_refs[0]}),
        )
        updated = self.commands.put_investigation_gap(
            self.run_id,
            gap.state_revision,
            gap_ref=gap.entity_ref,
            description="Updated gap",
            requirement_refs=frozenset({self.created.requirement_refs[1]}),
        )
        resolved = self.commands.resolve_investigation_gap(
            self.run_id, updated.state_revision, gap.entity_ref, "Resolved by evidence"
        )
        reopened = self.commands.reopen_investigation_gap(
            self.run_id, resolved.state_revision, gap.entity_ref
        )
        persisted = self.repository.load(self.run_id).investigation_gaps[gap.entity_ref]

        self.assertEqual(resolved.state_revision + 1, reopened.state_revision)
        self.assertEqual("Updated gap", persisted.description)
        self.assertIsNone(persisted.resolution)

    def test_paper_status_changes_are_explicit_and_reject_noop(self) -> None:
        paper_ref, _, revision = self._retain_pair()
        retired = self.commands.set_paper_research_status(
            self.run_id,
            revision,
            paper_ref,
            PaperResearchStatus.RETIRED,
        )

        with self.assertRaisesRegex(CommandRejectedError, "must change"):
            self.commands.set_paper_research_status(
                self.run_id,
                retired.state_revision,
                paper_ref,
                PaperResearchStatus.RETIRED,
            )

        self.assertIs(
            self.repository.load(self.run_id).papers[paper_ref].research_status,
            PaperResearchStatus.RETIRED,
        )

    def test_partial_delivery_is_explicit_and_records_current_basis(self) -> None:
        result = self.commands.authorize_partial_delivery(
            self.run_id, 1, "Known limitations remain"
        )
        run = self.repository.load(self.run_id)

        self.assertEqual(2, result.state_revision)
        self.assertIs(run.lifecycle, LifecycleMode.DELIVERY)
        self.assertIsInstance(run.delivery_basis, PartialAuthorizationBasis)
        assert isinstance(run.delivery_basis, PartialAuthorizationBasis)
        self.assertEqual(result.state_revision, run.delivery_basis.basis_revision)
        self.assertEqual(1, run.delivery_basis.basis_contract_revision)
        self.assertEqual("Known limitations remain", run.delivery_basis.rationale)

    def test_partial_delivery_is_not_available_from_completion_check(self) -> None:
        requested = self.commands.request_completion_check(
            self.run_id, 1, "Check first"
        )

        with self.assertRaisesRegex(CommandRejectedError, "requires RESEARCH"):
            self.commands.authorize_partial_delivery(
                self.run_id,
                requested.state_revision,
                "Cannot bypass pending check",
            )

    def test_approach_requires_a_current_representative_paper(self) -> None:
        with self.assertRaisesRegex(CommandRejectedError, "at least one"):
            self.commands.put_approach_family(
                self.run_id,
                1,
                name="Ungrounded",
                core_idea="No paper",
                representative_paper_refs=frozenset(),
            )

    def test_amend_contract_rejects_semantic_noop(self) -> None:
        current_contract = deepcopy(
            self.repository.load(self.run_id).contract.revisions[0].contract
        )

        with self.assertRaisesRegex(CommandRejectedError, "must change"):
            self.commands.amend_contract(
                self.run_id, 1, current_contract, "No actual change"
            )

    def test_contract_value_is_copied_before_persistence(self) -> None:
        replacement = ResearchContract(
            mission="Replacement",
            requirements={},
            scope="Replacement scope",
            deliverable=Deliverable(description="Replacement delivery"),
        )
        self.commands.amend_contract(self.run_id, 1, replacement, "Replacement")
        replacement.mission = "Mutated by caller"

        persisted = self.repository.load(self.run_id).contract.revisions[-1].contract
        self.assertEqual("Replacement", persisted.mission)
