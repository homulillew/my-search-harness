# 002 — 架构问题梳理

> 状态：Architecture Study
> 本文用于明确接下来必须做出的架构选择。
>
> 本文**不记录最终决策**，也不定义代码结构、数据模型或模块划分。
>
> 每个问题的目的都是：
>
> > 先明确我们究竟在选择什么，再决定应该采用哪种方案。

---

# 1. 为什么先整理架构问题

前面的设计原则和 Core Problem Model 已经回答了两个问题：

第一，我们希望构建怎样的系统：

> 一个面向 Claude Code 的论文调研 Harness，使研究过程可恢复、可验证、可控制、可积累。

第二，这个系统至少必须解决六类问题：

```text
Research Control
Research State
Evidence
Context
Completion
Knowledge
```

但这些仍然只是问题空间。

真正开始设计系统之前，我们必须进一步回答：

> **面对这些问题，我们具体有哪些选择？**

如果跳过这一层直接开始设计类、文件、CLI 或状态结构，很容易出现：

```text
先写代码
↓
代码隐含了某种架构
↓
为了保住已有实现
↓
反过来为架构找理由
```

因此这一阶段只做一件事：

> **把未来必须作出的架构选择显式化。**

---

# 2. 阅读本文的方式

每个架构问题都按照相同思路讨论：

```text
为什么必须决定？
↓
已经知道什么？
↓
有哪些合理方案？
↓
真正的取舍是什么？
↓
哪些事情现在故意不决定？
```

这里列出的方案不是完整穷举。

如果后续发现更简单、更符合约束的方案，可以增加。

Reference Study 提供的是证据，而不是选项菜单。

---

# 3. 问题一：谁拥有 Research Loop？

这是整个系统最上层的架构问题。

我们已经确定：

```text
Claude Code
=
Agent Runtime

Python Harness
=
Research Runtime
```

但这句话仍然没有完全回答：

> **Research Loop 到底由谁推进？**

例如一次研究过程中，Claude 可能决定：

```text
现在继续搜索
还是阅读已有论文？
是否追踪引用？
是否比较两个技术路线？
是否已经可以请求 Review？
```

这些是语义选择。

与此同时，系统还存在另一类决定：

```text
Budget 是否已经耗尽？
当前状态是否允许进入 Review？
某个 Evidence ID 是否存在？
当前 Run 是否已经结束？
```

这些是控制约束。

因此真正需要解决的是：

> **Claude 的语义决策权和 Python 的控制权在哪里分界？**

---

## 3.1 候选方案

### 方案 A：Python 驱动完整循环

形态类似：

```text
while not done:
    ask Claude what to do
    execute action
    update state
```

Python 拥有循环。

Claude 只是循环中的一个决策函数。

> 注：若此方案意味着 Python 维护完整循环、Claude 仅作为被调用的决策函数，则它已与既有边界冲突（Claude Code = Agent Runtime / Loop Driver）。保留在此仅用于对照理解边界；真正开放的是方案 C 中 Lifecycle State Machine 的薄厚。

### 方案 B：Claude Code 驱动完整循环

Claude 自己：

```text
读取状态
→ 判断
→ 调用 Harness Action
→ 再读取状态
→ 继续
```

Python 不主动调度研究流程。

### 方案 C：Claude 驱动研究，Python 驱动生命周期

Claude 决定：

```text
SEARCH
READ
ANALYZE
```

但 Python 决定：

```text
当前是否允许继续 RESEARCH
是否必须进入 REVIEW
是否允许进入 SYNTHESIZE
```

---

## 3.2 真正的取舍

核心不是：

> 谁写 `while`？

而是：

> **谁拥有 Semantic Policy，谁拥有 Control Authority？**

我们需要找到一个边界，使：

```text
Python 不成为第二个 Agent Runtime
```

同时又避免：

```text
Claude 可以随意绕过所有生命周期约束
```

---

## 3.3 当前已知约束

目前已经比较明确：

