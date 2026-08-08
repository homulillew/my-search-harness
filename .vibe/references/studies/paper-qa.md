# Study Note: Future-House/paper-qa

> 本 Note 是第三份 Reference Study。前两份解决了 Harness 外壳：
> spec-kit-harness 给了克制的 baseline（Simple loop / Rich state），old-search-harness
> 演示了 control-flow explosion 的越界方向。**paper-qa 开始回答外壳内部的问题**——
> 真正的论文 Research Semantics 应该是什么。因此本 Note 不再研究「怎么做状态机」，
> 而是围绕七个研究语义问题展开：Search Result / Paper Candidate / Read 的分界、
> Reading 分级、Paper→Evidence、Evidence 排序筛选、Evidence↔Claim 绑定、
> Query refinement 位置、LLM 与 deterministic retrieval 的边界。
>
> 结论先行：**PaperQA 是一个成熟的、answer-centric 的通用科学 RAG**。它的研究语义
> 分层（Paper Search ≠ Evidence Retrieval、question-bound evidence、证据驱动的
> grounded answer）正是我们要的；但它是「单答案」范式，没有 research loop 的持久
> 状态、budget、stop conditions——那些是我们前两份 Study 已经定位过的 Harness 外壳。

## Snapshot

```
Repository: https://github.com/Future-House/paper-qa
Commit:     d7675d7（#1335 NemotronParseBBox；研究时点 HEAD）
Study date: 2026-08-09
License:    Apache-2.0
Language:   Python；基于 aviary/ldp agent 框架（ToolSelector + RolloutManager）
```

---

## Why We Studied It

Tier 1 中唯一真正面对科学论文检索与证据组织的参考项目。前两份 Study 证明了「循环要简单、
状态要丰富、控制流要薄」，但没有回答**循环内部每一步对论文到底做什么**。paper-qa 填补的
正是这个空白：

```text
scientific paper search        （候选怎么来）
document reading                （论文怎么读）
evidence gathering              （论文怎么变成证据）
citation-grounded answering     （证据怎么约束结论）
```

它不研究生命周期、不研究 resume、不研究 budget——那些我们已经有答案。它研究的是
**Harness 里真正的论文研究语义**。

同时它是重要的反面参照：完整 RAG 基础设施（索引、embedding、MMR、媒体解析、元数据
provider 全家桶、1290 行配置）远超我们需要。按指南：**学它的 research semantics，
不继承它的 infrastructure。**

---

## Architecture in One Diagram

```text
                         用户问题（一个聚焦问题，answer-centric）
                                    │
                        agent（LLM 自由决定工具调用顺序/措辞）
                                    ▼
┌─────────────────────  Research loop（单会话，无持久状态）  ─────────────────────┐
│                                                                                 │
│  PaperSearch(query) ──► SearchIndex（预建本地语料索引，向量+全文）                 │
│       │                offset 分页续搜（同一 query 最多两次）→ 返回论文+chunk        │
│       ▼                ──► 论文/文本进入 state.docs（工作集，内容hash去重）          │
│  GatherEvidence(question)                                                        │
│       │  retrieve_texts：MMR 取 top-k=10 chunk                                    │
│       │  每个 chunk ──► LLM「按该问题总结 + 相关性打分 0-10」                       │
│       │                ──► Context{question, 摘要, 原样Text, score}               │
│       │  只保留 score>0，append 进 session.contexts（证据账本）                     │
│       │  只把 top-1 个证据回显给 agent（bounded context）                          │
│       ▼                                                                          │
│  GenerateAnswer                                                                  │
│       │  context_serializer：按 score 排序取 top-5、过滤 cutoff≥1、按 question 分组 │
│       │  qa LLM：只凭 context 写答案，必须引用 pqac-{id} → 提取引文 → BibTeX        │
│       │  无 context → CANNOT_ANSWER（拒绝无证据作答）                              │
│       ▼                                                                          │
│  Complete / Reset（或超时/截断→回退强制 gen_answer）                                │
└──────────────────────────────────────────────────────────────────────────────────┘

      语料侧（入库，与 loop 分离）：
      aadd(path) → md5 dockey → read_doc 分块(5000字符/重叠250) → 嵌入 → SearchIndex
                   引用先 peek 前 3 页 → LLM 生成 citation → 需要时从 providers 补水
```

