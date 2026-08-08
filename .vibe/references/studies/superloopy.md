# Study Note: beefiker/superloopy

> 本 Note 是第五份 Reference Study。
>
> 本项目研究 Superloopy 的**首要目的不是研究 Wiki**，而是研究：
>
> > **怎样用尽可能少的 Runtime 概念，让 Loop 的 DONE 真正依赖 Evidence。**
>
> Superloopy 当前版本额外包含了一套很强的 Research Evidence Discipline，例如 claim ledger、counter-search、retrieval verdict、contradiction handling 和 fail-closed validator。这些内容非常有价值，但属于本 Study 的 **Secondary Finding**。
>
> 本 Study 必须保持两个层次：
>
> ```text
> Primary Study
>     ↓
> Evidence-Gated Loop
>
> Secondary Finding
>     ↓
> Research Evidence Discipline
>
> Future Implication
>     ↓
> Possible Wiki ingestion discipline
> ```
>
> 不应把 Superloopy 本身描述成一个跨-run Local LLM Wiki，因为它当前并没有真正解决跨 Research Run 的知识复利问题。

---

# 1. Snapshot

```text
Repository:
https://github.com/beefiker/superloopy

Studied commit:
9814acc

Study date:
2026-08-09

License:
MIT

Implementation shape:
Claude Code / Codex plugin
+
JavaScript Runtime
+
Skills / Hooks
+
Optional host-native subagents
```

当前版本的 Superloopy 已经明显超过一个极简 coding loop。

它同时包含：

```text
generic loop runtime
evidence artifacts
quality gates
audit
continuation engine
research skill
multi-agent integration
```

因此阅读时必须区分：

> 哪些是它最小 Loop Core 的设计？

与：

> 哪些是后续产品能力不断叠加后的外围复杂度？

否则容易把整个成熟产品误认为 V1 所需最小架构。

---

# 2. Why We Studied It

`REFERENCE_PROJECTS.md` 对 Superloopy 的原始定位是：

```text
strict evidence gates
bounded loop
Claude / Codex integration
proof-oriented completion
```

它主要用于回答：

> 怎样让 Agent 不能仅凭自己的状态描述宣布完成？

前四份 Reference 已经分别帮助我们理解：

```text
spec-kit-harness
→ State externalization / bounded context

old-search-harness
→ Rich state 如何错误膨胀成 control-flow complexity

paper-qa
→ Paper Search / Reading / Evidence / Synthesis 的研究语义

spec-kit-loop
→ Maker / Checker / Completion Authority
```

Superloopy 应该进一步回答：

```text
Evidence 到底如何进入 Completion Gate？

做了工作与证明完成如何区分？

哪些验证可以由 Runtime 机械执行？

哪些验证必须保留给 Semantic Reviewer？

一个 Evidence-Gated Loop 最小需要多少状态？
```

它最值得我们的地方不是：

> “它有很多成熟功能。”

而是：

> **它真的把 Evidence Artifact 和 Completion Condition 绑定到了 Runtime。**

---

# 3. Architecture in One Diagram

先忽略其 Research Skill、Crew、Hooks 等外围能力，Superloopy 的核心 Loop 可以压缩为：

```text
User Brief
    ↓
Plan
├── Goals
└── Criteria
    ↓
Agent does work
    ↓
Evidence Artifact
    ↓
Criterion status
    ↓
Quality Gate
    ↓
Aggregate Completion
```

更具体：

```text
                  Agent / Host Runtime
                         │
                         │ does work
                         ▼
                 Evidence-producing action
                         │
                         ▼
                ┌──────────────────┐
                │ Evidence Artifact│
                └────────┬─────────┘
                         │
                 Runtime validates:
                 - exists
                 - inside evidence root
                 - regular file
                 - non-empty
                 - valid path
                         │
                         ▼
                   Criterion PASS
                         │
                         ▼
                Goal completion check
                         │
                         ▼
                 Plan quality gate
                         │
                         ▼
               Aggregate Completion
```

最重要的关系是：

```text
Work
≠
Proof

Proof
≠
Completion

Completion
=
Evidence-backed criteria
+
gate
```

---

# 4. Core Loop State

Superloopy 的最小 Loop State 比它外围功能表现出来的复杂度要小得多。

核心 `Plan` 大致包含：

```text
Plan
├── version
├── mode
├── goals[]
├── aggregateCompletion
├── evidencePath
├── ledgerPath
└── repositoryBinding
```

每个 Goal：

```text
Goal
├── id
├── title
├── objective
├── status
├── attempt
├── createdAt
├── updatedAt
└── criteria[]
```

