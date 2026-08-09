# V1 System Architecture

**Status:** Architecture Frozen
**Scope:** V1
**Source of decisions:** ADR-001 ～ ADR-010
**Role of this document:** 描述当前系统架构真相；架构决策的历史原因与替代方案保留在对应 ADR 中。

> V1 Architecture frozen after ADR-001–010 consistency review and N1–N8 adjudication. Further changes require explicit architectural evidence rather than implementation convenience.

---

## 1. Architecture Goal

本项目构建一个面向 Claude Code 的学术论文调研 Harness。

系统接收一个开放式 Research Question，通过受控 Research Loop 逐步形成可验证、可恢复的 Research State，并最终生成带引用的领域调研报告以及可跨 Research Run 复用的 Local Wiki。

核心目标不是扩大 Claude 的搜索能力，而是控制论文调研过程，使研究：

* 可恢复；
* 可验证；
* 可积累；
* 可停止；
* 可追溯。

整体设计遵循：

> **Claude owns agency. Python owns invariants. State carries continuity.**

Claude Code 负责语义研究决策。

Python Harness 负责确定性执行、状态完整性、权限边界与持久化。

系统不试图在 Python 中实现第二套 Research Agent，也不使用复杂状态机描述 Claude 的研究步骤。

---

## 2. System Shape

V1 的核心结构保持单向：

```text
                    User
                      │
                      ▼
                 Claude Code
        Agent Runtime / Semantic Policy
              │                     ▲
              │ actions / requests  │ State Context
              ▼                     │ (bounded view from
        Python Harness ─────────────┤  Research State,
      Control / Persistence /       │  rendered by Harness)
      Determinism                   │ Research Observations
              │ read / write        │ (ephemeral results
              ▼                     │  of external I/O)
          Authoritative             │
         ResearchRun State ─────────┘
              │
        ┌─────┴─────┐
        ▼           ▼
      Report     Local Wiki

External Research I/O（由 Python Harness 执行，
结果作为 Research Observations 返回 Claude）：
  Paper Search   → PaperSearchHit[]
  Web Search     → Web Search Result
  Source Access  → SourceOutline / SourceContent
  Wiki Query     → Wiki Query Result
```

唯一权威研究状态位于 `ResearchRun`。

Report、Wiki、Context、Search Hit、Source Content 与 Event History 都不是第二事实源。

它们分别是派生产物、临时 Observation 或操作记录。

---

## 3. Authority Model

### 3.1 Claude Code

Claude Code 是 Research Loop 的主动执行者。

它负责：

* 理解用户研究任务；
* 形成 Research Contract；
* 决定搜索什么；
* 选择值得保留和阅读的论文；
* 决定阅读位置与深度；
* 解释 Primary Paper；
* 形成 Paper Analysis；
* 综合 Literature Landscape；
* 识别 Investigation Gap 与 Open Problem；
* 判断何时值得请求 Completion Check；
* 完成报告叙事组织；
* 完成 Wiki 的跨 Run 语义投影。

Claude 决定：

> **下一步研究什么。**

### 3.2 Python Harness

Python 不判断什么研究方向最重要，也不判断领域知识是否已经足够全面。

它负责：

* Lifecycle enforcement；
* Actor / Command 权限；
* stable ID 与 cross-reference；
* State Mutation；
* Aggregate validation；
* optimistic locking；
* Paper identity normalization；
* Provider failure semantics；
* Source locator validation；
* Resource limits；
* deterministic citation rendering；
* persistence；
* artifact provenance；
* atomic publication。

Python 决定：

> **某个动作是否允许发生，以及发生后 State 是否仍然合法。**

### 3.3 User

User 保留改变研究目标与终止条件的最终权力。

例如：

* 修改研究 Scope；
* 修改 Deliverable；
* 修改 Research Requirements；
* 在已知研究不足时授权 Partial Delivery。

普通完整交付不要求额外建立 User Approval Gate。

---

## 4. ResearchRun

`ResearchRun` 是一次研究任务的 Aggregate Root，也是 V1 的唯一一致性边界。

