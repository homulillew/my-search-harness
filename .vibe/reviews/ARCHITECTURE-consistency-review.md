# ARCHITECTURE.md Consistency Review

* **日期**：2026-08-10
* **审阅范围**：`docs/ARCHITECTURE.md`（1478 行，35 节）对照 `docs/adr/ADR-001-*.md` … `docs/adr/ADR-010-*.md` 十份 ADR 全文
* **审阅视角**：GPT 指令——"是否忠实于 ADR-001～010、是否意外新增决策"；通过后即可 Architecture Freeze 并进入 V1 Domain Model
* **本轮不做**：不新增设计、不修改 ARCHITECTURE.md。发现的确认事项供 ChatGPT 裁决。

---

## Overall Assessment

**结论：忠实度通过——零矛盾、零方向偏离；全部章节可追溯到 ADR 链。**

十份 ADR 逐一通读（ADR-001～003 已含 V1 术语收敛说明；ADR-004～010 原文核对），与 ARCHITECTURE.md 35 节逐条比对：

* **B1/B2（上轮审阅 Blocking）已完全吸收**。ARCHITECTURE.md 使用收敛后术语：`Evidence` 只出现在"非实体"语境（§4「V1 不建立独立 Evidence Entity。Evidence 是知识质量约束」、§32 非目标清单）；`Technical Route` / `Derived Question` 实体化 / `Research Facts` / `REVIEW` / `Reviewer` 全文为零。结构图均为 ADR-004 实体集（Approach Families / Landscape Findings / Open Problems / Investigation Gaps / Completion Checks）。
* **C1/C2/C3（上轮审阅裁决点）全部显式落地**，且方向与审阅建议一致（详见下节）。
* **没有发现"意外新增决策"中与 ADR 冲突的项**。但发现 **8 处架构层新增决策/显式裁决（N1–N8）**——它们都不在十份 ADR 正文里，而是 ADR 授权边界（"具体命令名可调整"、"不冻结具体接口"）内的机制细化，被 ARCHITECTURE 层主动写死。这类决策是 Architecture 文档的正当职责（§34 明言"冻结的是边界，不是实现细节"），但**必须显式登记给 ChatGPT 确认后再 Freeze**，避免静默带入 Domain Model。
* 另有 **6 处次要遗漏/表述问题（M1–M6）**，均不改变任何决策，不阻塞 Freeze，但建议顺手修正。

---

## C1 / C2 / C3 裁决落实情况

| 上轮裁决点 | ARCHITECTURE.md 落点 | 判定 |
|---|---|---|
| **C1** Completion Checker 如何创建/重开 Investigation Gap | §17.3：`SubmitCompletionCheck` 原子完成「保存 Verdict / 必要时创建或 reopen blocking Investigation Gaps / 建立 blocking refs / 执行 Lifecycle transition」，Checker 本身无普通 Research Mutation 权限 | ✅ 采用审阅建议方向 1（与 verdict 同批次原子提交）；与 §17.2「Checker 输出 Gap 而不是 Finding」内部自洽 |
| **C2** Delivery 完成判定与 CloseRun authority | §22：Claude 请求 `CloseRun(outcome=COMPLETE)`，Harness 机械检查 Delivery Preconditions（mode==DELIVERY、存在当前有效 PASS、Contract 要求的 Artifact 已存在、必要 deterministic checks 已完成、无已知 semantic escalation）；完整交付不要求额外 User Approval Gate；Partial 路径保留 `AuthorizePartialDelivery` | ✅ 采用审阅"最小方向"的方案 B，且无条件化（ADR-004 只定义 PARTIAL 需 USER_ACCEPT_PARTIAL，COMPLETE 路径无用户门与 ADR 一致） |
| **C3** Wiki 如何被未来 Run 消费 | §11：`Wiki Query Result` 与 `PaperSearchHit`、`SourceOutline`、`SourceContent` 并列为 Research Observation；§11 晋升路径 Wiki Lead → Retain Paper → read_source → Current Research State，与 ADR-010 L349-352 原样一致 | ✅ 按审阅建议归类为 External Observation 通道，ADR-006 投影规则未被破坏 |

