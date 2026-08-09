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


def add_pending_check(run: ResearchRun) -> CompletionCheck:
    check = CompletionCheck(
        basis_revision=run.state_revision,
        basis_contract_revision=run.contract.current_revision,
        requester_rationale="Ready to assess",
        requested_at=NOW,
    )
    run.completion_checks[check.id] = check
    run.lifecycle = LifecycleMode.COMPLETION_CHECK
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

    def test_normalized_doi_collision_is_rejected(self) -> None:
        run = make_minimal_run()
        first = Paper(source=PaperSource(title="First", doi="10.1000/example"))
        second = Paper(
            source=PaperSource(title="Second", doi="https://doi.org/10.1000/EXAMPLE")
        )
        run.papers = {first.id: first, second.id: second}

        with self.assertRaisesRegex(DomainValidationError, "share stable identifier"):
            validate_run(run)

    def test_normalized_arxiv_collision_is_rejected(self) -> None:
        run = make_minimal_run()
        first = Paper(source=PaperSource(title="First", arxiv_id="2608.00001v2"))
        second = Paper(
            source=PaperSource(
                title="Second", arxiv_id="https://arxiv.org/pdf/2608.00001.pdf"
            )
        )
        run.papers = {first.id: first, second.id: second}

        with self.assertRaisesRegex(DomainValidationError, "share stable identifier"):
            validate_run(run)

    def test_exact_canonical_url_collision_is_rejected(self) -> None:
        run = make_minimal_run()
        first = Paper(
            source=PaperSource(title="First", canonical_url="https://example.org/Paper")
        )
        second = Paper(
            source=PaperSource(
                title="Second", canonical_url="  https://example.org/Paper  "
            )
        )
        run.papers = {first.id: first, second.id: second}

        with self.assertRaisesRegex(DomainValidationError, "share stable identifier"):
            validate_run(run)

    def test_canonical_url_path_case_is_not_normalized(self) -> None:
        run = make_minimal_run()
        first = Paper(
            source=PaperSource(title="First", canonical_url="https://example.org/Paper")
        )
        second = Paper(
            source=PaperSource(
                title="Second", canonical_url="https://example.org/paper"
            )
        )
        run.papers = {first.id: first, second.id: second}

        validate_run(run)

    def test_other_identifiers_do_not_trigger_automatic_collision(self) -> None:
        run = make_minimal_run()
        first = Paper(
            source=PaperSource(
                title="First", other_identifiers={"provider_key": "Paper-42"}
            )
        )
        second = Paper(
            source=PaperSource(
                title="Second", other_identifiers={"provider_key": "paper-42"}
            )
        )
        run.papers = {first.id: first, second.id: second}

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

    def test_pending_check_basis_revision_cannot_be_rewritten(self) -> None:
        before = make_minimal_run()
        check = add_pending_check(before)
        after = deepcopy(before)
        after.state_revision = 2
        after.completion_checks[check.id].basis_revision = 2

        with self.assertRaisesRegex(DomainValidationError, "request metadata"):
            validate_transition(before, after)

    def test_pending_check_contract_basis_cannot_be_rewritten(self) -> None:
        before = make_minimal_run()
        before.state_revision = 2
        revised_contract = deepcopy(before.contract.revisions[0].contract)
        revised_contract.mission = "Refined bounded question"
        before.contract.revisions.append(
            ContractRevision(
                revision=2,
                contract=revised_contract,
                reason="Refine the mission",
                recorded_at=NOW,
            )
        )
        before.contract.current_revision = 2
        check = add_pending_check(before)
        after = deepcopy(before)
        after.state_revision = 3
        after.completion_checks[check.id].basis_contract_revision = 1

        with self.assertRaisesRegex(DomainValidationError, "request metadata"):
            validate_transition(before, after)

    def test_pending_check_requested_at_cannot_be_rewritten(self) -> None:
        before = make_minimal_run()
        check = add_pending_check(before)
        after = deepcopy(before)
        after.state_revision = 2
        after.completion_checks[check.id].requested_at = datetime(
            2026, 8, 11, 9, 30, tzinfo=timezone.utc
        )

        with self.assertRaisesRegex(DomainValidationError, "request metadata"):
            validate_transition(before, after)

    def test_pending_check_rationale_cannot_be_rewritten(self) -> None:
        before = make_minimal_run()
        check = add_pending_check(before)
        after = deepcopy(before)
        after.state_revision = 2
        after.completion_checks[check.id].requester_rationale = "Changed rationale"

        with self.assertRaisesRegex(DomainValidationError, "request metadata"):
            validate_transition(before, after)

    def test_pending_check_cannot_be_deleted(self) -> None:
        before = make_minimal_run()
        check = add_pending_check(before)
        after = deepcopy(before)
        after.state_revision = 2
        after.lifecycle = LifecycleMode.RESEARCH
        del after.completion_checks[check.id]

        with self.assertRaisesRegex(DomainValidationError, "cannot be deleted"):
            validate_transition(before, after)

    def test_pending_check_can_complete_without_changing_request_metadata(self) -> None:
        before = make_minimal_run()
        check = add_pending_check(before)
        after = deepcopy(before)
        after.state_revision = 2
        after.lifecycle = LifecycleMode.RESEARCH
        proposed_check = after.completion_checks[check.id]
        proposed_check.verdict = CompletionVerdict.CONTINUE
        proposed_check.reasons = ("More research is needed",)
        proposed_check.completed_at = NOW

        validate_transition(before, after)

    def test_pending_check_can_remain_during_resource_transition(self) -> None:
        before = make_minimal_run()
        add_pending_check(before)
        after = deepcopy(before)
        after.state_revision = 2
        after.resources.usage["source_requests"] = 1

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
