# ADR-005：Research State 通过类型化变更在 ResearchRun 边界内原子更新

* **状态**：已接受
* **阶段**：Runtime / State Mutation
* **日期**：2026-08-09
* **影响范围**：ResearchRun、State Mutation、Domain Commands、Persistence、Concurrency Control
* **关联决策**：

  * ADR-001 — Claude Code 驱动研究循环，Python Harness 守住系统不变量
  * ADR-002 — Research Run 使用四个最小生命周期模式
  * ADR-003 — Research Contract 定义 Research Run 的语义边界
  * ADR-004 — 持久化论文级理解与领域级理解

## 背景

ADR-004 已经定义了 Research Run 需要长期保存什么：

```text
ResearchRun
├── Contract
├── Lifecycle
├── Resources
├── Papers
├── Literature Landscape
├── Investigation Gaps
└── Completion Checks
```

下一步的问题不是继续增加 State，而是：

> **Claude 应该如何安全地修改这些 State？**

如果每个字段都设计一个专门函数，例如：

```text
set_paper_analysis
add_finding_source
remove_finding_source
set_gap_status
resolve_gap
rename_approach_family
add_representative_paper
...
```

接口数量会随着 Domain Model 增长，最终重新形成大量命令和分支逻辑。

另一种极端是提供：

```text
update_state(path, value)
```

或通用 JSON Patch。

虽然接口很少，但它允许调用者绕过领域边界，直接修改 Lifecycle、Contract、Completion Check 或其它受保护状态。Python Harness 将失去守住系统不变量的能力。

因此我们需要一个中间方案：

> **普通状态变化使用极少数类型化原子操作；真正涉及领域不变量的变化使用显式领域命令。**

这样既保持接口统一，也不隐藏重要语义。

## 决策

V1 将 `ResearchRun` 视为整个 Research Run 的状态一致性边界。

所有持久化研究状态都必须通过这一边界修改。

概念上：

```text
Claude
  │
  ▼
Typed Mutation / Domain Command
  │
  ▼
ResearchRun
  │
  ├── 权限检查
  ├── 类型检查
  ├── 局部不变量检查
  ├── 跨对象引用检查
  └── Lifecycle 检查
  │
  ▼
Proposed State
  │
  ▼
Whole-state Validation
  │
  ▼
Atomic JSON Replace
```

V1 借鉴 DDD 中 Aggregate、Entity、Value Object，Command Pattern、Repository、Unit of Work 和 Optimistic Locking 的思想。

这些模式只用于明确边界和减少特殊逻辑。

**不因此引入数据库、消息总线、事件溯源、工作流引擎或其它新的基础设施。**

## ResearchRun 是统一的一致性边界

`ResearchRun` 是 V1 的 Aggregate Root。

这并不意味着所有业务逻辑都塞进一个巨大 Python 类。

它意味着：

> **一次 Research Run 内需要共同保持一致的状态，通过同一个边界读取、验证和提交。**

例如一次论文深读可能同时产生：

```text
Paper Analysis 更新
Approach Family 更新
Landscape Finding 更新
Investigation Gap 关闭
新的 Investigation Gap 创建
```

这些变化属于同一次研究判断。

如果 Paper、Finding、Gap 分别独立提交，一次 Session Crash 就可能留下半更新状态。

因此 V1 不为 Paper、Finding、Gap 分别建立独立 Repository 或独立事务边界。

它们都属于当前 `ResearchRun`。

## State 使用强类型对象，而不是自由 Dict

内存中的 Research State 应表现为强类型 Domain Model。

例如：

```text
ResearchRun
│
├── ResearchContract
├── Lifecycle
├── ResourceState
│
├── Paper
│   ├── PaperSource
│   ├── ResearchStatus
│   └── PaperAnalysis
│
├── LiteratureLandscape
│   ├── ApproachFamily
│   ├── LandscapeFinding
│   └── OpenProblem
│
├── InvestigationGap
└── CompletionCheck
```