关键观察：**整个 diagram 没有生命周期状态、没有持久化、没有 budget**——单会话、内存态、
agent 自由驱动。这是它与我们 Harness 需求最大的结构性差异，也是它不必学的地方。

---

## Core Concepts

1. **Paper Search ≠ Evidence Retrieval**（最重要）。搜索返回的是**论文**（粗粒度、廉价、
   vector 检索）；证据收集返回的是**按问题解读过的 chunk**（细粒度、LLM 逐块总结、昂贵）。
   论文是证据的候选源，不是证据本身。
2. **Evidence 是 question-bound 的**：`Context = {question, context(按该问题写的摘要),
   text(原样 chunk), score(0-10)}`。同一段原文，服务于不同子问题，会产生不同的 evidence。
   原样 Text 始终保留，用于引用与核对。
3. **证据账本是 append-only 的**：`session.contexts` 只增不减，去重靠 `c not in
   session.contexts`。这是 rich state 的正面示范。
4. **LLM 相关性分是过滤器，不是裁判**：score>0 才保留、score≥1 才进 answer、取 top-N。
   它**不**回答「证据够不够」（那是 sufficiency），只回答「这段原文和当前问题相不相关」。
5. **答案必须扎根证据**：context 为空 → CANNOT_ANSWER；答案引用必须可解析到
   context→Text→Doc。这是 grounding 的硬约束。
6. **Reading 没有逐级深入，只有 chunk 级检索**：论文一进来就全文分块进索引；「深度」体现
   在**问题的粒度**（更具体的子问题 → 检索到不同 chunk → 不同 evidence），不在论文侧。
7. **Query refinement 是 agent 的自由**：「tools can be invoked in any order by a
   language agent… narrow and broad search, different phrasing for gather evidence
   vs generate answer」。没有专门的 refinement 步骤。

---

## Important Files

| 文件 | 角色 | 关键点 |
|---|---|---|
| `src/paperqa/agents/tools.py` | 三个核心工具 | `PaperSearch`(109)、`GatherEvidence`(217)、`GenerateAnswer`(314)、`Complete`/`Reset` |
| `src/paperqa/agents/main.py` | agent 编排 | aviary/ldp 三种 runner；`run_fake_agent` 确定性基线 |
| `src/paperqa/docs.py` | 文档集合 | `aadd` 入库、`retrieve_texts`(MMR)、`aget_evidence`(证据)、`aquery`(答案) |
| `src/paperqa/types.py` | 数据模型 | `Doc`(75)、`Text`(155, chunk)、`Context`(238, 证据)、`PQASession`(319) |
| `src/paperqa/settings.py` | 配置 | `AnswerSettings`、`AgentSettings`；`context_serializer`(1202) |
| `src/paperqa/agents/search.py` | 索引 | `SearchIndex`(Tantivy 全文+向量)、offset 分页、`get_directory_index` |
| `src/paperqa/readers.py` | 文档解析 | `read_doc` 分块、媒体解析、peek 页 |
| `src/paperqa/clients/` | 元数据 provider | openalex/crossref/semantic_scholar/unpaywall/retractions/journal_quality |
| `src/paperqa/prompts.py` | 提示词 | summary / qa / citation 模板、`EXAMPLE_CITATION` |

**关键默认值（settings.py 实证）**：`evidence_k: 10`（每次收集取 10 块）、
`evidence_relevance_score_cutoff: 1`、`evidence_summary_length: "about 100 words"`、
`agent_evidence_n: 1`（**每次只回显 top-1 证据给 agent**）、`answer_max_sources: 5`、
`search_count: 8`（每次搜索返回 8 篇）、`max_concurrent_requests: 4`、
chunk `5000/250` 字符。

---

## Key Data Flow

