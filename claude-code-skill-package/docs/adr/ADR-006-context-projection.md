# ADR-006：Research State 通过用途化投影渲染为有界 Context

* **状态**：已接受
* **阶段**：Runtime / Context Projection
* **日期**：2026-08-09
* **影响范围**：Context Rendering、Research Resume、Completion Check、Delivery、Read Interface
* **关联决策**：

  * ADR-001 — Claude Code 驱动研究循环，Python Harness 守住系统不变量
  * ADR-002 — Research Run 使用四个最小生命周期模式
  * ADR-003 — Research Contract 定义 Research Run 的语义边界
  * ADR-004 — 持久化论文级理解与领域级理解
  * ADR-005 — Research State 通过类型化变更在 ResearchRun 边界内原子更新

## 背景

ADR-004 和 ADR-005 已经分别回答：

> **Research Run 应该保存什么？**

以及：

> **这些 Research State 应该如何安全修改和持久化？**

当前 Research Run 的权威状态可以持续增长：

```text
ResearchRun
├── Contract
├── Lifecycle
├── Resources
├── Papers
│   └── Paper Analysis
├── Literature Landscape
│   ├── Approach Families
│   ├── Landscape Findings
│   └── Open Problems
├── Investigation Gaps
└── Completion Checks
```

但 Claude 每一步推理并不需要同时看到所有状态。

如果每次 Session 都直接把完整 `state.json` 放入 Context：

```text
Persistent State
      ↓
dump everything
      ↓
Claude Context
```

那么随着论文、Paper Analysis、Landscape Finding 和 Source Locator 增长，Context 成本也会持续增长。

最终会重新产生：

```text
状态虽然外置
↓
每轮又全部塞回 Conversation
↓
外置状态失去意义
```

另一种极端是让 Python 自动判断：

```text
哪些 Finding 最重要？
哪个 Gap 最值得研究？
哪几篇 Paper 最相关？
下一步 Claude 应该做什么？
```

这又会让 Context Renderer 逐渐变成第二个 Research Agent，与 ADR-001 中：

> **Claude 拥有 Semantic Decision Authority，Python 只负责确定性机制。**

发生冲突。

因此本 ADR 要解决的问题是：

> **完整 Research State 如何被稳定地转换成 Claude 当前需要的有限 Context，同时保持 State 可恢复、Context 有界，并且不让 Python 开始替 Claude 做研究语义判断？**

## 决策

Research State 与 Context 明确分离。

```text
Research State
=
持久化、权威、完整

Context
=
临时、派生、有界
```

Context 不持久化，也不成为新的知识来源。

当前 Lifecycle Mode 决定应该生成哪一种 Context Projection：

```text
                    ResearchRun
                        │
                        ▼
                       view
                        │
              current Lifecycle mode
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
    RESEARCH      COMPLETION_CHECK     DELIVERY
       │                │                │
       ▼                ▼                ▼
 Research View   Completion Check View Delivery View
```

三个 View 是三种不同的 Projection Contract，而不是三套独立 Runtime、三个持久化对象或三个新的生命周期。

Claude 需要更多细节时，通过 Stable Ref 使用统一的：

```text
inspect
```

按需读取具体 Domain Object。

整体读路径为：

```text
ResearchRun
    │
    ▼
   view
    │
    ▼
高层研究地图
    │
    ▼
 Stable Ref
    │
    ▼
  inspect
    │
    ▼
Domain Object
    │
    ▼
Source Ref / Locator
    │
    ▼
read_source
    │
    ▼
Primary Paper
```

`read_source` 属于外部论文访问能力，不属于 Context Renderer。

核心原则是：

> **先给地图，再按引用下钻。**

## Context 是 Projection，不是第二份 State

V1 不创建：

```text
research_context.json
completion_context.json
delivery_context.json
context-cache/
```

Context 必须始终从当前 authoritative `ResearchRun` 重新生成。

因此：

```text
state.json
   │
   ▼
ResearchRun
   │
   ▼
Projection
   │
   ▼
Context
```

而不是：

```text
state.json
   ↓
context.json
   ↓
后续继续修改 context.json
```

如果 Session 消失，新 Session 重新读取 Research State 并执行 `view` 即可恢复当前研究局面。