* Query 如何写属于 Claude；
* 读哪篇论文属于 Claude；
* Evidence 如何解释属于 Claude；
* ID、Budget、状态合法性属于 Python；
* Researcher 不能直接写 DONE；
* Python 不应该决定“哪条技术路线更重要”。

真正仍待决定的是：

> Python 是否应该维护一个最小 Lifecycle State Machine，以及这个 State Machine 到底有多薄。

---

## 3.4 暂不决定

这里暂时不决定：

* Python 模块名；
* Claude 如何调用 Harness；
* CLI 还是其它接口；
* 是否存在 `engine.py`；
* 具体 Phase Enum。

---

# 4. 问题二：最小 Research Lifecycle 是什么？

我们已经接受：

> Phase 描述生命周期，Action 描述工作。

但还没有真正决定生命周期本身。

当前长期使用的候选形态是：

```text
PLAN
 ↓
RESEARCH ↺
 ↓
REVIEW
 ↓
SYNTHESIZE
 ↓
DONE / PARTIAL
```

这很合理，但还只是 hypothesis。

---

## 4.1 为什么必须决定

Lifecycle 决定：

```text
哪些状态转换是合法的
哪些操作当前允许执行
谁有权改变哪个状态
什么时候触发 Review
什么时候可以生成最终交付
```

它也是 Python 最可能真正机械 enforce 的部分。

如果 Lifecycle 太复杂，就会重新走向旧 Harness 的 Phase Explosion。

如果太简单，又可能无法表达：

```text
研究尚未开始
正在研究
等待审查
已经完成但证据不足
```

这些真实差异。

---

## 4.2 需要比较的方案

### 方案 A：极简三阶段

```text
RESEARCH
↓
REVIEW
↓
DONE
```

PLAN 只是 Research Contract 创建动作。

SYNTHESIZE 只是完成后的生成动作。

### 方案 B：五阶段

```text
PLAN
RESEARCH
REVIEW
SYNTHESIZE
DONE / PARTIAL
```

生命周期明确表达整个 Research Run。

### 方案 C：只维护“控制状态”

不强调传统 Phase，而只记录：

```text
research_allowed
review_required
synthesis_allowed
terminal
```

生命周期由状态条件推导。

---

## 4.3 关键判断标准

最终 Lifecycle 应满足：

1. 能表达真实的控制差异；
2. 每一个 Phase 都拥有明确的 invariant；
3. 删除一个 Phase 后，如果没有任何约束丢失，就应该删除；
4. 新 Research Action 不应该要求增加新 Phase；
5. Phase 数量不能随着产品功能增长不断增加。

---

## 4.4 一个重要问题

需要特别确认：

> SYNTHESIZE 是 Lifecycle Phase，还是一种 Projection Action？

因为如果：

```text
Report
Wiki
```

都是 Accepted Evidence 的 Projection，

那么 SYNTHESIZE 也许不需要承担很多状态机职责。

这个问题必须在正式 Lifecycle ADR 前解决。

---

# 5. 问题三：Research Contract 应该固定什么？

开放式研究不能完全无约束开始。

否则研究过程中很容易发生：

```text
目标漂移
问题越研究越大
标准不断改变
完成条件事后定义
```

但另一方面，研究本身就是一个不断发现未知问题的过程。

如果一开始把整个 Contract 冻结，又会产生：

```text
Premature Ontology
```

也就是：

> 还没有真正理解领域，就假设自己已经知道应该研究哪些路线和问题。

---

## 5.1 需要解决的核心问题

Research Contract 中：

> **哪些东西必须稳定？**

以及：

> **哪些东西应该允许研究过程中演化？**

---

## 5.2 一个可能的两层模型

可以考虑区分：

### Stable Core

例如：

```text
Mission
Primary Research Questions
Scope
Critical Requirements
Budget
Evidence Expectations
Deliverable
```

这些定义：

> 为什么进行这次研究，以及成功至少意味着什么。

### Evolving Research Landscape

例如：

```text
Technical Routes
Sub-questions
Research Gaps
Contradictions
New Questions
```

这些是研究过程中逐渐发现的。

