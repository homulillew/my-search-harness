"""Report pipeline orchestration without embedding semantic judgment in Python."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from my_search_harness.domain import (
    ArtifactKind,
    CompletionVerdict,
    LifecycleMode,
    PaperSource,
    SourceLocator,
)
from my_search_harness.runtime import (
    CitationReference,
    CompletionCheckDecision,
    CompletionCheckRuntime,
    CreateRunRequest,
    EditorialIssue,
    EditorialReview,
    IntegrityDisposition,
    JsonResearchRunRepository,
    LocalArtifactStore,
    NarrativePlan,
    NarrativeSection,
    PaperSearchHit,
    PublishedReportPipelineResult,
    ReportManuscript,
    ReportPipeline,
    ReportPipelineError,
    ReportResearchReopenedResult,
    ReportRevisionRequiredError,
    ReportWritingGuideLoadError,
    ResearchEscalationRequired,
    ResearchIntegrityReview,
    SourceContent,
    SourceOutline,
    SourceOutlineEntry,
    build_runtime_capabilities,
    load_report_writing_guide,
)


class FakeSourceAccessProvider:
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
            content="Primary evidence for integrity review",
        )


class PassingChecker:
    def evaluate(self, view, evidence):
        return CompletionCheckDecision(
            verdict=CompletionVerdict.PASS,
            reasons=("Research state is sufficient",),
        )


class StaticCheckerFactory:
    def create(self):
        return PassingChecker()


class RecordingPlanner:
    def __init__(self, calls: list[str], paper_ref: str) -> None:
        self.calls = calls
        self.paper_ref = paper_ref

    def plan(self, view, writing_guideline):
        self.calls.append("plan")
        return NarrativePlan(
            audience="Technical readers",
            reader_takeaway="Understand the central result",
            sections=(
                NarrativeSection(
                    title="Main result",
                    purpose="Explain the accepted finding",
                    research_refs=(self.paper_ref,),
                ),
            ),
            terminology=(("Method", "Method"),),
        )


class RecordingComposer:
    def __init__(self, calls: list[str], paper_ref: str) -> None:
        self.calls = calls
        self.paper_ref = paper_ref
        self.inspected_kind: str | None = None

    def compose(self, view, plan, writing_guideline, evidence):
        self.calls.append("compose")
        inspected = evidence.inspect((self.paper_ref,))
        self.inspected_kind = inspected.objects[0].kind
        return ReportManuscript(
            markdown="# Draft\n\nA grounded statement {{cite:main}}.",
            citations=(
                CitationReference(
                    citation_id="main",
                    paper_ref=self.paper_ref,
                    locator=SourceLocator(kind="section", value="Results"),
                ),
            ),
        )


class RecordingIntegrator:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def integrate(self, view, plan, manuscript, writing_guideline, evidence):
        self.calls.append("integrate")
        return ReportManuscript(
            markdown=manuscript.markdown.replace("Draft", "Integrated"),
            citations=manuscript.citations,
        )


class RecordingEditor:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self.deliverable: str | None = None

    def review(self, deliverable, plan, writing_guideline, manuscript):
        self.calls.append("fresh_review")
        self.deliverable = deliverable
        return EditorialReview(
            issues=(
                EditorialIssue(
                    description="Use a more direct opening",
                    location="Introduction",
                ),
            )
        )


class RecordingEditorFactory:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self.instances: list[RecordingEditor] = []

    def create(self):
        self.calls.append("create_fresh_editor")
        editor = RecordingEditor(self.calls)
        self.instances.append(editor)
        return editor


class RecordingReviser:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def revise(
        self,
        view,
        plan,
        manuscript,
        review,
        writing_guideline,
        evidence,
    ):
        self.calls.append("revise")
        return ReportManuscript(
            markdown=manuscript.markdown.replace("Integrated", "Final"),
            citations=manuscript.citations,
        )


class RecordingIntegrityReviewer:
    def __init__(
        self,
        calls: list[str],
        disposition: IntegrityDisposition = IntegrityDisposition.PASS,
        *,
        read_paper_ref: str | None = None,
    ) -> None:
        self.calls = calls
        self.disposition = disposition
        self.read_paper_ref = read_paper_ref
        self.read_revision: int | None = None

    def review(self, view, manuscript, evidence):
        self.calls.append("integrity")
        if self.read_paper_ref is not None:
            read = evidence.read_source(
                self.read_paper_ref,
                SourceLocator(kind="section", value="Results"),
            )
            self.read_revision = read.state_revision
        issues = (
            ()
            if self.disposition is IntegrityDisposition.PASS
            else ("The authoritative research semantics need correction",)
        )
        return ResearchIntegrityReview(
            disposition=self.disposition,
            issues=issues,
        )


class RecordingRenderer:
    def __init__(self, calls: list[str], content: str = "# Report\n\nRendered [1]."):
        self.calls = calls
        self.content = content

    def render(self, view, manuscript):
        self.calls.append("render_citations")
        return self.content


class ReportWritingGuideLoaderTests(TestCase):
    def test_authoritative_guide_loads_verbatim_as_utf8(self) -> None:
        guide_path = (
            Path(__file__).parents[1]
            / ".claude"
            / "skills"
            / "literature-research"
            / "references"
            / "REPORT_WRITING_GUIDE.md"
        )

        guideline = load_report_writing_guide(guide_path)

        self.assertEqual(guide_path.read_text(encoding="utf-8"), guideline)
        self.assertIn("普通概念优先使用中文", guideline)
        self.assertIn("一个段落通常只完成一个主要论证任务", guideline)
        self.assertIn("第一次正式介绍该方法名称", guideline)
        self.assertIn("方法超链接只提供导航，不替代 structured citation", guideline)
        self.assertIn("领域技术路线报告不应只停留在路线名称层", guideline)

    def test_curated_regression_links_methods_without_replacing_citations(
        self,
    ) -> None:
        example_path = (
            Path(__file__).parents[1]
            / "examples"
            / "speculative-decoding-guide-regression.md"
        )
        example = example_path.read_text(encoding="utf-8")

        expected_pairs = (
            ("https://arxiv.org/abs/2211.17192", "[1, section:"),
            ("https://arxiv.org/abs/2311.08981", "[2, section:"),
            ("https://arxiv.org/abs/2502.01662", "[3, section:"),
        )
        for canonical_url, citation in expected_pairs:
            linked_paragraph = next(
                paragraph
                for paragraph in example.split("\n\n")
                if f"]({canonical_url})" in paragraph
            )
            self.assertIn(citation, linked_paragraph)

    def test_missing_guide_fails_explicitly(self) -> None:
        with TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing-guide.md"

            with self.assertRaisesRegex(
                ReportWritingGuideLoadError,
                "report writing guide not found",
            ):
                load_report_writing_guide(missing)

    def test_empty_guide_fails_explicitly(self) -> None:
        with TemporaryDirectory() as temporary:
            empty = Path(temporary) / "empty-guide.md"
            empty.write_text(" \n\t", encoding="utf-8")

            with self.assertRaisesRegex(
                ReportWritingGuideLoadError,
                "report writing guide is empty",
            ):
                load_report_writing_guide(empty)


class ReportPipelineTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name) / "runs"
        self.repository = JsonResearchRunRepository(self.root)
        self.artifacts = LocalArtifactStore(self.root)
        self.capabilities = build_runtime_capabilities(
            self.repository,
            self.artifacts,
            paper_search_provider=None,
            source_access_provider=FakeSourceAccessProvider(),
        )
        created = self.capabilities.researcher.create_run(
            CreateRunRequest(
                mission="Write a grounded report",
                requirements=("Explain the accepted result",),
                scope="A deterministic report fixture",
                deliverable_description="A concise cited report",
                required_artifacts=frozenset({ArtifactKind.REPORT}),
            )
        )
        retained = self.capabilities.researcher.retain_papers(
            created.run_id,
            created.state_revision,
            (
                PaperSearchHit(
                    title="Grounded paper",
                    authors=("Ada Author",),
                    publication_year=2026,
                    doi="10.1000/report",
                    arxiv_id="2608.00003",
                ),
            ),
        )
        self.run_id = created.run_id
        self.paper_ref = retained.paper_refs[0]
        CompletionCheckRuntime.from_capabilities(self.capabilities).request_and_run(
            self.run_id,
            retained.state_revision,
            "Ready to deliver",
            StaticCheckerFactory(),
        )
        self.delivery_revision = self.repository.load(self.run_id).state_revision

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @property
    def report_path(self) -> Path:
        return self.root / self.run_id / "artifacts" / "report.md"

    def _pipeline(
        self,
        *,
        integrity_disposition: IntegrityDisposition = IntegrityDisposition.PASS,
        read_during_integrity: bool = False,
        renderer_content: str = "# Report\n\nRendered [1].",
        composer=None,
    ):
        calls: list[str] = []
        editor_factory = RecordingEditorFactory(calls)
        recording_composer = composer or RecordingComposer(calls, self.paper_ref)
        integrity = RecordingIntegrityReviewer(
            calls,
            integrity_disposition,
            read_paper_ref=self.paper_ref if read_during_integrity else None,
        )
        pipeline = ReportPipeline(
            self.capabilities.delivery,
            planner=RecordingPlanner(calls, self.paper_ref),
            composer=recording_composer,
            integrator=RecordingIntegrator(calls),
            editor_factory=editor_factory,
            reviser=RecordingReviser(calls),
            integrity_reviewer=integrity,
            citation_renderer=RecordingRenderer(calls, renderer_content),
            writing_guideline="Write a concise, grounded technical report.",
        )
        return pipeline, calls, editor_factory, recording_composer, integrity

    def test_pipeline_runs_frozen_order_and_publishes_report(self) -> None:
        pipeline, calls, editor_factory, composer, _ = self._pipeline()

        result = pipeline.run(self.run_id)

        self.assertIsInstance(result, PublishedReportPipelineResult)
        assert isinstance(result, PublishedReportPipelineResult)
        self.assertEqual(
            [
                "plan",
                "compose",
                "integrate",
                "create_fresh_editor",
                "fresh_review",
                "revise",
                "integrity",
                "render_citations",
            ],
            calls,
        )
        self.assertEqual("paper", composer.inspected_kind)
        self.assertEqual(1, len(editor_factory.instances))
        self.assertEqual(
            "A concise cited report", editor_factory.instances[0].deliverable
        )
        self.assertEqual("# Report\n\nRendered [1].", self.report_path.read_text())

    def test_complete_guide_reaches_all_semantic_writing_stages_only(self) -> None:
        guide_path = (
            Path(__file__).parents[1]
            / ".claude"
            / "skills"
            / "literature-research"
            / "references"
            / "REPORT_WRITING_GUIDE.md"
        )
        guideline = load_report_writing_guide(guide_path)
        received: dict[str, str] = {}
        integrity_calls = 0
        paper_ref = self.paper_ref

        class Planner:
            def plan(self, view, writing_guideline):
                received["planner"] = writing_guideline
                return NarrativePlan(
                    audience="Technical readers",
                    reader_takeaway="Understand the accepted finding",
                    sections=(
                        NarrativeSection(
                            title="Finding",
                            purpose="Explain the accepted finding",
                            research_refs=(paper_ref,),
                        ),
                    ),
                )

        class Composer:
            def compose(self, view, plan, writing_guideline, evidence):
                received["composer"] = writing_guideline
                return ReportManuscript(markdown="# Draft\n\nGrounded finding.")

        class Integrator:
            def integrate(self, view, plan, manuscript, writing_guideline, evidence):
                received["integrator"] = writing_guideline
                return manuscript

        class Editor:
            def review(self, deliverable, plan, writing_guideline, manuscript):
                received["fresh_editor"] = writing_guideline
                return EditorialReview()

        class EditorFactory:
            def create(self):
                return Editor()

        class Reviser:
            def revise(
                self,
                view,
                plan,
                manuscript,
                review,
                writing_guideline,
                evidence,
            ):
                received["reviser"] = writing_guideline
                return manuscript

        class IntegrityReviewer:
            def review(self, view, manuscript, evidence):
                nonlocal integrity_calls
                integrity_calls += 1
                return ResearchIntegrityReview(disposition=IntegrityDisposition.PASS)

        ReportPipeline(
            self.capabilities.delivery,
            planner=Planner(),
            composer=Composer(),
            integrator=Integrator(),
            editor_factory=EditorFactory(),
            reviser=Reviser(),
            integrity_reviewer=IntegrityReviewer(),
            citation_renderer=RecordingRenderer([]),
            writing_guideline=guideline,
        ).run(self.run_id)

        self.assertEqual(
            {"planner", "composer", "integrator", "fresh_editor", "reviser"},
            set(received),
        )
        self.assertEqual({guideline}, set(received.values()))
        self.assertEqual(1, integrity_calls)

    def test_integrity_source_read_advances_revision_before_artifact_publish(
        self,
    ) -> None:
        pipeline, _, _, _, integrity = self._pipeline(read_during_integrity=True)

        result = pipeline.run(self.run_id)
        run = self.repository.load(self.run_id)

        self.assertIsInstance(result, PublishedReportPipelineResult)
        self.assertEqual(self.delivery_revision + 1, integrity.read_revision)
        self.assertEqual(integrity.read_revision, run.state_revision)
        self.assertEqual(1, run.resources.usage["source_read_attempts"])
        self.assertEqual(
            run.delivery_basis,
            self.artifacts.read_report_metadata(self.run_id).delivery_basis,
        )

    def test_delivery_revision_required_does_not_publish_or_change_lifecycle(
        self,
    ) -> None:
        pipeline, calls, _, _, _ = self._pipeline(
            integrity_disposition=IntegrityDisposition.REVISE_DELIVERY
        )

        with self.assertRaises(ReportRevisionRequiredError):
            pipeline.run(self.run_id)

        run = self.repository.load(self.run_id)
        self.assertIs(run.lifecycle, LifecycleMode.DELIVERY)
        self.assertEqual(self.delivery_revision, run.state_revision)
        self.assertNotIn("render_citations", calls)
        self.assertFalse(self.report_path.exists())

    def test_integrity_research_issue_reopens_and_invalidates_delivery_basis(
        self,
    ) -> None:
        pipeline, calls, _, _, _ = self._pipeline(
            integrity_disposition=IntegrityDisposition.REOPEN_RESEARCH
        )

        result = pipeline.run(self.run_id)
        run = self.repository.load(self.run_id)

        self.assertIsInstance(result, ReportResearchReopenedResult)
        self.assertEqual(self.delivery_revision + 1, result.state_revision)
        self.assertIs(run.lifecycle, LifecycleMode.RESEARCH)
        self.assertIsNone(run.delivery_basis)
        self.assertNotIn("render_citations", calls)
        self.assertFalse(self.report_path.exists())

    def test_semantic_stage_can_explicitly_escalate_new_inference_to_research(
        self,
    ) -> None:
        calls: list[str] = []

        class EscalatingComposer:
            def compose(self, view, plan, writing_guideline, evidence):
                calls.append("compose")
                raise ResearchEscalationRequired(
                    "A new substantive inference needs source verification"
                )

        pipeline, _, _, _, _ = self._pipeline(composer=EscalatingComposer())

        result = pipeline.run(self.run_id)

        self.assertIsInstance(result, ReportResearchReopenedResult)
        assert isinstance(result, ReportResearchReopenedResult)
        self.assertIn("substantive inference", result.rationale)
        self.assertIs(
            self.repository.load(self.run_id).lifecycle,
            LifecycleMode.RESEARCH,
        )

    def test_unknown_narrative_ref_is_rejected_before_composition(self) -> None:
        calls: list[str] = []

        class InvalidPlanner:
            def plan(self, view, writing_guideline):
                return NarrativePlan(
                    audience="Readers",
                    reader_takeaway="Understand",
                    sections=(
                        NarrativeSection(
                            title="Invalid",
                            purpose="Reference missing state",
                            research_refs=(
                                "paper_00000000-0000-4000-8000-000000000000",
                            ),
                        ),
                    ),
                )

        pipeline = ReportPipeline(
            self.capabilities.delivery,
            planner=InvalidPlanner(),
            composer=RecordingComposer(calls, self.paper_ref),
            integrator=RecordingIntegrator(calls),
            editor_factory=RecordingEditorFactory(calls),
            reviser=RecordingReviser(calls),
            integrity_reviewer=RecordingIntegrityReviewer(calls),
            citation_renderer=RecordingRenderer(calls),
            writing_guideline="Grounded writing",
        )

        with self.assertRaisesRegex(ReportPipelineError, "unknown research refs"):
            pipeline.run(self.run_id)

        self.assertEqual([], calls)
        self.assertFalse(self.report_path.exists())

    def test_invalid_semantic_runner_output_fails_closed(self) -> None:
        class InvalidComposer:
            def compose(self, view, plan, writing_guideline, evidence):
                return "untyped draft"

        pipeline, _, _, _, _ = self._pipeline(composer=InvalidComposer())

        with self.assertRaisesRegex(ReportPipelineError, "ReportManuscript"):
            pipeline.run(self.run_id)

        self.assertFalse(self.report_path.exists())

    def test_empty_renderer_output_fails_closed_without_artifact(self) -> None:
        pipeline, _, _, _, _ = self._pipeline(renderer_content="")

        with self.assertRaisesRegex(ReportPipelineError, "non-empty"):
            pipeline.run(self.run_id)

        self.assertFalse(self.report_path.exists())

    def test_pipeline_adds_no_report_lifecycle_state(self) -> None:
        pipeline, _, _, _, _ = self._pipeline()
        pipeline.run(self.run_id)
        state = (self.root / self.run_id / "state.json").read_text()

        self.assertNotIn("REPORT_DRAFTING", state)
        self.assertNotIn("editorial_status", state)
        self.assertNotIn("quality_score", state)
