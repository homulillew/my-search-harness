# 002 — Architecture Questions

> Status: Architecture Study
> This document defines the **questions that must be answered before implementation**.
>
> It does **not** contain accepted Architecture Decisions.
>
> Each section records:
>
> * why the question matters;
> * constraints already established by Project Vision and Reference Study;
> * plausible alternatives;
> * what remains deliberately undecided;
> * what evidence would justify a decision.

---

# 1. Purpose

前一阶段已经完成：

```text
PROJECT_VISION
      ↓
Reference Studies
      ↓
Reference Synthesis
      ↓
Design Goals & Principles
      ↓
Core Problem Model
```

现在我们已经知道 Harness 必须解决六个核心问题：

```text
Control
State
Evidence
Context
Completion
Knowledge
```

下一步不是立刻把这些名词做成：

```text
engine.py
state.py
evidence.py
wiki.py
```

而是先找出：

> **哪些架构选择一旦做错，会迫使后续整个系统围绕错误假设生长？**

本阶段只回答这些高杠杆问题。

---

# 2. Question 1 — Who Owns the Research Loop?

## Why This Must Be Decided

本项目已经确定：

```text
Claude Code = Agent Runtime / Loop Driver
Python Harness = Research Runtime
```

但这还没有回答更细的问题：

> **Claude Code 驱动 Loop 到什么程度？**

存在一个连续谱：

```text
Claude owns everything
        │
        │
        ▼
Claude chooses semantic actions
Python enforces lifecycle
        │
        │
        ▼
Python orchestrates phases
Claude fills semantic steps
```

如果 Python 拿走太多控制：

```text
Python
→ decides search
→ decides read
→ decides reflect
→ decides retry
```

就会重新长成旧 Harness 的 Workflow Engine。

但如果 Python 完全不约束：

```text
Claude
→ arbitrary actions
→ arbitrary state mutation
→ arbitrary completion
```

则 Harness 失去存在意义。

---

## Known Constraints

已经明确：

```text
Claude owns semantic research policy.

Python owns deterministic reliability.
```

以及：

```text
Phase ≠ Action.
```

Python 可以决定：

```text
this action is illegal
budget is exhausted
review is required
state transition is invalid
```

但不应该替 Claude 判断：

```text
SEARCH or READ?
which paper is semantically most useful?
what query wording is best?
```

---

## Alternatives

### Alternative A — Prompt-Owned Loop

Claude 完全按照 Skill / Prompt 自己维护：

```text
phase
budget
allowed actions
review
```

Python 只提供工具。

#### Advantages

* 最简单；
* Claude 自由度最大；
* Runtime 很薄。

#### Risks

* 关键 invariant 依赖 prompt discipline；
* 容易绕过 budget/state transition；
* 与 spec-kit-harness 的已知弱点相同。

---

### Alternative B — Claude Semantic Loop + Python Control Authority

Claude 决定：

```text
next semantic research action
```

Python 决定：

```text
whether action is legal
whether resource remains
how state changes are committed
whether control obligation changes
```

例如：

```text
RESEARCH

Claude:
SEARCH gap G03

Python:
valid gap?
budget?
duplicate?
phase permits search?

→ execute
→ persist
```

#### Advantages

* 保留研究灵活性；
* deterministic invariant 真正 enforce；
* 与现有 Design Principles 最一致。

#### Risks

* 必须非常清楚地区分：
  `control obligation` 和 `semantic recommendation`；
* Runtime API 稍有膨胀就可能变成 orchestrator。

---

### Alternative C — Python Orchestrated Research Loop

Python 主动执行：

```text
while not complete:
    ask Claude what to do
    dispatch handler
```

甚至自己决定：

```text
search
read
analyze
review
```

#### Advantages

* 控制集中；
* 普通程序员容易理解；
* 自动化程度高。

#### Risks

* 建立第二 Agent Runtime；
* 重复 Claude Code 的职责；
* 极易重现旧 Harness control-flow explosion。

---

## Current Direction to Test

最强候选：

```text
Alternative B
```

但本阶段不正式接受。

---

## Decision Must Clarify

最终 Decision 必须明确：

```text
What can Claude choose?

What can Python reject?

What state can Claude request to mutate?

What state can only Runtime derive?

What is a control obligation?

What is a semantic action?
```

---

# 3. Question 2 — What Is the Smallest Useful Lifecycle?

