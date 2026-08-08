# Project Vision — Claude Code Literature Research Harness

## 1. 项目定位

本项目旨在构建一个面向 **Claude Code** 的论文调研 Harness。

它不是一个通用聊天机器人，也不是一个追求复杂 Multi-Agent 编排的 Deep Research Framework，更不是一个由 Python 自己实现完整 Agent Runtime、不断调用 Claude API 的通用 Agent 系统。

它的目标是：

> 将 Claude Code 的开放式论文调研过程工程化为一个可恢复、可验证、可迭代、可积累的 Research Loop。

用户给出一个论文调研主题或研究问题后，Claude Code 作为 Research Agent，通过持续的：

```text
分析
→ Query 改写
→ 搜索
→ 论文筛选
→ 阅读
→ 证据分析
→ Research Gap 分析
→ Query 再改写
→ 再搜索
→ ...
```

逐步建立对一个技术领域的结构化理解。

Python Harness 不负责替代 Claude Code 做语义研究决策。

Python Harness 负责提供：

* 持久化 Research State；
* 可恢复状态；
* Search / Read 等确定性 Action；
* Budget；
* Deduplication；
* Schema Validation；
* Evidence Integrity；
* State Transition；
* Resume；
* Review Gate 的机械约束。

因此，本项目的核心执行关系是：

```text
Claude Code
Agent Runtime / Loop Driver
        │
        │ semantic decision
        ▼
Python Harness Action Interface
        │
        │ deterministic execution
        ▼
Persistent Research State
        │
        │ bounded state rendering
        └──────────────────→ Claude Code
```

而不是：

```text
Python while-loop
        ↓
call Claude API
        ↓
parse model response
        ↓
execute
        ↓
call Claude API again
```

这一点是本项目最重要的架构边界之一。

---

# 2. 最终产物

调研完成后，系统应产生两类长期资产：

```text
Accepted Research Evidence
        │
        ├──→ Local LLM Wiki
        │
        └──→ Domain Survey Report
```

其中：

* **Local LLM Wiki** 用于跨调研任务积累长期知识；
* **Survey Report** 用于交付当前领域调研结果；
* 二者都应建立在可追溯 Evidence 上；
* 二者都不应依赖 Claude 对历史对话的记忆作为事实来源。

---

# 3. 我们真正要解决的问题

本项目的重点不是：

> 让 Claude 搜索更多论文。

而是解决长程论文调研过程中几个反复出现的工程问题。

---

# 3.1 Context Drift

传统 Agent Search 往往把以下信息都留在模型上下文中：

* 已经搜索过哪些 Query；
* 已发现哪些论文；
* 哪些论文已经读过；
* 哪些论文被排除；
* 当前识别出了哪些技术路线；
* 哪些结论已有证据；
* 哪些结论存在冲突；
* 还有哪些 Research Gap；
* 当前为什么继续搜索。

随着研究轮数增加，上下文会越来越长。

容易出现：

* 重复搜索；
* 遗忘早期发现；
* 证据与结论脱节；
* Research Gap 丢失；
* 后期决策质量下降；
* Session 结束后无法继续。

因此本项目希望做到：

> Conversation 可以丢失，但 Research State 不能丢失。

Claude Code 的一次 Session 只是当前工作的临时上下文。

真正长期存在的研究状态必须保存在 Harness 管理的持久化数据中。

---

# 3.2 LLM 同时承担 Reasoning 和 Bookkeeping

LLM 擅长：

* 理解研究问题；
* 判断论文相关性；
* 分析论文内容；
* 比较技术路线；
* 发现研究缺口；
* 解释矛盾；
* 综合复杂证据。

但 LLM 并不适合可靠承担：

* ID 管理；
* Query 去重；
* Budget 计数；
* 文件一致性；
* Cache；
* Retry；
* Schema 校验；
* Evidence 引用完整性；
* 状态持久化；
* Atomic Write。

因此本项目明确区分：

```text
Claude Code
    ↓
Semantic Policy / Judgment

Python Harness
    ↓
Deterministic Mechanism / Control
```

Claude 决定：

> 下一步做什么最有研究价值？

Harness 负责：

> 这件事怎样被可靠执行、记录和约束？

---

# 3.3 Research Agent 容易过早宣布完成

一个 Research Agent 如果同时负责：

```text
做研究
+
判断自己的研究是否已经充分
```

就存在明显的 Self-Grading 问题。

模型很容易因为：

