# ADR-011：通过候选论文闭合将 Deep Reading 接入 Research Loop

* **状态**：拟议
* **阶段**：Domain Model / Research Loop
* **日期**：2026-08-11
* **影响范围**：Paper、Paper Analysis、Research Loop、Candidate Selection、Completion Check、Context Projection
* **关联决策**：

  * ADR-001 — Claude Code 驱动研究循环，Python Harness 守住系统不变量
  * ADR-003 — Research Contract 定义 Research Run 的语义边界
  * ADR-004 — 持久化论文级理解与领域级理解
  * ADR-005 — Research State 通过类型化变更在 ResearchRun 边界内原子更新
  * ADR-006 — Research State 通过用途化投影渲染为有界 Context
  * ADR-008 — 论文通过按需 Source Access 支持渐进式阅读

## 背景

ADR-004 已经确定：

```text
Paper-level Understanding
        ↓
Field-level Understanding

Paper Analysis
        ↓
Literature Landscape
```

ADR-008 进一步确定，论文阅读通过按需 `Source Access` 完成，不建立固定的 Reading Lifecycle 或 `reading_depth`。

现有设计已经能较好回答：

> **当 Researcher 已经决定研究一篇论文后，应该如何读取它，并如何把阅读结果持久化为 Paper Analysis。**

但真实运行暴露了另一个问题：

> **Researcher 为什么选择这些论文进入深读，以及为什么其它已经发现的重要论文可以不再研究。**

一次实际 KV Cache 调研中，搜索阶段发现了数十篇高度相关论文，但最终只有约十篇进入深度分析。最终的 Approach Families、Findings 和 Completion Check 都围绕这组已分析论文形成。

这种结果本身不一定有问题。

广泛搜索后只深读少数代表论文，可以是合理的研究策略。

问题在于，从 Search Observation 到最终研究语料之间缺少 durable boundary：

```text
Search Results
      ↓
Claude selects some papers
      ↓
Retained / Analyzed Papers
      ↓
Literature Landscape
      ↓
Completion Check
```

如果某篇已经被发现的论文没有进入持久 Research State，它会随着 Search Observation 离开 Context。

Completion Checker 随后只能判断：

> **当前已经分析的论文是否足以支持已有 Landscape。**

它无法判断：

> **是否存在 Researcher 已经发现、且仍可能改变重要结论的论文，却在进入 Completion 前无声消失。**

这使 Research Loop 在论文阅读处容易退化成：

```text
broad search
→ implicit representative-paper selection
→ fixed reading batch
→ synthesis
→ completion
```

而不是：

```text
current uncertainty
→ select candidate
→ read
→ update State
→ reassess
→ change next action
↺
```

本 ADR 需要确定：

> **如何让重要候选论文在 Search、Deep Reading、State Reassessment 和 Completion 之间形成可恢复的闭环，同时避免建立新的 Reading Workflow、论文数量阈值或候选评分系统。**

---

## 决策

V1 使用现有 `Paper` 作为 durable candidate boundary。

Search Result 继续保持 ephemeral Observation。

只有当 Researcher 判断：

> **如果现在忘掉这篇论文，它仍有合理可能改变当前 Research Contract 下的重要研究判断。**

该候选才通过 `RetainPapers` 进入持久 Research State。

进入 State 后，Paper 必须形成明确的研究 disposition：

```text
SearchHit
   │
   │ material enough to preserve
   ▼
 Paper
   │
   ├── ACTIVE + no Paper Analysis
   │       unresolved candidate
   │
   ├── ACTIVE + Paper Analysis
   │       integrated research paper
   │
   └── RETIRED + retirement reason
           explicitly closed candidate
```

因此：

> **SearchHit 是发现结果；Retained Paper 是 Research Run 已决定不能无声遗忘的研究候选。**

所有进入这个 durable boundary 的候选，在 Completion 前必须已经被研究整合，或者具有明确的退出理由。