---

## 逐节核对

| ARCHITECTURE.md 节 | 对应 ADR 依据 | 判定 |
|---|---|---|
| §1 Architecture Goal | ADR-001（Claude owns agency / Python owns invariants / State carries continuity） | ✅ |
| §2 System Shape | ADR-004/005（唯一权威 ResearchRun）、ADR-006/009/010（Context/Report/Wiki 均非第二事实源）、ADR-007/008/010（Observation 分类，含 C3） | ✅ 见图注 M1 |
| §3 Authority Model | ADR-001/002/003/004/005/006/009/010（Claude 语义职责清单、Python 机械职责清单均逐一可溯源）；User 段 = ADR-003（用户可改 Contract）+ ADR-004（USER_ACCEPT_PARTIAL）+ C2 裁决 | ✅ |
| §4 ResearchRun | ADR-004 Minimal Persistent State 结构图（Contract/Lifecycle/Resources/Papers/Paper Analysis/Literature Landscape/IG/CC） | ✅ 见图注 M2、M3 |
| §5 Research Contract | ADR-003（四部分、Completion Boundary、演化清单、Amendment 判定）+ ADR-005（contract_revision、旧 PASS 失效、CompletionCheck 不可变） | ✅ |
| §6 Lifecycle | ADR-002 四态；DELIVERY 动作清单 = ADR-002/009；"发现改变领域知识→RESEARCH" = ADR-004/009 | ✅ |
| §7 State Mutation | ADR-005（PUT/MERGE、显式 Domain Command、原子 Batch、整体验证） | ✅ 见图注 N5 |
| §8 Structural vs Semantic | ADR-001/002/004（Python 只判结构、Checker 判语义、无魔法分数、blocking 是 verdict reasoning） | ✅ |
| §9 Persistence | ADR-005（state.json 权威、events.jsonl 审计、optimistic locking、整体拒绝） | ✅ 见图注 M6 |
| §10 Context | ADR-006（投影不重解释、selects not reinterprets、view→inspect、不持久化、无 cache） | ✅ |
| §11 Research Observations | ADR-007/008（Search Hit、Source Content 为 Observation）+ C3（Wiki Query Result） | ✅ 见图注 M4 |
| §12 Paper Search | ADR-007（能力依赖不依赖 Provider、Hit 不入 State、Retain 才建 Paper、稳定身份机械去重、语义等价归 Claude） | ✅ |
| §13 External Actions / Resource | ADR-001/002/005/007/008（hard limit 先于外部动作、budget 只约束成本） | ✅ 见图注 N1 |
| §14 Progressive Source Access | ADR-008（Source Access 非 Reading Lifecycle、inspect_source/read_source、ephemeral DTO、保存理解不保存轨迹） | ✅ |
| §15 Source Locator | ADR-008（定位粒度、UNSUPPORTED_LOCATOR 显式失败、不静默降精度）+ ADR-010（旧 Run Locator 作导航线索） | ✅ |
| §16 Grounding | ADR-004（LiteratureSource=paper_ref+relation+locator、粒度匹配、supports/challenges/qualifies）+ ADR-008（AI Summary 非 Primary Source） | ✅ |
| §17 Completion Check | ADR-002/006（fresh Checker、冻结 State、basis_revision、View 不含 Budget/Action History）+ ADR-004（Gap 由 Checker 创建/重开）+ C1 | ✅ 见图注 N2、N3 |
| §18 PASS Validity | ADR-002/005/009（失效→显式回 RESEARCH）；"PASS 有效性不靠 revision equality / 重复 boolean"为新裁决 | ✅ 见图注 N4 |
| §19 Delivery & Report | ADR-009 流水线（Narrative Plan→Compose→Editorial Integration→Fresh Editorial Review→Integrity/Citation→Final Report）+ ADR-004（Delivery 不产生新领域知识） | ✅ 见图注 N9 |
| §20 Artifact Provenance | ADR-005（delivery_basis）+ ADR-009（Artifact 非第二事实源）；"自动 stale"语义为新规则 | ✅ 见图注 N6 |
| §21 Editorial / Integrity | ADR-009（Fresh Editor 输入与检查清单、无 Research Authority、Python 做确定性引用检查） | ✅ |
| §22 CloseRun | ADR-005（CloseRun 命令）+ ADR-004（PARTIAL 授权路径）+ C2 | ✅ |
| §23–27 Local Wiki | ADR-010 全部：资格从 State 推导（无 Promotion Flag）、只投影 AF/LF/OP/代表论文/来源、Full Derivation（旧 prose 不作输入）、Topic 分区/affected-topic invalidation 语义、Build→Validate→Publish 原子替换、机械/语义验证清单、合并表达不合并身份、manifest provenance | ✅ 见图注 M5 |
| §28 Failure Semantics | ADR-007（Provider failure≠empty）、ADR-008（SOURCE_UNAVAILABLE/UNSUPPORTED_LOCATOR 语义）、ADR-005（stale≠last-write-wins）、ADR-010（构建失败≠部分发布） | ✅ 见图注 N1 |
| §29 State vs Audit Ordering | ADR-005（state 正确性不依赖 event log、不要求事务一致、不回滚）；"显式报告 audit failure"为新要求 | ✅ 见图注 N7 |
| §30 Derived Content Authority Rule | ADR-006/007/008/009/010（Context、Hit、AI Summary、Plan、Draft、Editor Feedback、Report、Wiki prose 均非事实源） | ✅ |
| §31 Cross-Architecture Invariants（25 条） | 逐条溯源：1–4 ADR-005/002、5–6 ADR-006（6 含 N2）、7 ADR-002/006、8 ADR-005+C1、9 ADR-005（幂等含 N3）、10 ADR-005/009（显式命令含 N5）、11 见 N4、12–13 ADR-001/002、14 ADR-007/008+C3、15 ADR-006、16 ADR-006/009/010、17 ADR-007、18 ADR-008、19 见 N6、20 ADR-009/010、21 ADR-010、22 见 N1、23 ADR-007、24 ADR-002、25 ADR-002/005/006 | ✅（25 条中 24 条直接溯源，5 条含新裁决成分见 N1–N8） |
| §32 Non-Goals | ADR-005/006/007/008/009/010 拒绝清单逐一对应（Database/Event Sourcing/Workflow/Saga/Plugin/Router/VectorDB/Embedding/RAG/Knowledge Graph/GlobalPaper/Canonical Entity/Evidence/Claim/Contradiction/DerivedQuestion/Reading Lifecycle/Context Cache/Report Revision SM/Wiki Lifecycle/增量 prose/Multi-Agent Voting/Quality Score） | ✅ 见图注 N8 |
| §33 First Vertical Slice | ADR-004 Research Loop + ADR-005 命令 + ADR-009；"若需大量 awaiting_*/revision_* 隐式状态应重查 Domain Model"= ADR-002 验证方式 #12 原文精神 | ✅ |
| §34 Architecture Boundary | ADR-005/006/007/008/009/010 的"不冻结"声明（命令名、函数签名、CLI、JSON 字段、frontmatter）逐项对应 | ✅ |
| §35 Architecture Summary | ADR-002 四态闭环 + ADR-009/010 两条单向派生路径；哲学句与 Vision 一致 | ✅ |

