# Reference Synthesis Guide

> Status: Tier-1 Reference Study synthesis
> Stage: Reference Study → Architecture Study handoff
> This document is **NOT an Architecture Decision Record**.
>
> 本文不决定最终架构。
>
> 它的作用是：
>
> * 综合六份 Reference Study；
> * 区分哪些观察得到多个 Reference 的共同支持；
> * 区分哪些只是某个项目的局部实现选择；
> * 记录 Reference 之间的冲突、反例与过度迁移风险；
> * 整理仍需 Architecture 阶段解决的问题；
> * 为后续 Architecture Decisions 提供可追溯的设计证据。
>
> 核心原则：
>
> > **Reference Projects are architecture evidence, not architecture authority.**
>
> 以及：
>
> > **Study problems, not features.**

---

# 1. Relationship to PROJECT_VISION

Reference Study 的上游仍然是：

```text
.vibe/context/PROJECT_VISION.md
```

关系必须始终保持：

```text
PROJECT_VISION
      ↓
defines product boundaries
and design principles
      ↓
Reference Studies
      ↓
provide architecture evidence
      ↓
Reference Synthesis
      ↓
Architecture Questions
      ↓
Architecture Decisions
```

因此本文不能因为某个 Reference：

* 功能更多；
* 工程更成熟；
* Agent 更多；
* 数据结构更多；
* 命令更多；
* Pipeline 更复杂；

就自动要求本项目采用相同设计。

尤其，以下属于 **PROJECT_VISION 已经确定的产品边界**，不是本次 Reference Synthesis 新产生的 Architecture Decision：

```text
Claude Code = Agent Runtime / Loop Driver

Python Harness = Research Runtime
               + deterministic actions
               + persistent state
               + validation
               + lifecycle constraints
```

以及：

```text
Simple loop.
Rich state.
Hard evidence.
Criteria over magic scores.
```

Reference 可以帮助我们理解这些原则如何落地，也可以挑战具体实现方案。

但除非出现非常强的新证据，否则不应重新打开产品定位本身。

---

# 2. Reference Corpus

本阶段共完成六份 Tier-1 Reference Study。

| Reference                   | 主要研究问题                                      | 它在整体证据链中的角色                                        |
| --------------------------- | ------------------------------------------- | -------------------------------------------------- |
| `formin/spec-kit-harness`   | 长程 Research State 如何离开 Conversation？        | State Externalization / Context Rendering / Resume |
| `homulillew/search-harness` | 第一版为什么发生 Control-Flow Explosion？哪些工程能力值得保留？ | Positive + Negative Architecture Experiment        |
| `Future-House/paper-qa`     | 论文检索、阅读、Evidence、Synthesis 的研究语义是什么？        | Scientific Literature Research Semantics           |
| `formin/spec-kit-loop`      | Agent 为什么不能自己做、自己检查、自己宣布完成？                 | Completion Authority / Independent Review          |
| `beefiker/superloopy`       | DONE 如何真正依赖 Evidence，而不是 Agent 的状态句子？       | Evidence-Gated Completion                          |
| `formin/spec-kit-wiki`      | Accepted Evidence 如何成为跨 Run 的长期知识？          | Knowledge Accumulation / Wiki Projection           |

这六份 Reference 不应该被理解成六块需要拼进产品的组件。

它们更接近六个实验：

```text
State
↓
Complexity Boundary
↓
Research Semantics
↓
Completion Authority
↓
Evidence Gate
↓
Cross-Run Knowledge
```

它们共同描述的是一个问题空间，而不是一套现成架构。

---

# 3. How to Read the Synthesis

后续 Architecture 阶段使用 Reference Evidence 时，统一分成四种类别。

## 3.1 Convergent Evidence

多个独立 Reference 从不同角度支持同一设计方向。

例如：

```text
spec-kit-harness
+
spec-kit-loop
+
Superloopy
+
old-search-harness
```

都支持：

```text
important state must survive outside conversation
```

这种属于强架构信号。

---

## 3.2 Strong Single-Reference Evidence

只有一个 Reference 深入解决了该问题，但它与我们的场景高度同构。

例如：

```text
PaperQA
→ Paper Search ≠ Evidence Retrieval
```

它虽然主要来自一个项目，但 PaperQA 正是本 Reference Corpus 中唯一真正面向 scientific literature retrieval 的成熟实现。

因此仍然属于强证据。

---

## 3.3 Counter-Evidence

某个 Reference 的设计非常成熟，但它恰好证明我们为什么不应该采用同样方案。

例如：

```text
old-search-harness
→ phase explosion
→ giant orchestrator
→ scalar sufficiency

spec-kit-wiki
→ accumulated LLM pages
→ pages become working truth
→ summary-of-summary drift
```

这些不是“失败的 Reference”。

它们是非常重要的 Negative Evidence。

---

## 3.4 Open Hypothesis

Reference 提供了有趣设计，但当前证据不足以升格成 Architecture Decision。

例如：

```text
exact excerpt mechanical matching
MMR
Paper / Route / Topic taxonomy
claim dependency graph
confidence field
two-source rule
token-exact context accounting
```

这些只能进入：

```text
Architecture Questions
```

而不能因为某份 Study 提到了，就直接进入 V1。

---

# 4. Cross-Reference Convergence

六份 Study 中最强的价值，不是任何单个项目的实现，而是若干设计边界被反复独立验证。

---

## 4.1 Conversation Is Not Research State

支持来源：

```text
spec-kit-harness
spec-kit-loop
old-search-harness
Superloopy
PROJECT_VISION
```

共同观察：

```text
Conversation
      ≠
Persistent Research State
```

长程 Agent 如果依赖 Conversation 保存：

* 已搜 Query；
* Papers；
* Evidence；
* Gaps；
* Contradictions；
* Budget；
* Completion State；

最终会出现：

