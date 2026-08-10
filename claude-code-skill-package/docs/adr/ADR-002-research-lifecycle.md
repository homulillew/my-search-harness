# ADR-002：Research Run 使用四个最小生命周期模式

* **状态**：已接受
* **阶段**：Architecture Design
* **日期**：2026-08-09
* **影响范围**：Research Run、Lifecycle、Completion Gate、Delivery
* **关联决策**：ADR-001 — Claude Code 驱动研究循环，Python Harness 守住系统不变量

## V1 术语与后续决策收敛说明

本 ADR 确立的四态 Lifecycle 与控制边界仍然有效。本文写作时 Research State 的部分领域概念尚未完成最终收敛，后续 ADR-004 对其进行了明确。

本文中的相关早期表达按以下方式理解：

* `Evidence` 不表示独立持久化实体。Completion Check 检查的是 Research State 中领域判断的 grounding、来源可核验性与证据边界。
* `Contradiction` 不建立独立 Domain Entity，而作为 Literature Landscape 中需要保留的重要冲突或分歧处理。
* `Gap` 在正式 Domain Model 中主要对应 `Investigation Gap`；领域本身尚未解决的问题由 `Open Problem` 表达。
* Research State 的 V1 实体结构以 ADR-004 为准。
* ADR-010 后续明确 Local Wiki Build 属于 Research Run 结束后的 repository-level cross-run projection，不属于 `DELIVERY` Action。`CLOSED` 仍然是 ResearchRun Lifecycle 的终点。

参考项目描述中的 `Evidence Gathering`、`Evidence-Gated Completion` 等词保留原文。它们是对参考项目的描述，其中的 Evidence 是通用概念，不代表本项目重新引入 Evidence Entity。

## 背景

ADR-001 已经确定：

```text
Claude owns agency.
Python owns invariants.
State carries continuity.
```

因此，Research Run 的 Lifecycle 不应该描述 Claude 正在执行哪一种研究工作，而应该只表达真正影响控制权、动作合法性和系统不变量的状态变化。

论文研究过程中会发生很多动作：

```text
Search
Read
Deep Read
Follow Citation
Compare
Analyze Paper / Synthesize Landscape
Update Gap
Synthesize
Write Report
```

这些动作数量可能随着能力增长不断增加。如果每种动作都升级成 Lifecycle Phase，Python Harness 会逐渐承担研究流程编排，最终重新形成复杂状态机和大型 Orchestrator。

本 ADR 要解决的问题是：

> 一个 Research Run 最少需要哪些 Lifecycle Mode，才能清楚表达研究、完成性检查、交付和终止，同时不把工作步骤塞进状态机？

## 决策

Research Run 使用四个 Lifecycle Mode：

```text
RESEARCH
COMPLETION_CHECK
DELIVERY
CLOSED
```

它们只表达控制状态，不表达具体研究步骤。

完整主路径如下：

```text
             create_run(valid contract)
                       │
                       ▼
               ┌──────────────┐
               │   RESEARCH   │◄───────────────┐
               └──────┬───────┘                │
                      │                        │
        REQUEST_COMPLETION_CHECK              │
                      │                        │
                      ▼                        │
            ┌────────────────────┐             │
            │ COMPLETION_CHECK   │             │
            └─────────┬──────────┘             │
                      │                        │
             ┌────────┼────────┐               │
             │        │        │               │
         CONTINUE  UNCERTAIN  PASS             │
             │        │        │               │
             └────────┘        │               │
                  │            │               │
                  └────────────┼────→ RESEARCH │
                               │               │
                               ▼               │
                      ┌────────────────┐         │
                      │    DELIVERY    │         │
                      └───────┬────────┘         │
                              │                  │
                    critical gap found ──────────┘
                              │
                     delivery complete
                              │
                              ▼
                       ┌─────────────┐
                       │   CLOSED    │
                       │             │
                       │ outcome:    │
                       │ COMPLETE    │
                       │ PARTIAL     │
                       └─────────────┘
```

## Lifecycle 只描述控制权变化

Lifecycle Mode 的判断标准是：

