# ADR-012：通过 Report Brief 与双重审校闭环生成最终报告

* **状态**：已接受
* **阶段**：Delivery / Report Generation
* **日期**：2026-08-13
* **影响范围**：Delivery、Report Construction、Report Brief、Writer、Editorial Review、Research Integrity Review、Source Access、Citation Rendering
* **关联决策**：

  * ADR-001 — Claude Code 驱动研究循环，Python Harness 守住系统不变量
  * ADR-002 — Research Run 使用四个最小生命周期模式
  * ADR-003 — Research Contract 定义 Research Run 的语义边界
  * ADR-004 — 持久化论文级理解与领域级理解
  * ADR-005 — Research State 通过类型化变更在 ResearchRun 边界内原子更新
  * ADR-006 — Research State 通过用途化投影渲染为有界 Context
  * ADR-008 — 论文通过按需 Source Access 支持渐进式阅读
  * ADR-009 — 最终报告从权威 Research State 经叙事规划与独立编辑生成
  * ADR-011 — 通过候选论文闭合将 Deep Reading 接入 Research Loop

本 ADR 延续 ADR-009 的基本原则：

* Research State 是报告事实权威；
* Report 与 Wiki 独立从 Research State 派生；
* Delivery 不建立独立 Report State Machine；
* Editorial Review 与 Research Integrity 分开；
* Writing Guideline 不由 Runtime 自动演化。

本 ADR 取代 ADR-009 中：

```text
Narrative Plan
→ Compose
→ Editorial Integration
→ Fresh Editorial Review
```

的具体中间设计。

新的报告生成骨架为：

```text
Research State
→ Report Brief
→ Writer
→ Report Reviewer ↔ Reviser
→ Research Integrity Reviewer
→ Citation Renderer
→ Final Report
```

可以概括为：

> **一个权威 State，一个 Report Brief，两个独立 gate；问题返回最早有资格修复它的层。**

---

## 背景

Completion Check 通过只说明：

> **当前 Research Contract 下，已经存在足够的权威研究知识，可以开始形成交付物。**

Research State 按研究语义组织 Paper Analysis、Approach Families、Landscape Findings 和 Open Problems。

最终报告则需要按照读者认知组织：

```text
应该先建立什么认识？
哪些判断需要展开？
这些判断怎样形成连续论证？
哪些材料承担支持、对比、限制或反例作用？
哪些证据边界必须保留？
```

两种结构不能直接等同。

ADR-009 的 `Narrative Plan` 已经尝试处理这一差异，但真实运行暴露出三个问题。

### Narrative Plan 过薄

现有 Narrative Plan 能描述：

```text
这一节谈什么
```

但不能稳定保存：

```text
这一节怎样建立判断
材料为什么出现在这里
哪些具体条件和限制必须恢复
证据在哪里停止
```

因此正文仍可能在正确主题下退化成 paper-by-paper summary。

### Writer 职责过宽

现有 Writer 同时承担：

```text
文章组织
+
Research State / Source drilldown
+
研究材料解释
```

当计划材料不足时，Writer 容易在写作过程中形成新的 research interpretation。

这些解释即使合理，也可能超过 Completion 已经接受的 Research State。

### Editorial Review 没有形成闭环

现有 pipeline 只运行一次 Fresh Editor。

修订后的正文不会自动交给新的 first-time reader 再次检查，因此没有形成：

```text
draft
→ find blockers
→ repair
→ new independent read
→ blockers gone
```

的真实闭环。

---

## 决策

V1 将 Report Generation 明确分为三个数据层：

```text
Research State
      ↓
Report Brief
      ↓
Final Report
```

其中：

* `Research State` 保存当前 Run 已接受的研究知识；
* `Report Brief` 保存当前 Deliverable 的论证、材料和证据边界；
* `Final Report` 将 Brief 写成人类可以连续阅读的技术文章。

整体 Delivery 流程为：

```text
Research State
      ↓
Completion Check
      ↓ PASS
Report Construction
      ↓
Report Brief
      ↓
Writer
      ↓
Manuscript
      ↓
NEW Report Reviewer
      ├─ Blocking Issues → Reviser → New Manuscript → NEW Reviewer ↺
      └─ no Blocking Issues
      ↓
Research Integrity Review
      ├─ PASS → Citation Renderer → Publish
      ├─ REVISE_DELIVERY → earliest faulty Delivery layer
      └─ REOPEN_RESEARCH → Research
```

所有步骤仍属于现有 `DELIVERY`。

V1 不新增 Report lifecycle mode 或独立 Report FSM。

---

## Report Brief 是唯一报告语义中间层

`Report Brief` 取代 `Narrative Plan`。

