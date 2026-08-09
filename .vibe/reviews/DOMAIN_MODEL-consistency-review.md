# DOMAIN_MODEL ↔ ARCHITECTURE ↔ ADR-003/004/005 Consistency Review

* **日期**：2026-08-10
* **审阅范围**：`docs/DOMAIN_MODEL.md`（审阅基线 2020 行，59 节；同步后 2054 行）对照 Frozen `docs/ARCHITECTURE.md`（5236ba9 冻结）与 ADR-003 / ADR-004 / ADR-005 全文
* **审阅视角**：只找三类问题——(1) Domain Model 是否违反 Frozen Architecture；(2) 是否存在无法恢复的引用语义；(3) 是否把 semantic criterion 偷偷写成 structural invariant。**不挑字段风格。**
* **本轮动作**：审查 + 按审查结果同步修正 DOMAIN_MODEL.md。

---

## Overall Assessment

**结论：整体忠实，无硬性违反。** DOMAIN_MODEL 的 Aggregate 边界、实体集、Contract / Paper / Literature Landscape / Completion Check 语义、N1–N8 落地、Observation / Audit / Artifact 边界均与 Frozen ARCHITECTURE 及 ADR-003/004/005 一致。

发现需处理的项：

* **1 处 structural/semantic 边界问题**（ApproachFamily `representative_papers != empty` 原为无依据的 persistent structural invariant）——已同步降级为创建命令约束；
* **2 处引用语义需定死**（`basis_revision` 的 marker 语义、artifact freshness 相等性含自由文本）——已同步补充精确语义；
* **1 处 M 级补列**（§55 漏 `CitationMap`）——已同步。

另发现 1 处 **Frozen ARCHITECTURE 自身的遗留缺陷**（§31#14 漏 Web Search Result），按冻结纪律不动，登记给 ChatGPT 决定是否解冻修补。

---

## 第一类：违反 Frozen Architecture

### 逐项核对

| DOMAIN_MODEL | 依据 | 判定 |
|---|---|---|
| §2 Aggregate（唯一 ResearchRun） | ARCHITECTURE §4/§7；ADR-005 | ✅ 单 Aggregate，无独立 Repository/事务 |
| §3 Entity vs Value Object | ADR-004/005（"只有真正需要稳定身份的对象才获得 ID"） | ✅ |
| §5–6 Contract revision history | ADR-003 可追溯要求（what/when/why）+ ADR-005 `contract_revision` | ✅ 正例：history 是权威 Domain State，`basis_contract_revision` 可解析 |
| §8 ResearchRequirement | ADR-003（Requirement 是 Completion 基准）；Gap/Check 需稳定引用 | ✅ 不保存 status/is_satisfied/completion_score，满足与否归 Checker |
| §9 `required_artifacts` | ARCHITECTURE §22 CloseRun 机械前置（"Contract 要求的 Artifact 已存在"） | ✅ 机械存在性检查，不让 Python 理解 Deliverable prose |
| §10–14 Paper / identity | ADR-004；ADR-007（identity 规范化）；ARCHITECTURE §31#17 | ✅ "Python merges identity; Claude merges semantics" |
| §15 PaperAnalysis | ADR-004（Deep Reading produces Paper Analysis, not Evidence fragments） | ✅ run-specific，不拆 Evidence |
| §18 LandscapeFinding | ARCHITECTURE §8；ADR-004（不建 Comparison/Consensus/Contradiction/Trend 等） | ✅ 见第三类正例 |
| §22–25 InvestigationGap | ADR-004（不持久化 blocking=true）；Gap 不强制绑定 Action | ✅ |
| §26–31 CompletionCheck | ARCHITECTURE §17/§18/§22；ADR-002 | ✅ N2（request 先持久化）、N3（check identity 幂等）、N4（validity 不靠 revision equality）均落地 |
| §32–35 DeliveryBasis | ARCHITECTURE §18/§22；ADR-005（delivery_basis） | ✅ 无 completion_valid/delivery_valid/approval_valid 布尔 |
| §38–39 ResourceState / accounting | ARCHITECTURE §13（N1 精确语义）；ADR-005 | ✅ §39 与冻结 §13 逐字一致 |
| §40–42 Retirement / Merge | ADR-005（RetireLandscapeItem / MergeApproachFamily）；ARCHITECTURE §31#3 | ✅ 无 tombstone；merge 机械重写 refs |
| §43–45 Artifact | ARCHITECTURE §20（basis_completion_check）+ N6 | ✅ 无 Artifact Lifecycle/Status |
| §48–51 Validation Model | ARCHITECTURE §8/§31；ADR-001 | ✅ 三分类正确（见 A1） |
| §52–53 Mutation Boundary | ADR-005（PUT/MERGE + 显式命令 + 原子 Batch） | ✅ |
| §55 Non-Model | ADR-004 非实体清单 + ADR-010（无 Global* / WikiClaim）+ 无 Reading Machine | ✅ 见 M1 |
| §57 冻结边界 | ARCHITECTURE §34 | ✅ 不冻结字段拼写/命令名/模块布局 |