```text
ResearchRun
├── Research Contract
│   ├── Mission
│   ├── Research Requirements
│   ├── Scope
│   └── Deliverable
│
├── Lifecycle
├── Resources
│
├── Papers
│   └── Paper
│       ├── Paper Source
│       ├── Research Status
│       └── Paper Analysis
│
├── Literature Landscape
│   ├── Approach Families
│   ├── Landscape Findings
│   └── Open Problems
│
├── Investigation Gaps
└── Completion Checks
```

系统在真正进行语义判断的粒度上保存知识。

Paper Analysis 保存论文级理解。

Literature Landscape 保存领域级理解。

> **深读形成论文级理解，综合形成领域级理解。**

V1 不建立独立 Evidence、Claim、Contradiction、DerivedQuestion、Consensus、Trend 或 CitationMap Entity。

Evidence 是知识质量约束，通过来源 grounding 表达。

---

## 5. Research Contract

每个正式 Research Run 必须拥有 Research Contract。

```text
Research Contract
├── Mission
├── Research Requirements
├── Scope
└── Deliverable
```

Contract 定义：

> **这次研究为什么存在、必须研究清楚什么、研究边界在哪里，以及最终需要交付什么。**

Contract 定义 Completion Boundary，不定义研究路径。

Search Query、Paper Selection、Paper Analysis、Approach Family、Landscape Finding、Investigation Gap 与 Open Problem 都属于可以持续演化的 Research State。

Contract 默认稳定。

如果某个变化会改变 Completion Check 的 PASS 条件，则必须使用显式 Contract Amendment。

例如改变：

* Research Requirement；
* Scope；
* Deliverable；
* 会影响完成标准的 Source Requirement。

Contract Amendment 必须产生新的 `contract_revision`。

此前基于旧 Contract 获得的 Completion PASS 自动失去当前授权能力，并返回 `RESEARCH`。

历史 CompletionCheck 本身不修改。

---

## 6. Lifecycle

V1 只有四个 Lifecycle Mode：

```text
RESEARCH
COMPLETION_CHECK
DELIVERY
CLOSED
```

Lifecycle 描述控制权变化，不描述工作步骤。

### 6.1 RESEARCH

`RESEARCH` 是唯一允许普通、实质性 Research State Mutation 的模式。

Claude 可以执行：

```text
Search
Retain Paper
Inspect / Read Source
Update Paper Analysis
Update Literature Landscape
Update Investigation Gap
Request Completion Check
```

Search、Read、Deep Read、Compare、Follow Citation 等都是 Research Action，而不是 Lifecycle Phase。

### 6.2 COMPLETION_CHECK

进入 Completion Check 后，Research State 被冻结为检查基线。

普通 Research Mutation 暂停。

fresh Completion Checker 获得完成性裁决权。

它回答：

> **当前 Research State 是否已经足以满足当前 Research Contract？**

### 6.3 DELIVERY

PASS 后进入 `DELIVERY`。

普通 Research Mutation 继续关闭。

允许完成：

```text
Narrative Planning
Report Composition
Editorial Integration
Citation Verification
Artifact Rendering
```

Delivery 中允许的 Synthesis 是叙事组织与表达压缩。

领域级知识综合必须已经存在于 Literature Landscape。

如果 Delivery 过程中发现会改变“我们对领域知道什么”的问题，则必须返回 `RESEARCH`。

如果只是改变“如何把已有知识讲清楚”，则继续留在 DELIVERY。

### 6.4 CLOSED

`CLOSED` 是 Research Run 的终态。

普通 Research Mutation 不再允许。

最终结果单独记录为：

```text
COMPLETE
PARTIAL
```

Outcome 表达终止结果，不是新的 Lifecycle Mode。

---

## 7. State Mutation

Research State 有两类写入路径。

### 7.1 Local Typed Mutation

不跨越复杂系统不变量的局部变化，可以通过类型化 PUT / MERGE 表达。

例如：

```text
Update Paper Analysis
Update Landscape Finding
Update Investigation Gap
```

### 7.2 Explicit Domain Command

凡是涉及 identity、cross-reference、Contract、Lifecycle 或 Completion invariant 的操作，都必须通过显式 Domain Command。

