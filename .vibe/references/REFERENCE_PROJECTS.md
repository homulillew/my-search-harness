# Reference Projects — Architecture Study Guide

## 1. Purpose

本目录用于记录 `my-search-harness` 在架构设计阶段参考的开源项目、论文和已有实现。

Reference Study 的目标不是：

> 找一个项目复制，然后改成自己的 Harness。

而是：

> 观察不同项目如何解决与我们相同或相邻的问题，并提炼可以支撑本项目 Architecture Decision 的设计证据。

所有参考项目都必须带着明确的问题阅读。

基本阅读方式：

```text
Problem
↓
How does the reference project solve it?
↓
Why might it have chosen this design?
↓
Does the same problem exist in our project?
↓
Which part transfers?
↓
Which part does not transfer?
↓
Can we solve it more simply?
```

禁止采用：

```text
Reference project has X
↓
Therefore we should also implement X
```

---

# 2. Relationship to PROJECT_VISION

Reference Study 必须服从：

```text
.vibe/context/PROJECT_VISION.md
```

而不是反过来。

也就是说：

```text
PROJECT_VISION
      ↓
defines problems and principles
      ↓
Reference Study
      ↓
provides design evidence
      ↓
Architecture Decisions
```

参考项目可以挑战我们对某个具体实现方式的判断。

但它不能因为“功能更多”而自动推翻已经确定的核心产品定位。

尤其必须保持以下边界：

```text
Claude Code = Agent Runtime / Loop Driver

Python Harness = Research Runtime
               + Persistent State
               + Deterministic Actions
               + Guardrails
```

V1 不构建第二套 Python Agent Runtime。

---

# 3. Reference Source Code Location

第三方源码不进入：

```text
my-search-harness/
```

仓库。

统一使用兄弟目录：

```text
parent/
│
├── my-search-harness/
│
└── my-search-harness-references/
    ├── spec-kit-harness/
    ├── spec-kit-loop/
    ├── superloopy/
    ├── paper-qa/
    ├── spec-kit-wiki/
    └── old-search-harness/
```

原因：

1. 避免第三方源码污染 Git history。
2. 避免 GitHub LOC / Language 统计被第三方项目影响。
3. 避免 License 与 Attribution 边界模糊。
4. 避免 Claude Code 搜索本项目源码时误把参考实现当产品代码。
5. 避免以后无意识 copy architecture。
6. 参考源码应该可以随时删除而不影响产品运行。

原则：

> Reference source code is local study material, not project source code.

---

# 4. Pin Reference Versions

Clone 完成后，不应只记录：

```text
main
```

而应该记录实际研究时的：

```text
repository
commit SHA
study date
```

例如：

```text
Repository:
Future-House/paper-qa

Studied commit:
<git rev-parse HEAD>

Studied at:
2026-08-08
```

原因是参考项目会持续变化。

Architecture Decision 必须能够回答：

> 当时我们究竟参考的是哪个版本？

不要求把仓库永久 checkout 到旧版本。

但 Study Note 必须记录 Commit SHA。

---

# 5. Reference Tiers

当前参考项目分为三类。

## Tier 1 — Core References

这些项目直接对应我们的核心架构问题。

当前包括：

```text
formin/spec-kit-harness
formin/spec-kit-loop
Future-House/paper-qa
formin/spec-kit-wiki
beefiker/superloopy
homulillew/search-harness
```

Tier 1 第一阶段全部 Clone。

---

## Tier 2 — Supporting References

这些项目可能有价值，但当前不需要立即 Clone。

未来在遇到具体架构问题时再引入。

例如：

```text
OpenScholar
Pydantic AI Harness
Open Deep Research
llm-wiki-agent
WikiCrow
```

原则：

> 不为了“参考充分”而无限扩大 Reference Corpus。

---

## Tier 3 — Theory / Papers

用于理解思想来源，而不是直接研究代码。

例如：

```text
Harness-1
Loop Engineering
相关 Agent Search / scientific research papers
```

它们后续进入：

```text
research notes / architecture citations
```

但本次 Reference Bootstrap 不要求下载完整论文库。

---

# 6. Core Reference 1 — formin/spec-kit-harness

Repository:

```text
https://github.com/formin/spec-kit-harness.git
```

## Why we study it

这是目前与我们的项目在“Research Harness”概念上最直接接近的参考之一。

它关注：

```text
state externalization
budgeted exploration
evidence curation
claim verification
bounded context
resume
```

我们主要用它回答：

