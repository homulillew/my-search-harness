"""Provider-neutral source access authorization and accounting tests."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
from unittest import TestCase

from my_search_harness.domain import CompletionVerdict, SourceLocator
from my_search_harness.runtime import (
    CreateRunRequest,
    DeliveryCommands,
    JsonResearchRunRepository,
    LocalArtifactStore,
    PaperSearchHit,
    ResearchCommands,
    RevisionConflictError,
    SourceAccessAttemptError,
    SourceAccessFailureKind,
    SourceAccessProviderError,
    SourceAccessRejectedError,
    SourceAccessService,
    SourceContent,
    SourceOutline,
    SourceOutlineEntry,
)


class FakeSourceAccessProvider:
    def __init__(self) -> None:
        self.inspect_calls: list[tuple[str, object]] = []
        self.read_calls: list[tuple[str, object, SourceLocator | None]] = []
        self.validate_inspect_calls: list[object] = []
        self.validate_read_calls: list[tuple[object, SourceLocator | None]] = []
        self.preflight_failure: SourceAccessProviderError | None = None
        self.inspect_failure: Exception | None = None
        self.read_failure: Exception | None = None
        self.inspect_result: object | None = None
        self.read_result: object | None = None
        self.before_inspect: Callable[[], None] | None = None
        self.before_read: Callable[[], None] | None = None

    def validate_inspect(self, source) -> None:
        self.validate_inspect_calls.append(source)
        if self.preflight_failure is not None:
            raise self.preflight_failure

    def validate_read(self, source, locator: SourceLocator | None) -> None:
        self.validate_read_calls.append((source, locator))
        if self.preflight_failure is not None:
            raise self.preflight_failure

    def inspect_source(self, paper_ref: str, source) -> SourceOutline:
        self.inspect_calls.append((paper_ref, source))
        if self.before_inspect is not None:
            self.before_inspect()
        if self.inspect_failure is not None:
            raise self.inspect_failure
        if self.inspect_result is not None:
            return cast(SourceOutline, self.inspect_result)
        return SourceOutline(
            paper_ref=paper_ref,
            sections=(
                SourceOutlineEntry(
                    title="1 Introduction",
                    locator=SourceLocator(
                        kind="section",
                        value="1 Introduction",
                    ),
                ),
            ),
            total_tokens=1200,
        )

    def read_source(
        self,
        paper_ref: str,
        source,
        locator: SourceLocator | None,
    ) -> SourceContent:
        self.read_calls.append((paper_ref, source, locator))
        if self.before_read is not None:
            self.before_read()
        if self.read_failure is not None:
            raise self.read_failure
        if self.read_result is not None:
            return cast(SourceContent, self.read_result)
        return SourceContent(
            paper_ref=paper_ref,
            locator=locator,
            content="Primary paper content.",
        )


class SourceAccessServiceTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name) / "runs"
        self.repository = JsonResearchRunRepository(self.root)
        self.research = ResearchCommands(self.repository)
        created = self.research.create_run(
            CreateRunRequest(
                mission="Read a retained paper",
                requirements=("Understand the primary source",),
                scope="arXiv only",
                deliverable_description="Research state",
                required_artifacts=frozenset(),
            )
        )
        retained = self.research.retain_papers(
            created.run_id,
            created.state_revision,
            (
                PaperSearchHit(
                    title="A retained paper",
                    arxiv_id="2608.00001v2",
                ),
            ),
        )
        self.run_id = created.run_id
        self.paper_ref = retained.paper_refs[0]
        self.revision = retained.state_revision

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _state_bytes(self) -> bytes:
        return (self.root / self.run_id / "state.json").read_bytes()

    def _set_resource_limit(self, key: str, limit: int, usage: int = 0) -> int:
        current = self.repository.load(self.run_id)
        proposed = deepcopy(current)
        proposed.state_revision = current.state_revision + 1
        proposed.resources.limits[key] = limit
        proposed.resources.usage[key] = usage
        self.repository.save(proposed, current.state_revision)
        return proposed.state_revision

    def test_inspect_returns_ephemeral_outline_and_accounts_attempt(self) -> None:
        provider = FakeSourceAccessProvider()

        result = SourceAccessService(self.repository, provider).inspect_source(
            self.run_id,
            self.revision,
            self.paper_ref,
        )

        run = self.repository.load(self.run_id)
        self.assertEqual(self.revision + 1, result.state_revision)
        self.assertEqual(self.paper_ref, result.outline.paper_ref)
        self.assertEqual("1 Introduction", result.outline.sections[0].title)
        self.assertEqual(1, run.resources.usage["source_inspect_attempts"])
        self.assertIsNone(run.papers[self.paper_ref].analysis)
        self.assertEqual({}, run.literature_landscape.findings)
        self.assertEqual(1, len(provider.inspect_calls))

    def test_whole_source_read_has_minimum_provenance_and_is_not_persisted(
        self,
    ) -> None:
        provider = FakeSourceAccessProvider()

        result = SourceAccessService(self.repository, provider).read_source(
            self.run_id,
            self.revision,
            self.paper_ref,
        )

        self.assertEqual(self.revision + 1, result.state_revision)
        self.assertEqual(self.paper_ref, result.source_content.paper_ref)
        self.assertIsNone(result.source_content.locator)
        self.assertEqual("Primary paper content.", result.source_content.content)
        self.assertNotIn(b"Primary paper content.", self._state_bytes())
        run = self.repository.load(self.run_id)
        self.assertEqual(1, run.resources.usage["source_read_attempts"])
        self.assertIsNone(run.papers[self.paper_ref].analysis)

    def test_section_read_preserves_actual_locator(self) -> None:
        requested = SourceLocator(kind="section", value="Method")
        actual = SourceLocator(kind="section", value="3 Method")
        provider = FakeSourceAccessProvider()
        provider.read_result = SourceContent(
            paper_ref=self.paper_ref,
            locator=actual,
            content="The actual method section.",
        )

        result = SourceAccessService(self.repository, provider).read_source(
            self.run_id,
            self.revision,
            self.paper_ref,
            requested,
        )

        self.assertEqual(actual, result.source_content.locator)
        self.assertEqual(1, len(provider.read_calls))

    def test_attempt_is_persisted_before_inspect_provider_call(self) -> None:
        provider = FakeSourceAccessProvider()
        observed: list[tuple[int, int]] = []

        def observe() -> None:
            run = self.repository.load(self.run_id)
            observed.append(
                (run.state_revision, run.resources.usage["source_inspect_attempts"])
            )

        provider.before_inspect = observe

        SourceAccessService(self.repository, provider).inspect_source(
            self.run_id,
            self.revision,
            self.paper_ref,
        )

        self.assertEqual([(self.revision + 1, 1)], observed)

    def test_attempt_is_persisted_before_read_provider_call(self) -> None:
        provider = FakeSourceAccessProvider()
        observed: list[tuple[int, int]] = []

        def observe() -> None:
            run = self.repository.load(self.run_id)
            observed.append(
                (run.state_revision, run.resources.usage["source_read_attempts"])
            )

        provider.before_read = observe

        SourceAccessService(self.repository, provider).read_source(
            self.run_id,
            self.revision,
            self.paper_ref,
        )

        self.assertEqual([(self.revision + 1, 1)], observed)

    def test_provider_failures_are_accounted_and_keep_precise_kind(self) -> None:
        current_revision = self.revision
        for kind in SourceAccessFailureKind:
            with self.subTest(kind=kind):
                provider = FakeSourceAccessProvider()
                provider.read_failure = SourceAccessProviderError(kind, "fixture")

                with self.assertRaises(SourceAccessAttemptError) as captured:
                    SourceAccessService(self.repository, provider).read_source(
                        self.run_id,
                        current_revision,
                        self.paper_ref,
                    )

                current_revision += 1
                self.assertIs(kind, captured.exception.failure_kind)
                self.assertEqual(current_revision, captured.exception.state_revision)

        run = self.repository.load(self.run_id)
        self.assertEqual(4, run.resources.usage["source_read_attempts"])
        self.assertIsNone(run.papers[self.paper_ref].analysis)

    def test_unexpected_provider_failure_is_accounted_as_source_unavailable(
        self,
    ) -> None:
        provider = FakeSourceAccessProvider()
        provider.inspect_failure = RuntimeError("unexpected")

        with self.assertRaises(SourceAccessAttemptError) as captured:
            SourceAccessService(self.repository, provider).inspect_source(
                self.run_id,
                self.revision,
                self.paper_ref,
            )

        self.assertIs(
            SourceAccessFailureKind.SOURCE_UNAVAILABLE,
            captured.exception.failure_kind,
        )
        self.assertEqual(self.revision + 1, captured.exception.state_revision)

    def test_invalid_outline_contract_is_accounted_as_invalid_response(self) -> None:
        provider = FakeSourceAccessProvider()
        provider.inspect_result = SourceOutline(
            paper_ref="paper_wrong",
            sections=(),
        )

        with self.assertRaises(SourceAccessAttemptError) as captured:
            SourceAccessService(self.repository, provider).inspect_source(
                self.run_id,
                self.revision,
                self.paper_ref,
            )

        self.assertIs(
            SourceAccessFailureKind.INVALID_RESPONSE,
            captured.exception.failure_kind,
        )

    def test_empty_content_is_accounted_as_invalid_response(self) -> None:
        provider = FakeSourceAccessProvider()
        provider.read_result = SourceContent(
            paper_ref=self.paper_ref,
            content=" \n ",
        )

        with self.assertRaises(SourceAccessAttemptError) as captured:
            SourceAccessService(self.repository, provider).read_source(
                self.run_id,
                self.revision,
                self.paper_ref,
            )

        self.assertIs(
            SourceAccessFailureKind.INVALID_RESPONSE,
            captured.exception.failure_kind,
        )

    def test_stale_revision_rejects_without_preflight_or_attempt(self) -> None:
        provider = FakeSourceAccessProvider()
        before = self._state_bytes()

        with self.assertRaises(RevisionConflictError):
            SourceAccessService(self.repository, provider).inspect_source(
                self.run_id,
                99,
                self.paper_ref,
            )

        self.assertEqual([], provider.validate_inspect_calls)
        self.assertEqual([], provider.inspect_calls)
        self.assertEqual(before, self._state_bytes())

    def test_unretained_paper_rejects_without_attempt(self) -> None:
        provider = FakeSourceAccessProvider()
        before = self._state_bytes()

        with self.assertRaisesRegex(SourceAccessRejectedError, "not retained"):
            SourceAccessService(self.repository, provider).read_source(
                self.run_id,
                self.revision,
                "paper_00000000-0000-4000-8000-000000000000",
            )

        self.assertEqual([], provider.validate_read_calls)
        self.assertEqual([], provider.read_calls)
        self.assertEqual(before, self._state_bytes())

    def test_missing_provider_rejects_without_attempt(self) -> None:
        before = self._state_bytes()

        with self.assertRaisesRegex(SourceAccessRejectedError, "not configured"):
            SourceAccessService(self.repository, None).inspect_source(
                self.run_id,
                self.revision,
                self.paper_ref,
            )

        self.assertEqual(before, self._state_bytes())

    def test_invalid_locator_rejects_without_preflight_or_attempt(self) -> None:
        provider = FakeSourceAccessProvider()
        before = self._state_bytes()

        with self.assertRaisesRegex(SourceAccessRejectedError, "non-empty"):
            SourceAccessService(self.repository, provider).read_source(
                self.run_id,
                self.revision,
                self.paper_ref,
                SourceLocator(kind="section", value=" "),
            )

        self.assertEqual([], provider.validate_read_calls)
        self.assertEqual(before, self._state_bytes())

    def test_provider_preflight_failure_is_explicit_and_unaccounted(self) -> None:
        provider = FakeSourceAccessProvider()
        provider.preflight_failure = SourceAccessProviderError(
            SourceAccessFailureKind.UNSUPPORTED_LOCATOR,
            "unsupported",
        )
        before = self._state_bytes()

        with self.assertRaises(SourceAccessRejectedError) as captured:
            SourceAccessService(self.repository, provider).read_source(
                self.run_id,
                self.revision,
                self.paper_ref,
                SourceLocator(kind="table", value="Table 2"),
            )

        self.assertIs(
            SourceAccessFailureKind.UNSUPPORTED_LOCATOR,
            captured.exception.failure_kind,
        )
        self.assertEqual([], provider.read_calls)
        self.assertEqual(before, self._state_bytes())

    def test_exhausted_inspect_limit_rejects_without_provider_call(self) -> None:
        revision = self._set_resource_limit("source_inspect_attempts", 1, usage=1)
        provider = FakeSourceAccessProvider()
        before = self._state_bytes()

        with self.assertRaisesRegex(SourceAccessRejectedError, "exhausted"):
            SourceAccessService(self.repository, provider).inspect_source(
                self.run_id,
                revision,
                self.paper_ref,
            )

        self.assertEqual([], provider.inspect_calls)
        self.assertEqual(before, self._state_bytes())

    def test_exhausted_read_limit_rejects_without_provider_call(self) -> None:
        revision = self._set_resource_limit("source_read_attempts", 1, usage=1)
        provider = FakeSourceAccessProvider()
        before = self._state_bytes()

        with self.assertRaisesRegex(SourceAccessRejectedError, "exhausted"):
            SourceAccessService(self.repository, provider).read_source(
                self.run_id,
                revision,
                self.paper_ref,
            )

        self.assertEqual([], provider.read_calls)
        self.assertEqual(before, self._state_bytes())

    def test_completion_check_targeted_read_only_changes_resource_state(self) -> None:
        requested = self.research.request_completion_check(
            self.run_id,
            self.revision,
            "Existing research is ready for source verification",
        )
        before = self.repository.load(self.run_id)
        pending_before = deepcopy(
            before.completion_checks[requested.completion_check_ref]
        )

        result = SourceAccessService(
            self.repository,
            FakeSourceAccessProvider(),
        ).read_source(
            self.run_id,
            requested.state_revision,
            self.paper_ref,
            SourceLocator(kind="section", value="1 Introduction"),
        )

        after = self.repository.load(self.run_id)
        self.assertEqual(requested.state_revision + 1, result.state_revision)
        self.assertEqual(
            pending_before,
            after.completion_checks[requested.completion_check_ref],
        )
        self.assertEqual(before.papers, after.papers)
        self.assertEqual(before.literature_landscape, after.literature_landscape)
        self.assertEqual(before.investigation_gaps, after.investigation_gaps)

    def test_delivery_source_read_is_allowed(self) -> None:
        requested = self.research.request_completion_check(
            self.run_id,
            self.revision,
            "Ready",
        )
        submitted = self.research.submit_completion_check(
            self.run_id,
            requested.state_revision,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("All requirements are covered",),
        )

        result = SourceAccessService(
            self.repository,
            FakeSourceAccessProvider(),
        ).inspect_source(
            self.run_id,
            submitted.state_revision,
            self.paper_ref,
        )

        self.assertEqual(submitted.state_revision + 1, result.state_revision)

    def test_closed_run_rejects_source_access_without_attempt(self) -> None:
        requested = self.research.request_completion_check(
            self.run_id,
            self.revision,
            "Ready",
        )
        submitted = self.research.submit_completion_check(
            self.run_id,
            requested.state_revision,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("All requirements are covered",),
        )
        closed = DeliveryCommands(
            self.repository,
            LocalArtifactStore(self.root),
        ).close_run(self.run_id, submitted.state_revision)
        provider = FakeSourceAccessProvider()
        before = self._state_bytes()

        with self.assertRaisesRegex(SourceAccessRejectedError, "CLOSED"):
            SourceAccessService(self.repository, provider).read_source(
                self.run_id,
                closed.state_revision,
                self.paper_ref,
            )

        self.assertEqual([], provider.validate_read_calls)
        self.assertEqual([], provider.read_calls)
        self.assertEqual(before, self._state_bytes())
