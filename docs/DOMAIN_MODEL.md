# V1 Domain Model

**Status:** Domain Model Baseline
**Scope:** V1
**Architecture:** `docs/ARCHITECTURE.md` — Frozen
**Decision basis:** ADR-001 ～ ADR-010 + Architecture adjudications N1–N8 + Domain Model pressure tests
**Role of this document:** 定义 V1 Research State 的领域对象、身份、引用、持久化边界与结构不变量。Architecture 负责系统 authority、control flow 与 data flow；本文负责这些规则作用于什么领域数据。

---

## 1. Domain Model Goal

V1 Domain Model 的目标不是完整描述论文研究过程，而是保存：

> **恢复 Research Process、承载当前研究理解、执行架构不变量所需的最小权威状态。**

模型遵循四条原则：

> **Persist decisions, not trajectories.**

保存研究理解，不保存完整阅读轨迹。

> **Stable identity only where references require it.**

只有真正需要长期引用的对象才获得 ID。

> **Derived state should remain derived.**

能够从其它权威事实稳定推导出的状态不重复持久化。

> **Structural validity is not semantic readiness.**

Python 保证 State 在结构上合法；Claude 与 Completion Checker 判断研究在语义上是否充分。

---

## 2. Aggregate Boundary

V1 只有一个 Aggregate Root：

```text
ResearchRun
```

一次 Research Run 内所有权威研究状态都通过这一边界共同读取、验证和提交。

概念结构：

```text
ResearchRun
├── id
├── state_revision
│
├── contract
├── lifecycle
├── outcome?
├── resources
│
├── papers
├── literature_landscape
├── investigation_gaps
├── completion_checks
└── delivery_basis?
```

`Paper`、`LandscapeFinding`、`InvestigationGap` 等对象不是独立 Aggregate，也没有独立 Repository 或事务边界。

一次 Claude semantic decision 可以同时修改多个对象，但最终必须形成一个完整合法的 `ResearchRun`，然后原子提交。

---

## 3. Entity and Value Object

V1 使用 Entity / Value Object 区分，但不建立复杂继承体系。

### 3.1 Entities

需要稳定身份并可能被其它对象长期引用：

```text
ResearchRequirement
Paper
ApproachFamily
LandscapeFinding
OpenProblem
InvestigationGap
CompletionCheck
```

它们拥有 Run-local stable ID。

### 3.2 Value Objects

意义由字段值决定，不需要独立身份：

```text
ResearchContract
ContractRevision
Deliverable

PaperSource
PaperAnalysis

LiteratureLandscape
LiteratureSource
SourceLocator

ResourceState

CompletionPassBasis
PartialAuthorizationBasis
DeliveryBasis
```

例如：

```text
LiteratureSource
├── paper_ref
├── relation
└── locator?
```

不需要 `source_id`。

---

## 4. Stable References

V1 使用显式稳定引用表达对象关系。

概念上包括：

```text
RunRef
RequirementRef
PaperRef
ApproachFamilyRef
FindingRef
OpenProblemRef
GapRef
CompletionCheckRef
```

具体字符串格式属于 Implementation Design，不在本文冻结。

例如实现可以选择：

```text
R001
RR3
P8
AF2
LF7
OP3
IG4
CC6
```

但 Domain Model 只要求：

1. ID 在所属 ResearchRun 中唯一；
2. 已分配的 ID 不重新用于另一个领域对象；
3. 所有当前 State 中的 Ref 必须能够解析；
4. 机械 identity merge 可以重写 Ref；
5. Python 不能通过文本相似度推断 semantic identity。

---

# Research Contract

## 5. VersionedResearchContract

Research Contract 是 Completion Boundary，因此 Contract Amendment 必须具有权威历史。

V1 使用：

```text
VersionedResearchContract
├── current_revision
└── revisions
    └── ContractRevision*
```

当前 Contract 不单独复制。

权威当前值定义为：

```text
revisions[current_revision].contract
```

这样避免出现：

```text
current_contract
+
contract_history
```

两份可能漂移的事实源。

---

## 6. ContractRevision

```text
ContractRevision
├── revision
├── contract
├── reason
└── recorded_at
```

`revision` 是单调递增的 Contract revision number，同时也是该历史版本的稳定键。

不需要额外：

```text
contract_revision_id
```

初始 Contract 是 revision 1。

后续 `AmendContract` 追加新的 `ContractRevision`，不修改已有历史版本。

Contract Revision History 是 authoritative Domain State，不依赖 `events.jsonl` 才能恢复过去 Completion Check 的语义边界。

---

## 7. ResearchContract

```text
ResearchContract
├── mission
├── requirements
├── scope
└── deliverable
```

### Mission

简洁描述本次研究最终需要理解什么。

它不是 Research Plan，也不保存预期论文、路线或执行步骤。

### Scope

定义研究边界。

V1 不提前把 Scope 拆成复杂 taxonomy。