典型语义包括：

```text
Retain Papers
Merge Approach Family
Amend Contract
Request Completion Check
Submit Completion Check
Authorize Partial Delivery
Close Run
Reopen Research / Invalidate Completion
```

具体 API 名称可以在实现阶段调整。

Architecture 冻结的是：

> **局部变化统一表达，跨不变量变化显式表达。**

一次 Claude semantic decision 对应一次原子 Mutation Batch。

Harness 对整个 ResearchRun 进行 validation，并一次提交最终状态。

不允许部分成功。

---

## 8. Structural Validity and Semantic Readiness

V1 明确区分两个问题。

### Structural Validity

Python 判断：

> **这个 Research State 在系统结构上是否合法？**

例如：

```text
Ref 是否存在
ID 是否唯一
Lifecycle transition 是否允许
Revision 是否 stale
LiteratureSource 是否引用当前 Run 的 Paper
Enum / schema 是否合法
Cross-reference 是否悬空
```

### Semantic Readiness

Completion Checker 判断：

> **这个合法的 Research State 是否已经足以满足 Research Contract？**

例如：

```text
主要路线是否覆盖充分
代表论文是否足够
是否遗漏关键方向
来源是否真正支持重要判断
是否仍存在 blocking Investigation Gap
重要冲突是否得到合理处理
```

因此：

> **Structurally valid does not mean semantically complete.**

Python 不得通过诸如以下规则偷偷建立第二套 Completion Model：

```text
每个 Approach Family 至少 N 篇论文
每个 Finding 至少 N 个来源
必须发现 N 条技术路线
Open Gap 必须为零
```

Hard limits 可以使用数字。

Semantic quality 使用 criteria 和 semantic judgment。

---

## 9. Persistence

V1 使用本地文件，不引入数据库。

概念目录：

```text
runs/
└── <run_id>/
    ├── state.json
    ├── events.jsonl
    └── artifacts/
```

`state.json` 是权威当前快照。

`events.jsonl` 用于审计与诊断，不用于 Event Sourcing，也不承担 State Reconstruction。

ResearchRun 至少维护：

```text
state_revision
contract_revision
```

写入使用 optimistic locking。

如果客户端基于旧 revision 写入：

```text
expected_revision != current_revision
```

Harness 整体拒绝该 Mutation Batch。

Python 不自动 merge Claude 的语义修改。

Claude 必须重新读取最新 State 后重新判断。

---

## 10. Context

Claude 获得系统信息分为两类：

```text
State Context
Research Observations
```

两者必须保持边界。

### 10.1 State Context

State Context 是当前 ResearchRun 的有界投影。

```text
Research State
      ↓
Lifecycle-aware Projection
      ↓
bounded view
      ↓
Claude
```

Projection 可以：

```text
选择
排序
分组
裁剪
显示 stable refs
计算确定性派生事实
```

Projection 不可以重新解释已有语义。

因此 Context Renderer 不应执行：

```text
LLM summarize all findings
```

再把新的摘要当成 State 的替代表示。

原则是：

> **Projection selects; it does not reinterpret.**

如果 Claude 需要细节：

```text
view
→ stable ref
→ inspect
```

Context 不持久化，也不建立独立 Context Cache 或 Focus State。

---

## 11. Research Observations

Research Observation 是 Claude 主动获得、但尚未成为 Current Research State 的信息。

V1 的主要 Observation 包括：

```text
PaperSearchHit
SourceOutline
SourceContent
Web Search Result
Wiki Query Result
```

它们都不自动成为 Research Fact。

典型晋升路径：

```text
Search Hit
→ Retain Paper
→ Persistent Paper

Source Content
→ Claude interpretation
→ Paper Analysis / Landscape

Web Search Result
→ Claude identifies a paper / useful lead
→ normal paper research path when applicable

Wiki Lead
→ Paper lead
→ Retain Paper
→ read_source
→ Current Research State
```

Web Search Result 不自动成为 Persistent Research State，也不自动转换为 `PaperSearchHit`。

