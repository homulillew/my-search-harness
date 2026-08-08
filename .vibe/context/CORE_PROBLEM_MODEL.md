# Core Problem Model

> Status: Architecture input
> This document defines the **core problems the Harness must solve**.
>
> It is **not an Architecture Decision Record**, does not define the final module structure, and does not freeze the domain model or runtime API.

---

# 1. Purpose

本项目要构建一个面向 **Claude Code** 的 Literature Research Harness。

它的目标不是把论文调研变成一条固定 Workflow，也不是在 Python 中重新实现一套 Agent Runtime。

真正的问题是：

> **如何让 Claude Code 可以自然地进行开放式论文研究，同时让研究过程具备可靠的状态、证据、边界、审查和长期积累能力。**

从系统角度看，这可以进一步压缩为六个必须解决的核心问题：

```text
1. Research Control
2. Research State
3. Evidence
4. Context
5. Completion
6. Knowledge
```

这六个问题构成后续 Architecture Design 的问题空间。

---

# 2. Problem 1 — Research Control

## The Problem

论文调研不是固定顺序的 Pipeline。

Claude 可能根据当前研究状态决定：

```text
search
read
follow references
inspect another paper
compare results
analyze evidence
return to an earlier gap
request review
```

这种选择具有明显的语义性质。

如果 Python 试图提前编码所有研究路径：

```text
SEARCH_PHASE
↓
READ_PHASE
↓
CITATION_PHASE
↓
COMPARE_PHASE
↓
REFLECTION_PHASE
...
```

系统会逐渐变成复杂 Workflow Engine。

但如果完全依赖 Claude 自由运行，又会出现：

```text
重复搜索
忘记已有工作
绕过预算
非法状态变化
无限循环
过早宣布完成
```

因此第一个核心问题是：

> **如何保留 Claude 的语义研究自由，同时对研究过程施加最小但可靠的控制？**

---

## Required Outcome

系统需要同时满足：

```text
Claude
→ decides semantic next action

Harness
→ constrains what actions are currently legal
→ executes them reliably
→ records their effects
```

需要明确区分：

```text
Semantic Research Choice
```

和：

```text
Deterministic Control Obligation
```

例如：

Claude 可以决定：

```text
SEARCH vs READ vs ANALYZE
```

但 Harness 可以确定：

```text
budget exhausted
→ no further search allowed
→ review required
```

---

## Success Condition

一个好的 Research Control 设计应该做到：

> **研究动作可以扩展，而生命周期不会随动作数量同步膨胀。**

---

# 3. Problem 2 — Research State

## The Problem

长程论文研究产生大量跨迭代信息：

```text
Research Questions
Query History
Paper Candidates
Selected Papers
Evidence
Technical Routes
Research Gaps
Contradictions
Budget
Review State
```

如果这些信息主要存在于 Conversation 中：

```text
Claude remembers it
```

那么随着 Context 增长、压缩、Session 中断或重新启动，会出现：

```text
Context Drift
Duplicate Work
Lost Decisions
Inconsistent State
Resume Failure
```

因此：

> **Conversation 不能承担 Research Process 的长期状态。**

---

## Required Outcome

所有影响未来研究行为的重要事实，都应该存在于：

```text
Persistent Research State
```

而不是只存在于：

```text
Conversation History
```

Session 可以结束。

新的 Claude Session 应能够根据 State 理解：

```text
研究目标是什么
已经做了什么
已经知道什么
还缺什么
当前允许做什么
为什么还没有完成
```

---

## Success Condition

系统应做到：

> **Resume 恢复 Research Process，而不是恢复 Conversation。**

也就是说，即使完全丢失之前的对话，研究仍然能够继续。

---

# 4. Problem 3 — Evidence

## The Problem

论文研究最危险的错误之一是把：

```text
Paper
```

直接当成：

```text
Evidence
```

例如：

> “Paper X 和这个问题相关。”

并不能推出：

> “Paper X 支持 Claim Y。”

同样：

```text
Claude read the paper
```

也不能推出：

```text
we have proof
```

真正能够进入研究结论的内容必须具有清晰的来源链：

```text
Claim
↓
Evidence
↓
Paper
↓
Locator
↓
Source Passage
```

---

## Required Outcome

Evidence 必须同时回答两个不同问题。

### Source

```text
这条 Evidence 来自哪里？
```

例如：

```text
paper
section
locator
source passage
```

### Meaning

```text
这条 Evidence 对当前研究问题意味着什么？
```

例如：

