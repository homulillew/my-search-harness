# ADR-008：论文通过按需 Source Access 支持渐进式阅读

* **状态**：已接受
* **阶段**：Runtime / Source Access
* **日期**：2026-08-09
* **影响范围**：Paper Reading、Source Grounding、Paper Analysis、Completion Check、Delivery Citation Verification
* **关联决策**：

  * ADR-001 — Claude Code 驱动研究循环，Python Harness 守住系统不变量
  * ADR-004 — 持久化论文级理解与领域级理解
  * ADR-005 — Research State 通过类型化变更在 ResearchRun 边界内原子更新
  * ADR-006 — Research State 通过用途化投影渲染为有界 Context
  * ADR-007 — 论文搜索通过可替换的 Paper Search Provider 与 Research Loop 解耦

## 背景

ADR-007 已经定义论文搜索的边界：

```text
search_papers
      ↓
PaperSearchHit[]
      ↓
Claude selects
      ↓
RetainPapers
      ↓
Persistent Paper
```

但论文被 Retain 之后，Researcher 仍然需要读取论文内容，才能形成 ADR-004 中定义的：

```text
Paper Analysis
```

如果每次读取论文都默认把全文放入 Claude Context：

```text
Paper
  ↓
full text
  ↓
Claude Context
```

那么随着论文长度和工作集增长，Context 成本会快速放大。

另一种做法是建立固定的阅读流程：

```text
ABSTRACT
→ HEAD
→ SECTION
→ DEEP_READ
→ FULL_READ
```

并持久化：

```text
reading_depth
reading_progress
sections_read
```

但真实研究并不是严格线性的。

Claude 可能只看摘要就判断论文不值得继续研究，也可能因为当前 Investigation Gap 很具体，直接阅读某个关键 Section；在其它情况下，则可能需要全文才能理解跨章节机制。

因此本 ADR 要解决的问题不是：

> **论文当前处于第几级阅读状态？**

而是：

> **Claude 如何按当前研究需要，以逐步增加信息成本的方式访问论文内容，同时保持来源可核验，并避免把 Provider-specific 阅读接口泄漏进 Research Domain？**

## 决策

渐进式阅读被定义为一种：

> **按需 Source Access 策略。**

它不是 Lifecycle，也不是 Paper 的 Reading State Machine。

Retained Paper 通过两个最小读取能力访问：

```text
inspect_source(paper_ref)

read_source(paper_ref, locator?)
```

整体链路为：

```text
PaperSearchHit
     │
     │ Claude decides worth researching
     ▼
RetainPapers
     │
     ▼
   Paper P8
     │
     ├───────────────┐
     ▼               ▼
inspect_source   read_source
     │               │
     ▼               ▼
Source Outline   Source Content
     │               │
     └───────┬───────┘
             ▼
      Claude Interpretation
             ▼
        Paper Analysis
             ▼
   Literature Landscape
```

核心原则是：

> **Progressive Reading means increasing access cost on demand, not passing through fixed reading stages.**

即：

> **渐进式阅读意味着按需增加读取成本，而不是强制逐级阅读。**

## Progressive Reading 不是 Lifecycle

V1 不建立：

```text
BRIEF_READ
HEAD_READ
SECTION_READ
DEEP_READ
FULL_READ
```

这样的 Lifecycle Mode。

也不在 `Paper` 中保存：

```text
reading_depth
current_reading_stage
reading_complete
```

因为同一篇论文对于不同 Research Requirement 或 Investigation Gap，所需的阅读粒度可能不同。

例如：

```text
P8
↓
abstract 已足够判断无关
↓
停止
```

也可能：

```text
P12
↓
当前 Gap 明确涉及实验成本
↓
直接读取 Experiments
```

或者：

```text
P17
↓
多个章节共同解释核心机制
↓
读取全文
```

因此：

> **Lifecycle 描述控制状态；Reading 描述 Researcher 的访问策略。**

## Cheap Triage 发生在 Retain 之前

`PaperSearchHit` 可以携带：

```text
title
authors?
abstract?
published_at?
identifiers?
url?
```

这些信息已经足以支持低成本的第一轮判断：

> **这篇论文是否值得进入当前 Research Run 的正式工作集？**

因此 V1 不要求额外建立：

```text
brief_paper
preview_candidate
candidate_read
```

