"""Lifecycle-aware context projection and stable-ref inspection tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from my_search_harness.domain import (
    ApproachFamily,
    CompletionVerdict,
    InvestigationGap,
    LandscapeFinding,
    LiteratureSource,
    OpenProblem,
    PaperAnalysis,
    SourceLocator,
    SourceRelation,
)
from my_search_harness.runtime import (
    CompletionView,
    ContextContinuation,
    ContextLimitExceededError,
    ContextLimits,
    ContextProjectionError,
    ContextProjectionService,
    ContextSection,
    CreateRunRequest,
    DeliveryView,
    JsonResearchRunRepository,
    NewBlockingGap,
    PaperSearchHit,
    ResearchCommands,
    ResearchView,
    RevisionConflictError,
    StableRefNotFoundError,
)


class ContextProjectionTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name) / "runs"
        self.repository = JsonResearchRunRepository(self.root)
        self.research = ResearchCommands(self.repository)
        created = self.research.create_run(
            CreateRunRequest(
                mission="Map a small research field",
                requirements=("Identify approaches", "Compare results"),
                scope="A bounded primary-paper corpus",
                deliverable_description="A grounded report",
                required_artifacts=frozenset(),
            )
        )
        retained = self.research.retain_papers(
            created.run_id,
            created.state_revision,
            (
                PaperSearchHit(
                    title="Paper Alpha",
                    authors=("Ada",),
                    arxiv_id="2608.00001",
                ),
                PaperSearchHit(
                    title="Paper Beta",
                    authors=("Lin",),
                    arxiv_id="2608.00002",
                ),
                PaperSearchHit(
                    title="Paper Gamma",
                    authors=("Kai",),
                    arxiv_id="2608.00003",
                ),
            ),
        )
        self.run_id = created.run_id
        self.paper_refs = retained.paper_refs

        current = self.repository.load(self.run_id)
        proposed = deepcopy(current)
        proposed.state_revision = current.state_revision + 1
        proposed.papers[self.paper_refs[0]].analysis = PaperAnalysis(
            summary="Canonical paper-level summary alpha.",
            relevance_to_run="Explains the first approach.",
            contributions=("Contribution alpha",),
            key_results=("Result alpha",),
            limitations=("Limitation alpha",),
            key_locators=(SourceLocator(kind="section", value="3 Method"),),
        )
        first_approach = ApproachFamily(
            name="Approach Alpha",
            core_idea="Canonical core idea alpha.",
            representative_papers={self.paper_refs[0]},
        )
        second_approach = ApproachFamily(
            name="Approach Beta",
            core_idea="Canonical core idea beta.",
            representative_papers={self.paper_refs[1]},
        )
        proposed.literature_landscape.approach_families = {
            first_approach.id: first_approach,
            second_approach.id: second_approach,
        }
        first_source = LiteratureSource(
            paper_ref=self.paper_refs[0],
            relation=SourceRelation.SUPPORTS,
            locator=SourceLocator(kind="section", value="4 Experiments"),
        )
        second_source = LiteratureSource(
            paper_ref=self.paper_refs[1],
            relation=SourceRelation.QUALIFIES,
        )
        first_finding = LandscapeFinding(
            statement="Canonical finding alpha.",
            approach_refs={first_approach.id},
            sources={first_source},
        )
        second_finding = LandscapeFinding(
            statement="Canonical finding beta.",
            approach_refs={second_approach.id},
            sources={second_source},
        )
        proposed.literature_landscape.findings = {
            first_finding.id: first_finding,
            second_finding.id: second_finding,
        }
        first_problem = OpenProblem(
            statement="Canonical open problem alpha.",
            approach_refs={first_approach.id},
            sources={first_source},
        )
        second_problem = OpenProblem(
            statement="Canonical open problem beta.",
            approach_refs={second_approach.id},
            sources={second_source},
        )
        proposed.literature_landscape.open_problems = {
            first_problem.id: first_problem,
            second_problem.id: second_problem,
        }
        requirement_refs = tuple(proposed.contract.revisions[-1].contract.requirements)
        first_gap = InvestigationGap(
            description="Canonical investigation gap alpha.",
            requirement_refs={requirement_refs[0]},
            approach_refs={first_approach.id},
        )
        second_gap = InvestigationGap(
            description="Canonical investigation gap beta.",
            requirement_refs={requirement_refs[1]},
            approach_refs={second_approach.id},
        )
        resolved_gap = InvestigationGap(
            description="A resolved historical gap.",
            resolution="Resolved with the retained corpus.",
        )
        proposed.investigation_gaps = {
            first_gap.id: first_gap,
            second_gap.id: second_gap,
            resolved_gap.id: resolved_gap,
        }
        self.repository.save(proposed, current.state_revision)
        self.revision = proposed.state_revision
        self.approach_refs = (first_approach.id, second_approach.id)
        self.finding_refs = (first_finding.id, second_finding.id)
        self.problem_refs = (first_problem.id, second_problem.id)
        self.gap_refs = (first_gap.id, second_gap.id)
        self.resolved_gap_ref = resolved_gap.id
        self.requirement_refs = requirement_refs

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _service(self, **overrides: int) -> ContextProjectionService:
        defaults = {
            "research_page_size": 20,
            "completion_max_items": 500,
            "delivery_max_items": 500,
            "inspect_max_refs": 20,
            "max_characters": 100_000,
        }
        defaults.update(overrides)
        return ContextProjectionService(
            self.repository,
            limits=ContextLimits(**defaults),
        )

    def test_research_view_selects_canonical_semantics_without_resummary(self) -> None:
        view = self._service().view(self.run_id)

        self.assertIsInstance(view, ResearchView)
        assert isinstance(view, ResearchView)
        self.assertEqual(self.revision, view.state_revision)
        self.assertEqual("Map a small research field", view.contract.mission)
        self.assertEqual(2, len(view.contract.requirements))
        self.assertEqual(
            {"Canonical core idea alpha.", "Canonical core idea beta."},
            {approach.core_idea for approach in view.approach_families.items},
        )
        self.assertEqual(
            {"Canonical finding alpha.", "Canonical finding beta."},
            {finding.statement for finding in view.findings.items},
        )
        self.assertEqual(2, view.open_gaps.total)
        self.assertNotIn(
            self.resolved_gap_ref, {gap.ref for gap in view.open_gaps.items}
        )
        self.assertEqual(3, view.papers.total)
        self.assertTrue(any(paper.has_analysis for paper in view.papers.items))
        self.assertFalse(hasattr(view.papers.items[0], "analysis"))
        self.assertIsNone(view.latest_completion_feedback)

    def test_research_view_pages_complete_objects_with_visible_continuation(
        self,
    ) -> None:
        service = self._service(research_page_size=1)

        first = service.view(self.run_id)

        assert isinstance(first, ResearchView)
        self.assertEqual(1, first.findings.shown)
        self.assertEqual(2, first.findings.total)
        self.assertIsNotNone(first.findings.continuation)
        continuation = first.findings.continuation
        assert continuation is not None

        second = service.view(self.run_id, continuation)

        assert isinstance(second, ResearchView)
        self.assertEqual(1, second.findings.shown)
        self.assertNotEqual(first.findings.items, second.findings.items)
        self.assertIsNone(second.findings.continuation)
        self.assertEqual(first.papers.items, second.papers.items)

    def test_continuation_is_revision_bound(self) -> None:
        service = self._service(research_page_size=1)
        first = service.view(self.run_id)
        assert isinstance(first, ResearchView)
        continuation = first.papers.continuation
        assert continuation is not None
        current = self.repository.load(self.run_id)
        proposed = deepcopy(current)
        proposed.state_revision += 1
        proposed.resources.usage["fixture"] = 1
        self.repository.save(proposed, current.state_revision)

        with self.assertRaises(RevisionConflictError):
            service.view(self.run_id, continuation)

    def test_invalid_continuation_ref_is_rejected(self) -> None:
        continuation = ContextContinuation(
            state_revision=self.revision,
            section=ContextSection.PAPERS,
            after="paper_00000000-0000-4000-8000-000000000000",
        )

        with self.assertRaisesRegex(ContextProjectionError, "continuation ref"):
            self._service().view(self.run_id, continuation)

        malformed = ContextContinuation(
            state_revision=self.revision,
            section="papers",  # type: ignore[arg-type]
            after=self.paper_refs[0],
        )
        with self.assertRaisesRegex(ContextProjectionError, "fields are invalid"):
            self._service().view(self.run_id, malformed)

    def test_research_view_fails_closed_instead_of_truncating_one_large_object(
        self,
    ) -> None:
        with self.assertRaises(ContextLimitExceededError):
            self._service(max_characters=100).view(self.run_id)

    def test_completion_view_is_complete_and_omits_operational_noise(self) -> None:
        requested = self.research.request_completion_check(
            self.run_id,
            self.revision,
            "Researcher claims the current landscape is sufficient.",
        )

        view = self._service(research_page_size=1).view(self.run_id)

        self.assertIsInstance(view, CompletionView)
        assert isinstance(view, CompletionView)
        self.assertEqual(requested.state_revision, view.state_revision)
        self.assertEqual(2, len(view.approach_families))
        self.assertEqual(2, len(view.findings))
        self.assertEqual(2, len(view.open_problems))
        self.assertEqual(2, len(view.open_gaps))
        self.assertEqual(set(self.paper_refs[:2]), set(view.representative_paper_refs))
        self.assertEqual(requested.completion_check_ref, view.completion_check_ref)
        self.assertEqual(
            "Researcher claims the current landscape is sufficient.",
            view.requester_rationale,
        )
        self.assertFalse(hasattr(view, "resources"))
        self.assertFalse(hasattr(view, "events"))

    def test_completion_view_fails_closed_when_semantic_skeleton_exceeds_limit(
        self,
    ) -> None:
        self.research.request_completion_check(self.run_id, self.revision, "Ready")

        with self.assertRaisesRegex(ContextLimitExceededError, "Completion View"):
            self._service(completion_max_items=1).view(self.run_id)

    def test_completion_view_rejects_pagination(self) -> None:
        requested = self.research.request_completion_check(
            self.run_id,
            self.revision,
            "Ready",
        )
        continuation = ContextContinuation(
            state_revision=requested.state_revision,
            section=ContextSection.PAPERS,
            after=self.paper_refs[0],
        )

        with self.assertRaisesRegex(ContextProjectionError, "does not accept"):
            self._service().view(self.run_id, continuation)

    def test_research_view_contains_latest_completion_feedback(self) -> None:
        requested = self.research.request_completion_check(
            self.run_id,
            self.revision,
            "Ready",
        )
        submitted = self.research.submit_completion_check(
            self.run_id,
            requested.state_revision,
            requested.completion_check_ref,
            CompletionVerdict.CONTINUE,
            ("A comparison remains unsupported",),
            (
                NewBlockingGap(
                    description="Compare the retained approaches",
                    requirement_refs=frozenset({self.requirement_refs[1]}),
                ),
            ),
        )

        view = self._service().view(self.run_id)

        assert isinstance(view, ResearchView)
        feedback = view.latest_completion_feedback
        assert feedback is not None
        self.assertEqual(requested.completion_check_ref, feedback.completion_check_ref)
        self.assertEqual("CONTINUE", feedback.verdict)
        self.assertEqual(("A comparison remains unsupported",), feedback.reasons)
        self.assertEqual(
            submitted.blocking_gap_refs, frozenset(feedback.blocking_gap_refs)
        )

    def test_delivery_view_exposes_current_authorization_and_known_limitations(
        self,
    ) -> None:
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
            ("Current state satisfies the contract",),
        )

        view = self._service().view(self.run_id)

        self.assertIsInstance(view, DeliveryView)
        assert isinstance(view, DeliveryView)
        self.assertEqual(submitted.state_revision, view.state_revision)
        self.assertEqual(2, len(view.open_gaps))
        self.assertEqual(3, len(view.papers))
        self.assertEqual(
            requested.completion_check_ref,
            view.delivery_basis.completion_check_ref,  # type: ignore[union-attr]
        )
        self.assertFalse(hasattr(view, "resources"))

    def test_delivery_view_fails_closed_when_complete_projection_exceeds_limit(
        self,
    ) -> None:
        requested = self.research.request_completion_check(
            self.run_id,
            self.revision,
            "Ready",
        )
        self.research.submit_completion_check(
            self.run_id,
            requested.state_revision,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("Ready",),
        )

        with self.assertRaisesRegex(ContextLimitExceededError, "Delivery View"):
            self._service(delivery_max_items=1).view(self.run_id)

    def test_inspect_resolves_all_current_stable_entity_namespaces(self) -> None:
        refs = (
            self.requirement_refs[0],
            self.paper_refs[0],
            self.approach_refs[0],
            self.finding_refs[0],
            self.problem_refs[0],
            self.gap_refs[0],
        )

        result = self._service().inspect(self.run_id, self.revision, refs)

        self.assertEqual(self.revision, result.state_revision)
        self.assertEqual(refs, tuple(item.ref for item in result.objects))
        self.assertEqual(
            (
                "requirement",
                "paper",
                "approach_family",
                "landscape_finding",
                "open_problem",
                "investigation_gap",
            ),
            tuple(item.kind for item in result.objects),
        )

    def test_inspect_returns_detached_copy_not_a_write_path(self) -> None:
        result = self._service().inspect(
            self.run_id,
            self.revision,
            (self.paper_refs[0],),
        )
        inspected_paper = result.objects[0].value
        assert hasattr(inspected_paper, "source")
        inspected_paper.source.title = "Locally mutated detached copy"  # type: ignore[union-attr]

        persisted = self.repository.load(self.run_id).papers[self.paper_refs[0]]
        self.assertEqual("Paper Alpha", persisted.source.title)

    def test_inspect_is_revision_bound(self) -> None:
        with self.assertRaises(RevisionConflictError):
            self._service().inspect(
                self.run_id,
                self.revision + 1,
                (self.paper_refs[0],),
            )

    def test_inspect_rejects_unknown_duplicate_or_too_many_refs(self) -> None:
        service = self._service(inspect_max_refs=1)
        with self.assertRaises(StableRefNotFoundError):
            service.inspect(
                self.run_id,
                self.revision,
                ("paper_00000000-0000-4000-8000-000000000000",),
            )
        with self.assertRaisesRegex(ContextProjectionError, "unique"):
            self._service().inspect(
                self.run_id,
                self.revision,
                (self.paper_refs[0], self.paper_refs[0]),
            )
        with self.assertRaises(ContextLimitExceededError):
            service.inspect(
                self.run_id,
                self.revision,
                (self.paper_refs[0], self.paper_refs[1]),
            )

    def test_projection_does_not_depend_on_events_file(self) -> None:
        events = self.root / self.run_id / "events.jsonl"
        self.assertFalse(events.exists())

        view = self._service().view(self.run_id)
        inspected = self._service().inspect(
            self.run_id,
            self.revision,
            (self.finding_refs[0],),
        )

        self.assertIsInstance(view, ResearchView)
        self.assertEqual(self.finding_refs[0], inspected.objects[0].ref)
