# ADR-001–010 Architecture Review

* **日期**：2026-08-10
* **审阅范围**：`docs/adr/ADR-001-*.md` … `docs/adr/ADR-010-*.md` 共十份 ADR，以及 `.vibe/LEARNING_RULES.md`、`.vibe/REPORT_WRITING_GUIDE.md`
* **审阅视角**：即将根据这些 ADR 实现 V1 的工程师
* **本轮不做**：不新增设计、不修改任何 ADR。发现的修正方向供后续处理。

---

## Overall Assessment

十份 ADR 在**语义权威链**上已经闭合且严格单向：

> **Primary Papers → ResearchRun State（唯一权威，ADR-005）→ Context 投影（有界、临时、不持久化，ADR-006）→ Report（ADR-009）与 Local Wiki（ADR-010，可重建派生投影）**

逐项核对用户给定的检查点：

* **没有第二 Research Loop**。ADR-009 的 Report Generation 全部属于 `DELIVERY` 内工作（ADR-009 §「不建立 Report Revision State Machine」），问题升级复用已有 Lifecycle（DELIVERY→RESEARCH），不建立第二套循环；ADR-010 的 Wiki Build 明确"不属于 ResearchRun Lifecycle，`CLOSED` 仍然是终点，构建失败不重新打开 Run，不建立独立 Completion Gate"（ADR-010 §「Wiki 使用 Build → Validate → Publish」、§「Wiki Validation」）。**保持现状。**
* **没有第二事实源**。Report 直接读权威 Research State，Artifact 不进入 Research Domain（ADR-009 §「Report Artifact 不进入 Research Domain」）；Wiki 采用 Full Derivation（旧 Wiki prose 不作为知识输入）、"不进入 `ResearchRun.state.json`，不能成为 LandscapeFinding 的 Literature Source、Completion Check 的证据、Report 中研究判断的最终来源"（ADR-010 §「Research State 始终高于 Wiki」）。**保持现状。**
* **没有新的隐式状态机**。Wiki 不建 Promotion State / Knowledge Approval / Published Flag / Quality Score，资格从已有 Research State 推导；Wiki Page 无稳定领域身份、不需要 Merge Command / Alias Entity（ADR-010 §「只有合格的 Closed Run 进入 Wiki」、§「Wiki Page 不具有稳定领域身份」）。**保持现状。**

发现的问题集中在两类，**都不是方向性错误**：

1. **文档级矛盾**：ADR-001/002/003 写于 ADR-004 之前，其中的 Evidence 措辞与 "Research Facts" 结构枚举没有随 ADR-004 的实体收敛而修订。这是进入 ARCHITECTURE.md 前必须解决的（详见 Blocking Issues B1、B2）。
2. **authority 裁决点**：三处关键行为在 ADR 之间方向一致但机制未落定——Completion Checker 写 Investigation Gap、Delivery 完成判定与 CloseRun、Wiki 被未来 Run 消费的方式。它们不需要改架构，但必须由 ARCHITECTURE.md（或后续 ADR）显式裁决（详见 Important Clarifications C1–C3）。

结论：**语义架构闭合，方向正确；进入 ARCHITECTURE.md 之前需要少量 ADR 注记修正 + 三处裁决显式化。**

---

## Blocking Issues

> 只记录在进入 ARCHITECTURE.md 或实现前必须解决的问题。两项都源于同一个根因：早期 ADR（001–003）未随 ADR-004 的实体收敛修订，但影响面不同，分开列出。

### B1. "Evidence" 在 ADR-001/002/003 中是具体存储概念，与 ADR-004 的"V1 不建立独立 Evidence Entity"直接冲突

**涉及 ADR**：
* ADR-001：L43「解释论文内容并形成 Evidence」、L72「Evidence 引用的来源和 locator 必须能够解析」、L114「根据当前 Research Contract、Accepted Evidence、Gaps、Contradictions…做独立语义判断」、L150「当前 Evidence 是否充分」
* ADR-002：L185 检查输入「Important Accepted Evidence」、L198「检查关键结论是否有可追溯 Evidence」、L199「检查 Claim 的强度是否超过 Evidence 强度」、L202「对 load-bearing Evidence 做 targeted source inspection」
* ADR-003：L299「当前 Evidence 是否足以生成用户要求的最终成果」
* 对比 ADR-004：L95「V1 不建立独立的 Evidence Entity」、L335-339「Evidence 是知识质量约束，不一定是独立 Domain Entity」
* 对比 ADR-006：Completion Check View（L438-443）只含 Literature Landscape / Finding 摘要 / source refs，**没有 Evidence 列表**