具体使用 Pydantic、dataclass 或其它 Python 类型工具属于实现选择，本 ADR 不冻结。

重要的是：

> **State 必须有明确类型、字段和不变量，不能让 Runtime 把任意 JSON 当成合法 Research State。**

## Entity 与 Value Object

V1 使用经典 DDD 中 Entity / Value Object 的区分，但不为此建立复杂类层级。

具有稳定身份、会被其它对象长期引用的概念属于 Entity，例如：

```text
Paper
ApproachFamily
LandscapeFinding
OpenProblem
InvestigationGap
CompletionCheck
```

只由自身值决定语义、不需要独立身份的概念适合作为 Value Object，例如：

```text
PaperAnalysis
PaperSource
LiteratureSource
SourceLocator
ResourceState
```

例如：

```text
LiteratureSource
├── paper_ref
├── relation
└── locator?
```

不需要额外的 `source_id`。

它的意义就是这些字段共同表达的值。

原则是：

> **只有真正需要稳定身份的对象才获得 ID。**

## 普通字段修改只使用 PUT 和 MERGE

普通、局部的状态修改只需要两个基础操作：

```text
PUT
MERGE
```

### PUT

`PUT` 表示：

> **将一个允许修改的位置设置为新的完整值。**

例如：

```text
PUT Paper[P8].analysis = PaperAnalysis(...)

PUT InvestigationGap[IG3].state = RESOLVED

PUT LandscapeFinding[LF4].statement = "..."
```

对于允许创建的类型化集合项，`PUT` 也可以表示创建新的 canonical object。

例如：

```text
PUT InvestigationGap[IG7] = InvestigationGap(...)
```

具体 ID 可以由 Harness 分配或解析。

`PUT` 不是任意路径写入。

目标类型、字段和值都必须符合 Domain Schema。

### MERGE

`MERGE` 只用于集合型字段的类型安全增量更新。

例如：

```text
MERGE ApproachFamily[AF2].representative_papers
  + P8
  + P12
```

或：

```text
MERGE LandscapeFinding[LF4].sources
  + LiteratureSource(
      paper=P12,
      relation=QUALIFIES,
      locator="Table 4"
    )
```

`MERGE` 不表示任意递归字典合并。

每一种字段类型自己定义什么叫合法 Merge。

例如 `set[PaperRef]` 可以定义 add/remove；`set[LiteratureSource]` 可以定义来源集合更新。

这样普通状态变化不会继续增长成：

```text
add_source
remove_source
add_paper
remove_paper
set_status
set_analysis
...
```

一套字段一个函数的 API。

## 每个类型决定哪些字段可以被修改

统一的 `PUT / MERGE` 并不意味着所有字段都能自由修改。

例如：

```text
Paper
├── id
├── source
├── research_status
└── analysis
```

普通 Researcher 可以：

```text
PUT research_status
PUT analysis
```

但不能：

```text
PUT id
PUT source
```

因为 `source` 决定这究竟是哪一篇论文。

同理：

```text
LandscapeFinding.statement
→ PUT

LandscapeFinding.sources
→ PUT / MERGE

ApproachFamily.representative_papers
→ PUT / MERGE
```

而：

```text
Lifecycle.mode
```

虽然技术上只是一个字段，却完全不允许通过普通 `PUT` 修改。

因此：

> **字段结构决定数据形状；领域规则决定允许怎样改变它。**

## 原子字段操作不取代领域命令

并不是所有变化都应该强行表示成字段修改。

如果一个动作涉及对象身份、多个引用、生命周期或完成权限，就应该保留明确的领域语义。

例如：

```text
AF3 应归并到 AF2
```

不应该要求 Claude 手动执行：

```text
修改所有 Finding 对 AF3 的引用
修改所有 Gap 对 AF3 的引用
迁移 representative papers
删除 AF3
```

而应该使用一个明确的领域命令：

```text
MergeApproachFamily(AF3 → AF2)
```

Claude 决定：

> AF3 应该并入 AF2。

Python Harness 负责：