每个 Criterion：

```text
Criterion
├── id
├── kind
├── scenario
├── essential
├── status
├── artifact
└── capturedAt
```

Light Mode 默认只创建少量核心 criterion，例如：

```text
happy path
risk / failure path
```

较重模式才增加 regression 等额外 criterion。

这说明一个重要事实：

> **Evidence-Gated Completion 本身并不需要复杂 State Machine。**

真正不可缺少的状态只是：

```text
Goal
+
Criterion
+
Evidence Binding
+
Completion State
```

其余：

```text
crew
continuation engine
audit state
hooks
research waves
claim ledger
```

都是在解决更具体的问题。

---

# 5. Primary Question 1 — What Is the Minimal Loop State?

## Finding

Superloopy 的最小闭环不是：

```text
PLAN
ACT
REFLECT
VERIFY
REVISE
AUDIT
FINALIZE
...
```

而更接近：

```text
Goal
   ↓
Criteria
   ↓
Work
   ↓
Evidence
   ↓
Gate
   ↓
Complete
```

生命周期并不需要和所有工作动作一一对应。

### Why This Matters

这和我们从 `old-search-harness` 得到的结论完全一致：

> **Action 不应该自动升级成 Lifecycle Phase。**

Superloopy 的 Runtime 真正关心的不是 Agent 做了：

```text
edit
test
review
inspect
```

哪一种动作。

它关心的是：

```text
这个 criterion 有没有可信 Evidence？
```

### Transferability

对我们的 Literature Research Harness，可以映射为：

```text
Research Contract
      ↓
Research Criteria
      ↓
Research Actions
      ↓
Accepted Evidence
      ↓
Review
      ↓
Completion
```

而不需要：

```text
SEARCH_PHASE
READ_PHASE
COMPARE_PHASE
VERIFY_PHASE
FOLLOW_CITATION_PHASE
```

---

# 6. Primary Question 2 — When Does the Evidence Gate Run?

Superloopy 并不是在最终一步才第一次检查 Evidence。

Evidence Gate 实际存在多个层次。

## Layer 1 — Evidence Recording

当一个 criterion 被记录为 pass 时，需要绑定一个真实 artifact。

Runtime 不只是接受：

```text
artifact: some/path
```

而会检查：

```text
artifact exists
artifact is under evidence root
artifact is a regular file
artifact is not a symlink
artifact is not empty
small artifact is not whitespace-only
```

也就是说：

> **Evidence Reference 必须指向真实存在的东西。**

---

## Layer 2 — Criterion Completion

Criterion 的完成不是单纯：

```text
criterion.status = pass
```

而是：

```text
Criterion
+
Evidence Artifact
```

形成一个可检查状态。

---

## Layer 3 — Goal / Plan Completion

最终完成前：

```text
essential criteria
```

必须通过。

对于最终 Goal：

```text
all plan criteria
```

也必须通过。

---

## Layer 4 — Quality Gate / Audit

最终 Aggregate Completion 前还会验证：

```text
quality gate
audit provenance
evidence artifacts
```

部分可机械重跑的 Evidence 甚至会在完成时重新执行。

因此真正结构更接近：

```text
Evidence recorded
      ↓
Criterion eligible
      ↓
Goal eligible
      ↓
Plan gate
      ↓
Aggregate complete
```

---

# 7. Primary Question 3 — How Is Evidence Bound to Completion?

这是 Superloopy 对我们最重要的贡献。

Agent 不能仅说：

```text
"I tested it."
```

就让 Criterion PASS。

Runtime 会把 Evidence Artifact 直接写入 Criterion State：

```text
criterion.status
criterion.artifact
criterion.capturedAt
```

因此：

```text
Criterion PASS
```

不是一个孤立布尔值。

它携带：

```text
what proved it
when it was captured
```

---

## Core Principle

> **Completion claims must point to evidence artifacts.**

也就是说：

```text
Status sentence
≠
Proof
```

Agent 的：

```text
done
works
looks correct
tested successfully
```

都只是语言。

真正能进入 Gate 的是：

```text
Evidence Artifact
```

---

## Literature Research Adaptation

我们的对应关系应该是：

```text
Research Criterion
      ↓
Accepted Evidence IDs
      ↓
Evidence IDs exist
      ↓
Paper exists
      ↓
Locator exists
      ↓
Semantic Reviewer judges support
```

例如：

```text
Criterion:
“Verifier-guided stopping 路线已有代表论文和实证证据”

Evidence:
E012
E017
E023
```

Python 可以机械验证：

```text
E012 exists
E017 exists
E023 exists

their paper_id resolves
their locators exist
their schemas are valid
```