```text
context drift
duplicate work
resume failure
state inconsistency
```

因此：

> **State persistence matters more than conversation persistence.**

这是一条高度收敛的设计证据。

但 Reference 并没有证明：

```text
必须有 6 个文件
```

或者：

```text
必须用 Markdown
```

它只证明：

> Research State 必须外置、可恢复、可检查。

具体 Domain Model 和文件布局仍属于 Architecture 阶段。

---

# 5. Persistent State and Context Must Be Separate

`spec-kit-harness`、Superloopy 从不同方向证明持久化的：

```text
Rich Persistent State
        ≠
Current Working Context
```

PaperQA 则在单一会话内证明非持久化的：

```text
Research State
        ≠
Current Working Context
```

（PaperQA 的状态全部在内存、无跨会话持久化；它证明的是同一 evidence state 的 view 分离，而不是持久化。）

正确关系更接近：

```text
Persistent State
      ↓
Context Renderer
      ↓
Action-Specific View
      ↓
Claude
```

而不是：

```text
Persistent State
      ↓
dump everything
      ↓
Claude
```

PaperQA 特别提供了一个有价值的例子：

```text
same underlying evidence state
        ↓
different views
        ↓
agent decision context
answer synthesis context
```

因此后续 Architecture 应重点研究：

```text
PLAN_SEARCH view
SELECT_READ view
ANALYZE_EVIDENCE view
REVIEW view
SYNTHESIZE view
```

是否需要不同的 State Projection。

这里真正可迁移的是：

> **Same State, Different Views.**

不是某个 Reference 的具体 token cap 或 slice 数量。

---

# 6. Bound the View, Not the Knowledge

这是跨 Reference 综合后需要明确的一条修正。

部分 Reference 为了 Context Budget 会：

```text
cap curated items
evict low-priority entries
```

这对 working set 有意义。

但对我们的 Accepted Evidence Store：

```text
Context Capacity
        ≠
Knowledge Capacity
```

因此不能因为当前 Claude Context 放不下，就删除已经接受且可追溯的 Evidence。

更合理的设计压力是：

```text
Durable Evidence Store
        ↓
potentially large
        ↓
Context Renderer
        ↓
small bounded relevant subset
```

即：

> **Bound the view, not the durable knowledge.**

是否需要 Evidence eviction，目前没有足够 Reference Evidence 支持。

---

# 7. Phase Is Lifecycle; Action Is Work

这是整个 Reference Corpus 中最强的一条 Negative + Positive Convergence。

`old-search-harness` 直接展示了：

```text
Search
Citation Expansion
Reflection
Audit
Revision
Retrospective
```

不断升级成 Lifecycle Phase 后，如何产生：

```text
phase explosion
nested loops
giant orchestrator
control-flow complexity
```

Superloopy 与 spec-kit-harness 则证明：

Evidence-Gated Completion 并不要求复杂 State Machine。

因此跨项目证据强烈支持：

```text
Lifecycle
≠
Research Actions
```

当前最值得在 Architecture 阶段检验的生命周期 hypothesis 仍然是：

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

而：

```text
SEARCH
READ
FOLLOW_REFERENCE
SELECT_READ
EXTRACT
COMPARE
ANALYZE_EVIDENCE
```

应优先被理解为 Action。

注意：

这仍然是 Architecture Hypothesis。

Reference Synthesis 不负责冻结最终 Phase Enum。

它只明确告诉下一阶段：

> **不要再让 Feature Count 驱动 Phase Count。**

---

# 8. Claude Policy and Python Mechanism

六份 Study 对这一边界提供了非常强的共同证据。

PaperQA 的真实实现表明：

```text
Python:
retrieval
dedup
ranking
serialization
citation resolution

LLM:
query wording
relevance meaning
evidence interpretation
answer synthesis
```

old-search-harness 则证明，当 Python 开始承担：

```text
semantic sufficiency
research direction
complex phase orchestration
```

复杂度迅速增长。

Superloopy进一步说明：

```text
Python can validate proof integrity
but cannot mechanically decide semantic truth
```

corpus 里最极端的两个 prompt-only 案例也支持这一边界：

```text
spec-kit-harness
用纯 prompt 承担全部 enforcement
（零可执行代码，"agent is the interpreter"）
→ 它自己承认这正是 VISION 决定用 Python 硬强制去替代的薄弱环节

spec-kit-wiki
同样是 prompt-only protocol
（require_citations、conflict 标记、lint 全靠模型遵守）
→ 没有任何机制在运行时机械强制
```

old-search-harness 的 claude-research-pack 一侧展示了同一边界的另一面：

```text
控制流被塞进 prompt（SKILL.md S1.1–S5.9、dispatch 词汇、back-edges）
"prompt discipline 超过几个动词就崩"
```

新 Harness 是 Claude Code = prompt-driven，因此 prompt 里能放多少控制流，正是 Architecture 阶段必须界定的边界。

所以当前强证据支持：

```text
Claude
=
Semantic Policy / Judgment

Python
=
Deterministic Mechanism / Integrity
```

但后续 Architecture 仍需逐项回答：

> 哪些 invariant 必须 Python 强制？

而不是使用一个模糊的：

```text
Python controls everything deterministic
```

作为万能答案。

---

# 9. Paper Is Not Evidence

这是 PaperQA 最重要的贡献，同时得到 spec-kit-harness 和 old-search-harness 的旁证。

正确语义至少存在：

```text
Discovered Paper
      ↓
Research Judgment
      ↓
Read / Inspect
      ↓
Evidence
```

PaperQA进一步表明：

```text
Relevant Paper
      ≠
Relevant Passage
      ≠
Interpretation of Passage
```

因此后续 Domain Model 不能把：

```text
paper.relevant = true
```

当作 Claim 支撑。

这是非常强的 research-semantics evidence。

---