> 只有当一个状态改变了“谁可以做什么、哪些动作是否合法、系统必须守住什么 invariant”时，它才值得成为 Lifecycle Mode。

因此：

```text
Lifecycle Phase ≠ Research Action
```

例如 `SEARCH`、`READ`、`DEEP_READ`、`ANALYZE_PAPER`、`SYNTHESIZE_LANDSCAPE` 都属于 `RESEARCH` 中的工作动作，不会因为能力增加而产生新的 Lifecycle Mode。

同样，`WRITE_REPORT`、Citation Verification 等交付工作属于 `DELIVERY` 中的 Action，也不分别成为 Phase。Local Wiki Build 按 ADR-010 在 Research Run `CLOSED` 后独立执行，不属于 ResearchRun Lifecycle。

## RESEARCH

`RESEARCH` 是 Researcher 拥有研究主动权的状态。

Claude Code 可以根据当前 Research State 决定下一步语义动作，例如：

* Search；
* Read / Deep Read；
* Follow Citation；
* Compare；
* 形成或修正 `Paper Analysis`；
* 综合或修正 Literature Landscape；
* 更新 `Investigation Gap`；
* 识别重要研究冲突与 `Open Problem`；
* 调整研究方向；
* 请求 Completion Check。

Python Harness 负责验证动作合法性、执行工具调用、记录预算和持久化事实，但不决定下一步最值得研究什么。

Researcher 不能直接宣布 Run 完成。

当它认为当前研究可能已经足够时，只能请求：

```text
REQUEST_COMPLETION_CHECK
```

## COMPLETION_CHECK

`COMPLETION_CHECK` 是一个短暂的完成性检查状态。

这里不再使用 `REVIEW` 作为正式名称，因为在论文系统中容易被误解成 Paper Review、Deep Reading 或 Citation Review。

`COMPLETION_CHECK` 的唯一目的，是回答：

> 基于当前 Research Contract 和已有证据状态，现在是否有充分理由停止研究并进入 Delivery？

它是一个 Completion Gate，不是第二套 Research Workflow。

### 为什么它是 Lifecycle Mode

进入 Completion Check 后，系统发生了真实的控制权变化：

* Researcher 暂时失去修改研究基础的权限；
* 当前 Research State 作为检查基线保持稳定；
* Completion Checker 获得完成性判断权限；
* Search、修改 Paper Analysis、修改 Literature Landscape、Update Investigation Gap 等会改变研究基础的普通 Research Mutation 暂时不可执行。

因此它不是普通 Action，而是一个真正的控制状态。

### Completion Checker 的实现

Completion Check 默认由一个 **fresh Claude subagent / fresh context** 执行。

Subagent 是 Completion Check 的执行方式，不是新的长期 Agent Runtime。

它：

* 生命周期短；
* 不拥有独立 Research State；
* 不维护自己的长期 Memory；
* 不拥有自己的 Research Loop；
* 完成一次检查后即结束。

它读取由 Harness 生成的 bounded Completion Check View，而不是继承 Researcher 的完整 Conversation History。

典型输入包括：

```text
Research Contract
Research Requirements / Deliverable
Current Literature Landscape
Relevant Paper Analysis summaries
Grounding source refs
Investigation Gaps
Open Problems
Researcher completion rationale
```

其中 Researcher 的 completion rationale 只是待检查的主张，不作为完成事实。

### Completion Checker 可以做什么

Checker 可以：

* 检查各项 Research Requirement 是否真正得到覆盖；
* 检查关键 Landscape Finding 是否有可追溯 grounding；
* 检查结论强度是否超过来源实际支持范围；
* 检查重要研究分歧或相互冲突的结果是否被忽略；
* 检查是否仍存在足以阻止交付的 Investigation Gap；
* 对影响 Completion Verdict 的关键来源做 targeted source inspection。

例如，它可以根据某个关键 Landscape Finding 的 `LiteratureSource` 与 locator 回读论文具体位置，确认 source passage 与当前 interpretation 是否一致。

但它默认不做：