它可以表达时间范围、研究对象、来源约束与排除项，但具体 Python 表达方式留到 Implementation Design。

### Deliverable

描述最终需要交付什么。

详见 §9。

---

## 8. ResearchRequirement

`ResearchRequirement` 是 Contract 中唯一需要 stable ID 的子对象：

```text
ResearchRequirement
├── id: RequirementRef
└── statement
```

原因是 Investigation Gap、Completion reasoning 与 Context 需要稳定引用具体 Requirement。

不使用：

```text
requirements[2]
```

作为长期引用，因为 Contract Amendment 可能改变顺序。

### Requirement Identity

如果一次 Amendment 只是澄清同一 Requirement，可以继续保留其 ID。

如果 Completion Boundary 的语义要求发生实质改变，则应创建新的 Requirement ID。

判断：

> “这还是不是同一个 Requirement？”

属于 Claude / User 的语义决策。

Python 只保证 ID consistency，不根据文本相似度自动决定 Requirement identity。

Requirement 不保存：

```text
status
is_satisfied
completion_score
```

Requirement 是否已经满足，由 Completion Checker 根据当前 Research State 判断。

---

## 9. Deliverable

Deliverable 同时包含语义要求和最小机械关闭条件：

```text
Deliverable
├── description
└── required_artifacts
```

`description` 保存用户要求的语义交付内容，例如：

```text
一份带可追溯引用的领域调研报告，
包含主要技术路线、代表论文、路线比较、
主要限制和开放问题。
```

`required_artifacts` 保存 Harness 可以机械验证的 artifact kind。

V1 最小可包含：

```text
REPORT
```

它不保存：

```text
output_path
filename
Markdown heading style
workspace path
```

这些属于 Delivery Runtime。

`required_artifacts` 的作用只是使 `CloseRun` 能够确定性回答：

> Contract 要求的交付物是否存在？

而不是让 Python 理解 Deliverable prose。

---

# Papers

## 10. Paper

```text
Paper
├── id: PaperRef
├── source: PaperSource
├── research_status: PaperResearchStatus
└── analysis: PaperAnalysis?
```

Paper 是当前 ResearchRun 正式保留的研究材料。

Search Result 不是 Paper。

只有经过 Retain 操作后才创建 Persistent Paper。

---

## 11. PaperSource

`PaperSource` 回答：

> **这是哪一篇论文？**

概念字段：

```text
PaperSource
├── title
├── authors
├── publication_year?
├── doi?
├── arxiv_id?
├── canonical_url?
└── other_identifiers?
```

具体 Provider 不属于 Paper Identity。

以下内容：

```text
DeepXiv
OpenAlex
Web Search
Semantic Scholar
```

表示发现或访问路线，而不是 Persistent Paper Identity。

### Stable Identifier

Harness 可以机械规范化明确稳定标识，例如：

```text
DOI
arXiv ID
canonical paper URL
```

两个 Persistent Paper 不能拥有明显冲突的 normalized stable identity。

模糊标题、作者相似度或 embedding similarity 不能自动产生 identity merge。

---

## 12. Paper Identity Enrichment

`Paper.source` 不是普通 Researcher 可任意 PUT 的字段。

但随着研究进行，bibliographic identity 可能被补全。

例如：

```text
P3 initially:
arxiv_id = A
doi = None

later:
doi = D
```

如果新 identifier 不产生冲突，可以通过 identity-aware operation 补全。

如果新 identifier 与另一个 Persistent Paper 相撞：

```text
P3.doi = D
P8.doi = D
```

普通更新必须失败，并进入显式 Paper identity reconciliation。

具体命令名不冻结。

---

## 13. Paper Identity Merge

如果两个 PaperRef 被稳定 identity evidence 确认是同一篇论文，Harness 可以执行显式 Paper merge。

例如：

```text
P8 → P3
```

Python 可以机械处理：

```text
bibliographic identifiers
ApproachFamily.representative_papers
LiteratureSource.paper_ref
其它结构化 PaperRef
```

如果两个 Paper 都存在不同 `PaperAnalysis`，Python 不能自动进行语义合并。

Claude 必须提供最终 reconciled PaperAnalysis。

原则：

> **Python merges identity and references; Claude merges research semantics.**

V1 不建立：

```text
DuplicatePaper
PaperAlias
CanonicalPaper Entity
PaperTombstone
IdentityConflict Entity
```

---

## 14. PaperResearchStatus

V1 只需要：

```text
ACTIVE
RETIRED
```

它回答：

> 当前 Run 是否仍值得主动投入研究成本？

而不是：

> 论文读到哪个阶段？

因此不使用：

```text
DISCOVERED
ABSTRACT_READ
METHOD_READ
DEEP_READ
ANALYZED
VERIFIED
COMPLETE
```

`RETIRED` Paper 仍然存在于 ResearchRun 中，也可以继续作为已有 Finding 的来源。

它只表示：

> 当前 Researcher 不再计划主动投入研究成本。