```text
语料入库：path → md5 dockey → read_doc 分块 → embed → SearchIndex（预建）
          metadata：先 peek 1-3 页 → LLM 生成 citation → 按需从 providers 补水
                                          │
用户问题 → agent（LLM 驱动）
  1. PaperSearch(query, min/max_year) ──► 索引检索 → 论文 → state.docs（aadd_texts 嵌入）
  2. GatherEvidence(question)            ──► MMR 检索 top-10 chunk
                                              └─► 逐块 LLM: 按问题总结 + score
                                              └─► score>0 → session.contexts（append-only）
                                              └─► 回显 top-1 给 agent
  3. GenerateAnswer                       ──► context_serializer(top-5, cutoff≥1, 按问题分组)
                                              └─► qa LLM：grounded answer + pqac 引用
                                              └─► populate_formatted_answers_and_bib
  4. Complete / Reset；截断/超时 → 回退强制 gen_answer
```

**研究语义链**：`论文(chunk) → 按问题的 evidence(summary+score) → 证据账本 →
排序筛选 → grounded answer → citation → BibTeX`。这正好对应我们 P10 的
`Claim→Evidence→Paper→Locator` 链，只是 paper-qa 是「单答案」而非「证据账本→综合报告」。

---

## Key State Model

paper-qa 的状态**全部在内存**，没有持久化、没有生命周期 phase：

```text
PQASession（一次问答的会话态）
├── question                主问题
├── contexts: list[Context] ← 证据账本（append-only，去重）
│     Context{ id(pqac-xxxx), question, context(按问题摘要), text(原样chunk),
│              score(0-10) }
├── raw_answer / answer / answer_reasoning
├── context（serializer 产物，本次答案用到的 bounded context 串）
├── used_contexts: set[str]      ← 本次答案实际引用的 evidence id
├── citations → BibTeX / formatted answer
└── token 计数

EnvironmentState（agent 运行态）
├── docs: Docs                    ← 工作论文集（docs dict + texts_index）
├── question
├── action_log                    ← 工具调用记录（ephemeral）
└── status()                      ← 实时状态字符串（给 agent 看）
```

对照前两份 Study：spec-kit 把状态外置到 6 个文件；old-search-harness 把状态切碎成
10+ artifact；paper-qa 把状态留在内存、靠 agent 的一次性会话推进。三者都**不是**
我们的形态——我们要 spec-kit 的「状态外置、可重建」+ paper-qa 的「研究语义分层」，
用 Python 持久化。

---

## Design Decisions Worth Learning

### Decision 1 — Paper Search 与 Evidence Retrieval 分开（本 Study 最重要的决策）

**Problem**：一次问答要同时解决「找到相关论文」和「从论文里取出支持证据」两件事，但它们的
对象与成本完全不同。

**Design**：两个独立工具。`PaperSearch` 在**论文粒度**上工作——对预建索引做 vector 检索，
返回论文（+其全部 chunk），廉价、可并发、可 offset 分页续搜。`GatherEvidence` 在
**chunk 粒度**上工作——从工作集里 MMR 取 top-k chunk，逐块让 LLM「按当前问题总结+打分」，
产出 question-bound 证据，昂贵、LLM 密集、不可与自身并发。

**Why**：论文是粗粒度候选，用来决定「哪些论文值得深入」；证据是细粒度事实，用来支撑
最终论断。把两者混在一个步骤里，要么检索粒度太粗（证据不可用）、要么把每篇论文全文塞进
prompt（成本爆炸）。

**Trade-off**：需要两套机制（索引检索 + 证据总结）与两套预算；agent 必须学会在两者间
编排。paper-qa 为此引入完整 agent 循环，这是它的主要复杂度来源。

**我们是否存在同样的问题**：是。我们的 RESEARCH 循环同样需要「发现候选 → 从候选里取证据」
两层。**是否有更简单的实现**：spec-kit 的 Candidate/Curated/Evidence 三层 state 文件
就是同一个分离在状态层的体现——论文进 candidates/curated，证据进 evidence.md。
**结论**：采纳分离，但用 state 文件（spec-kit）承载，不引入独立 agent 编排层。