---

## 5.3 需要讨论的问题

例如：

* Primary Research Question 能不能修改？
* 新发现的重要子问题是否需要显式加入 Contract？
* Critical Criterion 能不能中途增加？
* 谁可以修改？
* 修改是否需要留下历史？
* Budget extension 是否属于 Contract amendment？
* Scope 扩展什么时候应该变成新的 Research Run？

---

## 5.4 一个重要边界

我们希望：

```text
Checkable
```

但不希望：

```text
Frozen
```

因此要避免误解：

> “研究开始前必须有可检查条件”

并不意味着：

> “研究开始前必须预知整个领域结构”。

---

# 6. 问题四：什么东西必须成为持久化 State？

这是 Domain Model 之前最重要的问题。

我们已经知道很多东西可能值得记录：

```text
Research Question
Gap
Query
Paper
Evidence
Criterion
Contradiction
Technical Route
Review Verdict
Budget
```

但：

> 值得记录，不等于必须成为一等 Entity。

---

## 6.1 为什么必须决定

如果所有概念都成为独立对象：

```text
复杂度会迅速膨胀
```

例如可能最终出现：

```text
ResearchQuestionStore
GapStore
QueryStore
PaperStore
EvidenceStore
RouteStore
CriterionStore
ReviewStore
...
```

系统会变得难以理解。

反过来，如果所有东西都塞进一个：

```text
state.json
```

又会导致：

```text
职责混乱
修改冲突
难以审计
难以局部读取
```

所以我们需要找到真正的状态边界。

---

## 6.2 判断某个概念是否是一等 State 的标准

可以问：

### 它是否需要稳定 ID？

如果别的对象需要引用它，通常需要。

### 它是否有独立生命周期？

例如 Paper：

```text
discovered
selected
read
rejected
```

如果生命周期明显，可能值得独立。

### 它是否需要跨 Action 复用？

Evidence 显然需要。

### 它是否需要独立审计或恢复？

如果需要，通常不应该只存在于自由文本。

### 删除它以后能否从其它状态重新计算？

如果完全可派生，也许应该只是 Projection。

---

## 6.3 当前尤其需要讨论的对象

重点不是一次解决所有 Entity。

优先讨论：

```text
ResearchRun
ResearchContract
Paper
Evidence
Gap
ReviewVerdict
```

因为它们决定最小 Research Loop 是否成立。

而：

```text
TechnicalRoute
Topic
WikiPage
CitationMap
```

可能可以后置。

---

# 7. 问题五：Paper 的状态应该怎么表达？

Paper 是系统里非常重要，但也非常容易过度建模的对象。

同一篇论文可能同时具有多个维度：

```text
已经发现
相关
值得深读
核心论文
已经阅读
证据不足
被排除
作为背景材料
```

如果只用一个：

```text
status
```

很容易出现：

```text
selected
```

和：

```text
read
```

到底哪个覆盖哪个的问题。

---

## 7.1 两种候选方向

### 单状态模型

例如：

```text
candidate
selected
read
accepted
rejected
```

简单，但多个维度被压成一条线。

### 多维状态模型

例如：

```text
discovery_state
reading_state
research_role
decision
```

语义更准确，但复杂度更高。

---

## 7.2 真正要解决的问题

不是设计最漂亮的 Paper Schema。

而是：

> **最小需要哪些状态，才能支持 SELECT_READ、避免重复阅读、解释为什么保留/拒绝一篇论文？**

只保留真正服务 Research Loop 的维度。

---

## 7.3 阅读深度与成本：Progressive Reading

前面的设计原则已经明确：不应默认把整篇论文全文塞进 Claude Context，而应按深度逐步深入。

但真正的问题还没有回答：

> **什么时候把阅读深度从摘要升级到全文？升级由谁决定？**

### 候选阅读梯度

```text
metadata
abstract
headings / 章节结构
相关 sections
exact evidence / 全文
```

### 需要回答

