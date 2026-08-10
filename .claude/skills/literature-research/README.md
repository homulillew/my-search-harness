# literature-research Claude Code Skill

This package combines a Claude-authored semantic research loop with the deterministic
`my-search-harness` V1 Runtime. Claude decides what to research, how to synthesize it,
whether to request completion, and how to write. Python enforces lifecycle authority,
stable references, revision-safe commands, provenance, accounting, persistence,
citations, and artifact validation.

## Install a standalone export

```bash
cp -R literature-research ~/.claude/skills/literature-research
cd ~/.claude/skills/literature-research
./scripts/setup.sh
export DEEPXIV_TOKEN=...
```

Do not put the token in the skill, a JSON input file, `.env`, or shell script.

Check the installation:

```bash
mkdir -p ~/literature-research-workspace
./scripts/doctor.py --workspace ~/literature-research-workspace
```

Runtime workspace is user or project data and must remain outside the Skill installation
directory. A project may instead use its own `workspace/` directory.

Return to the project where the research data should live before starting Claude Code;
do not use a relative `workspace/` while the Skill installation directory is the current
directory. Then invoke:

```text
/literature-research 调研 LLM KV Cache 优化的主要技术路线和最新进展
```

The project-local version is discovered from `.claude/skills/literature-research` and
uses the repository Runtime source. A standalone export uses `runtime/src` bundled by
the release packager. In both modes, use `${CLAUDE_SKILL_DIR}/scripts/harness`; do not
manipulate the workspace files directly.

## Export from the repository

From the repository root:

```bash
python scripts/package_skill.py
```

The command recreates ignored `dist/literature-research/` from the tracked Skill and the
single authoritative `src/my_search_harness/` source tree. Generated `dist` content is
not committed.

## Layout

```text
literature-research/
├── SKILL.md
├── README.md
├── references/
├── scripts/
└── runtime/
    ├── requirements.txt
    └── src/my_search_harness/
```

See `references/RUNTIME_API.md` for command schemas and
`references/RESEARCH_PROTOCOL.md` for operating guidance.
