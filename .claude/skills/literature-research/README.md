# literature-research Claude Code Skill

This package combines a Claude-authored semantic research loop with the deterministic
`my-search-harness` V1 Runtime. Claude decides what to research, how to synthesize it,
whether to request completion, and how to write. Python enforces lifecycle authority,
stable references, revision-safe commands, provenance, accounting, persistence,
citations, and artifact validation.

The included example is a compact Chinese survey of speculative decoding. It was chosen
because it demonstrates route-level synthesis, primary-paper navigation links, close
citations, experimental qualifications, and explicit unknowns without pretending to be
a new large-scale acceptance run.

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
./scripts/doctor.py --workspace "$PWD/workspace"
```

Then start Claude Code and invoke:

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
├── examples/
├── references/
├── scripts/
└── runtime/
    ├── requirements.txt
    └── src/my_search_harness/
```

See `references/RUNTIME_API.md` for command schemas and
`references/RESEARCH_PROTOCOL.md` for operating guidance.