* 升级深度是语义判断（Claude 根据当前 Gap 决定需要多深）还是固定规则？
* 每个深度的 token 成本如何估算与约束？
* 已读深度是否需要进入 Paper 状态，以避免重复阅读？
* 深度选择是否应该对齐当前 Research Gap（缺什么信息就读多深）？
* 不同深度提取的 Evidence 之间，Locator 一致性如何保持？

### 暂不决定

不决定具体的 Reading Depth 枚举值，也不决定全文缓存的存储形式。

---

# 8. 问题六：什么才算 Evidence？

这是整个系统最关键的 Domain Question。

我们已经确认：

```text
Paper ≠ Evidence
```

但还没有决定 Evidence 的正式 Contract。

---

## 8.1 Evidence 最少要回答什么？

一个 Evidence 至少可能需要回答：

```text
来自哪篇论文？
来自哪里？
原文是什么？
它服务于哪个问题？
我们认为它说明什么？
它和 Claim 的关系是什么？
```

候选字段可能涉及：

```text
paper_id
locator
excerpt
claim
research_question / gap
stance
interpretation
```

但这些目前都只是候选。

---

## 8.2 最大的几个开放问题

### Excerpt 是否必须存在？

方案 A：

```text
必须保留 verbatim excerpt
```

优点：

* 可回查；
* semantic reviewer 更容易核验；
* citation drift 更低。

代价：

* 需要缓存或稳定访问原文；
* validator 更复杂；
* PDF parsing 差异可能导致匹配困难。

方案 B：

```text
只保存 locator + structured interpretation
```

更简单，但重新验证成本更高。

---

### Locator 需要多精确？

可能是：

```text
page
section
paragraph
text offset
semantic anchor
```

Locator 太弱：

> 回不到真实支撑位置。

Locator 太强：

> 文档重新解析或版本变化后很容易失效。

---

### Evidence 是“原文”，还是“解释”？

答案很可能是两者都需要，但必须分层。

例如：

```text
Source Evidence
+
Research Interpretation
```

但正式模型如何表达仍未决定。

---

### Evidence 什么时候成为 Accepted？

可能存在：

```text
candidate evidence
accepted evidence
refuted evidence
excluded evidence
```

但是否真的需要完整 lifecycle？

或者：

> 只有 Accepted Evidence 才进入持久 Evidence Store，其它只留 action/event history？

需要比较。

---

# 9. 问题七：Evidence 与 Claim / Criterion 的关系是什么？

即使 Evidence 定义清楚，还存在一个更高层的问题：

```text
Evidence
≠
Completion
```

一条 Evidence 到底支持什么？

可能是：

```text
Evidence → Claim
```

也可能：

```text
Evidence → Research Criterion
```

或者：

```text
Evidence → Claim → Criterion
```

---

## 9.1 为什么这个问题重要

如果 Evidence 直接绑定 Criterion：

```text
模型简单
```

但一个 Criterion 往往是：

> “这一技术路线已经有足够代表论文和失败边界。”

这不是一条 Evidence 能表达的。

如果引入完整 Claim Layer：

```text
Evidence
↓
Claim
↓
Criterion
```

语义更漂亮，但会多出一个重要 Domain Object。

---

## 9.2 需要回答

* Claim 是否需要一等 ID？
* Report Claim 和 Research Claim 是否是同一个概念？
* 一条 Evidence 能支持多个 Claim 吗？
* 一个 Claim 是否需要多条 Evidence？
* Criterion 的 coverage 是从 Claim 推导还是直接 Review？
* Contradiction 发生在 Evidence、Claim 还是 Analysis 层？

这是 Evidence Architecture 的核心选择之一。

---

# 10. 问题八：Research Gap 是什么？

我们强调 Gap-Driven Research。

但如果 Gap 定义得太随意：

```text
“还可以再多看一些”
```

它就没有真正控制价值。

如果定义得过于结构化，又会增加不必要的 bookkeeping。

---

## 10.1 Gap 至少应该表达什么？

一个 Gap 可能至少需要：

```text
还有什么不知道？
为什么重要？
它属于哪个 Research Question？
目前有什么 Evidence？
下一步调查可能是什么？
```