它不是 Research Domain Entity，也不是 Research State 的第二事实源。

它回答：

> **对于当前 Deliverable 和读者，在不超过已接受 Research State 的前提下，报告应该建立什么判断、怎样建立、需要哪些材料，以及证据在哪里停止。**

概念上，Brief 可以包含：

```text
audience
report_goal
reader_takeaway
narrative_logic

sections:
    title
    requirement_refs
    purpose
    reader_takeaway
    argument_flow
    research_refs
    material
    evidence_boundary

terminology
intentional_omissions
```

这些字段描述 semantic shape，不要求所有报告或 section 机械填写所有字段。

### `argument_flow`

`argument_flow` 表示建立 section takeaway 所需的有序 semantic moves。

它不是 paragraph plan，也不是句子模板。

### `material`

Material 保存当前论证真正需要的高密度事实、条件、机制、数字和限制，并保留其 evidence refs / locators。

Material 可以带自然语言 role，例如：

```text
mechanism contrast
limitation
independent validation
negative composition evidence
```

V1 不建立 MaterialRole Enum。

Material 是 Delivery-specific distillation，不是新的 Research truth，也不缓存大段原始 SourceContent。

### `evidence_boundary`

Brief 可以记录当前论证不能越过的证据边界。

它帮助 Writer 保持 claim strength，但不替代 Research Integrity Review。

---

## Report Brief 不进入 Research Domain

V1 不在 `ResearchRun` 中增加：

```text
report_brief
report_plan
report_revision
```

字段，也不新增：

```text
ArtifactKind.REPORT_BRIEF
```

Report Brief 是 rebuildable Delivery work product。

是否持久化 Brief 属于 Delivery resume 与实现成本之间的实现选择，不改变其 authority boundary。

---

## Brief freshness 绑定 Delivery Basis

Delivery 中的 source access 和 resource accounting 可以推进 `state_revision`，但不一定改变 Completion 已接受的研究依据。

因此 Brief freshness 绑定：

```text
DeliveryBasis
```

而不是普通：

```text
state_revision
```

如果重新进入 `RESEARCH`，旧 DeliveryBasis 失效，旧 Brief 随之失效。

---

## Report Construction 从 Deliverable 反推论证与材料

`Report Constructor` 取代 `Narrative Planner`。

它从：

```text
Research Contract
Delivery View
Delivery Basis
Writing Guideline
```

出发，决定：

```text
当前 Deliverable 必须回答什么
→ 读者需要理解什么
→ 报告必须建立哪些判断
→ 这些判断怎样组织
→ 每节需要什么 argument flow
→ 哪些 accepted Research refs 支撑
→ 还缺哪些具体 material
```

如果现有 Paper Analysis 足够，就不机械 reread source。

如果当前 report promise 需要更多细节，可以按需：

```text
inspect Research ref
→ inspect-source
→ targeted read-source
```

Delivery reading depth 由当前 material need 决定，不由 source-read count 决定。

---

## Semantic Ceiling 限制 Delivery 的解释权限

Delivery 可以恢复表达现有判断所需的：

```text
数字
实验条件
mechanism detail
baseline
hardware
limitation
说明性例子
```

但不能改变已接受研究语义。

如果新的 Delivery reading 说明：

```text
Finding scope / strength 应改变
consensus 应改变
Approach Family 关系应改变
Open Problem 应改变
Contract-facing judgment 应改变
```

则必须返回 `RESEARCH`。

原则是：

> **Delivery 可以增加 detail density，不能扩张 accepted semantic scope。**

---

## Report taxonomy 独立于 Research taxonomy

Approach Family、Finding、Open Problem 和 Paper Analysis 是研究知识结构。

它们不决定最终报告章节。

因此：

> **Research Entity 是 Report material，不是 Report outline。**

论文应服务于报告判断，而不是默认成为文章段落单位。

---

## Writer 有文章推理权，没有 Research Authority

Writer 主要根据：

```text
Report Brief
Writing Guideline
必要的 retained-paper / citation metadata
```

形成 `ReportManuscript`。

Writer 负责：

```text
信息顺序
段落设计
因果与对比关系
abstraction level
terminology
density / rhythm
prose / list / table
内容展开与压缩
```

但不能重新定义 Research State 中的研究语义。

Writer 默认不承担 broad Research / Source drilldown。

这一边界限制的是 semantic authority，而不是永久禁止某个物理只读工具。

如果 Writer 发现 Brief 材料不足，应反馈给 Report Construction。

原则是：

> **Writer 有反馈权和文章推理权，但没有研究解释权。**

---

## 表达形式由信息关系决定

Writing Guide 继续负责一般写作标准。

格式选择遵循：