Reviewer 再判断：

```text
这些 Evidence 是否真的足以满足 Criterion？
```

---

# 8. Primary Question 4 — Work Is Not Proof

Superloopy 非常明确地区分：

```text
doing work
```

与：

```text
proving work
```

对于命令型任务，`prove` 实际执行：

```text
spawn command
      ↓
capture stdout
capture stderr
capture exit code
      ↓
derive pass / fail
      ↓
write transcript artifact
      ↓
bind artifact to criterion
```

因此：

```text
"I ran the tests"
```

没有意义。

真正的 Proof 是：

```text
the command actually ran
+
the observed result was captured
```

---

## Literature Research Equivalent

对我们而言：

```text
"I read Paper X"
```

只是 Work。

它不是 Proof。

真正的 Proof Candidate 是：

```text
Evidence E017
├── paper_id
├── locator
├── excerpt
├── claim
├── stance
└── interpretation
```

所以我们可以明确：

> **Reading is work. Evidence is proof.**

同理：

```text
Search
```

也是 Work。

搜索结果不是 Evidence。

```text
Paper candidate
```

也不是 Evidence。

必须经过：

```text
Search
→ Select
→ Read
→ Extract
→ Interpret
→ Evidence
```

---

# 9. Primary Question 5 — Mechanical Integrity vs Semantic Validity

这是 Superloopy 最值得迁移的架构边界之一。

Superloopy 自己明确区分：

```text
command-backed criterion
```

与：

```text
manual / commandless criterion
```

对于 command-backed criterion：

Runtime 可以：

```text
re-run command
observe exit code
re-derive pass/fail
```

机械保证很强。

对于 manual criterion：

Runtime 最多证明：

```text
artifact exists
```

却不能证明：

> Artifact 内容表达的判断在语义上是正确的。

---

## This Maps Perfectly to Research

我们的 Evidence Integrity 也天然分两层。

### Mechanical Evidence Integrity

Python 可以验证：

```text
Evidence ID exists
Paper ID resolves
Locator exists
Schema valid
Citation link valid
Excerpt present
State transition legal
Budget valid
No duplicate ID
```

### Semantic Evidence Validity

Claude Reviewer 判断：

```text
这段原文是否真的支持 Claim？

这个 interpretation 是否忠于原文？

这是 supporting 还是 qualifying？

所谓 contradiction 是否真的构成矛盾？

Coverage 是否足够？

Critical Gap 是否仍然存在？
```

---

## Important Principle

> **Hard evidence does not mean Python decides truth.**

Hard Evidence 的真正含义是：

> Python 保证 Reviewer 看到的是一个真实存在、可追溯、结构合法的 Evidence Object，而不是 Agent 自己凭空声称的结论。

因此：

```text
Python
=
Evidence Integrity

Claude
=
Evidence Meaning
```

这应该成为 V1 最重要的架构边界之一。

---

# 10. Primary Question 6 — How Does Superloopy Keep the Core Lightweight?

虽然当前 Superloopy 产品已经不算特别轻量，但它最核心的 Evidence Gate 思想其实很简单。

最小闭环：

```text
Brief
↓
Goal
↓
Criteria
↓
Evidence
↓
Gate
↓
Complete
```

它不要求：

```text
full workflow graph
multi-agent framework
graph database
complex planner
LLM API runtime
```

Agent Runtime 仍然由：

```text
Claude Code / Codex host
```

承担。

Superloopy 自己强调：

> 它 rides the host，而不是自己 spawn / own 一个完整 Agent Runtime。

这和我们的核心边界高度一致：

```text
Claude Code = Agent Runtime
Python Harness = Research Runtime
```

---

# 11. What “Lightweight” Does NOT Mean

不能因为 Superloopy 自称 lightweight，就认为整个当前仓库都应该迁移。

当前版本已经包含：

```text
Continuation Engine
Stop Hooks
Crew
Role Routing
Audit State
Quality Gates
Research Skill
Source Grading
Claim Ledger
Auto Resume Guidance
Host Integration
```

这些都是长期演进出来的能力。

所以我们应该区分：

```text
Lightweight Core
```

和：

```text
Mature Product Surface
```

### Lightweight Core

```text
persistent goal state
criteria
evidence artifact
gate
resume
```

### Mature Product Surface

```text
multi-agent crew
hooks
continuation
auto resume
audit orchestration
complex research protocol
host compatibility
```

我们只应优先借前者。

---

# 12. Core Design Decision 1 — Criterion Must Bind to Evidence

## Problem

Agent 很容易产生：