## Why This Must Be Decided

Lifecycle 是系统骨架。

如果过细：

```text
SEARCH
READ
CITATION
REFLECT
VERIFY
REVISE
```

会形成 phase explosion。

如果过粗：

```text
RUNNING
DONE
```

又无法约束 Review、Synthesis、Resume。

当前 hypothesis：

```text
PLAN
 ↓
RESEARCH ↺
 ↓
REVIEW
 ↓
SYNTHESIZE
 ↓
DONE / PARTIAL
```

但它目前仍然只是 hypothesis。

---

## Known Constraints

Lifecycle 应表达：

```text
meaningful authority / obligation changes
```

而不是：

```text
which tool is currently being used
```

因此：

```text
SEARCH
READ
FOLLOW_REFERENCE
COMPARE
```

原则上属于 Action。

---

## Alternatives

### Alternative A — 2-State

```text
ACTIVE
DONE
```

#### Advantages

极简。

#### Problems

很难表达：

```text
review authority
synthesis boundary
partial completion
```

---

### Alternative B — 4-State

```text
RESEARCH
REVIEW
SYNTHESIZE
DONE
```

Research Contract 在 run 创建前完成，不设 PLAN phase。

#### Advantages

更薄。

#### Questions

* Planning 是否只是初始化动作？
* Contract amendment 如何表达？

---

### Alternative C — 5-State

```text
PLAN
RESEARCH
REVIEW
SYNTHESIZE
DONE / PARTIAL
```

#### Advantages

生命周期意图清晰。

#### Risks

PLAN 是否真的值得成为 phase，
还是只是 ResearchRun 初始化状态？

---

## Decision Must Clarify

```text
What creates a phase boundary?

Which state changes require a lifecycle transition?

Is PARTIAL a phase or terminal outcome?

Can REVIEW return to RESEARCH?

What happens when budget is exhausted but review says CONTINUE?
```

---

## Required Property

无论最终选多少 Phase：

> **Adding a new Research Action must not normally require adding a new Lifecycle Phase.**

---

# 4. Question 3 — What Is the Persistent Research State?

## Why This Must Be Decided

这是 Domain Model 的入口问题。

当前研究产生很多概念：

```text
ResearchRun
ResearchContract
ResearchQuestion
Gap
Query
Paper
Evidence
Criterion
Contradiction
TechnicalRoute
ReviewVerdict
Budget
Event
```

如果所有名词都变成独立 Entity：

> State Model 会过度设计。

如果全部塞进：

```text
state.json
```

又会失去语义边界和可维护性。

---

## Known Constraints

State 必须支持：

```text
resume
audit
dedup
context rendering
review
report/wiki projection
```

并且：

```text
Persistent State ≠ Context
```

---

## Main Question

真正需要决定的是：

> **什么信息具有独立身份和生命周期，因此值得成为一等 State Object？**

---

## Candidate Categories

### Run Control State

```text
phase
budget
run status
timestamps
```

### Research Intent

```text
mission
research questions
criteria
scope
```

### Discovery State

```text
queries
papers
retrieval results
```

### Knowledge State

```text
evidence
gaps
contradictions
routes
```

### Review State

```text
review verdict
unresolved items
```

### Event State

```text
what happened
when
why
```

---

## Alternatives

### Alternative A — One Aggregate State Object

```text
state.json
```

contains everything.

#### Advantages

* simplest persistence;
* simple snapshot.

#### Risks

* frequent rewrites;
* weak append-only history;
* conceptual coupling.

---

### Alternative B — Typed State Files by Concern

For example:

```text
contract.json
state.json
papers.json
evidence.jsonl
analysis.json
events.jsonl
```

#### Advantages

* semantic separation;
* JSONL works naturally for ledgers/events;
* bounded context rendering easier.

#### Risks

* cross-file consistency;
* more persistence machinery.

---

### Alternative C — Embedded Database

SQLite or similar.

#### Advantages

* transactions;
* querying;
* relationships.

#### Risks

* V1 complexity;
* harder human inspection;
* likely premature.

---

## Decision Must Clarify

```text
Which objects have stable IDs?

Which records are append-only?

Which records may mutate?

Which state is run-local?

Which state survives across runs?

What is authoritative vs derived?
```

---

# 5. Question 4 — What Exactly Counts as Evidence?

## Why This Must Be Decided