等 Pre-Retain 阅读步骤。

如果 Abstract 仍不足以判断是否值得深入研究，Claude可以选择：

```text
RetainPapers
↓
Paper P8
↓
inspect_source / read_source
```

这并不意味着 Retain 是 endorsement。

Retain 只表示：

> **这篇论文值得正式进入当前 Research Run，并允许投入进一步研究成本。**

## 正式 Source Access 只针对 Retained Paper

`inspect_source` 和 `read_source` 只接受当前 Research Run 中已有稳定身份的 `Paper`。

即：

```text
Search Hit
↓
Retain
↓
P8
↓
Source Access
```

而不是：

```text
Search Hit
↓
直接深读外部临时结果
```

原因是，一旦开始 substantive reading，这篇论文已经成为当前 Run 的正式研究材料。

使用 Stable Paper Ref 可以保证后续：

```text
Resume
Audit
Paper Analysis
Source Grounding
Completion Verification
```

都可以明确回到：

```text
P8
```

而不依赖一次性的 Provider Result。

原则是：

> **Cheap triage may happen before Retain; substantive reading happens after Retain.**

## `inspect_source` 提供论文地图

`inspect_source(paper_ref)` 回答：

> **这篇论文有哪些可以继续读取的位置？**

概念上可以返回：

```text
P8

§1 Introduction
§2 Related Work
§3 Method
  ├── §3.1 Search
  └── §3.2 Verifier
§4 Experiments
§5 Limitations
```

它的职责是：

> **Navigation。**

而不是：

> **Analysis。**

因此 `inspect_source` 可以包含：

```text
section identifier
section title
hierarchy
optional size / token estimate
```

但不应要求生成：

```text
section importance
recommended sections
relevance score
LLM-generated section analysis
```

Python 不负责判断哪个 Section 值得读。

Claude 根据当前 Research Requirement、Investigation Gap 和已有 Paper Analysis 自己选择下一步。

## `read_source` 返回来源内容

`read_source(paper_ref, locator?)` 回答：

> **这个来源位置实际写了什么？**

例如：

```text
read_source(P8, §3 Method)
```

或者：

```text
read_source(P8, §4 Experiments)
```

如果 `locator` 为空：

```text
read_source(P8)
```

表示请求当前可访问的完整论文内容。

全文读取是合法能力，但它是：

> **昂贵 fallback。**

而不是默认入口。

Harness 不根据语义自行决定何时必须全文阅读。

是否值得承担全文读取成本仍然由 Claude 决定。

## Source Locator 同时用于 Grounding 与重新读取

ADR-004 已经定义：

```text
LiteratureSource
├── paper_ref
├── relation
└── locator?
```

ADR-008 复用同一个 `Source Locator` 作为 Source Access 的导航语义。

例如：

```text
LandscapeFinding LF7

sources:
- paper_ref: P8
  relation: supports
  locator: §4.3 Cost Analysis
```

之后 Researcher、Completion Checker 或 Delivery 都可以：

```text
read_source(P8, §4.3 Cost Analysis)
```

重新取得相同来源位置。

因此：

```text
read_source
     ↓
Source Content
     ↓
Claude Interpretation
     ↓
Landscape Finding
     ↓
Literature Source
     ├── paper_ref
     └── locator
             ↓
       read_source again
```

形成完整 Grounding 闭环。

原则是：

> **同一个 Locator 同时用于指出证据和重新访问证据。**

V1 不额外建立：

```text
ReadingSelector
DeepReadTarget
ContentSelector
```

等第二套定位模型。

## V1 不要求支持所有 Locator 类型

Source Locator 在语义上可以逐步支持：

```text
section
page
table
figure
paragraph
```

但本 ADR 不要求 V1 一次实现全部定位方式。

当前实现可以先可靠支持：

```text
section
whole source
```

以后只有当新的 Source Adapter 或真实研究场景证明需要时，再增加更精确的 Locator 支持。

因此：

> **Locator Model 可以比当前 Adapter Capability 更丰富，但 Adapter 不得假装支持自己无法可靠定位的粒度。**

## Source Access 返回值是临时 Observation

`inspect_source` 和 `read_source` 的返回值属于 Runtime DTO，而不是 Persistent Domain Entity。

概念上：

