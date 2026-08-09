# ADR-010：Local Wiki 作为 Closed Research State 的可重建跨 Run 投影

* **状态**：已接受
* **阶段**：Knowledge / Cross-Run Projection
* **日期**：2026-08-10
* **影响范围**：Local Wiki、Cross-Run Knowledge、Wiki Projection、Wiki Query、Knowledge Reuse、Wiki Validation
* **关联决策**：

  * ADR-001 — Claude Code 驱动研究循环，Python Harness 守住系统不变量
  * ADR-002 — Research Run 使用四个最小生命周期模式
  * ADR-003 — Research Contract 定义 Research Run 的语义边界
  * ADR-004 — 持久化论文级理解与领域级理解
  * ADR-005 — Research State 通过类型化变更在 ResearchRun 边界内原子更新
  * ADR-006 — Research State 通过用途化投影渲染为有界 Context
  * ADR-008 — 论文通过按需 Source Access 支持渐进式阅读
  * ADR-009 — 最终报告从权威 Research State 经叙事规划与独立编辑生成

## 背景

一次 Research Run 结束后，其中形成的领域理解仍然具有跨任务价值。

如果后续 Run 完全从零开始，Claude 会反复重新发现：

* 已知技术路线；
* 代表论文；
* 已确认的领域判断；
* 已知冲突；
* 开放问题；
* 有价值的来源定位。

直接搜索历史 `ResearchRun` 可以复用这些信息，但随着 Run 数量增加，每次查询都需要重新完成跨 Run 的归组、去重和综合。

因此需要一个 Local Wiki，提前把已完成研究压缩成可查询的长期知识。

但 Wiki 不能成为第二套权威 Research State。

如果持续在旧 Wiki 页面上增量改写：

**Old Wiki + New Research → LLM Rewrite → New Wiki**

页面会逐渐依赖过去的摘要和改写结果，而不是原始研究状态，最终产生 summary-of-summary 漂移。页面本身也会逐渐承担事实源角色。

本 ADR 需要解决：

> **如何让知识跨 Research Run 复用，同时保持 Research State 和 Primary Paper 的权威地位，并避免建立第二套跨 Run Domain Model？**

## 决策

V1 将 Local Wiki 定义为：

> **由已完成 Research Run 的权威领域级研究状态生成的、可重建的跨 Run 语义投影。**

整体关系为：

**Primary Papers → ResearchRun State → Local Wiki**

未来 Run 使用 Wiki 时：

**Local Wiki → Knowledge Prior / Research Lead → Primary Paper → Current ResearchRun State**

Wiki 帮助 Claude 更快找到值得研究的方向和来源，但不能直接为当前 Run 提供权威研究判断。

## Research State 始终高于 Wiki

Wiki Page 是派生内容，可以删除、重命名、拆分、合并并重新生成。

它不进入 `ResearchRun.state.json`，也不能成为：

* `LandscapeFinding` 的 Literature Source；
* Completion Check 的证据；
* Report 中研究判断的最终来源。

当前 Run 如果需要使用 Wiki 中的某项结论，必须回到对应论文，并按照当前 Research Contract 重新核验。

因此：

> **Wiki 帮助决定研究什么；Primary Paper 决定当前 Run 可以声称什么。**

Wiki 错误通过修正权威研究输入并重新构建解决，而不是长期手工维护派生页面。

## 只有合格的 Closed Run 进入 Wiki

V1 只从已经通过 Completion Check 并最终进入 `CLOSED` 的 Research Run 构建 Wiki。

是否满足投影资格从已有 Research State 推导，不新增：

* Wiki Promotion State；
* Knowledge Approval；
* Wiki Published Flag；
* Knowledge Quality Score。

未完成或仅部分交付的 Run 默认不进入 Wiki。

如果未来证明这一限制过强，再单独引入显式 Promotion 机制。

## Wiki 只投影具有跨 Run 价值的领域级知识

V1 的主要投影输入包括：

* Approach Families；
* Landscape Findings；
* Open Problems；
* Representative Papers；
* Literature Sources。

`Paper Analysis` 可以作为语义投影的辅助上下文，但不要求整体复制到 Wiki。

以下内容默认不进入 Wiki：

* Investigation Gaps；
* Completion Check；
* Budget 与 Resource State；
* Action / Event History；
* Report prose；
* Delivery-specific Narrative Plan。

`Investigation Gap` 描述某次 Run 尚未研究清楚的问题；`Open Problem` 描述领域本身尚未解决的问题。只有后者具有稳定的跨 Run 知识价值。

## Wiki 使用 Full Derivation，而不是增量改写旧页面

Wiki 每次构建都从当前所有 eligible Research Runs 的权威输入重新推导。

逻辑上：

**Eligible Research States → Wiki Projection → Wiki**