### A1（需 ChatGPT 确认，已同步修正）

**发现**：§17 "Structural Rule" + §49#8 定义 `representative_papers != empty` 为 **persistent structural invariant**。

* ADR-004 只写 Approach Family "**可以**保存 representative papers"（L195），从未要求非空；
* Frozen ARCHITECTURE §31 的 25 条不变量无此条；
* ARCHITECTURE §8 明文把「**每个 Approach Family 至少 N 篇论文**」列为 Python 不得偷偷建立的"第二套 Completion Model"规则；
* 该规则禁止合法中间态（Claude 先搭路线骨架、代表论文后补；或由 Wiki Lead / 外部 survey 先识别路线、再在本 Run 补代表工作）。

**同步**：降级为**创建命令的输入约束**（§17 "Creation-time Command Invariant" + §50 新增 "Create ApproachFamily"）：创建 batch 必须至少指定一个 representative Paper；但 whole-state validator 不再强制，空代表论文作为合法中间态允许，路线是否被当前研究实例化属 semantic quality。

---

## 第二类：无法恢复的引用语义

### B1（已同步修正）：`basis_revision` 的引用语义未定死

`basis_revision`（§30）与 `PartialAuthorizationBasis.basis_revision`（§34）原表述「共同使 CompletionCheck 的历史判断能够解释」，隐含"可重载 snapshot"。但：

* `state.json` 是原子替换的**单份快照**（ADR-005 §9）；V1 不保留历史 revision 快照（§30 自述），也不做 event sourcing；
* 若 reader 按字面理解"可解释"而尝试重载 basis_revision 的快照，会失败；更危险的是可能反向引入 `current_state_revision == basis_revision` 的有效性判断——直接违反 ARCHITECTURE §18 / N4。

**同步**：§30 新增 "`basis_revision` 的引用语义" 小节：它是 **Lifecycle / coherence marker，不是可重载的 snapshot 指针**；不可据此做 revision-equality 判断；历史 Check 的可解释性由三件**可恢复**事实提供——(1) Check 自身不可变的 verdict/reasons/blocking_gap_refs，(2) `basis_contract_revision` 解析到 append-only ContractRevision history，(3) COMPLETION_CHECK 期间研究语义冻结的 Lifecycle 不变量。§34 同步注明。

### B2（已同步修正）：artifact freshness 相等性含自由文本

§45 用 `artifact.delivery_basis == run.delivery_basis` 推导 freshness，但 `PartialAuthorizationBasis` 含可选自由文本 `rationale?`。artifact 副本若省略或改动了 rationale，值相等会误判为 stale——一个错误的派生结果。

**同步**：§45 定义相等性只比较 basis 的身份性字段（CompletionPassBasis → `completion_check_ref`；PartialAuthorizationBasis → `basis_revision + basis_contract_revision + authorized_at`），自由文本不参与；§34 注明。

### 正例（引用语义处理正确，无需改）

* **§25** Gap 永不物理删除 → 历史 `blocking_gap_refs` 永不 dangling（Gap 的当前 OPEN 状态与历史 Check 解耦）。
* **§29** `blocking_gap_refs` 只要求解析、不要求当前 OPEN → 后续 resolution 不 retroactively 使历史 Check 失效（与 N4 同构）。
* **§6** ContractRevision history 是权威 Domain State，不依赖 events.jsonl → `basis_contract_revision` 永久可解析（正确回答"过去 Check 的语义边界"）。
* **§20** `LiteratureSource.paper_ref` 必须指向当前 Run Persistent Paper；locator 在对应 PaperSource 语境解释 → grounding 引用可恢复。

---

## 第三类：Semantic Criterion 偷偷写成 Structural Invariant

### C1 = A1（同一发现，语义视角）

原 §17 自称「这是结构边界，不是研究充分性规则」——**这正是审阅要挑战的自我辩护**。它把「该技术路线是否已被当前研究实例化」的语义充分性，用「≥1 篇代表论文」的基数规则强制化成 whole-state 校验。且与 §51（"代表论文数量是否足够"不得进 validator）自相矛盾。已按 A1 同步。

### 正例（边界画得正确，明确不修）

* **§18** `LandscapeFinding.sources` 结构上允许为空；「Grounding sufficiency 是 semantic quality criterion，不统一简化成 `sources.length >= N`」——与 ARCHITECTURE §8（禁止"每个 Finding 至少 N 个来源"）逐字一致；空来源的合法形态（corpus-bounded absence claim）也被正确解释。
* **§28** "PASS 通常 `blocking_gap_refs = empty`" 用「通常」hedge，没有做成 persistent invariant。
* **§50 CloseRun** 只列机械前置（required_artifacts 存在、provenance 匹配、deterministic checks）；"无已知 semantic escalation"留给 Claude 的语义判断，未混入命令不变量。
* **§49#10** verdict↔completed_at 共存是原子写入的派生一致性，是真结构，不属 semantic proxy。
* **§51** 完整列出 8 类禁止进 validator 的 semantic criteria + 拒绝 5 类分数（coverage / evidence / read_depth / quality / completion）。