Evidence is the trust boundary of the entire product.

If Evidence is weak:

```text
Report grounding
Review
Wiki
Completion
```

all become weak.

If Evidence is too heavyweight:

```text
every note requires exact PDF replay,
hashing,
full-text archive,
complex provenance graph
```

Research becomes expensive and brittle.

---

## Known Constraints

Must preserve:

```text
Paper ≠ Evidence

Source ≠ Interpretation

Work ≠ Proof
```

Evidence must be traceable to a Paper and Locator.

---

## Candidate Minimal Shape

Conceptually:

```text
Evidence
├── stable id
├── paper reference
├── locator
├── source material
├── research question / gap
├── interpreted claim
├── stance
└── interpretation provenance
```

This is not yet a schema.

---

## Architecture Choices

### Source Passage

Should Evidence require:

```text
verbatim excerpt
```

or can it initially store:

```text
locator + source reference
```

and load the passage later?

---

### Locator Strength

Candidates:

```text
page
section
paragraph
text span
provider-specific locator
```

More precision improves traceability,
but PDF parsing makes stable locators difficult.

---

### Interpretation

Should Evidence store:

```text
semantic interpretation
```

as durable state?

If yes, how do we distinguish:

```text
source_reported
researcher_interpretation
```

---

### Acceptance

Does Evidence exist immediately when Claude extracts it?

Or do we distinguish:

```text
proposed evidence
accepted evidence
refuted evidence
excluded evidence
```

---

### Reuse

Can one Evidence object support multiple:

```text
claims
criteria
routes
research questions
```

or should Evidence remain tightly question-bound?

---

## Mechanical Boundary

Potential Python checks:

```text
ID valid
paper exists
locator exists
required fields present
citation resolves
duplicate detection
```

Open question:

```text
Should excerpt text be mechanically verified
against cached source text in V1?
```

---

## Semantic Boundary

Claude must still determine:

```text
relevance
stance
meaning
scope
support quality
```

---

## Decision Must Clarify

> **What is the minimum Evidence object strong enough to support Review, Report, Wiki and Resume without rebuilding the old heavyweight evidence pipeline?**

---

# 6. Question 5 — How Should Context Be Rendered?

## Why This Must Be Decided

Externalized state only helps if Claude receives the right subset.

Too much:

```text
context overload
```

Too little:

```text
state blindness
```

Therefore Context Renderer is potentially a first-class architectural concern.

---

## Known Constraints

```text
Context = View of State
```

and:

```text
Bound the view, not the knowledge.
```

---

## Candidate Decision Views

Current candidates:

```text
PLAN_SEARCH
SELECT_READ
ANALYZE_EVIDENCE
REVIEW
SYNTHESIZE
```

But these should not automatically become classes or files.

---

## Alternatives

### Alternative A — One General Status View

One bounded summary for every semantic action.

#### Advantages

Simple.

#### Risks

Likely either too broad or insufficient.

---

### Alternative B — Action-Specific Views

Different semantic tasks receive different state slices.

#### Advantages

* stronger context economy;
* easier to control leakage;
* Review can receive independent view.

#### Risks

* renderer complexity;
* too many views could become another workflow language.

---

### Alternative C — Claude Queries State Directly

Harness only exposes low-level state read APIs.

Claude decides what to fetch.

#### Advantages

Flexible.

#### Risks

* repeated tool calls;
* Claude may forget critical context;
* difficult deterministic budget control.

---

## Selection Questions

Context rendering must decide:

```text
How are critical gaps always preserved?

How are old queries summarized?

How many evidence records are shown?

How is relevance determined?

How does REVIEW avoid seeing irrelevant researcher process?

Do we measure exact tokens or use simpler serialized-size bounds?
```

---

## Decision Must Avoid

Do not turn Context Renderer into:

```text
semantic planner
```

It should decide:

```text
what state is visible
```

not:

```text
what research conclusion Claude should reach
```

---

# 7. Question 6 — What Is the Completion Contract?

## Why This Must Be Decided

This is the central Loop Engineering question.

Without an explicit Completion Contract:

```text
Researcher
→ feels done
→ stops
```

With an overly mechanical contract:

```text
score > threshold
→ done
```

the Harness manufactures false certainty.

---

## Known Constraints

```text
Researcher cannot self-declare DONE.

Evidence ≠ Completion.

Budget exhaustion ≠ Completion.

Critical criteria are non-compensatory.
```