这形成：

```text
Discover
→ Promote material candidates
→ Read against current uncertainty
→ Integrate or explicitly retire
→ Reassess State
→ Choose next action
→ Close retained candidate frontier
→ Completion Check
```

---

## SearchHit 继续是 ephemeral Observation

Paper Search Provider 返回的 `PaperSearchHit` 不进入 Research State。

SearchHit 的职责仍然是：

```text
discovery
triage
query refinement
candidate identification
```

Researcher 可以从一个 Search Result 中看到几十甚至上百篇论文，而只 Retain 其中少数。

V1 不要求持久化：

```text
all search hits
rejected search hits
screening decisions
search candidate queue
```

明显重复、明显越界、低相关或无法影响当前研究判断的结果可以直接离开 Context。

因此本 ADR 不改变 ADR-007 / ADR-008 已建立的：

```text
SearchHit
→ Claude selection
→ RetainPapers
→ Paper
```

边界。

它进一步定义 `Retain` 的语义：

> **Retain 表示该候选已经具有足够的当前研究决策价值，需要一个 durable disposition。**

它不表示论文已经被认可，也不表示论文一定会进入最终报告。

---

## Candidate Promotion 由 Researcher 负责

候选论文是否值得 Retain 是语义研究判断。

Python Harness 不计算：

```text
candidate_score
relevance_score
reading_priority
materiality_probability
```

也不根据论文数量、citation count 或 provider score 自动晋升候选。

Researcher 根据当前 Research Contract、Landscape 和 Investigation Gaps 判断候选是否具有 material value。

典型情况包括：

* 可能解决当前 Investigation Gap；
* 可能形成新的主要技术路线；
* 是某项重要 mechanism claim 所需的 Primary Source；
* 可能挑战、限制或修正当前 Landscape Finding；
* 提供重要 negative result 或 conflicting evidence；
* 覆盖当前缺失的模型、Benchmark、硬件或 Deployment Condition；
* 对 latest / recent / SOTA 任务具有实质 frontier 价值；
* 可能改变当前代表论文选择；
* 可能改变路线间的 trade-off 判断。

判断问题可以概括为：

> **如果这个候选现在从 Context 消失，它是否仍可能造成 contract-facing research loss？**

如果答案为是，应 Retain。

如果答案明显为否，可以继续保持 ephemeral。

---

## ACTIVE Paper 表示仍在当前研究中

`PaperResearchStatus.ACTIVE` 表示：

> **这篇论文仍属于当前 Research Run 的有效研究工作集。**

它不表示当前必须立即读取，也不表示已经深读完成。

结合 `PaperAnalysis` 可以得到两种重要状态。

### ACTIVE + `analysis = None`

表示：

> **这篇论文已经跨过 materiality boundary，但当前还没有形成可供 Research State 使用的 paper-level understanding。**

它是一个 durable unresolved candidate。

这组 Paper 可以从现有 State 动态推导为：

```text
Reading Frontier
=
ACTIVE Papers
where PaperAnalysis is absent
```

`Reading Frontier` 是 Context / Reasoning 层的派生概念。

V1 不建立独立：

```text
ReadingFrontier
ReadingQueue
ReadingTask
```

Domain Entity。

### ACTIVE + Paper Analysis

表示：

> **当前 Run 已经形成了这篇论文的 paper-level understanding，并且它仍属于当前有效研究 corpus。**

这类 Paper 可以参与 Literature Landscape。

---

## Paper Analysis 不表示永久完成阅读

ADR-008 已经确定，阅读深度取决于当前研究问题。

因此：

```text
analysis != None
```

不等价于：

```text
READ_COMPLETE
```

Paper Analysis 表示：

> **当前 Research Run 已经整合的论文级理解。**

之后如果新的 Finding、Contradiction 或 Investigation Gap 需要重新核验这篇论文，Researcher 可以再次：

