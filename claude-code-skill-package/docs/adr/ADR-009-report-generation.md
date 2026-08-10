# ADR-009：最终报告从权威 Research State 经叙事规划与独立编辑生成

* **状态**：已接受
* **阶段**：Delivery / Report Generation
* **日期**：2026-08-10
* **影响范围**：Delivery、Report Generation、Narrative Planning、Editorial Review、Citation Verification、Writing Guideline
* **关联决策**：

  * ADR-001 — Claude Code 驱动研究循环，Python Harness 守住系统不变量
  * ADR-002 — Research Run 使用四个最小生命周期模式
  * ADR-003 — Research Contract 定义 Research Run 的语义边界
  * ADR-004 — 持久化论文级理解与领域级理解
  * ADR-005 — Research State 通过类型化变更在 ResearchRun 边界内原子更新
  * ADR-006 — Research State 通过用途化投影渲染为有界 Context
  * ADR-008 — 论文通过按需 Source Access 支持渐进式阅读

## 背景

Completion Check 通过以后，Research Run 获得进入 `DELIVERY` 的资格，但“研究已经足够”并不意味着可以直接把 Research State 展开成一份高质量报告。

Research State 按研究语义组织 Paper Analysis、Approach Families、Landscape Findings 和 Open Problems。这种结构适合保存和验证知识，却不一定符合读者理解领域的顺序。

如果直接采用：

**Research State → Content Skeleton → Expand → Polish**

文章结构会在写作早期被知识结构固定。后续润色可以改善措辞，却很难修复章节顺序、信息分组、论文罗列和整体论述路径。

同时，Report 与 Local Wiki 面向不同用途。Report 服务于一次 Deliverable 的连续阅读；Wiki 服务于跨 Run 的知识检索和复用。两者都可以来源于 Research State，但不应互相作为生成中间层。

因此需要明确 Report Generation 的边界：

> **报告如何从已经验证的 Research State 转化为适合人阅读的技术文章，同时保持研究依据、写作质量和系统复杂度之间的平衡？**

## 决策

V1 的最终报告直接从当前 Research Run 的权威 Research State 生成。

整体过程为：

**Delivery View + Writing Guideline → Narrative Plan → Compose → Editorial Integration → Fresh Editorial Review → Research Integrity / Citation Verification → Final Report**

这些步骤全部属于 `DELIVERY` 中的工作，不形成新的 Lifecycle，也不建立独立的 Report State Machine。

## Report 直接读取权威 Research State

Report 不通过 Wiki、旧报告或其它摘要层间接生成。

Narrative Plan 负责决定如何组织内容，但正文中的事实、领域判断和来源应继续从权威 Research State 获取。

因此：

> **Narrative Plan 决定怎么讲，Research State 决定可以讲什么。**

Writer 不应把 Narrative Plan 中的摘要文本继续扩写成正文，以避免 summary-of-summary 带来的语义漂移。

需要具体证据时，Writer 可以按照 ADR-006 和 ADR-008，通过稳定 Research Ref 下钻到 Domain Object 和原始来源。

## Narrative Plan 描述读者理解路径

写作开始前，Claude 需要形成一个轻量 Narrative Plan。

它至少解决以下问题：

* 当前 Deliverable 面向什么读者；
* 整篇报告希望读者最终理解什么；
* 哪些领域判断最值得展开；
* 内容按照什么顺序出现；
* 哪些 Research Ref 支撑各部分；
* 哪些术语需要统一。

Narrative Plan 组织的是读者认知路径，不是 Research State 的目录，也不是固定报告模板。

它可以作为 Delivery Artifact 保存以支持 Resume 和人工检查，但不进入 `state.json`，也不成为新的 Domain Entity。

对于很短的报告，Narrative Plan 可以自然退化为简单计划，不要求独立文件。

## Compose 直接基于研究状态写作

Writer 根据 Narrative Plan 选择当前需要的 Research State，并直接形成正文。

V1 不冻结“全文一次生成”或“逐节生成”的固定调用方式。不同长度的报告可以采用不同生成粒度，但长报告的局部生成必须保留对全局 Narrative Plan、必要前文和相关 Research State 的可见性。

论文不默认成为文章结构。多篇论文讨论同一问题时，应优先围绕机制、差异、条件和冲突进行综合。

Research State 可以比最终报告丰富得多。报告的完整性以 Research Contract 中的 Deliverable 为边界，而不是要求输出所有已知知识。

## 整体编辑取代末端润色

Compose 之后需要以完整文档为对象进行 Editorial Integration。

它允许：

* 调整章节和段落顺序；
* 合并重复内容；
* 拆分过载段落；
* 删除无信息量的解释；
* 调整标题、列表和表格；
* 统一术语；
* 改善段落节奏和逻辑连接。

Editorial Integration 可以重新组织表达，但不能创造新的领域判断或改变 Research State 中的研究语义。

因此它属于结构性编辑，而不是简单语言润色。

## 使用 Fresh Editor 提供独立阅读视角

完成整体编辑后，由一个 fresh-context Claude 作为 Editorial Reviewer 阅读 Draft。

Fresh Editor 默认获得：

* Deliverable 与必要读者信息；
* Narrative Plan；
* `REPORT_WRITING_GUIDE.md`；
* 当前 Draft。

它默认不获得完整 Research State。

这种信息隔离是有意设计的。Fresh Editor 模拟第一次阅读报告的技术读者，更容易发现作者因为掌握过多背景而忽略的问题，例如：