```text
done
tested
verified
covered
```

这种状态句子。

但状态句子本身没有证明力。

## Superloopy Design

Criterion PASS 必须绑定 Evidence Artifact。

Artifact 必须真实存在，并经过 Runtime Path / File Validation。

## Why

这样：

```text
criterion status
```

不再只是 Agent 的语言输出。

它拥有一个可重新检查的物理锚点。

## Transferability

我们的 Research Criterion 应绑定：

```text
Accepted Evidence IDs
```

而不是：

```text
researcher confidence
```

### Intended Adaptation

```text
criterion
├── status
├── evidence_ids[]
└── unresolved_reason?
```

具体 schema 等 Domain Model 阶段再决定。

---

# 13. Core Design Decision 2 — Evidence Integrity Is Mechanical

## Problem

即使 Agent 给出 Evidence ID，也可能：

```text
ID 不存在
locator 无效
paper 不存在
artifact 为空
citation 悬空
```

## Superloopy Design

Runtime fail-closed 检查 Evidence Artifact。

## Why

这些都是 deterministic invariants。

不需要浪费 LLM 判断。

## Our Adaptation

Python 应负责：

```text
Evidence schema validation
Paper reference validation
Locator validation
ID uniqueness
Citation reference validation
State consistency
```

这正符合：

> Semantic Policy belongs to Claude. Mechanical correctness belongs to Python.

---

# 14. Core Design Decision 3 — Semantic Truth Remains Outside Mechanical Gate

## Problem

机械 Evidence Integrity 很容易被误解为：

> 只要 artifact 存在，就证明它正确。

## Superloopy Design

它明确承认 Manual Criterion 的 correctness 无法由 Runtime 完全重派生。

## Our Adaptation

Evidence Gate 分两层：

```text
Mechanical Precondition
       ↓
Semantic Review
```

例如：

```text
Mechanical:
E017 exists and resolves

Semantic:
E017 really supports C04
```

Python 不应该试图通过：

```text
keyword overlap
embedding similarity
magic score
```

自动替代语义判断。

---

# 15. Core Design Decision 4 — Completion Is Derived

Superloopy 的 Completion 不是 Agent 直接写：

```text
done = true
```

而是通过：

```text
criteria
→ goals
→ quality gate
→ aggregate completion
```

推导。

这给我们的启发是：

```text
Evidence
      ↓
Criterion Coverage
      ↓
Review Outcome
      ↓
Research Completion
```

而不是：

```text
Researcher:
"I think this is enough."

        ↓

DONE
```

这进一步支持：

> Researcher Cannot Self-Declare DONE.

---

# 16. Core Design Decision 5 — Re-Derive What Can Be Re-Derived

Superloopy 对 command-backed criteria 不完全信任旧状态。

在 audit / completion gate 时，可以重新执行原命令并重新观察结果。

核心哲学：

> **Do not trust stale “pass” when the underlying proof can be reproduced.**

---

## Our Adaptation

论文 Claim 本身不能像：

```text
npm test
```

那样重新执行。

但一些机械事实可以重新派生：

```text
Evidence ID still exists
Paper reference still resolves
Locator still exists
Excerpt still present in cached text
Citation references still valid
Wiki projection still corresponds to accepted evidence
Report citations still resolve
```

因此 V1 可以采用：

> **Re-derive deterministic integrity at review / synthesis boundaries.**

但不要把论文语义判断伪装成可机械重跑。

---

# 17. Secondary Finding — Superloopy Research Evidence Discipline

Superloopy 当前版本包含一个完整 `superloopy-research` Skill。

这并不是我们研究它的原始主任务，但里面有不少值得保留的设计。

主要包括：

```text
retrieval verdict
source grading
claim ledger
counter-search
primary-source requirement
observed / as-of
contradictions
abstention
fail-closed validator
untrusted content
```

这些内容应作为：

> **Secondary Architecture Evidence**

而不是让它取代 Primary Evidence-Gate Study。

---

# 18. Secondary Finding 1 — Retrieval Result Needs a Verdict

Superloopy 强调：

```text
retrieved
```

并不自动意味着：

```text
successfully investigated
```

来源可能是：

```text
ok
partial
blocked
error
empty
```

这非常有价值。

因为：

```text
empty
```

可能意味着：

```text
没有结果
```

也可能意味着：

```text
provider failed
quota exhausted
parser failed
request blocked
```

如果一律当成“没有相关内容”，Research Loop 会错误收敛。

---

## Our Adaptation

Paper provider action 应区分：

```text
retrieval success
no results
provider error
rate limited
partial
unavailable
```

不要让：

