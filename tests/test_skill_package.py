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

from my_search_harness.runtime import PaperSearchHit, PaperSearchResult


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
        self.assertLessEqual(len(lines), 300)

    def test_supporting_files_and_executables_exist(self) -> None:
        expected = (
            "README.md",
            "references/RESEARCH_PROTOCOL.md",
            "references/RUNTIME_API.md",
            "references/COMPLETION_GUIDE.md",
            "references/REPORT_WRITING_GUIDE.md",
            "scripts/harness",
            "scripts/harness.py",
            "scripts/doctor.py",
            "scripts/setup.sh",
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

    def test_guide_is_complete_and_is_the_only_tracked_guide(self) -> None:
        guides = tuple(
            path
            for path in ROOT.rglob("REPORT_WRITING_GUIDE.md")
            if "dist" not in path.relative_to(ROOT).parts
        )
        self.assertEqual(guides, (SKILL / "references" / "REPORT_WRITING_GUIDE.md",))
        content = guides[0].read_text(encoding="utf-8")
        self.assertIn("## 1. 写作目标", content)
        self.assertIn("## 10. 最终检查", content)
        self.assertIn("方法名写为 Markdown 超链接", content)
        self.assertIn("认知负担过高的长段", content)


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
                    hits=(
                        PaperSearchHit(
                            title="Frontier paper",
                            authors=("A. Author",),
                            publication_year=2026,
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
