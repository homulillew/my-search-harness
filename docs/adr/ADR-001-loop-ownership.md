# ADR-001：Claude Code 驱动研究循环，Python Harness 守住系统不变量

- **状态**：已接受
- **阶段**：Architecture Design
- **日期**：2026-08-09
- **影响范围**：Research Loop、Control Plane、Runtime Boundary

## V1 术语收敛说明

本 ADR 确立的 Claude / Python 控制边界仍然有效，但本文写于 V1 Research State 对象模型正式收敛之前。

后续 ADR-002～ADR-004 对部分早期术语进行了进一步定义。本文中的相关表达按以下方式理解：

* `Evidence` 不表示独立持久化实体。V1 中，重要研究判断通过 `Paper Analysis`、`Landscape Finding` 及其 `LiteratureSource` 保持来源 grounding，并可通过 Source Access 回到 Primary Paper 核验。
* `Contradiction` 不建立独立 Domain Entity。研究间的重要冲突保留在 Literature Landscape 的判断、来源关系与不确定性表达中。
* `Research Gap` 在 V1 中进一步区分为 `Investigation Gap` 与 `Open Problem`：前者表示当前 Run 尚未调查充分的问题，后者表示领域本身仍未解决的问题。
* 本 ADR 中的 `Review / Reviewer` 后续正式收敛为 `Completion Check / Completion Checker`。

V1 的持久化 Research State 与 grounding 模型以 ADR-004 为准；本 ADR 继续作为 Loop Ownership 与 Authority Boundary 的决策依据。

参考项目描述中的 `Evidence Interpretation`、`Evidence Gate` 等词保留原文。这些位置描述的是一般意义上的“证据”或外部项目自己的概念，并不声明 V1 存在 `Evidence` Domain Entity，无需为术语统一而机械替换。

## 背景

本项目要构建一个面向 Claude Code 的论文调研 Harness。

研究过程本身具有很强的语义性。搜索什么、读哪篇论文、什么时候需要深入阅读、如何解释 Evidence、当前还缺什么，这些判断都依赖对研究问题和已有证据的理解。如果把这些决策提前编码进 Python，Harness 很容易逐渐演变成第二套 Agent Runtime，并重新出现旧实现中的问题：Phase 不断增加、控制流膨胀、语义判断被压进状态机和分数规则。

另一方面，如果 Python 只是一个没有状态和约束的工具集合，Claude 又可能绕过预算、重复执行动作、写入非法状态，甚至直接宣布研究完成。

因此需要明确 Claude Code 与 Python Harness 的控制边界。

## 决策

Claude Code 是 Research Loop 的主动执行者，也是语义研究决策的责任方。

Python Harness 不主动编排研究策略，也不决定“下一步最值得研究什么”。它围绕持久化 Research State 提供确定性动作，并负责守住系统不变量。

可以概括为：

```text
Claude owns agency.
Python owns invariants.
State carries continuity.
```

具体来说：

### Claude Code 负责语义研究判断

包括但不限于：

- 理解用户研究问题；
- 形成和调整研究策略；
- 生成搜索 Query；
- 选择值得阅读的论文；
- 决定阅读深度；
- 解释论文内容，形成 `Paper Analysis`，并据此更新有来源支撑的 Literature Landscape；
- 识别 `Investigation Gap`、`Open Problem` 以及 Literature Landscape 中的重要冲突；
- 判断是否已经值得请求 Review；
- 完成最终 Synthesis。

### Python Harness 负责确定性机制与约束

Python 不判断研究意义，而负责三类完整性。

**状态完整性**

- ID 与引用关系合法；
- 状态写入可靠；
- 必要结构完整；
- 并发写入不会破坏 Run；
- 可恢复的状态能够稳定落盘。

**控制完整性**

- 当前动作是否允许执行；
- 预算是否允许继续消耗资源；
- 当前角色是否拥有对应状态的写权限；
- 生命周期约束是否被违反；
- Researcher 不能直接写最终 Completion Verdict。

**边界完整性**

- Provider 失败不能被解释成“没有搜索结果”；
- 外部论文、网页和 PDF 内容只能作为研究数据，不能成为 Harness 控制指令；
- 重要研究判断关联的 Paper / `LiteratureSource` 及其 locator 必须能够解析，并在需要时回读 Primary Source。

Python 可以拒绝一个非法动作，但不应该替 Claude 选择另一个语义动作。

例如，当 Search Budget 已经耗尽时，Python 可以拒绝新的 `SEARCH`，但不应该自行决定下一步必须 `READ` 或 `REVIEW`。它只暴露当前事实、约束和允许的操作，由 Claude 根据研究状态继续判断。

## Research Loop 的基本形态

```text
Persistent Research State
          │
          ▼
   bounded state view
          │
          ▼
     Claude Code
  decides next action
          │
          ▼
    Python Harness
 validate / execute / persist
          │
          ▼
Persistent Research State
          │
          └───────────────↺
```

研究循环的连续性来自持久状态，而不是某一个 Claude Code Session。

Session 可以结束，新的 Claude Context 只要能够从 Research State 重建当前工作视图，就可以继续同一个 Research Run。

## Review 的位置

Researcher 可以认为研究“可能已经足够”，但不能直接宣布完成。

它只能提出：

```text
REQUEST_REVIEW
```

随后由 fresh-context Completion Checker 根据当前 Research Contract、Literature Landscape、Investigation Gaps、Open Problems、grounding source refs 和 completion rationale 做独立语义判断。

