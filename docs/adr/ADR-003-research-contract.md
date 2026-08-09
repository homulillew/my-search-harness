# ADR-003：Research Contract 定义 Research Run 的语义边界

* **状态**：已接受
* **阶段**：Architecture Design
* **日期**：2026-08-09
* **影响范围**：Research Contract、Completion Check、Research Run、Scope Management
* **关联决策**：

  * ADR-001 — Claude Code 驱动研究循环，Python Harness 守住系统不变量
  * ADR-002 — Research Run 使用四个最小生命周期模式

# ADR-003 修改说明

## 1. 在关联决策之后、`## 背景` 之前插入

## V1 术语收敛说明

本 ADR 确立的 Research Contract 边界仍然有效：Contract 定义稳定的 Completion Boundary，研究路径与研究理解可以持续演化。

本文写于 ADR-004 的 Research State 对象模型正式收敛之前，因此部分早期领域术语需要按后续决策解释：

* `Evidence` 不表示独立持久化实体。V1 的研究判断通过 `Paper Analysis`、Literature Landscape 与 `LiteratureSource` 保持 grounding。
* `Technical Route` 后续正式收敛为 `Approach Family`。
* `Derived Question` 不建立独立 Domain Entity。当前 Run 尚需调查的问题按需要进入 `Investigation Gap`；领域本身尚未解决的问题进入 `Open Problem`。
* `Contradiction` 不建立独立 Domain Entity，而作为 Literature Landscape 中需要保留的研究冲突或分歧表达。
* 本 ADR 中一般性的 `Gap` 在 V1 Domain Model 中主要对应 `Investigation Gap`。

V1 Research State 的持久化结构以 ADR-004 为准。本 ADR 继续负责定义 Contract 与 Evolving Research State 之间的边界。

## 2. 修改背景第一段

将：

Research Run 可以持续多轮 Search、Read、Deep Read、Evidence Analysis 和 Gap-driven Research。

替换为：

Research Run 可以持续多轮 Search、Read、Deep Read、Paper Analysis、Landscape Synthesis 和 Gap-driven Research。

## 3. 修改「决策」中会持续演化的对象

将：

Search Query、Paper Selection、Research Gap、Technical Route、Derived Question 等内容都允许随着研究过程持续演化。

替换为：

Search Query、Paper Selection、Paper Analysis、Investigation Gap、Approach Family、Landscape Finding 与 Open Problem 等研究内容都允许随着研究过程持续演化。

## 4. 修改 Research Requirements 中关于细分问题的说明

将：

研究过程中产生的更细问题属于 Derived Questions 或 Gap，不需要进入 Contract。

替换为：

研究过程中产生的更细问题不需要进入 Contract。当前 Run 尚未调查充分的问题可以形成 `Investigation Gap`；如果研究结果表明问题属于领域本身尚未解决的事项，则记录为 `Open Problem`。V1 不建立独立 `DerivedQuestion` Entity。

## 5. 修改 Provider 一节中的术语

将：

这属于 Source / Evidence Scope，因为它改变了研究完成条件。

替换为：

这属于 Source Scope，因为它改变了研究完成条件。

## 6. 替换「Query、Paper、Gap、Technical Route、Derived Question」这一小节

将标题替换为：

### Query、Paper 与 Evolving Research State

正文替换为：

Search Query、Paper Selection、Paper Analysis、Investigation Gap、Approach Family、Landscape Finding 与 Open Problem 都属于研究过程中可以持续演化的 Research State。

它们可以随着新的论文、来源核验与领域理解被创建、修正、重组或关闭，但不能因为研究内容发生变化就自动修改 Research Contract。

只有当某项变化真正改变 Completion Check 的 PASS 条件时，才需要 Contract Amendment。

## 7. 替换「Stable Contract，Evolving Research State」结构图

将旧的：

Evolving Research State

* Papers
* Evidence
* Gaps
* Contradictions
* Derived Questions
* Technical Routes

替换为：

Evolving Research State

* Papers

  * Paper Analysis
* Literature Landscape

  * Approach Families
  * Landscape Findings
  * Open Problems
* Investigation Gaps
* Completion Checks

然后将图后的这一句：

这允许 Researcher 在不修改 Contract 的情况下自由改写 Query、发现 Paper、建立 Gap、推翻原路线假设、发现新的 Technical Route、产生更细的 Derived Question，并更新 Evidence Interpretation。

替换为：

这允许 Researcher 在不修改 Contract 的情况下自由调整 Query、发现和保留 Paper、更新 Paper Analysis、创建或关闭 Investigation Gap、重组 Approach Family、修正 Landscape Finding，并识别新的 Open Problem。