原则是：

> **State survives; Context is rebuilt on demand.**

也可以概括为：

> **持久化 State，不持久化 Context。**

## Context Renderer 只选择已有语义，不重新总结

ADR-004 中已经存在：

```text
Paper Analysis
Approach Family
Landscape Finding
Open Problem
Investigation Gap
```

这些对象本身就是研究过程形成的语义压缩结果。

因此 Context Renderer 不再调用 LLM 对它们进行第二次摘要。

禁止：

```text
75 Landscape Findings
       ↓
LLM summarize
       ↓
Context Summary
```

因为这会形成：

```text
Primary Paper
     ↓
Paper Analysis
     ↓
Landscape Finding
     ↓
Context Summary
```

不断从摘要生成摘要，会增加语义漂移，并制造一个无法直接回到 authoritative State 的中间知识层。

因此：

> **Context Renderer 选择和组织已有权威语义，不重新解释已有语义。**

英文可以概括为：

> **Select authoritative summaries; do not summarize summaries.**

## 当前 Lifecycle 决定 View，不额外传入 purpose

V1 不设计：

```text
view(run, purpose=RESEARCH)
view(run, purpose=COMPLETION_CHECK)
```

因为当前 `ResearchRun.mode` 已经是权威控制状态。

例如：

```text
mode = RESEARCH
```

只能生成 Research View。

```text
mode = COMPLETION_CHECK
```

只能生成 Completion Check View。

因此概念接口只需要：

```text
view(run)
```

由当前 Lifecycle 决定 Projection Contract。

这样避免出现：

```text
当前 mode = COMPLETION_CHECK
调用者却请求 ResearchView
```

这一类重复权限问题。

原则是：

> **可以从权威 State 推导出的信息，不再作为独立输入维护。**

## 不按 Research Action 增长 View 类型

Context View 不对应 Search、Read、Deep Read、Compare、Follow Citation 等具体 Research Action。

V1 不建立：

```text
SearchView
ReadView
DeepReadView
CompareView
AnalyzeView
CitationView
```

否则 Read Side 会重新出现与旧 Harness 类似的 Phase / Action Explosion。

ADR-002 已经确定：

> **Lifecycle 描述控制状态，Action 描述工作。**

ADR-006 延续同一原则：

> **View 服务稳定的 Lifecycle 语义目的，而不是具体工作步骤。**

因此 V1 只有三个 Projection Contract：

```text
Research View
Completion Check View
Delivery View
```

`CLOSED` 不需要继续驱动 Research Context；关闭后的 Wiki、Report 或其它查询属于后续 Projection / Knowledge 能力。

## Research View

Research View 服务的问题是：

> **当前已经知道什么，还有什么没有弄清？**

它需要让一个新的 Claude Session 能够恢复 Research Process，而不依赖旧 Conversation。

基础结构包括：

```text
Research View
│
├── state_revision
├── mode = RESEARCH
│
├── Research Contract
│   ├── Mission
│   ├── Research Requirements
│   └── Scope
│
├── Resource Summary
│
├── Literature Landscape
│   ├── Approach Family index
│   ├── Landscape Finding index
│   └── Open Problem index
│
├── Open Investigation Gaps
│
├── Paper Index
│
└── Latest Completion Feedback
    └── if previous check returned CONTINUE / UNCERTAIN
```

这里的 Paper Index 保存的是论文身份和足够支持导航的研究状态，而不是完整 Paper Analysis。

例如：

```text
P8  Tree Search with Process Reward Models
P9  ...
P10 ...
```

需要了解 P8 时：

```text
inspect P8
```

Research View 不推荐：

```text
recommended_next_action = investigate IG7
```

也不对 Gap 做语义优先级排序。

它只提供当前事实：

```text
Open Gaps:
IG3 ...
IG7 ...

Resources:
...
```

然后由 Claude 自己决定下一步研究行为。

这继续遵守 ADR-001：

> **Claude 决定研究什么，Python 只负责把当前状态可靠地展示出来。**

## Completion Check View

Completion Check View 服务的问题是：

> **当前 Literature Landscape 是否已经足以满足 Research Contract？**

因此它与 Research View 有意不同。

基础结构包括：