---

## 发现

### N 类：架构层新增决策 / 显式裁决（不在任何 ADR 正文，需 ChatGPT 确认）

> 定性说明：以下各项**均不与任何 ADR 冲突**，属于"ADR 授权边界内的机制被 ARCHITECTURE 层主动写死"。按 §34 的文档定位（冻结边界、不冻结实现细节），它们是 Architecture 的正当内容；但其中 N1、N4、N8 具有一定决策分量，建议 Freeze 前逐条确认。

* **N1（§13 / §28 / §31#22）：失败的外部动作消耗 allowance**。§13「一次 Provider timeout 可以：不产生新的 Research Knowledge，但仍然消耗一次 Search allowance」、§28「失败的 Search Attempt 已消耗一次 hard action allowance」。ADR-007/008 定义了失败语义与 budget 的约束作用，但**没有定义失败是否计费**。这是一条新的资源记账规则（方向合理：防静默绕过 hard limit），需要确认。
* **N2（§17.1 / §31#6）：Completion Check request 必须先持久化再启动 Checker；崩溃恢复 = mode=COMPLETION_CHECK + pending CompletionCheck**。ADR-006 只规定"冻结 State 作为检查基线"，持久化顺序与 pending-check 恢复机制是新规定（是 ADR-005 持久化纪律的自然推论）。
* **N3（§17.3 / §31#9）：check identity 幂等重提**。同 identity 重试返回已有结果、与已有 Verdict 冲突则拒绝。ADR-005 只规定 CompletionCheck 不可变，幂等协议是新增（是"原子提交 + 不可变记录"的推论）。
* **N4（§18 / §31#11）：PASS 有效性不通过 `current_state_revision == basis_revision` 判断，由 Lifecycle / invalidation invariant 保证**。这是对 ADR-005（DELIVERY 允许精化 locator → revision 会递增）与 ADR-006（STALE_STATE fail closed）之间潜在张力的**必要裁决**——若用 revision equality 判 PASS 有效，合法 Delivery 动作会误杀 PASS。方向正确且重要，但属新增裁决。
* **N5（§7.2 / §18 / §31#10）：显式命令 `Reopen Research / Invalidate Completion`**。ADR-002/004/009 都有"DELIVERY→RESEARCH、旧 approval 失效"的语义路径，但没有命令形态；ADR-005 命令清单声明可调整，故属允许范围。注意：§7.2 清单同时**省略**了 ADR-005 清单中的 `RetireLandscapeItem`（实现阶段可恢复，非问题，仅提示）。
* **N6（§20 / §31#19）：Delivery Artifact 的 `basis_completion_check` provenance 与自动 stale 规则**。ADR-005 的 `state.json` 已有 `delivery_basis`（支持 Resume）；Artifact 级 provenance + "basis 失效则 Artifact 自动 stale、不能作新 Delivery 事实输入"是新增语义（ADR-009"Artifact 不成为第二事实源"的方向展开）。
* **N7（§29）：audit append 失败必须显式报告**。ADR-005 只规定"state 已提交则不回滚、Run 仍合法"，"显式报告 audit failure"是新操作性要求。
* **N8（§32 末段）：暂不设计 post-close 通用 ResearchRun integrity invalidation protocol**。技术损坏的 Run 在构建时显式失败；科学观点演化通过后续 Run 与冲突表达处理；未来有行政性撤销需求时再设计最小机制。这是一条**新的非目标声明**（上轮审阅 Safe Deferrals S1–S7 未覆盖此项），方向与前轮审阅精神一致，但需确认是否纳入 Freeze 范围。