```text
Researcher
    │
REQUEST_REVIEW
    ▼
Fresh Completion Checker
    │
    ├── PASS
    ├── CONTINUE
    └── UNCERTAIN
```

这里的 Review 是一次完成裁决权的切换，不是第二套 Research Workflow。

Completion Checker 不负责重新搜索整个领域，也不承担日常 Deep Reading。深读论文仍然属于正常 Research Loop 中的 Research Action。

Python 可以机械保证 Researcher 无权写最终 Completion Verdict；Completion Checker 是否运行在 fresh context 中，则由 Claude Code 的执行协议保证。

## 为什么不选择 Python 驱动完整循环

一种直接方案是让 Python 持有主循环：

```text
while not done:
    ask Claude what to do
    execute
    update state
```

这种设计表面上更容易控制，但 Python 很快需要理解越来越多研究语义：

- 当前应该 Search 还是 Read；
- 哪个 Gap 更重要；
- 是否需要继续引用扩展；
- 当前 Research State 的关键判断是否已有足够、可核验的文献支撑；
- 什么时候应该结束某个研究分支。

这些判断一旦进入 Python，就会逐渐形成复杂 Orchestrator。

旧 Search Harness 已经提供了明确的负面经验：当 Research Action 被不断升级成 Lifecycle Phase，并通过加权 sufficiency score 和多个子循环推进时，Rich State 最终转化成了 Rich Control Flow。

因此本项目不采用 Python 主动驱动 Research Policy 的方案。

## 为什么不选择“Claude 完全自由，Python 只是工具库”

完全依赖 Prompt 纪律也不够。

预算、状态合法性、来源引用完整性、Provider Failure Semantics、Completion Authority 等约束具有明确的机械性质，应由 Runtime 强制，而不是依赖 Claude 每次记得遵守。

因此 Python Harness 必须是有状态的 Control Envelope，而不是无状态工具集合。

## 设计后果

这一决策意味着：

1. Python 中不应出现负责“下一步研究什么”的语义 Planner 或大型 Orchestrator。
2. 新增 Search、Read、Follow Citation、Compare、Deep Read 等能力时，默认把它们视为 Research Action，而不是新的 Lifecycle Phase。
3. `allowed actions`、control obligations 等信息应尽量从当前状态与规则推导，而不是作为重复事实长期持久化。
4. 能由已有事实推导出来的控制状态，不应为了方便再保存一份副本。
5. Resume 恢复的是 Research Process，不是 Conversation。
6. Deep Reading 可以未来使用临时 subagent 优化执行，但不因此成为新的 Architecture Role。
7. Reviewer 是少数真正值得拥有独立上下文和独立权限的角色，因为它解决的是 Completion Authority，而不是研究效率问题。

## 暂不决定

本 ADR 只确定控制权边界，不决定以下内容：

- 最终 Lifecycle 有几个 Phase；
- `PLAN`、`SYNTHESIZE` 是否属于 Phase；
- Action 的具体 API；
- `allowed actions` 的推导方式；
- Research State 的最终 Schema；
- Context Renderer 的具体接口；
- Review Verdict 的最终数据模型；
- Claude Code 如何启动 fresh Reviewer 的具体命令；
- 是否以及何时使用 Deep-Reading subagent。

这些问题由后续 Architecture Decisions 单独处理。

## 参考证据

本决策主要建立在以下 Tier-1 Reference 的共同证据上：

- `spec-kit-harness`：状态外置、bounded context、Policy 与 bookkeeping 分离；
- `old-search-harness`：复杂 Orchestrator、Phase Explosion 和 scalar sufficiency 的负面经验；
- `PaperQA`：LLM 负责 query / evidence interpretation，Python 负责 retrieval / serialization / citation 等确定性机制；
- `spec-kit-loop`：Maker 与 Checker 分离，Researcher 不能自己拥有最终完成权；
- `Superloopy`：Evidence Gate 可以保持很小，机械完整性与语义正确性必须分层；
- `spec-kit-wiki`：Prompt-only enforcement 的局限进一步说明确定性约束需要 Runtime 支持。

Reference 是本决策的证据，不是架构权威。本决策最终来自本项目自身的产品边界、运行推演和异常场景压力测试。

## 验证方式

后续实现应能够通过以下场景验证本 ADR：

- Claude 可以自由选择 Search、Read、Analyze 等研究动作，而 Python 不生成语义上的“最佳下一步”；
- Search Budget 耗尽时，Python 能拒绝新的 Search，但不会自动决定其它研究动作；
- Researcher 尝试直接写 DONE 时，Runtime 必须拒绝；
- Provider 超时不会被记录成空搜索结果；
- Evidence 引用不存在的 Paper 或 locator 时，Runtime 必须拒绝；
- Claude Code Session 结束后，新 Session 能仅依赖持久状态继续 Research Run；
- Reviewer 返回 CONTINUE 后，研究回到同一个 Research Loop，而不是进入独立 Revision Workflow。

如果实现这些场景需要 Python 理解研究内容、维护大量语义 Phase 或主动编排复杂 Workflow，应重新检查是否违反本 ADR。

## 决策摘要

本项目不在 Python 中重新实现一个 Agent。

Claude Code 负责研究主动性和语义判断；Python Harness 负责可靠执行、持久状态和不可越过的系统约束。

> **Claude 决定研究往哪里走，Python 保证它不会走出系统允许的边界。**