> 确定性地重写所有引用，并保证最终 State 一致。

类似的领域命令包括：

```text
RetainPapers
RetireLandscapeItem
MergeApproachFamily

AmendContract

RequestCompletionCheck
SubmitCompletionCheck

AuthorizePartialDelivery
CloseRun
```

具体命令名和外部协议格式可以在实现阶段调整。

本 ADR 冻结的是原则：

> **局部变化统一表达，跨不变量变化显式表达。**

## Paper 的进入使用显式领域命令

搜索 Provider 返回的 Raw Search Hit 不是 Persistent Paper。

Claude 决定保留某篇论文以后，通过：

```text
RetainPapers
```

进入 Research State。

Harness 负责机械工作：

```text
标准化 DOI / arXiv ID
识别明确重复项
分配稳定 Paper ID
建立 PaperSource
写入当前 Run
```

这借鉴 Factory Pattern：

```text
External Search Hit
        ↓
Paper Factory
        ↓
Persistent Paper
```

但 V1 不要求真的建立复杂 Factory 框架。

核心只是：

> **外部搜索结果不能绕过 Paper identity 规则直接写进 State。**

## Lifecycle 只能通过 Transition 改变

Lifecycle 描述控制权，因此不能作为普通字段修改。

非法：

```text
PUT Lifecycle.mode = DELIVERY
```

合法变化只能通过领域命令发生。

例如：

```text
RequestCompletionCheck
RESEARCH → COMPLETION_CHECK
```

以及 Completion Checker 的正式 Verdict：

```text
PASS
COMPLETION_CHECK → DELIVERY
```

Lifecycle 内部遵守 ADR-002 已确定的有限状态机。

因此：

> **数据上是一个 Enum，语义上是一个 State Machine。**

V1 不需要引入专门的 State Machine 框架。

## Research Contract 不能通过普通 Mutation 修改

Research Contract 定义 Completion Check 的边界。

因此普通 Research Mutation 不能：

```text
PUT Contract.requirements
MERGE Contract.scope
```

Contract 改变必须通过：

```text
AmendContract
```

显式发生。

Harness 负责：

```text
产生新的 contract_revision
记录修订原因
使旧 Completion PASS 失效
必要时回到 RESEARCH
```

这样 Researcher 不能通过普通 State Mutation 静默降低完成标准。

## CompletionCheck 是不可变记录

一次 Completion Check 完成后，其结果不再修改。

不能：

```text
PUT CC7.verdict = CONTINUE
```

来改写曾经的 PASS。

新的检查产生新的 `CompletionCheck`。

因此：

> **历史判断通过追加新记录演化，而不是修改旧判断。**

这保证 Completion Check 可以可靠审计。

## 修改权限由角色、Lifecycle 和目标共同决定

权限不应该散落在每个字段函数里。

概念上，Harness 根据：

```text
Actor
×
Lifecycle Mode
×
Target Type
×
Field / Command
×
Operation
```

决定当前变化是否允许。

例如：

```text
Researcher
+ RESEARCH
+ Paper.analysis
+ PUT
→ allowed
```

而：

```text
Researcher
+ DELIVERY
+ LandscapeFinding.statement
+ PUT
→ denied
```

Delivery 阶段可以：

```text
PUT LiteratureSource.locator
```

精化已有引用位置。

但不能修改：

```text
LandscapeFinding.statement
```

如果引用核查发现研究理解本身错误，应按照 ADR-004 回到 `RESEARCH`，而不是在 Delivery 中偷偷修改 Landscape。

这里借鉴 Policy / Capability 的思想，但 V1 不引入 RBAC 系统或权限基础设施。

它可以只是清晰、可测试的 Python 规则。

## 一次语义变化作为一个原子 Batch 提交

一次 Claude 推理可能自然地产生多个相关修改。

例如深读 P8 后：

```text
PUT P8.analysis

MERGE AF2.representative_papers += P8

MERGE LF4.sources += P8/Table2

PUT IG3.state = RESOLVED

PUT IG3.resolution = "..."

PUT IG7 = new InvestigationGap
```