### M 类：次要遗漏 / 表述问题（不改变决策，建议顺手修正）

* **M1（§2 图）**：`State Context` 箭头画为 Claude Code → State Context → Python Harness，与 ADR-006（Python 从 State 渲染 Context **给** Claude）方向相反。§10 文字正确，图易误导，建议调整箭头方向。
* **M2（§4 树）**：未画 ADR-004 结构图中的 `Operational / Action Event History` 分支。§2/§9 已覆盖 events.jsonl，不影响语义，仅结构图不完整。
* **M3（§4 / §32）**：实体剔除清单未含 ADR-004 的 `CandidateFinding` / `Comparison` / `CandidatePaper` / `CuratedPaper`（§11/§12 隐含覆盖：Observation 不自动晋升、无 Candidate 模型）。
* **M4（§11 / §2 图）**：Observation 清单未含 Web Search。ADR-007 决定 Web Search 是独立能力（`search_web`），ARCHITECTURE.md 全篇未体现该能力（不矛盾，仅未覆盖一项 ADR 决策）。
* **M5（§24）**：Wiki 投影内容未提 ADR-010 的"Paper Analysis 可作为语义投影辅助上下文（不要求整体复制）"。
* **M6（§9）**：概念目录省略 ADR-005 的 `sources/`。对应上轮审阅 Safe Deferral S1（sources/ 目录用途），省略可接受。
* **M7（§19 流水线）**：比 ADR-009 多出 `Revision` 与 `Deterministic Citation Rendering` 两步——均可在 ADR-009 找到语义依据（"Writer 可根据 Fresh Editor 的具体问题进行必要修订"、"引用解析、编号、Bibliography 完整性由 Python Harness 处理"），属步骤展开而非新决策，无需修改。