```text
claim
research question / gap
supporting / contradicting / qualifying
researcher interpretation
```

这两层必须显式分开。

否则很容易把：

```text
Claude interpretation
```

错误地表达成：

```text
Paper reported fact
```

---

## Mechanical vs Semantic Boundary

Harness 可以机械检查：

```text
Evidence exists
Paper exists
Locator resolves
Required fields exist
Citation is valid
```

但无法仅靠确定性规则判断：

```text
这段原文真的支持 Claim 吗？
Interpretation 是否忠于原文？
这是 contradiction 还是 scope difference？
```

因此 Evidence 问题天然包含两层：

```text
Mechanical Integrity
+
Semantic Validity
```

---

## Success Condition

一个 Evidence 必须：

> **真实存在、可回源、可解释其与研究问题的关系，并且 Source 与 Interpretation 不混淆。**

---

# 5. Problem 4 — Context

## The Problem

Research State 外置以后，会产生新的问题：

> State 越来越丰富，Claude 每一轮应该看到多少？

如果每次都：

```text
load entire research state
```

那么外置状态最终只是：

```text
把 Conversation 爆炸
换成 State Dump 爆炸
```

但如果给的信息太少，Claude 又可能：

```text
重复工作
漏掉重要 contradiction
忽略已有 evidence
做出脱离整体研究目标的决定
```

所以：

> **Persistent State 与 Working Context 必须是两个不同概念。**

---

## Required Outcome

系统需要从同一份 Rich State 中，根据当前任务生成不同的：

```text
bounded context view
```

例如搜索决策可能主要需要：

```text
Research Questions
Current Gaps
Previous Queries
Relevant Routes
Budget
```

Evidence 分析可能主要需要：

```text
Current Paper
Relevant Source Passages
Existing Evidence
Related Gap
Contradictions
```

Review 则需要另一套整体视角。

---

## Core Relation

```text
Persistent State
      ↓
Context Projection
      ↓
Task-Specific View
      ↓
Claude
```

原则不是限制长期知识规模，而是限制当前工作视图：

> **Bound the view, not the knowledge.**

---

## Success Condition

Claude 应该：

> **看到当前决策所需的足够信息，但不需要重新读取整个 Research History。**

---

# 6. Problem 5 — Completion

## The Problem

开放式研究没有天然的：

```text
all tests passed
```

信号。

Claude 很容易因为：

```text
已经搜了很多
已经读了很多
最近没找到新东西
感觉覆盖差不多
```

就得出：

```text
DONE
```

但这些都不能证明研究已经充分。

同样，简单数字也不能可靠解决：

```text
sufficiency_score = 0.84
```

因为关键研究问题不能被其它维度的高分补偿。

因此 Completion 是整个 Harness 中最重要的控制问题之一。

---

## Work, Evidence and Completion Must Be Separate

至少必须保持：

```text
Work
≠
Evidence
≠
Criterion Satisfaction
≠
Completion
```

例如：

```text
read 20 papers
```

只是 Work。

获得 30 条 Evidence：

```text
Evidence exists
```

仍然不能自动说明：

```text
research question is sufficiently answered
```

---

## Researcher Cannot Self-Declare DONE

执行 Research 的角色最多应该提出：

```text
ready_for_review
```

而不是直接修改：

```text
DONE
```

最终 Completion 需要一个独立 Review Authority 判断：

```text
关键 Research Questions 是否覆盖？
Evidence 是否足够？
Critical Gap 是否存在？
Contradictions 是否被诚实处理？
是否仍存在重要 unresolved？
```

---

## Budget Is Not Completion

Budget 只回答：

```text
还能花多少资源？
```

它不回答：

```text
研究是否已经足够？
```

因此：

```text
Budget exhausted
→ stop autonomous work
→ review
```

而不是：

```text
Budget exhausted
→ DONE
```

---

## Success Condition

Completion 必须是：

> **由 Evidence-backed Criteria 和独立 Review 推导出来的状态，而不是 Researcher 的自我评价。**

---

# 7. Problem 6 — Knowledge

## The Problem

一次 Research Run 完成后，会积累大量有价值的信息：

```text
important papers
technical routes
accepted evidence
known contradictions
failed approaches
open questions
```

如果这些东西只存在于最终 Report：

> 下一次研究仍然需要大量重复发现。

所以系统需要长期知识积累。

但如果让 LLM 持续修改一套 Wiki Pages，并把这些页面直接当作新的 Truth：

```text
old summary
+
new information
→
new summary
→
future summary
```

又会产生：