```text
provider failure
```

伪装成：

```text
research saturation
```

这可以直接进入 Python Adapter Contract。

---

# 19. Secondary Finding 2 — Contradiction Is a First-Class Outcome

Superloopy Research 不要求所有 Claim 最终变成 verified。

它允许：

```text
verified
unresolved
refuted
deferred
```

并要求 Synthesis 显式保留：

```text
Contradictions
Gaps
```

这和旧 Harness 的 Non-Consensus 经验高度一致。

---

## Our Adaptation

我们的 Evidence 层至少保留：

```text
stance:
supporting
contradicting
qualifying
```

Analysis 层保留：

```text
contradictions[]
open_gaps[]
```

不要在生成 Report/Wiki 时把矛盾自动平均成一个“共识”。

---

# 20. Secondary Finding 3 — Counter-Search Is Useful, but Not Universal

Superloopy 对高风险 Claim 要求：

```text
主动搜索反例
```

这是很好的 Confirmation Bias 防线。

但不能机械迁移成：

> 每个 Literature Claim 都必须做独立 Counter Search。

例如：

```text
"Paper X proposes Method Y."
```

原始 Paper 本身已经是最权威来源。

无需专门找第二篇论文反驳。

---

## Better Rule for Us

Counter-search 更适合：

```text
field-level conclusions
comparative claims
consensus claims
performance superiority claims
causal interpretations
controversial claims
```

而不是所有 Paper-level Fact。

因此：

> Counter-search should be risk/claim-type dependent, not universal.

---

# 21. Secondary Finding 4 — No Universal “Two Sources” Rule

Superloopy 的高风险 web claim 要求：

```text
2+ independent observations
```

这在开放 Web Research 中合理。

但不能直接推导：

> Wiki 每条知识必须有两篇论文支持。

例如：

```text
Paper A introduced Method X.
```

唯一最好的证据就是 Paper A。

所以：

```text
Paper-specific factual claim
→ one authoritative primary paper may suffice

Cross-paper conclusion
→ broader evidence required

Field-level consensus claim
→ multiple independent papers preferred

High-stakes comparative claim
→ stronger corroboration
```

原则：

> **Evidence requirement depends on claim type.**

而不是固定：

```text
N >= 2
```

---

# 22. Secondary Finding 5 — Time / Vintage Is Conditional

Superloopy 的：

```text
observed
as-of
```

对以下类型 Claim 很重要：

```text
pricing
market share
legal status
current product capability
ecosystem state
```

论文调研更常见的是：

```text
publication date
arXiv version
conference version
journal version
```

所以我们不应要求所有 Evidence 都拥有：

```text
observed_at
as_of
```

作为核心语义字段。

更合适的是：

> **Time-sensitive claims require explicit vintage.**

论文则优先保留：

```text
paper version
publication date
retrieved version
```

---

# 23. Secondary Finding 6 — Fail-Closed Evidence Validator

Superloopy 的 `validate-research-evidence.mjs` 是这次 Study 很值得保留的发现。

它真正机械检查：

```text
claim ledger schema
verified status requirements
dependencies
citation resolution
required synthesis sections
blocked-source handling
expected-truth routing
index reachability
```

如果契约被违反：

```text
exit != 0
```

而不是：

> “最好以后修一下。”

---

## Correct Layer for Our Architecture

这个思想首先应该进入：

```text
Evidence Integrity Layer
```

而不是只被理解成：

```text
Wiki lint
```

正确关系：

```text
Raw Research
      ↓
Evidence Validation
      ↓
Accepted Evidence
      ├────────→ Report Projection
      └────────→ Wiki Projection
```

因此一个 Evidence Validator 可以同时保护：

```text
Report
Wiki
Review
Resume
```

---

# 24. Secondary Finding 7 — Retrieved Content Is Data, Not Instruction

Superloopy Research 明确要求：

> 从 Web/API/文件取回的内容只能作为 Evidence Data，不能成为执行指令。

这对我们的系统同样重要。

论文 PDF、HTML、metadata、README 等都属于：

```text
untrusted external content
```

即使其中出现：

```text
ignore previous instructions
run this command
download this file
```

也只能被理解为：

```text
source text
```

而不是 Agent Instruction。

---

## Our Boundary

```text
Claude / Harness Instructions
        ≠
Retrieved Research Content
```

Provider 取得的内容：

```text
may inform research
```

但不能：

```text
authorize tool use
modify harness rules
execute code
change completion rules
```

这值得进入 Security / Provider ADR。

---

# 25. Secondary Finding 8 — Index / Detail Separation

Superloopy Research 使用：