---

## 已同步的 DOMAIN_MODEL.md 修改

| 位置 | 修改 |
|---|---|
| §17 | "Structural Rule" → "Creation-time Command Invariant"：`representative_papers != empty` 降为创建命令输入约束；明示空代表论文为合法中间态；实例化/重要性属 semantic quality |
| §30 | 新增 "`basis_revision` 的引用语义" 小节：marker ≠ snapshot 指针；不据此做 revision-equality 判断；可解释性三来源 |
| §34 | 注明 `basis_revision` 同为 marker（交叉引用 §30）；`rationale?` 不参与 DeliveryBasis 相等性 |
| §45 | 定义 freshness 相等性只比较身份性字段，排除自由文本 |
| §49 | 移除 persistent invariant #8（ApproachFamily 非空），重编号为 1–22 |
| §50 | 新增 "Create ApproachFamily" command invariant |
| §55 | 补列 `CitationMap`（对齐 ADR-004 非实体清单） |

---

## 观察项（本次不修改）

* **ARCHITECTURE §31#14** 只列 "Search Hit、Source Content 和 Wiki Query Result"，漏了 Freeze Cleanup 已加入 §11 的 "Web Search Result"——Frozen ARCHITECTURE 自身的遗留小缺陷。按冻结纪律（further changes require explicit architectural evidence）不动，登记给 ChatGPT 决定是否解冻修补。
* §40 LandscapeFinding / OpenProblem retirement 只进 audit——因无结构化对象反向引用它们，不产生 dangling；与 Gap「永不删除」的不对称由「CompletionCheck 引用 Gap、不引用 Finding」证明合理。
* DOMAIN_MODEL §49 其余 22 条 persistent invariants 均可从 ARCHITECTURE §31 的 25 条不变量映射或直接溯源，无其它新增 semantic 代理。

---

## 结论

* **忠实性**：通过——无违反 Frozen Architecture 的硬性项。同步修正消除 1 处无依据的 persistent invariant（A1/C1）与 2 处引用语义含混（B1/B2），另补 1 处 M 级清单项。
* **待 ChatGPT 确认**：
  1. A1 的裁决方向——"创建命令约束 ≥1 代表论文、whole-state 不强制"是否接受（或更彻底地完全去掉）；
  2. 是否解冻修补 Frozen ARCHITECTURE §31#14（补 Web Search Result）。
* **不阻塞**：DOMAIN_MODEL 仍为 Domain Model Baseline，本次修正属 V1 Domain Model 阶段的正常收敛，未新增实体、未改架构 authority/control/data flow。

---

## ChatGPT Adjudication Resolution（2026-08-10）

> 本节记录 ChatGPT 对上文两个待确认项的正式裁决。保留原审查与同步历史，不将争议改写为从未发生。

### A1 — ApproachFamily Existential Grounding

**A1 REJECTED AS PROPOSED.**

`representative_papers != empty` remains a persistent structural invariant because it expresses existential grounding of a canonical ApproachFamily, not research sufficiency.

一个进入 authoritative LiteratureLandscape 的 canonical ApproachFamily，至少必须能够指向一个当前 ResearchRun 的 retained Paper。零篇 representative Paper 的路线仍然只是 research lead、hypothesis 或 Investigation Gap，不应持久化为 canonical ApproachFamily。

这条规则只回答：

> 当前 Run 中是否至少存在一个能够实例化该 Family 的文献对象？

它不回答：

```text
该 Family 是否重要
是否属于主要技术路线
代表论文数量是否足够
覆盖是否充分
是否满足 Completion
```

后者继续属于 Researcher / Completion Checker 的 semantic criterion。一次语义变化通过 atomic semantic batch 提交，因此实现不需要把空 representative paper 集合作为持久化中间态。任何移除最后一个 representative Paper 的变化必须在同一 batch 中添加 replacement，或 retire / merge 该 ApproachFamily。

同步结果：

* `docs/DOMAIN_MODEL.md` §17 恢复 persistent structural invariant；
* §49 Whole-State Validator 恢复 `ApproachFamily.representative_papers != empty`；
* §50 改为约束所有 representative-paper maintenance，不再把规则描述成 creation-only；
* 未新增 Entity、status、boolean 或 score。

### Architecture §31#14 — Observation List

Architecture §31#14 observation list corrected to match already-frozen §11 semantics; no architectural decision changed.

该修改只是 Freeze Cleanup 后的 clerical consistency correction：补齐已经在 §11 明确定义的 `Web Search Result`，并统一使用 `PaperSearchHit`、`SourceOutline`、`SourceContent` 与 `Wiki Query Result` 正式术语。Architecture authority、Lifecycle、data flow、capability 集合与 `Status: Architecture Frozen` 均未改变，也不新增 ADR。

### Resolution

* A1：原降级方案不接受；persistent structural invariant 恢复。
* Architecture §31#14：允许文书一致性修正。
* 两项待确认事项均已裁决，不再阻塞 Domain Model Baseline。
