# ADR-004：持久化论文级理解与领域级理解

* **状态**：已接受
* **阶段**：Domain Model
* **日期**：2026-08-09
* **影响范围**：Persistent State、Paper、Literature Landscape、Investigation Gap、Source Grounding
* **关联决策**：

  * ADR-001 — Claude Code 驱动研究循环，Python Harness 守住系统不变量
  * ADR-002 — Research Run 使用四个最小生命周期模式
  * ADR-003 — Research Contract 定义 Research Run 的语义边界

## 背景

本项目的目标是完成论文领域调研，而不是对单篇论文做细粒度问答。

最终需要形成的是：

* 主要技术路线；
* 代表工作；
* 路线之间的重要差异；
* 当前文献形成的共识与争议；
* 领域本身仍未解决的问题；
* 一份可追溯到原始论文的调研报告和可复用知识。

因此，Persistent State 的粒度应该与系统真正进行研究判断的粒度一致。

如果把论文阅读直接建模成大量细粒度 Evidence：

```text
Paper
  ↓
Evidence E1
Evidence E2
Evidence E3
...
```

系统会逐渐把深度阅读变成结构化摘录。状态数量增加，但对领域的整体理解反而被切碎。

另一方面，如果只保存论文列表和最终报告，Claude Session 中形成的大量研究理解又会随着上下文消失，无法可靠 Resume。

本 ADR 要解决的问题是：

> **一次论文调研最少应该持久化哪些研究语义，既能支持深度阅读、跨 Session 恢复和领域综合，又不把知识模型拆得过细？**

## 决策

Research Run 持久化两个主要语义层次：

```text
Paper-level Understanding
        ↓
Field-level Understanding
```

对应：

```text
Paper Analysis
        ↓
Literature Landscape
```

同时使用 `Investigation Gap` 表示当前 Research Run 仍需调查的具体未知，并使用轻量来源引用保证重要领域判断可以回到原始论文。

核心结构为：

```text
ResearchRun
│
├── Contract
├── Lifecycle
├── Resources
│
├── Papers
│   └── Paper
│       ├── Source
│       ├── Research Status
│       └── Paper Analysis
│
├── Literature Landscape
│   ├── Approach Families
│   ├── Landscape Findings
│   └── Open Problems
│
├── Investigation Gaps
│
└── Completion Checks

Operational
└── Action / Event History
```

V1 不建立独立的 Evidence Entity。

## Paper 是研究材料，不是最终知识单元

Paper 是 Research Run 中最基本的外部研究来源。

它至少需要保存三类信息：

```text
Paper
├── Source
├── Research Status
└── Paper Analysis
```

### Source

`Source` 描述论文身份和访问来源，例如 title、authors、publication year、DOI / arXiv ID、source URL 和其它稳定 bibliographic identifiers。

它回答：

> **这是哪一篇论文？**

Paper Source 可以在不同 Research Run 之间复用。

### Research Status

`Research Status` 描述这篇论文在当前 Research Run 中是否仍值得继续投入研究成本，以及当前是否已经形成足够的论文级理解。

本 ADR 不冻结具体状态枚举。

V1 不要求建立复杂的 reading state machine，也不使用统一的 `reading_depth = 0..5` 之类分数。

一篇论文可能只需要检查 abstract，也可能只深读 Method 和 Experiments。单一数值无法准确表达这种阅读状态。

需要持久化的是：

> **Resume 所需要的研究进度，而不是完整阅读行为历史。**

具体 Search、Read、Provider 调用继续进入 Action / Event History。

### Paper Analysis

`Paper Analysis` 保存：

> **这篇论文对当前 Research Run 意味着什么。**

它不是通用论文摘要，而是 run-specific research analysis。

同一篇论文在不同 Research Run 中可能关注完全不同的内容，因此 Paper Source 可以复用，但 Paper Analysis 属于具体 Run。

Paper Analysis 可以包括核心贡献、方法或机制、与当前问题有关的重要结果、主要限制、为什么对当前研究重要，以及与当前 Literature Landscape 的关系。

本 ADR 不冻结具体字段。

关键原则是：

> **Deep Reading produces Paper Analysis, not Evidence fragments.**

深度阅读首先形成对论文的整体理解，而不是要求 Claude 每读到一个有用内容就创建一条独立 Evidence。

## Literature Landscape 是领域级理解的持久化核心

单篇 Paper Analysis 解决的是：

> **这篇论文是什么意思？**

Literature Landscape 解决的是：