* 逻辑跳跃；
* 重复解释；
* 标题过密；
* 段落碎片化；
* 论文逐篇罗列；
* 术语漂移；
* 中英文使用不自然；
* 模板化转折和总结；
* 信息密度失衡。

Fresh Editor 输出具体、可行动的 Editorial Issues，不提供抽象质量分数。

它没有 Research Authority，不能创造新的领域判断，也不能自行修改 Research State。

## 编辑质量与研究完整性分别检查

V1 不建立统一的 Report Quality Score。

Editorial Review 回答：

> **这篇报告是否形成了一篇清晰、自然、专业的技术文章？**

Research Integrity 与 Citation Verification 回答：

> **报告中的研究判断是否仍然忠实于权威 Research State 和原始来源？**

后者至少需要验证：

* 重要判断是否来自 Research State；
* 引用是否能够解析到对应 Paper；
* 必要 Locator 是否存在；
* 不确定性和证据边界是否被保留；
* Delivery 是否引入了未经研究的新判断。

可以确定性检查的引用解析、编号、Bibliography 完整性和内部 ID 泄漏继续由 Python Harness 处理。

语义性的研究支持关系由 Claude 根据 Research State 和来源判断。

## Delivery 中发现问题时按语义影响升级

Delivery 阶段允许发现新的问题，但不能直接把新的实质研究判断写入权威 Research State。

处理原则是：

> **问题是否改变权威研究语义？**

如果只是：

* 结构或措辞问题；
* Draft 表述超出已有 Research State；
* 术语不一致；
* Citation / Locator 的机械错误；
* 对已有来源进行引用核验；

则留在 `DELIVERY` 中修正。

如果核验发现：

* Paper Analysis 或 Landscape Finding 本身错误；
* 新问题会影响 Contract Requirement；
* 核心结论缺少必要研究；
* 需要产生新的实质领域判断；

则返回 `RESEARCH`。

Research State 被实质修改后，原 Completion approval 失效，需要重新经过 Completion Check 才能进入 Delivery。

因此：

> **Delivery 可以发现研究问题，但不能在交付阶段静默完成新的研究。**

## Writing Guideline 是跨 Run 的写作策略

V1 使用 `.claude/skills/literature-research/references/REPORT_WRITING_GUIDE.md`
保存长期写作标准。

它规定准确性、简洁性、自然表达、专业术语、叙事组织、结构节奏和常见反模式，但不规定固定报告模板。

Research Contract 与当前 Deliverable 高于 Guideline 的默认表达偏好；研究准确性和来源完整性则始终属于系统不变量。

Human Feedback 可以产生 Guideline 修改建议，但 V1 不允许 Claude 自动批准自己的长期策略变化。

演化流程为：

**Human Feedback → Claude Distillation → Guideline Patch Proposal → Human Promotion**

Git 负责保存版本历史，不建立 Guideline Database、Policy Entity 或额外事件系统。

原则是：

> **Research knowledge accumulates; writing policy distills.**

## Report Artifact 不进入 Research Domain

Narrative Plan、Draft、Editorial Review、Citation Map 和 Final Report 都属于 Delivery Artifact。

概念上可以保存在：

`runs/<run_id>/artifacts/report/`

具体文件名和序列化格式留给实现阶段决定。

这些 Artifact 可以用于 Resume、调试和人工检查，但不成为 Research State 的第二事实来源。

## 不建立 Report Revision State Machine

V1 不引入：

* `REPORT_DRAFTING`
* `REPORT_REVIEW`
* `REPORT_REVISING`
* 多 Reviewer 投票
* 固定最大修订轮数
* 基于分数阈值的自动优化循环

Writer 可以根据 Fresh Editor 的具体问题进行必要修订，并在需要时再次检查。

这些行为仍然只是 `DELIVERY` 中的 Action。

如果问题升级到 Research，则复用已有 Lifecycle，而不是建立第二套 Report Loop。

## 不采用的方案

### Research State 直接生成最终报告

结构最简单，但容易把知识存储结构直接映射成文章结构，长期表现依赖模型默认写作习惯。

不采用。

### 先生成 Wiki，再从 Wiki 生成 Report

增加一层摘要来源，使 Wiki 实际成为第二事实源，并产生 summary-of-summary 漂移。

不采用。

### Skeleton → Expand → Polish

过早冻结文章结构，将真正的叙事问题留给末端润色处理。

不采用。

### Writer 自我检查即可

缺少独立阅读视角，难以稳定发现隐含跳步、重复和结构惯性。

不采用。

### 多 Agent Writer / Critic 优化循环

能够增加反馈次数，但同时引入新的循环、终止条件和质量阈值，与 V1 简洁目标不符。

不采用。

### 自动更新 Writing Guideline

能够降低人工维护成本，但容易把一次性偏好或错误反馈提升成长期策略。

V1 保留 Human Promotion Authority。

不采用。

## 后果

这一决策使 Report Generation 保持在一个简单边界内：

* Research State 保存权威研究知识；
* Narrative Plan 负责一次交付的叙事取舍；
* Writing Guideline 保存跨 Run 写作经验；
* Writer 负责形成和编辑正文；
* Fresh Editor 提供独立阅读视角；
* Research Integrity 与 Citation Verification 守住事实边界；
* Python Harness 继续负责确定性的引用和 Artifact 处理。

代价是 Delivery 中会增加一次 Narrative Planning 和独立 Editorial Review，并可能在发现研究问题时重新进入 Research。

这个成本是有意接受的，因为它没有增加新的领域状态机或基础设施，却能够分别处理研究正确性和人类可读性两个不同问题。