---

## 15. PaperAnalysis

`PaperAnalysis` 保存：

> **这篇论文对当前 Research Run 意味着什么。**

它属于具体 Run，不是通用论文摘要。

V1 最小语义结构：

```text
PaperAnalysis
├── summary
├── contributions
├── key_results
├── limitations
├── relevance_to_run
└── key_locators
```

`key_locators` 保存值得 Resume 或 targeted reread 的关键位置。

PaperAnalysis 不要求每一句话都绑定一个 locator，也不拆成 Evidence fragments。

同一论文在两个 ResearchRun 中可以拥有完全不同的 PaperAnalysis。

---

# Literature Landscape

## 16. LiteratureLandscape

`LiteratureLandscape` 是当前领域级理解的容器：

```text
LiteratureLandscape
├── approach_families
├── findings
└── open_problems
```

它本身没有 ID、status 或 revision。

版本由整个 `ResearchRun.state_revision` 表达。

---

## 17. ApproachFamily

```text
ApproachFamily
├── id: ApproachFamilyRef
├── name
├── core_idea
└── representative_papers: set[PaperRef]
```

ApproachFamily 只表达：

> **这是什么技术路线，以及哪些论文是其代表工作。**

优势、限制、趋势、比较和争议不进入 ApproachFamily 字段，而进入 LandscapeFinding。

### Creation-time Command Invariant

创建 ApproachFamily 的 batch 必须至少指定一个当前 Run 的 representative Paper：

```text
representative_papers != empty
```

（作为创建命令的输入约束）

原因是 Claude 只有在已经识别出至少一篇代表论文时，才应当声称存在一个技术路线。

它不是 whole-state persistent structural invariant：

* ApproachFamily 允许作为合法中间态存在——例如代表论文尚未补齐的路线骨架；
* 一个技术路线是否真正被当前研究实例化、是否重要，属于 semantic quality，由 Researcher 与 Completion Checker 判断。

Python 不要求：

```text
至少 3 篇论文
至少 N 个来源
```

这类充分性数量标准。

---

## 18. LandscapeFinding

```text
LandscapeFinding
├── id: FindingRef
├── statement
├── approach_refs: set[ApproachFamilyRef]
└── sources: set[LiteratureSource]
```

`statement` 可以表达：

* 跨论文比较；
* 共识；
* disagreement；
* trend；
* limitation；
* trade-off；
* conditional conclusion。

V1 不分别建立：

```text
Comparison
Consensus
Contradiction
Trend
RouteLimitation
```

Entity。

### `approach_refs`

可以为空。

如果 Finding 明确涉及某些 Approach Family，应通过显式 Ref 表达，而不是依赖 Python 从 statement 自然语言解析。

这使 `MergeApproachFamily` 可以机械重写引用。

### `sources`

结构上允许为空。

原因是一些合法的 corpus-bounded synthesis，例如：

> 在本次 Scope 覆盖的代表论文中，我们没有发现……

不能由某一篇论文单独作为支持来源。

因此：

> **Grounding sufficiency 是 semantic quality criterion，不统一简化成 `sources.length >= N` 的 schema rule。**

重要 Finding 是否拥有足够来源，由 Researcher、Completion Checker 与 Research Integrity Check 判断。

---

## 19. OpenProblem

```text
OpenProblem
├── id: OpenProblemRef
├── statement
├── approach_refs: set[ApproachFamilyRef]
└── sources: set[LiteratureSource]
```

OpenProblem 表示：

> **当前文献领域本身仍未解决的重要问题。**

它不拥有：

```text
status = OPEN
resolved = false
```

因为 unresolved 已经是它作为 OpenProblem 存在的语义。

OpenProblem 的来源充分性同样由 semantic quality 判断，而不是统一的固定来源数量规则。

---

## 20. LiteratureSource

```text
LiteratureSource
├── paper_ref: PaperRef
├── relation: SourceRelation
└── locator: SourceLocator?
```

`paper_ref` 必须指向当前 ResearchRun 的 Persistent Paper。

V1 `SourceRelation`：

```text
SUPPORTS
CHALLENGES
QUALIFIES
```

不使用：

```text
confidence_score
evidence_strength
source_id
```

Wiki Ref、Report Ref 或其它跨 Run Ref 不能直接进入 `LiteratureSource.paper_ref`。

---

## 21. SourceLocator

```text
SourceLocator
├── kind
└── value
```

例如：

```text
kind = "section"
value = "4.2"
```

或者：

```text
kind = "table"
value = "Table 3"
```

V1 不冻结 provider-specific locator vocabulary。

Locator 在对应 PaperSource / Source Access capability 的语境中解释。

它不是跨 Provider 永久坐标。

如果 Provider 不支持请求精度，应显式失败，而不是静默降低定位精度。

---

# Investigation Gaps

## 22. InvestigationGap