它们应该作为一个 Mutation Batch 提交。

Harness 按以下顺序处理：

```text
读取当前 ResearchRun
        ↓
检查 expected_revision
        ↓
检查权限
        ↓
在内存中构造 Proposed State
        ↓
应用全部 Mutation / Domain Command
        ↓
检查对象局部不变量
        ↓
检查跨对象引用
        ↓
检查完整 ResearchRun
        ↓
全部合法后一次写入
```

任何一步失败：

> **整批不提交。**

这样不会产生“Paper Analysis 已更新，但 Gap 还没关闭”一类半完成状态。

这里借鉴 Unit of Work 的思想。

但 V1 的 Unit of Work 只是：

> **一批内存状态修改 + 一次原子文件替换。**

不引入事务管理器。

## 使用 revision 防止旧 Context 覆盖新 State

每个 `ResearchRun` 保存一个单调递增：

```text
state_revision
```

Claude 获取 Context 时同时获得当前 revision。

例如：

```text
state_revision = 42
```

提交修改时：

```text
expected_revision = 42
```

如果当前 State 已经变成：

```text
state_revision = 43
```

Harness 拒绝这次修改，并要求调用者基于新 State 重新判断。

这借鉴 Optimistic Locking。

它主要防止的不是多线程数据库竞争，而是：

> **旧 Claude Context 对已经变化的 Research State 继续写入。**

`state_revision` 与 ADR-003 中的 `contract_revision` 是两个不同概念。

```text
state_revision
→ 整个 Run 当前状态版本

contract_revision
→ Research Contract 的语义修订版本
```

二者不应混用。

## V1 使用本地 JSON 作为权威持久化状态

本 ADR 明确：

> **V1 不因为采用经典设计模式而引入数据库。**

每个 Research Run 可以保持非常简单的本地目录：

```text
runs/
└── R001/
    ├── state.json
    ├── events.jsonl
    ├── sources/
    └── artifacts/
```

其中：

```text
state.json
```

是当前 Research Run 的**唯一权威状态快照**。

它保存可以恢复 Research Process 所需的 typed state。

例如：

```text
run_id
state_revision
contract
lifecycle
resources
papers
literature_landscape
investigation_gaps
completion_checks
delivery_basis
```

具体 JSON Schema 由实现阶段确定。

## JSON 写入使用临时文件和原子替换

保存时不直接覆盖当前 `state.json`。

使用：

```text
serialize proposed ResearchRun
        ↓
write state.json.tmp
        ↓
flush / close
        ↓
atomic replace
        ↓
state.json
```

只有完整 State 通过全部验证后才发生替换。

因此即使进程在写入途中 Crash，原来的 authoritative `state.json` 仍然存在。

这已经足以满足 V1 的本地单写者可靠性需求。

## events.jsonl 是辅助审计，不是第二份真相

`events.jsonl` 可以记录：

```text
revision
actor
mutation / command summary
reason
timestamp
provider outcome
```

用于调试、审计和解释 Research Run 如何演化。

但是：

> **Research State 的正确性不能依赖 Event Log。**

恢复 Run 只需要 `state.json`。

如果 State 已经成功提交而 Event Log 因 Crash 少了一条记录：

> Research Run 仍然是合法的。

因此 V1 不要求 `state.json` 与 `events.jsonl` 具有数据库级事务一致性。

这也是我们明确不采用 Event Sourcing 的原因。

## Repository 只是薄持久化边界

Domain Model 不应该知道 State 存储在 JSON 文件里。

概念上只需要一个很薄的 Repository：

```text
load(run_id) → ResearchRun

save(run, expected_revision)
```

V1 实现是：

```text
JsonResearchRunRepository
```

这样未来只有在真实需求出现时，例如：

```text
大量并发 Run
复杂查询
State 大到整文件读写成为瓶颈
严格跨记录事务需求
```

才有理由替换底层实现。

在这些问题出现之前：