**问题**：前五处都把 "Evidence" 当作用户可以点名、Checker 可以枚举和计数的**存储对象**（"Accepted Evidence"、"load-bearing Evidence"、"Evidence 是否充分"）。但 V1 的状态里没有这个对象——重要判断的 grounding 是以 `LiteratureSource`（`paper_ref + relation + locator`）落在 Landscape Finding / Paper Analysis 上的（ADR-004、ADR-008 §「Source Locator 同时用于 Grounding 与重新读取」）。

**为什么是实际架构问题**：实现 Completion Checker 的工程师第一条 vertical slice 就会卡住——按 ADR-002 L185/L198 去 `state.json` 里找 "Accepted Evidence" 枚举，找不到；若按 ADR-004/006 用 Landscape Finding + source refs，则 L198 的"可追溯 Evidence"和 L199 的"Claim 强度 vs Evidence 强度"需要重新翻译成"对 Finding 的 Grounding 是否可读回原文"。这不是措辞洁癖，而是**两套对象模型**，会直接决定 Checker 的输入数据结构。

**最小修正方向**：在 ADR-001/002/003 各加一行 supersession 注记（或由 ARCHITECTURE.md 开一章「术语映射」显式裁决）：
> 本 ADR 中的 "Evidence" 在 V1 中对应 Landscape Finding / Paper Analysis 上的 `LiteratureSource`（paper_ref + locator）及其可核验性；"load-bearing evidence inspection" 对应 ADR-008 `read_source` 核验；**不存在独立的 Evidence 对象**。

改动量小，但必须在 ARCHITECTURE.md 定稿前落地，否则 ARCHITECTURE.md 的 Checker 输入模型会照着 ADR-002 画。

### B2. ADR-002/003 的 "Research Facts" 结构枚举与 ADR-004 的 V1 实体清单冲突

**涉及 ADR**：
* ADR-002：L357-370 正交表「Research Facts ├── Papers ├── Evidence ├── Gaps ├── Contradictions └── Check Verdict」
* ADR-003：L254-266「Evolving Research State ├── Papers ├── Evidence ├── Gaps ├── Contradictions ├── Derived Questions └── Technical Routes」、L442-462 位置图（含 Contradictions、Derived Questions）、L70「Technical Route、Derived Question 等内容都允许随研究过程演化」
* 对比 ADR-004：L512-526 明确 **V1 不建立** Contradiction / DerivedQuestion / Claim / Consensus / Trend / Comparison / CitationMap / CandidatePaper / CuratedPaper；L184-187 用 Approach Family 取代 Technical Route

**问题**：ADR-002/003 的结构图把 Contradiction、Derived Question、Technical Route 列为 Research State 的标准成员；ADR-004 明确从 V1 实体集剔除。Technical Route 与 Derived Question 尤其危险——它们不是"可以有也可以没有"，而是 ADR-004 给出的**替代路径**（Approach Family 承载路线知识；领域未解问题进 Open Problem，Run 级未解问题进 Investigation Gap，细分问题不设独立实体）。

**为什么是实际架构问题**：按 ADR-003 的位置图建模的工程师会自然建出 `Contradiction` 和 `DerivedQuestion` 两个持久化对象、对应的 PUT/MERGE 路径、Ref 前缀和权限规则，然后在 ADR-004 的实体清单面前全部返工。这是第一 slice 的实体建模风险点。

**最小修正方向**：ADR-002/003 的结构图加一行 supersession 注记，指向 ADR-004 §「Minimal Persistent State」（或直接替换图为 ADR-004 的实体集），说明 V1 中：
* "Contradictions" → 以 Landscape Finding 之间的 `challenges` 关系表达，不设 Contradiction 实体
* "Derived Questions" → 细分的入 Investigation Gap；领域级的入 Open Problem
* "Technical Routes" → Approach Family 的组成概念

> 以上两项与"是否把 V1 实体集视为最终正确"无关——ADR-004 的实体收敛本身方向正确（无 Evidence 实体、Contradiction 用关系表达、Approach Family 取代 Technical Route，都是把对象模型压到最小）。Blocking 的唯一原因是在进入 ARCHITECTURE.md 前，ADR-001/002/003 的过时表述会主动误导实现。

---

## Important Clarifications

> 架构方向正确，但需要 ARCHITECTURE.md 统一表达或显式裁决的地方。不需要改 ADR 的结构，但必须在 ARCHITECTURE.md 里落一句明确的话。

### C1. Completion Checker 如何创建/重新打开 Investigation Gap——机制未定