---

## Research Contract

Before Research begins, some minimally checkable contract is required.

Possible stable fields:

```text
mission
research questions
critical requirements
budget
evidence expectations
deliverable expectations
```

But research may discover:

```text
new routes
new gaps
new contradictions
new questions
```

Therefore we must distinguish:

```text
Stable Research Contract
```

from:

```text
Evolving Research Landscape
```

---

## Request Review

What allows Researcher to say:

```text
ready_for_review
```

Possible signals:

```text
all known critical gaps addressed
low marginal gain
researcher believes criteria are satisfied
budget nearly exhausted
```

These may trigger Review.

None independently proves completion.

---

## Review Output

Need to define overall outcome semantics:

```text
PASS
CONTINUE
UNCERTAIN
PARTIAL
```

Possible criterion state:

```text
covered
partial
missing
```

Possible unresolved reasons:

```text
missing_evidence
conflicting_evidence
source_unavailable
ambiguous_scope
interpretation_uncertain
```

---

## Review Authority

Need to decide:

```text
who may write ReviewVerdict?
who may transition to SYNTHESIZE?
who may mark terminal completion?
```

Python can enforce authority separation.

Claude Code protocol handles context independence.

---

## Budget Edge Case

Must explicitly define:

```text
Reviewer = CONTINUE
Budget = exhausted
```

Possible outcomes:

```text
PARTIAL
request user budget extension
explicit unresolved delivery
```

Never:

```text
silently continue
```

---

## Decision Must Clarify

> **What observable, evidence-backed conditions make research eligible to stop, and who has authority to make that judgment?**

---

# 8. Question 7 — How Does Accepted Evidence Become Reusable Knowledge?

## Why This Must Be Decided

Research has two downstream products:

```text
current-run report
cross-run memory
```

Both derive from research state, but serve different purposes.

If each builds its own truth:

```text
Evidence
Report truth
Wiki truth
```

Citation Drift and knowledge drift become inevitable.

---

## Known Constraints

Strong direction:

```text
Accepted Evidence
       │
       ├── Report
       └── Wiki
```

Wiki must not become an independent Evidence Source of Truth.

---

## Report Questions

Need to decide:

```text
Does every important report claim reference Evidence IDs?

Does synthesis create intermediate claims?

How are internal Evidence IDs turned into reader-facing citations?

What citation integrity can Python verify?

What semantic support requires Review?
```

---

## Wiki Questions

Need to decide:

```text
What knowledge belongs in the Wiki?

What remains run-local?

Is Wiki fully rebuildable?

How is a page identified across runs?

How does new Evidence update existing knowledge?

How are contradictions rendered?

How is stale knowledge detected?
```

---

## Page Taxonomy

Current hypothesis:

```text
Paper
Route
Topic
```

But this remains deliberately undecided.

Architecture should first answer:

> What stable knowledge identities actually exist?

Then choose page taxonomy.

---

## Projection Alternatives

### Alternative A — LLM-Maintained Pages

```text
old page + new evidence
→ LLM rewrite
```

#### Advantages

Readable, flexible.

#### Risks

Summary drift and second truth source.

---

### Alternative B — Deterministic Structured Projection

```text
accepted evidence
→ rules/templates
→ wiki
```

#### Advantages

Rebuildable and auditable.

#### Risks

May be less readable and less expressive.

---

### Alternative C — Structured Core + Generated Narrative

```text
structured evidence-backed view
+
optional regenerated prose
```

#### Advantages

Potential balance.

#### Risks

Need clear rule for which layer is authoritative.

---

## Future-Run Rule

Must preserve:

```text
Wiki
→ prior / lead

Paper
→ verification source
```

not:

```text
Wiki claim
→ automatically accepted evidence
```

---

# 9. Cross-Cutting Question — What Must Python Enforce?

This question cuts across all seven decisions.

We should explicitly classify invariants into three groups.

---

## A. Must Be Mechanically Enforced

Likely candidates:

```text
ID validity
schema validity
atomic persistence
state transition legality
budget accounting
dedup
evidence reference existence
citation resolution
provider error distinction
write authority
```

---

## B. Must Be Semantically Judged

Likely candidates:

```text
paper relevance
query quality
claim interpretation
evidence support
contradiction meaning
coverage sufficiency
technical route synthesis
```