```text
INDEX.md
```

作为日常重读层。

详细 wave artifacts 留在磁盘。

需要时才进入 detail。

核心思想：

> **Write detail down; read summaries back.**

这与：

```text
State persistence, not context persistence
```

完全一致。

---

## Our Adaptation

我们不一定需要：

```text
INDEX.md + wave-N.md
```

文件布局。

但应该保留：

```text
Persistent Rich State
       ↓
Context Renderer
       ↓
Bounded Summary View
       ↓
on-demand details
```

也就是说：

> 借 Context Pattern，不借目录结构。

---

# 26. What We Should Borrow

1. **Work ≠ Proof**
   Search / Read / Analyze 是工作；Evidence 才是可验证的 Research Output。

2. **Criterion 必须绑定 Evidence**
   Completion Criterion 不能只依赖 Agent 的自然语言 self-report。

3. **Mechanical Evidence Integrity**
   ID、path、locator、schema、citation、state transition 交给 Python fail-closed enforce。

4. **Semantic Validity Remains Semantic**
   Evidence 是否真的支持 Claim 交给 Fresh Reviewer。

5. **Completion Is Derived**
   Evidence → Criteria → Review → Completion，而不是 Agent 直接 DONE。

6. **Re-derive deterministic facts at gates**
   可以机械重算的状态不要盲信 cached pass。

7. **Retrieval verdict**
   provider failure / empty / partial / blocked 不得混成一个“无结果”。

8. **Contradictions and abstention are legitimate states**
   unresolved/refuted 不能被静默删除。

9. **Fail-closed Evidence Validator**
   Evidence Contract 应成为可执行 invariant。

10. **Untrusted-content boundary**
    Retrieved content 永远只是数据。

11. **Index / Detail separation**
    Rich state 留磁盘，Context 读取 bounded projection。

---

# 27. What We Should Not Borrow

1. **完整 Plugin / Hook Infrastructure**

```text
Stop hook
Session hooks
Auto-update
Wrapper install
Host-specific glue
```

这些不是 Research V1 核心。

---

2. **完整 Continuation Engine**

我们不需要：

```text
no-progress high water
auto stop hook loop
quota resume scheduler semantics
```

V1 先用简单 Budget + Review Gate。

---

3. **六 Crew / Role System**

```text
franky
zoro
usopp
jinbe
robin
nami
```

是成熟产品的 Agent UX。

我们的 V1 仍然坚持：

```text
one Researcher
+
one Fresh Reviewer
```

---

4. **Coding-specific command proof**

```text
exit code == 0
```

是代码任务的强验证。

论文 Claim 无法如此机械重跑。

我们借的是：

> Evidence binding pattern.

不是 command execution 本身。

---

5. **Universal 2-source rule**

不能规定：

```text
every accepted research claim
requires 2 papers
```

Claim 类型不同，Evidence 要求不同。

---

6. **Full A–E web source ladder**

我们以论文为主。

Source quality 以后可能需要简单分类，但无需直接复制 web-oriented A–E taxonomy。

---

7. **12-surface closed vocabulary**

这是 Web Research 为验证“独立观察”设计的机制。

我们的主要对象是：

```text
Paper
Section
Evidence
```

不存在相同 surface 模型。

---

8. **Expected Truths as universal mechanism**

只在存在 external authority 时有意义。

开放式领域调研不应预先制造“应该是什么”的假设。

---

9. **Per-run Evidence Root 目录照搬**

我们会有自己的 State Layout。

借：

```text
artifact discipline
```

不借：

```text
具体目录结构。
```

---

10. **Superloopy 当前全部 Research Workflow**

当前 Research Skill 已经是一个完整的 exhaustive web research system。

它不是我们的 V1 Architecture Template。

---

# 28. Conflicts with PROJECT_VISION

## 28.1 Strong Alignment — Hard Evidence

PROJECT_VISION：

> Hard evidence.

Superloopy：

```text
criterion pass
must point to evidence artifact
```

高度一致。

---

## 28.2 Strong Alignment — Claude / Runtime Split

Superloopy rides the host runtime。

Runtime 主要负责：

```text
state
artifact validation
gate
audit
```

这与：

```text
Claude Code = Agent Runtime
Python Harness = Research Runtime
```

高度一致。

---

## 28.3 Strong Alignment — Researcher Cannot Self-Declare DONE

Superloopy Completion 由 criteria + gate 推导。

不是 Agent 状态句子。

支持：

```text
Researcher
→ ready_for_review

Reviewer / Gate
→ completion decision
```

---

## 28.4 Alignment — State Persistence

Loop state 和 Evidence 均落盘。