---

### Decision 2 — Evidence 是 question-bound 的三元组（摘要 + 原样 + 分数）

**Problem**：一段原文对问题的意义，无法用「整段原文」直接表达（太长），也无法用「单条摘录」
表达（不同的子问题需要不同的解读）。

**Design**：`Context{question, context(≤100 词、按该问题写的摘要), text(原样 chunk),
score(0-10)}`。LLM 逐块生成；`text` 永远保留原始 chunk 供引用核对；`context` 是
「这段原文对当前问题意味着什么」的可消费表述；`score` 用于排序过滤。

**Why**：把「证据」定义为「原文 × 问题的函数」而非「原文本身」，是 query-specific
evidence 的精确实现。原样保留解决可追溯性（P10），按问题总结解决可消费性。

**Trade-off**：同一 chunk 服务不同问题时要重复总结（LLM 成本 × 问题数 × chunk 数）。
paper-qa 用 `max_concurrent_requests` 并行缓解，但仍是最贵的一步。

**我们是否存在同样的问题**：是——我们 P10 的 Evidence 需要「Claim→Evidence→Paper→Locator」。
**是否有更简单的实现**：第一版可以只存 verbatim excerpt + locator + stance，把
「按问题总结」推迟到证据真正要被写进某个 claim 时再做（懒总结）。paper-qa 是 eager 的
（gather 时就总结），我们的证据生命周期更长（一个 evidence 服务于多个 claim），懒总结
更省。
**结论**：采纳「原样 excerpt + locator + stance」为证据本体；「question-bound 摘要」
作为可选投影（P15-17 的 projection 思路），按需生成。

---

### Decision 3 — LLM 相关性分是过滤器，不是充分性裁判

**Problem**：证据收集后，怎么从一堆 chunk 里筛出真正相关、且可用的那些？

**Design**：每个 context 带 LLM 打分 0-10。`score>0` 才进账本（连不相关的都丢掉）、
`score≥1` 才进答案、排序取 top-N。没有任何「总分」「充分性阈值」——分数只用于
**局部排序与过滤**，不回答「证据够不够」。

**Why**：这是 old-search-harness 的对照答案。old harness 把 5 类异构指标加权成一个
`sufficiency_score` 去决定继续还是停止（false precision，见上一份 Study）；paper-qa
把分数限制在「这段 chunk 与这个问题相关吗」这个它确实能答的问题上，不越权。

**Trade-off**：分数是 LLM 主观输出，可能漂移；但作为粗过滤（>0）足够鲁棒，且 dedup
在分数之外独立做，不互相污染。

**我们是否存在同样的问题**：是。**是否有更简单的实现**：分数可以只是一个
supporting/contradicting/qualifying 的 stance + 一个 0-1 相关位，不必是 0-10。
**结论**：采纳「分数只做过滤与排序、不做充分性判断」的原则（P13）；分数形态可以是
typed stance + 相关位，而非 0-10 标量。

---

### Decision 4 — 答案必须扎根证据：无证据 → 拒绝作答

**Problem**：如何强制「答案只在证据上说话」？

**Design**：`context_serializer` 把证据按 score 排序、取 top-5、过滤 cutoff≥1、按
question 分组渲染进 prompt；若 context 串为空 → 直接输出 `CANNOT_ANSWER`，不调用
答案模型。答案 prompt 要求用 `pqac-{id}` 引用 evidence；事后用正则提取引文、构建
BibTeX、解析引用 → context → Text → Doc 的追溯链。另有两个保护：`EXAMPLE_CITATION`
出现在答案里会被剔除（防模型偷抄模板）、`answer_filter_extra_background` 剥离模型自带的
背景信息（防越权引入证据外的内容）。

**Why**：grounding 不是靠 prompt 哀求，而是靠「没证据就短路」+「引用必须可解析」两层
硬约束。这正是 P8「Paper Is Not Evidence」与 P10 可追溯性的执行层。

