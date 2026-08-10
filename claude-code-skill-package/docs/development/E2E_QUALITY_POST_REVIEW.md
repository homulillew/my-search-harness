# E2E Quality Post-Review

This is a development and acceptance-evidence document. It records a quality finding
about a prior end-to-end run and explains the resulting Skill/Protocol policy change
(P0-D). It is **not** a run artifact, not part of any `ResearchRun`, not part of the
Wiki projection, not part of a delivered report, and not a `required_artifact`. It lives
under `docs/development/` alongside other development guidance.

## Loop Engineering finding

The prior E2E run achieved real scale — tens of deduplicated candidates across multiple
searches, a populated landscape, and a rendered report — but it collapsed the intended
adaptive outer loop into staged batching. The run's effective shape was:

```text
search a broad batch → retain all candidates → batch-analysis all papers
→ one synthesis pass → request completion
```

This is a pipeline, not a research loop. Each stage ran to completion before the next
began, and reassessment against updated State did not drive the choice of the next
search or read. The scale came from the batch, not from adaptive turns.

### Why this matters

A search call is not a research iteration. A research iteration starts from a specific
uncertainty, acquires evidence for it, integrates durable State, and reassesses before
the next turn. When discovery, reading, and synthesis are staged instead of interleaved,
two failures follow:

1. **Volume substitutes for judgment.** A large retained corpus looks like coverage, but
   if the queries were not re-derived from reassessed State, the corpus reflects one
   broad sweep rather than targeted uncertainty reduction.
2. **Synthesis becomes report-first.** When all analysis happens in one batch after all
   reading, the landscape tends to be reverse-engineered from the intended report rather
   than built from evidence as it accrues.

### What the prior E2E did and did not prove

It **did** prove:

- The harness command surface works at scale (search, retain, inspect, read,
  put-paper-analysis, put-approach-family, put-finding, put-open-problem, render-report,
  publish-report, close-run).
- Optimistic revision handling survives a long batch of mutations.
- The deterministic citation renderer resolves a large citation map.
- A full CLOSED+COMPLETE run can be produced and validated end-to-end.

It **did not** prove:

- That the adaptive outer loop was actually run. The batch builders in `.e2e/` stage
  search → retain-all → batch-analysis by construction; they are mechanical smoke
  tooling, not a model of loop discipline.
- That queries were re-derived from reassessed State rather than pre-staged.
- That synthesis interleaved with reading rather than following it.
- That completion was requested from reassessed coverage rather than from batch
  exhaustion.

## Workload vs. loop adaptivity

Search volume, paper counts, and analysis counts are **workload telemetry**. They
describe how much work was done, not whether the work was done in an adaptive loop. A
run with high workload and no loop adaptivity is a staged batch; a run with modest
workload and genuine per-turn reassessment is a real research loop. Acceptance must judge
the latter, not count the former.

This is why the `.e2e/` batch builders are now marked `FIXTURE / MECHANICAL SMOKE ONLY`.
They remain useful to exercise the command surface and produce a populated run for
mechanical smoke, but their output must not be cited as evidence of correct loop
discipline.

## What changed (P0-D)

P0-D is a **semantic Skill/Protocol policy fix, not a Runtime change**. It adds no new
Domain entity, no loop FSM, no fixed loop count, and no automatic loop detector. The
changes are:

- **SKILL.md**: a "Keep discovery inside the research loop" section stating that a search
  call is not a research iteration and that discovery, reading, synthesis, and
  reassessment must interleave. The "Own the semantic outer loop" diagram was distilled
  so each turn reads as starting from a specific uncertainty and updating State before
  the next turn, rather than as a staged pipeline.
- **RESEARCH_PROTOCOL.md**: a "Loop discipline" section distinguishing a search loop
  (paging/reformulating queries) from a research loop (the adaptive cycle), naming the
  staged-batching failure mode, and stating that completion is a feedback boundary, not a
  loop counter.
- **`.e2e/` batch builders**: marked as fixture/mechanical smoke only, so their output
  is not mistaken for semantic Research Loop proof.
- **This document**: records the finding and the policy response as development evidence.

## Acceptance implication

A future fresh semantic Researcher E2E must demonstrate the adaptive loop, not just
workload. The acceptance question is not "how many papers were retained?" but "did each
turn of the loop start from a reassessed uncertainty and update State before the next
turn?" This document is the standing record of why that distinction matters.