> 一个长程 Research Agent 的状态应该如何从 Conversation 中外置？

---

## Primary Questions

阅读时重点回答：

### Q1

Candidate、Curated Source、Evidence 为什么要分开？

### Q2

哪些状态必须长期持久化？

### Q3

哪些信息应该进入当前 Context？

### Q4

它如何避免把所有历史状态重新塞给 Agent？

### Q5

它如何表达 Budget 和 Stop Condition？

### Q6

它如何处理 Resume？

### Q7

哪些规则依赖 Prompt discipline，哪些是真正 Runtime enforce 的？

---

## What We May Borrow

重点考虑：

```text
externalized durable research state
candidate != accepted evidence
bounded context rendering
explicit budget
resume from disk
evidence pointer / provenance
verification-oriented workflow
```

---

## What We Should NOT Blindly Copy

不直接复制：

```text
Spec Kit integration
prompt-only runtime assumptions
flat research-source model
all Markdown runtime representation
its exact command structure
its exact state schema
```

尤其注意：

我们的边界已经确定为：

```text
Claude Code drives semantic research
Python enforces deterministic research state
```

因此，如果 `spec-kit-harness` 中某些约束主要依赖模型遵守 Prompt，我们要判断：

> 是否应该在我们的 Python Harness 中真正 enforce？

---

## Intended Adaptation

我们想从中学习的是：

> State Externalization。

不是：

> Spec Kit Extension Architecture。

---

# 7. Core Reference 2 — formin/spec-kit-loop

Repository:

```text
https://github.com/formin/spec-kit-loop.git
```

## Why we study it

它直接对应本项目的：

> Loop Engineering

问题。

主要回答：

> 当 Agent 可以长时间自主迭代时，怎样避免它自己做、自己检查、自己宣布完成？

---

## Primary Questions

### Q1

Loop Contract 中真正不可缺少的字段是什么？

### Q2

为什么 maker 不能给自己最终 verdict？

### Q3

Checker 独立性的实际价值是什么？

### Q4

PASS / FAIL / UNCERTAIN 比 numeric score 好在哪里？

### Q5

Budget 在 Loop 中是什么角色？

### Q6

哪些状态值得持久化？

### Q7

它如何防止 Loop 无限运行？

---

## What We May Borrow

重点考虑：

```text
explicit loop contract
checkable done criteria
bounded iteration
maker/checker separation
externalized loop state
PASS / FAIL / UNCERTAIN
independent verification
```

---

## What We Should NOT Blindly Copy

不直接复制：

```text
Spec Kit workflow
coding-task-specific criteria
worktree isolation
human sign-off as mandatory research requirement
comprehension debt as a first-class research subsystem
five separate loop commands
```

我们的论文调研场景不等于 Coding Loop。

尤其：

> Human Sign-off 对代码发布很重要，但不意味着每次文献 Research Run 都必须人工签字才能结束。

---

## Intended Adaptation

我们的适配方向应该更接近：

```text
Researcher
    ↓
ready_for_review
    ↓
Fresh Semantic Review
    ↓
PASS / CONTINUE / UNCERTAIN
```

而不是复制完整 Spec Kit Loop Workflow。

---

# 8. Core Reference 3 — Future-House/paper-qa

Repository:

```text
https://github.com/Future-House/paper-qa.git
```

## Why we study it

这是 Tier 1 中最重要的：

> Scientific Literature Research

参考项目。

它和其他 Loop/Harness 项目不同。

它真正面对：

```text
scientific papers
paper retrieval
document reading
evidence gathering
citation-grounded answers
```

因此它主要帮助我们解决：

> Research Loop 内部的论文检索与 Evidence Retrieval 应如何组织？

---

## Primary Questions

### Q1

Paper Search 和 Evidence Gathering 为什么分离？

### Q2

一篇“相关论文”如何进一步变成 query-specific evidence？

### Q3

论文如何进入 Index / Corpus？

### Q4

Document Reading 如何分块？

### Q5

Evidence 如何排序或筛选？

### Q6

最终 Answer 如何限制在 Evidence 上？

### Q7

Query refinement 如何发生？

### Q8

哪些步骤是 deterministic retrieval，哪些步骤依赖 LLM？

### Q9

Citation 与原始 document context 如何保持关系？

### Q10

它为了通用科学 RAG 引入了哪些我们不需要的复杂度？

---

## What We May Borrow

重点考虑：

```text
Paper Search != Evidence Retrieval
query-specific evidence gathering
scientific document ingestion
metadata normalization
citation-aware answer generation
contextual evidence selection
iterative query refinement
```

