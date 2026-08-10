---
name: literature-research
description: Conduct deep, recoverable academic literature research with DeepXiv search, primary-source reading, explicit synthesis, independent completion checking, and cited report delivery.
---

# Literature Research

Use this skill when the user asks for an academic literature review, technical-route
survey, state-of-the-art analysis, research landscape, or evidence-backed technical
report. Claude is the semantic Researcher; the Python Harness is the deterministic
runtime for authority, persistence, stable references, provenance, accounting, and
validation.

Never edit `state.json`, event logs, report artifacts, or repository files directly.
All observations and mutations must go through `${CLAUDE_SKILL_DIR}/scripts/harness`.

## Read the protocol before acting

Read only the supporting material needed for the current stage:

- [Research protocol](references/RESEARCH_PROTOCOL.md): contracts, adaptive search,
  source reading, synthesis, recovery, and the outer loop.
- [Runtime API](references/RUNTIME_API.md): commands, JSON input shapes, revision
  handling, and error behavior.
- [Completion guide](references/COMPLETION_GUIDE.md): the independent completion
  boundary and PASS / CONTINUE / UNCERTAIN criteria.
- [Report writing guide](references/REPORT_WRITING_GUIDE.md): the authoritative style
  and editorial standard used by all semantic writing stages.
- [Research integrity guide](references/RESEARCH_INTEGRITY_GUIDE.md): evidence-strength,
  benchmark, comparison, causality, recency, and high-risk claim checks used by the
  independent Research Integrity Reviewer.

## Start from the request

Treat `$ARGUMENTS` as the user's research request. If it is empty, ask for the topic,
intended audience, scope, and desired deliverable. Otherwise infer a conservative
initial Research Contract and state the important assumptions before creating it.

Convert the request into:

1. a precise mission;
2. independently checkable requirements;
3. an explicit in-scope / out-of-scope boundary;
4. a deliverable description;
5. required artifacts, normally `REPORT` for a written survey.

Do not encode fixed paper counts as completion conditions. Workload expectations can
guide exploration, but coverage, evidence quality, recency, contradiction handling,
and requirement satisfaction determine completion.

Run the environment check first:

```bash
${CLAUDE_SKILL_DIR}/scripts/harness --workspace workspace doctor
```

Create a run using a JSON file, not shell-escaped inline JSON:

```bash
${CLAUDE_SKILL_DIR}/scripts/harness --workspace workspace create-run \
  --input /tmp/research-contract.json
```

Keep runtime data in the chosen workspace, never inside the skill directory.

## Own the semantic outer loop

The Harness does not prescribe a fixed research finite-state machine. Claude owns an
adaptive outer loop:

```text
view current state
→ identify the highest-value uncertainty or gap
→ search, inspect, or read evidence
→ retain selected papers explicitly
→ synthesize durable research objects
→ reassess coverage and contradictions
→ repeat, request completion, or explain a blocker
```

Choose the next action from current evidence. Do not perform a ritual sequence merely
because it appeared in a previous run.

After every state-changing command, use the returned `state_revision` for the next
command. On a revision conflict, discard the stale plan, call `view`, and reason again.

## Search in two complementary modes

Begin with broad discovery queries that reveal terminology, canonical route names,
seminal work, surveys, and competing framings. Vary query vocabulary and route rather
than repeating one prompt.

For requests containing “latest”, “current”, “recent”, “state of the art”, or an
equivalent time-sensitive requirement, run a Frontier Sweep:

```text
broad recent search → inspect current terminology → emerging-term expansion
→ route-specific recent searches → deliberate pagination → reassess coverage
```

Use explicit `--date-from` and `--date-to`, derived from the request and current date.
Do not create frontier queries only by paraphrasing the request. Extract method names,
training algorithms, reward designs, benchmarks, mechanisms, new terminology, and useful
authors from recent hits, then use them as follow-up seeds. Deep surveys normally use a
30–100-result discovery funnel when provider cost permits and observe tens of
deduplicated candidates; retain only the useful subset.