这些变化属于正常研究状态演化，而不是 Contract Amendment。

## 8. 修改 Completion Check 与 Deliverable 的对应关系

将：

Deliverable
↓
当前 Evidence 是否足以生成用户要求的最终成果？

替换为：

Deliverable
↓
当前 Research State 及其 grounding 是否足以生成用户要求的最终成果？

## 9. 修改 Contract Amendment 的反例

将：

例如新增 Derived Question、发现新的 Technical Route、创建新的 Gap、修改 Search Query、增加 Paper 或 Evidence，都不需要修改 Contract。

替换为：

例如创建新的 Investigation Gap、发现新的 Approach Family、修改 Search Query、增加 Paper、更新 Paper Analysis 或修正 Landscape Finding，都不需要修改 Contract。

## 10. 替换「Research Requirement 与 Gap 的关系」中的研究循环

原来的语义链：

Research Requirement
→ Gap
→ Research Action
→ Evidence
→ Gap updated
→ Completion Check

替换为：

Research Requirement
→ Investigation Gap
→ Research Action
→ Paper Analysis / Landscape Update
→ Investigation Gap updated
→ Completion Check

并将这一节中的：

Gap 表达当前为什么还没有完成。

替换为：

`Investigation Gap` 表达当前为什么还没有完成，或者当前 Run 还有什么需要进一步调查。

将：

Gap 不会自动升级成新的 Research Requirement。

替换为：

Investigation Gap 不会自动升级成新的 Research Requirement。

## 11. 替换「Research Run 中的位置」结构图

将旧的 `Research Facts`：

* Papers
* Evidence
* Gaps
* Contradictions
* Derived Questions

替换为：

* Papers / Paper Analysis
* Literature Landscape
* Investigation Gaps
* Completion Checks

这一节整体应表达：

Research Contract

* Mission
* Requirements
* Scope
* Deliverable

Lifecycle Mode

* RESEARCH
* COMPLETION_CHECK
* DELIVERY
* CLOSED

Resource Facts

* Budget
* Provider
* Cost
* Limits

Research State

* Papers / Paper Analysis
* Literature Landscape
* Investigation Gaps
* Completion Checks

其中 Research Contract 定义 Completion Boundary，但不承担资源控制、研究路径或领域知识本身。

## 12. 修改「为什么不使用详细 Research Plan」

将：

Candidate Routes、Paper Targets、Reading Order、Expected Evidence 和 Stop Strategy

替换为：

Candidate Approaches、Paper Targets、Reading Order、Expected Findings 和 Stop Strategy

将：

Researcher 会倾向验证最初 Plan，而不是根据 Evidence 调整方向。

替换为：

Researcher 会倾向验证最初 Plan，而不是根据新的论文、来源核验和研究理解调整方向。

## 13. 修改「为什么不让 Researcher 动态决定完成目标」

将：

Researcher 还可能因为当前 Evidence 不足而逐渐降低自己的完成标准。

替换为：

Researcher 还可能因为当前 Research State 尚未充分覆盖要求，而逐渐降低自己的完成标准。

## 14. 修改验证场景 2 和 3

将：

2. 新发现一条 Technical Route 不需要修改 Contract。
3. 新增一个 Derived Question 不需要修改 Contract。

替换为：

2. 新发现或重组一个 `Approach Family` 不需要修改 Contract。
3. 新增一个 `Investigation Gap` 或识别一个 `Open Problem` 不需要修改 Contract。

## 15. Reference Evidence 中的通用术语保留

参考项目名称和设计概念中的：

* Evidence Gathering
* Goal / Criteria / Evidence / Gate

可以保留。

这些是外部 Reference 的概念，不属于本项目 V1 Research State Schema。


## 背景

Research Run 可以持续多轮 Search、Read、Deep Read、Evidence Analysis 和 Gap-driven Research。

开放式研究的一个核心风险是目标逐渐漂移。

例如，用户最初要求调研：

```text id="2uipec"
近三年 verifier-guided agent search
的主要技术路线、代表论文、关键差异和开放问题
```

随着研究深入，Claude 可能不断发现新的相关方向：

```text id="vrtohm"
agent planning
tree search
process reward model
self-reflection
reasoning model
reinforcement learning
```

这些方向可能都有研究价值，但如果系统没有一个稳定的语义边界，就会越来越难回答两个基本问题：

```text id="qsnmem"
这次 Research Run 到底承诺研究什么？

什么时候可以合理停止 Research？
```