# 10. Candidate / Curated / Evidence Must Be Understood Semantically

`spec-kit-harness` 强调：

```text
Candidate
→ Curated
→ Evidence
```

这个分层的思想值得保留：

```text
discovered
≠
accepted as useful
≠
proof for a claim
```

但 Reference Corpus **没有证明我们必须创建一个独立 Curated Entity**。

例如：

```text
Paper
├── candidate
├── selected
├── core
├── supporting
└── rejected
```

可能已经足够表达 paper-level research judgment。

因此 Architecture 阶段应研究的是：

> 我们需要哪些语义层？

而不是：

> spec-kit 有三个表，所以我们也建三个表。

---

# 11. Evidence Needs Two Layers

PaperQA 与 Superloopy 综合后，Evidence 最重要的内部边界越来越清楚：

```text
Evidence
│
├── Source Layer
│   ├── paper
│   ├── locator
│   └── excerpt / source material
│
└── Semantic Layer
    ├── research question / gap
    ├── claim
    ├── stance
    └── interpretation
```

Source Layer 解决：

> Evidence 来自哪里？

Semantic Layer 解决：

> 这段东西对当前 Research Question 意味着什么？

这两个层次不能混淆。

特别需要区分：

```text
source_reported
```

与：

```text
researcher_interpretation
```

否则最终 Wiki / Report 很容易把 Claude 的解释写成论文原话。

具体 Evidence Schema 仍留给 Domain Model 阶段。

---

# 12. Relevance and Stance Are Orthogonal

Reference 综合中值得统一校正的一个过度迁移风险：

```text
relevance score
→ typed stance
```

两者实际上回答不同问题。

```text
Relevance:
这段 Evidence 与当前问题有多相关？

Stance:
它与 Claim 的关系是什么？
```

例如：

```text
highly relevant + supporting
highly relevant + contradicting
weakly relevant + supporting
```

都合法。

因此未来模型不应让：

```text
supporting / contradicting / qualifying
```

替代 retrieval relevance。

更合理的候选方向是：

```text
stance
→ durable semantic state

relevance/ranking
→ possibly ephemeral retrieval metadata
```

是否持久化 relevance，以及是否需要数字评分，仍未决定。

---

# 13. Progressive Reading Remains an Open but Strong Candidate

PaperQA 不做：

```text
Abstract
→ Sections
→ Full Text
```

式 Progressive Reading。

但原因非常关键：

PaperQA 已经提前承担：

```text
full document parsing
chunking
embedding/indexing
```

成本。

因此它可以：

```text
question
→ retrieve relevant chunks
```

我们的 Harness 面对的成本结构不同：

```text
Search metadata
→ Abstract
→ maybe full text
→ parsing
→ section reading
```

所以不能从 PaperQA 推出：

> Progressive Reading 没必要。

更准确的对照：

```text
PaperQA
=
parse first, retrieve later

Our candidate
=
screen first, fetch/read progressively
```

因此：

```text
Progressive Reading
```

继续作为 Architecture Hypothesis 保留。

但它应该是：

```text
reading policy / cost-control mechanism
```

而不是新的 Lifecycle Phase。

注意：这相对 PROJECT_VISION 的 Principle 9（默认不把整篇论文塞进 Context、逐步深入阅读）是一次显式软化——触发条件是 PaperQA 的成本结构（提前支付 full-text parsing/chunking/embedding）与我们的不同。Architecture 阶段应显式决定是否保留 P9，而不是默认它继续原样生效。

---

# 14. Work Is Not Proof

这是 Superloopy 提供的最强 Evidence-Gate 思想。

```text
Search
Read
Analyze
```

都属于：

```text
Work
```

而不是：

```text
Proof
```

对论文调研：

```text
"I read Paper X."
```

没有任何 Completion 证明力。

真正接近 Proof 的是：

```text
Evidence E017
→ Paper X
→ Locator Y
→ Excerpt Z
→ Claim relation
```

因此：

> **Reading is work. Evidence is proof candidate.**

这条原则把 PaperQA 的：

```text
Paper ≠ Evidence
```

继续推进成：

```text
Work ≠ Evidence
```

---

# 15. Evidence Is Not Completion

Superloopy进一步说明：

```text
Evidence
≠
Criterion PASS
≠
Completion
```

一条 Evidence 存在，只能证明：

> 有一个可检查对象存在。

它不能自动证明：

> 当前研究问题已经被充分回答。

因此完整层级更接近：

```text
Paper
 ↓
Evidence
 ↓
Criterion / Coverage
 ↓
Review
 ↓
Completion
```

这条链路是六份 Study 综合后的核心概念之一。

---

# 16. Hard Evidence Does Not Mean Python Decides Truth

Superloopy 对 command-backed 与 manual criterion 的区分，对我们尤其重要。

Python 可以机械判断：

```text
Evidence ID exists
Paper ID resolves
Locator exists
Schema is valid
Citation resolves
State transition is legal
Budget remains
```

但 Python 很难可靠判断：

```text
这段原文真的支持这个 Claim 吗？

这个 interpretation 公平吗？

这是 contradiction 还是 scope difference？

这个技术路线已经被充分覆盖了吗？
```

所以：

```text
Mechanical Integrity
        ≠
Semantic Validity
```

当前最强的跨项目设计压力是：

```text
Python
→ Evidence Integrity

Claude
→ Evidence Meaning
```

这不是说 Semantic Layer 不受约束。

而是：

> Python 应保证 Claude 的语义判断站在真实、合法、可追溯的 Evidence 上。

---

# 17. Completion Authority Must Be Separate From Research Authority

spec-kit-loop 的核心贡献：

```text
Maker
≠
Checker
```

PROJECT_VISION 已经要求：

```text
Researcher
→ ready_for_review
```

而不是：

```text
Researcher
→ DONE
```

Reference Corpus 强烈支持这个方向。