```text
SourceOutline
```

以及：

```text
SourceContent
```

都只是当前一次外部读取结果。

它们不进入：

```text
ResearchRun.state.json
```

真正需要持久化的是阅读后形成的研究语义：

```text
Paper Analysis
Approach Family
Landscape Finding
Open Problem
Investigation Gap
Literature Source
```

因此：

> **保存理解，不保存所有被读过的原始内容。**

如果未来为了性能对论文正文做本地 Cache，该 Cache 仍然是 Infrastructure，而不是 Research State。

## Source Content 必须保留最小 Provenance

`read_source` 返回的内容必须能够回答：

> **这段内容来自哪篇论文的什么位置？**

最小语义为：

```text
SourceContent
├── paper_ref
├── locator?
└── content
```

例如：

```text
paper_ref = P8
locator   = §4 Experiments
content   = ...
```

如果调用者请求了一个模糊 Locator，而 Adapter 实际解析到了更具体的位置，则返回值应携带：

> **实际内容对应的 Locator。**

本 ADR 不要求同时持久化：

```text
requested_locator
provider_request
retrieved_at
content_hash
reading_depth
confidence
```

除非后续真实需求证明这些信息不可缺少。

## Provider-generated Summary 不是 Primary Source

Source Access 必须区分：

```text
论文实际内容
```

与：

```text
Provider 生成的摘要或解释
```

例如某个 Provider 可能提供：

```text
TLDR
section summary
AI overview
```

这些内容可以作为研究便利信息，但不能通过：

```text
read_source
```

伪装成论文原文。

`read_source` 的稳定语义必须是：

> **返回可以回溯到真实论文来源的内容。**

因此：

```text
Provider-generated interpretation
≠
Primary Source Content
```

这保证 ADR-004 的 Source Grounding 最终能够回到论文，而不是回到 Provider 对论文的二次解释。

## 阅读结果不自动修改 Research State

和 ADR-007 中的 Search 一样：

```text
inspect_source
read_source
```

都只产生 External Observation。

它们不能自动：

```text
生成 Paper Analysis
创建 Landscape Finding
更新 Approach Family
关闭 Investigation Gap
```

正确流程是：

```text
read_source
      ↓
Source Content
      ↓
Claude Interpretation
      ↓
PUT / MERGE / Domain Command
      ↓
Persistent Research State
```

Claude可以连续读取多个 Section：

```text
§3 Method
§4 Experiments
§5 Limitations
```

然后基于整体语义判断，一次性原子更新：

```text
Paper Analysis
+
Landscape Finding
+
Investigation Gap
```

这与 ADR-005 中：

> **一次 Claude 语义判断作为一个原子 Batch 提交。**

保持一致。

## 不持久化 Reading Progress

V1 不在 `Paper` 中保存：

```text
sections_read
last_section
reading_depth
read_count
reading_complete
```

因为这些信息主要描述：

> **Claude 做过什么。**

而真正服务 Resume 的信息应该描述：

> **Claude 已经理解了什么。**

这个职责由：

```text
Paper Analysis
```

承担。

如果为了 Debug、Cost 或 Audit 需要知道：

```text
读取过哪些 Section
```

可以记录在 Action / Event History 中。

但 Event History 不是 authoritative Research State。

原则是：

> **保存语义结果，不保存完整认知轨迹。**

## 不存在全局“阅读完成”

V1 不定义：

```text
Paper.reading_complete = true
```

因为对于一篇论文，“读完”没有稳定的全局研究语义。

对于一个 Requirement：

```text
Method section
```

可能已经足够。

对于另一个后来出现的 Finding：

```text
Experiments / Limitations
```

又可能需要重新访问同一篇论文。

因此系统判断完成的是：

```text
Research Contract 是否得到足够领域理解
```

而不是：

```text
每一篇 Paper 是否被完整阅读
```

最终停止条件仍由 Completion Check 判断。

## Source Access Failure 必须保持语义精度

读取失败不能统一退化成：

```text
None
""
[]
```

至少需要区分以下三种语义：

```text
SOURCE_UNAVAILABLE
```

表示论文来源当前无法访问，例如网络失败、Provider 不可用或正文无法取得。

```text
LOCATOR_NOT_FOUND
```

表示 Source 本身可访问，但请求的位置不存在。