```bash
${CLAUDE_SKILL_DIR}/scripts/harness --workspace workspace search-papers \
  --run-id RUN --expected-revision REV --query "QUERY" \
  --limit 20 --offset 0 --date-from YYYY-MM-DD --date-to YYYY-MM-DD
```

Search output includes provider-reported `total_count`, and hits include publication
date as well as year when available. Use `total_count`, new unique identities, route
novelty, and recent-paper novelty to decide whether to page; do not mechanically exhaust
all results. A first page is discovery input, not proof of coverage, and local date
sorting of retrieved candidates is not a global latest-paper search.

Search hits remain ephemeral observations. If a citation, user input, or known identifier
names a specific paper, use exact title or arXiv ID as a verification/targeted-discovery
fallback, never as a replacement for broad search. Provider semantic search is not
guaranteed exhaustive; record an explicit limitation when a required recent paper or
window cannot be retrieved.

Select useful candidates and call `retain-papers` explicitly. Provider summaries and
abstract snippets may guide selection, but they must not become Findings, PaperAnalysis,
or report claims without appropriate primary-source evidence.

## Inspect before reading

For a retained paper, call `inspect-source` first to obtain provider-supported sections.
Then call `read-source` with a targeted locator for methods, experiments, limitations,
or another specific need. Read the full source only when the structure is unavailable
or broad context is genuinely necessary.

`SourceContent` is ephemeral. Do not treat retrieved text as durable state. Convert the
evidence that matters into a concise `PaperAnalysis`, preserving experimental conditions,
limitations, and useful locators.

## Synthesize periodically

Do not postpone synthesis until the end. After each meaningful cluster of reading,
update the structured landscape:

- `PaperAnalysis` records what a retained paper contributes, shows, and fails to show.
- `ApproachFamily` groups methods sharing a real mechanism, not merely vocabulary.
- `Finding` records a supported cross-paper technical judgment.
- `OpenProblem` records an unresolved field-level question supported by the landscape.
- `InvestigationGap` records work still required for this run or contract.

An Open Problem belongs to the researched domain. A Gap belongs to the current research
process. Do not substitute one for the other.

Use source relations (`SUPPORTS`, `CHALLENGES`, `QUALIFIES`) and locators to preserve
evidence boundaries. Retire or update obsolete semantic objects through explicit
commands instead of silently changing their meaning.

For a deep technical-route survey, normally seek multiple query formulations, more
than one representative method per major route where the literature permits it,
seminal and frontier evidence, competing results, deployment conditions, and explicit
unknowns. These are exploration heuristics, never mechanical completion thresholds.

For an explicitly deep or comprehensive technical-route survey, a corpus of only a
few investigated papers is normally insufficient unless the scope is genuinely narrow.
Tens of deduplicated search candidates across multiple adaptive searches are a normal
exploration scale for a broad field survey. Before requesting Completion from a much
smaller corpus, the Researcher must be able to explain from the Contract and current
landscape why the scope is narrow enough that additional search is unlikely to reveal
a major route, representative method, disagreement, or recent frontier development.
This is workload guidance, not a paper-count or Completion threshold.

Before requesting Completion for a latest/recent task, answer from the retained corpus:
the newest relevant paper date, the searched recent window, the frontier queries used,
whether emerging terminology triggered follow-up searches, and whether pagination added
recent work. This is a Researcher self-check; the fresh Completion Checker still judges
only retained state and the structured landscape, never audit history.

## Resume from authoritative state

When resuming, ignore conversational memory as authority. Recover from:

1. `view` for the current lifecycle, contract, revision, gaps, and landscape;
2. `inspect` for exact objects behind stable references;
3. targeted source reads when evidence must be rechecked;
4. `audit-history` for prior search queries, pagination, filters, and external attempts.

Do not repeat searches blindly. Use the audit trail to identify missing routes, stale
date coverage, or unexamined pages.

## Request independent completion

When the Research Contract appears satisfied, call `request-completion`. Then create a
fresh checker context that has not participated in the research loop and follow
[COMPLETION_GUIDE.md](references/COMPLETION_GUIDE.md).

The fresh Completion Checker may only:

- call `completion-view`;
- call `completion-inspect` for exact retained objects;
- call `completion-read-source` for targeted evidence verification;
- submit PASS, CONTINUE, or UNCERTAIN.