```text
InvestigationGap
├── id: GapRef
├── description
├── requirement_refs: set[RequirementRef]
├── approach_refs: set[ApproachFamilyRef]
└── resolution?
```

InvestigationGap 表示：

> **当前 Research Run 自己还没有研究清楚、且值得继续追踪的问题。**

它与 OpenProblem 不同：

```text
InvestigationGap
= 我们还没弄清

OpenProblem
= 我们已经弄清领域本身还没解决
```

---

## 23. Gap State Is Derived

InvestigationGap 不保存 `state` enum。

其当前状态由：

```text
resolution is None
→ OPEN

resolution exists
→ RESOLVED
```

推导。

Resolve：

```text
resolution = "..."
```

Reopen：

```text
resolution = None
```

因此 V1 不持久化：

```text
GapState
is_open
is_resolved
blocking
```

`blocking` 只属于某次 CompletionCheck 的 reasoning。

---

## 24. Gap References

`requirement_refs` 可以为空。

探索式 Research Gap 不必强制来源于某个 Requirement。

`approach_refs` 也可以为空。

所有当前 `requirement_refs` 必须引用 **当前 active Contract Revision** 中存在的 Requirement。

如果 Contract Amendment 删除某个 Requirement，Harness 可以机械移除当前 Gap 对该 Requirement 的 obsolete ref。

它不能因此自动：

```text
resolve gap
delete gap
```

因为 Requirement 被删除不等于研究问题已经解决。

---

## 25. InvestigationGap Is Never Physically Deleted

InvestigationGap 一旦进入 ResearchRun，就不物理删除。

原因是历史 CompletionCheck 可以长期引用它：

```text
CompletionCheck.blocking_gap_refs
```

因此 Gap 通过：

```text
resolution None / non-None
```

表达当前状态，而不是从 State 中删除。

这样历史 CompletionCheck 不会产生 dangling GapRef。

---

# Completion Check

## 26. CompletionCheck

```text
CompletionCheck
├── id: CompletionCheckRef
├── basis_revision
├── basis_contract_revision
│
├── requested_at
├── requester_rationale
│
├── verdict?
├── reasons
├── blocking_gap_refs
└── completed_at?
```

CompletionCheck 是 append-oriented immutable historical judgment。

新的检查创建新的 CompletionCheck。

已经完成的 CompletionCheck 不修改。

---

## 27. Completion Check Status Is Derived

CompletionCheck 不保存：

```text
status = REQUESTED | COMPLETED
```

其状态由 Verdict 推导：

```text
verdict is None
→ pending

verdict exists
→ completed
```

结构关系：

```text
verdict is None
↔
completed_at is None
```

以及：

```text
verdict exists
↔
completed_at exists
```

这样避免 `status` 与 `verdict` 漂移。

---

## 28. CompletionVerdict

V1 Verdict：

```text
PASS
CONTINUE
UNCERTAIN
```

完成后的 Check 应保存具体 `reasons`。

### PASS

表示当前 Research State 在语义上足以满足当前 Contract。

通常：

```text
blocking_gap_refs = empty
```

### CONTINUE

表示仍有阻止交付的研究缺口。

`SubmitCompletionCheck` 原子地创建或 reopen 对应 InvestigationGap，并保存：

```text
blocking_gap_refs
```

### UNCERTAIN

表示当前边界无法安全做出 PASS / CONTINUE，例如 Contract 本身需要用户澄清。

它不强制创建 InvestigationGap。

---

## 29. Blocking Gap References Are Historical

完成后的：

```text
CC7.blocking_gap_refs = {IG4}
```

表示：

> IG4 在 CC7 作出 Verdict 时是 blocking gap。

之后：

```text
IG4.resolution != None
```

CC7 仍然完全合法。

因此 Persistent Whole-State Validation 只要求：

```text
blocking_gap_refs resolve
```

不要求它们当前仍然 OPEN。

“Submit CONTINUE 时 blocking Gap 必须 OPEN”属于 Command invariant，不是永久 State invariant。

---

## 30. Completion Basis

`basis_revision` 表示：

> RequestCompletionCheck 成功完成时，Checker 开始检查的 ResearchRun revision。

`basis_contract_revision` 表示：

> 该 Check 使用的 Contract revision。

它们共同使 CompletionCheck 的历史判断能够解释。

V1 不因此保存每一个 `state_revision` 的完整历史 snapshot。

在 `COMPLETION_CHECK` 中，Contract、Paper Analysis、Literature Landscape 与 Investigation Gap 的普通 Research Mutation 被禁止，因此研究语义 basis 保持冻结。

targeted Source Access 可能更新 ResourceState，并使整体 `state_revision` 前进，这不自动改变 Checker 的研究语义 basis。

V1 不新增：

```text
research_revision
completion_snapshot_store
```

### `basis_revision` 的引用语义

`basis_revision` 是 **Lifecycle / coherence marker**（检查起点对应的 state revision），不是可重载的 state snapshot 指针：