例如：

```text
read_source(P8, "Efficiency Analysis")
```

而论文中不存在对应 Section。

```text
UNSUPPORTED_LOCATOR
```

表示当前 Source Adapter 可以访问论文，但无法可靠支持请求的定位粒度。

例如调用者要求：

```text
Table 2
```

而当前 Adapter 只能可靠定位到 Section。

在这种情况下，Adapter 不得静默返回：

```text
整个全文
```

或者：

```text
Experiments section
```

并假装满足了精确读取要求。

原则是：

> **Adapter 可以明确说做不到，但不能静默降低来源定位精度。**

对于无法可靠解析的 Provider Response，还应 fail closed，而不是把未知数据包装成合法 Source Content。

## Empty Source Content 不是正常成功

论文搜索：

```text
search_papers
→ []
```

可以合法表示：

> 搜索成功，没有结果。

但：

```text
read_source(P8, §4)
→ ""
```

通常不应被视为成功。

如果已经声称某个 Source Locator 被成功读取，却没有取得实际内容，应返回明确错误，例如：

```text
LOCATOR_NOT_FOUND
```

或者：

```text
INVALID_RESPONSE
```

具体错误取决于 Adapter 能否可靠判断原因。

因此：

> **Empty Search Result 可以成功；Empty Source Content 默认不能成功。**

## Source Access 不依赖 DeepXiv 的具体阅读模式

V1 可以使用 DeepXiv 实现 Source Access。

DeepXiv 的：

```text
head
section
raw
```

可以自然映射为：

```text
inspect_source
read_source(locator)
read_source(full)
```

但 Harness 不把 DeepXiv 的：

```text
brief
head
preview
section
raw
```

原样提升为长期 Runtime Contract。

尤其不建立：

```text
brief_source
preview_source
deep_read
full_read
```

等 Provider-specific 核心操作。

原则是：

> **Harness 定义稳定阅读语义；Adapter 吸收具体 Provider 的访问方式。**

如果未来增加本地 PDF、arXiv HTML 或其它 Source Adapter，只要仍然能够实现：

```text
inspect_source
read_source
```

Research Loop 就无需修改。

本 ADR 不要求现在建立完整 Source Provider Framework。

## 不引入 RAG 基础设施

渐进式阅读不等于建立自动 Evidence Retrieval 系统。

V1 明确不因此引入：

```text
全文 Chunk Index
Embedding
Vector Database
MMR Retrieval
Semantic Chunk Ranking
LLM Evidence Scoring
Reading Agent
ProgressiveReadingManager
```

这些机制未来可能在真实规模证明必要，但当前 Claude 已经拥有 Research Semantic Authority。

因此当前更简单的路径是：

```text
Claude chooses what to inspect
        ↓
Harness fetches that source region
```

而不是：

```text
Claude asks semantic question
        ↓
Python retrieval pipeline guesses relevant chunks
        ↓
LLM ranks them
        ↓
return top evidence
```

原则是：

> **Claude 选择读哪里；Python 负责可靠地把那里取回来。**

## Budget 约束成本，不决定阅读策略

Source Access 可以具有不同资源成本：

```text
inspect_source
      cheap

read_source(section)
      higher

read_source(full)
      highest
```

具体 Cost Accounting 由实现阶段决定。

但 Budget 不负责判断：

> **当前是否应该深读某篇论文。**

只要没有违反 Hard Limit，是否继续投入阅读成本仍然由 Claude 根据当前研究需求决定。

因此：

> **Budget controls how much can be read; Claude decides what is worth reading.**

## Completion Check 可以使用 Source Access 核验已有来源

Source Access 不只服务 Researcher。

Completion Checker 可以基于已有 Grounding：

```text
LF7
└── P8 @ §4.3
```

执行：

```text
read_source(P8, §4.3)
```

核验已有 Research State 是否与原论文一致。

但 Completion Checker 不能借 Source Access 演变成新的 Research Loop：

```text
广泛搜索新论文
扩张技术路线
建立大量新 Finding
```

如果已有来源不足，需要新的外部研究，应返回：

```text
CONTINUE
```

或：

```text
UNCERTAIN
```

并回到 `RESEARCH`。

## Delivery 可以使用 Source Access 精修引用

Delivery 阶段也可以：

