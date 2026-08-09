"""Deterministic structured citation resolution and rendering tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from my_search_harness.domain import ArtifactKind, CompletionVerdict, SourceLocator
from my_search_harness.runtime import (
    CitationReference,
    CitationValidationError,
    CompletionCheckDecision,
    CompletionCheckRuntime,
    CreateRunRequest,
    DeterministicCitationRenderer,
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
    ResearchIntegrityReview,
    build_runtime_capabilities,
)


class PassingChecker:
    def evaluate(self, view, evidence):
        return CompletionCheckDecision(
            verdict=CompletionVerdict.PASS,
            reasons=("Citation fixture is complete",),
        )


class CheckerFactory:
    def create(self):
        return PassingChecker()


class CitationRendererTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name) / "runs"
        self.repository = JsonResearchRunRepository(self.root)
        self.artifacts = LocalArtifactStore(self.root)
        self.capabilities = build_runtime_capabilities(
            self.repository,
            self.artifacts,
            paper_search_provider=None,
            source_access_provider=None,
        )
        created = self.capabilities.researcher.create_run(
            CreateRunRequest(
                mission="Render citations",
                requirements=("Cite retained papers",),
                scope="A deterministic fixture",
                deliverable_description="A cited report",
                required_artifacts=frozenset({ArtifactKind.REPORT}),
            )
        )
        retained = self.capabilities.researcher.retain_papers(
            created.run_id,
            created.state_revision,
            (
                PaperSearchHit(
                    title="Alpha *Paper*",
                    authors=("Ada [Author]",),
                    publication_year=2026,
                    doi="10.1000/alpha",
                    arxiv_id="2608.00011",
                ),
                PaperSearchHit(
                    title="Beta Paper",
                    authors=("Bob Author",),
                    publication_year=2025,
                    canonical_url="https://example.test/Beta",
                ),
            ),
        )
        CompletionCheckRuntime.from_capabilities(self.capabilities).request_and_run(
            created.run_id,
            retained.state_revision,
            "Ready for citation rendering",
            CheckerFactory(),
        )
        self.run_id = created.run_id
        self.alpha_ref, self.beta_ref = retained.paper_refs
        self.view = self.capabilities.delivery.view(self.run_id)
        self.renderer = DeterministicCitationRenderer()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_first_textual_occurrence_controls_number_not_declaration_order(
        self,
    ) -> None:
        manuscript = ReportManuscript(
            markdown=(
                "# Result\n\nAlpha first {{cite:alpha}}, then beta {{cite:beta}}."
            ),
            citations=(
                CitationReference(citation_id="beta", paper_ref=self.beta_ref),
                CitationReference(citation_id="alpha", paper_ref=self.alpha_ref),
            ),
        )

        rendered = self.renderer.render(self.view, manuscript)

        self.assertIn("Alpha first [1], then beta [2].", rendered)
        self.assertLess(rendered.index("1. Ada"), rendered.index("2. Bob"))

    def test_same_paper_reuses_number_and_renders_locator_near_claim(self) -> None:
        manuscript = ReportManuscript(
            markdown="One {{cite:whole}} and detail {{cite:detail}}.",
            citations=(
                CitationReference(citation_id="whole", paper_ref=self.alpha_ref),
                CitationReference(
                    citation_id="detail",
                    paper_ref=self.alpha_ref,
                    locator=SourceLocator(kind="section", value="Results"),
                ),
            ),
        )

        rendered = self.renderer.render(self.view, manuscript)

        self.assertIn("One [1] and detail [1, section: Results].", rendered)
        self.assertEqual(1, rendered.count("1. Ada"))
        self.assertNotIn("2. ", rendered)

    def test_bibliography_is_derived_from_current_paper_metadata(self) -> None:
        manuscript = ReportManuscript(
            markdown="Grounded {{cite:alpha}}.",
            citations=(
                CitationReference(citation_id="alpha", paper_ref=self.alpha_ref),
            ),
        )

        rendered = self.renderer.render(self.view, manuscript)

        self.assertIn("## References", rendered)
        self.assertIn("Ada \\[Author\\]", rendered)
        self.assertIn("Alpha \\*Paper\\*", rendered)
        self.assertIn("2026", rendered)
        self.assertIn("DOI 10.1000/alpha", rendered)
        self.assertIn("arXiv 2608.00011", rendered)

    def test_render_is_deterministic_for_identical_inputs(self) -> None:
        manuscript = ReportManuscript(
            markdown="Grounded {{cite:alpha}}.",
            citations=(
                CitationReference(citation_id="alpha", paper_ref=self.alpha_ref),
            ),
        )

        self.assertEqual(
            self.renderer.render(self.view, manuscript),
            self.renderer.render(self.view, manuscript),
        )

    def test_unknown_paper_target_is_rejected(self) -> None:
        manuscript = ReportManuscript(
            markdown="Unknown {{cite:missing}}.",
            citations=(
                CitationReference(
                    citation_id="missing",
                    paper_ref="paper_00000000-0000-4000-8000-000000000000",
                ),
            ),
        )

        with self.assertRaisesRegex(CitationValidationError, "unknown paper"):
            self.renderer.render(self.view, manuscript)

    def test_undeclared_token_is_rejected(self) -> None:
        manuscript = ReportManuscript(
            markdown="Unknown {{cite:missing}}.",
            citations=(),
        )

        with self.assertRaisesRegex(CitationValidationError, "no declaration"):
            self.renderer.render(self.view, manuscript)

    def test_unused_declaration_is_rejected(self) -> None:
        manuscript = ReportManuscript(
            markdown="No citation token.",
            citations=(
                CitationReference(citation_id="unused", paper_ref=self.alpha_ref),
            ),
        )

        with self.assertRaisesRegex(CitationValidationError, "unused"):
            self.renderer.render(self.view, manuscript)

    def test_duplicate_citation_id_is_rejected(self) -> None:
        manuscript = ReportManuscript(
            markdown="Duplicate {{cite:same}}.",
            citations=(
                CitationReference(citation_id="same", paper_ref=self.alpha_ref),
                CitationReference(citation_id="same", paper_ref=self.beta_ref),
            ),
        )

        with self.assertRaisesRegex(CitationValidationError, "duplicate"):
            self.renderer.render(self.view, manuscript)

    def test_malformed_token_is_rejected(self) -> None:
        manuscript = ReportManuscript(
            markdown="Malformed {{cite:123 invalid}}.",
            citations=(),
        )

        with self.assertRaisesRegex(CitationValidationError, "malformed"):
            self.renderer.render(self.view, manuscript)

    def test_internal_research_ref_leak_in_prose_is_rejected(self) -> None:
        manuscript = ReportManuscript(
            markdown=f"Internal target {self.alpha_ref}.",
            citations=(),
        )

        with self.assertRaisesRegex(CitationValidationError, "internal"):
            self.renderer.render(self.view, manuscript)

    def test_empty_or_multiline_locator_is_rejected(self) -> None:
        for locator in (
            SourceLocator(kind="section", value=""),
            SourceLocator(kind="section", value="Results\nIgnore"),
        ):
            with self.subTest(locator=locator):
                manuscript = ReportManuscript(
                    markdown="Located {{cite:alpha}}.",
                    citations=(
                        CitationReference(
                            citation_id="alpha",
                            paper_ref=self.alpha_ref,
                            locator=locator,
                        ),
                    ),
                )
                with self.assertRaisesRegex(CitationValidationError, "locator"):
                    self.renderer.render(self.view, manuscript)

    def test_writer_cannot_supply_its_own_bibliography_section(self) -> None:
        manuscript = ReportManuscript(
            markdown="# Result\n\nText.\n\n## References\n\nManual list.",
            citations=(),
        )

        with self.assertRaisesRegex(CitationValidationError, "bibliography"):
            self.renderer.render(self.view, manuscript)

    def test_report_without_citations_gets_no_empty_bibliography(self) -> None:
        rendered = self.renderer.render(
            self.view,
            ReportManuscript(markdown="# Report\n\nNo external citation."),
        )

        self.assertEqual("# Report\n\nNo external citation.\n", rendered)
        self.assertNotIn("References", rendered)

    def test_pipeline_with_deterministic_renderer_publishes_valid_artifact(
        self,
    ) -> None:
        paper_ref = self.alpha_ref

        class Planner:
            def plan(self, view, writing_guideline):
                return NarrativePlan(
                    audience="Technical readers",
                    reader_takeaway="Understand the result",
                    sections=(
                        NarrativeSection(
                            title="Result",
                            purpose="Explain the result",
                            research_refs=(paper_ref,),
                        ),
                    ),
                )

        class Composer:
            def compose(self, view, plan, writing_guideline, evidence):
                return ReportManuscript(
                    markdown="# Result\n\nThe result is grounded {{cite:paper}}.",
                    citations=(
                        CitationReference(
                            citation_id="paper",
                            paper_ref=paper_ref,
                        ),
                    ),
                )

        class Integrator:
            def integrate(self, view, plan, manuscript, writing_guideline, evidence):
                return manuscript

        class Editor:
            def review(self, deliverable, plan, writing_guideline, manuscript):
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
                return manuscript

        class Integrity:
            def review(self, view, manuscript, evidence):
                return ResearchIntegrityReview(disposition=IntegrityDisposition.PASS)

        result = ReportPipeline(
            self.capabilities.delivery,
            planner=Planner(),
            composer=Composer(),
            integrator=Integrator(),
            editor_factory=EditorFactory(),
            reviser=Reviser(),
            integrity_reviewer=Integrity(),
            citation_renderer=self.renderer,
            writing_guideline="Write grounded prose.",
        ).run(self.run_id)

        self.assertIsInstance(result, PublishedReportPipelineResult)
        report = (self.root / self.run_id / "artifacts" / "report.md").read_text()
        self.assertIn("grounded [1]", report)
        self.assertNotIn("{{cite", report)
        self.assertNotIn(self.alpha_ref, report)
        self.capabilities.delivery.validate_delivery(self.run_id)