但不一定全部都要成为字段。

---

## 10.2 Gap 与 Query 的关系

我们已经比较明确：

```text
Gap
→ provides rationale

Claude
→ writes actual query
```

Python 可以要求：

```text
一个新 Query 必须能够说明自己服务于哪个 Gap
```

但不应该：

```text
自动把 Gap 模板化成搜索词
```

---

## 10.3 Gap 什么时候关闭？

不能简单：

```text
搜到 Paper
→ gap closed
```

也不能：

```text
有 Evidence
→ gap closed
```

可能需要 Review 判断：

```text
covered
partial
missing
```

因此 Gap 本身可能是：

> Research State

而 closure 是：

> Semantic Judgment。

---

# 11. 问题九：Context Renderer 的 Contract 是什么？

Persistent State 解决“记得住”。

Context Renderer 解决：

> **Claude 当前应该看到什么？**

这两者同样重要。

---

## 11.1 一个 Renderer 还是多个 View？

候选方向一：

```text
render_context(action_type)
```

统一 Renderer，根据 Action 类型选择内容。

候选方向二：

```text
plan_search_view
select_read_view
analyze_evidence_view
review_view
synthesis_view
```

每种 View 独立定义。

---

## 11.2 当前候选语义检查点

至少需要研究：

```text
PLAN_SEARCH
SELECT_READ
ANALYZE_EVIDENCE
REVIEW
SYNTHESIZE
```

是否真的需要不同的 Context。

注意：

这些名字未必是 Runtime Actions。

它们更可能是：

> **Semantic Decision Points。**

这一点需要在后续设计中特别保持。

---

## 11.3 Context 如何缩小？

可能依据：

```text
current gap
current paper
related evidence
recent queries
critical unresolved items
```

而不是简单：

```text
last N records
```

因此 Context Selection 本身具有部分语义。

需要决定：

> 哪些选择可以 deterministic，哪些必须依赖 Claude？

---

# 12. 问题十：如何控制 Context Budget？

仅说：

> bounded context

还不够。

必须决定：

```text
bound 什么？
```

可能包括：

```text
字符数
token 数
Evidence 数量
Paper 数量
Gap 数量
```

---

## 12.1 两种风险

太严格：

```text
关键 Evidence 被裁掉
```

太宽松：

```text
Context Renderer 失去意义
```

所以真正的问题不是：

> token limit 用多少？

而是：

> **哪些信息无论如何不能因为 Context Budget 被静默丢弃？**

例如：

```text
critical gaps
blocking contradictions
review failures
```

可能应该拥有优先级。

具体策略后续再决定。

---

# 13. 问题十一：什么时候允许请求 Review？

Researcher 不能直接 DONE。

但它必须有某个时刻说：

```text
ready_for_review
```

什么时候允许？

---

## 13.1 候选触发条件

可能包括：

```text
researcher believes criteria are covered
budget near exhaustion
low marginal gain
all current gaps resolved
explicit user request
```

这些条件的性质不同。

例如：

```text
budget exhausted
```

是 mechanical trigger。

而：

```text
I believe the field is sufficiently covered
```

是 semantic judgment。

---

## 13.2 一个可能的重要原则

Researcher 不需要“证明完成”才能请求 Review。

否则：

> Review 本身就失去价值。

更合理的是：

```text
Researcher:
I believe this may be sufficient.

Reviewer:
Let's test that claim.
```

因此：

> `ready_for_review` 可能是一个 request，而不是 pass candidate。

---

# 14. 问题十二：Review 到底审什么？

Review 如果只是：

```text
“你觉得研究够了吗？”
```

很容易重新变成 self-grading 的变体。

因此必须定义 Review Contract。

---

## 14.1 Review 可能需要看到

```text
Research Contract
Critical Criteria
Coverage
Accepted Evidence
Contradictions
Open Gaps
Budget
Researcher completion rationale
```

但不应该看到整个 Conversation。

---

## 14.2 Review 需要判断的层次

至少有两个不同问题：