```text
summary drift
citation drift
stale knowledge
second source of truth
```

因此：

> **长期知识必须可复用，但不能脱离 Evidence 独立成为事实源。**

---

## Required Outcome

Accepted Evidence 应能够产生至少两种不同用途的结果：

```text
Accepted Evidence
        │
        ├── Report
        │
        └── Long-Term Knowledge / Wiki
```

Report：

```text
serves current research run
```

Wiki：

```text
serves future research runs
```

但两者都不应该改变 Evidence Authority。

---

## Future Research Use

未来 Research Run 可以通过 Wiki 快速获得：

```text
known papers
known technical routes
known contradictions
open questions
```

用于决定：

```text
what to investigate next
```

但不能：

```text
Wiki says X
→ X automatically becomes accepted evidence
```

必须回到：

```text
Paper / Source
```

重新验证。

---

## Success Condition

长期知识系统应该做到：

> **提高未来研究效率，同时保持每个重要知识结论最终可回到 Evidence。**

---

# 8. How the Six Problems Relate

六个问题并不是六个独立功能。

它们形成一个闭环：

```text
                    Research Goal
                         │
                         ▼
                  Research Control
                         │
                  chooses / permits
                     actions
                         │
                         ▼
                  Research State
                   /     |     \
                  /      |      \
             Papers   Evidence   Gaps
                         │        │
                         │        └──────┐
                         ▼               │
                      Context            │
                         │               │
                         ▼               │
                     Claude              │
                  Semantic Research      │
                         │               │
                         └───────────────↺
                         │
                  ready_for_review
                         │
                         ▼
                    Completion
                    Review Gate
                         │
             ┌───────────┴───────────┐
             │                       │
          CONTINUE                  PASS
             │                       │
             └────→ Research         ▼
                                   Knowledge
                                /             \
                               ▼               ▼
                            Report            Wiki
                                               │
                                               ▼
                                      Future Research Prior
```

这个图表达的是：

> **Problem Structure，而不是最终 Architecture。**

它没有决定：

```text
模块名称
class 数量
文件数量
具体 phase enum
数据库
JSON schema
CLI commands
```

这些都属于后续设计。

---

# 9. What Must Remain Separate

后续 Architecture Design 中，尤其需要避免重新混淆以下概念：

```text
Conversation
≠
Research State
```

```text
State
≠
Context
```

```text
Lifecycle Phase
≠
Research Action
```

```text
Paper
≠
Evidence
```

```text
Source
≠
Interpretation
```

```text
Work
≠
Proof
```

```text
Evidence
≠
Completion
```

```text
Budget Exhaustion
≠
Semantic Completion
```

```text
Research Authority
≠
Completion Authority
```

```text
Wiki
≠
Evidence Source of Truth
```

这些分界比任何具体模块名称都更重要。

---

# 10. What This Document Deliberately Does Not Decide

本文不决定：

```text
最终 Lifecycle 有几个 Phase
具体有哪些 Actions
Research Contract Schema
Evidence Schema
Paper Status Model
Context View 数量
ReviewVerdict Schema
JSON / JSONL 文件布局
是否使用 Pydantic
CLI command surface
Provider interface
Wiki page taxonomy
Report citation format
```

也不决定：

```text
Paper / Route / Topic
```

是否最终都是一等长期知识对象。

这些必须在后续 Architecture Questions 中逐项讨论。

---

# 11. Architecture Entry Questions

从这六个 Core Problems 出发，下一阶段最需要回答的问题可以先压缩为：

```text
Q1. Who owns the loop and lifecycle?

Q2. What state must persist?

Q3. What exactly counts as Evidence?

Q4. What state should Claude see for each kind of decision?

Q5. What makes research eligible for completion?

Q6. How should accepted evidence become reusable knowledge?
```

这些问题的答案最终可能产生正式 ADR。

但在回答之前：

> **不要先创建模块去暗示答案。**

---

# 12. Core Problem Summary

整个 Harness 的问题空间最终可以压缩为：

```text
Control
→ How does research continue safely?

State
→ What must survive?

Evidence
→ What are we allowed to believe?

Context
→ What does Claude need to see now?

Completion
→ Who can say the research is enough?

Knowledge
→ What should survive into the next research run?
```

如果一个未来设计无法明确说明它解决上述哪一个问题：

> 它很可能不应该进入 V1 Core。

最终约束仍然是：

> **Keep the research loop simple, make the state rich, require hard evidence, separate research from completion authority, and let long-term knowledge remain downstream of evidence.**
