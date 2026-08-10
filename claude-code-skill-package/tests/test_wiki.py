"""Local Wiki eligibility, projection boundaries, publication, and freshness tests."""

from __future__ import annotations

import json
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
    WikiPageDraft,
    WikiProjectionService,
    WikiProvenanceRef,
    WikiPublicationError,
    WikiQueryService,
    WikiService,
    WikiUnavailableError,
)


class WikiServiceTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.runs_root = self.base / "runs"
        self.wiki_path = self.base / "wiki"
        self.repository = JsonResearchRunRepository(self.runs_root)
        self.artifacts = LocalArtifactStore(self.runs_root)
        self.research = ResearchCommands(self.repository)
        self.delivery = DeliveryCommands(self.repository, self.artifacts)
        self.publisher = LocalWikiPublisher(self.wiki_path)
        self.wiki = WikiService(WikiProjectionService(self.repository), self.publisher)

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
                    publication_date="2026-08-03",
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

    def _page(
        self,
        refs: dict[str, str],
        *,
        slug: str = "methods",
        title: str = "Methods",
        markdown: str = "# Methods\n\nAccepted cross-run knowledge.",
        ref_key: str = "finding_ref",
    ) -> WikiPageDraft:
        return WikiPageDraft(
            slug=slug,
            title=title,
            markdown=markdown,
            contributing_refs=(
                WikiProvenanceRef(
                    run_id=refs["run_id"],
                    research_ref=refs[ref_key],
                ),
            ),
        )

    def _current_build_id(self) -> str:
        pointer = json.loads((self.wiki_path / "current.json").read_text(encoding="utf-8"))
        return pointer["build"]

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

        projection = self.wiki.project()

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

        projection = self.wiki.project()
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
        self.assertEqual("2026-08-03", projected.papers[0].publication_date)
        self.assertNotIn(refs["unreferenced_ref"], repr(projection))

    def test_publish_writes_versioned_build_and_current_pointer(self) -> None:
        refs = self._create_complete_run()
        projection = self.wiki.project()

        result = self.wiki.publish(
            projection.source_runs,
            (self._page(refs),),
        )

        self.assertEqual(self.wiki_path, result.wiki_path)
        build_id = self._current_build_id()
        build_dir = self.wiki_path / "builds" / build_id
        self.assertTrue(build_dir.is_dir())
        self.assertTrue((build_dir / "INDEX.md").is_file())
        self.assertTrue((build_dir / "pages" / "methods.md").is_file())
        self.assertTrue((build_dir / "manifest.json").is_file())
        self.assertEqual(1, result.manifest.schema_version)
        self.assertEqual(refs["run_id"], result.manifest.source_runs[0].run_id)
        page = result.manifest.pages[0]
        self.assertEqual("pages/methods.md", page.path)
        self.assertEqual(refs["finding_ref"], page.contributing_refs[0].research_ref)

    def test_rebuild_replaces_current_pointer_and_preserves_old_build(self) -> None:
        refs = self._create_complete_run()
        projection = self.wiki.project()
        self.wiki.publish(
            projection.source_runs,
            (self._page(refs, slug="old-topic", title="Old Topic", markdown="# Old\n\nOLD_WIKI_POISON"),),
        )
        first_build_id = self._current_build_id()

        self.wiki.publish(
            projection.source_runs,
            (
                self._page(
                    refs,
                    slug="new-topic",
                    title="New Topic",
                    markdown="# New\n\nFresh derivation only.",
                ),
            ),
        )
        second_build_id = self._current_build_id()

        self.assertNotEqual(first_build_id, second_build_id)
        current_build = self.wiki_path / "builds" / second_build_id
        self.assertFalse((current_build / "pages" / "old-topic.md").exists())
        self.assertTrue((current_build / "pages" / "new-topic.md").is_file())
        self.assertNotIn(
            "OLD_WIKI_POISON",
            (current_build / "pages" / "new-topic.md").read_text(),
        )
        # The old build is preserved on disk as an inert orphan.
        self.assertTrue((self.wiki_path / "builds" / first_build_id).is_dir())

    def test_invalid_provenance_fails_before_publication(self) -> None:
        refs = self._create_complete_run()
        projection = self.wiki.project()
        invalid_page = WikiPageDraft(
            slug="invalid",
            title="Invalid",
            markdown="# Invalid",
            contributing_refs=(
                WikiProvenanceRef(
                    run_id=refs["run_id"],
                    research_ref=refs["gap_ref"],
                ),
            ),
        )
        with self.assertRaisesRegex(WikiBuildError, "contributing"):
            self.wiki.publish(projection.source_runs, (invalid_page,))
        self.assertFalse((self.wiki_path / "current.json").exists())

    def test_invalid_link_fails_before_publication(self) -> None:
        refs = self._create_complete_run()
        projection = self.wiki.project()
        invalid_link = WikiPageDraft(
            slug="invalid-link",
            title="Invalid link",
            markdown="# Invalid\n\n[Missing](missing.md)",
            contributing_refs=(
                WikiProvenanceRef(
                    run_id=refs["run_id"],
                    research_ref=refs["finding_ref"],
                ),
            ),
        )
        with self.assertRaisesRegex(WikiBuildError, "link"):
            self.wiki.publish(projection.source_runs, (invalid_link,))
        self.assertFalse((self.wiki_path / "current.json").exists())

    def test_failed_build_preserves_previous_current_pointer(self) -> None:
        refs = self._create_complete_run()
        projection = self.wiki.project()
        self.wiki.publish(projection.source_runs, (self._page(refs),))
        first_build_id = self._current_build_id()

        original_replace = __import__("os").replace
        calls = 0

        def fail_pointer_replace(source, target):
            nonlocal calls
            calls += 1
            # The second os.replace is the current.json pointer swap.
            if calls == 2:
                raise OSError("simulated pointer replace failure")
            return original_replace(source, target)

        with patch("my_search_harness.runtime.wiki.os.replace", fail_pointer_replace):
            with self.assertRaises(WikiPublicationError):
                self.wiki.publish(
                    projection.source_runs,
                    (self._page(refs, slug="new-build", title="New Build"),),
                )

        self.assertEqual(first_build_id, self._current_build_id())
        current_build = self.wiki_path / "builds" / first_build_id
        self.assertTrue((current_build / "pages" / "methods.md").is_file())

    def test_stale_publication_allowed_and_is_current_detects_it(self) -> None:
        # Run A closes COMPLETE.
        refs_a = self._create_complete_run()
        projection_a = self.wiki.project()
        source_runs_a = projection_a.source_runs
        self.assertEqual(1, len(source_runs_a))

        # Publish with source_runs_a (fresh). is_current() is True.
        self.wiki.publish(source_runs_a, (self._page(refs_a),))
        self.assertTrue(self.wiki.is_current())

        # Run B closes COMPLETE. The current projection is now A+B, but the
        # published manifest still records A only — so it is stale.
        refs_b = self._create_complete_run(
            mission="Second accepted run",
            finding_statement="A conflicting accepted result",
            doi="10.1000/wiki-second",
        )
        self.assertFalse(self.wiki.is_current())

        # Stale publication is allowed, not rejected: publish with source_runs_a
        # (stale) again. The manifest honestly records A only.
        self.wiki.publish(source_runs_a, (self._page(refs_a),))
        self.assertEqual(
            source_runs_a,
            LocalWikiPublisher(self.wiki_path).read_manifest().source_runs,
        )
        self.assertFalse(self.wiki.is_current())

        # Re-project (now A+B) and publish fresh pages citing A and B.
        projection_ab = self.wiki.project()
        source_runs_ab = projection_ab.source_runs
        self.assertEqual(2, len(source_runs_ab))
        fresh_pages = (
            WikiPageDraft(
                slug="methods",
                title="Methods",
                markdown="# Methods\n\nBuilt from A and B.",
                contributing_refs=(
                    WikiProvenanceRef(
                        run_id=refs_a["run_id"],
                        research_ref=refs_a["finding_ref"],
                    ),
                    WikiProvenanceRef(
                        run_id=refs_b["run_id"],
                        research_ref=refs_b["finding_ref"],
                    ),
                ),
            ),
        )
        self.wiki.publish(source_runs_ab, fresh_pages)
        self.assertEqual(
            source_runs_ab,
            LocalWikiPublisher(self.wiki_path).read_manifest().source_runs,
        )
        self.assertTrue(self.wiki.is_current())

    def test_projection_preserves_conflicting_accepted_findings(self) -> None:
        self._create_complete_run(finding_statement="Method A succeeds")
        self._create_complete_run(
            finding_statement="Method A fails under another condition",
            doi="10.1000/wiki-conflict",
        )

        projection = self.wiki.project()
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
        projection = self.wiki.project()
        self.wiki.publish(
            projection.source_runs,
            (
                self._page(
                    refs,
                    markdown="# Methods\n\nA searchable mechanism description.",
                ),
            ),
        )
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

        refs = self._create_complete_run()
        projection = self.wiki.project()
        self.wiki.publish(projection.source_runs, (self._page(refs),))
        build_id = self._current_build_id()
        page_path = self.wiki_path / "builds" / build_id / "pages" / "methods.md"
        page_path.write_text("corrupt content", encoding="utf-8")

        with self.assertRaises(WikiUnavailableError):
            WikiQueryService(publisher).query("anything")

    def test_empty_eligible_input_publishes_explicit_empty_index(self) -> None:
        self._create_partial_run()
        result = self.wiki.publish((), ())

        self.assertEqual((), result.manifest.source_runs)
        self.assertEqual((), result.manifest.pages)
        build_id = self._current_build_id()
        self.assertIn(
            "No eligible research knowledge",
            (self.wiki_path / "builds" / build_id / "INDEX.md").read_text(),
        )