```text
Completion Check View
│
├── state_revision
├── mode = COMPLETION_CHECK
│
├── Research Contract
│   └── all Research Requirements
│
├── Literature Landscape
│   ├── all Approach Family summaries
│   ├── all Landscape Finding summaries
│   │    └── source refs / relations
│   └── all Open Problem summaries
│
├── Open Investigation Gaps
│
├── Representative Paper refs
│
└── Researcher Completion Rationale
```

Researcher Completion Rationale 必须明确标记为：

> **Researcher 的完成主张，而不是已经成立的事实。**

Fresh Completion Checker 可以：

```text
inspect LF4
inspect P8
read_source P8 / Table 2
```

验证已有研究状态。

但 Completion Checker 不负责：

```text
搜索大量新论文
建立新的技术路线
扩展 Literature Landscape
重新执行完整 Research Loop
```

如果 Checker 判断必须进一步研究才能完成判断，应返回：

```text
CONTINUE
```

或：

```text
UNCERTAIN
```

并交回 `RESEARCH`。

原则是：

> **Completion Checker 可以挑战已有研究状态，但不成为第二个 Researcher。**

## Completion Check View 默认不包含 Budget

Budget 描述：

> **还能够投入多少研究资源。**

Completion Check 判断：

> **当前研究理解是否已经足够。**

二者必须保持正交。

因此 Completion Check View 默认不显示：

```text
budget remaining
search count
research duration
number of actions
```

否则 Checker 可能因为：

```text
budget = 0
```

而降低对 Semantic Completion 的判断标准。

即使：

```text
Completion Check = CONTINUE
Budget = 0
```

也仍然是一个合法状态组合。

之后由 Control Plane 决定：

```text
扩展 Budget
或
用户明确授权 Partial Delivery
```

而不是让资源耗尽伪装成 PASS。

## Completion Check View 默认不包含 Action History

Completion Check 判断的是 Research State 是否足够，而不是 Researcher 是否足够努力。

因此以下内容默认不进入 Completion Check View：

```text
完整 Conversation
Search 次数
Read 次数
完整 Event History
“我们已经研究了很久”
```

这继续保持：

```text
Work
≠
Proof
≠
Completion
```

当前 authoritative Research State 应该已经足以表达：

> **研究实际学到了什么。**

如果必须依赖完整 Action History 才能判断当前领域理解，说明 Persistent State 本身设计不完整。

## Completion Check 使用冻结 State

进入 `COMPLETION_CHECK` 后，Research Mutation 被关闭。

假设：

```text
state_revision = 82
```

Completion Checker 看到：

```text
Completion Check View
state_revision = 82
```

后续：

```text
inspect LF4 expected_revision=82
inspect P8 expected_revision=82
```

都必须基于同一 Research State。

Completion Check 最终记录：

```text
basis_revision = 82
```

这里 `CompletionCheck.basis_revision` 是领域事实：

> **这次 Completion Check 检查的是哪一个 Research State。**

它与 Context 不需要再建立新的 `basis_revision` 概念。

## Delivery View

Delivery View 服务的问题是：

> **如何基于已经获准交付的 Research State 生成最终 Deliverable？**

基础结构包括：

```text
Delivery View
│
├── state_revision
├── mode = DELIVERY
│
├── Research Contract
│   ├── Mission
│   ├── Scope
│   └── Deliverable
│
├── Delivery Authorization
│   ├── Completion PASS
│   └── or explicit Partial Authorization
│
├── Literature Landscape
│
├── Literature Sources / Paper refs
│
└── Remaining Investigation Gaps / limitations
```

如果当前是 Partial Delivery，未解决的重要限制必须明确进入 View。

否则最终报告可能把：

```text
部分完成
```

错误写成：

```text
完整领域结论
```

Delivery 不按报告章节继续派生新的 View 类型。

例如写“技术路线 AF2”章节时，Claude可以：

```text
inspect AF2
inspect LF3
inspect LF4
inspect P8
```

按需取得细节。

不建立：

```text
TaxonomyView
ApproachView
ComparisonView
ConclusionView
```

## View 提供地图，inspect 提供下钻

V1 Read Side 只保留两个核心能力：

```text
view
inspect
```

`view` 回答：