```text
因果 / 递进 / 连续解释
→ prose

真正并列、可独立扫描
→ list

多个对象 × 共同维度
→ table
```

V1 不建立列表配额、表格配额或视觉丰富度分数。

---

## Report Reviewer 使用两阶段 Cold Reading

`Fresh Editorial Reviewer` 改为 `Report Reviewer`。

`Fresh` 是执行要求，不是角色名称。

每次 revision 后都重新请求新的 Reviewer instance；agent adapter 应为其提供 fresh model context。

### Phase 1 — Blind Read

Reviewer 首次只获得：

```text
Deliverable description
Writing Guideline
Manuscript
```

不获得 Report Brief。

这一阶段检查最终文章实际向第一次读者传达了什么。

### Phase 2 — Brief Check

Blind Read 后才提供 Report Brief。

Reviewer 检查：

```text
重要判断是否遗漏或弱化
关键 material 是否没有服务于论证
正文是否加入 Brief 未授权的重要判断
evidence boundary 是否被隐藏或削弱
正文是否真正完成 report promise
```

Reviewer 可以发现正文与 Brief 不一致，但不负责最终确认 claim 是否被 Primary Evidence 支持。

后者属于 Research Integrity Review。

---

## Editorial Loop 只处理 Blocking Issues

V1 不使用统一质量分数。

Reviewer 返回具体、可修复的 Blocking Issues。

停止条件是：

```text
Blocking Issues = ()
```

不是固定轮数，也不是 score threshold。

硬资源限制可以终止执行，但不能把“资源耗尽”解释为 PASS。

---

## Reviser 修具体问题，不重新研究

Reviser 根据：

```text
Report Brief
Writing Guideline
Current Manuscript
Editorial / Integrity issue
```

修复明确的 manuscript problem。

如果问题不属于 Manuscript：

```text
Brief 有缺陷
→ Report Construction

Research State 有缺陷
→ RESEARCH
```

Reviser 不拥有重新研究或改变 Research State 的 authority。

---

## Manuscript 修改后必须重新通过 Editorial gate

Runtime 不判断：

```text
minor change
material change
editorially relevant change
```

V1 使用简单不变量：

> **只要 Manuscript 被修改，旧 Editorial PASS 就失效。**

因此任何 Revised Manuscript 都必须由新的 Report Reviewer 再次 Cold Read。

这一规则用额外一次 Reviewer call 换取更简单的 Runtime boundary。

---

## Research Integrity Review 独立于 Editorial Review

Report Reviewer 回答：

> **这篇文章作为文章是否成立，并且是否忠实完成 Brief？**

Research Integrity Reviewer 回答：

> **文章中的重要研究判断，其强度是否仍然与 Research State 和 Primary Evidence 匹配？**

两者不能合并。

Integrity Reviewer 可以获得：

```text
Delivery View
Report Brief
Manuscript
Delivery Evidence Access
Research Integrity Guide
```

Brief 在这里作为 traceability map，而不是重新规划文章的入口。

Integrity disposition 保持：

```text
PASS
REVISE_DELIVERY
REOPEN_RESEARCH
```

### `PASS`

可以进入 Citation Rendering。

### `REVISE_DELIVERY`

Research State 仍足以支持当前交付，但 Delivery artifact 需要修复。

它是 disposition，不等价于固定调用 Reviser。

修复继续遵守 earliest faulty layer。

### `REOPEN_RESEARCH`

如果 Research State 本身不足、错误，或需要新的 contract-facing research judgment，则返回 `RESEARCH` 并重新经过 Completion。

---

## 问题返回最早有资格修复它的层

所有反馈统一遵循：

```text
State 正确
Brief 正确
Manuscript 有问题
→ Reviser

State 正确
Brief / material / argument 有问题
→ Report Construction

State 本身不足或错误
→ RESEARCH
```

这一规则适用于 Writer feedback、Editorial Review、Research Integrity Review，以及当前 Delivery 中的人类反馈。

因此不需要 Material Queue、Revision State 或新的 workflow entity。

---

## Citation Renderer 只做确定性引用工作

Research Integrity `PASS` 后才进入 Citation Rendering。

Renderer 负责引用解析、编号、Bibliography、canonical navigation、内部 ref 防泄漏和最终 artifact content。

Renderer 不重新判断 research support，也不修改文章语义。

---

## Claude 与 Python Harness 的职责边界

Claude 负责：

* report goal 与 reader model；
* argument flow；
* material sufficiency；
* targeted drilldown 是否需要；
* report taxonomy；
* prose / list / table；
* Blocking Issue；
* evidence boundary 的语义解释；
* claim strength 与 evidence strength 的匹配；
* earliest faulty layer；
* 是否返回 Research。