```text
inspect_source
→ read_source
→ update Paper Analysis
```

同一篇论文可以在不同研究迭代中被多次针对性读取。

V1 不新增：

```text
UNREAD
SCANNED
PARTIALLY_READ
DEEP_READ
READ_COMPLETE
```

等 Reading State。

也不新增：

```text
reading_depth
sections_read
reading_progress
```

字段。

阅读深度继续属于 Researcher 的语义判断。

---

## RETIRED 表示候选已经显式闭合

`PaperResearchStatus.RETIRED` 表示：

> **这篇论文曾经值得进入当前 Research Run，但现在已经不需要继续占据当前研究工作集。**

RETIRED Paper 必须保存：

```text
retirement_reason
```

它记录的是当前 durable semantic decision，例如：

```text
superseded by a later full version already retained
```

```text
mechanistically redundant with stronger primary evidence
already integrated in this run
```

```text
after source inspection, the paper falls outside the
final Research Contract boundary
```

或者：

```text
source access remains unavailable, but no current
contract-facing conclusion depends on this paper
```

`retirement_reason` 不记录完整筛选轨迹，也不保存优先级历史。

它只回答：

> **为什么当前 Run 可以停止继续研究这篇已经被 Retain 的论文？**

因此 Paper 使用：

```text
ACTIVE
→ retirement_reason = None

RETIRED
→ retirement_reason = non-empty
```

重新激活 Paper 时清除旧 `retirement_reason`。

Action / Event History 继续记录状态变化本身，不在 Research State 中复制完整时间线。

---

## Retired Paper 不能继续承担当前 Landscape Evidence

Literature Landscape 表示当前接受的领域级研究理解。

因此它只能依赖：

```text
ACTIVE
+
PaperAnalysis exists
```

的 Paper。

以下情况必须由 Runtime 拒绝：

```text
ACTIVE + analysis=None
→ ApproachFamily representative paper
```

```text
ACTIVE + analysis=None
→ Finding / OpenProblem LiteratureSource
```

以及：

```text
RETIRED Paper
→ current Landscape evidence
```

同样，一个已经被当前：

```text
ApproachFamily
LandscapeFinding
OpenProblem
```

引用的 Paper 不能直接被 RETIRED。

Researcher 必须先重新处理相应语义对象：

```text
update / replace / retire affected Landscape object
↓
remove current dependency
↓
retire Paper
```

Python 不自动删除或重写这些引用，因为：

> **取消一篇论文的研究资格可能改变当前领域判断，这属于语义研究决策。**

Harness 只负责拒绝结构上矛盾的状态。

---

## Deep Reading 是 Research Loop 内部 Action

论文阅读不建立新的 Phase。

Researcher 每轮从当前 Research State 开始：

```text
Research State N
        ↓
Current Uncertainty
        ↓
Candidate Frontier / Discovery
        ↓
Select highest-value paper or small coherent wave
        ↓
Primary Source Access
        ↓
Paper Analysis / Landscape / Gap mutation
        ↓
Research State N+1
        ↓
Reassessment
        ↓
Next Action
```

下一篇论文应由更新后的 State 决定。

Researcher 不应因为之前形成了一份 Reading List，就在 State 已发生变化后继续机械执行该列表。

因此 Deep Reading Loop 的关键性质是：

```text
Paper read
↓
State changes
↓
Researcher reassesses
↓
next action may change
```

如果阅读结果没有反馈到下一次研究决策，那么即使论文读取数量很多，整体行为仍然只是：

```text
Search Pipeline
→ Reading Pipeline
→ Synthesis Pipeline
```

而不是 ADR-001 所要求的 adaptive Research Loop。

---

## Reading Wave 可以批量，但不定义完成阈值

Researcher 可以为了执行效率，在同一个明确 uncertainty 下选择一个小型 coherent reading wave：

```text
State N
↓
Paper A
Paper B
Paper C
↓
integrate
↓
State N+1
↓
reassess
```

