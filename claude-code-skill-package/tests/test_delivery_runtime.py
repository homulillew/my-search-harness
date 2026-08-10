"""End-to-end tests for the V1 delivery runtime vertical slice."""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from my_search_harness.domain import (
    ArtifactKind,
    CompletionPassBasis,
    CompletionVerdict,
    ContractRevision,
    LifecycleMode,
    PartialAuthorizationBasis,
    RunOutcome,
)
from my_search_harness.domain.model import utc_now
from my_search_harness.runtime import (
    ArtifactValidationError,
    CommandRejectedError,
    CreateRunRequest,
    DeliveryCommands,
    JsonResearchRunRepository,
    LocalArtifactStore,
    ResearchCommands,
    RevisionConflictError,
)


class DeliveryRuntimeTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name) / "runs"
        self.repository = JsonResearchRunRepository(self.root)
        self.research = ResearchCommands(self.repository)
        self.artifacts = LocalArtifactStore(self.root)
        self.delivery = DeliveryCommands(self.repository, self.artifacts)
        created = self.research.create_run(
            CreateRunRequest(
                mission="Map the research area",
                requirements=("Explain the main result",),
                scope="A bounded V1 study",
                deliverable_description="A cited report",
                required_artifacts=frozenset({ArtifactKind.REPORT}),
            )
        )
        self.run_id = created.run_id
        requested = self.research.request_completion_check(
            self.run_id,
            1,
            "The current research is sufficient",
        )
        self.first_check_ref = requested.completion_check_ref
        self.research.submit_completion_check(
            self.run_id,
            2,
            self.first_check_ref,
            CompletionVerdict.PASS,
            ("All requirements are covered",),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @property
    def report_path(self) -> Path:
        return self.root / self.run_id / "artifacts" / "report.md"

    @property
    def metadata_path(self) -> Path:
        return self.root / self.run_id / "artifacts" / "report.meta.json"

    @property
    def state_path(self) -> Path:
        return self.root / self.run_id / "state.json"

    def _publish(self, content: str = "# Report\n\nSupported findings.\n"):
        return self.delivery.publish_report(self.run_id, 3, content)

    def _reopen_and_pass_again(self):
        self.delivery.reopen_research(self.run_id, 3)
        requested = self.research.request_completion_check(
            self.run_id,
            4,
            "The revised research is sufficient",
        )
        self.research.submit_completion_check(
            self.run_id,
            5,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("The revised requirements are covered",),
        )
        return requested.completion_check_ref

    def test_delivery_with_pass_basis_can_publish_report(self) -> None:
        result = self._publish()

        self.assertIs(result.artifact_kind, ArtifactKind.REPORT)
        self.assertEqual(self.report_path, result.path)
        self.assertTrue(self.report_path.is_file())
        self.assertEqual(
            "# Report\n\nSupported findings.\n", self.report_path.read_text()
        )

    def test_report_metadata_captures_current_full_delivery_basis(self) -> None:
        result = self._publish()
        metadata = self.artifacts.read_report_metadata(self.run_id)
        raw_metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))

        self.assertEqual(result.delivery_basis, metadata.delivery_basis)
        self.assertEqual(
            {
                "type": "completion_pass",
                "completion_check_ref": self.first_check_ref,
            },
            raw_metadata["delivery_basis"],
        )

    def test_report_metadata_digest_matches_utf8_content(self) -> None:
        content = "# Unicode report\n\n证据。\n"
        result = self._publish(content)
        metadata = self.artifacts.read_report_metadata(self.run_id)
        expected = hashlib.sha256(content.encode("utf-8")).hexdigest()

        self.assertEqual(expected, result.content_sha256)
        self.assertEqual(expected, metadata.content_sha256)

    def test_publish_report_does_not_advance_state_revision(self) -> None:
        before = self.state_path.read_bytes()

        self._publish()

        self.assertEqual(before, self.state_path.read_bytes())
        self.assertEqual(3, self.repository.load(self.run_id).state_revision)

    def test_publish_report_rejects_non_delivery_run(self) -> None:
        self.delivery.reopen_research(self.run_id, 3)

        with self.assertRaisesRegex(CommandRejectedError, "requires DELIVERY"):
            self.delivery.publish_report(self.run_id, 4, "Report")

        self.assertFalse(self.report_path.exists())

    def test_publish_report_rejects_stale_expected_revision(self) -> None:
        with self.assertRaisesRegex(RevisionConflictError, "expected revision 2"):
            self.delivery.publish_report(self.run_id, 2, "Report")

        self.assertFalse(self.report_path.exists())

    def test_publish_report_rejects_empty_or_whitespace_content(self) -> None:
        for content in ("", " \n\t"):
            with self.subTest(content=content):
                with self.assertRaisesRegex(CommandRejectedError, "non-empty"):
                    self.delivery.publish_report(self.run_id, 3, content)

        self.assertFalse(self.report_path.exists())

    def test_publish_report_rejects_non_string_content(self) -> None:
        with self.assertRaisesRegex(CommandRejectedError, "non-empty string"):
            self.delivery.publish_report(self.run_id, 3, None)  # type: ignore[arg-type]

        self.assertFalse(self.report_path.exists())

    def test_valid_current_report_passes_delivery_validation(self) -> None:
        published = self._publish()

        result = self.delivery.validate_delivery(self.run_id)

        self.assertEqual(published.delivery_basis, result.delivery_basis)
        self.assertEqual(frozenset({ArtifactKind.REPORT}), result.validated_artifacts)

    def test_required_report_missing_fails_delivery_validation(self) -> None:
        with self.assertRaisesRegex(ArtifactValidationError, "content is missing"):
            self.delivery.validate_delivery(self.run_id)

    def test_report_metadata_missing_fails_delivery_validation(self) -> None:
        self._publish()
        self.metadata_path.unlink()

        with self.assertRaisesRegex(ArtifactValidationError, "metadata is missing"):
            self.delivery.validate_delivery(self.run_id)

    def test_report_content_missing_with_metadata_fails_validation(self) -> None:
        self._publish()
        self.report_path.unlink()

        with self.assertRaisesRegex(ArtifactValidationError, "content is missing"):
            self.delivery.validate_delivery(self.run_id)

    def test_report_content_digest_mismatch_fails_validation(self) -> None:
        self._publish()
        self.report_path.write_text("manually changed", encoding="utf-8")

        with self.assertRaisesRegex(ArtifactValidationError, "digest"):
            self.delivery.validate_delivery(self.run_id)

    def test_report_basis_mismatch_fails_validation(self) -> None:
        self._publish()
        self._reopen_and_pass_again()

        with self.assertRaisesRegex(ArtifactValidationError, "basis"):
            self.delivery.validate_delivery(self.run_id)

    def test_invalid_report_artifact_kind_fails_validation(self) -> None:
        self._publish()
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        metadata["artifact_kind"] = "FUTURE_KIND"
        self.metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        with self.assertRaisesRegex(ArtifactValidationError, "metadata is invalid"):
            self.delivery.validate_delivery(self.run_id)

    def test_validation_does_not_persist_a_pass_flag_or_change_state(self) -> None:
        self._publish()
        before = self.state_path.read_bytes()

        self.delivery.validate_delivery(self.run_id)

        self.assertEqual(before, self.state_path.read_bytes())
        self.assertNotIn("validation_passed", self.state_path.read_text())

    def test_stale_pass_basis_cannot_validate_or_close_newer_contract(self) -> None:
        run = self.repository.load(self.run_id)
        revised_contract = deepcopy(run.contract.revisions[-1].contract)
        revised_contract.deliverable.required_artifacts.clear()
        run.contract.revisions.append(
            ContractRevision(
                revision=2,
                contract=revised_contract,
                reason="Current delivery no longer requires a report",
            )
        )
        run.contract.current_revision = 2
        run.state_revision = 4
        # Deliberately persist an architecture-invalid snapshot to verify that
        # the Delivery boundary cannot authorize it.
        self.repository.save(run, 3)
        before = self.state_path.read_bytes()

        with self.assertRaisesRegex(CommandRejectedError, "contract revision"):
            self.delivery.validate_delivery(self.run_id)
        with self.assertRaisesRegex(CommandRejectedError, "contract revision"):
            self.delivery.close_run(self.run_id, 4)

        self.assertEqual(before, self.state_path.read_bytes())

    def test_validation_uses_legally_current_contract_requirements(self) -> None:
        created = self.research.create_run(
            CreateRunRequest(
                mission="Deliver a run with no required artifacts",
                requirements=("Record the completion decision",),
                scope="Empty artifact fixture",
                deliverable_description="No derived artifact is required",
                required_artifacts=frozenset(),
            )
        )
        requested = self.research.request_completion_check(
            created.run_id,
            1,
            "The artifact-free contract is complete",
        )
        self.research.submit_completion_check(
            created.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("The current contract requirements are covered",),
        )

        result = self.delivery.validate_delivery(created.run_id)

        self.assertEqual(frozenset(), result.validated_artifacts)

    def test_partial_basis_cannot_validate_or_close_newer_contract(self) -> None:
        created = self.research.create_run(
            CreateRunRequest(
                mission="Exercise stale partial authorization",
                requirements=("Record the partial boundary",),
                scope="Corrupt fixture",
                deliverable_description="No derived artifact is required",
                required_artifacts=frozenset(),
            )
        )
        partial = self.repository.load(created.run_id)
        partial.state_revision = 2
        partial.lifecycle = LifecycleMode.DELIVERY
        partial.delivery_basis = PartialAuthorizationBasis(
            basis_revision=1,
            basis_contract_revision=1,
            authorized_at=utc_now(),
            rationale="Authorized under contract revision 1",
        )
        self.repository.save(partial, 1)

        stale = self.repository.load(created.run_id)
        revised_contract = deepcopy(stale.contract.revisions[-1].contract)
        stale.contract.revisions.append(
            ContractRevision(
                revision=2,
                contract=revised_contract,
                reason="Simulated unreachable contract amendment",
            )
        )
        stale.contract.current_revision = 2
        stale.state_revision = 3
        self.repository.save(stale, 2)
        state_path = self.root / created.run_id / "state.json"
        before = state_path.read_bytes()

        with self.assertRaisesRegex(CommandRejectedError, "contract revision"):
            self.delivery.validate_delivery(created.run_id)
        with self.assertRaisesRegex(CommandRejectedError, "contract revision"):
            self.delivery.close_run(created.run_id, 3)

        self.assertEqual(before, state_path.read_bytes())

    def test_reopen_transitions_delivery_to_research(self) -> None:
        result = self.delivery.reopen_research(self.run_id, 3)
        run = self.repository.load(self.run_id)

        self.assertEqual(4, result.state_revision)
        self.assertIs(run.lifecycle, LifecycleMode.RESEARCH)

    def test_reopen_clears_current_delivery_basis(self) -> None:
        self.delivery.reopen_research(self.run_id, 3)

        self.assertIsNone(self.repository.load(self.run_id).delivery_basis)

    def test_reopen_preserves_historical_pass_check(self) -> None:
        before = deepcopy(
            self.repository.load(self.run_id).completion_checks[self.first_check_ref]
        )

        self.delivery.reopen_research(self.run_id, 3)

        after = self.repository.load(self.run_id).completion_checks[
            self.first_check_ref
        ]
        self.assertEqual(before, after)
        self.assertIs(after.verdict, CompletionVerdict.PASS)

    def test_reopen_does_not_delete_existing_report_files(self) -> None:
        self._publish()

        self.delivery.reopen_research(self.run_id, 3)

        self.assertTrue(self.report_path.is_file())
        self.assertTrue(self.metadata_path.is_file())

    def test_old_report_is_stale_after_reopen(self) -> None:
        self._publish()
        self.delivery.reopen_research(self.run_id, 3)

        with self.assertRaisesRegex(ArtifactValidationError, "basis"):
            self.delivery.validate_delivery(self.run_id)

    def test_reopen_advances_exactly_one_revision(self) -> None:
        result = self.delivery.reopen_research(self.run_id, 3)

        self.assertEqual(4, result.state_revision)
        self.assertEqual(4, self.repository.load(self.run_id).state_revision)

    def test_reopen_rejects_non_delivery_lifecycle(self) -> None:
        self.delivery.reopen_research(self.run_id, 3)

        with self.assertRaisesRegex(CommandRejectedError, "requires DELIVERY"):
            self.delivery.reopen_research(self.run_id, 4)

        self.assertEqual(4, self.repository.load(self.run_id).state_revision)

    def test_new_pass_after_reopen_creates_a_new_delivery_basis(self) -> None:
        old_basis = self.repository.load(self.run_id).delivery_basis

        second_check_ref = self._reopen_and_pass_again()
        new_basis = self.repository.load(self.run_id).delivery_basis

        self.assertEqual(
            CompletionPassBasis(completion_check_ref=second_check_ref), new_basis
        )
        self.assertNotEqual(old_basis, new_basis)

    def test_old_report_remains_stale_after_new_pass(self) -> None:
        old_artifact = self._publish()
        self._reopen_and_pass_again()
        current_basis = self.repository.load(self.run_id).delivery_basis

        self.assertNotEqual(old_artifact.delivery_basis, current_basis)
        with self.assertRaisesRegex(ArtifactValidationError, "basis"):
            self.delivery.validate_delivery(self.run_id)

    def test_republish_after_new_pass_makes_report_current(self) -> None:
        self._publish("old report")
        self._reopen_and_pass_again()

        published = self.delivery.publish_report(self.run_id, 6, "new report")
        validated = self.delivery.validate_delivery(self.run_id)

        self.assertEqual(published.delivery_basis, validated.delivery_basis)
        self.assertEqual("new report", self.report_path.read_text(encoding="utf-8"))
        self.assertEqual(6, self.repository.load(self.run_id).state_revision)

    def test_close_with_current_required_report_enters_closed(self) -> None:
        self._publish()

        self.delivery.close_run(self.run_id, 3)

        self.assertIs(self.repository.load(self.run_id).lifecycle, LifecycleMode.CLOSED)

    def test_close_with_completion_pass_basis_sets_complete_outcome(self) -> None:
        self._publish()

        result = self.delivery.close_run(self.run_id, 3)

        self.assertIs(result.outcome, RunOutcome.COMPLETE)
        self.assertIs(self.repository.load(self.run_id).outcome, RunOutcome.COMPLETE)

    def test_close_retains_delivery_basis_as_closure_provenance(self) -> None:
        self._publish()
        basis = self.repository.load(self.run_id).delivery_basis

        self.delivery.close_run(self.run_id, 3)

        self.assertEqual(basis, self.repository.load(self.run_id).delivery_basis)

    def test_close_advances_exactly_one_revision(self) -> None:
        self._publish()

        result = self.delivery.close_run(self.run_id, 3)

        self.assertEqual(4, result.state_revision)
        self.assertEqual(4, self.repository.load(self.run_id).state_revision)

    def test_close_with_missing_report_rejects_without_state_change(self) -> None:
        before = self.state_path.read_bytes()

        with self.assertRaises(ArtifactValidationError):
            self.delivery.close_run(self.run_id, 3)

        self.assertEqual(before, self.state_path.read_bytes())

    def test_close_with_corrupt_report_rejects_without_state_change(self) -> None:
        self._publish()
        self.report_path.write_text("corrupt", encoding="utf-8")
        before = self.state_path.read_bytes()

        with self.assertRaisesRegex(ArtifactValidationError, "digest"):
            self.delivery.close_run(self.run_id, 3)

        self.assertEqual(before, self.state_path.read_bytes())

    def test_close_with_stale_provenance_rejects_without_state_change(self) -> None:
        self._publish("old report")
        self._reopen_and_pass_again()
        before = self.state_path.read_bytes()

        with self.assertRaisesRegex(ArtifactValidationError, "basis"):
            self.delivery.close_run(self.run_id, 6)

        self.assertEqual(before, self.state_path.read_bytes())

    def test_close_rejects_non_delivery_lifecycle(self) -> None:
        self.delivery.reopen_research(self.run_id, 3)
        before = self.state_path.read_bytes()

        with self.assertRaisesRegex(CommandRejectedError, "requires DELIVERY"):
            self.delivery.close_run(self.run_id, 4)

        self.assertEqual(before, self.state_path.read_bytes())

    def test_partial_basis_closes_mechanically_as_partial(self) -> None:
        partial_created = self.research.create_run(
            CreateRunRequest(
                mission="Deliver an authorized partial result",
                requirements=("State the known limitations",),
                scope="Partial fixture",
                deliverable_description="A partial report",
                required_artifacts=frozenset({ArtifactKind.REPORT}),
            )
        )
        partial = self.repository.load(partial_created.run_id)
        partial.state_revision = 2
        partial.lifecycle = LifecycleMode.DELIVERY
        partial.delivery_basis = PartialAuthorizationBasis(
            basis_revision=1,
            basis_contract_revision=1,
            authorized_at=utc_now(),
            rationale="Authorized fixture",
        )
        self.repository.save(partial, 1)

        published = self.delivery.publish_report(
            partial.id,
            2,
            "# Partial report\n",
        )
        result = self.delivery.close_run(partial.id, 2)
        closed = self.repository.load(partial.id)
        metadata = json.loads(
            (self.root / partial.id / "artifacts" / "report.meta.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(partial.delivery_basis, published.delivery_basis)
        self.assertEqual(
            {
                "type": "partial_authorization",
                "basis_revision": 1,
                "basis_contract_revision": 1,
                "authorized_at": partial.delivery_basis.authorized_at.isoformat(),
                "rationale": "Authorized fixture",
            },
            metadata["delivery_basis"],
        )
        self.assertIs(result.outcome, RunOutcome.PARTIAL)
        self.assertIs(closed.lifecycle, LifecycleMode.CLOSED)
        self.assertIs(closed.outcome, RunOutcome.PARTIAL)
        self.assertEqual(partial.delivery_basis, closed.delivery_basis)

    def test_failed_initial_metadata_publish_leaves_content_but_is_invalid(
        self,
    ) -> None:
        real_replace = os.replace

        def replace_with_metadata_failure(
            source: str | Path, target: str | Path
        ) -> None:
            if Path(target).name == "report.meta.json":
                raise OSError("simulated metadata publication failure")
            real_replace(source, target)

        with patch(
            "my_search_harness.runtime.artifacts.os.replace",
            side_effect=replace_with_metadata_failure,
        ):
            with self.assertRaisesRegex(OSError, "metadata publication"):
                self._publish()

        self.assertTrue(self.report_path.is_file())
        self.assertFalse(self.metadata_path.exists())
        self.assertFalse(self.metadata_path.with_suffix(".json.tmp").exists())
        with self.assertRaisesRegex(ArtifactValidationError, "metadata is missing"):
            self.delivery.validate_delivery(self.run_id)

    def test_failed_republish_leaves_old_metadata_and_new_content_invalid(self) -> None:
        self._publish("old report")
        real_replace = os.replace

        def replace_with_metadata_failure(
            source: str | Path, target: str | Path
        ) -> None:
            if Path(target).name == "report.meta.json":
                raise OSError("simulated metadata publication failure")
            real_replace(source, target)

        with patch(
            "my_search_harness.runtime.artifacts.os.replace",
            side_effect=replace_with_metadata_failure,
        ):
            with self.assertRaisesRegex(OSError, "metadata publication"):
                self._publish("new report")

        self.assertEqual("new report", self.report_path.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ArtifactValidationError, "digest"):
            self.delivery.validate_delivery(self.run_id)