* V1 不保留、也不重建 `basis_revision` 对应时刻的完整 State snapshot（`state.json` 只有当前一份快照，原子替换）；
* 因此不能用 `current_state_revision == basis_revision` 判断 Completion Check 或 PASS 是否仍有效（ARCHITECTURE §18：PASS validity 由 Lifecycle 与显式 invalidation invariant 保证，不靠 revision equality）；
* 历史 CompletionCheck 的可解释性由三件可恢复事实提供：
  1. Check 自身不可变的 `verdict` / `reasons` / `blocking_gap_refs`（§26–29）；
  2. `basis_contract_revision` 解析到 append-only ContractRevision history（§6，权威 Domain State，不依赖 events.jsonl）；
  3. `COMPLETION_CHECK` 期间研究语义冻结的 Lifecycle 不变量（§31 pending 唯一 + §27 状态推导）。

---

## 31. Pending Completion Check

当：

```text
lifecycle = COMPLETION_CHECK
```

必须存在且只存在一个当前 pending CompletionCheck：

```text
verdict = None
```

这样 Session crash 后可以恢复：

```text
COMPLETION_CHECK
+
pending check
→ restart fresh Checker
```

其它 Lifecycle Mode 不允许存在 pending CompletionCheck。

---

# Delivery Authorization

## 32. DeliveryBasis

`DeliveryBasis` 回答：

> **为什么当前 ResearchRun 合法地处于 DELIVERY，或为什么它后来能够合法 CLOSED？**

它是 tagged Value Object：

```text
DeliveryBasis
=
CompletionPassBasis
|
PartialAuthorizationBasis
```

不是独立 Entity。

---

## 33. CompletionPassBasis

正常完整交付：

```text
CompletionPassBasis
└── completion_check_ref
```

该 Ref 必须指向：

```text
completed CompletionCheck
+
verdict = PASS
```

不额外保存：

```text
completion_valid
approval_valid
```

当前授权是否有效由 Lifecycle 与显式 invalidation path 保证。

---

## 34. PartialAuthorizationBasis

部分交付由 User 显式授权。

```text
PartialAuthorizationBasis
├── basis_revision
├── basis_contract_revision
├── authorized_at
└── rationale?
```

它表达：

> User 接受哪个 Research State / Contract revision 作为 Partial Delivery 的授权基础。

`basis_revision` 与 CompletionCheck 的 `basis_revision` 一样是 Lifecycle / coherence marker，不是可重载的 snapshot 指针（见 §30）。授权记录的语义由授权时点、ContractRevision history 与 Lifecycle 不变量共同解释。

`rationale?` 是自由文本，不参与 DeliveryBasis 的相等性判断。

V1 不建立：

```text
PartialAuthorization Entity
Approval Lifecycle
Approval Status
```

---

## 35. DeliveryBasis Lifecycle Invariant

```text
RESEARCH
→ delivery_basis = None

COMPLETION_CHECK
→ delivery_basis = None

DELIVERY
→ delivery_basis required

CLOSED
→ delivery_basis retained
```

返回 `RESEARCH` 时，当前失效的 DeliveryBasis 被清空。

进入 `CLOSED` 后保留 DeliveryBasis，作为：

> Run 为什么合法关闭的 closure provenance。

---

# Run Lifecycle and Outcome

## 36. LifecycleMode

唯一 Lifecycle Enum：

```text
RESEARCH
COMPLETION_CHECK
DELIVERY
CLOSED
```

Domain Model 不增加：

```text
SEARCHING
READING
WAITING_REVIEW
REPORTING
RETRYING
FAILED
```

Lifecycle 只能通过 Domain Command 变化，不能普通 PUT。

---

## 37. RunOutcome

```text
RunOutcome
=
COMPLETE
|
PARTIAL
```

约束：

```text
lifecycle != CLOSED
→ outcome = None
```

以及：

```text
lifecycle = CLOSED
→ outcome required
```

`COMPLETE` 需要由 `CompletionPassBasis` 支撑。

`PARTIAL` 需要由 `PartialAuthorizationBasis` 支撑。

因此不保存：

```text
is_closed
is_complete
is_partial
```

---

# Resource State

## 38. ResourceState

ResourceState 是 operational fact，不是 Research Knowledge。

概念上：

```text
ResourceState
├── limits
└── usage
```

它只需要支撑：

* hard limit authorization；
* usage accounting。

不包含：

```text
provider health
retry state
fallback state
semantic sufficiency
```

---

## 39. External Attempt Accounting

只有：

```text
local action/resource validation passed
+
external provider attempt actually started
```

后，该 attempt 才消耗相应 hard action allowance。

因此：

```text
local validation rejected
→ no external attempt
→ no allowance consumption
```

而：

```text
external attempt started
→ timeout / rate limit / provider failure
→ allowance consumed
```

Provider success 与 Resource consumption 是两个不同事实。

---

# Retirement and Merge Semantics

## 40. Landscape Item Retirement

