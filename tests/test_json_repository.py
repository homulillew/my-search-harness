"""JSON codec and file repository behavior."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from my_search_harness.domain import (
    ApproachFamily,
    ArtifactKind,
    CompletionPassBasis,
    DomainValidationError,
    LandscapeFinding,
    LifecycleMode,
    LiteratureSource,
    OpenProblem,
    Paper,
    PaperAnalysis,
    PaperSource,
    PartialAuthorizationBasis,
    RunOutcome,
    SourceLocator,
    SourceRelation,
    validate_run,
)
from my_search_harness.runtime import (
    JsonResearchRunRepository,
    RevisionConflictError,
    RunAlreadyExistsError,
    run_from_json,
    run_to_json,
)

from test_domain_validation import NOW, add_completed_pass, make_minimal_run


def make_rich_delivery_run():
    run = make_minimal_run()
    run.contract.revisions[0].contract.deliverable.required_artifacts = {
        ArtifactKind.REPORT
    }
    paper = Paper(
        source=PaperSource(
            title="A paper",
            authors=("Ada Example", "Lin Example"),
            publication_year=2026,
            doi="10.1000/example",
            arxiv_id="2608.00001v2",
            canonical_url="https://example.test/paper",
            other_identifiers={"corpus": "P-42"},
        ),
        analysis=PaperAnalysis(
            summary="Summary",
            relevance_to_run="Directly relevant",
            contributions=("A contribution",),
            key_results=("A result",),
            limitations=("A limitation",),
            key_locators=(SourceLocator(kind="page", value="3"),),
        ),
    )
    run.papers[paper.id] = paper
    approach = ApproachFamily(
        name="Approach",
        core_idea="Core idea",
        representative_papers={paper.id},
    )
    run.literature_landscape.approach_families[approach.id] = approach
    source = LiteratureSource(
        paper_ref=paper.id,
        relation=SourceRelation.SUPPORTS,
        locator=SourceLocator(kind="section", value="4.2"),
    )
    finding = LandscapeFinding(
        statement="Finding",
        approach_refs={approach.id},
        sources={source},
    )
    problem = OpenProblem(
        statement="Open problem",
        approach_refs={approach.id},
        sources={source},
    )
    run.literature_landscape.findings[finding.id] = finding
    run.literature_landscape.open_problems[problem.id] = problem
    check = add_completed_pass(run)
    run.lifecycle = LifecycleMode.DELIVERY
    run.delivery_basis = CompletionPassBasis(completion_check_ref=check.id)
    run.resources.limits["search_requests"] = 10
    run.resources.usage["search_requests"] = 2
    validate_run(run)
    return run


class JsonCodecTests(TestCase):
    def test_round_trip_preserves_domain_types(self) -> None:
        original = make_rich_delivery_run()

        restored = run_from_json(run_to_json(original))

        self.assertEqual(original, restored)
        self.assertIs(restored.lifecycle, LifecycleMode.DELIVERY)
        self.assertIsInstance(restored.delivery_basis, CompletionPassBasis)
        self.assertIsInstance(
            restored.contract.revisions[0].recorded_at.tzinfo,
            type(NOW.tzinfo),
        )
        approach = next(iter(restored.literature_landscape.approach_families.values()))
        self.assertIsInstance(approach.representative_papers, set)
        finding = next(iter(restored.literature_landscape.findings.values()))
        self.assertIsInstance(finding.sources, set)

    def test_partial_authorization_tag_round_trips(self) -> None:
        original = make_minimal_run()
        original.lifecycle = LifecycleMode.CLOSED
        original.outcome = RunOutcome.PARTIAL
        original.delivery_basis = PartialAuthorizationBasis(
            basis_revision=1,
            basis_contract_revision=1,
            authorized_at=NOW,
            rationale="User accepts partial results",
        )

        restored = run_from_json(run_to_json(original))

        self.assertEqual(original, restored)
        basis = restored.delivery_basis
        self.assertIsInstance(basis, PartialAuthorizationBasis)
        assert isinstance(basis, PartialAuthorizationBasis)
        self.assertEqual("User accepts partial results", basis.rationale)

    def test_unknown_delivery_basis_tag_is_rejected(self) -> None:
        payload = run_to_json(make_minimal_run()).replace(
            '"delivery_basis": null',
            '"delivery_basis": {"type": "future_variant"}',
        )

        with self.assertRaisesRegex(DomainValidationError, "unknown value"):
            run_from_json(payload)


class JsonResearchRunRepositoryTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name) / "runs"
        self.repository = JsonResearchRunRepository(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_create_load_and_save_round_trip(self) -> None:
        original = make_rich_delivery_run()
        self.repository.create(original)
        self.assertEqual(original, self.repository.load(original.id))

        proposed = deepcopy(original)
        proposed.state_revision = 2
        proposed.resources.usage["search_requests"] = 3
        self.repository.save(proposed, expected_revision=1)

        self.assertEqual(proposed, self.repository.load(original.id))

    def test_create_does_not_overwrite_existing_run(self) -> None:
        run = make_minimal_run()
        self.repository.create(run)

        with self.assertRaises(RunAlreadyExistsError):
            self.repository.create(run)

    def test_stale_expected_revision_is_rejected(self) -> None:
        run = make_minimal_run()
        self.repository.create(run)
        proposed = deepcopy(run)
        proposed.state_revision = 2

        with self.assertRaises(RevisionConflictError):
            self.repository.save(proposed, expected_revision=0)

    def test_validation_failure_does_not_corrupt_previous_state(self) -> None:
        run = make_minimal_run()
        self.repository.create(run)
        state_path = self.root / run.id / "state.json"
        previous_bytes = state_path.read_bytes()
        proposed = deepcopy(run)
        proposed.state_revision = 2
        proposed.lifecycle = LifecycleMode.DELIVERY

        with self.assertRaises(DomainValidationError):
            self.repository.save(proposed, expected_revision=1)

        self.assertEqual(previous_bytes, state_path.read_bytes())
        self.assertEqual(run, self.repository.load(run.id))

    def test_replace_failure_does_not_corrupt_previous_state(self) -> None:
        run = make_minimal_run()
        self.repository.create(run)
        state_path = self.root / run.id / "state.json"
        previous_bytes = state_path.read_bytes()
        proposed = deepcopy(run)
        proposed.state_revision = 2
        proposed.resources.usage["search_requests"] = 1

        with patch(
            "my_search_harness.runtime.persistence.os.replace",
            side_effect=OSError("simulated replace failure"),
        ):
            with self.assertRaises(OSError):
                self.repository.save(proposed, expected_revision=1)

        self.assertEqual(previous_bytes, state_path.read_bytes())
        self.assertFalse(state_path.with_name("state.json.tmp").exists())
        self.assertEqual(run, self.repository.load(run.id))
