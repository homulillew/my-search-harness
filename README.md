# my-search-harness

`my-search-harness` is a formal Claude Code Skill for controlled, recoverable academic
literature research, backed by a deterministic Python V1 Runtime.

Claude owns semantic work: contract interpretation, adaptive search strategy,
primary-source reasoning, synthesis, independent completion judgment, and report writing.
The Runtime owns lifecycle authority, stable references, revision-safe commands,
persistence, resource accounting, provenance, citations, audit, and artifact validation.

> **Status: V1 Runtime implemented; Claude Code Skill packaged**

## Quick start in this repository

Requirements are Python 3.11+ and a DeepXiv token supplied only through the environment:

```bash
python -m pip install -e .
export DEEPXIV_TOKEN=...
.claude/skills/literature-research/scripts/harness --workspace workspace doctor
```

Open Claude Code at the repository root and invoke:

```text
/literature-research 调研 LLM KV Cache 优化的主要技术路线和最新进展
```

The slash command reads the research request from `$ARGUMENTS`, forms an explicit
Research Contract, and drives the existing capability surfaces. It never asks Claude to
edit Repository state or artifacts directly.

## Standalone Skill export

Build a portable package from the current tracked Skill and Runtime source:

```bash
python scripts/package_skill.py
```

This recreates ignored `dist/literature-research/`. Install it with:

```bash
cp -R dist/literature-research ~/.claude/skills/literature-research
cd ~/.claude/skills/literature-research
./scripts/setup.sh
export DEEPXIV_TOKEN=...
mkdir -p ~/literature-research-workspace
./scripts/doctor.py --workspace ~/literature-research-workspace
```

The export bundles `src/my_search_harness` at build time. The repository keeps only one
tracked Runtime source tree; generated `dist/` content is never committed.

In project-local mode, the repository's `workspace/` is valid project data. In
standalone mode, use a workspace outside the Skill installation directory, such as
`~/literature-research-workspace` or the active project's own `workspace/`. Runtime
workspace is user or project data, not Skill installation data.

## Architecture

```text
Claude Code
    ↓ semantic research, completion, and writing
literature-research Skill
    ↓ JSON / CLI typed adapter
public Researcher / Completion Checker / Delivery capabilities
    ↓ deterministic authority and persistence
my-search-harness V1 Runtime
```

Research, Completion, and Delivery capabilities are intentionally separate. Search hits
and source text are observations until Claude explicitly retains and synthesizes them.
Completion uses a fresh verification-only checker. Report style stages share the complete
authoritative Writing Guide; Research Integrity remains a separate boundary.

## Repository layout

```text
.claude/skills/literature-research/  # project Skill and release source
src/my_search_harness/               # single authoritative Runtime source
tests/                               # Runtime and Skill packaging tests
docs/                                # Frozen design and development guidance
examples/                            # curated reports and acceptance summaries
scripts/package_skill.py             # standalone release builder
workspace/                           # ignored runtime data
```

The authoritative report style source is
[`REPORT_WRITING_GUIDE.md`](.claude/skills/literature-research/references/REPORT_WRITING_GUIDE.md).
Runtime composition continues to receive its path explicitly:

```python
pipeline = runtime.report_pipeline(
    planner=planner,
    composer=composer,
    integrator=integrator,
    editor_factory=editor_factory,
    reviser=reviser,
    integrity_reviewer=integrity_reviewer,
    writing_guideline_path=(
        ".claude/skills/literature-research/references/REPORT_WRITING_GUIDE.md"
    ),
)
```

The Runtime does not discover the guide from the current working directory.

## Development authority

- Frozen design: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md),
  [`docs/DOMAIN_MODEL.md`](docs/DOMAIN_MODEL.md), and [`docs/adr/`](docs/adr/).
- Development workflow: [`docs/development/AI_WORKFLOW.md`](docs/development/AI_WORKFLOW.md).
- Learning and module-explanation rules:
  [`docs/development/LEARNING_RULES.md`](docs/development/LEARNING_RULES.md).
- Skill operating protocol:
  [`.claude/skills/literature-research/SKILL.md`](.claude/skills/literature-research/SKILL.md).

## Verification

```bash
PYTHONPATH=src python -m unittest discover -s tests
python -m mypy src tests
python -m black --check src tests
git diff --check
python scripts/package_skill.py
```

Release verification also scans for references to the retired development-workspace
directory and expects no matches.