Session 可以丢失。

支持：

> Resume restores process, not conversation.

---

## 28.5 Partial Conflict — Product Complexity

Superloopy 当前已经加入：

```text
crew
hooks
continuation
research orchestration
audit orchestration
```

这与我们的：

> Complexity must earn its place.

存在明显 scope 差异。

因此只学习它的 core invariants。

---

## 28.6 Partial Conflict — Web Research Semantics

Superloopy Research 针对：

```text
web
codebase
market
standards
product research
```

设计。

我们主要针对：

```text
scientific literature
```

Source model 和 Evidence requirements 必须重新适配。

---

# 29. Implications for Our Evidence Model

Superloopy 进一步支持我们当前的 Evidence Model：

```text
Evidence
├── id
├── paper_id
├── research_question / gap
├── claim
├── locator
├── excerpt
├── stance
└── interpretation
```

可以再明确两个层次：

```text
Source Evidence
├── paper_id
├── locator
└── excerpt

Research Interpretation
├── research_question / gap
├── claim
├── stance
└── interpretation
```

Python 能机械检查 Source Layer。

Claude 判断 Semantic Layer。

---

# 30. Implications for Review Gate

Superloopy 说明：

> Evidence existence 和 Evidence correctness 是不同层。

因此我们的 REVIEW 可以设计为：

```text
REVIEW
│
├── Mechanical Preconditions
│   ├── evidence ids valid
│   ├── paper refs valid
│   ├── locators valid
│   ├── required fields present
│   ├── citations resolvable
│   └── budget/state valid
│
└── Semantic Review
    ├── criteria coverage
    ├── evidence support
    ├── contradiction handling
    ├── critical gaps
    └── unresolved issues
```

Python 不负责语义 PASS。

但 Python 可以拒绝：

```text
Reviewer says PASS
while referenced evidence IDs do not exist
```

---

# 31. Implications for Completion

目前最合理的 Completion Chain 越来越清晰：

```text
Accepted Evidence
      ↓
Criterion State
      ↓
Fresh Semantic Review
      ↓
PASS
      ↓
SYNTHESIZE
      ↓
DONE
```

Researcher 不拥有：

```text
DONE
```

Python 不拥有：

```text
semantic PASS
```

Reviewer 不拥有：

```text
inventing evidence
```

三方职责明确。

---

# 32. Secondary Implications for Future Wiki

Superloopy 当前**没有真正跨-run Wiki**。

所以本节只保留对未来 Wiki 的启发，不把它作为本 Reference 的主结论。

有价值的启发包括：

```text
only accepted/verified knowledge should be projected
contradictions should remain visible
projection should be mechanically traceable
stale derived state should be rebuildable
```

但具体问题：

```text
Paper Page
Route Page
Topic Page
cross-run merge
stable identity
page update
future query prior
```

仍然必须由下一份：

```text
formin/spec-kit-wiki
```

Study 专门回答。

---

# 33. Questions Still Open

## Q1 — Criterion 与 Evidence 是一对多还是多对多？

可能：

```text
Criterion
→ Evidence[]
```

同时：

```text
Evidence
→ multiple Claims / Criteria
```

Domain Model 阶段需要决定关系。

---

## Q2 — Evidence Accepted 与 Criterion PASS 是否要分离？

很可能需要：

```text
Evidence accepted
```

只表示：

> 这是一条有效、可追溯的 Evidence。

而：

```text
Criterion pass
```

表示：

> 一组 Evidence 足以满足某个 Research Criterion。

二者不能混成一个 status。

---

## Q3 — 哪些 Mechanical Checks 是 V1 Hard Requirement？

候选：

```text
schema valid
paper exists
locator present
citation resolvable
atomic persistence
evidence IDs valid
```

是否一开始要求：

```text
excerpt mechanically matches parsed source
```

仍待决定。

---

## Q4 — Completion Gate 是否需要独立 Artifact？

Superloopy 有 Quality Gate Artifact。

我们可能只需要：

```text
ReviewVerdict
```

作为持久化对象。

是否另建：

```text
completion.json
```

应由 Domain Model 决定，不应因为 Superloopy 有就复制。

---

## Q5 — 是否需要 Evidence Dependency Graph？

Superloopy Claim Ledger 有：

```text
depends-on
```

这在复杂 Web Claims 中很有价值。

论文调研 V1 是否需要 Claim Dependency 还是可以先只保留：

```text
Evidence
Contradictions
Routes
Gaps
```

目前应保持克制。

---

## Q6 — Evidence Validator 在哪个阶段执行？

可能：