Python Harness 负责：

* lifecycle legality；
* stable ref validation；
* capability boundary；
* source access accounting；
* revision；
* DeliveryBasis freshness；
* Brief refs 的结构合法性；
* Blind Review Phase 1 接口不接收 Brief；
* revision 后重新请求新的 Reviewer instance；
* Editorial blockers 清空前不能进入 Integrity；
* Integrity 非 PASS 时不能 render / publish；
* existing `REOPEN_RESEARCH` transition；
* deterministic citation rendering；
* artifact provenance 与 validation。

Python 不计算：

```text
argument_quality
material_score
readability_score
report_quality_score
```

---

## 不建立新的 Report Domain Model

V1 不新增：

```text
Report
ReportSection
ArgumentNode
ReaderNeed
DeliveryObligation
RequirementChain
MaterialNeed
MaterialRequest
EvidenceItem
ReportRevision
EditorialRound
ReviewStatus
SectionStatus
```

等 Domain Entity。

Brief 内部可以使用轻量 value object，但它们没有 stable identity、independent lifecycle 或 cross-run authority。

---

## Human Feedback 的边界

当前 `DELIVERY` 中的人类反馈继续遵循 earliest faulty layer。

长期 Writing Guide 的演化继续由 Human Promotion 控制。

以下问题不在本 ADR 中决定：

```text
CLOSED → human feedback → reopen-delivery
published Report v1 → later Report v2 → artifact history
```

Post-CLOSED revision 与 published artifact history 需要单独 ADR。

---

## 不采用的方案

### Research State 直接生成 Final Report

会重新混合 research storage structure、report structure 和 Writer research authority。

不采用。

### 只增强 Narrative Plan Prompt

缺失的是稳定的 argument flow、role-aware material 与 evidence boundary，不只是 Prompt 强度。

不采用。

### Writer 继续拥有 broad Research / Source authority

会重新混合 writing 与 research interpretation。

不采用。

### 保留 Editorial Integrator

其职责已被 Writer、Reviewer 和 Reviser覆盖，缺少独立语义边界。

不采用。

### Reviewer 第一次阅读就看到 Brief

会削弱 first-time-reader validation。

不采用。

### 同一 Reviewer 连续参与 revision

会逐渐失去独立阅读视角。

不采用。

### 合并 Editorial Review 与 Research Integrity

可读性与 research fidelity 是不同 failure mode。

不采用。

### Report Quality Score

会把不可约的质量问题压成任意标量和阈值。

不采用。

### 固定最大修订轮数作为完成条件

固定轮数属于资源策略，不属于 semantic completion。

不采用。

### 每节强制 reread Primary Source

会错误地把阅读深度定义成 source-read count。

不采用。

### 将 Report Brief 写入 ResearchRun

Brief 是 Deliverable 派生工作产品，不是 Research truth。

不采用。

### 新建 Report FSM / Revision Domain

现有 Delivery Action、Report Brief 与两个 gate 已经可以闭合问题。

不采用。

---

## 后果

最终结构为：

```text
Research State
→ Report Brief
→ Writer
→ Reviewer ↔ Reviser
→ Integrity
→ Citation Renderer
→ Final Report
```

收益：

* Research taxonomy 与 Report taxonomy 解耦；
* Brief 保存“怎样建立判断”，而不只保存“谈什么”；
* Writer 专注文章推理，不重新拥有 broad Research authority；
* Blind Review 验证第一次读者实际获得的理解；
* Reviewer / Reviser 形成真实 editorial closure；
* Integrity 独立守住 research fidelity；
* source reread 仍按具体 material need 触发；
* 不需要 Report FSM、Quality Score 或新的 persistent Domain Entity。

代价：

* Delivery 增加 semantic model calls；
* Reviewer / Reviser loop 调用次数不固定；
* Brief 比 Narrative Plan 更丰富；
* Constructor 需要准备更高质量 material；
* Integrity repair 后即使修改很小，也重新经过 Editorial Review；
* Brief persistence 与 Delivery resume 仍需实现层权衡。

最终不变量只有五条：

```text
1. Research State 是唯一研究权威。

2. Report Brief 是唯一报告语义中间层。

3. Writer 有文章推理权，没有 Research Authority。

4. 每个最终 Manuscript 必须通过：
   Reader gate + Research Integrity gate。

5. 问题返回最早有资格修复它的层：
   Manuscript → Reviser
   Brief      → Constructor
   State      → Research
```

复杂性被限制在：

```text
rich semantic reasoning
+
one derived work product
+
two independent gates
```

之内，而没有扩张为新的 Domain、Lifecycle 或评分系统。
