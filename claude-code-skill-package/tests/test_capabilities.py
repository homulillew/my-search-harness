"""External capability façades preserve role and lifecycle authority."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from my_search_harness.domain import (
    ArtifactKind,
    CompletionVerdict,
    PaperSource,
    SourceLocator,
)
from my_search_harness.runtime import (
    CapabilityUnavailableError,
    CompletionView,
    ContextProjectionError,
    CreateRunRequest,
    DeliveryView,
    JsonResearchRunRepository,
    LocalArtifactStore,
    PaperSearchHit,
    PaperSearchPage,
    ResearchView,
    SourceContent,
    SourceOutline,
    SourceOutlineEntry,
    build_runtime_capabilities,
)


class FakePaperSearchProvider:
    def search(
        self,
        query: str,
        *,
        limit: int,
        offset: int = 0,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> PaperSearchPage:
        return PaperSearchPage(
            total_count=1,
            hits=(
                PaperSearchHit(
                    title="Capability Paper",
                    arxiv_id="2608.00001",
                ),
            ),
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

    def inspect_source(
        self,
        paper_ref: str,
        source: PaperSource,
    ) -> SourceOutline:
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
            content="Primary source content.",
        )


class RuntimeCapabilitiesTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name) / "runs"
        self.repository = JsonResearchRunRepository(self.root)
        self.capabilities = build_runtime_capabilities(
            self.repository,
            LocalArtifactStore(self.root),
            paper_search_provider=FakePaperSearchProvider(),
            source_access_provider=FakeSourceAccessProvider(),
        )
        self.created = self.capabilities.researcher.create_run(
            CreateRunRequest(
                mission="Prove capability separation",
                requirements=("Retain and verify one paper",),
                scope="A deterministic fixture",
                deliverable_description="A report",
                required_artifacts=frozenset({ArtifactKind.REPORT}),
            )
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_facades_do_not_expose_low_level_persistence_or_cross_role_actions(
        self,
    ) -> None:
        researcher = self.capabilities.researcher
        checker = self.capabilities.completion_checker
        delivery = self.capabilities.delivery

        for facade in (researcher, checker, delivery):
            self.assertFalse(hasattr(facade, "repository"))
            self.assertFalse(hasattr(facade, "save"))
            self.assertFalse(hasattr(facade, "artifact_store"))
            self.assertFalse(hasattr(facade, "update_state"))

        self.assertFalse(hasattr(researcher, "submit_completion_check"))
        self.assertFalse(hasattr(researcher, "close_run"))
        self.assertFalse(hasattr(researcher, "authorize_partial_delivery"))
        self.assertFalse(hasattr(researcher, "amend_contract"))
        self.assertFalse(hasattr(checker, "search_papers"))
        self.assertFalse(hasattr(checker, "retain_papers"))
        self.assertFalse(hasattr(checker, "apply_research_mutation"))
        self.assertFalse(hasattr(delivery, "search_papers"))
        self.assertFalse(hasattr(delivery, "retain_papers"))
        self.assertFalse(hasattr(delivery, "submit_completion_check"))

    def test_researcher_exposes_typed_research_maintenance_not_authority_escalation(
        self,
    ) -> None:
        retained = self.capabilities.researcher.retain_papers(
            self.created.run_id,
            self.created.state_revision,
            (PaperSearchHit(title="Representative", arxiv_id="2608.00002"),),
        )
        approach = self.capabilities.researcher.put_approach_family(
            self.created.run_id,
            retained.state_revision,
            name="Typed route",
            core_idea="Maintain canonical semantics through commands",
            representative_paper_refs=frozenset(retained.paper_refs),
        )
        gap = self.capabilities.researcher.put_investigation_gap(
            self.created.run_id,
            approach.state_revision,
            description="A researcher-owned gap",
            approach_refs=frozenset({approach.entity_ref}),
        )

        self.assertEqual(approach.state_revision + 1, gap.state_revision)

    def test_lifecycle_selects_which_facade_has_an_active_view(self) -> None:
        research_view = self.capabilities.researcher.view(self.created.run_id)
        self.assertIsInstance(research_view, ResearchView)

        with self.assertRaises(CapabilityUnavailableError):
            self.capabilities.completion_checker.view(self.created.run_id)
        with self.assertRaises(CapabilityUnavailableError):
            self.capabilities.delivery.view(self.created.run_id)
        with self.assertRaises(CapabilityUnavailableError):
            self.capabilities.delivery.validate_delivery(self.created.run_id)

    def test_researcher_search_retain_source_and_request_flow(self) -> None:
        searched = self.capabilities.researcher.search_papers(
            self.created.run_id,
            self.created.state_revision,
            "capability boundaries",
        )
        retained = self.capabilities.researcher.retain_papers(
            self.created.run_id,
            searched.state_revision,
            searched.hits,
        )
        inspected = self.capabilities.researcher.inspect_source(
            self.created.run_id,
            retained.state_revision,
            retained.paper_refs[0],
        )
        requested = self.capabilities.researcher.request_completion_check(
            self.created.run_id,
            inspected.state_revision,
            "The retained source is ready for independent verification",
        )

        self.assertEqual(1, len(searched.hits))
        self.assertEqual(1, len(inspected.outline.sections))
        self.assertEqual(inspected.state_revision + 1, requested.state_revision)
        with self.assertRaises(CapabilityUnavailableError):
            self.capabilities.researcher.view(self.created.run_id)
        with self.assertRaises(CapabilityUnavailableError):
            self.capabilities.researcher.read_source(
                self.created.run_id,
                requested.state_revision,
                retained.paper_refs[0],
            )

    def test_checker_can_only_verify_existing_state_and_submit_typed_verdict(
        self,
    ) -> None:
        searched = self.capabilities.researcher.search_papers(
            self.created.run_id,
            self.created.state_revision,
            "capability boundaries",
        )
        retained = self.capabilities.researcher.retain_papers(
            self.created.run_id,
            searched.state_revision,
            searched.hits,
        )
        requested = self.capabilities.researcher.request_completion_check(
            self.created.run_id,
            retained.state_revision,
            "Ready for independent verification",
        )

        view = self.capabilities.completion_checker.view(self.created.run_id)
        inspected = self.capabilities.completion_checker.inspect(
            self.created.run_id,
            view.state_revision,
            (retained.paper_refs[0],),
        )
        read = self.capabilities.completion_checker.read_source(
            self.created.run_id,
            view.state_revision,
            retained.paper_refs[0],
            SourceLocator(kind="section", value="1 Introduction"),
        )
        submitted = self.capabilities.completion_checker.submit_completion_check(
            self.created.run_id,
            read.state_revision,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("Existing authoritative state satisfies the contract",),
        )

        self.assertIsInstance(view, CompletionView)
        self.assertEqual("paper", inspected.objects[0].kind)
        self.assertEqual(view.state_revision + 1, read.state_revision)
        self.assertEqual(read.state_revision + 1, submitted.state_revision)
        with self.assertRaises(CapabilityUnavailableError):
            self.capabilities.completion_checker.view(self.created.run_id)

    def test_delivery_capability_publishes_validates_and_closes(self) -> None:
        searched = self.capabilities.researcher.search_papers(
            self.created.run_id,
            self.created.state_revision,
            "capability boundaries",
        )
        retained = self.capabilities.researcher.retain_papers(
            self.created.run_id,
            searched.state_revision,
            searched.hits,
        )
        requested = self.capabilities.researcher.request_completion_check(
            self.created.run_id,
            retained.state_revision,
            "Ready",
        )
        submitted = self.capabilities.completion_checker.submit_completion_check(
            self.created.run_id,
            requested.state_revision,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("Ready",),
        )

        view = self.capabilities.delivery.view(self.created.run_id)
        inspected = self.capabilities.delivery.inspect(
            self.created.run_id,
            view.state_revision,
            (retained.paper_refs[0],),
        )
        source = self.capabilities.delivery.read_source(
            self.created.run_id,
            view.state_revision,
            retained.paper_refs[0],
        )
        published = self.capabilities.delivery.publish_report(
            self.created.run_id,
            source.state_revision,
            "# Deterministic report\n\nGrounded delivery.",
        )
        validated = self.capabilities.delivery.validate_delivery(self.created.run_id)
        closed = self.capabilities.delivery.close_run(
            self.created.run_id,
            source.state_revision,
        )

        self.assertIsInstance(view, DeliveryView)
        self.assertEqual("paper", inspected.objects[0].kind)
        self.assertEqual(ArtifactKind.REPORT, published.artifact_kind)
        self.assertEqual(
            frozenset({ArtifactKind.REPORT}),
            validated.validated_artifacts,
        )
        self.assertEqual(source.state_revision + 1, closed.state_revision)
        with self.assertRaises(ContextProjectionError):
            self.capabilities.delivery.view(self.created.run_id)
