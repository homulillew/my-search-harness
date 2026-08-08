# Design Goals & Principles

> Status: Architecture input
> This document is **not an ADR** and does not define the final implementation.

## 1. Product Goal

本项目构建一个面向 **Claude Code** 的论文调研 Harness。

它不是一个通用 Deep Research Agent，也不是第二套 Python Agent Runtime。

它要解决的是：

> **让开放式论文调研过程变得可恢复、可验证、可控制、可积累。**

Claude Code 仍然负责真正的研究判断：

```text
理解问题
→ 搜索
→ 筛选论文
→ 阅读
→ 分析 Evidence
→ 发现 Gap
→ 继续调查
→ 综合结论
```

Harness 的职责不是替 Claude 研究，而是为这个过程提供可靠的 Research Runtime。

---

# 2. Runtime Boundary

系统最核心的职责边界：

```text
Claude Code
=
Semantic Research Policy

Python Harness
=
Deterministic Research Mechanism
```

Claude 负责：

```text
研究问题理解
Query formulation
论文选择
阅读判断
Evidence interpretation
Gap discovery
Contradiction analysis
Synthesis
```

Python 负责：

```text
可靠执行
状态持久化
去重与 ID
Budget
Validation
Evidence integrity
State transition
Resume
Context rendering
```

原则：

> **Claude decides what the research means and what to investigate next.
> Python ensures the process is executed and recorded reliably.**

---

# 3. Simple Loop, Rich State

研究行为可以复杂，但控制流必须简单。

```text
Phase
=
Research lifecycle

Action
=
Work performed inside a phase
```

例如：

```text
search
read
follow reference
extract evidence
compare papers
```

都应该优先作为 Action，而不是新的 Lifecycle Phase。

原则：

> **Feature count must not drive phase count.**

复杂度应该优先进入 Rich State，而不是进入 Rich Control Flow。

---

# 4. State Outside Conversation

Conversation 不是可靠的长期 Research State。

需要持久化的重要信息包括：

```text
Research Questions
Queries
Papers
Evidence
Gaps
Contradictions
Budget
Review State
```

Session 可以结束，Research Process 不能因此丢失。

原则：

> **Resume restores the research process, not the conversation.**

---

# 5. Context Is a View of State

外置 State 不能再次全部塞回 Claude Context。

正确关系：

```text
Persistent State
      ↓
Context Renderer
      ↓
bounded task-specific view
      ↓
Claude Code
```

不同任务应该看到不同的信息。

原则：

> **Keep durable knowledge rich; keep working context selective.**

也就是：

> **Bound the view, not the knowledge.**

---

# 6. Paper Is Not Evidence

找到一篇论文，只意味着发现了一个潜在来源。

```text
Paper
≠
Evidence
```

真正能够支撑研究结论的对象必须进一步绑定：

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

原则：

> **A paper is a source of evidence, not evidence itself.**

---

# 7. Evidence Separates Source From Interpretation

Evidence 至少包含两个不同层次：

```text
Source
+
Research Interpretation
```

Source 回答：

> 原论文在哪里、说了什么？

Interpretation 回答：

> 这段内容对当前 Research Question 意味着什么？

两者不能混淆。

原则：

> **Researcher interpretation must never be presented as source-reported fact.**

---

# 8. Hard Evidence, Semantic Judgment

Python 可以机械验证：

```text
Evidence exists
Paper resolves
Locator exists
Citation resolves
Schema is valid
```

但 Python 不应该假装能够机械决定：

```text
这段 Evidence 是否真的支持 Claim
这个 interpretation 是否公平
这个 contradiction 是否成立
```

原则：

```text
Python
→ integrity

Claude
→ meaning
```

因此：

> **Hard Evidence means semantic judgment is anchored to real, traceable evidence—not that Python decides truth.**

---

# 9. Gap-Driven Research

Research Loop 不应因为“还能继续搜”而继续。

新的研究动作应尽量由明确的未解决问题驱动：

```text
Evidence
↓
Current Understanding
↓
Research Gap
↓
Next Investigation
```

Claude 决定如何把 Gap 转化成搜索或阅读策略。

Python 负责记录：

```text
why this action exists
which gap it serves
whether it duplicates prior work
whether budget remains
```

原则：

> **Research should continue because a gap exists, not because the loop has momentum.**

