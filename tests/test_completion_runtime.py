"""Fresh-checker orchestration, crash recovery, and authority tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from my_search_harness.domain import (
    CompletionVerdict,
    LifecycleMode,
    PaperSource,
    SourceLocator,
)
from my_search_harness.runtime import (
    CompletionCheckDecision,
    CompletionCheckRuntime,
    CompletionOrchestrationError,
    CreateRunRequest,
    JsonResearchRunRepository,
    LocalArtifactStore,
    NewBlockingGap,
    PaperSearchHit,
    SourceContent,
    SourceAccessAttemptError,
    SourceAccessFailureKind,
    SourceAccessProviderError,
    SourceOutline,
    SourceOutlineEntry,
    build_runtime_capabilities,
)


class FakeSourceAccessProvider:
    def __init__(self, *, fail_read: bool = False) -> None:
        self.fail_read = fail_read

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
        if self.fail_read:
            raise SourceAccessProviderError(
                SourceAccessFailureKind.SOURCE_UNAVAILABLE,
                "fixture source unavailable",
            )
        return SourceContent(
            paper_ref=paper_ref,
            locator=locator,
            content="Primary evidence",
        )


class StaticFactory:
    def __init__(self, runner) -> None:
        self.runner = runner
        self.create_count = 0

    def create(self):
        self.create_count += 1
        return self.runner


class CompletionRuntimeTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name) / "runs"
        self.repository = JsonResearchRunRepository(self.root)
        self.capabilities = build_runtime_capabilities(
            self.repository,
            LocalArtifactStore(self.root),
            paper_search_provider=None,
            source_access_provider=FakeSourceAccessProvider(),
        )
        self.runtime = CompletionCheckRuntime.from_capabilities(self.capabilities)
        self.created = self.capabilities.researcher.create_run(
            CreateRunRequest(
                mission="Verify a fresh checker",
                requirements=("Verify evidence",),
                scope="A deterministic fixture",
                deliverable_description="A report",
            )
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _retain(self):
        return self.capabilities.researcher.retain_papers(
            self.created.run_id,
            self.created.state_revision,
            (PaperSearchHit(title="Evidence", arxiv_id="2608.00001"),),
        )

    def test_request_is_persisted_before_fresh_checker_starts(self) -> None:
        repository = self.repository
        run_id = self.created.run_id

        class PersistenceAssertingRunner:
            def evaluate(self, view, evidence):
                run = repository.load(run_id)
                self.persisted = (
                    run.lifecycle is LifecycleMode.COMPLETION_CHECK
                    and view.completion_check_ref in run.completion_checks
                    and run.completion_checks[view.completion_check_ref].completed_at
                    is None
                )
                return CompletionCheckDecision(
                    verdict=CompletionVerdict.PASS,
                    reasons=("Persisted baseline is sufficient",),
                )

        runner = PersistenceAssertingRunner()
        factory = StaticFactory(runner)
        result = self.runtime.request_and_run(
            run_id,
            self.created.state_revision,
            "Ready for an independent check",
            factory,
        )

        self.assertTrue(runner.persisted)
        self.assertEqual(1, factory.create_count)
        self.assertIs(result.verdict, CompletionVerdict.PASS)
        self.assertIs(self.repository.load(run_id).lifecycle, LifecycleMode.DELIVERY)

    def test_crash_leaves_pending_check_and_resume_creates_new_runner(self) -> None:
        repository = self.repository
        run_id = self.created.run_id

        class CrashRunner:
            def evaluate(self, view, evidence):
                raise RuntimeError("simulated semantic runner crash")

        class RecoveryRunner:
            def evaluate(self, view, evidence):
                return CompletionCheckDecision(
                    verdict=CompletionVerdict.PASS,
                    reasons=("Recovered with a fresh checker",),
                )

        class SequencedFactory:
            def __init__(self) -> None:
                self.instances: list[object] = []

            def create(self):
                runner = CrashRunner() if not self.instances else RecoveryRunner()
                self.instances.append(runner)
                return runner

        factory = SequencedFactory()
        with self.assertRaisesRegex(RuntimeError, "simulated"):
            self.runtime.request_and_run(
                run_id,
                self.created.state_revision,
                "Persist before crash",
                factory,
            )

        pending = repository.load(run_id)
        pending_check = next(iter(pending.completion_checks.values()))
        self.assertIs(pending.lifecycle, LifecycleMode.COMPLETION_CHECK)
        self.assertIsNone(pending_check.completed_at)

        result = self.runtime.resume_pending(run_id, factory)

        self.assertEqual(2, len(factory.instances))
        self.assertIsNot(factory.instances[0], factory.instances[1])
        self.assertIs(result.verdict, CompletionVerdict.PASS)

    def test_targeted_read_advances_resource_revision_without_changing_request(
        self,
    ) -> None:
        retained = self._retain()
        run_id = self.created.run_id

        class ReadingRunner:
            def evaluate(self, view, evidence):
                self.initial_revision = evidence.state_revision
                read = evidence.read_source(
                    retained.paper_refs[0],
                    SourceLocator(kind="section", value="Results"),
                )
                self.read_revision = read.state_revision
                self.has_broad_search = hasattr(evidence, "search_papers")
                self.has_retain = hasattr(evidence, "retain_papers")
                self.has_submit = hasattr(evidence, "submit_completion_check")
                return CompletionCheckDecision(
                    verdict=CompletionVerdict.PASS,
                    reasons=("Targeted primary evidence confirms the state",),
                )

        runner = ReadingRunner()
        result = self.runtime.request_and_run(
            run_id,
            retained.state_revision,
            "Inspect one retained source",
            StaticFactory(runner),
        )
        run = self.repository.load(run_id)
        check = run.completion_checks[result.completion_check_ref]

        self.assertEqual(runner.initial_revision + 1, runner.read_revision)
        self.assertEqual(runner.read_revision + 1, result.state_revision)
        self.assertEqual(runner.initial_revision, check.basis_revision)
        self.assertEqual("Inspect one retained source", check.requester_rationale)
        self.assertEqual(1, run.resources.usage["source_read_attempts"])
        self.assertFalse(runner.has_broad_search)
        self.assertFalse(runner.has_retain)
        self.assertFalse(runner.has_submit)

    def test_continue_decision_uses_typed_gap_and_returns_to_research(self) -> None:
        requirement_ref = self.created.requirement_refs[0]

        class ContinueRunner:
            def evaluate(self, view, evidence):
                return CompletionCheckDecision(
                    verdict=CompletionVerdict.CONTINUE,
                    reasons=("One requirement is not yet grounded",),
                    blocking_gaps=(
                        NewBlockingGap(
                            description="Ground the remaining requirement",
                            requirement_refs=frozenset({requirement_ref}),
                        ),
                    ),
                )

        result = self.runtime.request_and_run(
            self.created.run_id,
            self.created.state_revision,
            "Check current coverage",
            StaticFactory(ContinueRunner()),
        )
        run = self.repository.load(self.created.run_id)

        self.assertIs(result.verdict, CompletionVerdict.CONTINUE)
        self.assertEqual(1, len(result.blocking_gap_refs))
        self.assertIs(run.lifecycle, LifecycleMode.RESEARCH)

    def test_caught_source_failure_keeps_latest_accounted_revision_for_submit(
        self,
    ) -> None:
        capabilities = build_runtime_capabilities(
            self.repository,
            LocalArtifactStore(self.root),
            paper_search_provider=None,
            source_access_provider=FakeSourceAccessProvider(fail_read=True),
        )
        runtime = CompletionCheckRuntime.from_capabilities(capabilities)
        retained = self._retain()
        paper_ref = retained.paper_refs[0]

        class FailureAwareRunner:
            def evaluate(self, view, evidence):
                try:
                    evidence.read_source(paper_ref)
                except SourceAccessAttemptError as exc:
                    self.attempted_revision = exc.state_revision
                return CompletionCheckDecision(
                    verdict=CompletionVerdict.CONTINUE,
                    reasons=("Required evidence was unavailable",),
                    blocking_gaps=(
                        NewBlockingGap(description="Retry the unavailable source"),
                    ),
                )

        runner = FailureAwareRunner()
        result = runtime.request_and_run(
            self.created.run_id,
            retained.state_revision,
            "Verify unavailable evidence",
            StaticFactory(runner),
        )

        self.assertEqual(runner.attempted_revision + 1, result.state_revision)
        self.assertEqual(
            1,
            self.repository.load(self.created.run_id).resources.usage[
                "source_read_attempts"
            ],
        )

    def test_invalid_runner_result_leaves_recoverable_pending_check(self) -> None:
        class InvalidRunner:
            def evaluate(self, view, evidence):
                return {"verdict": "PASS"}

        with self.assertRaises(CompletionOrchestrationError):
            self.runtime.request_and_run(
                self.created.run_id,
                self.created.state_revision,
                "Invalid runner fixture",
                StaticFactory(InvalidRunner()),
            )

        run = self.repository.load(self.created.run_id)
        self.assertIs(run.lifecycle, LifecycleMode.COMPLETION_CHECK)
        self.assertEqual(1, len(run.completion_checks))
        self.assertIsNone(next(iter(run.completion_checks.values())).completed_at)

    def test_completion_runtime_does_not_persist_checker_session_state(self) -> None:
        class PassRunner:
            def evaluate(self, view, evidence):
                return CompletionCheckDecision(
                    verdict=CompletionVerdict.PASS,
                    reasons=("Sufficient",),
                )

        self.runtime.request_and_run(
            self.created.run_id,
            self.created.state_revision,
            "No session entity",
            StaticFactory(PassRunner()),
        )
        state_text = (self.root / self.created.run_id / "state.json").read_text()

        self.assertNotIn("checker_session", state_text)
        self.assertNotIn("completion_score", state_text)
