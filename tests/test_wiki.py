"""Local Wiki eligibility, projection boundaries, and atomic rebuild tests."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from my_search_harness.domain import (
    CompletionVerdict,
    LifecycleMode,
    LiteratureSource,
    RunOutcome,
    SourceRelation,
)
from my_search_harness.runtime import (
    CreateRunRequest,
    DeliveryCommands,
    JsonResearchRunRepository,
    LocalArtifactStore,
    LocalWikiPublisher,
    PaperSearchHit,
    ResearchCommands,
    WikiBuildError,
    WikiDraft,
    WikiPageDraft,
    WikiProjection,
    WikiProjectionService,
    WikiProvenanceRef,
    WikiPublicationError,
    WikiQueryService,
    WikiRuntime,
    WikiSemanticReview,
    WikiSemanticValidationError,
    WikiUnavailableError,
)


class ApprovingValidator:
    def validate(self, projection, draft):
        return WikiSemanticReview(approved=True)


class RejectingValidator:
    def validate(self, projection, draft):
        return WikiSemanticReview(
            approved=False,
            issues=("The draft hides an important conflict",),
        )


class ProjectionPageBuilder:
    def __init__(
        self,
        *,
        slug: str = "methods",
        title: str = "Methods",
        markdown: str = "# Methods\n\nAccepted cross-run knowledge.",
    ) -> None:
        self.slug = slug
        self.title = title
        self.markdown = markdown
        self.seen_projection: WikiProjection | None = None

    def build(self, projection):
        self.seen_projection = projection
        if not projection.runs:
            return WikiDraft(pages=())
        run = projection.runs[0]
        ref = run.findings[0].ref if run.findings else run.approaches[0].ref
        return WikiDraft(
            pages=(
                WikiPageDraft(
                    slug=self.slug,
                    title=self.title,
                    markdown=self.markdown,
                    contributing_refs=(
                        WikiProvenanceRef(
                            run_id=run.run_id,
                            research_ref=ref,
                        ),
                    ),
                ),
            )
        )


class StaticDraftBuilder:
    def __init__(self, draft: WikiDraft) -> None:
        self.draft = draft

    def build(self, projection):
        return self.draft


class WikiRuntimeTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.runs_root = self.base / "runs"
        self.wiki_path = self.base / "wiki"
        self.repository = JsonResearchRunRepository(self.runs_root)
        self.artifacts = LocalArtifactStore(self.runs_root)
        self.research = ResearchCommands(self.repository)
        self.delivery = DeliveryCommands(self.repository, self.artifacts)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _create_complete_run(
        self,
        *,
        mission: str = "Map methods",
        finding_statement: str = "Method A improves the bounded task",
        doi: str = "10.1000/wiki",
    ) -> dict[str, str]:
        created = self.research.create_run(
            CreateRunRequest(
                mission=mission,
                requirements=("Map accepted knowledge",),
                scope="A Wiki fixture",
                deliverable_description="No artifact required",
            )
        )
        retained = self.research.retain_papers(
            created.run_id,
            created.state_revision,
            (
                PaperSearchHit(
                    title="Representative paper",
                    authors=("Ada Author",),
                    publication_year=2026,
                    doi=doi,
                ),
                PaperSearchHit(
                    title="Unreferenced retained paper",
                    doi=f"{doi}/unused",
                ),
            ),
        )
        representative_ref = retained.paper_refs[0]
        unreferenced_ref = retained.paper_refs[1]
        approach = self.research.put_approach_family(
            created.run_id,
            retained.state_revision,
            name="Method A",
            core_idea="Use accepted evidence",
            representative_paper_refs=frozenset({representative_ref}),
        )
        source = frozenset(
            {
                LiteratureSource(
                    paper_ref=representative_ref,
                    relation=SourceRelation.SUPPORTS,
                )
            }
        )
        finding = self.research.put_landscape_finding(
            created.run_id,
            approach.state_revision,
            statement=finding_statement,
            approach_refs=frozenset({approach.entity_ref}),
            sources=source,
        )
        problem = self.research.put_open_problem(
            created.run_id,
            finding.state_revision,
            statement="Generalization remains open",
            approach_refs=frozenset({approach.entity_ref}),
            sources=source,
        )
        gap = self.research.put_investigation_gap(
            created.run_id,
            problem.state_revision,
            description="Run-local gap must not enter Wiki input",
        )
        requested = self.research.request_completion_check(
            created.run_id,
            gap.state_revision,
            "Ready for closure",
        )
        completed = self.research.submit_completion_check(
            created.run_id,
            requested.state_revision,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("Accepted state covers the contract",),
        )
        closed = self.delivery.close_run(created.run_id, completed.state_revision)
        return {
            "run_id": created.run_id,
            "paper_ref": representative_ref,
            "unreferenced_ref": unreferenced_ref,
            "approach_ref": approach.entity_ref,
            "finding_ref": finding.entity_ref,
            "problem_ref": problem.entity_ref,
            "gap_ref": gap.entity_ref,
            "state_revision": str(closed.state_revision),
        }

    def _create_partial_run(self) -> str:
        created = self.research.create_run(
            CreateRunRequest(
                mission="Partial knowledge",
                requirements=("Incomplete",),
                scope="Partial fixture",
                deliverable_description="No artifact required",
            )
        )
        authorized = self.research.authorize_partial_delivery(
            created.run_id,
            created.state_revision,
            "Known limitation",
        )
        closed = self.delivery.close_run(created.run_id, authorized.state_revision)
        self.assertIs(closed.outcome, RunOutcome.PARTIAL)
        return created.run_id

    def _runtime(self, builder, validator=None) -> WikiRuntime:
        return WikiRuntime(
            WikiProjectionService(self.repository),
            builder,
            validator or ApprovingValidator(),
            LocalWikiPublisher(self.wiki_path),
        )

    def test_projection_selects_only_closed_complete_runs(self) -> None:
        complete = self._create_complete_run()
        partial_run_id = self._create_partial_run()
        research_run = self.research.create_run(
            CreateRunRequest(
                mission="Still researching",
                requirements=(),
                scope="Open fixture",
                deliverable_description="Nothing yet",
            )
        )

        projection = WikiProjectionService(self.repository).project()

        self.assertEqual(
            (complete["run_id"],), tuple(run.run_id for run in projection.runs)
        )
        self.assertNotEqual(partial_run_id, projection.runs[0].run_id)
        self.assertNotEqual(research_run.run_id, projection.runs[0].run_id)

    def test_projection_type_omits_process_delivery_and_report_data(self) -> None:
        refs = self._create_complete_run()
        run_directory = self.runs_root / refs["run_id"]
        (run_directory / "events.jsonl").write_text(
            "AUDIT_POISON",
            encoding="utf-8",
        )
        artifacts = run_directory / "artifacts"
        artifacts.mkdir(exist_ok=True)
        (artifacts / "report.md").write_text("REPORT_POISON", encoding="utf-8")
        builder = ProjectionPageBuilder()

        self._runtime(builder).rebuild()
        projection = builder.seen_projection
        assert projection is not None
        projected = projection.runs[0]

        for forbidden in (
            "investigation_gaps",
            "completion_checks",
            "resources",
            "events",
            "report",
            "delivery_basis",
        ):
            self.assertFalse(hasattr(projected, forbidden))
        self.assertNotIn("AUDIT_POISON", repr(projection))
        self.assertNotIn("REPORT_POISON", repr(projection))
        self.assertEqual(
            {refs["paper_ref"]},
            {paper.ref for paper in projected.papers},
        )
        self.assertNotIn(refs["unreferenced_ref"], repr(projection))

    def test_rebuild_publishes_index_pages_and_complete_manifest(self) -> None:
        refs = self._create_complete_run()

        result = self._runtime(ProjectionPageBuilder()).rebuild()

        self.assertTrue(result.wiki_path.is_symlink())
        self.assertTrue((self.wiki_path / "INDEX.md").is_file())
        self.assertTrue((self.wiki_path / "pages" / "methods.md").is_file())
        self.assertTrue((self.wiki_path / "manifest.json").is_file())
        self.assertEqual(1, result.manifest.schema_version)
        self.assertEqual(refs["run_id"], result.manifest.source_runs[0].run_id)
        page = result.manifest.pages[0]
        self.assertEqual("pages/methods.md", page.path)
        self.assertEqual(refs["finding_ref"], page.contributing_refs[0].research_ref)

    def test_full_rebuild_does_not_use_or_retain_old_wiki_prose(self) -> None:
        self._create_complete_run()
        first = self._runtime(
            ProjectionPageBuilder(
                slug="old-topic",
                title="Old Topic",
                markdown="# Old\n\nOLD_WIKI_POISON",
            )
        )
        first.rebuild()
        old_target = os.readlink(self.wiki_path)

        second = self._runtime(
            ProjectionPageBuilder(
                slug="new-topic",
                title="New Topic",
                markdown="# New\n\nFresh derivation only.",
            )
        )
        second.rebuild()

        self.assertNotEqual(old_target, os.readlink(self.wiki_path))
        self.assertFalse((self.wiki_path / "pages" / "old-topic.md").exists())
        self.assertTrue((self.wiki_path / "pages" / "new-topic.md").is_file())
        self.assertNotIn(
            "OLD_WIKI_POISON",
            (self.wiki_path / "pages" / "new-topic.md").read_text(),
        )

    def test_semantic_rejection_preserves_previous_publication(self) -> None:
        self._create_complete_run()
        self._runtime(ProjectionPageBuilder()).rebuild()
        old_target = os.readlink(self.wiki_path)
        old_index = (self.wiki_path / "INDEX.md").read_bytes()

        with self.assertRaises(WikiSemanticValidationError):
            self._runtime(
                ProjectionPageBuilder(slug="rejected"),
                RejectingValidator(),
            ).rebuild()

        self.assertEqual(old_target, os.readlink(self.wiki_path))
        self.assertEqual(old_index, (self.wiki_path / "INDEX.md").read_bytes())

    def test_invalid_provenance_or_link_fails_before_publication(self) -> None:
        refs = self._create_complete_run()
        invalid_ref = WikiDraft(
            pages=(
                WikiPageDraft(
                    slug="invalid",
                    title="Invalid",
                    markdown="# Invalid",
                    contributing_refs=(
                        WikiProvenanceRef(
                            run_id=refs["run_id"],
                            research_ref=refs["gap_ref"],
                        ),
                    ),
                ),
            )
        )
        with self.assertRaisesRegex(WikiBuildError, "contributing"):
            self._runtime(StaticDraftBuilder(invalid_ref)).rebuild()

        invalid_link = WikiDraft(
            pages=(
                WikiPageDraft(
                    slug="invalid-link",
                    title="Invalid link",
                    markdown="# Invalid\n\n[Missing](missing.md)",
                    contributing_refs=(
                        WikiProvenanceRef(
                            run_id=refs["run_id"],
                            research_ref=refs["finding_ref"],
                        ),
                    ),
                ),
            )
        )
        with self.assertRaisesRegex(WikiBuildError, "link"):
            self._runtime(StaticDraftBuilder(invalid_link)).rebuild()
        self.assertFalse(self.wiki_path.exists())

    def test_atomic_pointer_failure_preserves_previous_wiki(self) -> None:
        self._create_complete_run()
        self._runtime(ProjectionPageBuilder()).rebuild()
        old_target = os.readlink(self.wiki_path)
        original_replace = os.replace
        calls = 0

        def fail_pointer_replace(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated pointer replace failure")
            return original_replace(source, target)

        with patch("my_search_harness.runtime.wiki.os.replace", fail_pointer_replace):
            with self.assertRaises(WikiPublicationError):
                self._runtime(ProjectionPageBuilder(slug="new-build")).rebuild()

        self.assertEqual(old_target, os.readlink(self.wiki_path))
        self.assertTrue((self.wiki_path / "pages" / "methods.md").is_file())

    def test_post_replace_fsync_failure_rolls_back_pointer(self) -> None:
        self._create_complete_run()
        self._runtime(ProjectionPageBuilder()).rebuild()
        old_target = os.readlink(self.wiki_path)

        with patch.object(
            LocalWikiPublisher,
            "_fsync_directory",
            side_effect=OSError("simulated fsync failure"),
        ):
            with self.assertRaises(WikiPublicationError):
                self._runtime(ProjectionPageBuilder(slug="new-build")).rebuild()

        self.assertEqual(old_target, os.readlink(self.wiki_path))
        self.assertTrue((self.wiki_path / "pages" / "methods.md").is_file())

    def test_freshness_is_derived_from_eligible_run_revisions(self) -> None:
        self._create_complete_run()
        runtime = self._runtime(ProjectionPageBuilder())
        runtime.rebuild()
        self.assertTrue(runtime.is_current())

        self._create_complete_run(
            mission="Second accepted run",
            finding_statement="A conflicting accepted result",
            doi="10.1000/wiki-second",
        )

        self.assertFalse(runtime.is_current())

    def test_projection_preserves_conflicting_accepted_findings(self) -> None:
        self._create_complete_run(finding_statement="Method A succeeds")
        self._create_complete_run(
            finding_statement="Method A fails under another condition",
            doi="10.1000/wiki-conflict",
        )

        projection = WikiProjectionService(self.repository).project()
        statements = {
            finding.statement for run in projection.runs for finding in run.findings
        }

        self.assertEqual(
            {
                "Method A succeeds",
                "Method A fails under another condition",
            },
            statements,
        )

    def test_query_returns_observation_and_distinguishes_no_match(self) -> None:
        refs = self._create_complete_run()
        self._runtime(
            ProjectionPageBuilder(
                markdown="# Methods\n\nA searchable mechanism description.",
            )
        ).rebuild()
        query = WikiQueryService(LocalWikiPublisher(self.wiki_path))
        state_before = (self.runs_root / refs["run_id"] / "state.json").read_bytes()

        found = query.query("searchable mechanism")
        empty = query.query("definitely absent")

        self.assertEqual(1, len(found.hits))
        self.assertIn("searchable mechanism", found.hits[0].excerpt)
        self.assertEqual(
            refs["finding_ref"], found.hits[0].contributing_refs[0].research_ref
        )
        self.assertEqual((), empty.hits)
        self.assertEqual(
            state_before,
            (self.runs_root / refs["run_id"] / "state.json").read_bytes(),
        )

    def test_missing_or_corrupt_publication_is_explicit_not_empty(self) -> None:
        publisher = LocalWikiPublisher(self.wiki_path)
        with self.assertRaises(WikiUnavailableError):
            WikiQueryService(publisher).query("anything")

        self._create_complete_run()
        self._runtime(ProjectionPageBuilder()).rebuild()
        page_path = self.wiki_path / "pages" / "methods.md"
        page_path.write_text("corrupt content", encoding="utf-8")

        with self.assertRaises(WikiUnavailableError):
            WikiQueryService(publisher).query("anything")

    def test_empty_eligible_input_publishes_explicit_empty_index(self) -> None:
        self._create_partial_run()
        result = self._runtime(ProjectionPageBuilder()).rebuild()

        self.assertEqual((), result.manifest.source_runs)
        self.assertEqual((), result.manifest.pages)
        self.assertIn(
            "No eligible research knowledge",
            (self.wiki_path / "INDEX.md").read_text(),
        )
