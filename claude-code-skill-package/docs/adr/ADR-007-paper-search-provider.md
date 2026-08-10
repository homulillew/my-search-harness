# ADR-007：论文搜索通过可替换的 Paper Search Provider 与 Research Loop 解耦

* **状态**：已接受
* **阶段**：Runtime / Paper Search
* **日期**：2026-08-09
* **影响范围**：Paper Search、External Research I/O、DeepXiv Integration、Provider Replacement
* **关联决策**：

  * ADR-001 — Claude Code 驱动研究循环，Python Harness 守住系统不变量
  * ADR-004 — 持久化论文级理解与领域级理解
  * ADR-005 — Research State 通过类型化变更在 ResearchRun 边界内原子更新
  * ADR-006 — Research State 通过用途化投影渲染为有界 Context

## 背景

V1 需要让 Claude 能够搜索论文。

当前计划使用：

```text
DeepXiv
```

作为主要论文搜索来源，并允许 Claude 在需要时使用网络搜索补充发现。

但 DeepXiv 只是当前选用的一种外部服务。

未来可能加入：

```text
OpenAlex
Semantic Scholar
arXiv API
其它论文搜索 API
```

如果 Research Loop 直接依赖 DeepXiv 的请求参数、返回结构和错误格式，那么更换或增加搜索服务时，就会迫使：

```text
Research Loop
Domain Model
Claude Tool Contract
```

一起修改。

这会把一个外部基础设施选择泄漏进研究核心。

另一方面，当前需求只是：

> **搜索论文。**

因此也没有必要提前设计完整 Plugin Framework、Provider Orchestrator 或多 Provider 调度系统。

本 ADR 只解决一个问题：

> **如何让论文搜索与具体搜索 API 解耦，使 V1 可以使用 DeepXiv，同时以后能够低成本替换或增加新的论文搜索服务？**

## 决策

Research Runtime 定义一个最小的论文搜索能力：

```text
PaperSearchProvider
```

Research Loop 依赖这个稳定能力，而不直接依赖 DeepXiv。

概念结构：

```text
                 Claude
                   │
                   ▼
            search_papers
                   │
                   ▼
          PaperSearchProvider
                   │
            ┌──────┴──────┐
            ▼             ▼
         DeepXiv       Future API
         Adapter        Adapter
            │             │
            └──────┬──────┘
                   ▼
            PaperSearchHit[]
                   │
             Claude selects
                   │
                   ▼
              RetainPapers
                   │
                   ▼
                Papers
```

V1 默认实现：

```text
DeepXivSearchProvider
```

未来增加新的论文搜索服务时，应通过新增 Adapter 实现相同的稳定搜索契约，而不是修改 Research Loop。

## PaperSearchProvider 保持最小

本 ADR 不冻结具体 Python Protocol、ABC 或 CLI 形式。

概念上只需要一个能力：

```text
search(request)
→ PaperSearchHit[]
```

例如：

```text
search_papers(
    query,
    limit
)
```

具体函数签名属于实现阶段决定。

V1 不把 DeepXiv 当前支持的全部高级参数复制进稳定 Contract，例如：

```text
authors
organizations
categories
venues
citation filters
rerank options
BM25 / vector options
provider-specific search modes
```

这些属于具体 Provider 的能力，而不是当前 Harness 已证明需要长期稳定支持的研究语义。

原则是：

> **Provider 新增功能，不等于 Harness 必须新增功能。**

只有当某个搜索约束成为跨 Provider、重复出现的真实研究需求时，才考虑把它提升进稳定 Search Contract。

## Search Result 是临时 Observation

论文搜索返回：

```text
PaperSearchHit
```

它只是一次外部搜索观察，不是 Persistent Research State，也不是新的 Domain Entity。

最小信息可以包括：

```text
PaperSearchHit
├── title
├── authors?
├── abstract?
├── published_at?
├── arxiv_id?
├── doi?
└── url?
```

具体字段可以根据 Provider 实际能力缺省。

`PaperSearchHit` 不拥有独立生命周期，也不使用类似：

```text
CandidatePaper
DiscoveredPaper
SearchResultEntity
```