---

## What We Should NOT Blindly Copy

不要默认复制：

```text
its complete RAG stack
its model abstraction stack
all supported document readers
all metadata providers
its entire indexing infrastructure
its agent framework/runtime
all configuration options
```

PaperQA 是成熟、通用的科学 RAG 系统。

我们的目标更窄：

> Claude Code Literature Research Harness。

因此：

> Learn its research semantics; do not inherit all of its infrastructure.

---

## Intended Adaptation

我们尤其关注：

```text
Paper
  !=
Evidence
```

以及：

```text
Search
→ select paper
→ inspect paper
→ gather evidence
→ synthesize
```

这一语义分层。

---

# 9. Core Reference 4 — formin/spec-kit-wiki

Repository:

```text
https://github.com/formin/spec-kit-wiki.git
```

## Why we study it

它直接对应本项目的：

> Local LLM Wiki / Knowledge Accumulation

能力。

我们希望一次 Research Run 的有价值知识不会随着 Report 完成而消失。

---

## Primary Questions

### Q1

什么知识值得进入长期 Wiki？

### Q2

Raw Source 和 Wiki Knowledge 如何区分？

### Q3

Source Registry 的作用是什么？

### Q4

Wiki 页面如何引用来源？

### Q5

已有 Page 如何 Update，而不是无限 append？

### Q6

Conflict 如何保留？

### Q7

Lint / consistency check 解决什么问题？

### Q8

Wiki 如何成为 future query 的 prior knowledge？

---

## What We May Borrow

重点考虑：

```text
persistent Markdown knowledge
source-aware pages
compounding knowledge
incremental update
citation discipline
conflict visibility
lint / consistency checks
```

---

## What We Should NOT Blindly Copy

不默认复制：

```text
Spec Kit integration
its exact page taxonomy
its exact ingest commands
all project-code-oriented semantics
full query interface
```

---

## Intended Adaptation

我们目前更倾向：

```text
Accepted Evidence
      ↓
Wiki Projection
      ↓
Paper / Route / Topic pages
```

Wiki 是：

```text
Derived State
```

而不是 Evidence Source of Truth。

这是阅读 `spec-kit-wiki` 时尤其需要检查的差异。

---

# 10. Core Reference 5 — beefiker/superloopy

Repository:

```text
https://github.com/beefiker/superloopy.git
```

## Why we study it

它是一个比大型 Agent Framework 更接近我们设计哲学的轻量 Loop Harness。

核心关注：

```text
strict evidence gates
bounded loop
Claude / Codex integration
proof-oriented completion
```

它主要帮助我们回答：

> 怎样用尽可能少的 Runtime 概念，让 Loop 的 DONE 真正依赖 Evidence？

---

## Primary Questions

### Q1

它最小的 Loop State 是什么？

### Q2

Evidence Gate 在什么时候执行？

### Q3

Evidence 如何与 completion condition 绑定？

### Q4

它如何区分“做了工作”和“证明工作完成”？

### Q5

它怎样保持 lightweight？

### Q6

哪些实现是 coding-specific，不能直接迁移到 Research？

---

## What We May Borrow

重点考虑：

```text
plan → act → evidence → gate
proof-oriented completion
small control surface
explicit blockers
evidence survives conversation
```

---

## What We Should NOT Blindly Copy

不直接复制：

```text
coding-specific evidence rules
its plugin packaging
all CLI UX
all preservation/audit features
current JavaScript implementation architecture
```

尤其不要因为它具备更多成熟功能，就扩大我们的 V1 scope。

---

## Intended Adaptation

我们主要借：

> Done is a verified state, not a sentence generated by the Agent.

---

# 11. Core Reference 6 — homulillew/search-harness

Repository:

```text
https://github.com/homulillew/search-harness.git
```

Local reference name:

```text
old-search-harness
```

## Why we study it

这是本项目最特殊的 Reference。

它既是：

> Positive Reference

也是：

> Negative Reference。

它已经实现了大量真实工程能力。

同时也真实暴露了第一版架构复杂度如何增长。

因此不能只把它看作“旧代码”。

它是我们最重要的：

> Architecture Experiment Result。

---

## Positive Questions

重点识别哪些已有实现经过真实开发后仍然值得保留。

例如：

```text
provider adapters
evidence ledger
schema validation
resume
fixtures
tests
error handling
atomic state concepts
```

回答：

### Q1

哪些模块是真正稳定、独立、可迁移的？