Web Search 是独立于 Paper Search 的广泛网络发现能力（ADR-007 §Web Search 保持独立）：它不实现 `PaperSearchProvider`，也不把所有 Web Result 自动转换成 `PaperSearchHit`。V1 不为 Web Search 建立独立 Domain Entity；如果 Web Search 发现一篇论文，由 Claude 将其带入正常论文研究流程。

因此：

> **Observation 可以影响研究决策，但不能绕过 ResearchRun 写入权威知识。**

---

## 12. Paper Search

Research Loop 依赖 Paper Search capability，而不依赖具体 Provider。

Search 返回 ephemeral：

```text
PaperSearchHit[]
```

Search Hit 不进入 Persistent Research State。

只有 Claude 明确保留论文以后，Harness 才创建 Persistent Paper。

### Paper Identity

Harness 可以使用稳定外部标识进行确定性去重，例如：

```text
DOI
arXiv ID
其它明确稳定 source identity
```

如果两个 Hit 明确具有同一稳定身份，可以映射到同一个 Persistent Paper。

模糊标题相似、embedding similarity 或 semantic similarity 不能自动产生 identity merge。

> **Stable identity evidence 可以机械解决身份；semantic equivalence 必须由 semantic authority 决定。**

同样，Python 不能因为两个 Approach Family 名称很像而自动合并它们。

---

## 13. External Actions and Resource Accounting

外部资源动作必须先通过本地 action / resource validation（hard limits 检查）。

概念顺序为：

```text
local validation（hard limits 检查）
        ↓
external provider attempt 实际发起
        ↓
consumes corresponding hard action allowance
        ↓
success or explicit failure
```

消费的时刻是「外部 attempt 实际发起」，而不是「本地验证通过」或「请求被接受」。

只有同时满足以下两个条件，一次 attempt 才消耗对应 hard action allowance：

* Harness 已通过本地 action / resource validation；且
* Harness 已实际发起外部 provider attempt。

两个明确判定：

```text
local validation rejected
→ 没有发起外部 attempt
→ 不消耗 external-action allowance

external attempt started
→ timeout / rate limit / provider failure
→ 不产生新的 Research Knowledge
→ allowance 仍然被消耗
```

Provider success 与 Resource consumption 是两个独立事实。

V1 不为此实现 reservation service、分布式事务、refund protocol 或复杂计费状态机。

Hard limits 优先保证不会被静默突破。

---

## 14. Progressive Source Access

阅读被建模为 Source Access，而不是 Reading Lifecycle。

核心能力：

```text
inspect_source
read_source
```

`inspect_source` 帮助 Claude理解来源结构和可读取位置。

`read_source` 返回 Primary Source content。

SourceOutline 和 SourceContent 都是 ephemeral DTO。

系统保存：

```text
研究理解
必要的 grounding locator
```

而不是保存：

```text
阅读阶段
阅读历史
read complete
deep-read status
```

---

## 15. Source Locator

Locator 用于重新定位 Primary Source 中的重要内容。

例如：

```text
section
paragraph
table
figure
algorithm
theorem
appendix region
```

Locator 默认解释在具体 `PaperSource` 的语境中。

它不被假定为跨 Provider 永久稳定坐标。

因此旧 Run 或 Wiki 中的 Locator 在未来 Run 中首先是：

> **Source navigation hint**

如果当前 Provider 不支持该精度：

```text
UNSUPPORTED_LOCATOR
```

必须显式失败。

Harness 不允许将精确定位请求静默退化为整篇读取并假装成功。

---

## 16. Grounding

重要研究判断必须能够回到 Primary Paper。

V1 使用轻量 `LiteratureSource` 表达来源关系。

概念结构：

```text
paper_ref
relation
locator?
```

`relation` 可以表达：

```text
supports
challenges
qualifies
```

Grounding 粒度与判断粒度匹配。

Broad field pattern 可以由 Paper Reference 支撑。

需要精确核验的判断应保留足够明确的 Locator。

Provider-generated AI Summary、搜索服务解释或其它二次解释不能伪装成 Primary Source。

---

## 17. Completion Check

Researcher 不能直接宣布研究完成。

它只能请求：

```text
RequestCompletionCheck
```

### 17.1 Request