* 当前上下文已经看起来完整；
* 最近搜索结果开始重复；
* 已经生成了结构良好的回答；
* 当前证据恰好支持已有假设；

而提前停止。

因此：

> Researcher 不应该拥有最终 DONE 权限。

Researcher 只能认为：

```text
ready_for_review
```

研究是否真正可以结束，应由：

```text
Research Contract
+
Persistent Research State
+
Independent Review Gate
```

共同决定。

---

# 3.4 一次调研完成后知识不会积累

传统研究工作流通常是：

```text
Research
→ Report
→ End
```

下一次相关调研又重新：

```text
Search
→ Read
→ Understand
```

造成大量重复工作。

本项目希望引入本地 LLM Wiki：

```text
Research Run
    ↓
Accepted Evidence
    ↓
Local Wiki
    ↓
Future Research
```

让一次研究产生的：

* 技术路线；
* 代表论文；
* 重要结论；
* 争议；
* 失败模式；
* Open Questions；

成为未来任务可以继续利用的知识资产。

---

# 3.5 报告容易产生 Citation Drift

常见的错误流程是：

```text
模型形成理解
→ 写报告
→ 最后补 Citation
```

容易产生：

* 引文并不真正支持 Claim；
* 论文被二次总结后语义漂移；
* 找不到 Claim 对应的原文位置；
* 同一 Citation 被过度泛化使用。

因此本项目坚持：

> Evidence First, Synthesis Second.

报告应由已有 Evidence State 驱动，而不是由模型对搜索过程的模糊记忆驱动。

---

# 4. 核心工作流

项目希望保留 Agent Search 最自然的研究方式：

```text
Analyze
   ↓
Rewrite Query
   ↓
Search
   ↓
Screen Papers
   ↓
Read
   ↓
Analyze Evidence
   ↓
Update Understanding
   ↓
Identify Research Gaps
   ↓
Rewrite Query
   ↓
Search Again
```

这个循环是系统的核心。

我们不希望通过大量人为固定 Pipeline Stage 限制研究行为。

相反：

> Research Loop 应该简单，Research State 应该丰富。

---

# 5. 核心执行模型

这是本项目必须长期保持清晰的架构边界。

## 5.1 Claude Code 是 Agent Runtime

Claude Code 负责驱动外层 Research Loop。

Claude Code 会：

* 读取当前 Research State 的 bounded slice；
* 判断当前最重要的研究问题；
* 改写 Query；
* 决定搜索方向；
* 判断候选论文是否值得深入；
* 决定应该阅读哪些 Section；
* 解释 Evidence；
* 识别新的 Research Gap；
* 请求进入 Review；
* 综合最终报告。

因此：

> Claude Code owns semantic orchestration.

---

## 5.2 Python Harness 不是第二套 Agent Runtime

V1 不实现类似下面的逻辑：

```python
while not done:
    response = call_claude_api(...)
    action = parse(response)
    execute(action)
```

Python Harness 不负责：

* 管理完整 Claude Conversation；
* 自己实现 Agent Tool Loop；
* 自己维护 LLM Prompt Lifecycle；
* 自己调度 Claude API；
* 自己复制 Claude Code 已有的 Agent Runtime。

### 为什么

如果这样设计，会产生：

```text
Claude Code Runtime
        +
Custom Python Agent Runtime
        +
Research Harness
```

形成两层 Agent Runtime。

这会增加：

* Prompt 生命周期；
* Tool Dispatch；
* Context 管理；
* Model Retry；
* Streaming；
* API Compatibility；
* Agent Lifecycle；
* Debug 成本。

而这些不是当前产品真正要解决的问题。

---

# 5.3 Python Harness 是 Research Runtime

Python Harness 负责提供稳定的 Research Runtime。

例如：

```text
search
read
persist
validate
deduplicate
update-state
render-context
request-review
resume
```

Claude Code 决定调用哪个 Action。

Harness 决定：

* 这个 Action 是否合法；
* Budget 是否允许；
* 数据如何规范化；
* 状态如何更新；
* Evidence 是否有效；
* 文件如何可靠写入；
* 重试如何执行；
* Session 重启后如何恢复。

---

# 5.4 Loop Driver 与 Control Authority 必须区分

Claude Code 是：

> Loop Driver

但不拥有全部：

> Control Authority。

例如 Claude 判断：

```text
我需要继续搜索。
```

Harness 可以拒绝：