**涉及 ADR**：
* ADR-004：L331「Completion Checker 可以在发现重要遗漏时创建或重新打开 Investigation Gap，然后让 Run 回到 RESEARCH」
* ADR-002：L155-159 进入 COMPLETION_CHECK 后「Researcher 暂时失去修改研究基础的权限…Search、Add Evidence、Update Gap 等会改变研究基础的动作暂时不可执行」
* ADR-005：CompletionCheck 不可变（L502-520）、SubmitCompletionCheck 是领域命令（L386）、权限由 Actor×Lifecycle×Target×Field/Command×Operation 决定（L522-580）

**问题**：ADR-004 授权 Checker 写 Gap，但机制未指定：是 Checker 直接经命令写 Gap（Checker 拥有 COMPLETION_CHECK 下对 InvestigationGap 的写权限），还是 Checker 只把 blocking gap 写进 verdict、回到 RESEARCH 后由 Researcher 依据 verdict 物化 Gap？两种路径的权限模型、状态修订顺序和 Resume 语义都不同。ADR-005 的权限表没有枚举这一种（完成裁决权的边界清晰，但 Checker 对研究基础的写权限含糊）。

**为什么需要裁决**：这是第一 slice 的 Completion Check 数据流必须写死的分支；不裁决则 Checker 实现会猜测，两条路径在审计上互相矛盾（检查期状态冻结 vs Checker 写了研究基础）。

**两个可行方向（择一写进 ARCHITECTURE.md）**：
1. **Checker 直接写**：gap 的 create/reopen 作为 SubmitCompletionCheck 的一部分、与 verdict 同一原子批次提交（符合 ADR-005 原子 Batch），检查基线 `basis_revision` 仍指检查前的修订。
2. **返回后物化**：Checker 只输出 verdict + blocking gap 描述；状态在回到 RESEARCH 后由 Researcher 经正常 PUT/MERGE 物化为 Investigation Gap。

倾向方向 1（单次原子提交、语义上更接近 ADR-004 原文），但两种都自洽，关键是**写死一种**。

### C2. Delivery 完成判定与 CloseRun 的 authority——未裁决

**涉及 ADR**：
* ADR-002：L284-285「delivery complete → CLOSED」
* ADR-005：CloseRun 是领域命令（L390-392）
* ADR-009：报告流水线完整（Narrative Plan → Compose → Editorial Integration → Fresh Editorial Review → Integrity/Citation Verification → Final Report），但**没有任何地方定义"什么算 delivery complete"、由谁判定、谁发起 CloseRun**
* 对照：Partial 路径有显式授权 USER_ACCEPT_PARTIAL（ADR-004），而完整路径没有对应的 USER_ACCEPT_COMPLETE

**问题**：ADR-002 把 "delivery complete" 当作 CLOSED 的触发条件，但整条 ADR 链里这个条件的**裁决者**缺失。Completion 阶段有独立 fresh Checker（ADR-002/006），Delivery 阶段却只有 Fresh Editor（管"文章质量"）和 Integrity Verification（管"忠实于 State"）——**没有任何组件回答"报告是否满足 Deliverable"**。是用户接受即完成？还是 Claude 声明完成 + 用户确认？还是一个 Delivery 级 gate？

**为什么需要裁决**：不裁决则 CloseRun 的触发条件无法写进 Python 的权限/命令层，Claude 可以自行"写完报告就 Close"，这与 ADR-001 的"Researcher 无权自判 DONE"精神相悖——DONE 的裁决被 Completion Checker 独立化之后，Delivery 阶段又把裁决权还给了 Researcher。

**最小方向**：ARCHITECTURE.md 明确一句——"CloseRun 由 Claude 在 Final Report 就绪后提出，经用户确认交付接受后由 Harness 执行；或在契约规定无需用户确认时由 Claude 提出、Harness 机械校验 Deliverable 存在后执行"。核心是**裁决权不落在 Researcher 单人自判**上。

### C3. Wiki 如何被未来 Run 消费，与 ADR-006 "Context 只从 ResearchRun 派生"的接驳——需要显式化

**涉及 ADR**：
* ADR-010：L331-359 Future Run 将 Wiki 作为 Prior 与 Research Lead；L345-352「Wiki 内容不能直接 PUT LandscapeFinding；正确路径为 Wiki Lead → Retain Paper → Read Source → Current Paper Analysis → Current Landscape」；L359「Wiki 是否陈旧主要影响研究效率，不影响 Current Research State 的正确性」
* ADR-006：L165-212 Context 必须始终从当前 authoritative ResearchRun 重新生成，是临时派生投影