---

# 10. Work Is Not Proof

这些都是 Research Work：

```text
searched
read
compared
analyzed
```

它们不能直接证明任务已经完成。

```text
Work
≠
Evidence
≠
Completion
```

原则：

> **Reading is work. Evidence is proof candidate. Completion requires more than evidence existence.**

---

# 11. Researcher Is Not the Final Judge

Researcher 可以判断：

```text
ready_for_review
```

但不能直接宣布：

```text
DONE
```

完成必须经过独立的 Review Authority。

```text
RESEARCH
    ↓
ready_for_review
    ↓
REVIEW
    ↓
PASS / CONTINUE / UNCERTAIN / PARTIAL
```

Python 可以约束谁有权写 Review / Completion State。

Reviewer 的 fresh context 则由 Claude Code 执行协议保证。

原则：

> **Research authority and completion authority are separate.**

---

# 12. Criteria Over Magic Scores

语义质量不能被压成：

```text
sufficiency_score = 0.84
```

关键条件不应该互相补偿。

例如：

```text
two questions well-covered
+
one critical question missing
```

仍然不能自动 PASS。

因此：

```text
Numbers
→ limit resources

Typed Criteria
→ judge semantic completion
```

原则：

> **Use numbers to bound cost, not to manufacture certainty.**

---

# 13. Budget Bounds Autonomy

Budget 回答：

> 还允许系统花多少资源？

Evidence / Review 回答：

> 研究是否已经足够？

二者不能混为一谈。

```text
Budget exhausted
      ↓
stop autonomous work
      ↓
Review
```

而不是：

```text
Budget exhausted
      ↓
DONE
```

原则：

> **Budget stops autonomy; it does not prove completion.**

---

# 14. Contradictions Are Research Results

论文之间的：

```text
support
contradiction
qualification
scope difference
evidence gap
```

都可能是真实研究结果。

系统不应该为了生成一个顺滑 Report 而静默抹平它们。

原则：

> **Contradictions must survive into state and synthesis until explicitly resolved.**

---

# 15. Evidence First, Synthesis Second

最终结论不应该先写出来，再倒找 Citation。

正确方向：

```text
Research
↓
Accepted Evidence
↓
Analysis
↓
Synthesis
```

原则：

> **Claims should emerge from evidence, not citations from claims.**

---

# 16. Report and Wiki Are Derived Views

Accepted Evidence 是长期可信研究状态的核心。

Report 和 Wiki 都应建立在它之上：

```text
             Accepted Evidence
                    │
           ┌────────┴────────┐
           ▼                 ▼
         Report             Wiki
```

Report 是本次 Research Run 的交付。

Wiki 是未来 Research Run 的长期 Prior。

它们都不应该成为新的独立事实源。

原则：

> **Evidence is authoritative research state; Report and Wiki are projections.**

---

# 17. Wiki Is Memory, Not Proof

未来 Research Run 可以利用 Wiki 快速知道：

```text
known papers
known routes
known contradictions
open questions
```

但：

```text
Wiki says X
```

不能直接升级成新的 Accepted Claim。

仍然需要回到 Paper / Evidence 验证。

原则：

> **Wiki helps decide what to investigate; papers decide what may be claimed.**

---

# 18. Complexity Must Earn Its Place

每增加一个：

```text
Phase
Module
Agent
Database
Graph
Score
Artifact
Dependency
```

都必须回答：

```text
What real problem does it solve?

What breaks without it?

Can the problem be solved more simply?
```

当前默认不引入：

```text
second Python agent runtime
generic multi-agent framework
graph database
vector database
scalar sufficiency score
self-modifying meta-loop
complex citation graph
```

除非真实运行结果证明这些复杂度值得存在。

原则：

> **Prefer the smallest mechanism that preserves the required invariant.**

---

# 19. Design Summary

整个 Harness 可以压缩成：

```text
Simple Loop
Rich State
Hard Evidence
Independent Review
Derived Knowledge
```

以及最核心的两个职责边界：

```text
Claude owns semantic research.
Python owns deterministic reliability.
```

最终目标不是让 Claude “搜得更多”。

而是：

> **让 Claude Code 能自然地进行论文研究，同时让研究过程可以被工程系统可靠地保存、检查、恢复和约束。**