```text
budget exhausted
```

Claude 判断：

```text
Research ready for review.
```

Harness 可以检查：

```text
current state does not satisfy review prerequisites
```

Claude 试图：

```text
DONE
```

Harness 应拒绝：

```text
Researcher is not allowed to declare DONE.
```

因此：

> Claude drives the loop, but does not own the rules of the loop.

---

# 6. 核心设计哲学

本项目采用以下总体设计哲学：

> **Simple loop. Rich state. Hard evidence. Criteria over magic scores.**

中文含义：

> **循环简单，状态丰富，证据刚性，用可检查条件代替魔法分数。**

后续设计如果与这些原则发生冲突，应优先重新审视设计。

---

# 7. Design Principle 1 — Simple Loop

Research Loop 本身应该保持简单。

我们不希望把：

```text
search
read
compare
verify
follow citation
extract
reflect
```

每一种行为都设计成独立生命周期 Phase。

应该明确：

> Phase 描述生命周期，Action 描述工作。

例如：

```text
PLAN
RESEARCH
REVIEW
SYNTHESIZE
DONE
```

可以是生命周期。

而：

```text
SEARCH
READ
FOLLOW_REFERENCE
EXTRACT_EVIDENCE
COMPARE
```

只是 Research 阶段中的 Action。

### 为什么

如果每增加一种能力就增加一个 Phase：

```text
Feature Count ↑
→ State Machine Complexity ↑
```

系统最终会产生 Phase Explosion。

新版必须避免这个问题。

---

# 8. Principle 2 — Rich Externalized State

Research State 不应依赖 Claude 当前对话上下文保存。

系统应该能够显式记录：

* Research Questions；
* Query History；
* Candidate Papers；
* Core Papers；
* Evidence；
* Technical Routes；
* Research Gaps；
* Contradictions；
* Budget；
* Current Lifecycle State。

Claude 每次工作时只读取当前 Action 所需要的 State Slice。

### 为什么

长期研究真正需要持久化的是：

> State

而不是：

> Conversation。

---

# 9. Principle 3 — Resume Restores Research, Not Conversation

当 Claude Code Session 结束：

```text
Claude Context
    X
```

系统不应该尝试恢复模型的完整思维过程。

新的 Session 应通过：

```text
new Claude Code session
        ↓
Harness status / next
        ↓
load persistent Research State
        ↓
render bounded state slice
        ↓
Claude continues
```

继续研究。

因此：

> Resume 恢复的是 Research Process，而不是 Conversation History。

这是本项目最核心的工程能力之一。

---

# 10. Principle 4 — Claude Owns Semantic Judgment

Claude Code 负责无法可靠通过固定规则完成的工作。

包括：

* 研究问题理解；
* Query Rewrite；
* 论文相关性判断；
* Section 阅读选择；
* Evidence Interpretation；
* Technical Route 判断；
* Contradiction 分析；
* Research Gap 识别；
* Report Synthesis。

### 为什么

这些任务需要真正的语义理解。

不应该为了“确定性”而强行用脆弱的启发式规则代替模型判断。

---

# 11. Principle 5 — Harness Owns Deterministic Bookkeeping

Python Harness 负责：

* API 调用；
* Retry / Timeout；
* Cache；
* Paper ID；
* Deduplication；
* Budget；
* State Transition；
* Persistence；
* Schema Validation；
* Evidence Reference Validation；
* Resume；
* Events。

### 为什么

这些工作是确定性的。

如果交给 LLM：

* 更贵；
* 更慢；
* 更难测试；
* 更容易漏步骤；
* 更难保证一致性。

基本原则：

> Semantic decision belongs to Claude.
> Mechanical correctness belongs to the Harness.

---

# 12. Principle 6 — Policy / Mechanism Separation

本项目可以使用 Policy / Mechanism 的方式理解核心边界。

Claude 是：

```text
Policy
```

负责：

> 下一步做什么？

Python Harness 是：

```text
Mechanism
```

负责：

> 这件事如何可靠执行？

例如：

```text
Claude:
Search verifier-guided stopping because G003 remains open.

Harness:
- validate G003 exists
- check budget
- deduplicate query
- call provider
- retry timeout
- normalize results
- assign IDs
- persist results
- update event log
```

这种分离是整个系统保持可解释和可测试的重要基础。

---

# 13. Principle 7 — Research Must Be Gap-Driven

下一轮搜索不应该来自：

> “我感觉还可以再搜一些。”