V1 不冻结 batch size。

Reading Wave 的数量只属于：

```text
execution cost
context management
parallelism
```

不属于 semantic sufficiency。

如果某篇论文在 wave 中产生了足以改变当前研究方向的重要 contradiction，Researcher 可以提前回到 State reassessment。

系统不要求完成之前计划的整个 reading batch。

---

## Completion 要求 retained candidate frontier 结构上闭合

Researcher 请求 Completion 时，Runtime 增加一个确定性约束：

```text
ACTIVE Paper
+
analysis is absent
→
request_completion rejected
```

原因是 Research State 自己仍然声明：

```text
Paper is ACTIVE
```

同时又没有形成最低限度的 paper-level understanding。

这是结构不一致，而不是论文数量不足。

Python 不判断：

```text
10 papers enough?
20 papers enough?
30% of search results enough?
```

Python 只判断：

> **是否仍存在 State 自己声明为 active、却尚未形成 Paper Analysis 的 durable candidate。**

语义上的“研究是否已经足够”仍由 Researcher 与 fresh Completion Checker 根据 Research Contract 判断。

因此：

```text
Candidate Closure
≠
Semantic Completion
```

Candidate Closure 是 Completion 的必要结构条件之一。

它不是充分条件。

---

## Completion Checker 必须能够看到 retained candidate closure

Completion Checker 不能只看到最终被选作 Approach representative 的论文。

Completion Context 必须能够观察当前 Run 中所有 Retained Papers 的候选状态，至少包括：

```text
Paper identity
Research Status
has_analysis
retirement_reason
```

Detailed Paper Analysis 仍然通过 stable ref 按需 inspect。

这样 Completion Checker 可以判断：

* 当前是否所有 ACTIVE Papers 都具有分析；
* 当前 Landscape 是否只依赖 ACTIVE + analyzed Papers；
* frontier-sensitive Candidate 是否被过早 RETIRE；
* 潜在 contradiction 是否具有可信的 retirement reason；
* Researcher 是否通过批量 RETIRE 候选来绕过进一步研究。

Completion Checker 不重新审查所有 Search Results。

它只审查已经跨过 durable materiality boundary 的 Retained Papers。

对于 RETIRED Papers，也不要求逐篇重新研究。

Checker 根据风险优先检查：

* 最新论文；
* 可能形成新路线的论文；
* 可能挑战当前 Finding 的论文；
* 与 Contract 高度直接相关的论文；
* retirement reason 明显过弱的论文。

Completion Check 继续是独立完成判断，不成为第二个日常 Research Loop。

---

## Candidate Closure 不等于保存所有筛选历史

V1 不要求回答：

> **搜索阶段出现的每一篇论文后来发生了什么？**

它只要求回答：

> **Researcher 已经明确认为重要到需要进入 Research State 的论文后来发生了什么？**

边界为：

```text
SearchHit
     │
     ├── immaterial
     │      ↓
     │   ephemeral
     │
     └── material
            ↓
          Paper
            ↓
     durable disposition required
```

这样可以防止 Search Result 无限制膨胀 Research State，也避免建立筛选数据库。

---

## Resume 恢复 Candidate Frontier，而不是 Reading Plan

新的 Claude Session 恢复 Research Run 时，只需要从 Research State 看到：

```text
A ACTIVE + analysis
B ACTIVE + no analysis
C RETIRED + retirement_reason
D ACTIVE + no analysis
```

即可推导：

```text
Current unresolved candidates:
B
D
```

然后结合当前：

```text
Research Contract
Literature Landscape
Investigation Gaps
```

重新决定 B 或 D 哪个更值得研究。

系统不保存：

```text
old reading list
old reading priority
candidate score
planned next paper
subagent task graph
```

因此仍然满足 ADR-001：

> **Resume 恢复 Research Process，不恢复 Conversation。**

---