但需要做一个重要校正。

---

# 18. Authority Separation and Context Independence Are Different Problems

Python 可以真正机械 enforce：

```text
RESEARCH
cannot write final review verdict

Researcher
cannot set DONE

only review transition
can write ReviewVerdict
```

但 Python 很难真正证明：

```text
这个 Reviewer
从未看到 Researcher 的旧思维上下文
```

因此要分开：

```text
Authority Separation
        ↓
Python can enforce

Context Independence
        ↓
Claude Code execution protocol
```

也就是说：

```text
Python:
who may mutate which state

Claude Code:
fresh sub-agent / fresh context
review-specific bounded slice
```

不要为了“证明 reviewer fresh”引入复杂身份、token 或 session security system。

这是 Architecture 阶段需要保持的重要边界。

---

# 19. Review Vocabulary Must Be Layered

不同 Reference 使用：

```text
PASS / FAIL / UNCERTAIN
covered / partial / missing
verified / refuted
supporting / contradicting
```

这些不能混成一个 Status Enum。

比较自然的语义分层是：

```text
Evidence relation:
supporting
contradicting
qualifying

Research coverage:
covered
partial
missing

Evidence / claim condition:
supported
unresolved
refuted
unknown

Overall review outcome:
PASS
CONTINUE
UNCERTAIN
PARTIAL
```

这只是词汇层次的综合指导，不是最终 Domain Model。

关键原则是：

> 不同语义问题使用不同 typed states。

不要重新把它们压成：

```text
quality_score = 0.84
```

---

# 20. Typed Criteria Beat Scalar Sufficiency

old-search-harness 是这一点最强的负面实验。

旧系统实际上已经拥有：

```text
per-dimension coverage
evidence counts
non-consensus state
primary-paper state
```

这些 rich typed state。

但最后却被压成：

```text
weighted sufficiency_score
```

再与一个 magic threshold 比较。

结果是：

```text
rich information
      ↓
lossy scalar compression
      ↓
control-flow decision
```

这证明：

> 收集 typed state，却最后用 scalar 决定质量，会把 rich state 的价值重新丢掉。

因此 Reference Corpus 强烈支持：

```text
Hard numbers
→ resource limits

Typed criteria
→ semantic quality
```

而不是：

```text
semantic quality
→ weighted score
```

---

# 21. Critical Criteria Should Be Non-Compensatory

例如：

```text
RQ1 covered
RQ2 covered
RQ3 critical but missing
```

不能因为前两个很好，就得到：

```text
overall = 82%
→ PASS
```

这是 old-search-harness 中 hard gates 最终不得不出现的原因。

与其：

```text
score
+
hard gate patches
```

更简单的是：

```text
typed critical criteria
```

直接 non-compensatory。

具体 criteria 的内容仍待 Architecture / Research Contract 设计。

---

# 22. Budget Stops Autonomy; It Does Not Prove Completion

spec-kit-harness、spec-kit-loop、Superloopy 都支持 bounded autonomy。

但必须区分：

```text
Stop spending resources
```

和：

```text
Research is semantically complete
```

因此：

```text
Budget exhausted
      ↓
stop autonomous research
      ↓
Review
```

是合理的。

而：

```text
Budget exhausted
      ↓
DONE
```

是不合理的。

如果 Reviewer 得出：

```text
CONTINUE
```

但：

```text
budget = 0
```

则不能偷偷继续研究。

应该进入类似：

```text
PARTIAL
```

或者：

```text
explicit budget extension
```

的路径。

Reviewer 能判断：

> 还需要研究。

但 Reviewer 不应拥有：

> 凭空增加资源预算。

---

# 23. Saturation Is a Review Trigger, Not Completion Proof

多个 Reference 使用：

```text
no new evidence
dry waves
marginal gain
no new leads
```

作为收敛信号。

这些信号很有价值。

但：

```text
no new evidence
```

可能表示：

```text
真的饱和
query 写坏
provider recall 不足
重复搜索
正在深读但尚未抽取 evidence
gap 定义错误
该领域本身缺证据
```

所以：

```text
low marginal gain
      ↓
request review
```

比：

```text
low marginal gain
      ↓
DONE
```

更可靠。

---

# 24. Gap-Driven Research Has Strong Support

PaperQA 展示了 evidence feedback 后 Query 会发生 refinement。

PROJECT_VISION 强调下一轮 Research 应有显式理由（P7 Gap-driven Research）。

因此：

```text
Research Gap
      ↓
next semantic investigation
```

是强设计压力。

但需要一个重要边界：

```text
Gap → Query relationship
```

可以被 Python 记录和校验。

而：

```text
Gap → exact Query wording
```

仍然是 Claude 的语义工作。

所以：

```text
Python:
query must reference a valid gap
query dedup
budget
history

Claude:
how to rewrite that gap into a useful query
```

不要把 Query Rewrite 变成 deterministic template engine。

---

# 25. Retrieval Failure Is Not Semantic Absence

old-search-harness 的 fail-closed DeepXiv adapter 与 Superloopy 的 retrieval verdict 都证明：

```text
No Result
```

与：

```text
Search Failed
```

必须分开。

典型状态可能包括：

```text
success
empty
partial
rate_limited
unavailable
provider_error
```

如果把 provider failure 记录成：

```text
0 results
```

Research Loop 会错误认为：

> 该方向没有 Evidence。

甚至进一步错误触发：

```text
saturation
```

因此 Provider Contract 是后续 Architecture 中的重要 deterministic boundary。

---

# 26. Grounding Has Multiple Strength Levels

PaperQA 是很好的 Grounding 参考，但不能把它概括成：

> 每个 Claim 都被机械保证有 Citation。

更准确的是：

```text
Hard:
no evidence → no answer

Mechanical:
citation ID must resolve

Prompt / semantic:
every substantive claim should actually be supported
```