而应该来自明确的 Research Gap。

例如：

```text
G003:
缺少 verifier-based stopping 在 2026 年工作的证据

        ↓

Query:
"verifier guided search stopping agent 2026"
```

每条 Query 应尽量能够解释：

```text
为什么搜索？
它试图解决哪个 Gap？
结果解决了吗？
```

### 为什么

Gap-driven Research 可以显著减少：

* 泛化搜索；
* 重复搜索；
* 无目的探索；
* Research Loop 无法收敛的问题。

---

# 14. Principle 8 — Paper Is Not Evidence

发现一篇论文并不等于拥有可以支持结论的 Evidence。

需要明确区分：

```text
Paper Candidate
      ↓
Paper Selection
      ↓
Paper Reading
      ↓
Evidence Extraction
```

论文级相关性回答：

> 这篇论文值得读吗？

Evidence 级相关性回答：

> 这篇论文的哪一部分能支持、反驳或限定当前 Claim？

### 为什么

如果把“相关论文”直接当成“证据”，最终报告很容易出现弱引用或错误引用。

---

# 15. Principle 9 — Progressive Reading

默认不应该把整篇论文全部塞进 Claude Context。

应优先按照：

```text
Title
↓
Abstract
↓
Section Structure
↓
Relevant Sections
↓
Exact Evidence
```

逐步深入。

### 为什么

这样可以：

* 降低 Token 成本；
* 减少 Context Noise；
* 提高 Citation Locator 精度；
* 让阅读行为和当前 Research Gap 对齐。

---

# 16. Principle 10 — Evidence Must Be Traceable

重要 Research Claim 必须能够追溯：

```text
Claim
 ↓
Evidence
 ↓
Paper
 ↓
Section / Locator
```

Evidence 不应只是：

```text
"Paper X supports this."
```

而应尽量包含：

* Paper ID；
* Section；
* Locator；
* Excerpt；
* Stance。

Stance 至少需要区分：

```text
supporting
contradicting
qualifying
```

### 为什么

领域调研真正可信的基础不是：

> 模型写得像论文。

而是：

> 结论可以回到原始论文检查。

---

# 17. Principle 11 — Researcher Cannot Self-Declare DONE

Research Agent 可以输出：

```text
ready_for_review
```

但不应该自己输出最终：

```text
DONE
```

完成应该经过独立 Review Gate。

Review 应尽量使用 Fresh Context，只读取：

* Research Contract；
* Research Questions；
* Technical Routes；
* Evidence；
* Research Gaps；
* Contradictions。

而不是沿用 Researcher 的完整 reasoning history。

### 为什么

这可以降低：

* Self-Grading；
* Confirmation Bias；
* Premature Stopping。

---

# 18. Principle 12 — Fresh Review Is a Semantic Checkpoint, Not Another Agent Runtime

V1 可以使用新的 Claude Code Context、Subagent 或独立 Review Session 来完成 Review。

但这里的重点不是构建一个复杂的：

```text
Reviewer Agent Service
```

而是保证：

> Reviewer 不继承 Researcher 的完整自我论证过程。

Review 的目的只是独立判断：

```text
PASS
CONTINUE
UNCERTAIN
```

如果需要继续，应返回：

```text
critical gaps
```

并写回 Research State。

---

# 19. Principle 13 — Numbers Bound Resources, Criteria Judge Quality

数字适合约束：

* 最大 Research Cycle；
* Search Call 数量；
* 最大读取论文数；
* Top-K；
* Context Token；
* Retry 次数。

例如：

```text
max_cycles = 4
max_search_calls = 20
max_papers_read = 15
```

这些参数代表明确的资源约束。

但研究质量不应轻易使用：

```text
sufficiency_score >= 0.75
```

这种单一魔法分数决定。

### 为什么

如果没有人工标注数据进行 Calibration：

* 0.75 缺少客观依据；
* 不同质量维度会错误互相补偿；
* Critical Gap 可能被其他高分掩盖；
* 数字制造虚假的精确感。

因此质量判断优先使用：

```text
covered
partial
missing

supported
contradicted
unknown

pass
continue
uncertain
```

等 Typed Criteria。

基本原则：

> **Numbers bound the loop; evidence closes the loop.**

---

# 20. Principle 14 — Critical Criteria Are Non-Compensatory

重要条件不能通过其他条件表现良好来抵消。

例如：