```text
on evidence write
+
before review
+
before synthesis
```

但不要为了“更安全”到处重复跑相同 validation。

需要 Architecture 阶段明确 single responsibility。

---

# 34. Candidate ADRs Influenced by This Project

## Candidate ADR 1

**Completion criteria must bind to real evidence objects; agent self-report is never sufficient proof.**

对应：

```text
Work ≠ Proof
```

---

## Candidate ADR 2

**Mechanical evidence integrity is enforced by Python; semantic evidence validity is judged by Claude.**

对应：

```text
Python = integrity
Claude = meaning
```

---

## Candidate ADR 3

**Research completion is derived from evidence-backed criteria and independent review; Researcher cannot write DONE directly.**

---

## Candidate ADR 4

**Deterministically re-derivable integrity must be rechecked at review/synthesis boundaries rather than trusting stale pass state.**

---

## Candidate ADR 5

**Provider/retrieval failures must remain distinct from semantic absence; failure cannot count as research saturation.**

---

## Candidate ADR 6

**Retrieved content is untrusted data, never executable instruction.**

---

# 35. Cross-Reference with Previous Studies

## spec-kit-harness

告诉我们：

```text
State
≠
Context
```

Superloopy 补充：

```text
State
must include evidence-backed completion facts
```

---

## old-search-harness

告诉我们：

```text
不要让 control-flow complexity
代替 rich state
```

Superloopy 表明：

```text
Goal + Criteria + Evidence + Gate
```

已经足以表达很多 Completion 逻辑。

---

## PaperQA

告诉我们：

```text
Paper
≠
Evidence
```

Superloopy进一步说明：

```text
Evidence
≠
Criterion PASS
```

因此完整层级是：

```text
Paper
↓
Evidence
↓
Criterion Coverage
↓
Review
↓
Completion
```

---

## spec-kit-loop

告诉我们：

```text
Maker
不能给自己最终 verdict
```

Superloopy进一步说明：

```text
即使 Checker / Agent 说 pass
也应该有 Evidence Artifact
作为可检查锚点
```

---

# 36. What This Study Changes in Our Architecture Direction

这份 Study **不推翻**任何已有 Project Vision。

它主要强化三个判断。

第一：

> **Hard Evidence 必须成为 State，而不能只是 Report Citation。**

第二：

> **Evidence Gate 应拆成 Mechanical Integrity + Semantic Judgment。**

第三：

> **Completion 应当是 derived state，而不是 Agent 可直接写入的状态。**

它还提醒我们：

> 不需要为了 Evidence Gate 建一个复杂 Workflow Engine。

最小核心仍然可以很薄。

---

# 37. The Five Sentences to Keep

如果把整份 Study 压缩成五句话，只保留：

> **1. Work is not proof.**

搜索、阅读、分析是工作；Evidence 才是 Proof Candidate。

> **2. A completion criterion must bind to real evidence.**

Agent 的完成声明没有独立证明力。

> **3. Mechanical integrity and semantic truth are different layers.**

Python 验证 Evidence 是否真实、合法、可追溯；Claude 判断 Evidence 是否真的支持 Claim。

> **4. Completion is derived from evidence-backed criteria, not from agent confidence.**

Evidence → Criteria → Review → Completion。

> **5. Re-derive whatever can be deterministically re-derived at the gate.**

能机械重算的完整性不要盲信陈旧状态。

---

# 38. One-Sentence Conclusion

Superloopy 对我们真正重要的不是它后期长出的 Crew、Hooks 或 Exhaustive Research Workflow，而是一个更简单的事实：

> **DONE 必须是一个由真实 Evidence、可检查 Criteria 和 Gate 推导出的状态，而不能只是 Agent 生成的一句话。**

它对我们的直接增量是：

```text
PaperQA:
Paper ≠ Evidence

spec-kit-loop:
Researcher ≠ Final Judge

Superloopy:
Evidence ≠ Completion
```

因此我们的核心链路逐渐清晰为：

```text
Paper
↓
Evidence
↓
Criterion Coverage
↓
Fresh Review
↓
Completion
```

而 Python Harness 的角色也进一步明确：

> **它不判断研究结论是否正确；它确保任何“正确”的声明都必须站在真实、结构合法、可追溯的 Evidence 上。**

Superloopy 当前 Research Skill 中关于 claim ledger、counter-search、retrieval verdict、contradictions、untrusted content 和 fail-closed validator 的能力，作为 Secondary Findings 保留，并在后续 Evidence Architecture 中参考。

但跨-run Wiki 的真正架构问题仍留给：

```text
formin/spec-kit-wiki
```

单独研究。