我们的 Harness 可以比这一层更进一步：

```text
Report Claim
      ↓
Evidence ID
      ↓
Paper + Locator
```

但“这条 Evidence 真支持这句话”仍然属于 Semantic Review。

因此 Citation Audit 要区分：

```text
reference integrity
```

和：

```text
semantic support
```

---

# 27. MMR Is Not the Same as Source Diversity

PaperQA 使用 MMR 来减少 retrieval redundancy。

但：

```text
semantic diversity
```

并不自动等于：

```text
independent source diversity
```

所以当前没有足够证据支持：

> V1 必须实现 MMR。

真正值得保留的需求是：

> Critical conclusions should not accidentally depend on one narrow source when broader evidence is required.

这可以通过：

```text
Review Criteria
```

解决，不一定需要 embedding-based MMR。

---

# 28. Evidence Requirements Depend on Claim Type

Superloopy 对高风险 Web Claim 使用：

```text
2+ independent observations
counter-search
primary source
```

这是很强的 Evidence Discipline。

但不能直接迁移成：

```text
every literature claim requires ≥2 papers
```

例如：

```text
"Paper A introduces Method X."
```

Paper A 本身就是最权威来源。

因此未来更合理的研究问题是：

```text
Paper-specific factual claim
→ one authoritative primary paper may suffice

Cross-paper comparative conclusion
→ broader support

Field-level consensus conclusion
→ multiple independent papers

High-stakes conclusion
→ stronger corroboration / counter-search
```

即：

> **Evidence requirements should depend on claim type and consequence.**

具体规则仍待设计。

---

# 29. Contradictions Must Survive

old-search-harness、Superloopy、spec-kit-wiki 都独立支持：

```text
contradiction
```

不应该在 Synthesis 时被悄悄平均掉。

论文研究中：

```text
supporting
contradicting
qualifying
```

是非常有价值的 state。

未来 Wiki / Report 可以：

```text
project contradictions
```

但不应该在 projection 层：

```text
resolve contradictions
```

真正的 semantic resolution 应发生在：

```text
Research Analysis / Fresh Review
```

然后写回 state。

Projection 只是忠实呈现。

---

# 30. Wiki Must Be Evaluated as Derived Knowledge, Not Storage

spec-kit-wiki 是整个 Reference Corpus 中非常有价值的反例。

它采用：

```text
Raw Sources
      ↓
LLM ingest / merge
      ↓
Wiki Pages
      ↓
Future Query reads Pages
```

优点非常明显：

```text
compounding knowledge
cheap future query
citation discipline（但注意：纯 prompt discipline，
                  require_citations 生效时完全靠模型遵守，
                  运行时无机械强制）
conflict markers
lint
```

但它也产生：

```text
pages become working truth
summary-of-summary drift
rm -rf wiki cannot reconstruct knowledge
```

我们的 PROJECT_VISION 候选方向不同：

```text
Paper
      ↓
Accepted Evidence
      ↓
Projection
      ↓
Wiki
```

需要保持准确措辞：spec-kit-wiki 证明 accumulate 同样可以精致，因此我们对 Projection 方向的偏好，是从它的 failure modes 加上可派生论证推出的判断，而不是参考项目本身对 Projection 的正向背书——它是很强的对照证据，不是认可。

Reference Corpus 强烈支持的只是：

> Wiki 不应成为第二事实源。

它并没有自动决定：

```text
具体 Page Schema
具体文件结构
具体 Projection Algorithm
具体 taxonomy
```

这些仍然属于后续 Architecture。

---

# 31. Wiki Query Should Produce Prior, Not Proof

spec-kit-wiki 的 Query 直接从 Pages 回答。

这正是我们需要谨慎的地方。

更符合当前 Project Vision 的使用方式是：

```text
Future Research Run
      ↓
Wiki
      ↓
known routes
known papers
known contradictions
open questions
      ↓
research lead / prior
      ↓
Paper / Evidence verification
```

核心句：

> **Wiki helps decide what to investigate; papers decide what we are allowed to claim.**

因此未来 Research Run 不能简单：

```text
Wiki says X
→ accepted claim
```

而应该：

```text
Wiki says X
→ investigate X
→ verify against source
→ accepted evidence
```

---

# 32. Wiki Update: Re-Projection Is a Strong Hypothesis

spec-kit-wiki 的：

```text
old page
+
new source
→
LLM rewrites page
```

暴露了 summary drift 风险。

因此 Reference Corpus 强烈支持继续测试：

```text
Accepted Evidence
      ↓
Projection
      ↓
Wiki
```

以及：

```text
Update
=
re-project
```

而不是：

```text
Update
=
LLM repeatedly summarizes old summaries
```

但以下仍未决定：

```text
Projection 是否完全 deterministic
如何保证可读性
是否允许 narrative layer
如何做局部 rebuild
什么时候触发 rebuild
什么内容属于 wiki（可派生边界）
```

其中”什么内容属于 wiki”有现成的强候选——spec-kit-wiki 本 reference 对我们最有用的概念（可派生边界）：

```text
evidence-backed 结论（含失败模式、why-a-route-was-rejected）
→ 可投影内容

process-level 的决策过程
→ 只留在 run state
```

这条边界同时决定了更新触发：evidence 版本/as-of 变化 → 标待重投影（provenance-driven stale），而不是按天数启发式 `stale_after_days`。

因此”Wiki = derived projection”是强方向；

“Projection Builder 的具体实现”仍是开放问题。

---

# 33. Wiki Taxonomy Is Not Frozen

当前候选：

```text
Paper
Route
Topic
```

有合理依据：

```text
Paper
→ single-source knowledge

Route
→ cross-paper technical synthesis

Topic
→ landscape / contradictions / open questions
```

但六份 Reference 没有证明：

> 这三个永远就是最终一级对象。