Completion Check 同样需要一个稳定的判断基准。否则 Checker 只能凭“看起来研究得比较全面”做主观判断，无法明确指出哪些要求已经满足、哪些仍然存在阻塞性缺口。

因此 Research Run 需要一个稳定的 Research Contract。

## 决策

每个正式 Research Run 必须绑定一个 Research Contract。

Research Contract 定义：

> **这次 Research Run 为什么存在、必须研究清楚什么、研究边界在哪里，以及最终要交付什么。**

它是 Research Run 的语义边界，也是 Completion Check 的主要判断基准。

Research Contract 使用四个核心部分：

```text id="qp1veq"
Research Contract
├── Mission
├── Research Requirements
├── Scope
└── Deliverable
```

它不规定研究路径。

Search Query、Paper Selection、Research Gap、Technical Route、Derived Question 等内容都允许随着研究过程持续演化。

## Mission

`Mission` 用一句简洁的话说明本次研究最终想理解什么。

例如：

```text id="u343iy"
理解近三年 verifier-guided agent search
的主要技术路线、代表工作、核心差异与开放问题。
```

Mission 的作用是保持整个 Research Run 与用户原始目标一致。

它不是背景介绍，也不是研究计划。

不应该在 Mission 中提前写入预期技术路线、候选论文、搜索策略、预设研究结论或具体执行步骤。这些内容属于后续 Research State，而不是 Contract。

## Research Requirements

`Research Requirements` 表达：

> **这次 Research Run 必须研究清楚哪些内容。**

例如：

```text id="2t4eik"
R1. 识别主要技术路线。

R2. 为主要路线给出代表论文与核心机制。

R3. 比较不同路线的重要差异。

R4. 总结主要限制与尚未解决的问题。
```

Research Requirements 是 Completion Check 最直接的判断对象。

Checker 不需要计算一个综合 sufficiency score，而是检查：

```text id="o71qf2"
R1 是否已经得到充分支持？
R2 是否已经得到充分支持？
R3 是否仍存在 blocking gap？
R4 是否存在明显遗漏？
```

如果某个必要 Requirement 仍然存在足以阻止交付的缺口，Completion Check 应返回 `CONTINUE`，并给出具体 blocking gap。

### 为什么使用 Research Requirements

本项目不在 Contract 中同时维护：

```text id="q01j8o"
Research Questions
Completion Criteria
Requirements
Objectives
```

多套语义高度重叠的对象。

对 V1 来说，Research Requirements 已经足以同时表达：

* 用户要求必须回答的问题；
* Completion Check 需要检查的内容；
* Gap 可以关联的上层研究要求。

研究过程中产生的更细问题属于 Derived Questions 或 Gap，不需要进入 Contract。

这样可以避免出现：

```text id="gt6azc"
RQ1
→ Criterion C3
→ Requirement R2
→ Gap G7
```

这类不必要的映射链。

## Scope

`Scope` 定义本次研究的边界。

它回答：

> **哪些内容属于这次 Research Run，哪些内容不属于。**

例如：

```text id="21v6ew"
Time:
2023–2026

Focus:
LLM / agent search systems

Sources:
以学术论文为核心来源

Exclude:
与 agentic search / planning 无直接关系的通用搜索排序研究
```

Scope 用来约束研究范围，而不是提前定义研究结论。

因此：

> **Scope defines boundaries, not taxonomy.**

除非用户明确要求，否则不应在 Contract 阶段预先指定只研究某些具体技术路线，因为“主要技术路线有哪些”本身可能正是研究需要回答的问题。

## Deliverable

`Deliverable` 描述最终要交付什么研究成果。

例如：

```text id="m8t9q4"
一份带可追溯引用的领域调研报告，
包含主要技术路线、代表论文、路线比较、
主要限制和 unresolved problems。
```

Deliverable 会影响 Completion Check。

例如，如果用户明确要求必须包含路线比较，那么只有论文列表，即使论文数量很多，也不能视为完成。

Deliverable 只描述语义交付要求，不负责保存 `output_path`、文件名、Markdown 标题风格、临时 workspace 路径等运行时细节。这些属于 Delivery Runtime 或配置。

## Research Contract 不包含什么

Research Contract 不应该逐渐变成整个 Research Run 的容器。

### Budget

Budget 属于 Resource State。

```text id="v5hqn9"
budget = 100
```

改成：

```text id="cfabws"
budget = 200
```

改变的是 Harness 允许继续消耗多少资源，而不是“什么算研究完成”。

因此：

```text id="07kbdc"
Research Contract ≠ Resource Budget
```

Budget exhaustion 也不能修改 Completion 条件，更不能自动意味着 Run 完成。

### Provider