### Q2

哪些测试可以转化为 V2 characterization test？

### Q3

哪些 provider logic 不依赖旧 Orchestrator？

### Q4

哪些 Evidence invariants 已经被证明有价值？

---

## Negative Questions

更加重要的是回答：

### Q5

为什么 Orchestrator 最终变得巨大？

### Q6

哪些 Action 被错误升级成 Lifecycle Phase？

### Q7

哪些 feature 没有证明价值就进入了 Core？

### Q8

哪些 artifact 互相重复表达同一状态？

### Q9

哪些 Loop 实际上是另一个 Loop 的补丁？

### Q10

哪些质量机制制造了 false precision？

### Q11

哪些功能应该删除，而不是重构？

---

## Things We May Reuse

候选包括：

```text
external provider knowledge
selected data normalization
evidence validation logic
fixtures
test cases
resume failure cases
error handling experience
```

但每一项都必须重新证明其边界仍符合 V2。

---

## Things We Must NOT Recreate

明确警惕：

```text
phase explosion
giant orchestrator
scalar sufficiency score
multiple competing loops
report revision state explosion
citation graph as core lifecycle
mandatory GitHub mapping
LoopEngineer as main phase
premature hash/audit complexity
```

---

## Intended Adaptation

旧仓库不是：

> V2 的代码模板。

它更应该被使用为：

> V2 的实验数据。

---

# 12. Cross-Project Study Matrix

完成阅读时，不要只写六份独立摘要。

最后必须横向回答这些问题。

| Architecture Question  | spec-kit-harness   | spec-kit-loop   | PaperQA          | spec-kit-wiki     | Superloopy     | Old Harness     |
| ---------------------- | ------------------ | --------------- | ---------------- | ----------------- | -------------- | --------------- |
| State externalization  | Primary            | Important       | Secondary        | Important         | Important      | Implemented     |
| Research semantics     | Primary            | Low             | Primary          | Secondary         | Low            | Primary         |
| Loop termination       | Important          | Primary         | Secondary        | Low               | Primary        | Overgrown       |
| Evidence model         | Primary            | Important       | Primary          | Citation-oriented | Primary        | Implemented     |
| Resume                 | Primary            | Primary         | Secondary        | Persistent        | Important      | Implemented     |
| Context control        | Primary            | Secondary       | Important        | Secondary         | Secondary      | Complex         |
| Knowledge accumulation | Low                | Memory only     | Corpus/index     | Primary           | Low            | Implemented     |
| Scientific papers      | No                 | No              | Primary          | No                | No             | Primary         |
| Claude Code fit        | Conceptual         | Strong          | Indirect         | Strong            | Strong         | Strong          |
| Complexity warning     | Prompt enforcement | Coding-specific | Mature RAG stack | Wiki scope        | Feature growth | Primary warning |

这张表不是最终结论。

它只是规定后续 Study 必须进行横向比较。

---

# 13. Architecture Questions the Reference Study Must Answer

Reference Study 完成以后，我们至少应该更有把握回答以下问题。

## State

```text
最小 Persistent Research State 到底包含什么？
```

## Control

```text
哪些生命周期状态真正必要？
```

## Action Interface

```text
Claude Code 和 Python Harness 之间最小 Action Surface 是什么？
```

## Context

```text
State Slice 应如何按 Action 渲染？
```

## Evidence

```text
Paper、Evidence、Claim、Locator 之间如何建模？
```

## Loop

```text
Researcher 什么时候可以 request review？
```

## Gate

```text
Review PASS 必须验证哪些 semantic criteria 和 mechanical invariants？
```

## Wiki

```text
什么状态可以进入 Wiki？
```

## Report

```text
Report 如何只依赖 accepted evidence，而不是 conversational memory？
```

## Resume

```text
一个新的 Claude Code session 最少需要什么才能继续？
```

如果某个 Reference Study 没有帮助回答任何这些问题：

> 它现在就不是 Core Reference。

---

# 14. Study Output Format

每个核心项目后续创建一份 Study Note：

```text
.vibe/references/studies/
├── spec-kit-harness.md
├── spec-kit-loop.md
├── paper-qa.md
├── spec-kit-wiki.md
├── superloopy.md
└── old-search-harness.md
```

每份统一使用以下格式：