尤其：

```text
Route identity
Topic identity
aliases
rename
cross-run dedup
```

都是尚未解决的问题。

因此 Architecture 阶段应把：

```text
Paper / Route / Topic
```

作为：

> hypothesis to test

而不是现成 taxonomy。

---

# 34. Source Registry Is Not Automatically Required

spec-kit-wiki 的 `sources.md` 解决：

```text
source identity
dedup
ingest time
pages touched
citation namespace
```

我们的环境已经可能存在：

```text
Paper Store
+
Evidence Store
```

因此不应自动再创建：

```text
SourceRegistry
```

但 Source Registry 的部分职责不能被忽略：

```text
stable source identity
source version/freshness
reverse dependency
source removal/retraction
```

Architecture 阶段真正要问的是：

> 这些职责由谁承担？

而不是：

> 是否复制一个叫 SourceRegistry 的模块？

---

# 35. Engineering Backbone Has Already Been Proven Valuable

old-search-harness 的 Positive Reference 部分提供了其它 Reference 缺少的真实 Python 经验：

```text
atomic writes
single-writer lock
append-only events
resume checkpoints
fail-closed provider validation
configuration snapshot
```

这些并不会自动决定最终文件结构。

但它们说明：

> 当 Python 真正承担 Research Runtime 时，状态安全是实际工程问题，不是理论问题。

因此这些应进入后续 Engineering Design 的候选 baseline。

同时要避免再次升级成：

```text
version every artifact
hash everything
audit everything
```

原则是：

> 保留可靠性骨架，裁掉未经证明的审计规模。

---

# 36. Reference-Specific Features We Should Not Accidentally Promote

以下设计目前没有足够跨项目证据成为 V1 Core：

| Reference-specific mechanism                  | 当前处理                             |
| --------------------------------------------- | -------------------------------- |
| spec-kit-harness 的 6 个 Markdown state files   | 学语义分离，不复制文件集合                    |
| `curated cap = 25`                            | 不采纳固定 cap                        |
| 3-action marginal gain stop                   | 只保留 saturation signal            |
| spec-kit-loop 五命令                             | 不复制 CLI workflow                 |
| mandatory human signoff                       | 不作为每个 Research Run 的必需 gate      |
| comprehension debt subsystem                  | 用 unresolved/open questions 表达即可 |
| PaperQA 完整 RAG / Tantivy / embedding stack    | V1 不引入                           |
| MMR                                           | 只保留 diversity concern            |
| PaperQA parse-first full corpus               | 不证明我们的 Progressive Reading 无效    |
| PaperQA 单答案范式（gen_answer 只是 SYNTHESIZE 的一个组件） | 不采纳：我们要 evidence-ledger → 对比 → report + non-consensus |
| PaperQA 纯内存会话（无持久化 / 无 resume / 无 budget）   | 不采纳：与外置持久 state 的 V1 冲突      |
| old-search-harness sufficiency score          | 明确反例                             |
| citation graph as core artifact               | 不升级成 core                        |
| mandatory GitHub research channel             | 后续可选                             |
| LoopEngineer meta-loop                        | 不进入 Research Lifecycle           |
| Superloopy crew / hooks / continuation engine | 不迁移                              |
| universal two-source rule                     | 不采纳                              |
| complete A–E source ladder                    | 不照搬                              |
| spec-kit-wiki accumulated page truth          | 反例                               |
| fixed Paper/Route/Topic taxonomy              | 保持 hypothesis                    |
| graph DB / vector DB                          | 无需求证据，不引入                        |

---

# 37. Cross-Study Normalizations

为避免后续 Architecture 直接从某一份 Study 的 Candidate ADR 复制结论，以下内容需要统一解释。

## 37.1 Candidate ADRs Are Not Accepted ADRs

每份 Study 中：

```text
Candidate ADRs Influenced by This Project
```

只表示：

> 这个 Reference 提供了支持某个 Architecture Question 的证据。

它不表示：

> 这个 Decision 已经批准。

正式 ADR 必须重新经过：

```text
Problem
↓
Project constraints
↓
Cross-reference evidence
↓
Alternatives
↓
Simplest viable option
↓
Trade-offs
↓
Validation plan
↓
Decision
```

---

## 37.2 Fresh Reviewer

不要写成：

```text
Python guarantees reviewer is fresh
```

应该分成：

```text
Python
→ guarantees review authority separation

Claude Code protocol
→ attempts context independence
```

---

## 37.3 Query Refinement

不要写：

```text
gap deterministically maps to query
```

应该是：

```text
Python:
gap/query relationship is explicit

Claude:
query wording is semantic
```

---

## 37.4 Relevance vs Stance

不要让：

```text
supporting / contradicting / qualifying
```

承担 retrieval relevance 的含义。

两者是不同维度。

---

## 37.5 Progressive Reading

不要从 PaperQA 得出：

```text
progressive reading unnecessary
```

它的成本已经被 full-text preprocessing 提前支付。

我们的成本模型不同。

---

## 37.6 Status / Next

不要让 Python 在 RESEARCH 中开始替 Claude 做 Research Policy。

应区分：

```text
Control Obligation
```

和：

```text
Semantic Research Choice
```

例如 Python 可以确定：

```text
budget exhausted
→ REVIEW required
```

但不应该决定：

```text
现在最值得 SEARCH 还是 READ？
```

---

## 37.7 Confidence

`high / medium / low` 可以作为风险 annotation。

但目前没有证据要求它进入 V1 completion logic。

相比：

```text
confidence = low
```

更有用的往往是：

```text
uncertainty_reason =
missing_evidence
conflicting_evidence
ambiguous_scope
source_unavailable
```

---

# 38. Strong Cross-Reference Design Pressures

下面这些不是正式 ADR。

但它们获得了足够多 Reference Evidence，应优先进入下一阶段 Architecture Study。