```text
RQ1 covered
RQ2 covered
RQ3 missing
Optional items all covered
```

如果 RQ3 是 Critical：

> Research 仍然不应该 PASS。

### 为什么

论文调研中一些遗漏是结构性的。

它们不应该被平均分掩盖。

---

# 21. Principle 15 — LLM Wiki Is Knowledge Accumulation, Not Truth

本地 LLM Wiki 用于保存长期有价值的知识：

* Paper；
* Technical Route；
* Topic；
* Important Findings；
* Contradictions；
* Open Questions。

但 Wiki 不是 Evidence Source of Truth。

Wiki 中的内容可以帮助下一次研究：

* 找到已有技术路线；
* 找到代表论文；
* 发现历史争议；
* 生成更好的 Query。

但正式 Claim 仍应回到：

```text
Evidence
→ Paper
→ Locator
```

验证。

原则：

> Wiki helps decide what to investigate.
> Papers decide what we are allowed to claim.

---

# 22. Principle 16 — Wiki and Report Are Projections

Wiki 和最终报告都应该从 Accepted Evidence 生成。

正确关系：

```text
             Accepted Evidence
                   │
          ┌────────┴────────┐
          ↓                 ↓
       Local Wiki       Survey Report
```

不推荐：

```text
Evidence
→ Wiki
→ Report
```

也不推荐：

```text
Evidence
→ Report
→ Wiki
```

### 为什么

二次总结再生成最终结论容易造成：

> Summary-of-summary drift。

Evidence Store 应保持为共同 Source of Truth。

---

# 23. Principle 17 — Wiki Should Be Rebuildable

Wiki 是 Derived State。

理想情况下：

```text
delete wiki
↓
rebuild from accepted evidence
```

仍然能够得到一致的知识库。

### 为什么

如果 Wiki 成为唯一事实源：

* 内容损坏难以恢复；
* 错误会长期累积；
* Evidence 与知识页面可能发生漂移。

因此 Wiki 应是可再生成的知识投影。

---

# 24. Principle 18 — Prefer Plain Files Before Infrastructure

V1 优先使用：

* JSON；
* JSONL；
* Markdown；
* Local Filesystem。

除非明确证明必要，否则不引入：

* PostgreSQL；
* Redis；
* Neo4j；
* Vector Database；
* Message Queue。

### 为什么

本项目当前核心难点是：

> Research Process Engineering

不是：

> Distributed Systems Engineering。

额外基础设施会增加：

* 环境配置；
* Debug 成本；
* 状态一致性问题；
* 部署负担；
* Vibe Coding 复杂度。

---

# 25. Principle 19 — Avoid Framework Complexity Without Evidence

V1 不因为：

> Agent 项目通常这么做。

就引入：

* LangGraph；
* Pydantic AI；
* Generic Agent Framework；
* Workflow Engine；
* Multi-Agent Framework。

Claude Code 本身已经是我们的 Agent Execution Environment。

### 为什么

额外 Agent Framework 会产生第二层 Runtime。

可能形成：

```text
Claude Code
↓
Agent Framework
↓
Harness
↓
Research Workflow
```

如果它没有解决明确问题，只会增加抽象层。

---

# 26. Principle 20 — One Researcher, One Independent Reviewer First

V1 不采用复杂 Agent Swarm。

优先采用：

```text
Claude Code Researcher
        ↓
Fresh-context Claude Reviewer
```

必要的 deterministic work 交给 Python。

### 为什么

多 Agent 会显著增加：

* Context Routing；
* State Ownership；
* Cost；
* Failure Modes；
* Observability 难度；
* Debug 难度。

在单 Researcher + Reviewer 尚未证明不足前，不增加更多角色。

---

# 27. Principle 21 — Context Is a View of State

Persistent Research State 可以越来越丰富。

但 Claude 当前看到的 Context 不应该无限增长。

因此需要明确：

```text
Persistent State
      ↓
Context Renderer
      ↓
Action-specific State Slice
      ↓
Claude Code
```

例如：

搜索决策可能只需要：

```text
Research Contract
Open Critical Gaps
Recent Queries
Relevant Routes
Recent Evidence
```

Evidence Analysis 可能只需要：

```text
Current RQ
Selected Paper Sections
Related Evidence
Known Contradictions
```

### 为什么

Externalized State 如果最终还是全部塞回 Context，就失去了意义。

---

# 28. Principle 22 — Harness Should Expose State, Not Hide It