---

## 结论

* **忠实性**：通过。无矛盾、无方向偏离、无术语回潮；B1/B2 已吸收，C1/C2/C3 已按审阅方向显式落地。
* **新增决策**：N1–N8 共 8 处架构层新增/裁决，其中 N4（PASS validity）是必要裁决、N8 是新非目标，均不冲突但需 ChatGPT 显式确认；确认后**不阻塞 Architecture Freeze**。
* **次要事项**：M1–M7 不改变任何决策，M1 建议在 Freeze 前顺手修正箭头方向，其余可延后。

> **建议结论：ARCHITECTURE.md 对 ADR-001～010 忠实，可以 Freeze；Freeze 声明中附 N1–N8 登记表（本审阅第 3 节），随后进入 V1 Domain Model 阶段。**

---

## Freeze Resolution（Architecture Freeze Cleanup 追加，2026-08-10）

> 本节是 Architecture Freeze Cleanup 时追加的裁决记录，不改写上文审阅内容，原「待确认」历史完整保留。

### N1–N8 裁决结果

N1–N8 经 ChatGPT 确认，**全部 ACCEPTED**，作为 V1 Architecture adjudications 纳入冻结范围：

| # | 裁决确认 |
|---|---|
| **N1** | 接受 §13 精确语义：**只有在 Harness 已通过本地 action / resource validation、并实际发起 external provider attempt 后，该 attempt 才消耗对应 hard action allowance**。两个明确判定：`local validation rejected → 没有发起外部 attempt → 不消耗 external-action allowance`；`external attempt started → timeout / rate limit / provider failure → 不产生新的 Research Knowledge → allowance 仍然被消耗`。V1 不为此实现 reservation service、分布式事务、refund protocol 或复杂计费状态机。 |
| **N2** | 接受：Completion Check request 必须先持久化，再启动 fresh Checker。 |
| **N3** | 接受：SubmitCompletionCheck 按 check identity 幂等重提。 |
| **N4** | 接受：PASS validity 由 Lifecycle 与显式 invalidation invariant 保证，不通过 `state_revision` equality 判断。 |
| **N5** | 接受：DELIVERY → RESEARCH 通过显式 Domain Command 表达；具体命令名不冻结。 |
| **N6** | 接受：Delivery Artifact 保留轻量 `basis_completion_check` provenance；basis 失效后 Artifact 自动 stale。 |
| **N7** | 接受：audit append 失败必须显式报告，但不回滚已提交的 state。 |
| **N8** | 接受：V1 不设计通用 post-close ResearchRun integrity invalidation protocol。 |

> **N1–N8 均已作为 V1 Architecture adjudications 明确接受，不需要 ADR-011。**

### M 类处理情况

* **M1**（§2 图 `State Context` 箭头方向）——已在本次 cleanup 中修正为 Harness → Claude（State Context 由 Harness 渲染）。
* **M4**（§11 缺 Web Search）——已在本次 cleanup 中补齐：`Web Search Result` Observation、晋升路径、与 `PaperSearchHit` / `PaperSearchProvider` 的独立性声明。
* **M2 / M3 / M5 / M6 / M7**——按 cleanup 任务指令不处理，保留为后续实现阶段可选项，不阻塞 Freeze。