**Trade-off**：强行限制会让模型在某些题上答不了（CANNOT_ANSWER 的诚实代价）；引用解析
对模型输出格式有假设，需要事后清洗。

**我们是否存在同样的问题**：是——我们的 claim 必须能追到 evidence。**是否有更简单的实现**：
不必复刻 BibTeX/引用解析全套；只要「claim 必须列出其 evidence 的 locator + 立场」，
结构校验由 Python 做。
**结论**：采纳「无证据拒绝结论 + 引用可解析」双约束；引用解析的复杂度按需裁剪。

---

### Decision 5 — Query refinement 是 agent 的工具选择自由，不是专门步骤

**Problem**：问题要不要改措辞、换粒度、拆子问题？

**Design**：不设 refinement 步骤。README 明说工具可任意顺序调用：agent 可以做
narrow+broad 两次搜索、用不同措辞 gather evidence、对已生成的答案迭代。
`GatherEvidence` 支持换入更具体的子问题（`state.session.question = question`，gather 完
还原）；`prior_answer_prompt` 支持对已有答案迭代。

**Why**：检索/证据收集的最优方式取决于问题本身，固定步骤无法覆盖。把决策权交给 LLM，
让它在证据反馈中自行调整。

**Trade-off**：refinement 质量完全依赖 agent 的自由发挥——没有显式的 gap 记录，agent
可能重复搜同一方向，可能过早收敛。这是「agent 自由」与「gap 驱动」的取舍点。

**我们是否存在同样的问题**：是，而且我们更想要显式版本。**是否有更简单的实现**：不依赖
agent 自由，而是把「未解决的 gap」作为 state（每 gap 一个记录），refinement 由
gap→新查询的确定性映射 + Claude 判断触发（P7 Gap-Driven Research）。这比 paper-qa
更结构化了。
**结论**：采纳「refinement 发生」的结论（它必须在证据反馈后发生），但用
P7 的 gap 驱动代替 agent 自由发挥。

---

### Decision 6 — 阅读只有 chunk 级，深度体现在问题粒度（negative 对照）

**Problem**：论文怎么读？

**Design**：论文入库时全文分块（5000/250 字符）进索引；不设逐级深入（无
abstract→section→full 的阶梯）。「读得深不深」由问题的粒度决定——更具体的子问题检索到
更精确的 chunk。metadata 侧倒是懒的：引用先 peek 前 3 页让 LLM 生成，整库补水按需
（`is_hydration_needed` → providers）。

**Why**：对 RAG 问答，chunk 级检索 + 逐块总结已经足够；逐级阅读是多余的控制流。

**Trade-off**：全文入库的解析成本对每篇论文都付了；对只贡献少量证据的论文是浪费。
old-search-harness 的 brief/head/section 逐级阅读正是为了省这笔成本。

**我们是否存在同样的问题**：是。**是否有更简单的实现**：两种极端之间取中——第一版按
「论文的 section 定位」检索（OpenAlex/arXiv 已有 section 结构时直接用），
不必全文入库；证据定位到 section 级别即可（P10 要求 Section Locator）。
**结论**：采纳「不逐级阅读、按问题取块」的效率观点；但我们的 locator 到 section 粒度，
且可以 lazy（只对进 curated 的论文深读），不必全文入库。

---

### Decision 7 — deterministic retrieval 与 LLM 的分界

**Problem**：哪些步骤可以确定性执行，哪些必须依赖 LLM？

**Design**：分界非常干净——

| 确定性（Python） | LLM（语义） |
|---|---|
| 索引检索（Tantivy 向量+全文、offset 分页） | 搜索 query 的措辞（agent / fake 模式也先让 LLM 提 3 条 query） |
| 入库分块、content-hash 去重 | 逐块「按问题总结 + 相关性打分」 |
| MMR top-k、score 过滤、排序、agent_evidence_n 回显 | citation 从 peek 页生成 |
| context_serializer（排序/分组/token 预算） | 最终 grounded answer |
| 引用提取、BibTeX、CANNOT_ANSWER 短路 | 答案迭代（prior_answer_prompt） |