> **综合当前文献，我们如何理解这个领域？**

它是 Research Run 中最重要的领域级工作模型。

V1 的 Literature Landscape 只保留三个核心组成部分：

```text
Literature Landscape
├── Approach Families
├── Landscape Findings
└── Open Problems
```

它不是最终报告，但最终 Report 和 Wiki 应主要从 Literature Landscape 投影生成。

## Approach Family

`Approach Family` 表示：

> **一组共享核心研究机制或思路的方法族。**

中文文档中可以自然称为“技术路线”。

例如：

```text
AF1  Verifier-based reranking
AF2  Verifier-guided search expansion
AF3  Verifier-guided pruning / stopping
```

Approach Family 可以保存 Run-local stable ID、名称、core idea 和 representative papers。

它不需要成为独立 Aggregate。

例如优势、缺点、趋势、路线间比较等，不应继续堆进 Approach Family 字段，而应作为 Landscape Finding 表达。

这样可以保持 taxonomy 本身简单稳定。

## Landscape Finding

`Landscape Finding` 表示：

> **当前 Research Run 对文献领域形成的一条重要领域级判断。**

例如：

```text
Search-integrated verification
通常通过增加 inference-time verifier calls
换取更强的搜索控制。
```

或者：

```text
当前文献对 process-level verification
是否稳定优于 outcome-level verification
没有一致结论。
```

或者：

```text
近年的代表工作逐渐从 post-hoc reranking
转向更深地把 verifier 集成进 search process。
```

共识、争议、趋势、路线比较、trade-off 和重要 limitation 不分别建立独立 Entity。

它们都是 Landscape Finding 的不同语义形态。

因此 V1 不建立 `Consensus`、`Disagreement`、`Trend`、`Comparison`、`Contradiction`、`RouteLimitation` 等平行对象。

### Paper Analysis 与 Landscape Finding 的边界

判断标准是：

> **这个判断的主语是谁？**

如果仍然是某一篇具体论文，它属于 Paper Analysis。

如果已经变成对 approach family、multiple papers、the literature 或 field 的判断，它属于 Literature Landscape。

可以概括为：

> **Paper Analysis 保存论文级理解；Landscape Finding 保存领域级判断。**

V1 不建立 Candidate Finding。

一个尚不成熟的高层想法，如果值得继续调查，应转化为 Investigation Gap；研究充分后再直接更新 Landscape。

## Open Problem

`Open Problem` 表示：

> **当前文献领域本身仍未解决的重要问题。**

Open Problem 是研究结果的一部分。

它不是当前 Research Run 的失败，也不应该因为仍然“未解决”而阻止 Completion Check。

如果 Contract 要求总结领域未解问题，那么识别出有充分文献依据的 Open Problem，恰恰表示该 Research Requirement 得到了满足。

## Investigation Gap

`Investigation Gap` 表示：

> **当前 Research Run 自己还没有研究清楚、且值得继续调查的问题。**

它与 Open Problem 必须严格区分：

```text
Investigation Gap
=
我们还没弄清

Open Problem
=
我们已经弄清楚领域本身还没解决
```

因此 Investigation Gap 的“解决”不表示科学问题已经获得确定答案。

它只表示：

> **这个 Gap 已经不再需要继续驱动当前 Research Loop。**

## Investigation Gap 不强制绑定所有 Research Action

Researcher 可以直接从 Research Contract 或当前 Landscape 发起探索性 Search。

Investigation Gap 只在一个未知值得跨多个 Action 持续追踪时创建。

因此：

```text
Research Action
→ may reference Research Requirement
→ may reference Investigation Gap
```

而不是：

```text
Research Action
→ must belong to Investigation Gap
```

这样可以避免把探索式研究形式化成大量虚假 Gap。

## Investigation Gap 与 Completion Check

存在 Open Investigation Gap 不等于 Completion Check 必须失败。

开放式研究始终可以提出更多问题。

Completion Check 真正判断的是：

> **当前 Literature Landscape 是否已经足以满足 Research Contract。**

某个尚未关闭的 Investigation Gap 是否足以阻止完成，由 Completion Checker 在具体 Check 中语义判断。

因此 V1 不在 Investigation Gap 上持久化 `blocking = true` 这种永久属性。

`blocking gap` 是某次 Completion Check Verdict 的 reasoning，而不是 Gap 本身的固定事实。

Completion Checker 可以在发现重要遗漏时创建或重新打开 Investigation Gap，然后让 Run 回到 `RESEARCH`。