**问题**：ADR-010 在**语义**上已经给出答案——Wiki 复用探索结果、不替代当前 Run 的证据责任，Future Run 拿到 Wiki 后必须回 Primary Paper 重新核验。但**机制**上没有把这条路径接入 ADR-006 的投影体系：Wiki 是 ResearchRun 之外的文件，它若进入 Claude 的 Context，就与 ADR-006"Context 由 view() 从当前 Run 派生"的字面规则冲突。

**为什么需要显式化**：不接驳则实现者要么绕过 view() 直接读 Wiki（制造 ADR-006 之外的第二条 Context 通道），要么完全忽略 Wiki（ADR-010 白做）。两种都偏离已定架构。

**裁决方向（写进 ARCHITECTURE.md）**：把 Wiki 消费归类为 **External Observation 通道**——与 ADR-007 的 Search Hit、ADR-008 的 Source Content 同级，是 Claude 主动拉取的外部输入，不是 view() 派生的 State 投影。Wiki Lead 必须经正常 Retain Papers 流程物化为当前 Run 的 Paper 后才能形成任何持久化判断。这样 ADR-006 的投影规则完全不被破坏，ADR-010 的路径原样成立。

> 此项严格说是"两个 ADR 的语义已经一致、只差一句接驳说明"，故列 Clarification 而非 Blocking。

---

## Safe Deferrals

> 属于实现细节或文档债务，可以推迟到 Domain Model 或实现阶段，不阻塞 ARCHITECTURE.md。

### S1. `runs/<run_id>/sources/` 目录用途未定义
ADR-005 L695-703 的 run 目录含 `sources/`，但 ADR-008 明确把 local source cache 列为"不提前设计"（L1036-1052）。V1 中 `sources/` 放什么（还是干脆不建）属于实现决定。**保持 ADR-005 现状，实现时若第一 slice 用不到就先不落盘**。

### S2. Source Access 稳定契约的命名
ADR-007 命名了 `PaperSearchProvider`，ADR-008 定义了 `inspect_source` / `read_source` 两个能力但没有命名对应的 Provider/Adapter 契约。单 provider 时不影响任何 authority 边界，命名留给 Domain Model/实现阶段。**保持现状。**

### S3. Delivery 阶段 Resume 边界一句话说明
ADR-006 说 Resume = state.json + view；ADR-009 L214-222 说 Delivery Artifact 可支持 Resume。二者关系（DELIVERY 中断后靠 state.json + `artifacts/report/` 恢复）在 ARCHITECTURE.md 补一句即可，不需 ADR 修改。**保持现状。**

### S4. ADR-004–010 均缺「参考证据」小节
ADR-001/002/003 有该小节，REPORT_WRITING_GUIDE §41 要求每个重要决策附 Reference Evidence，但 ADR-004 起连续七份缺失。这是**文档债务/可审性问题，不是架构问题**，不阻塞实现；建议在进入实现阶段前补齐，保持决策链可追溯。**本轮不改。**

### S5. User 交互细节与 UNCERTAIN 澄清通道
AuthorizePartialDelivery / CloseRun 等 User 侧命令如何由用户发起、UNCERTAIN 后由谁向用户澄清 Contract 歧义，属于 CLI/交互实现细节。ADR-002 已定 UNCERTAIN→RESEARCH 的方向，裁决路径正确。**保持现状。**

### S6. Wiki 构建中产生的 future research lead 是否落盘
ADR-010 L174 允许构建中发现的新推论"只能作为 future research lead"，但没定义 lead 是否持久化、落在哪。V1 可以忽略不落盘，需要时再设计。**保持现状。**

### S7. Wiki freshness / manifest 一致性协议
ADR-010 L285 允许 manifest 机械判断 Wiki 是否落后，L359 又声明 V1 不强一致 freshness protocol——二者已有分工（能判断、不强制），具体判定实现属实现细节。**保持现状。**

---

## Complexity Check

逐项核对十份 ADR 设计的机制，检查是否存在"为更完整而提前设计"、V1 用不到的复杂度：