**Why**：确定性部分负责「检索机制、去重、预算、结构、追溯」，LLM 部分负责「这段原文对
这个问题意味着什么」——与我们的 ADR（Claude=语义、Python=确定性记账）完全同构。

**Trade-off**：分界靠工具接口维持，agent 层会把两者搅在一起（工具顺序由 LLM 定）。

**我们是否存在同样的问题**：是——这正是我们 ADR 要落地的边界。**是否有更简单的实现**：
我们不必引入索引基础设施，确定性层更薄（检索是 API 调用 + 状态校验 + 记账）。
**结论**：这张表就是我们的 policy/mechanism 边界清单，直接进 ADR。

---

## What We Should Borrow

1. **Paper Search ≠ Evidence Retrieval 分层**（Decision 1）：候选论文层与证据层分开，
   spec-kit 的 Candidates/Curated/Evidence 文件分层与之一致。这是研究语义的骨架。
2. **Evidence 记录结构**（Decision 2）：question-bound 的三元组思路——原样 excerpt
   + locator 为主，按问题摘要为可选投影。直接服务 P10。
3. **分数只做过滤排序、不做充分性判断**（Decision 3）：P13 的实证；区别于
   old-search-harness 的 sufficiency 标量。
4. **无证据 → 拒绝作答**（Decision 4）：grounding 双约束（短路 + 引用可解析）。P8/P10
   的执行层。
5. **MMR 多样性检索**：避免证据全部来自同一篇论文。我们做多源证据时同样需要多样性约束。
6. **证据账本 append-only + 去重**：session.contexts 只增不减，rich state 正面示范。
7. **bounded context 回显**（agent_evidence_n=1）：给 agent 看的证据是「状态的一个
   view」，不是全部状态——P21（Context Is a View of State）的实证。
8. **content-hash 去重**（dockey=md5）：防同一论文重复入库。
9. **fake agent 确定性基线**：无 LLM 编排的固定顺序模式（LLM 提 query → 搜 → gather →
   answer），可作为我们的测试/对比基线。
10. **确定性引用链路**：answer 引用 → context → Text → Doc 可解析，BibTeX 渲染。
    我们做报告的 evidence-first 引用（spec-kit 已借鉴过 evidence-first reporting）。

## What We Should Not Borrow

1. **完整 RAG 索引基础设施**：Tantivy SearchIndex、embedding 管线、MMR 实现——我们检索是
   provider API（DeepXiv/arXiv/OpenAlex 搜索），不建本地全文索引。
2. **aviary/ldp agent 框架**（ToolSelector/RolloutManager/Environment）：我们的 agent
   runtime 是 Claude Code，不是 Python agent loop。Python 只做确定性动作。
3. **媒体/视觉增强**（ParsedMedia、图/表 enrichment、多模态 message）：论文图表证据是
   后期能力，第一版不做。
4. **元数据 provider 全家桶**（openalex/crossref/semantic_scholar/unpaywall/retractions/
   journal_quality）：最多选一个检索 provider；journal_quality/retractions 这类外围
   「质量过滤」是通用 RAG 的复杂度。
5. **1290 行 settings 配置面**：我们的配置按 spec-kit 保持精简。
6. **单答案范式本身**：paper-qa 输出一个 grounded answer；我们要的是证据账本 → 多论文
   比较 → 综合报告 + 非共识。它的 gen_answer 只是我们 SYNTHESIZE 的一个组件。
7. **pre/post 可配置管线**（预推理、Extra Background 剥离等润色步骤）：答案是
   state 的投影，不做多层可配置 post 处理。
8. **内存态会话**：无持久化、无 resume、无 budget。我们必须持久化（P2/P3/P5）——
   paper-qa 在这一点上不如 spec-kit 和 old-search-harness。

## Conflicts with PROJECT_VISION