> **当前 Research Run 整体是什么状态？**

`inspect` 回答：

> **某个明确 Domain Object 的完整当前状态是什么？**

例如：

```text
inspect(P8)

inspect(LF4)

inspect([AF2, LF4, IG7])
```

这种统一读取能力依赖 ADR-004 已经定义的 Stable Ref：

```text
P*
AF*
LF*
OP*
IG*
```

Stable Ref 因此同时承担：

```text
Persistent Identity
+
Context Navigation
```

## inspect 只读取有稳定身份的 Domain Object

`inspect` 不是任意 JSON Path 查询。

不支持：

```text
inspect("/landscape/findings/0")
inspect("/contract/requirements/2")
inspect("/anything")
```

它只接受具有稳定身份的领域对象，例如：

```text
Paper
ApproachFamily
LandscapeFinding
OpenProblem
InvestigationGap
```

嵌入式 Value Object：

```text
PaperAnalysis
PaperSource
LiteratureSource
SourceLocator
```

随父对象一起返回。

这样 Read Side 保持灵活，但不会暴露底层 JSON Schema 作为 Runtime Contract。

## Read Side 可以比 Write Side 更通用

ADR-005 明确拒绝任意 JSON Patch，因为通用写操作可能绕过 Domain Invariant。

ADR-006 则允许统一 `inspect`。

这种不对称是有意的：

```text
Read
────
view
inspect

Write
─────
PUT
MERGE
explicit Domain Command
```

原因是：

> **写操作可能破坏状态一致性，读取不会。**

因此：

> **写侧严格，读侧灵活。**

## View 和 inspect 复用 state_revision

ADR-005 已经定义：

```text
state_revision
```

ADR-006 不建立额外的：

```text
context_revision
view_revision
basis_revision
```

一次典型流程：

```text
ResearchRun
state_revision = 42
       │
       ▼
      view
       │
       ▼
Context
state_revision = 42
       │
       ▼
Claude reasoning
       │
       ├── inspect LF4
       │      expected_revision = 42
       │
       └── PUT / MERGE
              expected_revision = 42
```

如果当前 State 已经变成：

```text
state_revision = 43
```

则：

```text
inspect(... expected_revision=42)
```

和后续 Mutation 都必须 fail closed，例如返回：

```text
STALE_STATE
```

调用者重新执行 `view`。

这样一次语义判断不会混合：

```text
revision 42 的整体 View
+
revision 43 的对象细节
```

原则是：

> **一次语义判断应基于同一个 Research State revision。**

## Context 优先保留语义骨架

ADR-004 已经把论文级信息压缩为：

```text
Paper Analysis
```

又把跨论文理解压缩为：

```text
Literature Landscape
```

因此 Literature Landscape 本身就是高层语义地图。

Context Renderer 不应该再通过：

```text
importance score
relevance score
embedding similarity
```

决定哪些 Landscape Finding “更值得显示”。

Python 不知道：

> 哪个 Finding 对当前研究语义更重要。

因此：

> **高层语义骨架尽可能完整；昂贵细节按需下钻。**

优先完整保留：

```text
Research Requirements
Approach Families
Landscape Findings
Open Problems
Open Investigation Gaps
```

优先省略或分页：

```text
大量 Paper Index
完整 Paper Analysis
Source Locator 细节
Primary Paper 内容
```

## Context Budget 只约束成本，不判断重要性

Context 必须有界。

但 Context Budget 的职责仅仅是：

> **限制一次输出可以占用多少上下文资源。**

它不能决定：

> **什么知识在语义上重要。**

V1 不引入：

```text
semantic importance score
context relevance score
LLM-based context ranking
embedding-based State retrieval
```

基本顺序为：

```text
必要语义骨架
      ↓
当前请求的完整对象
      ↓
索引型 / 附加细节
      ↓
达到硬限制
      ↓
stop + explicit continuation
```

具体 token、字符、对象数量等限制属于配置，不由本 ADR 冻结。

原则继续遵守：

> **Hard limits use numbers; semantic quality uses criteria.**

## 截断只能发生在完整语义单元之间

Context Renderer 不从一个 Finding、Gap 或 Requirement 的中间截断字符串。

非法：

```text
LF21:
Current literature suggests verifier-integrated sea...
```