### Evidence Validity

```text
证据真的支持对应解释吗？
```

### Research Sufficiency

```text
整个研究是否已经足够回答任务？
```

这两个判断不要混为一个模糊：

```text
quality
```

---

## 14.3 是否 default-fail？

spec-kit-loop 强调 reviewer：

> 先尝试让 criterion 失败。

这是很强的 anti-self-grading 机制。

但我们需要决定：

> 文献调研是否也应该采用 adversarial review posture？

还是采用更中性的：

```text
evidence-based independent assessment
```

这仍是开放选择。

---

# 15. 问题十三：Review Verdict 应该是什么？

当前常用候选：

```text
PASS
CONTINUE
UNCERTAIN
PARTIAL
```

但每个词必须有严格含义。

---

## 15.1 需要定义的边界

### PASS

意味着：

> 当前 Contract 的关键条件已经满足，可以进入交付。

### CONTINUE

意味着：

> 存在明确、可行动的 Research Gap，并且继续研究有意义。

### UNCERTAIN

可能意味着：

> Reviewer 无法可靠判断，而不是简单“50% 完成”。

例如：

```text
source unavailable
evidence ambiguous
contract unclear
```

### PARTIAL

更可能是终态：

> 研究没有完全满足 Contract，但受 Budget / Source Availability 等限制，需要诚实交付当前结果。

---

## 15.2 最重要的问题

需要明确：

```text
UNCERTAIN
```

到底是：

> Review Verdict

还是：

> 一个需要用户介入的 Control State？

同样：

```text
PARTIAL
```

是 Review Outcome 还是 Terminal State？

正式设计前必须厘清。

---

# 16. 问题十四：Budget 与 Completion 如何组合？

Budget 与 Completion 已经明确是两个不同维度。

但真实状态组合仍需设计。

例如：

```text
Reviewer = CONTINUE
Budget > 0
→ return to RESEARCH
```

很自然。

但：

```text
Reviewer = CONTINUE
Budget = 0
```

怎么办？

---

## 16.1 候选处理

### 方案 A

自动进入：

```text
PARTIAL
```

### 方案 B

进入：

```text
BLOCKED_NEEDS_BUDGET
```

由用户决定是否扩展。

### 方案 C

ReviewVerdict 仍然是 CONTINUE，

但 Control Plane 决定：

```text
cannot continue
```

最终 Delivery 标记为 partial。

第三种语义可能最干净，因为它保持：

```text
Semantic Verdict
≠
Resource State
```

但需要正式比较。

---

# 17. 问题十五：什么是“长期知识”？

一次 Run 完成以后，并不是所有状态都值得进入 Wiki。

例如：

```text
某次 Query 为什么换了关键词
某次搜索 API 超时
Claude 曾经考虑过某个方向但没继续
```

这些可能适合保留在 Run State / Event Log。

而：

```text
Paper A 的核心方法
Route B 的失败边界
Topic C 的主要矛盾
```

更适合作为长期知识。

---

## 17.1 一个候选边界

可以考虑：

```text
Evidence-backed conclusion
→ long-term knowledge candidate

Process-level deliberation
→ run-local state
```

也就是说 Wiki 保存：

> 我们学到了什么。

而不是：

> 我们每一步是怎么想到的。

---

## 17.2 需要进一步讨论

* Failed Route 是否进入 Wiki？
* Open Gap 是否进入 Wiki？
* Negative Result 是否进入 Wiki？
* Reviewer unresolved 是否进入 Wiki？
* 某篇 Paper 被 Reject 的原因是否跨 Run 有价值？

这些都需要结合未来检索价值判断。

---

# 18. 问题十六：Wiki 是怎样的 Projection？

目前比较强的方向是：

```text
Accepted Evidence
↓
Projection
↓
Wiki
```

但：

> Projection 本身是什么意思？

还没有决定。

---

## 18.1 方案 A：完全确定性渲染

结构化 Evidence：

```text
→ 固定模板
→ Markdown
```

优点：

* 可重建；
* 无 summary drift；
* 容易测试。