这样的持久化模型。

基本流程为：

```text
search_papers
      ↓
PaperSearchHit[]
      ↓
Claude semantic selection
      ↓
RetainPapers
      ↓
Persistent Paper
```

也就是说：

> **搜索发现论文，Claude 决定哪些论文正式进入 Research Run。**

## Search 不隐式修改 Research State

调用：

```text
search_papers
```

不能自动：

```text
创建 Paper
更新 Paper Analysis
创建 Approach Family
创建 Landscape Finding
关闭 Investigation Gap
```

Search 只是 External Observation。

只有 Claude 做出明确语义判断后，才通过 ADR-005 已定义的 State Mutation / Domain Command 修改 Research State。

例如：

```text
Search
  ↓
hits
  ↓
Claude:
P3、P8 值得进一步研究
  ↓
RetainPapers
  ↓
ResearchRun.Papers
```

这继续遵守 ADR-001：

> **Claude 决定研究什么；Python 保证决定被可靠执行。**

## Provider 不是 Paper Identity

具体 Provider 只表示：

> **通过什么渠道发现了一篇论文。**

它不定义论文在 Research Domain 中的身份。

例如：

```text
DeepXiv
→ arXiv:2401.12345

Future Provider
→ DOI:10.xxxx/xxxx

Web Search
→ https://arxiv.org/abs/2401.12345
```

这些结果可能指向同一篇论文。

进入 `RetainPapers` 后，Harness 可以使用：

```text
DOI
arXiv ID
canonical URL
```

等稳定标识进行机械规范化和明确重复判断。

最终 Persistent Identity 是：

```text
Paper P8
```

而不是：

```text
deepxiv:2401.12345
```

因此替换或删除某个 Provider 不应该破坏已经存在的 Research State。

原则是：

> **Provider 是访问路线，不是论文身份。**

## Provider Failure 不得伪装成 Empty Result

论文搜索最重要的可靠性不变量是：

```text
搜索成功但没有结果
≠
Provider 调用失败
```

正常：

```text
search(...)
→ []
```

只表示：

> Provider 成功完成了这次搜索，但没有返回论文。

以下情况不能被转换为 `[]`：

```text
authentication failure
rate limit
timeout / network unavailable
server failure
malformed response
provider response schema changed
```

这些情况必须以明确失败返回。

概念上：

```text
ProviderError
```

即可。

本 ADR 不要求冻结复杂错误枚举，但实现必须保证：

> **Failure never masquerades as an empty search result.**

尤其对于无法识别或缺少必要字段的 Provider Response，应 fail closed，而不是猜测它意味着“没有结果”。

## DeepXiv 通过 Adapter 隔离

DeepXiv 的：

```text
request parameters
response envelopes
authentication
error semantics
API migrations
```

都属于：

```text
DeepXivSearchProvider
```

内部实现细节。

Research Loop 不读取 DeepXiv 原始 JSON，也不依赖其具体字段名。

概念上：

```text
DeepXiv API
      ↓
DeepXivSearchProvider
      ↓
PaperSearchHit[]
      ↓
Research Loop
```

如果 DeepXiv API 发生变化：

```text
旧字段 → 新字段
旧 response envelope → 新 envelope
```

应只修改 Adapter 和其测试。

不应该修改：

```text
ResearchRun
Paper
PaperAnalysis
LiteratureLandscape
CompletionCheck
Context Projection
Research Loop
```

## Web Search 保持独立

网络搜索与论文搜索不是同一个稳定能力。

Web Search 可能返回：

```text
论文页面
作者主页
Survey
项目主页
GitHub Repository
博客
会议页面
PDF
```

因此 V1 不强迫 Web Search 实现：

```text
PaperSearchProvider
```

也不把所有 Web Result 自动转换成 `PaperSearchHit`。

Claude 可以分别使用：

```text
search_papers
search_web
```

其中：

```text
search_papers
→ 结构化论文发现

search_web
→ 广泛网络发现
```

如果 Web Search 发现了一篇论文，再由 Claude 将其带入正常论文研究流程。

## 可替换不等于 Plugin Framework