```markdown
# Project

## Snapshot

Repository:
Commit:
Study date:
License:

## Why We Studied It

...

## Architecture in One Diagram

...

## Core Concepts

...

## Important Files

...

## Key Data Flow

...

## Key State Model

...

## Design Decisions Worth Learning

### Decision 1

Problem:

Design:

Why:

Trade-off:

Transferability to our project:

---

## What We Should Borrow

...

## What We Should Not Borrow

...

## Conflicts with PROJECT_VISION

...

## Questions Still Open

...

## Candidate ADRs Influenced by This Project

...
```

---

# 15. Important: Do Not Produce Generic Repository Summaries

Claude Code 不应该输出：

```text
This repo has README.md...
It supports command X...
It contains folder Y...
```

这种普通代码库摘要。

每份 Study 必须围绕：

> Architecture Decision

展开。

我们真正关心的始终是：

```text
What problem?
Why this abstraction?
What trade-off?
Does it transfer?
```

---

# 16. Important: Source Study Before Code Copying

Reference 阶段禁止：

* Copy 文件到 `src/`；
* 引入第三方依赖；
* 修改产品 architecture；
* 开始实现 Research Loop；
* 复制数据模型；
* 复制 Prompt；
* 复制 CLI。

Reference Study 的唯一产物应该是：

```text
knowledge
architecture evidence
open questions
candidate design decisions
```

而不是产品代码。

---

# 17. Clone Commands

在：

```text
my-search-harness/
```

的父目录执行：

```bash
mkdir -p my-search-harness-references
cd my-search-harness-references

git clone https://github.com/formin/spec-kit-harness.git
git clone https://github.com/formin/spec-kit-loop.git
git clone https://github.com/Future-House/paper-qa.git
git clone https://github.com/formin/spec-kit-wiki.git
git clone https://github.com/beefiker/superloopy.git
git clone https://github.com/homulillew/search-harness.git old-search-harness
```

Clone 后记录：

```bash
for repo in spec-kit-harness spec-kit-loop paper-qa spec-kit-wiki superloopy old-search-harness; do
    echo "=== $repo ==="
    git -C "$repo" rev-parse HEAD
done
```

实际 Commit SHA 写入对应 Study Note。

---

# 18. Do Not Install Reference Projects Yet

第一阶段只：

```text
clone
↓
read
↓
trace architecture
↓
write study
```

不要立即：

```text
pip install
npm install
build
run
```

除非理解某个架构行为确实必须运行代码验证。

原因：

> 当前是在做 Architecture Study，不是在搭建六个开发环境。

尤其 PaperQA 和 Superloopy 都是相对完整的成熟项目。

盲目安装只会扩大环境噪声。

---

# 19. Recommended Study Order

不要六个项目同时阅读。

建议顺序：

```text
1. spec-kit-harness
       ↓
2. old-search-harness
       ↓
3. paper-qa
       ↓
4. spec-kit-loop
       ↓
5. superloopy
       ↓
6. spec-kit-wiki
```

原因：

### First — spec-kit-harness

先建立：

> Research Harness / Externalized State

心智模型。

### Second — old-search-harness

马上对照：

> 我们第一次尝试哪里做对、哪里复杂化。

### Third — PaperQA

然后研究：

> 真正科学文献检索的内部语义。

### Fourth/Fifth — Loop projects

再解决：

> Research Loop 如何被可靠约束和结束。

### Sixth — Wiki

最后研究：

> Accepted Research 如何成为跨 Run 的长期知识。

这个顺序大致对应：

```text
State
↓
Our failure history
↓
Research semantics
↓
Loop control
↓
Knowledge accumulation
```

---

# 20. Reference Study Completion Criteria

Reference 阶段不是因为：

> 六个 README 都读完了。

就完成。

它应该在我们能够清楚回答以下问题后结束：

```text
What belongs to Claude?
What belongs to Python?

What state survives a session?

What is the smallest research lifecycle?

What is a research action?

What exactly is evidence?

What causes another search iteration?

Who may request review?

Who may declare completion?

What enters the Wiki?

What remains the source of truth?
```

完成 Reference Study 后：

> 不直接 Coding。

下一阶段进入：

```text
Architecture Decisions
```

将 Reference Evidence 和 PROJECT_VISION 转化成我们自己的正式架构。

---

# 21. Core Principle

Reference Projects are:

> **Architecture evidence, not architecture authority.**

它们告诉我们：

> 别人面对类似问题时做了什么选择，以及那个选择带来了什么。

最终我们的设计仍然必须由：

```text
Our Product Goal
+
Our Constraints
+
Our Evaluation Needs
+
Reference Evidence
```

共同决定。

本阶段最重要的一条规则：

> **Study problems, not features.**