缺点：

* 可读性可能较差；
* 跨论文综合能力有限。

---

## 18.2 方案 B：LLM 从 Evidence 重新生成

每次都：

```text
Accepted Evidence
→ LLM synthesis
→ fresh page
```

不读旧 Wiki 文本。

优点：

* 可读；
* 能做语义综合。

缺点：

* 同样 Evidence 可能生成不同文本；
* 需要额外 semantic validation。

---

## 18.3 方案 C：结构确定、文字语义生成

例如：

```text
Page identity / Evidence membership
→ deterministic

Narrative
→ Claude generated from current evidence only
```

这可能兼顾两者。

但复杂度是否值得，需要验证。

---

# 19. 问题十七：Wiki 的知识单位是什么？

当前常见候选：

```text
Paper
Route
Topic
```

但暂时不能把它们冻结。

真正需要回答：

> **未来 Research Run 会以什么粒度复用知识？**

如果未来最常问的是：

```text
某篇论文讲了什么？
```

Paper View 很有价值。

如果最常问：

```text
这个方向有哪些技术路线？
```

Route 更重要。

如果需要：

```text
这个领域还有什么 unresolved？
```

Topic View 更自然。

因此 taxonomy 应该从：

```text
future reuse pattern
```

推出来，而不是从美观的知识分类推出来。

---

# 20. 问题十八：如何保持跨 Run Identity？

Paper 的身份通常比较容易：

```text
DOI
arXiv ID
canonical URL
```

但：

```text
Technical Route
Topic
Research Question
```

没有天然 ID。

例如：

```text
Verifier-guided search
Verifier-assisted search
Search with external verifier
```

可能是同一个 Route，也可能不是。

---

## 20.1 这是一个真正困难的问题

如果 identity 不稳定：

```text
Wiki 会产生重复页
长期知识无法合并
历史 citation 失效
```

如果过度自动 canonicalize：

```text
不同概念可能被错误合并
```

因此至少要决定：

```text
哪些对象需要 stable identity
哪些 identity 可以人工/Claude 管理
哪些 identity 必须 deterministic
```

这个问题很可能应该后于 V1 Research Loop 本身。

---

# 21. 问题十九：Report 和 Wiki 是否共享 Synthesis？

Report 与 Wiki 都来自 Accepted Evidence。

所以自然会出现：

```text
是否应该共享一套 synthesis layer？
```

方案一：

```text
Evidence
├→ Report Generator
└→ Wiki Generator
```

完全独立。

方案二：

```text
Evidence
↓
Shared Analysis / Knowledge Representation
├→ Report
└→ Wiki
```

方案三：

```text
Wiki
→ Report
```

第三种目前风险最大，因为它容易让 Wiki 变成事实源。

---

## 21.1 需要守住的原则

无论共享多少：

```text
Report
```

和：

```text
Wiki
```

都必须最终可回到：

```text
Accepted Evidence
```

不能出现：

```text
Wiki prose
→ Report claim
```

却无法解释具体证据来源。

---

# 22. 问题二十：哪些可靠性机制值得进入 V1？

旧 Harness 已经证明以下问题是真实存在的：

```text
process crash
partial write
duplicate process
provider failure
state corruption
```

因此一些工程机制值得认真考虑：

```text
atomic write
single-writer lock
append-only events
checkpoint
fail-closed provider validation
```

但我们也已经见过过度设计：

```text
version everything
hash everything
audit everything
```

---

## 22.1 需要找到最小可靠性集合

判断标准应该是：

> 如果去掉它，是否会破坏一个明确的系统 invariant？

例如：

### Atomic Write

如果没有：

> crash 可能留下半个 JSON。

这是明确问题。

### Event Log

如果没有：

> 是否真的无法 resume / debug？

可能值得，但需要证明。

### Hash Chain

如果没有：

> 有什么具体风险？

目前看不明显。

所以不应该进入 V1。

---

# 23. 问题二十一：Provider 应该提供什么 Contract？

Provider 是 Research Runtime 与外部世界的边界。