`LandscapeFinding` 与 `OpenProblem` 表示 current canonical field understanding。

如果 Claude 判断某个对象已经不再属于当前领域理解，可以通过显式 retirement operation 将其从 canonical Landscape 移除。

不保存：

```text
status = RETIRED
```

其历史存在进入 audit history。

---

## 41. ApproachFamily Merge

如果两个 ApproachFamily 语义上应该合并：

```text
AF3 → AF2
```

必须由 Claude 显式提出。

Harness 机械执行：

```text
union representative papers
rewrite all structured ApproachFamilyRefs
remove AF3
```

Python 不根据名称或 embedding similarity 自动决定 merge。

---

## 42. ApproachFamily Retirement

ApproachFamily 可能被：

```text
LandscapeFinding.approach_refs
OpenProblem.approach_refs
InvestigationGap.approach_refs
```

引用。

因此不能直接删除并留下 dangling refs。

如果是 identity merge，Harness 可以机械重写 refs。

如果只是 semantic retirement，Claude 必须在同一个 atomic semantic batch 中处理所有受影响的领域语义。

Python 不能简单地从所有对象中自动删除该 Ref，因为自然语言 statement 可能仍然依赖这个技术路线。

---

# Artifact Boundary

## 43. Delivery Artifact Is Not Domain State

Report、Narrative Plan、Draft 等 Delivery Artifact 不进入：

```text
ResearchRun
```

它们保存在 Delivery Runtime / artifact filesystem。

ResearchRun 不建立：

```text
Artifact Entity
Artifact Lifecycle
Artifact Status
```

删除 Report 不会破坏 Research State。

Report 可以从 Research State 重新生成。

---

## 44. Artifact Provenance

Delivery Artifact 必须保存轻量 provenance：

```text
delivery_basis
```

它使用与 ResearchRun 相同的 `DeliveryBasis` Value Object。

例如：

```text
Report A
delivery_basis = CompletionPassBasis(CC8)
```

或者：

```text
Report B
delivery_basis = PartialAuthorizationBasis(...)
```

---

## 45. Artifact Freshness Is Derived

Artifact 不持久化：

```text
stale = true
```

当前 freshness 由：

```text
artifact.delivery_basis
==
run.delivery_basis
```

推导。

相等性只比较 basis 的身份性内容：

```text
CompletionPassBasis        → completion_check_ref
PartialAuthorizationBasis  → basis_revision + basis_contract_revision + authorized_at
```

自由文本字段（如 `rationale?`）不参与相等性，避免同一授权的 Artifact 副本因 prose 差异被误判为 stale。

如果 Delivery 返回 RESEARCH：

```text
run.delivery_basis = None
```

旧 Artifact 自动 stale。

如果之后产生新的 PASS：

```text
run.delivery_basis = CompletionPassBasis(CC9)
```

旧 Artifact 基于 CC8，因此仍然 stale。

不需要 Artifact 状态机。

---

# Non-Persistent Research Inputs

## 46. Research Observations

以下是强类型 Runtime DTO，但不是 authoritative Research State：

```text
PaperSearchHit
Web Search Result
SourceOutline
SourceContent
Wiki Query Result
```

它们可以影响 Claude 的研究决策，但不能直接成为 Domain Fact。

晋升必须经过显式 semantic action。

例如：

```text
PaperSearchHit
→ Retain Paper
→ Persistent Paper
```

以及：

```text
Wiki Lead
→ identify Primary Paper
→ Retain / Read
→ Claude interpretation
→ Current Research State
```

---

## 47. Audit History

以下执行事实进入：

```text
events.jsonl
```

例如：

```text
Search attempt
Source read
Provider failure
Paper retained
Approach Family merged
Gap reopened
Mutation committed
Resource usage
```

它们不是 ResearchRun Domain Objects。

当前 Domain State 保存 current truth。

Audit History 保存 evolution。

V1 不从 Event Log 重建 current State。

---

# Validation Model

## 48. Three Kinds of Invariants

Domain Model 必须严格区分：

### Persistent Structural Invariant

任何合法 `state.json` 始终满足。

### Command / Transition Invariant

仅在某个 Domain Command 执行时满足。

### Semantic Criterion

属于 Claude / Completion Checker 的开放式判断，不能进入 deterministic schema validation。

这是避免 Domain Model 重新膨胀成规则系统的关键边界。

---

## 49. Persistent Structural Invariants

V1 Whole-State Validator 至少检查：

