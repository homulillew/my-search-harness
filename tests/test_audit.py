"""Append-only audit behavior and state-authority ordering tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from my_search_harness.domain import (
    ArtifactKind,
    CompletionVerdict,
    PaperAnalysis,
    PaperSource,
    SourceLocator,
)
from my_search_harness.runtime import (
    AuditAppendError,
    AuditEvent,
    AuditReadError,
    CompletionCheckDecision,
    CompletionCheckRuntime,
    CreateRunRequest,
    DeliveryCommands,
    JsonResearchRunRepository,
    LocalArtifactStore,
    LocalAuditLog,
    PaperSearchAttemptError,
    PaperSearchHit,
    PaperSearchProviderError,
    PaperSearchRejectedError,
    ProviderFailureKind,
    PutPaperAnalysis,
    ResearchCommands,
    ResearchMutationBatch,
    RunNotFoundError,
    SourceContent,
    SourceOutline,
    SourceOutlineEntry,
    build_runtime_capabilities,
)


class FakeProvider:
    def search(
        self,
        query: str,
        *,
        limit: int,
        offset: int = 0,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[PaperSearchHit, ...]:
        return (
            PaperSearchHit(
                title="Audited paper",
                arxiv_id="2608.00020",
            ),
        )


class FailingProvider:
    def search(
        self,
        query: str,
        *,
        limit: int,
        offset: int = 0,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[PaperSearchHit, ...]:
        raise PaperSearchProviderError(
            ProviderFailureKind.RATE_LIMIT,
            "fixture rate limit",
        )


class FakeSourceProvider:
    def validate_inspect(self, source: PaperSource) -> None:
        return None

    def validate_read(
        self,
        source: PaperSource,
        locator: SourceLocator | None,
    ) -> None:
        return None

    def inspect_source(self, paper_ref: str, source: PaperSource) -> SourceOutline:
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
        return SourceContent(
            paper_ref=paper_ref,
            locator=locator,
            content="Sensitive primary content must not enter audit",
        )


class PassingChecker:
    def evaluate(self, view, evidence):
        return CompletionCheckDecision(
            verdict=CompletionVerdict.PASS,
            reasons=("Audited state is sufficient",),
        )


class CheckerFactory:
    def create(self):
        return PassingChecker()


class FailingAuditSink:
    def append(self, event: AuditEvent) -> None:
        raise OSError("simulated audit disk failure")


class AuditTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name) / "runs"
        self.repository = JsonResearchRunRepository(self.root)
        self.artifacts = LocalArtifactStore(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _request(self) -> CreateRunRequest:
        return CreateRunRequest(
            mission="Audit a run",
            requirements=("Exercise operational events",),
            scope="A deterministic fixture",
            deliverable_description="An audited report",
            required_artifacts=frozenset({ArtifactKind.REPORT}),
        )

    def test_full_runtime_appends_expected_operational_actions(self) -> None:
        capabilities = build_runtime_capabilities(
            self.repository,
            self.artifacts,
            paper_search_provider=FakeProvider(),
            source_access_provider=FakeSourceProvider(),
        )
        created = capabilities.researcher.create_run(self._request())
        searched = capabilities.researcher.search_papers(
            created.run_id,
            created.state_revision,
            "historical query strategy",
            limit=7,
            offset=14,
            date_from="2025-01-01",
            date_to="2026-08-10",
        )
        retained = capabilities.researcher.retain_papers(
            created.run_id,
            searched.state_revision,
            searched.hits,
        )
        read = capabilities.researcher.read_source(
            created.run_id,
            retained.state_revision,
            retained.paper_refs[0],
        )
        mutated = capabilities.researcher.apply_research_mutation(
            created.run_id,
            read.state_revision,
            ResearchMutationBatch(
                puts=(
                    PutPaperAnalysis(
                        paper_ref=retained.paper_refs[0],
                        analysis=PaperAnalysis(
                            summary="Accepted semantic summary",
                            relevance_to_run="Directly relevant",
                        ),
                    ),
                )
            ),
        )
        gap = capabilities.researcher.put_investigation_gap(
            created.run_id,
            mutated.state_revision,
            description="Temporary gap",
        )
        resolved = capabilities.researcher.resolve_investigation_gap(
            created.run_id,
            gap.state_revision,
            gap.entity_ref,
            "Resolved",
        )
        reopened = capabilities.researcher.reopen_investigation_gap(
            created.run_id,
            resolved.state_revision,
            gap.entity_ref,
        )
        completion = CompletionCheckRuntime.from_capabilities(capabilities)
        completed = completion.request_and_run(
            created.run_id,
            reopened.state_revision,
            "Ready",
            CheckerFactory(),
        )
        capabilities.delivery.publish_report(
            created.run_id,
            completed.state_revision,
            "# Audited report\n\nNo audit payload should copy this prose.",
        )
        capabilities.delivery.close_run(created.run_id, completed.state_revision)

        events = LocalAuditLog(self.root).read(created.run_id)
        actions = [event.action for event in events]

        self.assertEqual(
            [
                "run_created",
                "paper_search_attempt",
                "papers_retained",
                "source_read_attempt",
                "research_mutation",
                "investigation_gap_maintained",
                "investigation_gap_resolved",
                "investigation_gap_reopened",
                "completion_check_requested",
                "completion_check_submitted",
                "report_published",
                "run_closed",
            ],
            actions,
        )
        event_text = (self.root / created.run_id / "events.jsonl").read_text()
        self.assertIn("historical query strategy", event_text)
        self.assertNotIn("Sensitive primary content", event_text)
        self.assertNotIn("No audit payload should copy", event_text)
        self.assertEqual(
            {
                "query": "historical query strategy",
                "limit": 7,
                "offset": 14,
                "date_from": "2025-01-01",
                "date_to": "2026-08-10",
                "hit_count": 1,
            },
            events[1].details,
        )
        self.assertEqual("SUCCESS", events[1].provider_outcome)

    def test_provider_failure_is_accounted_and_audited_distinctly(self) -> None:
        capabilities = build_runtime_capabilities(
            self.repository,
            self.artifacts,
            paper_search_provider=FailingProvider(),
            source_access_provider=None,
        )
        created = capabilities.researcher.create_run(self._request())

        with self.assertRaises(PaperSearchAttemptError):
            capabilities.researcher.search_papers(
                created.run_id,
                created.state_revision,
                "rate limited query",
                limit=9,
                offset=18,
                date_from="2025-01-01",
            )

        run = self.repository.load(created.run_id)
        events = LocalAuditLog(self.root).read(created.run_id)
        failure = events[-1]
        self.assertEqual(created.state_revision + 1, run.state_revision)
        self.assertEqual(1, run.resources.usage["paper_search_attempts"])
        self.assertEqual("paper_search_attempt", failure.action)
        self.assertEqual("FAILURE", failure.outcome)
        self.assertEqual("RATE_LIMIT", failure.provider_outcome)
        self.assertEqual(
            {
                "query": "rate limited query",
                "limit": 9,
                "offset": 18,
                "date_from": "2025-01-01",
            },
            failure.details,
        )

    def test_local_rejection_creates_no_attempt_event(self) -> None:
        capabilities = build_runtime_capabilities(
            self.repository,
            self.artifacts,
            paper_search_provider=FakeProvider(),
            source_access_provider=None,
        )
        created = capabilities.researcher.create_run(self._request())

        with self.assertRaises(PaperSearchRejectedError):
            capabilities.researcher.search_papers(
                created.run_id,
                created.state_revision,
                "",
            )

        events = LocalAuditLog(self.root).read(created.run_id)
        self.assertEqual(("run_created",), tuple(event.action for event in events))
        self.assertEqual({}, self.repository.load(created.run_id).resources.usage)

    def test_invalid_local_date_range_creates_no_attempt_event(self) -> None:
        capabilities = build_runtime_capabilities(
            self.repository,
            self.artifacts,
            paper_search_provider=FakeProvider(),
            source_access_provider=None,
        )
        created = capabilities.researcher.create_run(self._request())

        with self.assertRaises(PaperSearchRejectedError):
            capabilities.researcher.search_papers(
                created.run_id,
                created.state_revision,
                "invalid range",
                date_from="2026-01-01",
                date_to="2025-01-01",
            )

        events = LocalAuditLog(self.root).read(created.run_id)
        self.assertEqual(("run_created",), tuple(event.action for event in events))
        self.assertEqual({}, self.repository.load(created.run_id).resources.usage)

    def test_audit_append_failure_does_not_rollback_committed_state(self) -> None:
        commands = ResearchCommands(self.repository)
        created = commands.create_run(self._request())
        audited_commands = ResearchCommands(self.repository, FailingAuditSink())

        with self.assertRaises(AuditAppendError) as raised:
            audited_commands.retain_papers(
                created.run_id,
                created.state_revision,
                (PaperSearchHit(title="Committed paper", doi="10.1000/audit"),),
            )

        run = self.repository.load(created.run_id)
        self.assertEqual(2, run.state_revision)
        self.assertEqual(1, len(run.papers))
        self.assertEqual("papers_retained", raised.exception.event.action)
        self.assertEqual(2, raised.exception.event.state_revision)

    def test_audit_failure_after_artifact_publish_keeps_artifact(self) -> None:
        commands = ResearchCommands(self.repository)
        created = commands.create_run(self._request())
        requested = commands.request_completion_check(
            created.run_id,
            created.state_revision,
            "Ready",
        )
        completed = commands.submit_completion_check(
            created.run_id,
            requested.state_revision,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("Complete",),
        )
        delivery = DeliveryCommands(
            self.repository,
            self.artifacts,
            FailingAuditSink(),
        )
        with self.assertRaises(AuditAppendError):
            delivery.publish_report(
                created.run_id,
                completed.state_revision,
                "# Persisted report",
            )

        report_path = self.root / created.run_id / "artifacts" / "report.md"
        self.assertEqual("# Persisted report", report_path.read_text())
        self.assertEqual(
            completed.state_revision,
            self.repository.load(created.run_id).state_revision,
        )

    def test_state_load_and_context_do_not_need_events_file(self) -> None:
        capabilities = build_runtime_capabilities(
            self.repository,
            self.artifacts,
            paper_search_provider=None,
            source_access_provider=None,
        )
        created = capabilities.researcher.create_run(self._request())
        event_path = self.root / created.run_id / "events.jsonl"
        event_path.unlink()

        self.assertEqual(created.run_id, self.repository.load(created.run_id).id)
        self.assertEqual(
            created.state_revision,
            capabilities.researcher.view(created.run_id).state_revision,
        )

    def test_events_cannot_reconstruct_missing_authoritative_state(self) -> None:
        capabilities = build_runtime_capabilities(
            self.repository,
            self.artifacts,
            paper_search_provider=None,
            source_access_provider=None,
        )
        created = capabilities.researcher.create_run(self._request())
        state_path = self.root / created.run_id / "state.json"
        state_path.unlink()

        self.assertTrue((self.root / created.run_id / "events.jsonl").is_file())
        with self.assertRaises(RunNotFoundError):
            self.repository.load(created.run_id)

    def test_corrupt_audit_does_not_corrupt_state_but_diagnostic_read_fails(
        self,
    ) -> None:
        capabilities = build_runtime_capabilities(
            self.repository,
            self.artifacts,
            paper_search_provider=None,
            source_access_provider=None,
        )
        created = capabilities.researcher.create_run(self._request())
        event_path = self.root / created.run_id / "events.jsonl"
        event_path.write_text("not-json\n", encoding="utf-8")

        self.assertEqual(created.run_id, self.repository.load(created.run_id).id)
        with self.assertRaises(AuditReadError):
            LocalAuditLog(self.root).read(created.run_id)

    def test_local_log_is_append_only_across_events(self) -> None:
        commands = ResearchCommands(self.repository)
        created = commands.create_run(self._request())
        log = LocalAuditLog(self.root)
        first = AuditEvent(
            run_id=created.run_id,
            state_revision=1,
            actor="test",
            action="first",
        )
        second = AuditEvent(
            run_id=created.run_id,
            state_revision=1,
            actor="test",
            action="second",
        )
        log.append(first)
        first_bytes = (self.root / created.run_id / "events.jsonl").read_bytes()
        log.append(second)
        final_bytes = (self.root / created.run_id / "events.jsonl").read_bytes()

        self.assertTrue(final_bytes.startswith(first_bytes))
        self.assertEqual(
            ("first", "second"),
            tuple(event.action for event in log.read(created.run_id)),
        )