```text
read_source(P8, locator)
```

对已有 Finding 的 citation locator 进行精确核验或细化。

如果读取过程只是确认：

```text
§4
→ §4.3
```

而不改变领域语义，可以继续 Delivery。

如果原文反而证明：

```text
现有 Landscape Finding 存在实质错误
```

则必须：

```text
DELIVERY
→ RESEARCH
→ 修正 Research State
→ Completion Check
```

而不能在 Report 中静默修正领域事实。

## 不提前设计的内容

本 ADR 有意不决定：

```text
PDF parsing architecture
local source cache
Source Adapter registry
dynamic provider discovery
OCR pipeline
table extraction engine
figure extraction
page-level exact layout model
全文索引
embedding retrieval
citation graph traversal
跨 Provider source fallback
```

这些问题只有在真实实现或规模证明需要时再单独设计。

当前 ADR 只负责：

> **Retained Paper 的按需 Source Access。**

## 验证方式

后续实现至少应证明以下场景成立：

1. Search Hit 可以仅凭 title / abstract 被 Claude丢弃，而不进入 Source Access。
2. 只有 Retained Paper 才能通过 Stable Paper Ref 执行正式 Source Access。
3. Claude可以在不了解论文结构时调用 `inspect_source(P8)` 获得可继续导航的位置。
4. Claude如果已经知道目标 Section，可以直接 `read_source(P8, locator)`，不要求先调用 `inspect_source`。
5. `inspect_source` 不生成推荐 Section、Importance Score 或新的 Research Finding。
6. `read_source` 返回能够回溯到 `paper_ref + locator` 的真实来源内容。
7. Provider-generated TLDR 或 AI Summary 不会通过 `read_source` 冒充 Primary Source。
8. Claude可以读取一个或多个 Section 后，再显式更新 Paper Analysis。
9. `read_source` 不自动修改 Paper Analysis、Literature Landscape 或 Investigation Gap。
10. Paper 不需要保存 `reading_depth`、`sections_read` 或 `reading_complete` 才能 Resume。
11. Completion Checker 可以根据已有 `LiteratureSource` 的 `paper_ref + locator` 重新读取原文核验 Finding。
12. Delivery 可以对已有 Grounding 的 Locator 做精细化核验。
13. 请求不存在的 Section 时返回 `LOCATOR_NOT_FOUND`，而不是空字符串。
14. 请求当前 Adapter 无法可靠处理的 Locator 时返回 `UNSUPPORTED_LOCATOR`，而不是静默降低精度。
15. Source 当前无法访问时返回明确 Failure，而不是空 Source Content。
16. 全文读取可以存在，但不要求单独建立 `FULL_READ` Lifecycle 或 Operation。
17. 替换 DeepXiv 的具体读取实现时，不需要修改 Paper、Paper Analysis、Landscape 或 Research Loop。
18. 增加新的阅读方式不要求增加新的 Lifecycle Mode。
19. SourceOutline 和 SourceContent 可以作为临时 Runtime DTO 重建，而不成为 Persistent Research State。
20. 删除 Action / Event History 后，已有 Paper Analysis 和 Literature Sources 仍足以表达当前研究理解与 Grounding。

## 决策摘要

渐进式阅读最终保持为：

```text
PaperSearchHit
     │
     │ cheap triage
     ▼
RetainPapers
     │
     ▼
   Paper P8
     │
     ├──────────────┐
     ▼              ▼
inspect_source   read_source
     │              │
     ▼              ▼
source map      source content
     │              │
     └──────┬───────┘
            ▼
     Claude Interpretation
            ▼
       Paper Analysis
            ▼
  Literature Landscape
            │
            ▼
 paper_ref + locator
            │
            └────→ read_source again
```

核心原则是：

> **渐进式阅读是按需 Source Access，不是 Reading Lifecycle。**

> **先用便宜信息判断是否值得研究，再对 Retained Paper 按需增加读取成本。**

> **`inspect_source` 提供地图，`read_source` 提供原文。**

> **Claude 决定读哪里；Python 负责可靠地把那里取回来。**

> **保存论文理解和来源定位，不保存完整阅读轨迹。**

> **Provider-generated interpretation 不能冒充 Primary Source。**

> **Adapter 可以明确不支持某种定位粒度，但不能静默降低来源精度。**