旧 Wiki prose 不作为新 Wiki 的知识输入。

V1 可以直接采用完整重建。

随着规模增长，可以优化为只识别受影响的主题并重建对应页面，但单个页面仍必须从权威 Research State 重新生成，而不是在旧页面上持续 patch。

因此：

> **可以增量判断什么失效，但知识内容始终重新推导。**

Full Rebuild 指语义来源完整回到当前权威输入，不要求一次 Prompt 或一次 Context 生成整个 Wiki。

## Claude 负责语义投影，Python 负责确定性边界

Wiki 无法完全通过确定性代码生成。

跨 Run 的：

* 同义概念归组；
* 重复判断压缩；
* 条件差异保留；
* 冲突表达；
* 页面主题划分；

都需要语义判断。

因此职责为：

**Python Harness**

* 选择 eligible Runs；
* 提取 Wiki Projection Input；
* 验证 Research Ref；
* 维护构建 provenance；
* 做文件与链接检查；
* 原子发布最终 Wiki。

**Claude**

* 形成 Topic Map；
* 综合相关 Research Findings；
* 组织 Wiki 页面；
* 保留冲突、条件和不确定性；
* 决定页面拆分与合并。

Claude 可以重新组织和压缩已有研究理解，但不能借跨 Run 综合创造新的权威 Landscape Finding。

如果构建过程中发现值得研究的新推论，它只能作为 future research lead，而不能作为已确认知识静默写入 Wiki。

## Wiki 不建立跨 Run Canonical Domain Entity

不同 Research Run 可能对相近概念使用不同名称，例如：

* `Process Reward Guided Search`
* `Search with Intermediate-State Evaluation`

Wiki 可以在同一页面中说明这些研究共享某些机制，但这不表示两个 `ApproachFamily` 在 Domain Identity 上被合并。

V1 不建立：

* Global Approach Family；
* Global Landscape Finding；
* Global Open Problem；
* Wiki Claim；
* Wiki Evidence；
* Canonical Topic Entity。

原则是：

> **Wiki 可以合并表达，不合并身份。**

跨 Run canonicalization 只有在未来确实需要多个 Run 共享稳定领域实体身份时才设计。

## Paper 去重只发生在投影层

同一论文可能在多个 Run 中以不同局部 `PaperRef` 存在。

Wiki 可以根据 DOI、arXiv ID 或其它已有稳定外部标识在展示层去重，但不因此建立 `GlobalPaper`。

Wiki provenance 仍可保留：

* contributing Run；
* contributing Paper Ref；
* optional Source Locator。

未来 Run 真正使用论文时，仍建立当前 Run 自己的 `Paper`。

## 冲突必须显式保留

多个 accepted Runs 可能得到不同甚至相反的结论。

Wiki 不采用：

* latest wins；
* majority wins；
* 自动平均；
* 静默覆盖。

如果 Research State 足以解释差异，Wiki 可以表达条件性结论。

如果现有证据不足以解释，则直接保留：

> 当前结果存在冲突，原因尚不明确。

Wiki 可以压缩重复知识，但不能压缩掉会改变机制、适用条件或未来研究决策的差异。

因此：

> **Wiki 压缩知识，不压平分歧。**

## Wiki Page 不具有稳定领域身份

V1 不冻结固定 Page Taxonomy。

页面只需满足：

* 围绕一个可理解主题；
* 实质判断可回到 Research State；
* 来源最终可回到 Primary Paper；
* 冲突和不确定性不会静默消失；
* 可以通过 INDEX 和链接导航；
* 可以从权威输入重新生成。

页面可以在下一次 rebuild 中自由：

* 重命名；
* 拆分；
* 合并；
* 删除。

因此不需要 Page Merge Command、Alias Entity 或页面迁移机制。

## Wiki 保留轻量 Projection Provenance

Wiki 页面需要能够回到生成它的权威研究状态。

V1 至少保留：

**Page → Contributing Research Refs**

Research Ref 可以进一步解析到：

**ResearchRun → Paper → PaperSource → Locator**

这类 provenance 属于 Projection Metadata，不是新的知识 Domain Model。

V1 可以使用简单的：

`wiki/manifest.json`

记录：

* 构建所使用的 Research Runs；
* 对应 `state_revision`；
* 页面列表；
* 页面对应的 contributing Research Refs；
* 必要的构建元数据。

这使系统能够机械判断 Wiki 是否落后于当前 eligible Runs，也为未来 affected-topic rebuild 提供依赖信息。

## Wiki 使用 Build → Validate → Publish

Wiki Build 不属于 ResearchRun Lifecycle。

`CLOSED` 仍然是 Research Run 的终点。

Wiki 可以在 Run 结束后独立重建：