更合理的是：

```text
LF1 ...
...
LF20 ...

shown: 20 / 75
next_after: LF20
```

因此：

> **Context Budget 的最小截断单位是完整语义对象，而不是字符流。**

## 省略必须显式可见

Context 可以省略具体内容，但不能省略：

> **还有内容没有展示。**

例如：

```text
Papers
shown: 30
total: 120
next_after: P30
```

而不能只输出 30 篇论文后直接结束。

否则 Claude可能错误认为：

> 当前 Run 只有 30 篇论文。

因此：

> **可以省略内容，不能省略“内容存在”这一事实。**

## Pagination / Continuation 不持久化

V1 不维护：

```text
context_session
pagination_state
last_seen_paper
current_focus
checker_seen_pages
```

分页采用无状态 continuation。

概念上：

```text
state_revision = 42
section = papers
after = P30
```

即可继续读取下一批。

是否在具体 API 中表现为：

```text
after=P30
```

或 opaque continuation token 属于实现细节。

架构上要求只有：

```text
deterministic ordering
+
stateless continuation
```

Context consumption history 不属于 Research State。

## Completion Check 的高层语义骨架不能静默截断

Completion Check 的正确性依赖 Checker 对整体 Research Landscape 有基本认识。

因此以下高层信息应尽量完整进入 Completion Check View：

```text
all Research Requirements

all Approach Families
  id + compact canonical description

all Landscape Findings
  id + canonical statement + source relations

all Open Problems
  id + canonical statement

all open Investigation Gaps
  id + question
```

Paper Analysis、Source Locator 和 Primary Source Content 继续通过 `inspect / read_source` 下钻。

如果未来 Research Landscape 大到连这一份高层语义骨架都无法放入允许的 Completion Context：

> V1 应 fail closed 或要求显式分批检查，而不是静默删除部分 Landscape 后允许 PASS。

本 ADR 不提前设计复杂 Reviewer Coverage Tracking。

## Research View 可以包含最近一次 Completion Feedback

当：

```text
COMPLETION_CHECK
     ↓ CONTINUE / UNCERTAIN
RESEARCH
```

Researcher 必须知道 Checker 为什么要求继续。

最新 Completion Check 本身已经是 Persistent State，因此 Research View 可以确定性地包含：

```text
latest completion feedback
├── verdict
├── reasons
└── blocking gaps
```

这不是依赖 Event History。

它形成闭环：

```text
Research
   ↓
Completion Check
   ↓ CONTINUE
Research View
   ↓
see checker feedback
   ↓
continue Research
```

## Event History 默认不进入 Context

ADR-005 已经明确：

```text
state.json
=
authoritative state

events.jsonl
=
auxiliary audit / debug record
```

因此正常：

```text
Research View
Completion Check View
Delivery View
```

都不能依赖 Event History 才能生成。

即使：

```text
events.jsonl
```

完全不存在，当前 Research Process 仍应能够：

```text
Resume
Completion Check
Delivery
```

Event History 未来可以提供独立 Audit / Debug 查询能力，但不是 Context Renderer 的核心输入。

## Primary Paper 内容不属于 Context Projection

Context Renderer 读取 Research State。

论文全文、PDF、网页或 Provider Content 属于外部 Source。

因此：

```text
Context Renderer
≠
Paper Reader
≠
Search Provider
```

Renderer 可以告诉 Claude：

```text
LF4
sources:
P8 supports @ Table 2
```

如果 Claude要检查 Table 2 的真实内容：

```text
read_source(P8, Table 2)
```

由 Source Access / Provider 层处理。

这样保持：

```text
Research State
↓
Domain inspection
↓
Primary Source verification
```

三层边界清楚。

## Report 文本不是 Research State 的事实来源

Delivery 阶段生成的：

```text
report.md
```

可以作为后续写作时保持结构和语言一致性的 Writing Context。

但它不能替代：

```text
Literature Landscape
Literature Sources
Primary Papers
```

成为研究事实来源。

不能因为：

```text
上一章节已经写过 X
```

就在下一章节把 X 当作已验证研究事实。

因此：

> **Report 可以成为写作上下文，但不能成为 Research Context 的 authority。**

这一原则与未来 Wiki Projection 同样适用。