未来 Harness 的接口应该帮助 Claude 和开发者清楚回答：

```text
当前 Phase 是什么？
当前 Research Gap 是什么？
为什么继续？
已经使用多少 Budget？
哪些 Action 合法？
哪些 Evidence 已接受？
```

因此未来可能存在类似：

```text
status
next
```

的接口。

这里的 `next` 主要作用不是：

> Python 替 Claude 决定下一步语义动作。

而是：

> 从 Persistent State 渲染当前工作环境、约束和合法 Action。

Claude Code 仍然负责 Semantic Choice。

---

# 29. Principle 23 — Complexity Must Earn Its Place

任何新模块、依赖、状态或 Pipeline Step 都必须回答：

```text
它解决什么真实问题？
如果删除它，会损失什么能力？
是否已有更简单方式解决？
```

如果无法明确回答：

> 不进入 Core。

项目不以功能数量衡量工程质量。

---

# 30. Non-Goals

V1 明确不以以下内容作为核心目标。

---

## 30.1 不做通用 Deep Research Platform

系统优先服务：

> 技术 / AI 论文领域调研。

不追求同时覆盖：

* 财经研究；
* 新闻调查；
* 法律研究；
* Web Intelligence；
* 企业知识搜索。

---

## 30.2 不做 Python Agent Runtime

V1 不自行实现：

```text
LLM conversation manager
tool calling runtime
model loop
Claude API orchestration
generic agent executor
```

Claude Code 已经承担 Agent Runtime 职责。

---

## 30.3 不做 Multi-Agent Swarm

暂时不实现：

```text
Planner Agent
Searcher Agent
Reader Agent
Verifier Agent
Writer Agent
Manager Agent
```

除非未来 Evaluation 明确证明单 Researcher 架构不够。

---

## 30.4 不做 Graph Database

论文之间可以存在 Citation / Lineage 关系。

但 V1 不因此引入 Neo4j。

需要的关系优先使用普通数据结构表达。

---

## 30.5 不做复杂 Citation Graph Runtime

Follow Citation / Follow Reference 可以成为一种 Search Action。

但暂时不把 Citation Graph 设计成独立生命周期系统。

---

## 30.6 不做 Scalar Research Quality Score

不使用未经 Calibration 的：

```text
quality_score
sufficiency_score
confidence_total
```

作为核心完成判据。

---

## 30.7 不做无限 Report Revision Loop

报告阶段优先：

```text
Draft
↓
Review
↓
One targeted revision
↓
Done / Partial
```

不设计复杂多态 Report State Machine。

---

## 30.8 不做自动执行第三方论文仓库

即使论文附带 GitHub 项目，V1 也不默认：

* Clone；
* Install；
* Execute；
* Run arbitrary code。

项目代码分析可以以后作为独立能力讨论。

---

## 30.9 不做自我修改 Harness

Loop Engineering 在本项目中首先用于：

> 设计 Research Loop。

不是让 Harness 自动修改自己的 Prompt、代码或策略。

自改进可以以后通过离线 Evaluation 讨论。

---

## 30.10 不为未来 Web Service 提前设计 Runtime

未来如果需要：

```text
background research jobs
API service
scheduled research
multi-user system
```

可以再抽象 Agent Adapter 或 Service Layer。

V1 不为了这些未来可能性提前承担复杂度。

---

# 31. 产品成功标准

项目成功不意味着：

> 支持最多 Agent。

也不意味着：

> Pipeline 最复杂。

V1 成功应该表现为以下能力。

---

## 31.1 Research Quality

能够围绕 Research Question：

* 找到主要技术路线；
* 找到代表论文；
* 提取可定位 Evidence；
* 识别关键矛盾；
* 明确尚未回答的问题；
* 生成结构化领域综述。

---

## 31.2 Traceability

重要结论能够追溯：

```text
Report Claim
→ Evidence
→ Paper
→ Section
```

---

## 31.3 Recoverability

Claude Code Session 终止后：

```text
new session
→ load state
→ render current context
→ continue
```

不需要依赖旧对话。

---

## 31.4 Bounded Autonomy

Research Loop 存在明确：

* Goal；
* Budget；
* Done Criteria；
* Review Gate。

不会无限运行。

---

## 31.5 Knowledge Accumulation

一次 Research Run 的 Accepted Knowledge 能进入 Local Wiki。

后续相关研究能够利用已有知识，而不是完全从零开始。

---

## 31.6 Explainability