### Persistent Research State

研究事实、过程状态与 Evidence 必须离开 Conversation。

### Bounded Context Projection

Context 是 State 的 View，而不是 State 本身。

### Simple Lifecycle

不要把 Research Actions 升级成 Phase。

### Semantic / Mechanical Separation

Claude 负责研究判断；Python 负责可靠执行与完整性。

### Paper / Evidence Separation

发现 Paper 不等于获得 Evidence。

### Evidence-Backed Completion

Work、Evidence、Coverage、Completion 是不同层级。

### Independent Review Authority

Researcher 无权直接写 DONE。

### Typed Completion Criteria

完成判断不使用 scalar sufficiency score。

### Budgeted Autonomy

数字约束资源，不替代语义完成判断。

### Contradiction Preservation

分歧是 state，不是写作噪音。

### Evidence-First Synthesis

Report/Wiki 从可追溯 Evidence 出发。

### Derived Wiki

长期 Wiki 不应成为独立 Truth Store。

### Resume From State

恢复 Research Process，而不是恢复 Conversation。

---

# 39. Architecture Questions That Remain Open

Reference 阶段完成后，真正需要下一阶段回答的是这些问题。

## Research Contract

需要哪些最小字段？

```text
mission
research questions
critical criteria
budget
scope
evidence requirements
deliverable requirements
```

哪些是稳定 Core？

哪些可以在研究过程中显式演化？

以及（spec-kit-loop ADR 3 的候选）：

```text
done-criteria 必须可检查：每条写明验证方法
无 checkable criteria 的 mission 不开始
```

---

## Domain Model

至少需要研究这些概念之间的边界：

```text
ResearchRun
ResearchContract
ResearchQuestion
ResearchGap
Query
Paper
Evidence
Criterion
Contradiction
TechnicalRoute
ReviewVerdict
```

哪些应该是一等 Entity？

哪些只是字段或 Projection？

---

## Evidence Model

需要决定：

```text
locator 粒度
excerpt 是否必需
excerpt 是否机械匹配
interpretation 如何表示
claim 与 evidence 是什么关系
evidence 是否跨 criteria 复用
accepted evidence 的状态生命周期
refuted / excluded evidence 如何表示（spec-kit-harness: 标记 refuted 但不删除，防重复推导旧错误）
time-sensitive 证据的 vintage/版本如何记录（superloopy: 时间敏感结论显式标 vintage，不要求每条 evidence 都有 observed_at）
```

---

## Paper State

需要决定：

```text
candidate
selected
read
core
supporting
rejected
```

到底用一个 status 表达，还是拆成不同维度。

---

## Progressive Reading

需要明确：

```text
metadata
abstract
headings
sections
full text
```

的成本策略以及什么时候升级阅读深度。

---

## Context Renderer

需要决定：

```text
不同 Action 看到什么
如何计算 size/token budget
如何保留关键 gaps
如何按 relevance/selectivity 渲染
```

---

## Action Interface

需要定义最小 Action Surface。

但设计目标不是：

> 动作越少越好。

而是：

> Action 数量增加不能导致 Lifecycle Phase 数量同步增加。

---

## Review Gate

需要决定：

```text
mechanical preconditions
semantic review input
criterion-level verdict
overall outcome
unresolved representation
fresh reviewer invocation protocol
budget exhaustion handling
adversarial default-fail posture（spec-kit-loop: checker 的职责是尝试让每条 criterion 失败；不确定时默认 fail/uncertain）
```

---

## Completion

需要定义：

```text
PASS
CONTINUE
UNCERTAIN
PARTIAL
```

分别意味着什么。

以及：

```text
budget exhausted + CONTINUE
```

如何处理。

---

## Persistence

需要决定：

```text
JSON vs JSONL
state decomposition
append-only event log
atomic write
lock
checkpoint
versioning scope
```

以及（spec-kit-loop ADR 5 的候选）：

```text
/status 由 state 推导唯一推荐动作（deterministic single next action）
```

---

## Wiki Projection

需要决定：

```text
page identity
taxonomy
projection determinism
local rebuild
incremental/local rebuild
source version changes
paper retraction/removal
cross-run dedup
wiki 内容边界：什么属于 wiki（evidence-backed 结论含失败模式），什么留在 run state（process 决策）
integrity-by-construction 引文（spec-kit-wiki ADR 2: 每个 wiki claim 携带 accepted-evidence ID，Python fail-closed）
provenance-driven stale 触发（evidence 版本/as-of 变化 → 标待重投影，而非天数启发式）
```

---

## Report Projection

需要决定：

```text
Claim → Evidence
citation rendering
authoring representation
reader representation
citation audit
```

但不应该让 Report Pipeline 重新长成第二套 Workflow。

---

## Provider / Security

需要决定：

```text
读取/检索到的内容是 untrusted data，不是 instruction
（外部 PDF/HTML/metadata 即使包含 "ignore previous instructions" 也不得作为指令执行）
fail-closed 的读取与解析（读取/解析失败 ≠ 内容为空）
```

这来自 superloopy 的 Candidate ADR 6——对会拉取外部论文/HTML 的 Harness，它是必须进入 Architecture 阶段的安全边界。

---

# 40. Questions That Should NOT Be Reopened Without New Evidence

除非后续实现或 Eval 提供明显反证，Architecture 阶段不应该浪费时间重新讨论：

```text
是否让 Python 自己成为完整 Agent Runtime？

是否引入通用 Multi-Agent Framework？

是否把每个 Action 设计成 Phase？

是否重新引入 sufficiency_score？

是否让 Wiki 成为新的 Evidence Source of Truth？

是否直接复制 Reference 的命令结构？

是否把 Reference Source Code 放进产品仓库？
（仓库卫生约定，非架构闭合：参考代码保留在 sibling 目录，不进入产品仓库）

是否现在引入 Graph DB / Vector DB？

是否构建 LoopEngineer 自修改元循环？
```

