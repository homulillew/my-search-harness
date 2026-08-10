"""Claude Code Skill layout, adapter, and standalone packaging tests."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any
from unittest import TestCase

from my_search_harness.runtime import (
    PaperSearchHit,
    PaperSearchResult,
)


ROOT = Path(__file__).parents[1]
SKILL = ROOT / ".claude" / "skills" / "literature-research"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class SkillLayoutTests(TestCase):
    def test_skill_has_valid_minimal_frontmatter_and_bounded_length(self) -> None:
        content = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        lines = content.splitlines()
        self.assertEqual(lines[0], "---")
        closing = lines.index("---", 1)
        frontmatter = lines[1:closing]
        self.assertEqual(len(frontmatter), 2)
        self.assertTrue(frontmatter[0].startswith("name: literature-research"))
        self.assertTrue(frontmatter[1].startswith("description: "))
        self.assertGreaterEqual(len(lines), 150)
        self.assertLessEqual(len(lines), 390)

    def test_supporting_files_and_executables_exist(self) -> None:
        expected = (
            "README.md",
            "references/RESEARCH_PROTOCOL.md",
            "references/RUNTIME_API.md",
            "references/COMPLETION_GUIDE.md",
            "references/REPORT_WRITING_GUIDE.md",
            "references/RESEARCH_INTEGRITY_GUIDE.md",
            "scripts/harness",
            "scripts/harness.ps1",
            "scripts/harness.py",
            "scripts/doctor.py",
            "scripts/setup.sh",
            "scripts/setup.ps1",
        )
        for relative in expected:
            with self.subTest(relative=relative):
                path = SKILL / relative
                self.assertTrue(path.is_file())
        for relative in ("scripts/harness", "scripts/doctor.py", "scripts/setup.sh"):
            self.assertTrue(os.access(SKILL / relative, os.X_OK))

    def test_skill_links_all_progressive_disclosure_references(self) -> None:
        content = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for name in (
            "RESEARCH_PROTOCOL.md",
            "RUNTIME_API.md",
            "COMPLETION_GUIDE.md",
            "REPORT_WRITING_GUIDE.md",
            "RESEARCH_INTEGRITY_GUIDE.md",
        ):
            self.assertIn(name, content)
        self.assertIn("${CLAUDE_SKILL_DIR}", content)
        self.assertNotIn(str(ROOT), content)

    def test_skill_does_not_depend_on_a_report_example(self) -> None:
        retired_example = "technical-" + "route-survey.md"
        for relative in ("SKILL.md", "README.md"):
            with self.subTest(relative=relative):
                content = (SKILL / relative).read_text(encoding="utf-8")
                self.assertNotIn(retired_example, content)

    def test_completion_policy_matches_checker_authority(self) -> None:
        content = (SKILL / "references" / "COMPLETION_GUIDE.md").read_text(
            encoding="utf-8"
        )
        for researcher_process in (
            "audit-" + "history",
            "explicit date-filtered searches",
            "pagination beyond",
        ):
            self.assertNotIn(researcher_process, content)
        self.assertIn("frontier coverage", content)
        self.assertIn("Recent primary work", content)
        self.assertIn(
            "may challenge current knowledge, but does not repair it", content
        )

    def test_workspace_documentation_keeps_data_outside_skill_installation(
        self,
    ) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        standalone_readme = (SKILL / "README.md").read_text(encoding="utf-8")
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        normalized_standalone = " ".join(standalone_readme.split())
        self.assertNotIn("$PWD/workspace", standalone_readme)
        self.assertNotIn("$PWD/workspace", root_readme)
        self.assertIn("never inside the skill directory", skill)
        self.assertIn("outside the Skill installation directory", normalized_standalone)

    def test_writing_and_integrity_guides_are_distinct_authorities(self) -> None:
        writing_guides = tuple(
            path
            for path in ROOT.rglob("REPORT_WRITING_GUIDE.md")
            if "dist" not in path.relative_to(ROOT).parts
        )
        integrity_guides = tuple(
            path
            for path in ROOT.rglob("RESEARCH_INTEGRITY_GUIDE.md")
            if "dist" not in path.relative_to(ROOT).parts
        )
        writing_path = SKILL / "references" / "REPORT_WRITING_GUIDE.md"
        integrity_path = SKILL / "references" / "RESEARCH_INTEGRITY_GUIDE.md"
        self.assertEqual(writing_guides, (writing_path,))
        self.assertEqual(integrity_guides, (integrity_path,))
        writing = writing_path.read_text(encoding="utf-8")
        integrity = integrity_path.read_text(encoding="utf-8")
        self.assertNotEqual(writing, integrity)
        for marker in (
            "Synthesis 优先于 Summary",
            "一个段落只完成",
            "Primary Paper 导航",
        ):
            self.assertIn(marker, writing)
        for marker in ("区分证据层级", "SOTA 是高风险表述", "Ablation 不自动证明机制"):
            self.assertIn(marker, integrity)

    def test_doctor_requires_research_integrity_guide(self) -> None:
        doctor = load_module(
            "literature_research_doctor_test", SKILL / "scripts" / "doctor.py"
        )
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture_skill = root / "literature-research"
            shutil.copytree(SKILL, fixture_skill)
            (fixture_skill / "references" / "RESEARCH_INTEGRITY_GUIDE.md").unlink()
            result = doctor.run_checks(root / "workspace", fixture_skill)
        references = result["checks"]["references"]
        self.assertFalse(references["RESEARCH_INTEGRITY_GUIDE.md"])
        self.assertFalse(result["healthy"])


class SkillAdapterTests(TestCase):
    harness: Any

    @classmethod
    def setUpClass(cls) -> None:
        cls.harness = load_module(
            "literature_research_harness_test",
            SKILL / "scripts" / "harness.py",
        )

    def _invoke(self, arguments, *, runtime_factory=None):
        stdout = StringIO()
        stderr = StringIO()
        keywords = {"stdout": stdout, "stderr": stderr}
        if runtime_factory is not None:
            keywords["runtime_factory"] = runtime_factory
        status = self.harness.main(arguments, **keywords)
        output = stdout.getvalue() if status == 0 else stderr.getvalue()
        return status, json.loads(output)

    def test_adapter_exposes_required_command_surface(self) -> None:
        script = (SKILL / "scripts" / "harness.py").read_text(encoding="utf-8")
        required = {
            "doctor",
            "create-run",
            "view",
            "inspect",
            "search-papers",
            "retain-papers",
            "inspect-source",
            "read-source",
            "put-paper-analysis",
            "put-approach-family",
            "merge-approach-family",
            "put-finding",
            "retire-finding",
            "put-open-problem",
            "retire-open-problem",
            "put-gap",
            "resolve-gap",
            "reopen-gap",
            "set-paper-status",
            "request-completion",
            "completion-view",
            "completion-inspect",
            "completion-read-source",
            "submit-completion",
            "delivery-view",
            "delivery-inspect",
            "delivery-read-source",
            "render-report",
            "publish-report",
            "validate-delivery",
            "reopen-research",
            "close-run",
            "audit-history",
            "wiki-query",
            "wiki-projection",
            "publish-wiki",
        }
        for command in required:
            with self.subTest(command=command):
                self.assertIn(f'"{command}"', script)

    def test_create_and_view_use_public_capability_path(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = root / "request.json"
            request.write_text(
                json.dumps(
                    {
                        "mission": "Map bounded research",
                        "requirements": ["Compare routes"],
                        "scope": "Primary literature",
                        "deliverable_description": "Technical report",
                        "required_artifacts": ["REPORT"],
                    }
                ),
                encoding="utf-8",
            )
            status, created = self._invoke(
                [
                    "--workspace",
                    str(root / "workspace"),
                    "create-run",
                    "--input",
                    str(request),
                ]
            )
            self.assertEqual(status, 0)
            run_id = created["result"]["run_id"]
            status, viewed = self._invoke(
                ["--workspace", str(root / "workspace"), "view", "--run-id", run_id]
            )
            self.assertEqual(status, 0)
            self.assertEqual(viewed["result"]["state_revision"], 1)
            self.assertEqual(viewed["result"]["lifecycle"], "RESEARCH")

    def test_search_maps_pagination_dates_and_all_observation_fields(self) -> None:
        calls = []

        class FakeResearcher:
            def search_papers(self, run_id, revision, query, **options):
                calls.append((run_id, revision, query, options))
                return PaperSearchResult(
                    state_revision=8,
                    total_count=41,
                    hits=(
                        PaperSearchHit(
                            title="Frontier paper",
                            authors=("A. Author",),
                            publication_year=2026,
                            publication_date="2026-08-03",
                            arxiv_id="2608.00001",
                            canonical_url="https://arxiv.org/abs/2608.00001",
                            abstract="Abstract",
                            provider_summary="Summary",
                            provider_score=0.9,
                            citation_count=3,
                            categories=("cs.LG",),
                        ),
                    ),
                )

        class FakeRuntime:
            researcher = FakeResearcher()

        status, output = self._invoke(
            [
                "--workspace",
                "/tmp/unused",
                "search-papers",
                "--run-id",
                "run_example",
                "--expected-revision",
                "7",
                "--query",
                "frontier decoding",
                "--limit",
                "25",
                "--offset",
                "50",
                "--date-from",
                "2025-01-01",
                "--date-to",
                "2026-08-10",
            ],
            runtime_factory=lambda workspace, external: FakeRuntime(),
        )
        self.assertEqual(status, 0)
        self.assertEqual(output["result"]["total_count"], 41)
        self.assertEqual(
            calls[0][3],
            {
                "limit": 25,
                "offset": 50,
                "date_from": "2025-01-01",
                "date_to": "2026-08-10",
            },
        )
        hit = output["result"]["hits"][0]
        self.assertEqual(hit["abstract"], "Abstract")
        self.assertEqual(hit["provider_summary"], "Summary")
        self.assertEqual(hit["provider_score"], 0.9)
        self.assertEqual(hit["citation_count"], 3)
        self.assertEqual(hit["publication_date"], "2026-08-03")

    def test_retain_accepts_complete_adapter_search_output(self) -> None:
        retained = []

        class FakeResearcher:
            def retain_papers(self, run_id, revision, hits):
                retained.extend(hits)
                return {"state_revision": revision + 1, "paper_refs": ["paper_x"]}

        class FakeRuntime:
            researcher = FakeResearcher()

        with TemporaryDirectory() as temporary:
            input_path = Path(temporary) / "search-output.json"
            input_path.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "command": "search-papers",
                        "result": {
                            "state_revision": 2,
                            "hits": [
                                {
                                    "title": "Observed paper",
                                    "authors": [],
                                    "categories": [],
                                    "other_identifiers": {},
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            status, _ = self._invoke(
                [
                    "retain-papers",
                    "--run-id",
                    "run_example",
                    "--expected-revision",
                    "2",
                    "--input",
                    str(input_path),
                ],
                runtime_factory=lambda workspace, external: FakeRuntime(),
            )
        self.assertEqual(status, 0)
        self.assertEqual(len(retained), 1)
        self.assertEqual(retained[0].title, "Observed paper")

    def test_errors_are_machine_readable_and_redact_token(self) -> None:
        token = "test-secret-value"

        def failing_factory(workspace, external):
            raise RuntimeError(f"provider rejected {token}")

        previous = os.environ.get("DEEPXIV_TOKEN")
        os.environ["DEEPXIV_TOKEN"] = token
        try:
            status, output = self._invoke(
                [
                    "search-papers",
                    "--run-id",
                    "run_example",
                    "--expected-revision",
                    "1",
                    "--query",
                    "query",
                ],
                runtime_factory=failing_factory,
            )
        finally:
            if previous is None:
                os.environ.pop("DEEPXIV_TOKEN", None)
            else:
                os.environ["DEEPXIV_TOKEN"] = previous
        self.assertEqual(status, 2)
        self.assertFalse(output["ok"])
        self.assertNotIn(token, json.dumps(output))
        self.assertIn("[REDACTED]", output["error"]["message"])

    def test_harness_doctor_returns_nonzero_when_environment_is_unhealthy(self) -> None:
        previous = os.environ.pop("DEEPXIV_TOKEN", None)
        try:
            with TemporaryDirectory() as temporary:
                status, output = self._invoke(["--workspace", temporary, "doctor"])
        finally:
            if previous is not None:
                os.environ["DEEPXIV_TOKEN"] = previous
        self.assertEqual(status, 1)
        self.assertFalse(output["ok"])
        self.assertFalse(output["result"]["checks"]["deepxiv_token"]["present"])

    def test_adapter_does_not_import_storage_write_boundaries(self) -> None:
        script = (SKILL / "scripts" / "harness.py").read_text(encoding="utf-8")
        for forbidden in (
            "JsonResearchRunRepository",
            "LocalArtifactStore",
            ".save(",
            "state.json",
            "json_patch",
        ):
            self.assertNotIn(forbidden, script)


class StandalonePackageTests(TestCase):
    def test_packager_builds_relocatable_runtime_and_doctor_passes(self) -> None:
        packager = load_module(
            "literature_skill_packager_test", ROOT / "scripts" / "package_skill.py"
        )
        with TemporaryDirectory() as temporary:
            fixture_root = Path(temporary) / "source"
            shutil.copytree(
                SKILL, fixture_root / ".claude" / "skills" / "literature-research"
            )
            shutil.copytree(
                ROOT / "src" / "my_search_harness",
                fixture_root / "src" / "my_search_harness",
            )
            destination = packager.package_skill(fixture_root)

            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertTrue(
                (destination / "references" / "RESEARCH_INTEGRITY_GUIDE.md").is_file()
            )
            retired_example = "technical-" + "route-survey.md"
            self.assertFalse((destination / "examples").exists())
            self.assertFalse(
                any(path.name == retired_example for path in destination.rglob("*"))
            )
            self.assertEqual(
                (destination / "runtime" / "requirements.txt").read_text(
                    encoding="utf-8"
                ),
                "deepxiv-sdk==0.3.1\n",
            )
            self.assertTrue(
                (
                    destination
                    / "runtime"
                    / "src"
                    / "my_search_harness"
                    / "runtime"
                    / "capabilities.py"
                ).is_file()
            )

            outside = Path(temporary) / "outside"
            outside.mkdir()
            environment = os.environ.copy()
            environment["CLAUDE_SKILL_DIR"] = str(destination)
            environment["DEEPXIV_TOKEN"] = "doctor-placeholder"
            environment.pop("PYTHONPATH", None)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(destination / "scripts" / "doctor.py"),
                    "--workspace",
                    str(outside / "workspace"),
                ],
                cwd=outside,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            diagnosis = json.loads(completed.stdout)
            self.assertTrue(diagnosis["healthy"])
            self.assertTrue(
                diagnosis["checks"]["references"]["RESEARCH_INTEGRITY_GUIDE.md"]
            )

            imported = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import my_search_harness; print(my_search_harness.__file__)",
                ],
                cwd=outside,
                env={**environment, "PYTHONPATH": str(destination / "runtime" / "src")},
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(str(destination) in imported.stdout)

            for path in destination.rglob("*"):
                if path.is_file() and path.suffix in {".md", ".py", ".sh", ""}:
                    retired_workspace = "." + "vibe"
                    self.assertNotIn(
                        retired_workspace, path.read_text(encoding="utf-8")
                    )


class WikiCliBridgeTests(TestCase):
    """wiki-projection and publish-wiki over the simplified Wiki service.

    Claude synthesizes Wiki pages from a projection and performs the semantic
    review outside the harness; ``publish-wiki`` accepts ``source_runs``
    (preserved from the prior ``wiki-projection``) plus the synthesized
    ``pages``. Python validates structure and provenance deterministically and
    publishes a versioned local build, recording ``source_runs`` verbatim as
    honest build provenance. A stale ``source_runs`` is allowed, not rejected;
    ``is_current()`` detects staleness. Invalid structure or provenance raises
    ``WikiBuildError`` before publication. Wiki failure never affects run state.
    """

    harness: Any

    @classmethod
    def setUpClass(cls) -> None:
        cls.harness = load_module(
            "literature_research_harness_wiki_test",
            SKILL / "scripts" / "harness.py",
        )

    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "workspace"
        self._build_closed_complete_run()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _build_closed_complete_run(self) -> None:
        """Build a CLOSED+COMPLETE run via the real LocalV1Runtime.

        Reuses the same construction path as test_wiki._create_complete_run so the
        CLI bridge is exercised against genuine authoritative state, not a fake.
        """
        from my_search_harness.domain import (
            CompletionVerdict,
            LiteratureSource,
            SourceRelation,
        )
        from my_search_harness.runtime import (
            CreateRunRequest,
            DeliveryCommands,
            JsonResearchRunRepository,
            LocalArtifactStore,
            ResearchCommands,
        )

        repository = JsonResearchRunRepository(self.workspace / "runs")
        artifacts = LocalArtifactStore(repository.root)
        research = ResearchCommands(repository)
        delivery = DeliveryCommands(repository, artifacts)
        created = research.create_run(
            CreateRunRequest(
                mission="Map methods",
                requirements=("Map accepted knowledge",),
                scope="A Wiki CLI fixture",
                deliverable_description="No artifact required",
            )
        )
        retained = research.retain_papers(
            created.run_id,
            created.state_revision,
            (
                PaperSearchHit(
                    title="Representative paper",
                    authors=("Ada Author",),
                    publication_year=2026,
                    publication_date="2026-08-03",
                    doi="10.1000/wiki-cli",
                ),
            ),
        )
        paper_ref = retained.paper_refs[0]
        approach = research.put_approach_family(
            created.run_id,
            retained.state_revision,
            name="Method A",
            core_idea="Use accepted evidence",
            representative_paper_refs=frozenset({paper_ref}),
        )
        source = frozenset(
            {
                LiteratureSource(
                    paper_ref=paper_ref,
                    relation=SourceRelation.SUPPORTS,
                )
            }
        )
        finding = research.put_landscape_finding(
            created.run_id,
            approach.state_revision,
            statement="Method A improves the bounded task",
            approach_refs=frozenset({approach.entity_ref}),
            sources=source,
        )
        problem = research.put_open_problem(
            created.run_id,
            finding.state_revision,
            statement="Generalization remains open",
            approach_refs=frozenset({approach.entity_ref}),
            sources=source,
        )
        gap = research.put_investigation_gap(
            created.run_id,
            problem.state_revision,
            description="Run-local gap must not enter Wiki input",
        )
        requested = research.request_completion_check(
            created.run_id,
            gap.state_revision,
            "Ready for closure",
        )
        completed = research.submit_completion_check(
            created.run_id,
            requested.state_revision,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("Accepted state covers the contract",),
        )
        delivery.close_run(created.run_id, completed.state_revision)
        self.run_id = created.run_id
        self.finding_ref = finding.entity_ref
        self.paper_ref = paper_ref

    def _invoke(self, arguments):
        stdout = StringIO()
        stderr = StringIO()
        status = self.harness.main(arguments, stdout=stdout, stderr=stderr)
        output = stdout.getvalue() if status == 0 else stderr.getvalue()
        return status, json.loads(output)

    def _source_runs(self) -> list:
        """Return the current projection source_runs via ``wiki-projection``.

        Mirrors the real flow: Claude calls ``wiki-projection`` first and
        carries the returned ``source_runs`` into ``publish-wiki`` as honest
        build provenance.
        """
        status, output = self._invoke(
            ["--workspace", str(self.workspace), "wiki-projection"]
        )
        self.assertEqual(status, 0, output)
        return output["result"]["source_runs"]

    def _publish_input(self, slug: str = "methods") -> dict:
        return {
            "source_runs": self._source_runs(),
            "pages": [
                {
                    "slug": slug,
                    "title": "Methods",
                    "markdown": "# Methods\n\nAccepted cross-run knowledge.",
                    "contributing_refs": [
                        {
                            "run_id": self.run_id,
                            "research_ref": self.finding_ref,
                        }
                    ],
                }
            ],
        }

    def test_wiki_projection_returns_only_closed_complete_runs(self) -> None:
        status, output = self._invoke(
            ["--workspace", str(self.workspace), "wiki-projection"]
        )
        self.assertEqual(status, 0, output)
        runs = output["result"]["runs"]
        source_runs = output["result"]["source_runs"]
        self.assertEqual(1, len(runs))
        self.assertEqual(1, len(source_runs))
        self.assertEqual(self.run_id, runs[0]["run_id"])
        self.assertEqual(self.run_id, source_runs[0]["run_id"])
        self.assertEqual(
            self.finding_ref, runs[0]["findings"][0]["ref"]
        )

    def test_publish_wiki_accepts_source_runs_and_pages(self) -> None:
        input_path = self.root / "publish.json"
        input_path.write_text(
            json.dumps(self._publish_input()), encoding="utf-8"
        )
        status, output = self._invoke(
            [
                "--workspace",
                str(self.workspace),
                "publish-wiki",
                "--input",
                str(input_path),
            ]
        )
        self.assertEqual(status, 0, output)
        wiki_path = Path(output["result"]["wiki_path"])
        self.assertTrue((wiki_path / "current.json").is_file())
        build_id = json.loads(
            (wiki_path / "current.json").read_text(encoding="utf-8")
        )["build"]
        build_dir = wiki_path / "builds" / build_id
        self.assertTrue((build_dir / "INDEX.md").is_file())
        self.assertTrue((build_dir / "pages" / "methods.md").is_file())
        self.assertEqual(
            self.run_id,
            output["result"]["manifest"]["source_runs"][0]["run_id"],
        )

    def test_invalid_provenance_fails_before_publication(self) -> None:
        invalid_input = self.root / "invalid.json"
        invalid_input.write_text(
            json.dumps(
                {
                    "source_runs": self._source_runs(),
                    "pages": [
                        {
                            "slug": "invalid",
                            "title": "Invalid",
                            "markdown": "# Invalid",
                            "contributing_refs": [
                                {
                                    "run_id": self.run_id,
                                    "research_ref": "gap_nonexistent",
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        status, output = self._invoke(
            [
                "--workspace",
                str(self.workspace),
                "publish-wiki",
                "--input",
                str(invalid_input),
            ]
        )
        self.assertEqual(status, 2, output)
        self.assertEqual("WikiBuildError", output["error"]["type"])
        self.assertFalse((self.workspace / "wiki" / "current.json").exists())

    def test_stale_publication_allowed_and_is_current_detects_it(self) -> None:
        # Step A: run A is already built in setUp. Capture its source_runs and
        # the page built from that projection.
        source_runs_a = self._source_runs()
        run_a_id = self.run_id
        finding_a_ref = self.finding_ref
        page_a = {
            "slug": "methods",
            "title": "Methods",
            "markdown": "# Methods\n\nBuilt from run A only.",
            "contributing_refs": [
                {"run_id": run_a_id, "research_ref": finding_a_ref}
            ],
        }

        # Step B: build run B. This closes COMPLETE and makes the current
        # projection A+B, so source_runs_a (A only) is now stale.
        self._build_closed_complete_run()
        run_b_id = self.run_id
        finding_b_ref = self.finding_ref
        self.assertNotEqual(run_a_id, run_b_id)
        source_runs_a_b = self._source_runs()
        self.assertEqual(2, len(source_runs_a_b))

        # Step C: publish with the stale source_runs_a. Stale publication is
        # allowed, not rejected — the manifest honestly records A only.
        stale_input = self.root / "stale.json"
        stale_input.write_text(
            json.dumps(
                {"source_runs": source_runs_a, "pages": [page_a]}
            ),
            encoding="utf-8",
        )
        status, output = self._invoke(
            [
                "--workspace",
                str(self.workspace),
                "publish-wiki",
                "--input",
                str(stale_input),
            ]
        )
        self.assertEqual(status, 0, output)
        manifest_source_runs = output["result"]["manifest"]["source_runs"]
        self.assertEqual(source_runs_a, manifest_source_runs)

        # Step D: the published Wiki is stale (manifest records A, current
        # projection is A+B). is_current() is False. Re-publish with the fresh
        # source_runs_a_b and pages citing A and B; is_current() becomes True.
        from my_search_harness.runtime import (
            JsonResearchRunRepository,
            LocalWikiPublisher,
            WikiProjectionService,
            WikiService,
        )

        repository = JsonResearchRunRepository(self.workspace / "runs")
        service = WikiService(
            WikiProjectionService(repository),
            LocalWikiPublisher(self.workspace / "wiki"),
        )
        self.assertFalse(service.is_current())

        fresh_input = self.root / "fresh.json"
        fresh_input.write_text(
            json.dumps(
                {
                    "source_runs": source_runs_a_b,
                    "pages": [
                        {
                            "slug": "methods",
                            "title": "Methods",
                            "markdown": "# Methods\n\nBuilt from A+B.",
                            "contributing_refs": [
                                {"run_id": run_a_id, "research_ref": finding_a_ref},
                                {"run_id": run_b_id, "research_ref": finding_b_ref},
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        status, output = self._invoke(
            [
                "--workspace",
                str(self.workspace),
                "publish-wiki",
                "--input",
                str(fresh_input),
            ]
        )
        self.assertEqual(status, 0, output)
        manifest_source_runs = output["result"]["manifest"]["source_runs"]
        self.assertEqual(source_runs_a_b, manifest_source_runs)
        self.assertTrue(service.is_current())


class CrossPlatformLauncherTests(TestCase):
    """Windows / PowerShell standalone launcher compatibility.

    The Runtime is already cross-platform; these tests cover the thin launchers
    (harness.ps1, setup.ps1) and the doctor venv-detection fix so a Windows
    PowerShell user can setup, doctor, and invoke the Skill without Bash/WSL.
    """

    def test_packaged_dist_contains_all_launchers(self) -> None:
        packager = load_module(
            "literature_skill_packager_launcher_test",
            ROOT / "scripts" / "package_skill.py",
        )
        with TemporaryDirectory() as temporary:
            fixture_root = Path(temporary) / "source"
            shutil.copytree(
                SKILL, fixture_root / ".claude" / "skills" / "literature-research"
            )
            shutil.copytree(
                ROOT / "src" / "my_search_harness",
                fixture_root / "src" / "my_search_harness",
            )
            destination = packager.package_skill(fixture_root)
            for relative in (
                "scripts/harness",
                "scripts/harness.ps1",
                "scripts/harness.py",
                "scripts/setup.sh",
                "scripts/setup.ps1",
                "scripts/doctor.py",
            ):
                with self.subTest(relative=relative):
                    self.assertTrue(
                        (destination / relative).is_file(),
                        f"dist missing {relative}",
                    )

    def test_powershell_launchers_are_identical_source_and_dist(self) -> None:
        packager = load_module(
            "literature_skill_packager_consistency_test",
            ROOT / "scripts" / "package_skill.py",
        )
        with TemporaryDirectory() as temporary:
            fixture_root = Path(temporary) / "source"
            shutil.copytree(
                SKILL, fixture_root / ".claude" / "skills" / "literature-research"
            )
            shutil.copytree(
                ROOT / "src" / "my_search_harness",
                fixture_root / "src" / "my_search_harness",
            )
            destination = packager.package_skill(fixture_root)
            for relative in ("scripts/harness.ps1", "scripts/setup.ps1"):
                with self.subTest(relative=relative):
                    source_text = (SKILL / relative).read_text(encoding="utf-8")
                    dist_text = (destination / relative).read_text(encoding="utf-8")
                    self.assertEqual(source_text, dist_text)

    def test_harness_ps1_static_behavior(self) -> None:
        """harness.ps1 resolves the Skill venv, delegates to harness.py, passes args."""
        script = (SKILL / "scripts" / "harness.ps1").read_text(encoding="utf-8")
        self.assertIn(".venv\\Scripts\\python.exe", script)
        self.assertIn("harness.py", script)
        self.assertIn("@args", script)
        self.assertIn("$LASTEXITCODE", script)
        # Must not hardcode a drive letter or depend on cwd.
        self.assertNotIn("C:\\", script)
        self.assertNotIn("Set-Location", script)
        self.assertNotIn("cd ", script)

    def test_setup_ps1_static_behavior(self) -> None:
        r"""setup.ps1 creates .venv, uses Scripts\python.exe, installs requirements."""
        script = (SKILL / "scripts" / "setup.ps1").read_text(encoding="utf-8")
        self.assertIn("-m venv", script)
        self.assertIn(".venv\\Scripts\\python.exe", script)
        self.assertIn("runtime\\requirements.txt", script)
        self.assertIn("--upgrade pip", script)
        # Must not activate the environment or hardcode a drive.
        self.assertNotIn("Activate.ps1", script)
        self.assertNotIn("C:\\", script)

    def test_doctor_detects_windows_venv_layout(self) -> None:
        r"""doctor._reexec_skill_venv must look for Scripts\python.exe, not only bin/python."""
        source = (SKILL / "scripts" / "doctor.py").read_text(encoding="utf-8")
        self.assertIn("Scripts", source)
        self.assertIn("python.exe", source)
        self.assertIn("bin", source)
        # Must not assume POSIX execv works on Windows.
        self.assertIn("os.name", source)

    def test_harness_py_isolation_in_path_with_spaces(self) -> None:
        """bundled runtime loads from a Skill path containing spaces, no PYTHONPATH."""
        harness = load_module(
            "literature_research_harness_isolation_test",
            SKILL / "scripts" / "harness.py",
        )
        with TemporaryDirectory() as temporary:
            # A Skill path with a space mirrors "C:\Users\Test User\My Project\...".
            spaced_root = Path(temporary) / "spaced project"
            spaced_skill = spaced_root / ".claude" / "skills" / "literature-research"
            shutil.copytree(SKILL, spaced_skill)
            environment = os.environ.copy()
            environment["CLAUDE_SKILL_DIR"] = str(spaced_skill)
            environment.pop("PYTHONPATH", None)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(spaced_skill / "scripts" / "harness.py"),
                    "--workspace",
                    str(spaced_root / "workspace"),
                    "--help",
                ],
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            # --help exits 0 and proves the bundled runtime imported cleanly.
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("usage:", completed.stdout)