RequestCompletionCheck 必须先持久化 Completion Check request，再启动 fresh Checker。

请求至少保存：

```text
check identity
basis_revision
requester rationale
requested_at
```

`basis_revision` 指：

> **RequestCompletionCheck 成功完成后，Checker 实际读取的冻结 `state.json` revision。**

不额外建立 `research_revision`。

如果 Session 在 Checker 启动前崩溃：

```text
mode = COMPLETION_CHECK
+
pending CompletionCheck
```

即可恢复检查。

### 17.2 Checker Authority

Completion Checker 可以：

```text
读取 Completion View
检查 Contract coverage
检查 grounding
targeted read_source
识别 blocking gap
返回 PASS / CONTINUE / UNCERTAIN
```

它不能：

```text
Broad Search
Retain new Papers
修改 Paper Analysis
修改 Literature Landscape
创建新的领域知识
启动自己的 Research Loop
```

原则是：

> **Completion Checker verifies existing research semantics; Researcher expands them.**

如果 targeted inspection 暴露出新的研究需要，Checker 输出 Gap，而不是 Finding。

Completion View 默认不暴露 Budget、Action Count 或研究已经花费多少成本，避免资源状态影响 semantic completion judgment。

### 17.3 Submit

Checker 返回：

```text
PASS
CONTINUE
UNCERTAIN
```

`SubmitCompletionCheck` 原子完成：

```text
保存 Verdict
必要时创建 / reopen blocking Investigation Gaps
建立 blocking refs
执行 Lifecycle transition
```

Checker 本身没有普通 Research Mutation 权限。

一次 CompletionCheck 只能完成一次。

如果客户端在提交成功后因 crash 重试：

```text
same check identity
```

Harness 返回已有完成结果，而不是创建第二次 Check。

如果重复提交与已有 Verdict 冲突，则拒绝。

完成后的 CompletionCheck 不再修改。

---

## 18. Completion PASS Validity

PASS 不通过：

```text
current_state_revision == basis_revision
```

来判断是否仍然有效。

进入 DELIVERY 后，合法的 Delivery 行为不应因为普通 operational change 自动让 PASS 失效。

PASS 是否仍然授权当前 Delivery，由 Lifecycle / invalidation invariant 保证。

任何会改变 PASS 语义基础的行为，例如：

```text
Contract Amendment
发现 Research State 中的事实性错误
发现会改变领域判断的 Critical Gap
```

都必须通过显式 Domain Command：

```text
invalidate current completion authorization
+
DELIVERY → RESEARCH
```

两者必须原子发生。

系统不新增：

```text
completion_valid
delivery_valid
approval_valid
```

等重复 boolean 状态。

---

## 19. Delivery and Report Generation

Report 直接来源于 authoritative Research State。

```text
Research State
+ Delivery View
+ Writing Guideline
        ↓
Narrative Plan
        ↓
Compose
        ↓
Editorial Integration
        ↓
Fresh Editorial Review
        ↓
Revision
        ↓
Research Integrity / Citation Verification
        ↓
Deterministic Citation Rendering
        ↓
Final Report
```

Wiki 不作为 Report 输入。

### Narrative Authority

Narrative Plan 决定：

> **怎么讲。**

Research State 决定：

> **可以讲什么。**

Writer 在生成正文时必须回读 authoritative Research State，而不能只扩写 Narrative Plan。

因此：

```text
Narrative Plan → factual authority   X
Old Draft → factual authority        X
Editor Feedback → factual authority  X
```

所有 Delivery Artifact 都是派生内容。

### Delivery 中发现新推论

如果 Writer 发现一个新的 substantive inference，而这个推论会改变领域知识，则必须返回：

```text
DELIVERY
→ RESEARCH
```

经过 Primary Source 验证、Research State 更新和新的 Completion Check 后才能重新进入 Delivery。

---

## 20. Delivery Artifact Provenance

Delivery Artifact 保留轻量 operational provenance。

至少应能够知道它基于哪个 Completion PASS 生成，例如：

```text
basis_completion_check
```

如果该 PASS 后来因为 Contract Amendment 或 Research Integrity Failure 失效：