## Deep Reading Subagent 不成为新的 Architecture Role

论文深读未来可以使用多个临时 Subagent 并行执行。

这属于 execution optimization。

推荐边界为：

```text
Main Researcher
    ↓
select coherent reading wave
    ↓
parallel Reader Subagents
    ↓
disposable reading notes
    ↓
Main Researcher integrates
    ↓
Harness persists Research State
```

原则为：

> **Subagents read. Main Researcher integrates. Harness persists.**

Subagent 不直接拥有独立 Research State，也不形成第二套长期知识库。

临时阅读笔记可以写入 Run 对应的 disposable scratch area。

删除所有 Subagent scratch notes 后，Research Run 必须仍然可以仅依赖持久 Research State 恢复。

V1 不为并行阅读新增：

```text
Reader Agent Entity
Reading Task Entity
Parallel Source Runtime
Source Lease
Reader Coordinator
```

只有真实运行证明 Source Access 并发已经成为瓶颈时，再单独设计执行层优化。

---

## 不采用的方案

### 固定最低深读论文数

例如：

```text
at least 20 papers
```

可以阻止极端少读，但无法说明这些论文是否覆盖真正重要的机制、冲突和 frontier。

它也会把开放式研究压缩成机械 workload threshold。

不采用。

### 使用 Search / Deep-read 比例

例如：

```text
deep_read_ratio >= 30%
```

Search Result 数量高度依赖 Query 粒度、Provider 行为和领域规模。

大量高度重复结果可能只需要少数代表论文，较小的结果集也可能遗漏关键方向。

比例不表达 semantic sufficiency。

不采用。

### Candidate Score / Sufficiency Score

可以统一排序，但会把多维研究判断压成 scalar，并诱导 Python 逐渐承担 Research Policy。

不采用。

### 建立 ReadingTask / ReadingQueue

可以显式保存每篇论文的待办状态，但 `ACTIVE + analysis=None` 已经能够表达 durable unresolved candidate。

额外 Entity 会复制已有事实，并逐渐引入 queue lifecycle、priority、retry 和 synchronization。

不采用。

### 建立 Reading State Machine

例如：

```text
UNREAD
→ SCANNED
→ TARGETED_READ
→ DEEP_READ
→ COMPLETE
```

论文阅读深度取决于当前 uncertainty，不具有稳定线性阶段。

ADR-008 已经明确将 Progressive Reading 定义为按需 Source Access。

不采用。

### 持久化全部 SearchHit 与 rejection reason

可以让 Completion 获得完整搜索轨迹，但会把 Research State 转化成 Candidate Screening Database，并增加大量低价值持久状态。

不采用。

### Completion Checker 重新搜索整个领域

可以独立验证 Search Recall，但会使 Completion Checker 成为第二个 Researcher，并破坏 Completion Authority 与 Research Authority 的边界。

不采用。

---

## 后果

这一决策使 Retained Paper 获得更清楚的 Run-local 语义：

```text
SearchHit
=
ephemeral discovery observation

ACTIVE + no analysis
=
durable unresolved candidate

ACTIVE + analysis
=
integrated research paper

RETIRED + retirement_reason
=
explicitly closed candidate
```

它带来的主要收益是：

1. 已经被认为具有实质研究价值的 candidate 不会在 Search Context 消失后无声退出。
2. Deep Reading 能够自然进入 `State → Action → Evidence → State` 的 Research Loop。
3. Resume 可以恢复 unresolved candidate frontier，而不需要保存 Claude 的旧 Reading Plan。
4. Completion Checker 可以判断 retained candidate closure，而不仅检查最终少量代表论文。
5. 系统不需要规定最低论文数量或阅读比例。
6. Paper Analysis、Literature Landscape 和 Investigation Gap 的既有职责保持不变。
7. Progressive Source Access 继续保持按需、非线性。
8. Python 只增加少量可机械验证的不变量，不承担候选优先级和阅读充分性的语义判断。