> **不引入 SQLite、PostgreSQL 或其它数据库。**

Repository Pattern 在这里的价值，不是让系统现在更复杂，而是：

> **让我们可以安心保持当前存储简单。**

## 不引入新的基础设施复杂度

本 ADR 明确拒绝因为“使用成熟模式”而附带引入以下系统：

```text
Database
ORM
Event Sourcing
Message Bus
Event Bus
Saga
Workflow Engine
Actor Runtime
Distributed Lock
Separate Read Database
Transaction Coordinator
```

这些都不是 V1 当前问题所需要的。

如果未来真实需求证明其中某项必要，应单独提出新的架构问题和 ADR，而不是在本阶段提前建设。

原则是：

> **设计模式用来减少自己发明的复杂度，不是用来合理化新的基础设施。**

## 典型研究事务

一次真实 Deep Read 可以表现为：

```text
当前 state_revision = 41

Claude 阅读 P8
        ↓
形成新的论文级和领域级理解
        ↓
提交 Batch

PUT P8.analysis

MERGE AF2.representative_papers += P8

MERGE LF4.sources +=
    LiteratureSource(
        paper=P8,
        relation=SUPPORTS,
        locator="Table 2"
    )

PUT IG3.state = RESOLVED

PUT IG3.resolution =
    "现有结果存在 setup dependency，已形成 LF7"

PUT IG7 =
    InvestigationGap(...)
```

Harness：

```text
revision == 41
        ↓
权限合法
        ↓
引用合法
        ↓
对象不变量合法
        ↓
ResearchRun 整体合法
        ↓
atomic replace state.json
        ↓
state_revision = 42
```

Python 不判断：

> P8 是否真的支持 LF4。

这是 Claude 的研究判断，并最终由 Completion Check 挑战。

Python只判断：

> P8 是否存在、字段是否合法、当前角色是否允许修改、引用是否有效、整个 State 是否保持结构一致。

因此继续遵守 ADR-001：

> **Claude 决定研究语义；Python 守住系统不变量。**

## 验证方式

后续实现至少应证明以下场景成立：

1. 多个相关 Research Mutation 可以一次提交，任何一个失败都不会产生部分 State。
2. 普通字段更新不需要一个字段对应一个专门函数。
3. 未被 Schema 允许的字段不能通过 `PUT / MERGE` 修改。
4. Researcher 无法通过普通 Mutation 修改 Lifecycle 或 Research Contract。
5. Approach Family 合并可以通过一个领域命令完成，并由 Harness 确定性重写相关引用。
6. Completion Check 形成后不能被普通 Mutation 修改。
7. Delivery 可以精化已有 Source Locator，但不能修改 substantive Landscape Finding。
8. 基于旧 `state_revision` 的修改会被拒绝。
9. `state.json` 写入过程中 Crash 不会破坏上一份合法 State。
10. 删除 `events.jsonl` 后，Research Run 仍然可以从 `state.json` 正常恢复。
11. 新增普通字段时，如果它只需要 `PUT / MERGE`，不需要增加新的 Runtime Command。
12. 新的领域命令只有在真实存在跨对象不变量时才引入。

## 决策摘要

Research State 的写入模型保持为：

```text
Typed Research State
        │
        ▼
PUT / MERGE
for ordinary local changes
        │
        +
Explicit Domain Commands
for invariant-changing actions
        │
        ▼
ResearchRun
consistency boundary
        │
        ▼
Whole-state validation
        │
        ▼
Atomic JSON Snapshot
```

V1 借鉴经典 DDD、Command、Repository、Unit of Work 和 Optimistic Locking 的设计思想，但不把这些模式扩展成新的基础设施。

最终原则是：

> **状态有类型，局部修改统一，领域变化显式。**

> **一次研究判断整体提交，而不是逐字段留下半完成状态。**

> **Repository 隔离存储，是为了保持 JSON 简单，而不是为了提前引入数据库。**

> **成熟设计模式应该帮助系统变简单，而不是让架构图变复杂。**