本 ADR 所说的“可替换 / 可插拔”只要求：

> **新增论文搜索服务时，不修改 Research Loop。**

V1 不因此引入：

```text
Plugin SDK
Dynamic Plugin Discovery
Plugin Manifest
Dependency Injection Container
Provider Router
Provider Orchestrator
Automatic Fallback Engine
Provider Health State Machine
Hot Reload
```

实现阶段完全可以通过普通 Python composition 完成：

```text
DeepXivSearchProvider
      ↓
configured as current PaperSearchProvider
```

未来加入新 API：

```text
+ OpenAlexSearchProvider
+ config / composition change
```

即可。

原则是：

> **Composition-time replaceability is enough for V1.**

## Provider 选择属于研究策略

V1 可以配置：

```text
default paper search provider = DeepXiv
```

但 Harness 不自动执行：

```text
DeepXiv failed
→ OpenAlex
→ Semantic Scholar
→ Web Search
```

这样的 fallback chain。

如果 DeepXiv 返回失败，Claude可以根据当前研究语境决定：

```text
修改 query
使用网络搜索
切换另一个论文搜索 Provider
停止当前方向
```

因此：

> **Provider 的使用策略属于 Claude；Provider 调用的可靠执行属于 Python。**

## 不提前设计的内容

本 ADR 有意不决定：

```text
论文全文如何读取
Progressive Reading abstraction
Source Locator access
PDF parsing
Local PDF Provider
Citation graph lookup
多 Provider 同时搜索
自动结果聚合
跨 Provider semantic ranking
Provider fallback
Provider cache
Provider retry framework
动态插件发现
```

这些问题只有在真实实现证明需要统一架构时再单独设计。

当前 ADR 只负责：

> **论文搜索。**

## 验证方式

后续实现至少应证明以下场景成立：

1. V1 可以通过 DeepXiv 完成论文搜索。
2. Research Loop 不直接依赖 DeepXiv SDK 或 DeepXiv Response Schema。
3. DeepXiv 搜索结果会被转换成稳定的临时 `PaperSearchHit`。
4. 调用 `search_papers` 不会隐式修改 Research State。
5. Claude 可以明确选择某些 Search Hit，并通过 `RetainPapers` 将其加入 Persistent Papers。
6. Provider 正常返回零结果时，Claude可以可靠看到“搜索成功但没有结果”。
7. Authentication、Rate Limit、Network Failure 或 Invalid Response 不会被转换成空结果。
8. Provider Response Schema 变化只要求修改对应 Adapter，而不修改 Research Loop 或 Domain Model。
9. 同一篇论文从不同搜索来源发现后，可以在 Retain 阶段通过稳定论文标识进行机械规范化。
10. 增加一个新的论文搜索 API 时，核心修改应主要局限于：

    ```text
    new adapter
    configuration / composition
    adapter tests
    ```

    而无需修改 ResearchRun、Literature Landscape、Completion Check 或 Context Projection。
11. Web Search 可以作为独立补充能力存在，而不需要实现 Paper Search Contract。
12. 新增 Provider 不要求建立新的 Lifecycle Mode 或 Research Action 类型。

## 决策摘要

论文搜索的 V1 架构保持为：

```text
                 Claude
                   │
                   ▼
            search_papers
                   │
                   ▼
          PaperSearchProvider
                   │
             DeepXiv Adapter
                   │
                   ▼
            PaperSearchHit[]
                   │
             Claude selects
                   │
                   ▼
              RetainPapers
                   │
                   ▼
                Papers
```

未来可以变成：

```text
          PaperSearchProvider
             │        │
             ▼        ▼
         DeepXiv   New Provider
         Adapter      Adapter
```

而不改变 Research Loop。

核心原则是：

> **Research Loop 依赖论文搜索能力，不依赖 DeepXiv。**

> **Search Result 是临时 Observation，不是 Persistent Research State。**

> **Claude 决定哪些论文值得进入 Research Run。**

> **Provider 是访问路线，不是 Paper Identity。**

> **Provider failure must never masquerade as an empty result.**

> **V1 的可插拔意味着增加 Adapter，而不是建立 Plugin Framework。**