## 不引入新的基础设施复杂度

本 ADR 借鉴经典的：

```text
Projection
Read Model
CQRS read-side separation
Index → Drill-down
Snapshot Read
```

思想。

这些模式只用于明确：

```text
完整 State
≠
当前 View
```

以及：

```text
Write Model
≠
Read Representation
```

V1 明确不因此引入：

```text
Context Database
Read Database
Vector Database
Embedding Index
Semantic Ranker
Context Agent
Context Cache
Projection Worker
Message Bus
Eventual Consistency
Persistent Context Session
```

实现可以只是：

```text
加载 ResearchRun
↓
调用一个确定性 projection function
↓
返回 structured view
```

成熟模式的作用是减少自创复杂度，而不是增加基础设施层数。

## 概念接口

本 ADR 不冻结 CLI 或 Python 函数签名。

概念上 Read Side 只需要：

```text
view(run)
```

以及：

```text
inspect(
    run,
    refs,
    expected_revision
)
```

外部 Primary Source Access 独立为：

```text
read_source(...)
```

写侧继续使用 ADR-005：

```text
PUT
MERGE
Domain Command
```

因此整个 Runtime 的核心词汇可以保持很小：

```text
Research State
──────────────
view
inspect
put
merge
domain command

External Research I/O
─────────────────────
search
read
```

## 验证方式

后续实现至少应证明以下场景成立：

1. 删除 Claude Conversation 后，可以仅通过 `state.json + view` 恢复 Research Process。
2. `view` 根据当前 Lifecycle 自动选择正确 Projection，不需要调用者额外指定 purpose。
3. RESEARCH、COMPLETION_CHECK、DELIVERY 三种 View 的信息边界不同，但使用同一 authoritative ResearchRun。
4. Research View 不自动推荐下一个 Investigation Gap 或 Research Action。
5. Completion Check View 不默认暴露 Budget、Action History 或完整 Conversation。
6. Completion Checker 可以通过 `inspect` 检查已有 Finding、Paper 和 Source Grounding，而不扩张 Research State。
7. Delivery 可以通过 `inspect` 按章节读取所需对象，而无需创建章节专用 View。
8. `inspect(P8)` 返回当前持久化 Paper Domain Object，但不会自动加载整篇论文。
9. 基于旧 `state_revision` 的 `inspect` 会 fail closed，而不是混合两个 State revision。
10. Context Renderer 不调用 LLM 对 Paper Analysis 或 Landscape Finding 重新摘要。
11. 当 Paper Index 超过 Context Budget 时，Renderer 显式返回 `shown / total / continuation`。
12. Context 截断不会发生在 Finding、Gap、Requirement 等完整语义单元内部。
13. 删除 `events.jsonl` 后，三个核心 View 仍然可以正常生成。
14. 不存在持久化 Context Cache 时，View 仍可廉价从当前 State 重新构建。
15. Completion Check 所依据的 `CompletionCheck.basis_revision` 可以明确追溯到被冻结的 Research State。
16. 添加新的 Research Action 不要求增加新的 Context View 类型。
17. 新增普通 Domain Entity 时，只要拥有 Stable Ref，就可以复用统一 `inspect` 读取，而无需新增专用读取命令。

## 决策摘要

Research State 的读取模型最终保持为：

```text
                  ResearchRun
                      │
                      ▼
                     view
                      │
              current Lifecycle
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
 Research View   Completion View Delivery View
        │             │             │
        └─────────────┼─────────────┘
                      │
                 Stable Refs
                      │
                   inspect
                      │
                 Domain Object
                      │
                 Source Locator
                      │
                  read_source
                      │
                 Primary Paper
```

核心原则是：

> **State 是完整知识，Context 是当前用途下的有限投影。**

> **先给地图，再按稳定引用下钻。**

> **Claude 决定看哪里，Python 只负责确定性地把那里展示出来。**

> **Context 可以省略内容，但不能隐藏内容的存在。**

> **Context 复用 `state_revision`，不建立第二套版本、缓存或会话状态。**

> **Projection 只选择已有权威语义，不重新总结已有语义。**

> **成熟设计模式帮助我们保持结构简单，而不是成为引入新基础设施的理由。**