最危险的错误之一是：

```text
request failed
```

被解释成：

```text
no results
```

因此 Provider 不能只返回：

```text
papers[]
```

还需要表达：

```text
success
empty
partial
rate limited
unavailable
error
```

---

## 23.1 另一个边界：内容是不可信数据

论文 PDF、网页、metadata、README 等内容都属于：

```text
untrusted external content
```

即使其中出现：

```text
ignore previous instructions
run command X
```

也只能作为论文内容处理。

不能成为 Harness 指令。

---

## 23.2 暂不决定

当前不决定：

* 第一版支持几个 Provider；
* DeepXiv 是否唯一 Provider；
* Provider Interface 的 Python 形式；
* 是否实现 fallback chain。

这里只确认：

> Provider failure semantics 和 trust boundary 是正式架构问题。

---

# 24. 哪些问题应该优先决策

上述问题不是同一优先级。

如果目标是尽快得到一个最小、正确的 V1 架构，建议分三层。

---

## 第一层：先决定 Control Skeleton

这些决定其它所有东西怎么挂上去：

```text
1. 谁拥有 Research Loop？
2. 最小 Lifecycle 是什么？
3. Research Contract 固定什么？
4. 谁有权请求 / 写 Review 和 Completion？
```

---

## 第二层：决定 Research State

这些构成 Harness 的领域核心：

```text
5. 什么 State 必须持久化？
6. Paper 如何表达？
7. 什么是 Evidence？
8. Evidence / Claim / Criterion 如何关联？
9. Gap 如何表达？
```

---

## 第三层：决定 Views 与 Delivery

这些建立在前两层之上：

```text
10. Context Renderer 如何工作？
11. Review Contract 是什么？
12. Wiki 如何 Projection？
13. Report 与 Wiki 如何共享 Evidence？
```

---

# 25. 建议的 ADR 顺序

如果这些问题讨论清楚，正式 ADR 不需要很多。

第一批大概只需要覆盖真正改变系统形状的决策。

建议候选顺序：

```text
ADR-001
Agent Runtime 与 Research Runtime 的职责边界

ADR-002
Research Lifecycle 与 Action 的关系

ADR-003
Persistent State 与 Context Projection

ADR-004
Paper / Evidence 边界与 Evidence Authority

ADR-005
Researcher / Reviewer / Completion Authority

ADR-006
Budget 与 Semantic Completion 的关系

ADR-007
Wiki / Report 作为 Evidence Projection
```

这只是：

> **ADR candidate map**

不是已经批准的七条决策。

如果几个问题最后可以合并成一个更简单的 ADR，应当合并。

---

# 26. 下一阶段的讨论方式

接下来不应该一次性把二十多个问题全部回答完。

更合适的方式是从最上层开始：

```text
Loop Ownership
↓
Lifecycle
↓
Research Contract
```

因为如果这三件事都没有确定，

那么讨论：

```text
Evidence JSON 长什么样
```

仍然太早。

---

# 27. 第一组需要正式回答的问题

因此下一轮 Architecture Study 建议只聚焦三个问题：

## A. Loop Ownership

> Claude 和 Python 分别拥有什么控制权？

## B. Minimal Lifecycle

> Research Run 最少需要哪些生命周期状态？

## C. Research Contract

> 哪些目标和约束必须稳定，哪些研究内容允许演化？

如果这三件事得到一致答案，

我们就会第一次拥有一个真正稳定的：

> **Control Skeleton**

之后再进入 State / Evidence Design。

---

# 28. 本阶段完成标准

这份文档的完成不意味着架构已经确定。

它的完成标准只是：

> **我们已经知道有哪些重要问题必须主动做选择，而不是让代码替我们偷偷选择。**

正式设计从下一步才开始。

下一步应该从：

```text
Loop Ownership
```

开始，对候选方案进行：

```text
Problem
↓
Constraints
↓
Alternatives
↓
Reference Evidence
↓
Trade-offs
↓
Decision
```

然后产生第一条真正的 Architecture Decision。