* broad search；
* 系统性发现新论文；
* 大规模 Deep Reading；
* 重建整个技术路线；
* 重新完成一次独立领域调研。

如果 Completion Checker 需要重新做完整研究，它就已经越过了自己的职责边界。

### Completion Check 结果

Checker 输出最小 typed result：

```text
PASS
CONTINUE
UNCERTAIN
```

`PASS` 表示：

> 基于当前 Research Contract、Research State 及其可核验 grounding，没有发现足以阻止进入 Delivery 的关键问题。

它不表示“所有结论都已经证明为绝对真理”。

`CONTINUE` 表示：

> 仍存在一个足以阻止当前完成、且可以继续调查的具体缺口。

`CONTINUE` 必须给出 actionable blocking gap。仅仅说“建议搜索更多论文”不构成有效的继续理由。

`UNCERTAIN` 表示：

> 当前状态不足以让 Checker 做出可靠完成性判断。

例如关键来源不可访问，或 Research Contract 本身存在需要用户澄清的歧义。

Python Harness 只验证 Verdict 的结构、引用和状态合法性，不替 Checker 做语义判断。

## DELIVERY

`DELIVERY` 表示 Research 已经通过 Completion Check，当前系统进入基于已批准研究基础完成正式交付的状态。

它解决的是一个真实控制差异：

```text
Completion Check PASS
≠
最终交付已经存在
```

在 Delivery 中可以执行：

* Synthesize；
* Write Report；
* Render Bibliography；
* Mechanical Citation Validation；
* 其它不改变研究基础的交付动作。

因此 `SYNTHESIZE` 不单独成为 Lifecycle Phase。

### Delivery 中发现重大问题

如果 Delivery 过程中发现新的 Critical Gap、grounding 错误、Research State 中的实质判断错误，或其它足以使原 Completion Check 失效的问题，不创建 Revision Phase。

而是：

```text
DELIVERY
    ↓
invalidate prior completion approval
    ↓
RESEARCH
```

之后重新进入原 Research Loop，并在适当时再次请求 Completion Check。

这样避免形成第二套 Report Revision Workflow。

## CLOSED

`CLOSED` 是 Research Run 的终止状态。

终止后的 authoritative Research State 默认不再接受普通 Research Mutation。

最终结果单独记录为：

```text
outcome = COMPLETE
```

或：

```text
outcome = PARTIAL
```

`COMPLETE` 和 `PARTIAL` 不分别成为 Lifecycle Mode，因为它们的控制行为相同：Run 都已经终止。

它们表达的是终止结果，而不是不同的控制阶段。

### COMPLETE

表示：

* Completion Check 已通过；
* 必要 Delivery 已完成；
* Run 正常闭合。

### PARTIAL

表示：

* 已知仍存在重要不足；
* 由于预算、来源不可用、用户决策或其它明确限制，不再继续研究；
* 当前结果以不完整状态诚实交付并关闭。

Budget exhausted 本身不能自动产生 `PARTIAL`，更不能产生 `COMPLETE`。

## PLAN 不成为 Lifecycle Mode

Research Contract 的初始形成发生在正式 Run 创建之前：

```text
User Request
    ↓
Claude understands task
    ↓
draft Research Contract
    ↓
Python validates
    ↓
create Research Run
    ↓
RESEARCH
```

如果没有合法 Contract，Harness 不创建正式 Research Run。

因此 `PLAN` 目前没有独立的控制 invariant，不需要成为 Lifecycle Mode。

Run 创建后的 Contract Amendment 由后续 ADR 单独设计。

## Lifecycle 与其它事实保持正交

Lifecycle 不承担所有状态表达。

Research Run 至少要区分三类事实：

```text
                         Research Run
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
   Lifecycle Mode       Research Facts       Resource Facts
          │                   │                   │
      RESEARCH        Papers / Paper Analysis    Budget
 COMPLETION_CHECK       Literature Landscape     Provider
      DELIVERY           Investigation Gaps      Cost
       CLOSED           Completion Checks        Limits
```

例如：

```text
budget exhausted
provider failed
required grounding missing
critical gap exists
outcome = PARTIAL
```