> 依赖它生成的 Narrative Plan、Draft 或 Final Artifact 自动成为 stale。

Stale Artifact 可以继续保留用于：

```text
诊断
人工比较
历史记录
```

但不能自动作为新 Delivery 的事实输入。

不需要建立 Artifact Lifecycle State Machine。

---

## 21. Editorial Review and Research Integrity

Fresh Editor 负责 Editorial Quality。

例如：

```text
阅读逻辑
重复
结构顺序
术语一致性
paragraph rhythm
过度标题化
paper-by-paper enumeration
模板化 prose
```

Editor 不拥有 Research Authority。

Research Integrity / Citation Verification 独立检查：

```text
Report claim 是否来自 Research State
引用是否回到正确 Paper
locator 是否可核验
文字是否超过来源支持范围
```

表达问题留在 DELIVERY。

权威研究语义问题返回 RESEARCH。

---

## 22. CloseRun

Claude 可以请求：

```text
CloseRun(outcome=COMPLETE)
```

Harness 机械检查 Delivery Preconditions，例如：

```text
mode == DELIVERY
存在当前有效 Completion PASS
Contract 要求的 Artifact 已存在
必要 deterministic checks 已完成
不存在已知需要返回 RESEARCH 的 semantic escalation
```

满足后：

```text
CLOSED
outcome = COMPLETE
```

完整交付默认不要求额外 User Approval Gate。

如果仍然存在已知重要不足，但由于预算、来源不可用或用户决策需要停止，则必须先经过：

```text
AuthorizePartialDelivery
```

然后才能：

```text
CloseRun(outcome=PARTIAL)
```

Budget exhaustion 本身不能自动产生 PARTIAL，更不能产生 COMPLETE。

---

## 23. Local Wiki

Local Wiki 是 repository-level、cross-run 的可重建知识投影。

它不属于 ResearchRun Lifecycle。

总体关系：

```text
Primary Papers
      ↓
Closed ResearchRun States
      ↓
Wiki Projection
      ↓
Local Wiki
```

Future Run：

```text
Local Wiki
      ↓
Knowledge Prior / Research Lead
      ↓
Primary Paper
      ↓
Current ResearchRun
```

Wiki 帮助 Claude 更快决定研究什么。

Primary Paper 决定 Current Run 最终能够声称什么。

---

## 24. Wiki Eligibility and Projection

V1 只使用已经完成研究并正常关闭的 eligible Research Runs 作为 Wiki 输入。

Partial Run 默认不进入 Wiki。

Wiki Projection 只提取具有跨 Run 价值的研究知识，例如：

```text
Approach Families
Landscape Findings
Open Problems
Representative Papers
Literature Sources
```

Investigation Gap、Budget、Action History、Completion reasoning 和 Report prose 默认不进入 Wiki。

Wiki Builder 应只接收需要的 Research State Projection，而不是整个 Run directory。

尤其：

> **Wiki Builder 不读取 Report 来“补知识”。**

通过输入边界减少 Prompt-only enforcement。

---

## 25. Wiki Semantics

Wiki 可以：

```text
语义归组
重复知识压缩
主题组织
冲突表达
代表论文整理
```

但不能：

```text
创建新的 authoritative Finding
latest-wins
majority-wins
自动压平冲突
建立跨 Run Domain Identity
```

不同 Run 中语义相近的 Approach Family 可以在同一页面解释，但不自动发生领域身份合并。

> **Wiki 可以合并表达，不合并身份。**

---

## 26. Wiki Build

Wiki 使用：

```text
Build
→ Validate
→ Publish
```

语义上使用 Full Derivation：

> 新 Wiki 的知识来源始终重新回到当前所有权威 eligible Research States。

旧 Wiki prose 不作为新 Wiki 的证据输入。

Full Rebuild 不要求一次 Prompt 读取所有 Runs。

构建可以按 Topic 分区执行。

未来如果 Full Rebuild 成本成为真实瓶颈，可以增加 affected-topic invalidation，但受影响页面仍然从权威 Research State 重新生成。

不能进行长期 incremental prose patch。

---

## 27. Wiki Validation and Publication

Python 执行 mechanical validation，例如：

