"""Provider-neutral paper search authorization and accounting tests."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from my_search_harness.domain import (
    CompletionPassBasis,
    CompletionVerdict,
    LifecycleMode,
    RunOutcome,
)
from my_search_harness.runtime import (
    CreateRunRequest,
    JsonResearchRunRepository,
    PaperSearchAttemptError,
    PaperSearchHit,
    PaperSearchProviderError,
    PaperSearchRejectedError,
    PaperSearchService,
    ProviderFailureKind,
    ResearchCommands,
    RevisionConflictError,
)


class FakePaperSearchProvider:
    def __init__(
        self,
        *,
        hits: tuple[PaperSearchHit, ...] = (),
        failure: Exception | None = None,
    ) -> None:
        self.hits = hits
        self.failure = failure
        self.calls: list[tuple[str, int]] = []
        self.before_return: Callable[[], None] | None = None

    def search(self, query: str, *, limit: int) -> tuple[PaperSearchHit, ...]:
        self.calls.append((query, limit))
        if self.before_return is not None:
            self.before_return()
        if self.failure is not None:
            raise self.failure
        return self.hits


class PaperSearchServiceTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name) / "runs"
        self.repository = JsonResearchRunRepository(self.root)
        self.research = ResearchCommands(self.repository)
        created = self._create_run()
        self.run_id = created.run_id

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _create_run(self):
        return self.research.create_run(
            CreateRunRequest(
                mission="Search a bounded literature question",
                requirements=("Find candidate papers",),
                scope="arXiv only",
                deliverable_description="Research state",
                required_artifacts=frozenset(),
            )
        )

    def _state_bytes(self, run_id: str | None = None) -> bytes:
        return (self.root / (run_id or self.run_id) / "state.json").read_bytes()

    def _set_attempt_limit(self, limit: int, usage: int = 0) -> int:
        current = self.repository.load(self.run_id)
        proposed = deepcopy(current)
        proposed.state_revision = current.state_revision + 1
        proposed.resources.limits["paper_search_attempts"] = limit
        proposed.resources.usage["paper_search_attempts"] = usage
        self.repository.save(proposed, current.state_revision)
        return proposed.state_revision

    def _assert_accounted_failure(self, kind: ProviderFailureKind) -> None:
        provider = FakePaperSearchProvider(
            failure=PaperSearchProviderError(kind, "fixture failure")
        )
        service = PaperSearchService(self.repository, provider)

        with self.assertRaises(PaperSearchAttemptError) as captured:
            service.search_papers(self.run_id, 1, "agentic search")

        self.assertIs(captured.exception.failure_kind, kind)
        self.assertEqual(2, captured.exception.state_revision)
        run = self.repository.load(self.run_id)
        self.assertEqual(2, run.state_revision)
        self.assertEqual(1, run.resources.usage["paper_search_attempts"])
        self.assertEqual({}, run.papers)
        self.assertEqual({}, run.literature_landscape.findings)
        self.assertEqual([("agentic search", 10)], provider.calls)

    def test_valid_research_search_calls_provider_once_and_accounts_attempt(
        self,
    ) -> None:
        hit = PaperSearchHit(title="A paper", arxiv_id="2608.00001")
        provider = FakePaperSearchProvider(hits=(hit,))
        service = PaperSearchService(self.repository, provider)

        result = service.search_papers(
            self.run_id,
            1,
            "  agentic search  ",
            limit=3,
        )

        run = self.repository.load(self.run_id)
        self.assertEqual(2, result.state_revision)
        self.assertEqual((hit,), result.hits)
        self.assertEqual([("agentic search", 3)], provider.calls)
        self.assertEqual(2, run.state_revision)
        self.assertEqual(1, run.resources.usage["paper_search_attempts"])
        self.assertEqual({}, run.papers)
        self.assertEqual({}, run.literature_landscape.findings)

    def test_attempt_is_persisted_before_provider_is_invoked(self) -> None:
        provider = FakePaperSearchProvider()
        observed: list[tuple[int, int]] = []

        def observe_committed_state() -> None:
            run = self.repository.load(self.run_id)
            observed.append(
                (run.state_revision, run.resources.usage["paper_search_attempts"])
            )

        provider.before_return = observe_committed_state
        service = PaperSearchService(self.repository, provider)

        service.search_papers(self.run_id, 1, "retrieval systems")

        self.assertEqual([(2, 1)], observed)
        self.assertEqual(1, len(provider.calls))

    def test_empty_success_returns_no_hits_but_consumes_attempt(self) -> None:
        provider = FakePaperSearchProvider(hits=())

        result = PaperSearchService(self.repository, provider).search_papers(
            self.run_id, 1, "a query"
        )

        self.assertEqual((), result.hits)
        self.assertEqual(2, result.state_revision)
        self.assertEqual(
            1,
            self.repository.load(self.run_id).resources.usage["paper_search_attempts"],
        )

    def test_missing_local_limit_allows_multiple_accounted_attempts(self) -> None:
        provider = FakePaperSearchProvider()
        service = PaperSearchService(self.repository, provider)

        first = service.search_papers(self.run_id, 1, "first")
        second = service.search_papers(self.run_id, first.state_revision, "second")

        run = self.repository.load(self.run_id)
        self.assertEqual(3, second.state_revision)
        self.assertEqual(2, run.resources.usage["paper_search_attempts"])
        self.assertEqual(2, len(provider.calls))

    def test_invalid_query_is_rejected_without_call_or_state_change(self) -> None:
        for query in ("", " \n\t", None):
            with self.subTest(query=query):
                provider = FakePaperSearchProvider()
                before = self._state_bytes()

                with self.assertRaisesRegex(PaperSearchRejectedError, "query"):
                    PaperSearchService(self.repository, provider).search_papers(
                        self.run_id,
                        1,
                        query,  # type: ignore[arg-type]
                    )

                self.assertEqual([], provider.calls)
                self.assertEqual(before, self._state_bytes())

    def test_invalid_limit_is_rejected_without_call_or_state_change(self) -> None:
        for limit in (0, 101, True, 1.5):
            with self.subTest(limit=limit):
                provider = FakePaperSearchProvider()
                before = self._state_bytes()

                with self.assertRaisesRegex(PaperSearchRejectedError, "limit"):
                    PaperSearchService(self.repository, provider).search_papers(
                        self.run_id,
                        1,
                        "query",
                        limit=limit,  # type: ignore[arg-type]
                    )

                self.assertEqual([], provider.calls)
                self.assertEqual(before, self._state_bytes())

    def test_stale_revision_is_rejected_without_call_or_state_change(self) -> None:
        provider = FakePaperSearchProvider()
        before = self._state_bytes()

        with self.assertRaises(RevisionConflictError):
            PaperSearchService(self.repository, provider).search_papers(
                self.run_id, 99, "query"
            )

        self.assertEqual([], provider.calls)
        self.assertEqual(before, self._state_bytes())

    def test_exhausted_local_limit_rejects_without_call_or_state_change(self) -> None:
        revision = self._set_attempt_limit(limit=1, usage=1)
        provider = FakePaperSearchProvider()
        before = self._state_bytes()

        with self.assertRaisesRegex(PaperSearchRejectedError, "exhausted"):
            PaperSearchService(self.repository, provider).search_papers(
                self.run_id, revision, "query"
            )

        self.assertEqual([], provider.calls)
        self.assertEqual(before, self._state_bytes())

    def test_available_local_limit_allows_exactly_one_attempt(self) -> None:
        revision = self._set_attempt_limit(limit=2, usage=1)
        provider = FakePaperSearchProvider()

        result = PaperSearchService(self.repository, provider).search_papers(
            self.run_id, revision, "query"
        )

        run = self.repository.load(self.run_id)
        self.assertEqual(revision + 1, result.state_revision)
        self.assertEqual(2, run.resources.usage["paper_search_attempts"])

    def test_missing_provider_rejects_without_state_change(self) -> None:
        before = self._state_bytes()

        with self.assertRaisesRegex(PaperSearchRejectedError, "not configured"):
            PaperSearchService(self.repository, None).search_papers(
                self.run_id, 1, "query"
            )

        self.assertEqual(before, self._state_bytes())

    def test_completion_check_lifecycle_rejects_without_provider_call(self) -> None:
        requested = self.research.request_completion_check(
            self.run_id, 1, "Ready to check"
        )
        provider = FakePaperSearchProvider()
        before = self._state_bytes()

        with self.assertRaisesRegex(PaperSearchRejectedError, "RESEARCH"):
            PaperSearchService(self.repository, provider).search_papers(
                self.run_id, requested.state_revision, "query"
            )

        self.assertEqual([], provider.calls)
        self.assertEqual(before, self._state_bytes())

    def test_delivery_lifecycle_rejects_without_provider_call(self) -> None:
        requested = self.research.request_completion_check(
            self.run_id, 1, "Ready to check"
        )
        delivered = self.research.submit_completion_check(
            self.run_id,
            requested.state_revision,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("Complete",),
        )
        provider = FakePaperSearchProvider()
        before = self._state_bytes()

        with self.assertRaisesRegex(PaperSearchRejectedError, "RESEARCH"):
            PaperSearchService(self.repository, provider).search_papers(
                self.run_id, delivered.state_revision, "query"
            )

        self.assertEqual([], provider.calls)
        self.assertEqual(before, self._state_bytes())

    def test_closed_lifecycle_rejects_without_provider_call(self) -> None:
        requested = self.research.request_completion_check(
            self.run_id, 1, "Ready to check"
        )
        delivered = self.research.submit_completion_check(
            self.run_id,
            requested.state_revision,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("Complete",),
        )
        current = self.repository.load(self.run_id)
        proposed = deepcopy(current)
        proposed.state_revision = delivered.state_revision + 1
        proposed.lifecycle = LifecycleMode.CLOSED
        proposed.outcome = RunOutcome.COMPLETE
        assert isinstance(proposed.delivery_basis, CompletionPassBasis)
        self.repository.save(proposed, delivered.state_revision)
        provider = FakePaperSearchProvider()
        before = self._state_bytes()

        with self.assertRaisesRegex(PaperSearchRejectedError, "RESEARCH"):
            PaperSearchService(self.repository, provider).search_papers(
                self.run_id, proposed.state_revision, "query"
            )

        self.assertEqual([], provider.calls)
        self.assertEqual(before, self._state_bytes())

    def test_authentication_failure_is_accounted_and_explicit(self) -> None:
        self._assert_accounted_failure(ProviderFailureKind.AUTHENTICATION)

    def test_rate_limit_failure_is_accounted_and_explicit(self) -> None:
        self._assert_accounted_failure(ProviderFailureKind.RATE_LIMIT)

    def test_server_failure_is_accounted_and_explicit(self) -> None:
        self._assert_accounted_failure(ProviderFailureKind.UNAVAILABLE)

    def test_invalid_response_failure_is_accounted_and_explicit(self) -> None:
        self._assert_accounted_failure(ProviderFailureKind.INVALID_RESPONSE)

    def test_unexpected_provider_failure_is_accounted_as_other(self) -> None:
        provider = FakePaperSearchProvider(failure=RuntimeError("SDK leak"))
        service = PaperSearchService(self.repository, provider)

        with self.assertRaises(PaperSearchAttemptError) as captured:
            service.search_papers(self.run_id, 1, "query")

        self.assertIs(captured.exception.failure_kind, ProviderFailureKind.OTHER)
        self.assertEqual(2, captured.exception.state_revision)
        self.assertIsNone(captured.exception.__cause__)
        self.assertEqual(1, len(provider.calls))

    def test_provider_contract_violation_is_accounted_as_invalid_response(self) -> None:
        provider = FakePaperSearchProvider()
        provider.hits = []  # type: ignore[assignment]

        with self.assertRaises(PaperSearchAttemptError) as captured:
            PaperSearchService(self.repository, provider).search_papers(
                self.run_id, 1, "query"
            )

        self.assertIs(
            captured.exception.failure_kind,
            ProviderFailureKind.INVALID_RESPONSE,
        )
        self.assertEqual(2, captured.exception.state_revision)
        self.assertEqual(1, len(provider.calls))