**CLOSED Runs → Build Wiki → Validate → Publish**

构建失败不会重新打开 Research Run，也不会改变其研究结果。

Wiki generation 可以分批完成，但 publication 应采用原子替换。

构建应先进入临时位置，全部验证成功后再替换当前发布版本。失败时保留旧 Wiki，不允许出现新旧页面混合状态。

## Wiki Validation 分为机械检查和语义检查

机械检查由 Python Harness 完成，例如：

* Research Ref 是否存在；
* Run 是否 eligible；
* manifest 是否完整；
* Paper Ref 是否可解析；
* 页面链接是否有效；
* 发布文件是否完整。

语义检查由 Claude 完成，例如：

* 页面中的实质判断是否来自输入 Research State；
* 是否遗漏影响结论的重要冲突；
* 是否把条件性结论错误写成普遍结论；
* 是否借综合产生了未经研究的新领域判断。

Wiki 不建立独立 Completion Gate 或 Lifecycle。

它的验证问题是：

> **当前投影是否忠实表达了给定的 accepted research inputs？**

而不是：

> **是否应该继续开放式研究？**

## Future Run 将 Wiki 作为 Prior 与 Research Lead

新 Research Run 可以通过 Wiki 快速获得：

* 已知领域地图；
* 主要技术路线；
* 已知冲突；
* Open Problems；
* 代表论文；
* 有价值的 Source Locator；
* 搜索关键词和研究线索。

这些信息用于降低探索成本。

Wiki 内容不能直接：

`PUT LandscapeFinding`

正确路径为：

**Wiki Lead → Retain Paper → Read Source → Current Paper Analysis → Current Landscape**

旧 Research Run 的来源定位可以被复用为导航线索，但当前 Run 真正依赖的判断仍需重新取得 Primary Source。

因此：

> **Wiki 复用探索结果，不替代当前 Run 的证据责任。**

Wiki 是否陈旧主要影响研究效率，不影响 Current Research State 的正确性，因此 V1 不要求强一致 freshness protocol。

## Wiki 与 Report 相互独立

Report 和 Wiki 都直接来源于权威 Research State。

V1 不采用：

**Research State → Wiki → Report**

也不采用：

**Research State → Report → Wiki**

Report 面向当前 Deliverable 的连续阅读；Wiki 面向跨 Run 的长期知识复用。

两者可以使用不同的组织方式，不互相承担事实源角色。

## 最小物理结构

V1 可以从简单本地文件开始，例如：

`wiki/INDEX.md`

`wiki/pages/`

`wiki/manifest.json`

具体 Markdown frontmatter、manifest schema、页面命名规则和查询实现属于实现阶段决定，本 ADR 不冻结。

V1 不因此引入：

* 数据库；
* Vector DB；
* Embedding Pipeline；
* Knowledge Graph；
* Wiki-specific Event Store。

如果未来知识规模导致检索成为真实瓶颈，可以增加全文索引或其它 Retrieval Infrastructure，但不改变 Wiki 的权威语义。

## 不采用的方案

### 直接查询历史 ResearchRun，不建立 Wiki

能够保持事实来源简单，但每次查询都要重新完成跨 Run 归组、去重、冲突发现和主题综合。

不采用。

### 持续增量改写旧 Wiki Page

单次成本较低，但长期会形成 summary-of-summary 漂移，并逐渐让 Wiki prose 成为事实源。

不采用。

### 建立跨 Run Global Knowledge Domain

可以提供稳定全局实体身份，但需要处理 canonicalization、merge、undo、冲突和生命周期，远超 V1 当前需求。

不采用。

### 固定 Wiki Page Taxonomy

可以提高页面格式一致性，但会提前冻结知识组织方式，并可能让页面类型反过来驱动领域理解。

不采用。

### Wiki 中允许产生新的跨 Run Finding

可以提高 Wiki 的综合能力，但会让 Wiki Builder 实际承担 Researcher 权限，使派生层成为新的知识入口。

不采用。

### Vector Database / RAG 作为 V1 基础设施

可能改善大规模查询，但目前没有证据表明 Markdown Wiki 的检索已经成为系统瓶颈。

不采用。

## 后果

这一决策使长期知识复用建立在一个单向、可重建的关系上：

**Research State 是权威知识；Wiki 是为了未来研究效率生成的读取投影。**

它允许 Claude 跨 Run 复用已有领域地图、论文线索和来源定位，同时不会让历史摘要绕过当前 Research Contract 和 Primary Source。

代价是 Wiki rebuild 需要重新执行语义综合，并且 Future Run 对真正依赖的判断仍需要回源核验。

这个成本是有意接受的，因为它避免了第二套跨 Run Domain Model、长期页面漂移和复杂一致性协议，同时保留了未来按规模逐步优化构建与检索的空间。