* **写路径两原语 PUT/MERGE + 显式领域命令**（ADR-005）：8 个领域命令（RetainPapers / RetireLandscapeItem / MergeApproachFamily / AmendContract / RequestCompletionCheck / SubmitCompletionCheck / AuthorizePartialDelivery / CloseRun）逐一对应"跨不变量变化"，是最小集。**保持现状。**
* **三投影 view + inspect + read_source**（ADR-006/008）：每个都有明确消费方（Research/Check/Delivery View；inspect 导航、read 取文），无冗余能力。**保持现状。**
* **Fresh Editor**（ADR-009）：是第二次 fresh agent（与 Completion Checker 并列），但它是单次编辑检查、无循环、无投票、无阈值，且 ADR-009 明确拒绝多 Agent Writer/Critic 优化循环。不属于"多 Agent 系统"。**保持现状。**
* **Narrative Plan**（ADR-009）：短报告可自然退化（L76），有存在价值。**保持现状。**
* **Wiki Full Rebuild**（ADR-010）：比增量改写成本高，但这是保证"语义来源永远回到权威输入"的正确默认，且 ADR-010 已给出未来的 affected-topic 优化路径。不是过度设计。**保持现状。**
* **不提前设计清单**：ADR-007/008/010 各自列了明确拒绝的基础设施（Database/Vector DB/Embedding/Plugin Framework/Workflow Engine/Knowledge Graph/Wiki Event Store 等），互相一致、无重复基建。**保持现状。**
* **唯一可裁剪项**：`runs/<run_id>/sources/` 目录（S1）。不是架构复杂度，实现时可先不落盘。

**结论**：没有需要删除的提前设计。十份 ADR 的机制密度与"V1 = 一条最小循环 + 单向投影"的规模相符。

---

## Cross-ADR Invariants

以下不变量被多份 ADR 共同锁定，实现时任何一条被破坏都应视为架构违规，建议写入 ARCHITECTURE.md 的约束区：

1. **单一权威 State**：`ResearchRun` 是唯一一致性边界，`state.json` 是唯一权威快照；事件、Report Artifact、Wiki 都**不是**权威（ADR-005/006/009/010）。
2. **单向投影链**：Primary Papers → ResearchRun State →（Context / Report / Wiki）；派生层永不回流为事实源（ADR-006/009/010）。
3. **Researcher 无权自判 DONE**：完成裁决权在 fresh Completion Checker；Delivery 完成与 CloseRun 的裁决权不得落回 Researcher 单人自判（ADR-001/002 + C2 待显式化）。
4. **四态 Lifecycle 收敛**：RESEARCH 是唯一可变模式；COMPLETION_CHECK 冻结状态；DELIVERY 不得新增实质研究判断；CLOSED 终态。预算耗尽从不自动完成（ADR-002/003/009）。
5. **Context 是 State 的临时投影**：不持久化、不缓存、随 Lifecycle 重建；可省略内容，不可省略"内容存在"这一事实（ADR-006）。
6. **V1 无 Evidence 实体**：重要判断的 grounding 落在 Landscape Finding / Paper Analysis 的 `LiteratureSource`（paper_ref + relation + locator）；"核验证据" = `read_source(locator)` 回读原文（ADR-004/008 + B1 待注记）。
7. **Failure 不得伪装成 Empty**：搜索失败 ≠ 空结果；Source 读取失败 ≠ 空内容；Adapter 可明说做不到，不可静默降精度（ADR-007/008）。
8. **Grounding 粒度匹配判断粒度**：Claim 级判断有 locator，领域级判断回 primary paper；方向一致 ≠ 证明同一件事（ADR-004/008、REPORT_WRITING_GUIDE §3）。
9. **Claude 决定语义，Python 决定确定性**：provider 选择、读哪、综合、叙事是 Claude 的；权限、引用、ref 校验、原子替换、provenance 是 Python 的（ADR-001/005/006/007/010）。
10. **每次升级都回到同一个 RESEARCH loop**：没有第二套循环；Checker 不能借 read_source 变成新研究循环；Wiki Build 不建立 Lifecycle（ADR-008/009/010）。

---

## Recommendation

**READY AFTER MINOR ADR AMENDMENTS**

判定依据：

* **不构成 NOT READY**：十份 ADR 的语义权威链闭合、无方向性冲突、无第二 loop / 第二事实源 / 隐式状态机；B1/B2 的最小修正是注记级改动，不涉及任何架构重构；C1/C2/C3 是裁决点而非矛盾。
* **不直接判定 READY**：B1/B2 会在 ARCHITECTURE.md 定稿时主动误导（Checker 输入模型、实体建模），按审阅约定属于"进入 ARCHITECTURE.md 前必须解决"；C1/C2/C3 也需要在 ARCHITECTURE.md 里落一句显式裁决，否则第一 slice 实现仍会各自猜测。

进入 ARCHITECTURE.md 的**前置条件**：

1. 落地 B1/B2 的 supersession 注记（ADR-001/002/003 各一行，或等效的一处统一术语裁决）；
2. 在 ARCHITECTURE.md 中显式裁决 C1（Checker 写 Gap 机制）、C2（Delivery 完成判定/CloseRun authority）、C3（Wiki 作为 External Observation 通道）。

其余内容（S1–S7、Complexity Check 结论、Cross-ADR Invariants）直接作为 ARCHITECTURE.md 的输入即可，无需先改 ADR。