```text
Research Ref 是否存在
Run 是否 eligible
Paper Ref 是否存在
manifest 是否完整
页面链接是否合法
publication files 是否完整
```

Claude 执行 semantic validation，例如：

```text
是否创造了输入中不存在的 substantive conclusion
是否遗漏改变判断的重要冲突
是否把条件性判断写成普遍判断
是否压缩掉影响未来研究决策的差异
```

Wiki generation 可以失败。

Wiki publication 必须原子发生。

构建在 staging location 中进行。

全部验证通过后才替换当前 published Wiki。

失败时保留上一已发布版本。

---

## 28. Failure Semantics

系统统一遵守：

> **Failure must not masquerade as Empty.**

例如：

```text
Provider failure
≠
empty search result

SOURCE_UNAVAILABLE
≠
empty content

UNSUPPORTED_LOCATOR
≠
successful coarse read

stale revision
≠
last-write-wins

Wiki build failure
≠
partial publication
```

外部失败通常不改变 Research Knowledge。

但资源事实可能变化：通过了本地 action / resource validation、并已实际发起外部 attempt 的 Search Attempt，即使失败（timeout / rate limit / provider failure），也已经消耗一次 hard action allowance（见 §13）。未通过本地验证的动作不会发起外部 attempt，因此不消耗 allowance。

---

## 29. State and Audit Failure Ordering

`state.json` 是 authoritative snapshot。

`events.jsonl` 是 audit trail。

因此：

> **Authoritative State outranks audit history.**

如果 State Mutation 已经成功提交，而后续 audit append 失败，系统必须显式报告 audit failure，但不为了保持两个本地文件强事务而回滚已经成功的 Research State。

V1 不为此引入数据库事务、Event Sourcing 或跨文件 Transaction Manager。

---

## 30. Derived Content Authority Rule

以下内容都不能成为 Research Fact 的事实源：

```text
Context rendering
Search Hit
Provider AI Summary
Narrative Plan
Draft
Editor Feedback
Final Report
Wiki prose
```

只有通过正常 Research Mutation 接受进入 `ResearchRun` 的研究理解才成为 authoritative Research State。

因此系统整体保持：

```text
Primary Source
     ↓
Research Semantics
     ↓
ResearchRun State
     ↓
Derived Artifacts
```

而不是反向传播。

---

## 31. Cross-Architecture Invariants

V1 实现必须始终满足以下约束：

1. `ResearchRun` 是单次研究唯一权威一致性边界。
2. `state.json` 是当前权威快照。
3. Researcher 不能自行写 Completion PASS。
4. `RESEARCH` 是唯一允许普通实质性 Research Mutation 的 Lifecycle Mode。
5. Completion Check 的 basis 必须是稳定冻结快照。
6. Pending Completion Check 必须在 fresh Checker 执行前持久化。
7. Completion Checker 可以验证已有知识，但不能扩展 authoritative Research Semantics。
8. `SubmitCompletionCheck` 的 Verdict、blocking Gap 与 Lifecycle transition 必须原子提交。
9. CompletionCheck 完成后不可修改；重复提交按 check identity 保持幂等。
10. Contract Amendment 或 Research Integrity Failure 必须显式使当前 Completion authorization 失效并返回 RESEARCH。
11. PASS validity 不通过 revision equality 或重复 boolean 状态表达。
12. Structural Validity 与 Semantic Readiness 相互独立。
13. Python 只强制结构不变量，不把研究质量启发式升级为 schema validity。
14. Search Hit、Source Content 和 Wiki Query Result 都是 Observation。
15. Context Projection 只能选择已有语义，不能重新解释并生成第二知识层。
16. Derived Artifact 永远不能反向成为 Research State 的事实源。
17. Stable external identity 可以机械去重；semantic equivalence 必须由 Claude 决定。
18. Locator 默认在对应 PaperSource 范围内解释，不能静默降低精度。
19. Delivery Artifact 必须能够识别其 Completion basis；basis 失效后 Artifact 自动 stale。
20. Report 和 Wiki 都直接来源于 Research State，不互相作为知识输入。
21. Wiki generation 可以失败，但失败不能污染已发布 Wiki。
22. Hard resource authorization 在外部动作之前执行；外部动作成功与资源消耗是不同事实。
23. Provider failure 与 legitimate empty result 必须严格区分。
24. 新能力默认增加 Action，而不是增加 Lifecycle Mode。
25. 能从已有权威事实推导出的状态不重复持久化。