系统应该能够回答：

```text
为什么搜索这个 Query？
为什么读这篇 Paper？
这个 Claim 的 Evidence 在哪里？
为什么继续搜索？
为什么请求 Review？
为什么最终停止？
```

---

## 31.7 Engineering Quality

至少应具备：

* Schema Validation；
* Retry / Timeout；
* Deterministic Deduplication；
* Atomic State Persistence；
* Resume；
* Tests；
* Offline Fixtures；
* Clear Error Handling；
* Partial Completion。

---

# 32. 最终系统心智模型

未来实现应始终能够被理解为：

```text
                User Research Question
                         ↓
                  Research Contract
                         ↓
                 Persistent State
                         │
                         │ bounded rendering
                         ▼
                    Claude Code
               Agent / Loop Driver
                         │
                  semantic decision
                         ▼
              Harness Action Interface
                         │
              deterministic execution
                         ▼
                 Persistent State
                         │
                         └──────────────→ Claude Code
```

研究过程：

```text
PLAN
 ↓
RESEARCH
 ↺
 ↓
REVIEW
 ├─ CONTINUE → RESEARCH
 ├─ UNCERTAIN → explicit unresolved state
 └─ PASS
      ↓
SYNTHESIZE
      ↓
DONE / PARTIAL
```

最终：

```text
                   Accepted Evidence
                         │
                ┌────────┴────────┐
                ▼                 ▼
            Local Wiki       Survey Report
                │
                │ prior knowledge
                └────────────→ future research
```

如果后续架构逐渐无法通过这几张图解释，说明系统可能再次变得过度复杂。

---

# 33. 第一个核心架构决策

## ADR Direction — Claude Code Is the Agent Runtime

本项目正式采用以下方向：

> **Claude Code owns the outer research loop; Python Harness provides deterministic actions, persistent state, validation and lifecycle constraints.**

换句话说：

```text
Claude Code = Agent Runtime
Python Harness = Research Runtime
```

不是：

```text
Python Harness = Agent Runtime
Claude = Model API
```

### 原因

1. 产品定位本身就是 Claude Code Harness。
2. Claude Code 已经提供 Agent Loop、Tool Use 和 Context Management。
3. 重复实现第二套 Agent Runtime 会增加不必要复杂度。
4. 我们真正需要创新和工程化的是 Research State、Evidence、Loop Contract、Resume、Review Gate 和 Wiki，而不是通用 Agent Runtime。
5. 该边界允许未来在确有需求时再抽象其他 Execution Adapter，而无需现在提前承担复杂度。

---

# 34. 参考项目的使用原则

本项目会学习其他开源项目，但不以复制某个项目为目标。

主要参考方向包括：

* Externalized State；
* Research Harness；
* Loop Engineering；
* Evidence Retrieval；
* Literature Research；
* LLM-maintained Wiki。

阅读开源项目时始终采用：

```text
Problem
↓
Why did they design it this way?
↓
What problem does the abstraction solve?
↓
Does the same problem exist here?
↓
Can we solve it more simply?
```

而不是：

```text
They have component X
↓
We should also have component X
```

参考项目是：

> 设计证据。

不是：

> 功能采购清单。

---

# 35. 当前开发阶段

当前仓库已经完成：

```text
Repository Bootstrap
```

当前已经明确：

```text
Project Vision
+
Core Design Principles
+
Agent Runtime Boundary
```

接下来仍然不是立即实现完整 Harness。

后续顺序应保持：

```text
Reference Project Study
        ↓
Architecture Decisions
        ↓
Domain Model
        ↓
Minimal Research Loop
```

每个阶段都应遵循：

```text
Design
→ Implement
→ Test
→ Review
→ Understand
→ Next
```

---

# 36. 最终原则

整个项目开发过程中，应持续维护以下四句话：

> **Simple loop.**

研究控制流保持简单。

> **Rich state.**

真正的研究复杂度通过显式状态表达，而不是不断增加 Phase。

> **Hard evidence.**

重要结论必须能够追溯到原始论文证据。

> **Criteria over magic scores.**

资源可以用数字限制，研究质量必须通过可解释、可检查的条件判断。

并增加一条执行边界：

> **Claude drives the research; the Harness makes it reliable.**

中文：

> **Claude 驱动研究，Harness 保证研究过程可靠。**

如果未来某个设计违背这些原则，应优先重新审视设计，而不是继续在其上增加更多补丁。