使用哪个搜索或论文 Provider 属于 Runtime Configuration / Resource Boundary。

例如 Semantic Scholar、OpenAlex、arXiv、DeepXiv 都不属于 Research Contract。

但如果用户要求：

```text id="ud8pfr"
最终核心结论只能使用同行评审论文
```

这属于 Source / Evidence Scope，因为它改变了研究完成条件。

### Query、Paper、Gap、Technical Route、Derived Question

这些都是研究过程中持续变化的 Research State。

它们必须允许随着 Evidence 和研究理解自由演化，不能因为被发现就自动改变 Contract。

## Stable Contract，Evolving Research State

Research Run 应保持两层明确分离：

```text id="0gnx4r"
Research Contract
        │
        │ stable semantic boundary
        ▼
Evolving Research State
├── Papers
├── Evidence
├── Gaps
├── Contradictions
├── Derived Questions
└── Technical Routes
```

可以概括为：

> **Contract 稳定“必须研究清楚什么”，Research State 演化“我们现在如何理解这个问题”。**

这允许 Researcher 在不修改 Contract 的情况下自由改写 Query、发现 Paper、建立 Gap、推翻原路线假设、发现新的 Technical Route、产生更细的 Derived Question，并更新 Evidence Interpretation。

这些变化属于正常研究，而不是 Contract Amendment。

## Completion Check 与 Contract

Completion Check 不应该自行发明一套独立的综合评分标准。

它主要依据 Research Contract 判断当前 Research State 是否足以进入 Delivery。

对应关系如下：

```text id="6ee5a4"
Mission
    ↓
当前研究是否仍然回答用户最初的核心目标？

Research Requirements
    ↓
每项必要研究要求是否得到充分支持？

Scope
    ↓
结论是否遗漏必要范围，或明显越过研究边界？

Deliverable
    ↓
当前 Evidence 是否足以生成用户要求的最终成果？
```

因此：

```text id="h6q5vg"
Research Contract
        ↓
defines completion boundary
        ↓
Completion Check
```

这也是项目不使用 magic sufficiency score 的重要基础。

## Contract 默认稳定，但允许显式修订

Research Contract 不应该绝对不可修改。

真实研究过程中，用户可能改变需求，Researcher 也可能发现原始 Contract 存在重要问题。

因此：

```text id="zahabd"
Contract
=
stable by default
+
explicit amendment
```

不允许 silent mutation。

### 什么情况属于 Contract Amendment

判断标准只有一个：

> **这次变化是否改变 Completion Check 的 PASS 条件？**

如果答案是否定的，它属于正常 Research State 演化。

例如新增 Derived Question、发现新的 Technical Route、创建新的 Gap、修改 Search Query、增加 Paper 或 Evidence，都不需要修改 Contract。

如果答案是肯定的，就必须显式修改 Contract。

例如：

```text id="bmcxdf"
增加或删除 Research Requirement
扩大或缩小 Scope
改变 Deliverable
改变会影响完成条件的 Source Requirement
```

这些都属于 Contract Amendment。

## Contract Amendment 的基本要求

本 ADR 不决定最终 Amendment 数据结构，但要求任何影响 Completion 条件的修改都必须可追溯。

至少需要能够知道：

```text id="gt3mjl"
what changed
why it changed
when it changed
```

Researcher 可以提出 Contract Amendment，但不能为了让 Completion Check 更容易 PASS 而静默删除未完成的 Research Requirement。

用户明确提出的范围或交付变化可以形成 Contract Amendment。

不同类型 Amendment 是否需要用户再次确认，由后续具体接口设计决定。

## Contract Amendment 与已有 Completion Check

Completion Check 的结论只对它检查时的 Contract 和 Research State 有效。

如果已经获得：

```text id="zgtyqx"
PASS
```

之后 Contract 发生改变 Completion 条件的 Amendment，那么之前的 Completion Approval 自动失效。

流程回到：

```text id="dm7r8r"
Contract Amendment
        ↓
previous completion approval invalidated
        ↓
RESEARCH
```

之后必须基于新的 Contract 再次完成研究和 Completion Check。

这保证最终 Delivery 与当前有效 Research Contract 一致。

## Research Requirement 与 Gap 的关系

Research Requirement 表达必须完成什么。

Gap 表达当前为什么还没有完成。

例如：

```text id="9wvf7o"
R3:
比较不同技术路线的重要差异

        ↓

G7:
目前缺少 inference-time verifier
与 training-time verifier 的系统比较
```

因此研究循环可以自然表示为：

```text id="iqmn0w"
Research Requirement
        ↓
Gap
        ↓
Research Action
        ↓
Evidence
        ↓
Gap updated
        ↓
Completion Check
```