1. **Answer-centric vs Loop-centric**：paper-qa 是「一个问题 → 一个 grounded 答案」；
   我们是「一个 mission → 证据账本 → 综合 → 报告」。它的「检索→证据→答案」是**循环内的
   一次迭代**，不是整个循环。我们采纳其研究语义分层，但嵌入我们的 PLAN/RESEARCH/REVIEW/
   SYNTHESIZE 生命周期。
2. **无持久状态 vs P2/P3**：paper-qa 会话不落盘、不可 resume。P2（Rich Externalized
   State）、P3（Resume Restores Research Process）要求全部研究状态可重建。矛盾。
3. **无 budget/stop vs P5/P13**：paper-qa 靠 agent 自由 + timeout，没有预算台账与
   typed stop conditions。spec-kit 与 old-search-harness 都更强。我们取前者。
4. **Query refinement 靠 agent 自由 vs P7（Gap-Driven）**：我们要求 refinement 由
   证据账本中的显式 gap 驱动，而不是 LLM 随意换措辞。更结构化的版本。
5. **分数 0-10 vs P13（Criteria over magic scores）**：0-10 相关性分作为**过滤器**可以
   接受（它不冒充充分性），但我们的 stance 记录（supporting/contradicting/qualifying）
   比数字更能表达证据立场。倾向 typed stance + 相关位。

## Questions Still Open

1. **Evidence 本体**：第一版是「verbatim excerpt + section locator + stance」就够，还是
   立刻引入 paper-qa 式「question-bound 摘要」？倾向前者 + 懒总结，待 Architecture 定。
2. **分数形态**：0-10 标量 vs typed stance + 相关位？我们 P10 的 stance 已经是 typed；
   还需要一个「相关度」数字做排序吗，还是按 gap 覆盖排序就够了？
3. **检索粒度**：locator 定位到 section（论文已有结构）够不够？要不要全文入库才能保证
   verbatim 可校验（old-search-harness 的教训）？这决定 evidence.py 的校验强度。
4. **多源多样性**：MMR 的多样性约束，我们是否需要显式机制（如「同论文证据上限」）？还是
   gap 驱动天然多样？
5. **fake-agent 基线**：是否值得在我们 harness 里保留一个「无 Claude 语义编排」的
   确定性跑通模式，用于对比与回归？

## Candidate ADRs Influenced by This Project

1. **ADR：Paper Search ≠ Evidence Retrieval。** 候选论文层与证据层是两种 state；发现与
   取证的检索粒度、预算、成本各不相同。（Decision 1）
2. **ADR：Evidence 记录 = {原样 excerpt + Section locator + stance + doc link}；按问题
   摘要是可选投影，按需生成。**（Decision 2，P10）
3. **ADR：相关性分数只做过滤与排序，不做充分性判断；不做加权总分。**（Decision 3，P13）
4. **ADR：结论必须 grounding——无证据拒绝断言；每个 claim 列出其 evidence locator +
   立场，Python 结构校验。**（Decision 4，P8/P10）
5. **ADR：Query refinement 是 gap 驱动的——证据账本中的未解决 gap 产生下一查询，
   由 Claude 判断触发。**（Decision 7、P7）
6. **ADR：LLM/deterministic 边界清单**（采纳 Decision 7 的表）：Python 负责检索机制、
   去重、预算、排序、引用解析、grounding 校验；Claude 负责 query 措辞、逐段语义、
   evidence 立场、答案综合。

## 一句话结论

paper-qa 贡献的不是 Harness 外壳（它在状态持久化、budget、stop 上都弱于我们前两份
Study），而是**外壳内部的论文研究语义**：Paper Search ≠ Evidence Retrieval、
evidence 是 question-bound 的三元组、相关性分只是过滤器、答案必须扎根证据、LLM 与
deterministic retrieval 有干净的分界。这些语义分层直接进我们的 candidate ADR；
它的 RAG 基础设施（索引、agent 框架、元数据全家桶、单答案范式）则明确不迁移。
研究语义从 paper-qa 拿，生命周期从 spec-kit 拿，工程 backbone 从 old-search-harness 拿——
三者合起来，就是我们 Architecture 阶段的输入。