代价是：

1. 一旦 Researcher 将候选 Retain，就需要最终分析或明确 RETIRE；
2. RETIRED Paper 需要额外保存一个 semantic reason；
3. Completion Context 需要比过去看到更完整的 Paper 工作集；
4. Paper Status 与 Landscape 引用之间需要更严格的一致性验证。

这些成本被接受，因为它们直接对应跨 Session 连续性和 Completion 可验证性，而没有引入新的 Research Workflow。

---

## 暂不决定

本 ADR 不冻结：

* Candidate Promotion 的 Prompt 文案；
* Reading Wave 的默认大小；
* Reading Frontier 是否在 Context 中拥有单独 derived field；
* Subagent 的具体启动接口；
* Subagent reading note 的精确 Markdown Schema；
* 并行 Source Access；
* Candidate priority ranking；
* Completion Checker 对 RETIRED Papers 的具体抽样数量；
* 单篇 Paper Analysis 的最终字段扩展。

这些属于 Skill Protocol、Context Design 或后续执行优化。

---

## 验证方式

后续实现至少应能够验证以下场景。

### Candidate 不会无声消失

一个已经被 Researcher 判断为 material 并 Retain 的论文，在 Completion 前必须处于：

```text
ACTIVE + PaperAnalysis
```

或：

```text
RETIRED + retirement_reason
```

不能保持：

```text
ACTIVE + analysis=None
```

并成功请求 Completion。

### Landscape 只依赖有效 Paper

以下状态必须被 Runtime 拒绝：

```text
unanalyzed Paper
→ representative paper
```

```text
unanalyzed Paper
→ Finding / OpenProblem source
```

```text
RETIRED Paper
→ current Landscape source
```

### Paper retirement 不破坏 Landscape

仍被 ApproachFamily、Finding 或 OpenProblem 引用的 Paper 不能直接 RETIRE。

Researcher 必须先完成相应 semantic mutation。

### Resume 不依赖旧 Reading Plan

Session 结束后，新 Claude Context 只通过 Research State 就能识别：

```text
ACTIVE + analysis=None
```

的 unresolved candidates，并重新决定下一步。

### Deep Reading 真正反馈到下一次决策

E2E 轨迹应能够观察：

```text
current uncertainty
→ read candidate
→ Paper Analysis / Landscape changes
→ reassess State
→ next research action changes
```

如果真实运行仍然表现为：

```text
search broad batch
→ retain fixed batch
→ read fixed batch
→ synthesize once
```

则说明本 ADR 的目标尚未真正实现，即使所有新字段和 Runtime validation 都已经存在。

### Completion 能看到 candidate closure

Completion Checker 应能观察：

```text
all retained Papers
+
status
+
has_analysis
+
retirement_reason
```

并能够按 stable ref 对高风险 candidate 下钻核验。

它不需要重新获得全部历史 Search Hits。

---

## 决策摘要

Deep Reading 的完整性不通过论文数量保证。

Researcher 可以搜索很多论文，也可以最终只深入研究其中较少的一部分。

系统要求的是：一篇论文一旦被判断为重要到需要进入 Research State，就不能再无声消失。

它必须保持为当前研究中的有效论文，形成 Paper Analysis；或者由 Researcher 明确说明为什么当前 Run 可以停止继续研究它。

因此：

```text
SearchHit
→ optional promotion
→ Retained Paper
→ analyze or retire
→ State reassessment
→ candidate closure
→ Completion
```

Python Harness 负责保证 retained candidate frontier 在结构上闭合。

Claude Code 继续负责判断哪些候选重要、哪篇最值得先读、需要读多深，以及整个研究在语义上是否已经足以请求 Completion。

> **Retain 决定哪些候选不能被遗忘；Deep Reading 改变 Research State；Candidate Closure 让 Completion 能够判断为什么研究可以停在这里。**