都不应该被塞进 Lifecycle Enum。

同样，不应长期持久化一组可以由 Lifecycle 和其它事实推导出来的重复布尔值，例如：

```text
research_allowed
check_required
delivery_allowed
terminal
```

如果这些值可以从 authoritative state 推导，就应该在读取时计算。

## 为什么不选择更少的三个状态

候选方案：

```text
RESEARCH
COMPLETION_CHECK
CLOSED
```

表面上更少，但 Completion Check PASS 后、最终报告尚未完成时存在真实的控制差异：

* Research mutation 应保持关闭；
* Delivery action 应被允许；
* Run 尚未真正完成；
* Session crash 后需要明确恢复到交付阶段。

如果删除 `DELIVERY`，这些差异只能通过多个布尔条件隐式表达。

因此三个状态属于“表面更少、隐式状态更多”。

## 为什么不选择更多阶段

另一候选方案是：

```text
PLAN
RESEARCH
REVIEW
SYNTHESIZE
DONE / PARTIAL
```

它的问题是把工作动作和结果类型升级成 Lifecycle State。

这会让能力数量逐渐驱动 Phase 数量，并重演旧 Search Harness 中的控制流膨胀。

当前四状态模型只保留真正改变 authority、allowed actions、invariants 和 resume meaning 的状态。

## 参考证据

本决策与六份 Tier-1 Reference 的主要结论一致：

* `spec-kit-harness`：支持简单 Loop、外置状态、bounded context；
* `old-search-harness`：证明 Action 升级为大量 Phase 会导致 control-flow explosion；
* `PaperQA`：证明 Search、Read、Evidence Gathering 等可以作为 agent-driven research actions，而不需要独立生命周期；
* `spec-kit-loop`：支持 Maker / Checker 分离和 fresh completion checking；
* `Superloopy`：证明 Evidence-Gated Completion 不要求复杂 State Machine；
* `spec-kit-wiki`：支持将长期知识投影放在研究完成后的派生层，而不是侵入 Research Lifecycle。

Reference 是设计证据，不是必须复制的流程模板。

## 验证方式

后续实现至少应通过以下场景：

1. 新增 Search、Deep Read、Follow Citation 等能力时，不需要增加 Lifecycle Mode。
2. Researcher 不能从 `RESEARCH` 直接进入 `CLOSED`。
3. 进入 `COMPLETION_CHECK` 后，改变研究基础的 mutation 被拒绝。
4. Completion Checker 使用 fresh context，并只接收 bounded check view。
5. `CONTINUE` 返回具体 blocking gap 后，Run 回到同一个 `RESEARCH`。
6. `PASS` 后进入 `DELIVERY`，而不是直接 `CLOSED`。
7. `DELIVERY` 中发现重大新 Gap 时，可以回到 `RESEARCH`，不创建 Revision Workflow。
8. Budget exhausted 不改变 Lifecycle Mode，也不自动决定 semantic completion。
9. Provider failure 不产生新的 Lifecycle Mode。
10. Session 在 `RESEARCH`、`COMPLETION_CHECK` 或 `DELIVERY` 中断后，都能依赖持久状态恢复。
11. `COMPLETE` 和 `PARTIAL` 作为 `CLOSED` 的 Outcome 记录，而不是独立 Lifecycle Phase。

如果未来实现需要大量 `awaiting_*`、`blocked_*`、`revision_*` Phase 才能正常运行，应重新检查是否把 Research Fact、Resource Fact 或 Action 错误塞进了 Lifecycle。

## 决策摘要

Research Run 的 Lifecycle 只记录真正的控制权变化：

```text
RESEARCH
→ COMPLETION_CHECK
→ DELIVERY
→ CLOSED
```

研究动作留在 `RESEARCH`，完成性判断交给 fresh Completion Checker，交付动作留在 `DELIVERY`，最终完成程度由 `CLOSED` 的 Outcome 表达。

> **Lifecycle 描述控制权，不描述工作步骤。**

> **Completion Check 是完成性门，不是论文 Review，也不是第二套 Research Workflow。**