1. 所有 Entity ID 在其命名空间内唯一；
2. 已使用 stable ID 不被重新赋予不同对象；
3. 所有当前 Domain Ref 可以解析；
4. `current_contract_revision` 指向存在的 ContractRevision；
5. Contract Revision number 单调且不可修改历史版本；
6. 当前 Gap 的 RequirementRef 只指向当前 Contract Revision 的 Requirement；
7. LiteratureSource.paper_ref 指向当前 Run Paper；
8. InvestigationGap 一旦创建不物理删除；
9. `resolution is None` 表示 Open Gap，存在 resolution 表示 Resolved Gap；
10. CompletionCheck 的 `verdict` 与 `completed_at` 同时存在或同时不存在；
11. completed CompletionCheck 不再修改；
12. `basis_contract_revision` 必须指向存在的 ContractRevision；
13. CompletionCheck.blocking_gap_refs 必须解析到存在的 Gap；
14. `COMPLETION_CHECK` 恰好存在一个 pending CompletionCheck；
15. 其它 Lifecycle Mode 不存在 pending CompletionCheck；
16. `DELIVERY` 必须存在 DeliveryBasis；
17. `RESEARCH` / `COMPLETION_CHECK` 不存在 DeliveryBasis；
18. `CLOSED` 必须存在 RunOutcome 与 DeliveryBasis；
19. `COMPLETE` closure 使用 CompletionPassBasis；
20. `PARTIAL` closure 使用 PartialAuthorizationBasis；
21. CompletionPassBasis 必须引用 completed PASS CompletionCheck；
22. 非 CLOSED Run 不保存 RunOutcome。

这些规则只判断 State 是否结构合法。

它们不判断研究质量。

---

## 50. Command / Transition Invariants

典型 Command invariant 包括：

### Retain Paper

* 输入 Observation 不能直接写入 Papers；
* stable identifier 先规范化；
* 明确 duplicate 不创建第二 Paper identity。

### Paper Identity Reconciliation

* stable identity evidence 必须一致；
* 所有 PaperRef 原子重写；
* 两份非空 PaperAnalysis 不由 Python 自动融合。

### Create ApproachFamily

* 创建命令必须至少指定一个 representative Paper（§17）；
* 该约束只作用于创建命令的输入，不成为 whole-state persistent invariant。

### MergeApproachFamily

* Claude 显式决定 merge；
* 所有 structured refs 原子重写；
* Final State 不允许 dangling refs。

### AmendContract

* append 新 ContractRevision；
* 更新 current revision；
* 清理 current Gap 中 obsolete RequirementRef；
* 失效当前 Delivery authorization；
* 必要时返回 RESEARCH。

### RequestCompletionCheck

* 仅从合法 RESEARCH 发起；
* 创建 pending CompletionCheck；
* 记录 basis_revision / basis_contract_revision；
* 进入 COMPLETION_CHECK；
* request 先持久化，再运行 fresh Checker。

### SubmitCompletionCheck

* 只完成当前 pending Check；
* 同 check identity 重试保持幂等；
* conflicting resubmission 拒绝；
* CONTINUE 原子创建/reopen blocking Gap；
* Verdict 与 Lifecycle transition 同批提交。

### AuthorizePartialDelivery

* User 是授权来源；
* 保存 basis_revision / basis_contract_revision；
* 建立 PartialAuthorizationBasis；
* 进入 DELIVERY。

### Reopen Research

* 当前 DeliveryBasis 失效；
* 原子清空 DeliveryBasis；
* 返回 RESEARCH。

### CloseRun

* mode 必须为 DELIVERY；
* current DeliveryBasis 合法；
* Contract.required_artifacts 均存在；
* Artifact provenance 与 current DeliveryBasis 匹配；
* deterministic delivery checks 通过；
* 设置 CLOSED + matching RunOutcome。

---

## 51. Semantic Criteria

以下内容不得进入 Python structural validator：

```text
主要技术路线是否覆盖充分
代表论文数量是否足够
一条 Finding 的来源是否语义充分
一个 Gap 是否应该阻塞 Completion
某篇 Paper 是否已经“读够”
某个 Approach Family 是否真正重要
当前研究是否应 PASS
Report 是否讲得足够好
```

同样不建立：

```text
coverage_score
evidence_score
read_depth
quality_score
completion_score
```

Hard resource limits 使用数字。

Semantic research quality 使用 criteria 与 semantic judgment。

---

# Mutation Boundary

## 52. Local Mutation vs Domain Command

普通局部研究变化可以通过 typed PUT / MERGE 表达。

例如：

```text
PUT Paper.analysis

PUT LandscapeFinding.statement

MERGE LandscapeFinding.sources

PUT InvestigationGap.resolution
```

涉及以下内容的变化必须使用显式 Domain Command：

```text
identity
cross-reference rewrite
Contract
Lifecycle
Completion authority
Delivery authority
closure
```

具体命令名不在 Domain Model 冻结。

冻结的是边界。

---

## 53. Atomic Semantic Batch

一次 Claude semantic decision 可以同时产生：

```text
PaperAnalysis
ApproachFamily
LandscapeFinding
InvestigationGap
```

多个变化。

它们作为一个 Mutation Batch：

```text
load current ResearchRun
→ verify expected_revision
→ apply proposed mutations
→ validate local invariants
→ validate refs
→ validate whole ResearchRun
→ atomic save
```

任何一步失败：

> 整批不提交。

---