这些要么已经被 PROJECT_VISION 排除，要么已经有很强的 Negative Reference Evidence；唯一例外是「Reference Source Code 不进产品仓库」——它属于仓库卫生约定，而非架构决定，因此不按证据门控处理。

---

# 41. How Reference Evidence Should Be Used in Architecture Design

下一阶段每一个重要 Architecture Decision，都应该包含一个：

```text
Reference Evidence
```

小节。

推荐格式：

```markdown
## Reference Evidence

### Supporting

- spec-kit-harness:
  <what problem/behavior it demonstrates>

- PaperQA:
  <what problem/behavior it demonstrates>

### Counter-Evidence

- old-search-harness:
  <what failure mode warns against this design>

### Non-Transferable Details

- <reference-specific implementation that should not be copied>
```

Reference Evidence 必须回答：

> 为什么这个设计适合我们的问题？

而不是：

> 哪些项目也这么做？

---

# 42. Architecture Decision Quality Bar

正式 ADR 不应该仅凭：

```text
one reference has feature X
```

成立。

一个重要 Decision 最好至少具备：

```text
Project problem
+
PROJECT_VISION constraint
+
Reference evidence
+
Alternative
+
Trade-off
+
Simplest viable design
+
Validation method
```

如果只有 Reference，没有我们的 Problem：

> 不做。

如果有 Problem，但一个更简单方案可以解决：

> 优先简单方案。

如果复杂度不能回答：

```text
What breaks if we remove this?
```

那么它不应该进入 V1 Core。

---

# 43. Reference Phase Completion Criteria

Tier-1 Reference Study 阶段现在可以认为完成，当我们已经可以回答：

```text
What belongs to Claude?

What belongs to Python?

What survives a session?

What is the smallest plausible lifecycle?

What is a Research Action?

What is a Paper?

What is Evidence?

What separates work from proof?

What makes a criterion eligible for completion?

Who may request review?

Who may declare completion?

What does budget exhaustion mean?

How are contradictions represented?

What is the source of truth?

What enters the Wiki?

How does future research reuse prior knowledge?
```

Reference 阶段的完成不意味着这些问题都有最终 schema。

它意味着：

> 我们已经拥有足够的设计证据，可以开始 Architecture Study，而不需要继续无边界扩大 Reference Corpus。

---

# 44. When to Add Another Reference

Tier-2 Reference 不应该按照：

```text
“还有什么优秀项目没读？”
```

继续扩。

只有出现一个明确 Architecture Question，并且当前六份 Reference 无法回答时，才引入新 Reference。

正确流程：

```text
Architecture Question
      ↓
Current evidence insufficient
      ↓
Identify missing evidence
      ↓
Choose one targeted reference
      ↓
Study only that question
```

而不是：

```text
collect more projects
      ↓
hope architecture becomes obvious
```

---

# 45. Next Stage

Reference Study 之后，不应该直接开始大规模写产品代码。

更合理的下一阶段：

```text
Reference Synthesis
        ✓
        ↓
Architecture Questions
        ↓
Architecture Decisions
        ↓
High-Level Architecture
        ↓
Domain Model
        ↓
Minimal Runtime Contract
        ↓
First Implementation Slice
```

特别注意：

```text
Architecture Decisions
```

应当是新的独立阶段。

不要把六份 Study 里的所有：

```text
Candidate ADR
```

直接汇总成：

```text
Accepted ADR
```

那只是把“Feature Shopping”换成了“ADR Shopping”。

---

# 46. Final Cross-Reference Mental Model

六个 Reference 最后可以压成六句话：

```text
spec-kit-harness
→ State must survive outside context.

old-search-harness
→ Rich state must not become rich control flow.

PaperQA
→ A paper is not evidence.

spec-kit-loop
→ The researcher is not the final judge.

Superloopy
→ Evidence is not completion.

spec-kit-wiki
→ Reusable knowledge must not become a second source of truth.
```

它们组合起来形成：

```text
                        Persistent Research State
                                  │
                  bounded action-specific views
                                  │
                                  ▼
                            Claude Code
                         Semantic Research
                                  │
                                  ▼
                         Research Actions
                                  │
                                  ▼
                          Paper Candidates
                                  │
                                  ▼
                              Evidence
                                  │
                                  ▼
                       Criterion / Coverage State
                                  │
                                  ▼
                         Independent Review
                                  │
                     ┌────────────┼────────────┐
                     ▼            ▼            ▼
                   PASS       CONTINUE     UNCERTAIN
                     │
                     ▼
                 SYNTHESIZE
                     │
              ┌──────┴──────┐
              ▼             ▼
            Report         Wiki
              │             │
              │        future prior
              │             │
              └─────────────┘
                    not proof
```

这张图不是最终 Architecture Diagram。

它只是六份 Reference 共同留下的：

> **Problem Structure。**

真正的下一步，是基于这份 Problem Structure，设计我们自己的最小 Architecture，而不是继续拼 Reference。

---

# 47. Final Principle

Reference 阶段结束后，应始终记住：

> **We are not building spec-kit-harness + PaperQA + spec-kit-loop + Superloopy + spec-kit-wiki.**

我们正在构建：

> **一个面向 Claude Code 的 Literature Research Harness。**

Reference 的价值，是帮助我们理解：

```text
哪些问题真实存在
哪些边界经过验证
哪些设计曾经失败
哪些复杂度没有必要
```

而真正的 Architecture，必须由：

```text
Our Product Problem
+
Our Constraints
+
Reference Evidence
+
Simplest Viable Design
```

共同产生。

因此本 Reference Synthesis 的最终职责只有一句话：

> **让下一阶段做 Architecture Decisions 时，有证据可依，但没有答案被提前替我们决定。**