---

## 32. V1 Explicit Non-Goals

V1 不设计：

```text
Database / ORM
Event Sourcing
Workflow Engine
Saga / Message Bus
Plugin Framework
Provider Routing Framework
Vector Database
Embedding Pipeline
RAG Infrastructure
Knowledge Graph
Global Paper Registry
Canonical Cross-Run Knowledge Entity
Evidence Entity
Claim Entity
Contradiction Entity
DerivedQuestion Entity
Reading Lifecycle
Context Cache
Report Revision State Machine
Wiki Lifecycle
Incremental Wiki Prose Merge
Multi-Agent Voting
Semantic Quality Score
```

这些能力只有在真实实现或真实规模证明当前架构不足时才重新讨论。

V1 同样暂不设计 post-close 的通用 ResearchRun integrity invalidation protocol。技术损坏的 Run 在构建时显式失败，科学观点演化通过后续有效 Research Runs 与冲突表达处理；如果未来出现必须行政性撤销某个 Closed Run 下游资格的真实需求，再单独设计最小机制。

---

## 33. First Vertical Slice

Architecture Freeze 后，第一条实现路径应尽可能短：

```text
Create ResearchRun
        ↓
Search Paper
        ↓
Retain Paper
        ↓
Inspect / Read Source
        ↓
Paper Analysis
        ↓
Landscape Finding
        ↓
Request Completion Check
        ↓
PASS
        ↓
Generate Short Report
        ↓
CloseRun
```

第一条 Slice 的目标不是覆盖所有功能，而是验证最关键的系统假设：

```text
Contract 能否稳定约束任务
State 是否足以承担 Session continuity
Paper identity 是否简单可靠
Source Access 是否可以支撑真实 grounding
Mutation 是否能够保持 Aggregate consistency
Context 是否足以驱动 Claude
Completion Authority 是否真正独立
Delivery 是否只依赖 Research State
四态 Lifecycle 是否足以吸收正常与失败路径
```

如果实现这条最小闭环仍然需要大量：

```text
awaiting_*
retry_*
revision_*
is_ready
is_complete
is_verified
is_stale
```

等隐式控制状态，应首先重新检查 Domain Model 是否违反 Architecture，而不是继续增加补丁。

---

## 34. Architecture Boundary

这份 Architecture 冻结的是：

```text
Authority
Lifecycle
State ownership
Persistence semantics
Mutation boundary
Observation boundary
Completion authority
Delivery authority
Cross-run knowledge boundary
Failure semantics
```

它不冻结：

```text
Python package layout
具体 class 名
CLI command syntax
Pydantic model 写法
JSON 字段最终命名
Provider adapter 目录结构
Markdown frontmatter
Prompt 文案
函数参数顺序
```

这些问题进入 Domain Model 和 Implementation Design 后再决定。

架构阶段的完成标准不是“提前设计所有代码”，而是：

> **让实现阶段不能在不自知的情况下替系统做高成本架构决策。**

---

## 35. Architecture Summary

V1 最终可以压缩成一个简单闭环：

```text
Research Contract
        ↓
     RESEARCH
        ↓
Authoritative Research State
        ↓
 COMPLETION_CHECK
   │           │
CONTINUE      PASS
   │           │
   └→ RESEARCH│
               ↓
            DELIVERY
               ↓
             CLOSED
```

以及两个单向派生路径：

```text
Research State → Report
Research State → Local Wiki
```

Claude 负责开放式语义探索。

Python 负责有限而刚性的系统边界。

复杂异常被表达为明确事实、失败结果或显式 Domain Command，而不是不断增加 Lifecycle State。

> **Simple loop. Rich state. Hard evidence. Criteria over magic scores.**

> **循环简单，状态丰富，证据刚性，用可检查条件代替魔法分数。**