Gap 不会自动升级成新的 Research Requirement。

只有当它真正改变了用户期望的 Completion Boundary 时，才需要 Contract Amendment。

## Research Run 中的位置

Research Contract 与 Lifecycle、Research Facts、Resource Facts 保持正交：

```text id="xzr3ah"
                         Research Run
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
 Research Contract       Lifecycle Mode        Resource Facts
        │                     │                     │
 Mission                RESEARCH                Budget
 Requirements           COMPLETION_CHECK        Provider
 Scope                  DELIVERY                Cost
 Deliverable            CLOSED                  Limits
        │
        │ defines
        ▼
 Research Facts
 ├── Papers
 ├── Evidence
 ├── Gaps
 ├── Contradictions
 └── Derived Questions
```

Research Contract 不承担资源控制。

Lifecycle 不承担研究内容。

Research Facts 不应该偷偷改变 Completion Boundary。

## 为什么不使用详细 Research Plan 作为 Contract

另一种方案是在 Run 创建时保存完整 Research Plan，包括 Research Questions、Queries、Candidate Routes、Paper Targets、Reading Order、Expected Evidence 和 Stop Strategy。

这种方案的问题是：

1. 开放式研究的重要信息往往只有研究开始后才能发现；
2. Plan 很快会过期；
3. Harness 需要不断同步 Plan 与实际 Research State；
4. Python 容易逐渐承担语义流程编排；
5. Researcher 会倾向验证最初 Plan，而不是根据 Evidence 调整方向。

因此本项目不把 Research Contract 设计成执行计划。

Contract 固定完成边界，Researcher 保留研究路径自由。

## 为什么不让 Researcher 动态决定完成目标

另一种极简方案是只保存 Mission，让 Claude 在研究过程中自己理解“什么时候算够”。

这种方案无法为 Completion Check 提供稳定判断依据。

Researcher 还可能因为当前 Evidence 不足而逐渐降低自己的完成标准。

显式 Research Requirements 和 Scope 可以防止这种目标漂移。

## 参考证据

本决策与 Tier-1 Reference 的主要经验一致：

* `spec-kit-harness`：Mission、state 和 completion condition 应外置，而不是依赖 Conversation；
* `old-search-harness`：复杂 Plan / Phase / sufficiency 逻辑容易演变为大型 Orchestrator；
* `PaperQA`：研究中的 Query 和 Evidence Gathering 应由 agent 根据当前问题动态决定；
* `spec-kit-loop`：Completion 必须依据预先存在、可检查的 criteria，而不是 maker 自己修改完成标准；
* `Superloopy`：Goal / Criteria / Evidence / Gate 可以形成小而明确的 completion model；
* `spec-kit-wiki`：长期知识与单次 Run 的目标、过程状态应保持分层。

这些 Reference 支持的是稳定完成边界与动态研究过程的分离，而不是某一个具体 Contract Schema。

## 验证方式

后续实现至少应通过以下场景：

1. 用户研究目标可以被清楚表达为 Mission + Research Requirements + Scope + Deliverable。
2. 新发现一条 Technical Route 不需要修改 Contract。
3. 新增一个 Derived Question 不需要修改 Contract。
4. Researcher 修改 Search Query 不需要修改 Contract。
5. Budget 增加或耗尽不修改 Contract。
6. 用户把时间范围从三年扩大到五年时，必须产生显式 Contract Amendment。
7. 用户增加新的最终报告要求时，必须产生显式 Contract Amendment。
8. Researcher 不能为了通过 Completion Check 静默删除未完成的 Research Requirement。
9. Contract Amendment 改变 Completion 条件后，旧 Completion Check PASS 自动失效。
10. Completion Checker 可以直接依据 Research Requirements 和当前 Evidence / Gap 判断 PASS 或 CONTINUE，而不依赖 scalar sufficiency score。

如果未来 Contract 开始包含 Query、Paper、Gap、Route、Budget、Provider 或大量执行步骤，应重新检查是否把 Evolving Research State 或 Runtime Configuration 错误塞进了语义契约。

## 决策摘要

Research Contract 定义 Research Run 的稳定语义边界：

```text id="s9j7fr"
Research Contract
=
Mission
+
Research Requirements
+
Scope
+
Deliverable
```

它规定必须研究清楚什么，但不规定研究如何进行。

Research State 可以自由演化；只有会改变 Completion Check PASS 条件的变化，才需要显式 Contract Amendment。

> **Contract defines what must be satisfied, not how research should proceed.**

> **稳定完成边界，开放研究路径。**