## Source Grounding

本项目仍然坚持重要领域判断必须有文献依据，但 V1 不要求所有知识都被原子化成 Evidence Entity。

核心原则是：

> **Evidence 是知识质量约束，不一定是独立 Domain Entity。**

Literature Landscape 中的重要判断通过轻量来源引用回到 Primary Paper。

### Paper Reference

表示某篇论文是一个领域判断、技术路线或 Open Problem 的来源之一。

对于技术路线归类、代表论文和 broad literature pattern，Paper Reference 通常已经足够。

### Source Anchor

表示某个判断需要回到论文中的具体位置核查。

Locator 可以是 section、paragraph、table、figure、algorithm、theorem、appendix region 或其它足够精确的位置。

不是所有 Paper Reference 都必须拥有 Source Anchor，否则系统会重新退化成细粒度 Evidence Store。

### Grounding 粒度与判断粒度匹配

本项目采用：

> **Grounding granularity should match claim granularity.**

领域级趋势可能只需要多个 Paper Reference；具体方法机制更适合 Paper + Section / Algorithm；实验数字应明确到 Paper + Table / Figure；重要争议则需要多个 Paper 及必要的 Source Anchors。

因此不使用全系统统一的 grounding depth，也不使用 evidence confidence score。

## 来源关系保留文献分歧

对于 Landscape Finding，不应该把所有来源都理解成“支持”。

来源应能够表达至少 `supports`、`challenges`、`qualifies` 一类关系，具体 vocabulary 由后续 Schema 设计确定。

这样可以直接保存文献结构中的共识与非共识，而不需要 `Contradiction Entity` 或 `Consensus Score`。

## 不要求 Synthesis 是原文复述

领域调研中的许多重要结论本来就是跨论文 synthesis。

因此：

> **Source Grounding 支撑 synthesis，但不要求 synthesis 等价于原文摘录。**

特别对于“没有研究……”“所有工作……”“整个领域……”一类 absence / universal claim，单个 Source Anchor 无法证明。

这类判断必须结合 Research Contract Scope、已覆盖 Paper corpus 和 Search History 谨慎表述，例如优先使用：

```text
在本次覆盖的代表文献中，我们没有发现……
```

而不是把有限检索结果描述成绝对领域事实。

## Search Result 与 Paper State 分开

一次 Provider Search 可能返回大量论文。

这些 Raw Search Hits 不应该全部进入 `Papers`，否则 Persistent State 会逐渐退化成搜索缓存。

因此：

```text
Raw Search Hits
→ Action / Operational Record

Retained Research Papers
→ Papers
```

只有当 Claude 判断某篇论文值得在当前 Run 中继续保存、筛选、阅读或引用时，它才进入持久化 Papers。

这样保留 `discovery ≠ acceptance` 的语义，同时不需要 CandidatePaper / CuratedPaper / Paper 三套实体。

## Action History 与当前 Domain State 分开

Persistent Domain State 保存当前已经形成的研究理解。

Action / Event History 保存 Search、Read、Provider Failure、Paper Retained、Approach Family Merge、Gap Reopened、State Mutation 和 Resource Usage 等执行事实。

当前 Domain State 保持 canonical。

历史变化进入 append-oriented Audit History。

V1 不采用完整 Event Sourcing，也不要求从 Event Log 重建全部当前状态。

## Delivery 不产生新的实质性研究结论

Completion Check 判断的是当前 Research Contract 和 Literature Landscape 是否足以停止研究。

因此进入 `DELIVERY` 后，可以组织已有 Landscape、写报告、生成 bibliography、精化 citation locator、构建 Wiki projection，并做 mechanical citation validation。

但不能静默增加新的 substantive Landscape Finding。

如果 Delivery 中发现新的重要研究结论、关键错误或需要改变 Literature Landscape 的信息：

```text
DELIVERY
    ↓
RESEARCH
    ↓
update Paper / Landscape
    ↓
COMPLETION_CHECK
    ↓
DELIVERY
```

不建立第二套 Report Revision Workflow。

如果只是给已有判断补充更精确的 Source Anchor，而没有改变原研究解释，可以留在 Delivery。

## Partial Delivery 的授权依据

完整交付与部分交付必须区分。

正常路径：

```text
Completion Check PASS
        ↓
DELIVERY
        ↓
CLOSED
outcome = COMPLETE
```

