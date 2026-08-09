"""Whole-state and transition invariants for the core domain kernel."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from unittest import TestCase

from my_search_harness.domain import (
    ApproachFamily,
    CompletionCheck,
    CompletionPassBasis,
    CompletionVerdict,
    ContractRevision,
    Deliverable,
    DomainValidationError,
    InvestigationGap,
    LifecycleMode,
    Paper,
    PaperSource,
    PartialAuthorizationBasis,
    ResearchContract,
    ResearchRequirement,
    ResearchRun,
    RunOutcome,
    VersionedResearchContract,
    validate_run,
    validate_transition,
)


NOW = datetime(2026, 8, 10, 9, 30, tzinfo=timezone.utc)


def make_minimal_run() -> ResearchRun:
    requirement = ResearchRequirement(statement="Explain the result")
    contract = ResearchContract(
        mission="Study a bounded question",
        scope="V1 scope",
        deliverable=Deliverable(description="A report"),
        requirements={requirement.id: requirement},
    )
    return ResearchRun(
        contract=VersionedResearchContract(
            current_revision=1,
            revisions=[
                ContractRevision(
                    revision=1,
                    contract=contract,
                    reason="Initial contract",
                    recorded_at=NOW,
                )
            ],
        )
    )


def add_completed_pass(run: ResearchRun) -> CompletionCheck:
    check = CompletionCheck(
        basis_revision=run.state_revision,
        basis_contract_revision=run.contract.current_revision,
        requester_rationale="Ready to assess",
        requested_at=NOW,
        verdict=CompletionVerdict.PASS,
        reasons=("Requirements covered",),
        completed_at=NOW,
    )
    run.completion_checks[check.id] = check
    return check


class ValidateRunTests(TestCase):
    def test_minimal_run_is_valid(self) -> None:
        validate_run(make_minimal_run())

    def test_dangling_representative_paper_ref_is_rejected(self) -> None:
        run = make_minimal_run()
        missing_paper_ref = Paper(source=PaperSource(title="Missing")).id
        approach = ApproachFamily(
            name="A",
            core_idea="An approach",
            representative_papers={missing_paper_ref},
        )
        run.literature_landscape.approach_families[approach.id] = approach

        with self.assertRaisesRegex(DomainValidationError, "dangling"):
            validate_run(run)

    def test_empty_approach_representatives_are_rejected(self) -> None:
        run = make_minimal_run()
        approach = ApproachFamily(name="A", core_idea="An approach")
        run.literature_landscape.approach_families[approach.id] = approach

        with self.assertRaisesRegex(DomainValidationError, "representative paper"):
            validate_run(run)

    def test_completion_verdict_and_timestamp_must_cohere(self) -> None:
        run = make_minimal_run()
        check = CompletionCheck(
            basis_revision=1,
            basis_contract_revision=1,
            requester_rationale="Check now",
            requested_at=NOW,
            completed_at=NOW,
        )
        run.completion_checks[check.id] = check

        with self.assertRaisesRegex(DomainValidationError, "verdict and completed_at"):
            validate_run(run)

    def test_pending_check_must_match_lifecycle(self) -> None:
        run = make_minimal_run()
        check = CompletionCheck(
            basis_revision=1,
            basis_contract_revision=1,
            requester_rationale="Check now",
            requested_at=NOW,
        )
        run.completion_checks[check.id] = check

        with self.assertRaisesRegex(DomainValidationError, "pending completion checks"):
            validate_run(run)

    def test_completion_check_lifecycle_requires_one_pending_check(self) -> None:
        run = make_minimal_run()
        run.lifecycle = LifecycleMode.COMPLETION_CHECK

        with self.assertRaisesRegex(DomainValidationError, "pending completion checks"):
            validate_run(run)

    def test_delivery_requires_delivery_basis(self) -> None:
        run = make_minimal_run()
        run.lifecycle = LifecycleMode.DELIVERY

        with self.assertRaisesRegex(DomainValidationError, "requires a delivery basis"):
            validate_run(run)

    def test_closed_outcome_must_match_basis(self) -> None:
        run = make_minimal_run()
        run.lifecycle = LifecycleMode.CLOSED
        run.outcome = RunOutcome.COMPLETE
        run.delivery_basis = PartialAuthorizationBasis(
            basis_revision=1,
            basis_contract_revision=1,
            authorized_at=NOW,
            rationale="Accept partial delivery",
        )

        with self.assertRaisesRegex(DomainValidationError, "CompletionPassBasis"):
            validate_run(run)

    def test_completion_pass_basis_must_point_to_completed_pass(self) -> None:
        run = make_minimal_run()
        check = CompletionCheck(
            basis_revision=1,
            basis_contract_revision=1,
            requester_rationale="Check now",
            requested_at=NOW,
            verdict=CompletionVerdict.CONTINUE,
            completed_at=NOW,
        )
        run.completion_checks[check.id] = check
        run.lifecycle = LifecycleMode.DELIVERY
        run.delivery_basis = CompletionPassBasis(completion_check_ref=check.id)

        with self.assertRaisesRegex(DomainValidationError, "completed PASS"):
            validate_run(run)

    def test_obvious_stable_paper_identifier_collision_is_rejected(self) -> None:
        run = make_minimal_run()
        first = Paper(source=PaperSource(title="First", doi="10.1000/example"))
        second = Paper(
            source=PaperSource(title="Second", doi="https://doi.org/10.1000/EXAMPLE")
        )
        run.papers = {first.id: first, second.id: second}

        with self.assertRaisesRegex(DomainValidationError, "share stable identifier"):
            validate_run(run)

    def test_naive_timestamp_is_rejected(self) -> None:
        run = make_minimal_run()
        run.contract.revisions[0].recorded_at = datetime(2026, 8, 10, 9, 30)

        with self.assertRaisesRegex(DomainValidationError, "timezone-aware"):
            validate_run(run)


class ValidateTransitionTests(TestCase):
    def test_contract_revision_history_cannot_be_rewritten(self) -> None:
        before = make_minimal_run()
        after = deepcopy(before)
        after.state_revision = 2
        after.contract.revisions[0].contract.mission = "Rewritten history"

        with self.assertRaisesRegex(DomainValidationError, "history is immutable"):
            validate_transition(before, after)

    def test_completed_check_cannot_be_modified(self) -> None:
        before = make_minimal_run()
        check = add_completed_pass(before)
        after = deepcopy(before)
        after.state_revision = 2
        after.completion_checks[check.id].reasons = ("Changed judgment",)

        with self.assertRaisesRegex(DomainValidationError, "is immutable"):
            validate_transition(before, after)

    def test_investigation_gap_cannot_be_deleted(self) -> None:
        before = make_minimal_run()
        gap = InvestigationGap(description="An unresolved question")
        before.investigation_gaps[gap.id] = gap
        after = deepcopy(before)
        after.state_revision = 2
        del after.investigation_gaps[gap.id]

        with self.assertRaisesRegex(DomainValidationError, "cannot be deleted"):
            validate_transition(before, after)

    def test_state_revision_must_advance_by_exactly_one(self) -> None:
        before = make_minimal_run()
        after = deepcopy(before)
        after.state_revision = 3

        with self.assertRaisesRegex(DomainValidationError, "exactly one"):
            validate_transition(before, after)

    def test_valid_transition_is_accepted(self) -> None:
        before = make_minimal_run()
        after = deepcopy(before)
        after.state_revision = 2
        after.resources.usage["search_requests"] = 1

        validate_transition(before, after)