It must not search, retain papers, mutate research objects, or inherit the Researcher's
private reasoning. CONTINUE must identify concrete blocking gaps; control then returns
to Research. UNCERTAIN is used when available evidence cannot justify either PASS or a
specific repair plan. PASS alone authorizes complete Delivery.

## Deliver a report

In DELIVERY, build the report from a fresh `delivery-view` and targeted inspections.
Load the two authority documents separately:

```text
${CLAUDE_SKILL_DIR}/references/REPORT_WRITING_GUIDE.md
${CLAUDE_SKILL_DIR}/references/RESEARCH_INTEGRITY_GUIDE.md
```

Apply the complete Writing Guide to the Narrative Planner, Report Composer, Editorial
Integrator, fresh Editor, and Reviser. It governs organization, prose, synthesis, and
readability. Create the independent Research Integrity Reviewer in a fresh context with
the complete Integrity Guide, Delivery state, manuscript, and targeted inspection/source
access. The Integrity Guide is its primary rubric; it does not receive the Writing Guide
as a style rubric and does not perform prose polish.

The semantic stages are:

```text
Narrative Planner
→ Report Composer
→ Editorial Integrator
→ Fresh Editor
→ Reviser when needed
→ Research Integrity Reviewer
→ deterministic citation renderer
→ publish-report
→ validate-delivery
→ close-run
```

If integrity review finds a Delivery-only writing or citation repair, revise in Delivery.
If it finds an unsupported claim or missing research, call `reopen-research` and return
to the research loop.

The fresh Editor reviews the whole report semantically: sections must be driven by
research questions or judgments rather than paper order; taxonomy must state its
classification criterion; each paragraph should make one main judgment and start with
a self-contained claim; giant paragraphs, abstract-noun chains, bureaucratic or
translated prose should be repaired. Representative methods must serve synthesis,
carry the required first-use hyperlink, and lead naturally from evidence to gaps. These
are editorial judgments, not Python paragraph-length or style validators.

The fresh Integrity Reviewer checks author claims versus independent evidence,
single-paper evidence versus consensus, correlation versus causation, ablation versus
causal mechanism, numerical gains versus statistical significance, SOTA and
generalization scope, benchmark validity, robustness and efficiency dimensions,
test-time compute/tool budgets, comparison fairness, recency and absolute claims,
corpus-bounded absence, and citation-to-claim alignment. It returns the existing typed
integrity result without a numeric score.

Integrity may inspect Delivery state and retained objects, reread targeted sources, and
review the manuscript. It must not search broadly, retain papers, mutate Research state,
create Findings, or silently add evidence. Completion asks whether Research State
satisfies the Contract; Integrity asks whether the report faithfully represents that
accepted State. Keep these authority boundaries separate.

When a retained primary paper has a canonical URL, hyperlink the first formal occurrence
of its method or system name to that URL. This navigation link never replaces a structured
citation. Keep citations close to the technical judgments they support.

Paragraph rhythm, natural Chinese, terminology, title density, and appropriate table use
are semantic editorial criteria. Do not ask the Harness to encode them as structural
validators. Preserve experimental conditions and qualifications while improving prose.

Use `render-report` to resolve structured citation tokens deterministically, then pass
the rendered content to `publish-report`. Only close after `validate-delivery` succeeds.

## Handle failures explicitly

The adapter emits one JSON object to stdout. Successful commands return `"ok": true`.
Failures return nonzero and machine-readable JSON on stderr without a stack trace.

External search and source attempts may advance the revision even when the provider
fails because resource usage is authoritative. Read the error's `state_revision` or
call `view` before retrying. Never replay with a stale revision.

Do not print, persist, or include `DEEPXIV_TOKEN` in JSON input, audit rationale, reports,
examples, logs, or commits. The runtime reads it only from the environment.

## Finish visibly

At handoff, report the run ID, final lifecycle, delivered artifact path, major coverage,
known limitations, and whether completion was PASS, CONTINUE, or UNCERTAIN. If blocked,
name the exact missing environment capability or unresolved research gap.