# Conceptual State Shape

## 54. V1 Conceptual Schema

```text
ResearchRun
│
├── id
├── state_revision
│
├── contract
│   ├── current_revision
│   └── revisions*
│       ├── revision
│       ├── contract
│       │   ├── mission
│       │   ├── requirements*
│       │   │   ├── id
│       │   │   └── statement
│       │   ├── scope
│       │   └── deliverable
│       │       ├── description
│       │       └── required_artifacts*
│       ├── reason
│       └── recorded_at
│
├── lifecycle
├── outcome?
├── resources
│
├── papers*
│   ├── id
│   ├── source
│   ├── research_status
│   └── analysis?
│
├── literature_landscape
│   ├── approach_families*
│   │   ├── id
│   │   ├── name
│   │   ├── core_idea
│   │   └── representative_papers*
│   │
│   ├── findings*
│   │   ├── id
│   │   ├── statement
│   │   ├── approach_refs*
│   │   └── sources*
│   │
│   └── open_problems*
│       ├── id
│       ├── statement
│       ├── approach_refs*
│       └── sources*
│
├── investigation_gaps*
│   ├── id
│   ├── description
│   ├── requirement_refs*
│   ├── approach_refs*
│   └── resolution?
│
├── completion_checks*
│   ├── id
│   ├── basis_revision
│   ├── basis_contract_revision
│   ├── requested_at
│   ├── requester_rationale
│   ├── verdict?
│   ├── reasons*
│   ├── blocking_gap_refs*
│   └── completed_at?
│
└── delivery_basis?
```

---

# Explicit Non-Model

## 55. Concepts V1 Does Not Persist as Domain Objects

V1 明确不建立：

```text
Evidence
Claim
CandidateFinding
CandidatePaper
CuratedPaper
Contradiction
Consensus
Trend
Comparison
DerivedQuestion
CitationMap

ReadingStage
ReadingHistory
ReadingDepth

GapState
CompletionCheckStatus
CompletionApproval
ArtifactStatus
ArtifactLifecycle

GlobalPaper
GlobalApproachFamily
WikiClaim
KnowledgeNode
```

如果未来某个概念证明具有：

* 独立身份；
* 独立生命周期；
* 跨模块长期引用；
* 且不能从现有权威状态安全推导；

才重新考虑升级为 Domain Object。

---

## 56. Derived Facts

以下状态显式保持派生：

```text
Gap open/resolved
← resolution

CompletionCheck pending/completed
← verdict

Artifact current/stale
← artifact.delivery_basis == run.delivery_basis

Run complete/partial
← CLOSED + outcome

Current Contract
← revisions[current_revision]

Current Delivery Authorization
← lifecycle + delivery_basis
```

不再同时保存对应 Boolean 或重复 Status。

---

# Domain Model Boundary

## 57. What This Document Freezes

本文冻结：

```text
Persistent domain objects
Entity vs Value Object
Stable reference relationships
Contract revision semantics
Paper identity boundary
Landscape object boundaries
Gap semantics
Completion record semantics
Delivery authorization shape
Persistent structural invariants
Command invariant categories
Semantic criteria boundary
Persistent vs ephemeral data
```

本文不冻结：

```text
Pydantic vs dataclass
Python module layout
JSON field spelling
serialization library
Ref string format
CLI syntax
tool names
final command names
function signatures
Repository class layout
provider adapter implementation
artifact filename/path
```

这些进入 Implementation Design。

---

## 58. Domain Model Quality Test

V1 Domain Model 应始终满足：

> 如果出现新的 failure case，优先尝试用现有事实、引用、显式 Domain Command 或派生状态表达。

只有在现有模型无法安全表达真实领域语义时，才新增对象。

特别警惕：

```text
is_ready
is_valid
is_verified
is_stale
is_complete
is_blocking
is_promoted
```

一类重复 Boolean。

也警惕给每个对象创建：

```text
CREATED
PROCESSING
REVIEWING
VERIFIED
ACCEPTED
```

独立生命周期。

复杂流程不自动意味着复杂 Domain Model。

---

## 59. Summary

V1 Domain Model 最终可以压缩为：

```text
Contract
   ↓
Papers
   ↓
Paper Analysis
   ↓
Literature Landscape
   ├── Approach Families
   ├── Landscape Findings
   └── Open Problems
   ↓
Investigation Gaps
   ↓
Completion Checks
   ↓
Delivery Basis
```

外层只有一个：

```text
ResearchRun
```

所有研究事实都在这个 Aggregate 中保持一致。

Observations 留在 Runtime。

Artifacts 留在 Delivery / Wiki projection。

Audit 留在 Event History。

语义质量留给 Claude。

Python 只守确定性边界。

> **系统保存的是研究判断，而不是研究动作的影子。**

> **对象保持少，引用保持明确，历史只在真正影响语义的地方保留。**

> **能推导的状态不重复保存；不能机械判断的质量不伪装成 schema rule。**