---

## C. Protocol-Level Guarantees

Things Python cannot fully prove:

```text
reviewer truly has fresh context
Claude considered all alternatives
Claude was not cognitively biased
```

These require:

```text
Claude Code execution protocol
+
bounded views
+
review discipline
```

The architecture should not invent fake deterministic guarantees for them.

---

# 10. Cross-Cutting Question — What Must Remain Untrusted?

The Harness consumes external:

```text
PDF
HTML
metadata
API responses
repository content
```

All retrieved content is:

```text
research data
```

not:

```text
instruction
```

Therefore Architecture must preserve:

> **Retrieved content cannot authorize tool execution, modify Harness rules, or change completion criteria.**

Also:

```text
provider failure
≠
empty research result
```

Read/search/parse failures must fail closed or remain explicitly typed.

---

# 11. Decision Order

These Architecture Questions have dependencies.

Recommended order:

```text
Q1 Loop Ownership
        ↓
Q2 Lifecycle
        ↓
Q3 Persistent State
        ↓
Q4 Evidence Contract
        ↓
Q5 Context Rendering
        ↓
Q6 Completion Contract
        ↓
Q7 Knowledge Projection
```

Reason:

```text
Loop ownership
determines runtime boundary.

Lifecycle
determines authority transitions.

State
determines what exists.

Evidence
defines the trust-bearing research object.

Context
defines how Claude sees that state.

Completion
depends on Evidence + State + Review authority.

Knowledge Projection
depends on accepted Evidence semantics.
```

Do not design Wiki before Evidence.

Do not design Completion before authority and lifecycle.

Do not design Context before State.

---

# 12. ADR Entry Criteria

Not every answer needs an ADR.

Create an ADR when a decision:

```text
changes system boundaries
is costly to reverse
affects multiple modules
controls an important invariant
has credible alternatives
```

Examples likely worthy of ADR:

```text
Claude vs Python loop ownership
Lifecycle model
Evidence authority / minimum contract
Completion authority
Wiki source-of-truth relationship
```

Examples that may not deserve ADR:

```text
exact CLI command name
small file naming convention
default page word limit
minor formatting choice
```

---

# 13. Required ADR Evidence

Any formal ADR created from this plan should include:

```text
Problem

Constraints

Reference Evidence

Alternatives

Decision

Why

Trade-offs

Consequences

Validation
```

Reference Evidence should contain:

```text
Supporting evidence
Counter-evidence
Non-transferable details
```

The purpose is not to prove:

> “other projects do this.”

The purpose is to explain:

> **why this decision is appropriate for our problem.**

---

# 14. What Is Still Deliberately Undecided

At the end of this Architecture Questions phase, we have still **not** chosen:

```text
number of Python modules
Pydantic vs dataclasses
JSON file names
JSON vs JSONL exact split
CLI syntax
provider implementation
Paper status enum
exact Evidence schema
exact ReviewVerdict schema
exact Context View count
Paper/Route/Topic taxonomy
report citation style
```

Those decisions must follow from answers to higher-level architecture questions.

---

# 15. Exit Criteria for This Phase

Architecture Questions phase is complete when we can explain:

```text
Who drives the loop?

What does Python actually control?

What lifecycle boundaries really exist?

What state must survive?

What exactly is Evidence?

How does Claude receive bounded state?

Who can judge completion?

How do budget and review interact?

What is authoritative after a run?

How do Report and Wiki derive from research state?
```

At that point we can begin writing formal ADRs.

---

# 16. First Decision to Tackle

The first formal Architecture Decision should likely answer:

> **Who owns the research loop, and what authority belongs to the Python Harness?**

Because almost every later question depends on it:

```text
Loop Ownership
      ↓
Lifecycle
      ↓
State mutation authority
      ↓
Context interaction
      ↓
Review authority
      ↓
Runtime API
```

Only after this boundary is explicit should implementation structure begin to emerge.

---

# Final Principle

This phase should continuously resist one failure mode:

```text
we have named a concept
        ↓
therefore create a module for it
```

Instead use:

```text
Problem
↓
Alternatives
↓
Trade-offs
↓
Decision
↓
only then
↓
Implementation
```

The purpose of this document is therefore not to make the architecture look complete.

It is to make the **remaining uncertainty explicit and ordered**, so that each important choice can be made intentionally rather than accidentally encoded into the first implementation.