如果 Completion Check 仍认为研究不足，但预算、来源条件或用户决策使研究不再继续，用户可以明确接受 Partial Delivery：

```text
USER_ACCEPT_PARTIAL
        ↓
DELIVERY
        ↓
CLOSED
outcome = PARTIAL
```

Budget exhaustion 本身不能伪造 Completion Check PASS。

为了支持 Resume，Delivery 必须能够知道当前交付由什么授权：valid Completion Check PASS，或 explicit Partial Delivery authorization。

本 ADR 不冻结具体数据结构。

## Minimal Persistent State

综合上述决定，V1 的最小持久化模型为：

```text
ResearchRun
│
├── Research Contract
│
├── Lifecycle Mode
│
├── Resource State
│
├── Papers
│   └── Source + Research Status + Paper Analysis
│
├── Literature Landscape
│   ├── Approach Families
│   ├── Landscape Findings
│   └── Open Problems
│
├── Investigation Gaps
│
└── Completion Checks

Operational
└── Action / Event History
```

V1 明确不建立以下核心 Entity：

```text
Evidence
Claim
CandidateFinding
Consensus
Contradiction
Trend
Comparison
DerivedQuestion
CitationMap
CandidatePaper
CuratedPaper
```

如果未来真实实现证明其中某个概念需要独立身份、生命周期、跨模块长期引用且无法从现有状态安全表达，再通过新的 ADR 引入。

## Research Loop

最终研究闭环为：

```text
Research Contract
       │
       ▼
Explore / Investigation Gap
       │
       ▼
Search / Select Papers
       │
       ▼
Read / Deep Read
       │
       ▼
Paper Analysis
       │
       ▼
Update Literature Landscape
 ├── Approach Family
 ├── Landscape Finding
 └── Open Problem
       │
       ▼
Resolve / Create Investigation Gaps
       │
       ├──────────↺
       │
       ▼
Completion Check
       │
   CONTINUE / PASS
```

它可以概括为：

> **Investigation Gap 驱动未完成研究，Paper Analysis 吸收单篇论文，Literature Landscape 保存领域理解，Completion Check 判断这种理解是否已经满足 Research Contract。**

## 验证方式

后续实现至少应通过以下场景：

1. 新搜索返回大量论文时，Raw Search Hits 不全部进入 Persistent Papers。
2. 一篇论文可以只保存 Paper Analysis，而不必生成任何 Landscape Finding。
3. 深读论文不要求创建大量细粒度 Evidence。
4. 同一篇论文在不同 Run 中可以拥有不同 Paper Analysis。
5. 新论文暂时无法分类时，不需要创建 Candidate Approach Family。
6. 多篇论文产生冲突时，可以直接形成表达 disagreement 的 Landscape Finding，而不是强制创建 Contradiction Entity。
7. Investigation Gap 可以通过“确认领域本身没有一致答案”而结束。
8. Open Problem 不会因为“尚未被领域解决”而阻止 Completion Check PASS。
9. 一个开放 Investigation Gap 不会自动成为 blocking gap。
10. Completion Checker 可以根据 Contract + Landscape 发现新的 blocking Investigation Gap。
11. Landscape Finding 至少知道自己依据哪些论文；具体判断需要时可以保存 Source Anchor。
12. 数值、具体方法机制和强争议判断可以追溯到 Section / Table / Figure 等具体位置。
13. Delivery 中发现新的 substantive insight 时回到同一个 Research Loop，而不是建立独立 Revision Workflow。
14. Completion Check PASS 与 Partial Delivery authorization 可以被明确区分。
15. Session 丢失后，新 Claude Session 可以依赖 Paper Analysis + Literature Landscape 恢复研究，而不需要恢复 Conversation。

如果未来实现需要大量 Evidence、Candidate、Observation、Hypothesis、Contradiction 或 Claim 对象才能运行，应重新检查是否把论文调研错误建模成了细粒度知识抽取系统。

## 决策摘要

本项目在产品真正进行推理的粒度上保存状态：

```text
Primary Papers
      ↓
Paper Analysis
      ↓
Literature Landscape
      ↓
Completion Check
      ↓
Report / Wiki
```

未完成研究通过 Investigation Gap 驱动。

重要领域判断通过轻量来源引用回到 Primary Paper。

V1 不建立独立 Evidence Entity。

> **深读形成论文级理解，综合形成领域级理解。**

> **重要判断必须有来源，但研究过程不需要被拆成证据碎片。**

> **系统应该在它真正做决策的粒度上保存状态。**
