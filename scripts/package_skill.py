#!/usr/bin/env python3
"""Build the standalone literature-research Claude Code Skill."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


REQUIREMENTS = "deepxiv-sdk==0.3.1\n"


def package_skill(repository_root: Path | None = None) -> Path:
    root = (
        Path(__file__).resolve().parents[1]
        if repository_root is None
        else repository_root.resolve()
    )
    skill_source = root / ".claude" / "skills" / "literature-research"
    runtime_source = root / "src" / "my_search_harness"
    destination = root / "dist" / "literature-research"

    if not (skill_source / "SKILL.md").is_file():
        raise RuntimeError(f"project Skill is missing: {skill_source}")
    if not (runtime_source / "__init__.py").is_file():
        raise RuntimeError(f"Runtime source is missing: {runtime_source}")
    if destination.parent != root / "dist":
        raise RuntimeError("refusing to package outside the repository dist directory")

    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        skill_source,
        destination,
        ignore=shutil.ignore_patterns(".venv", "__pycache__", "*.pyc", "runtime"),
    )

    bundled_runtime = destination / "runtime"
    bundled_source = bundled_runtime / "src" / "my_search_harness"
    bundled_runtime.mkdir(parents=True)
    (bundled_runtime / "requirements.txt").write_text(REQUIREMENTS, encoding="utf-8")
    shutil.copytree(
        runtime_source,
        bundled_source,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    print(
        json.dumps(
            {
                "ok": True,
                "destination": str(destination),
                "runtime_source": str(runtime_source),
            },
            sort_keys=True,
        )
    )
    return destination


if __name__ == "__main__":
    package_skill()
