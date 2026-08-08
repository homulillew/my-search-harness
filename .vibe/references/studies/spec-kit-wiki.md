# Study Note: formin/spec-kit-wiki

> 本 Note 是第六份 Reference Study，对应我们 **Local LLM Wiki / Knowledge
> Accumulation** 能力，也是 Reference 序列的最后一份。
>
> 它与上一份 Superloopy Study 的边界必须保持清楚：
>
> ```text
> Superloopy     → What evidence is trustworthy enough?   （验证门槛）
> spec-kit-wiki  → What do we do with trustworthy evidence across runs?
>                   （跨 run 长期知识）
> ```
>
> 本轮唯一主问题是：
>
> > **一次 Research Run 中已经被接受的 Evidence，如何转化为可跨 Run 复用、
> > 可更新、可追溯、可重建的本地知识？**
>
> 读完后最重要的发现：**spec-kit-wiki 是 Karpathy "LLM Wiki" 的 Spec Kit 适配，
> 而它走的是「accumulation-with-maintenance」路线——LLM 反复改写页面来积累知识；
> 我们候选方向是「derivation-with-rebuildability」——Wiki 从 Accepted Evidence
> 重投影。这份 Reference 恰恰是我们要验证的反面方案，研究它就是在研究我们
> 选择的对立面。** 它的强项（无 uncited claim、冲突保留、lint 机械/语义分层、
> query 诚实覆盖判定）都能迁移；它的弱项（summary-of-summary 漂移、页面即事实源、
> 不可重建）正是我们 P15-17 要避免的。

---

# 1. Snapshot

```text
Repository:
https://github.com/formin/spec-kit-wiki.git

Studied commit:
e80702b（chore: exclude repository-only files from release archives；
        其下 00231ba 为 Initial release v1.0.0；研究时点 HEAD = e80702b）

Study date:
2026-08-09

License:
MIT

Implementation shape:
Spec Kit extension（github/spec-kit 的社区扩展）
├── commands/*.md     —— 五个 command spec，全部是纯 prompt 文件（无执行代码）
├── docs/concepts.md  —— 设计映射与有意偏离的说明
├── extension.yml     —— 扩展清单（provides/hooks/config defaults）
└── config-template.yml
```

关键形态判断：**这个"实现"不是一个程序，而是一份给 LLM Agent 的协议规范**。
Spec Kit 把每个 command 定义成 prompt 文件，由宿主 Agent（Claude Code / Copilot /
Cursor / Gemini CLI 等）按文件里的步骤执行。README 明说：

> commands are plain prompt files; no external tools, MCP servers, or network
> access required.

因此它没有任何 Python/JS 运行时可以读——**"lint 逻辑"、"update 逻辑"都以
自然语言规则的形式写在 command spec 里**。这对我们有两层意义：
（1）这套机制的全部强度来自"prompt 纪律"，而 prompt 纪律没有机械强制力——这正是
我们引入 Python Harness 做 deterministic enforcement 的理由（见 §Lint / Validation
Boundary）；（2）它证明"用尽可能少的运行时概念表达一个知识积累系统"是可行的，
Spec Kit 本身（宿主）承担了 Agent Runtime 角色——和我们的 `Claude Code = Agent
Runtime` 同构。

---

# 2. Why We Studied It

`REFERENCE_PROJECTS.md` §9 的原始定位：

> 一次 Research Run 的有价值知识不会随 Report 完成而消失。

指南 Q1-Q8（什么知识值得进入 Wiki / Raw Source 与 Wiki Knowledge 如何区分 /
Source Registry 的作用 / 页面如何引用来源 / 已有 Page 如何 update 而非无限 append /
Conflict 如何保留 / Lint 解决什么问题 / Wiki 如何成为 future query 的 prior
knowledge）。

它的来头是 **Andrej Karpathy 的 "LLM Wiki" gist**：retrieval-only 系统没有
accumulation——模型每次都从原始文档重新发现知识；而一个由 LLM 维护的持久 Wiki 是
"compounding artifact"，每次 ingest 都让未来的回答更便宜更好。spec-kit-wiki 把这个
pattern 适配到 spec-driven development：Spec Kit 产生知识（`research.md` 结论、
plan 决策、实现中途发现）然后埋在 per-feature 目录里；feature 007 重新推导
feature 003 已经学过的内容。Wiki 是 **cross-feature memory layer**。

**为什么这份 Reference 对我们关键**：它正是我们候选方向的对立面，且做得很好。
我们假设 Wiki = Derived Projection（从 Accepted Evidence 重建）；它证明
Wiki = Accumulated Artifact（LLM 维护，从 Sources 增量积累）同样可以精致。
只有把它读透，我们才能说"为什么我们选 projection 而不选 accumulation"是
基于证据的判断，而不是偏好。它回答的不是"怎么做 wiki"，而是：
**"一个可持续积累的研究知识库，怎样在不对抗 projection 的前提下，避免成为
第二事实源、避免 summary drift、保持可追溯？"**

---

# 3. Architecture in One Diagram

## Reference 的三层结构 + 五命令

```text
                    人类：curate sources · ask questions · resolve conflicts
                    LLM：bookkeeping（summarize / cross-ref / consistency）
                                        │
        ┌───────────────────────────────┼──────────────────────────────┐
        ▼                               ▼                              ▼
  Raw sources（不可变）           wiki/pages/*.md               wiki/SCHEMA.md
  spec.md/plan.md/research.md    LLM 写的知识页                规则（类型/命名/引用/维护）
  文件/URL                        typed + frontmatter          user-editable，命令服从它
        │                          + INDEX.md
        └────── 被 sources.md registry 指向（S001…，绝不复制） ──┘
                                        │
   ┌────────────────────────────────────┼────────────────────────────┐
   ▼           ▼               ▼                ▼                  ▼
  init       ingest           query            lint              status
  建骨架      知识唯一入口       只读·带引文      6 项检查           只读·一个下一步
  (不覆盖)   register→extract   Covered/       机械自动修          session-resume
            →fold ≤N 页       Partial/        语义只报告          + 一条推荐动作
                             Uncovered
                                        │
                                        ▼
                          Query before specify → prior 流进新 feature
                          after_plan / after_implement hooks → ingest
```

## 我们的适配（hypothesis，非定论）

```text
         Accepted Evidence（Evidence Store = Source of Truth）
                          │
                          ▼
                 Projection Builder（deterministic）
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
   Route views      Topic views         Paper views
   （跨论文结论，     （研究主题景观，      （单篇论文：已接受 Evidence
     引多篇 Evidence）  含矛盾与开放问题）     聚合 + 证据支持的论文角色结论）
                          │
                          ▼
        Future Run：wiki query → prior / lead → paper 回源验证 → 新 accepted evidence
        （Wiki 帮助决定研究什么；论文决定我们被允许声称什么）
```

核心差异一句话：Reference 是 **Sources →（LLM 维护）→ Pages**，页面是积累品；
我们是 **Evidence →（deterministic 投影）→ Pages**，页面是派生态，可重建。

---

# 4. Core Concepts

1. **Three layers（Karpathy）**：raw sources（ground truth，不可变）→ wiki pages
   （LLM 写的知识）→ schema（SCHEMA.md，规则，可编辑，命令服从）。三者严格分层。
2. **Accumulation（compounding artifact）**：核心主张——没有积累的 retrieval 是
   从零重新发现；每次 ingest 都让未来回答更便宜。
3. **Ingest 是知识唯一入口**：init 建骨架、ingest 才写知识；query/status 只读；
   lint 只重写 INDEX/links/lint-report。"Knowledge enters only through ingest."
4. **No uncited claim**：`require_citations: true` 时，任何写入的 claim 必须带
   source ID（S-id）。(S003) 是唯一合法的证据锚点。
5. **Sources 不可变、pointed-to-not-copied**：Wiki 从不复制源内容，只通过 registry
   指向；sources.md 是 append-only 的 S-id 登记表。
6. **Hard caps written down**：`max_pages_per_ingest: 12`、`page_max_words: 600`、
   `pages_slice: 8`、`context_tokens: 4000`——"Prompt-only systems need their limits
   written down."
7. **Conflicts marked, never silently resolved**：`> ⚠ conflict: S002 says X; S007
   says Y`，lint 跟踪直到人类解决；"the wiki quietly changed its mind" 比被标记的
   分歧更糟。
8. **Lint 机械/语义分层**：index-drift/links 是确定性的、可自动修；contradictions/
   stale/citations 是判断，只报告带建议、绝不重写 prose。
9. **Query 诚实**：拒绝回答 pages 支撑不了的内容；coverage verdict
   Covered/Partial/Uncovered，Partial 要给出精确缺口 + 能补上的具体 ingest。
10. **Status 是 session-resume 入口**：只读快照 + 恰好一条推荐动作；"files are the
    memory"。
11. **Derivability boundary（vs OpenWiki）**：能从代码推导的 → regenerate
    （OpenWiki territory）；不能从代码推导的（为什么拒绝替代方案、约束、验证过的
    外部事实）→ accumulate（LLM Wiki territory）。这是本 reference 对我们最有
    用的一个概念，§7 会展开。

---

# 5. Important Files

| 文件 | 角色 | 对本 Study 的意义 |
|---|---|---|
| `docs/concepts.md` | 设计映射 + 与 gist 的有意偏离 + OpenWiki 边界 | **最浓缩的一篇**：三操作、六 invariant、derivability boundary |
| `commands/speckit.wiki.ingest.md` | 知识唯一入口 | **核心**：register→extract→cap-bounded fold→citation→conflict marker |
| `commands/speckit.wiki.query.md` | 只读问答 | 诚实边界：只答 pages、coverage verdict、绝不 improvise |
| `commands/speckit.wiki.lint.md` | 6 项健康检查 | **核心**：机械/语义分层、auto_fix 范围、report-only 语义 |
| `commands/speckit.wiki.status.md` | resume 快照 | 一个推荐动作的优先级、永不读 page body |
| `commands/speckit.wiki.init.md` | 建骨架 | SCHEMA/INDEX/sources 模板、idempotent |
| `config-template.yml` | 配置模板 | 所有 caps 的默认值、page_types 列表 |
| `extension.yml` | Spec Kit 清单 | 提供五命令、after_plan/after_implement hooks、defaults |
| `README.md` | 用法 + 与 gist/memory-md 的区分 | 使用模式（query before specify 等） |

注意：**仓库没有代码文件**。所有"实现"都是上述 prompt spec + 模板。这意味着
lint 的六个 check、ingest 的 merge 语义、query 的覆盖判定，全部是**规则文字**，
实际执行质量取决于宿主 Agent 对规则的信守——没有任何东西在"运行"时机械强制。

---

# 6. Key Data Flow

## Ingest（唯一写路径）

```text
$ARGUMENTS（file/dir/URL，空=当前 feature 的 research.md + plan 决策段）
  → 读 config（file→env→key=value）+ SCHEMA.md（规则优先）
  → sources.md：normalize 去重
       新源 → append 下一 S-id（type + 双日期 + 空 pages）
       旧源 → 只更新 Last ingested（re-ingest 是正常刷新路径）
  → 读源一次，extract 存活项（决策/约束/gotcha/概念/组件实际行为/已验证外部事实；
    跳过 transient、speculation、已存在且未变的）
  → 用 INDEX（不读全库）把每项映射到现有或新建 page
  → 硬 cap：最多触及 max_pages_per_ingest 页；超限 → 最有价值者先入，其余列 defer
  → 更新 page：merge 新项 / 更新被源改写的旧陈述 / 每 claim 带 (S-id) /
     冲突 → 加 > ⚠ conflict 标记（绝不静默覆盖）/ cross-link / 更新 frontmatter /
     超 page_max_words → 拆分并互链
  → 更新 sources.md 的 Pages touched + INDEX.md
  → 报告：S-id、新建/更新页、冲突、defer；下一步建议（有冲突→lint，否则→query）
```

## Query（只读）

```text
$ARGUMENTS（问题）
  → 读 INDEX → 挑 ≤ pages_slice 页（type 匹配问题的形状）
  → 只读选中页 → 每个承重陈述带 page + S-id 引文
  → 冲突内容按冲突呈现（双方 + 各自 source），绝不静默选边
  → 结尾 coverage verdict：Covered / Partial（精确缺口 + 具体 ingest）/ Uncovered
  → Guardrail：只从 pages 答；general knowledge 只用来措辞，不提供 pages 没有的事实
```

## Lint / Status（维护与恢复）

```text
Lint：6 checks（index-drift / links / orphans / contradictions / stale / citations）
  → 机械项（index-and-links）自动修；语义项（冲突/陈旧/无引文）只写 lint-report.md
  → report 每行 = # / check / severity / page / finding / suggested fix
  → 绝不改 prose、claims、conflict markers、sources.md 历史
Status：只读 SCHEMA(scope) + INDEX + sources + lint-report，不读 page body
  → 快照（scope/pages-by-type/freshness/open issues）
  → 恰好一条推荐动作（优先级：unresolved conflict > 从未 lint > 无页 > 有未 ingest
    的 shipped feature > 用最中心开放问题 probe query）
```

---

# 7. Key State Model

```text
wiki/
├── SCHEMA.md        规则契约：scope + page types + 命名/链接/引用/维护 workflow
│                    user-editable；所有命令写前必读；init 只建一次（重跑 append scope）
├── INDEX.md         页面目录（按 type 分组，一行一页）
│                    ingest 维护；lint 可整体重建；手工编辑在页面文件里，不在 INDEX
├── sources.md       来源登记表（append-only S-id）
│                    | ID | Source | Type | First ingested | Last ingested | Pages touched |
│                    dedup key = normalized path/URL；source 永不复制
├── pages/*.md       知识页
│                    frontmatter: title / type / sources[] / updated(ISO date)
│                    body: 每 claim 带 (S-id)；冲突用 > ⚠ conflict: 行；cross-link 相对路径
└── lint-report.md   最近一次健康检查（唯一允许整体覆盖的文件）
```

**重要观察**：这个 state model 有两个"身份"维度，但都隐含在文件名里——
（1）**source identity** = S-id（registry 的 key，dedup by path/URL）；
（2）**page identity** = filename/title（kebab-case）。没有独立 canonical ID，
没有 alias/rename 跟踪，没有 claim-level id。这是它的结构短板（§Q/C）。

frontmatter 的 `sources[]` + 每 claim 的 `(S-id)` 构成从 page → source 的双层
引用：page 级（这页的知识来自哪些源）+ claim 级（这句话出自哪个源）。它分离了
source identity 与 knowledge identity——一个 S-id 可以触达多页，一页聚合多 S-id。
**但没有到达 locator 级**（S-id 指到文档/URL，不指到文档内的段落/行）。

---

# 8. Knowledge Lifecycle

## Reference：Source → ingest → knowledge → page → update → query → future reuse

```text
Source（不可变输入）
  → ingest（register→extract→fold）
  → knowledge（page 上的 cited claims）
  → page（typed + frontmatter + cross-links，被 INDEX 收录）
  → update（下次 ingest 的 merge + stale 改写；re-ingest 是刷新机制）
  → query（slice + cite + coverage verdict）
  → future reuse（query-before-specify：prior 流进新 feature；hooks 在产生知识的
    时刻触发 ingest）
```

**关键**：这个 lifecycle 的"knowledge"形态是**累积的页面**——知识存在页面里，
每次 ingest 是"读旧页 + 读新源 → 写新页"。源只在 ingest 时被读，query 时
不回源。所以**页面是实践中的工作真值**，源是终极兜底。

## 我们的适配：Source → accepted evidence → projection → page → re-project → query → verify → new evidence

```text
Paper（不可变输入，Paper Store 收录，版本可演进）
  → Search/Read/Extract/Interpret → Accepted Evidence（Evidence Store = SoT）
  → Projection Builder（deterministic，从 Evidence 状态生成）
  → page（Route/Topic 知识页 + Paper 视图；每 claim 引 evidence ID）
  → update = re-project（evidence 版本/内容变了 → 重新投影，不是 merge）
  → query（future run 把 wiki 当 prior/lead）
  → 每个 lead 的 claim 回源验证（对 Paper/Evidence）→ 才成为新 accepted evidence
```

**本质差别**：reference 的 update 是"LLM 重写页面"（merge）；我们的 update 是
"从证据重投影"（rebuild）。Reference 的 knowledge 形态是页面；我们的 knowledge
形态是 accepted evidence，页面只是它的视图。这保证了 P15-17（可重建、可丢弃）。

---

# 9. Source of Truth Analysis（Architecture Question A）

## Reference 实际把谁当 authoritative？

**分层，且没有单一的 SoT：**

```text
raw sources        → 终极 ground truth（不可变，永不复制）
wiki pages         → 对 query 而言的 working truth（query 只答 pages，不回源）
SCHEMA.md          → 规则 truth（什么结构、什么允许）
sources.md         → 登记 truth（谁被收录、何时 ingest）
```

对 query 而言，**pages 是事实来源**——query 明确"只从 pages 答"，且拒绝
improvise。源是 pages 的兜底，但 query 时不读源。这意味着**页面在实践中就是
第二事实源**：它被当作用户问题的权威答案层。spec-kit-wiki 用引用纪律、冲突标记、
lint 来限制它，但从未改变"页面即答案"的事实。

## 我们的判断（与 PROJECT_VISION 一致）

```text
Accepted Evidence（Evidence Store） = Source of Truth
Paper Store                          = 终极 ground truth（evidence 引用它）
Wiki                                 = Derived State（投影，可丢弃、可重建）
Report                               = Derived State（本 run 交付）
```

**核心差异**：reference 的 query 把 pages 当答案；我们的未来 run 必须把
evidence 当答案、把 wiki 当 prior。这不是措辞差异——它决定了 wiki 是"第二事实源"
还是"可重建的视图"。这也是 §12 与 §Future-Run Reuse Model 的分界线。

---

# 10. Page Identity and Update Semantics（Q3/Q4/C）

## Page 是 knowledge object 还是 Markdown view？

**是 Markdown view + 一个很轻的 frontmatter 契约**（title/type/sources/updated）。
它不是一个类型化系统里的 knowledge object——没有 per-claim id、没有 schema 校验、
没有页面间的关系对象，只有相对链接 + 约定。type 由 SCHEMA.md 定义且 user-editable
（"edit freely; commands obey it"）。

聚合：一页把多个源的知识折叠在一起（frontmatter `sources[]` 列 S-ids），claim 级
`(S-id)` 指定每句出自哪个源。

稳定 identity：**filename（kebab-case）+ title**。没有 canonical ID。rename 的修复
靠 lint 的 links check"当目标无歧义时"修相对链接——**歧义时链接静默丢失**。
没有 alias/duplicate detection。

## Update 语义：merge-with-stale-update，由 LLM 执行

ingest step 5 的原话：

> Merge the new items where they belong; update statements the source has made stale.

所以参考模型的更新是：**LLM 读旧页 + 读新源 → 在页面上 merge 新项、改写被源
过时的陈述**。这是"读旧页 + 写新页"的 LLM 循环，**不是从源重建**。

它的防漂移机制：
- **旧引文保留**：每 claim 带 (S-id)，merge 不改旧 claim 的引文（冲突时是加 marker
  而不是删旧 claim）；
- **`stale` lint check 的 provenance 驱动项**：`pages whose source was re-ingested
  after the page was last updated` —— 源比页面新 → 标 stale。这是一个
  **provenance-driven 的陈旧信号**（派生物落后于其源），比 `stale_after_days`
  的纯天数启发式有信息量得多；
- **冲突显式化**：被新源反驳的旧 claim 以 marker 保留。

但它**无法**防止 summary-of-summary 失真：每次 merge 都是一次 re-summarize，
反复 re-summarize 会累积失真，而引文只锚到源文档（S-id），merge 时不会机械
核对旧 claim 是否仍忠实于源。lint 的 contradiction check 也只比较共享 source
或 link 的页对——跨不相关页的矛盾看不见。

## 对我们的判断

**我们必须选 re-projection，不是 merge。** 理由：
1. **漂移是渐进的**：LLM merge 模型下，每次 ingest 都可能微调措辞、悄悄改意思；
   "old page + new source → slightly newer page forever" 正是误区 3 描述的形状。
   Re-projection 下，页面内容 = 证据状态的函数，改证据才改页面，无中间态。
2. **身份短板要补**：filename-as-id + 启发式 link 修复对我们不够——跨 run merge
   需要 stable identity（canonical slug + aliases）。这是 C 的结论。
3. **derivability 决定取舍**：见 §11。凡能从 accepted evidence 推导的 → 投影。
   **关键是：绝大多数我们想长期保留的知识都是 evidence-backed conclusions**
   ——包括论文事实、route 结论、**失败模式 / 为什么拒绝某 route**（它们是对已接受
   evidence 的结论："route X 被拒，因为 A 显示该方法在此域失效、B 的评价域更窄"），
   因此都属于投影内容（PROJECT_VISION §3.4 把"失败模式"列为长期知识，P15 把
   "Paper"列为长期知识，都可被证据支持）。只有**过程级 deliberation**（头脑风暴过
   的替代方案轨迹、评审会话细节）不可推导，留在 Report/run state。
4. **但保留它的两个好机制**：`sources[]` page 级聚合 + `(S-id)` claim 级引用的
   双层引用结构（我们的等价物：page 级 evidence_ids[] + 每 claim 的 evidence id）；
   provenance-driven 陈旧信号（evidence 版本变了 → 标待重投影）。

---

# 11. Citation Model（Q6）

## Reference 的引文到哪一层？

```text
Wiki claim → (S-id) → sources.md 行 → source document（file/URL/artifact）
```

- **machine-readable？** 部分是：`(S003)` 是约定语法，lint 的 `links` check 会
  **机械检出 naming unknown S-ids 的引文**（悬空引文 → 报错）。但没有类型化
  schema、没有解析器——它是"可 grep 的约定"。
- **到 locator 级吗？** **不**。S-id 指到源文档整体（URL/文件），不指到文档内的
  段落/行/证据。一个 claim 引 S003 = "这句话出自那个文档"，无法机械核对"这句话
  真的在文档里、在原上下文里支持这个意思"。
- **claim-level vs page-level？** **claim-level**（每 claim 带 S-id）——这是它比
  page-level sources 强的地方。但 claim→S-id 仍是 doc-level 锚。

## Trade-off：Wiki Claim → Paper vs Wiki Claim → Evidence → Paper + Locator

```text
方案 A：Wiki Claim → Paper
  优点：简单；页面薄；阅读者一眼知道"这句话基于论文 X"。
  缺点：没有锚点。claim 与论文的哪个 section/段落对应不明；回源验证要重新找；
        claim 会从"某个具体段落支持的论断"漂移到"论文大致说了什么"。这正是
        reference 的 doc-level 引文的失真的根源。

方案 B：Wiki Claim → Evidence ID → Paper + Locator（我们的候选）
  优点：每个 wiki claim 精确锚到已接受的 evidence（excerpt + locator + stance）。
        "Every wiki statement remains traceable" 是构造性的（claim 生成时就绑定
        evidence id），不是靠 lint 事后找。回源验证 = 读 evidence，不重找。
        引文命名空间 = Evidence Store（已存在），wiki 不需要自己的 registry。
  缺点：wiki 变密（每 claim 都带 evidence id）；要求 evidence 持久（我们的
        Evidence Store 本来就是 SoT，持久是设计前提）；渲染时可能显得"引用噪音"。
```

**判断**：选 B。这不仅符合 P10（Claim→Evidence→Paper→Section/Locator→Stance）
和 P8（Paper ≠ Evidence），而且**消除了 reference 那种独立的 S-id 注册表**：我们锚
到 evidence id，而 evidence id 已经解析到 paper + locator。但要小心——§15 Decision 2
会说明，注册表的两个残余职能（外部新鲜度触发、evidence→依赖视图的逆映射）仍需在
Paper Store 与投影层各自安放，不能简单说"完全吸收"。

**Source 删除 / 变化后怎么办**（Q6 子问题，也是 failure mode E）：reference 只处理
"re-ingest 刷新"，不处理"源消失"。我们的语义必须明确：
- 论文从 Paper Store 移除 / 被 retract / 版本作废 → **re-projection 把该 paper 的
  evidence 与其依赖的 wiki claim 一并移除**（投影是 evidence 状态的函数：删除
  evidence = 删除视图上对应 claim）；
- 悬空引文检测必须是 **source-level**（一个已注册 paper 被移除 → 依赖它的视图被
  机械标记），而不是只查"未知 S-id"——那只能抓从未注册的 id，抓不到已注册后被
  移除的源；
- **retraction 必须触发 re-verification pass**：被撤销的论文不能静默消失，要在
  analysis 留痕（为什么移除），相关 route/topic 结论降级或标注待核验。

---

# 12. Conflict Model（Q5）

## Reference 怎么做？

- **不强迫二选一**：新源与旧 claim 矛盾时，保留双方 + `> ⚠ conflict: S002 says X;
  S007 says Y` 标记，**绝不静默覆盖**。
- **conflict 是 prose 里的内联 marker**，不是 page metadata、不是独立对象。
- **可以长期 unresolved**：lint 的 contradiction check 跟踪 marker 是否仍 unresolved；
  status 把 unresolved conflict 列为最高优先推荐动作；人类通过 re-ingest 或编辑
  页面解决。冲突被 lint 报告为"keep the newer claim, drop the marker"的建议。
- **lint 额外查"共享 source 或 link 的页对断言互斥"**——但 bound 到共享源的页对，
  跨无关页的矛盾看不见。

## 我们的判断：只需投影，不需子系统

我们有更规整的原料：`Evidence.stance ∈ {supporting, contradicting, qualifying}`
+ `analysis.contradictions[]` + non-consensus 记录（old-search-harness 的一等
产物）。因此 **Wiki 不需要复制 contradiction subsystem，只需把 contradiction
state 投影出来**：Route/Topic 页把矛盾双方 + 各自 evidence ids + stance 渲染成
可见小节（contradicting 组独立保留），标注 unresolved——和 reference 的 marker
同一目的（可见、不静默选边），但源是结构化 state 而非 prose 约定。

这带来一个 reference 没有的好处：**矛盾是数据，可被机械枚举**（新证据接受后
重投影），不需要人类逐个 marker 手工解决。但必须钉死一条规则（与 §19.3 的
determinism 边界一致）：**投影只能"保留"矛盾（渲染双方 + 各自 evidence），
永远不能在投影里"解析"矛盾**——解析（判定哪方胜出）是语义判断，只发生在
fresh-review 边界，作为分析层结论写入 state 后，再由下一次重投影呈现。

---

# 13. Lint / Validation Boundary（Q7）

## Reference 的六项检查与分层

| Check | 找什么 | severity | 处理 |
|---|---|---|---|
| `index-drift` | 页不在 INDEX；INDEX 行指向不存在文件 | mechanical | auto-fix |
| `links` | 相对链接指向缺失页；引文命名未知 S-id | mechanical | auto-fix |
| `orphans` | 无页链接到的页 | structural | report |
| `contradictions` | 未解决 marker；共享源/链的页对断言互斥 | semantic | report |
| `stale` | 页比 stale_after_days 旧；源被 re-ingest 而页未更新 | semantic | report |
| `citations` | require_citations 时无 S-id 的 claim | semantic | report |

**原则**：机械项（index/link）自动修；语义项（矛盾/陈旧/无引文）只报告 + 建议，
**绝不重写 prose**。`lint-report.md` 是唯一可整体覆盖的文件。"Findings must be
verifiable: every row names the page and the exact claim or link."

它解决的是：**记录与声称之间的漂移**——页面被维护者反复改写后，INDEX 是否还准、
链接是否还活、每句是否还有源、是否出现了未解决的矛盾、是否已陈旧。但它**不验证
语义**：不判断"这句是否真的支持 claim"、"summary 是否忠实"、"矛盾是否真构成矛盾"。
lint 明确地把这些排除在 auto-fix 之外（semantic → report）。

## 我们的判断：延续 Superloopy 的边界，并下放到 wiki 层

```text
Python（integrity，fail-closed）
  ├─ 每个 wiki claim 的 evidence id 存在且解析到 paper+locator
  ├─ page 引用（evidence_ids[]）有效、无重复
  ├─ 投影与 accepted evidence 一致（重投影校验 = 重建性保证）
  ├─ required metadata 齐全；链接有效；schema 合法
  ├─ 陈旧信号：evidence 版本/as-of 变了 → 待重投影标记
  └─ source-level 悬空检测：已注册 paper 被移除/retract → 依赖视图被标记
     （比 reference 的"未知 S-id"更强，能抓已注册后被移除的源）

Claude（meaning，semantic review）
  ├─ 页面陈述是否真的由所引 evidence 支持
  ├─ summary/interpretation 是否忠实于原文
  ├─ 标注的 contradiction 是否真构成矛盾
  └─ 覆盖面是否足够 / critical gap 是否仍存在
```

Reference 的 `stale` 用天数启发式 + provenance 信号；我们只保留 **provenance
驱动**的部分（evidence 变了 → 待重投影），天数启发式不要——因为我们的页面是
重投影生成的，陈旧 = evidence 状态变化，天然由重建触发，不需要猜 90 天。
Reference 的 `citations`（无引文 claim）在我们的投影里是**构造性满足**的
（投影生成的每个 claim 必带 evidence id），无需 lint 兜底——这正是
"integrity by construction"优于"integrity by lint"的例子。

---

# 14. Future-Run Reuse Model（Q8）

## Reference 的 reuse 模型

```text
future feature 开始 → /speckit.wiki.query "<该 feature 的 domain>"
  → 读 INDEX + slice 页 → 带引文回答 + coverage verdict
  → prior decisions/constraints 流进新 spec（而不是重新推导或被反驳）
```

关键机制：
- **query-before-specify 模式**：开始新工作前先问 wiki，prior 流进新 spec。
- **诚实边界**：query 拒绝回答 pages 支撑不了的内容（"the wiki's value is that its
  answers are backed"）；general knowledge 只措辞、不供料；coverage verdict 把
  Uncovered 变成具体的 ingest 建议——缺口是动作，不是失败。
- **hooks**：after_plan / after_implement → ingest，在知识产生的时刻抓取。

**但它把 wiki 当 truth**：query 从 pages 答，不回源。对 reference 这是特性
（backed answers）；对我们这是必须避免的——它会让已有 wiki 成为新研究的
confirmation bias 源（新 run 引用旧结论而不回源核验，错会延续）。

## 我们的判断：Wiki → search lead / prior，不是 Wiki → evidence

```text
future run 开始
  → wiki query → prior / lead / 待验证假设（含 contradiction 警示）
  → 每个 lead 的 claim 必须回源验证（读 Paper/Evidence，判定支持/反对）
  → 验证通过 → 新 accepted evidence → （本轮结束时）→ 重投影回 wiki
```

**Wiki 是"研究什么"的线索来源，不是"允许声称什么"的证据来源。** 论文决定我们
被允许声称什么。Reference 的部分机制支持这个方向（coverage verdict、refuse
beyond pages、conflict surfaced）——它挑战我们的地方是"query 从 pages 答"；我们
严格化它：**future run 的答案必须从 evidence 出，wiki 只提供 leads 和 prior
context**。这正是 PROJECT_VISION 的最终原则。

**"那为什么还要 wiki，直接查 Evidence Store 不就行？"（decorative-layer 挑战）**：
因为 wiki 是**预算便宜的预计算组织层**（P13）——它把 Evidence Store 的
route/topic 景观、覆盖判定、claim→evidence-id 映射预先排好，让未来 run 的
"现在该查什么、每句声称锚在哪条 evidence"从全库重扫变成 O(1) 的索引读取 + 对
locator 的一次回源。它可以被（昂贵的）全库扫描替代，但它存在的理由是让 reuse
变便宜、让 gap 可见。**可推导 ≠ 可免费得到**——这正是"derived but not
redundant"的辩护。

---

# 15. Design Decisions Worth Learning

### Decision 1 — Knowledge enters only through ingest, with a mandatory claim-level citation

**Problem**：知识的"唯一入口"如果没有纪律，页面会被随意写入（LLM 顺手把
memory 写进页面），引文纪律崩坏，无法追踪。

**Design**：只有 `ingest` 命令写知识；init 只建骨架，query/status 只读，lint 只
重写 INDEX/links/lint-report。`require_citations: true` 时**任何写入的 claim 必须带
S-id**；lint 有 `citations` check 兜底。Sources immutable——ingest 永不改源文件。

**Why**：把"什么进、怎么进"收窄到一条路径，让知识库的写模式可预期、可检查。
No-uncited-claim 把"可追溯"从愿望变成写入时的前置条件。

**Trade-off**：门槛带来摩擦（每句都要引文）；但也让知识库保持 honest。对 prompt
系统，这条规则的执行依赖 Agent 信守（没有机械强制）。

**我们是否有同样的问题**：是——wiki 必须有唯一写路径（我们的 projection
builder），且无引文 claim 必须是构造性不可能（不是靠 lint 兜底）。

**是否有更简单的实现**：我们的投影由 deterministic builder 生成——每个 claim
从某条 accepted evidence 生成，引文是构造的一部分。这比"事后 lint 检查无引文"
更强且更简单：**integrity by construction**。

**Transferability**：强。Wiki 写路径唯一化 + 构造性引文，直接进我们的
Projection Builder 设计。

---

### Decision 2 — Sources pointed-to, never copied; append-only registry; source identity ≠ knowledge identity

**Problem**：如果页面复制源内容，知识库膨胀、源更新时页面变 stale、且无法区分
"这是源里的事实"还是"这是我们的总结"。

**Design**：`sources.md` append-only S-id 登记表；dedup by normalized path/URL；
source 永不复制，只被指向。页面 frontmatter `sources[]` 列依赖的 S-ids；每 claim
`(S-id)`。registry 是 source identity 与 knowledge identity 的连接表——一个 S-id
触达多页，一页聚合多 S-id。

**Why**：把"源是什么"与"我们知道什么"解耦。源是稳定的（identity 稳定），知识是
派生的（可更新）。Re-ingest 同一 S-id = 刷新，不会产生重复源。

**Trade-off**：registry 是额外簿记；但对不可变源 + 引用纪律是必要的。它的
provenance 驱动 stale 信号（源被 re-ingest 而页未更新 → stale）是 registry 的
真实回报。

**我们是否有同样的问题**：是——但我们已有 Paper Store（source identity：
arXiv id/DOI）+ Evidence Store（knowledge identity：evidence id），身份与 dedup
两维度已覆盖，**不需要独立的 S-id 注册表**。

**是否有更简单的实现**：wiki claim 直接锚 evidence id（→ paper + locator）。
但要承认注册表的两个残余职能不能假装被吸收：
1. **外部新鲜度触发**：reference 的 `Last ingested` 时间戳（每次 re-ingest 更新）
   是"源变了"的**触发器**，lint 的 provenance stale check 依赖它。我们的
   Paper Store 需要一个薄的 `current version / last verified` 字段 + 一个显式的
   re-check 动作（arXiv v1→v2、preprint→published、retraction 的核对），否则
   "版本漂移"只能靠未来 run 恰好重访该论文才发现（§19.6 是反应机制，不是触发
   机制）。
2. **evidence → 依赖视图的逆映射**：局部重投影（§19.8）需要知道"一条 evidence
   变了要重建哪些 route/topic 视图"——这正等价于 reference 的 `Pages touched`
   可追溯性，是**投影层的索引**，不是 Evidence Store 自然持有的。必须作为投影
   层的一等结构（换个名字的 registry），不能假装不存在。
另外：reference 还登记 URL/file/已验证外部事实等非论文源；若我们未来要收录
非论文来源，需要给它们一个身份方案（arXiv/DOI 只覆盖论文）。

**Transferability**：强。借"双层引用 + 身份分离"，不借"独立 registry 文件"。

---

### Decision 3 — Hard caps written down（"prompt-only systems need their limits written down"）

**Problem**：没有运行时强制时，LLM 会把"更新 10-15 个相关页"理解成无限蔓延；
一次 ingest 碰 50 页、一页写 3000 词、query 加载全库。

**Design**：所有极限显式配置：`max_pages_per_ingest: 12`、`page_max_words: 600`、
`pages_slice: 8`、`context_tokens: 4000`、`stale_after_days: 90`。超限时**延迟可见**
（defer 项列在报告里作为 follow-up），而不是蔓延。

**Why**：prompt 系统的约束必须写下来——Agent 不知道你的隐性极限。cap 是
"复杂度必须挣得位置"（P13）的具体化：每次写都被资源边界约束。

**Trade-off**：cap 太紧会分片（知识被切成 follow-up）；cap 太松会蔓延。但对
bounded loop 而言，显式 cap + 可见 defer 远好于隐性蔓延。

**我们是否有同样的问题**：是——P13 明确"Numbers Bound Resources"。我们的
projection 同样需要 cap（每批投影页数、页大小、query slice）。

**是否有更简单的实现**：cap 直接进配置（我们的 Python harness 本来就持有
config），比写在 prompt 里更可靠——我们可以机械强制，不需要靠 Agent 自觉。

**Transferability**：强。cap 作为配置 + 可见 defer，直接迁移；且我们能比
reference 更硬（Python 强制而非 prompt 约定）。

---

### Decision 4 — Lint splits mechanical from semantic; prose is never auto-rewritten

**Problem**：健康检查若既改机械问题又改语义问题，等于让维护器拥有改写知识的
权力——漂移会从"lint 之后"开始。

**Design**：机械项（index-drift、links）确定性、可自动修（`auto_fix: index-and-links`）；
语义项（contradictions、stale、citations）只写 `lint-report.md` + 建议，绝不
auto-fix。lint 只重写 INDEX/links/lint-report，不动 prose、claims、conflict
markers、sources.md 历史。

**Why**：这是 reference 的安全边界——"一个只修目录和链接的 lint，比一个会
"帮你想清楚"的 lint 安全得多"。语义判断留给 human/next pass。

**我们是否有同样的问题**：是——这直接延续 Superloopy Study 的
`Python = integrity / Claude = meaning` 边界，并下放到 wiki 维护层。

**是否有更简单的实现**：我们的 lint 即"投影一致性校验"（Python 检查投影与
accepted evidence 一致）+ 语义 fidelity 交给 fresh review。比 reference 的六项
启发式更简单——因为我们的页面是构造出来的，漂移只有一种来源（evidence 变了），
校验也只有一种（重投影对比）。

**Transferability**：强。机械/语义分层是已确立边界（superloopy 后），此处获得
第二个独立佐证。

---

### Decision 5 — Conflicts are marked, never silently resolved; conflict is tracked until a human resolves it

**Problem**：共享 repo 里"wiki 悄悄改变了主意"比被标记的分歧更糟——静默覆盖
销毁信息且无人察觉。

**Design**：新源与旧 claim 矛盾 → 双方 + `> ⚠ conflict:` marker；ingest 报告里
显式 flag；lint 跟踪 marker 是否 unresolved；status 把 unresolved conflict 列为
最高优先的推荐动作；人类通过 re-ingest 或编辑解决。绝不静默选边，query 也按
冲突呈现双方。

**Why**：矛盾是知识库里最有价值的信息之一；平掉它等于销毁可审计性。让矛盾
"活着"直到人类裁决，是共享知识库的最低诚信。

**我们是否有同样的问题**：是——但我们的矛盾是结构化 state（Evidence.stance +
analysis.contradictions），不是 prose marker。

**是否有更简单的实现**：投影直接渲染 contradiction state（双方 + evidence +
unresolved 标注），不需要 marker 语法、不需要 lint 专门跟踪 marker。新 evidence
接受后重投影，矛盾自动被重新解释。

**Transferability**：强。借"不静默解决"的原则；不借 inline marker 语法（我们渲染
state 而非约定 prose）。

---

### Decision 6 — Query honesty: refuse beyond pages; report a coverage verdict

**Problem**：知识库问答最大的诱惑是"用模型知道的东西补全"，那会让答案失去
backing，缺口被静默填上。

**Design**：query 只从 pages 答；答不了的明确说 Uncovered 并指出可能在哪找；
Partial 要给出**精确缺口 + 能补上的具体 ingest**。coverage verdict 是回答的
标准收尾。README FAQ 直言：query refuses to answer something the model obviously
knows——**这是特性**：wiki 的价值是答案有 back，不是答案全。

**Why**：把"缺口"从失败变成动作（P7 gap-driven）。诚实覆盖判定让知识库的盲区
可管理，而不是被假装不存在。

**我们是否有同样的问题**：是——P7 的 gap-driven 要求未来 run 把 wiki 的盲区
转成 leads（哪些 topic 缺乏证据）。

**是否有更简单的实现**：我们的"coverage verdict"就是"该 route/topic 已接受的
evidence 是否支撑结论"——由投影 + 后续语义 review 决定，covered/partial/uncovered
可机械判定（有证据=covered；证据不足但非空=partial；空=uncovered）。

**Transferability**：强。诚实覆盖判定直接迁移，且与我们 P7/P11 一致。

---

### Decision 7 — Status is a first-class session-resume entry point with exactly one next action

**Problem**：Agent session 会死（重启、压缩、上下文溢出）；连续 operator 的假设
不成立。恢复需要"从文件重建工作画面"，而不是从旧对话。

**Design**：`status` 只读（SCHEMA scope + INDEX + sources + lint-report，不读 page
body），一屏快照 + **恰好一条**推荐动作（优先级：unresolved conflict > 从未 lint >
无页 > 有未 ingest 的 shipped feature > probe query）。"files are the memory,
context is rebuilt on demand." 新 session 从 status 恢复，不依赖任何先前对话。

**Why**：恢复成本 = 一条命令；推荐动作把"接下来干什么"变成确定性的，而不是让
Agent 猜。这是 P3（resume restores research process）的知识层版本。

**我们是否有同样的问题**：是——P3 已经确立；spec-kit-harness 已给 run 级
resume；这里是知识层的 resume（恢复时先看 wiki 状态）。

**是否有更简单的实现**：我们的 harness 已有 status/下一步逻辑（来自 harness
研究）；wiki 层的"一个推荐动作"直接复用同一模式，不新增机制。

**Transferability**：强（但主要是 corroborate，不是新增）。

---

### Decision 8 — SCHEMA.md: taxonomy and maintenance rules are an editable contract, not code

**Problem**：如果页面类型、命名、链接、引用规则硬编码在系统里，改结构要改代码，
且每种 repo 被迫接受同一套 taxonomy。

**Design**：`SCHEMA.md` 是规则契约——page types（concept/decision/component/
reference/howto）、命名/链接/引用规则、维护 workflow。**user-editable；所有命令
写前必读；SCHEMA 与 prompt 冲突时 SCHEMA 优先**。init 只建一次，重跑 append scope
行。config 里另有 `page_types` 列表与 SCHEMA 保持一致。

**Why**：让结构适配项目而不是项目适配结构。Taxonomy 是配置，不是架构。

**我们是否有同样的问题**：是——我们候选 Paper/Route/Topic 三种页面，不应在代码
里冻结；应作为可编辑的 schema 契约（页面类型、引用规则、维护规则），V1 可以
从最小集合开始。

**是否有更简单的实现**：直接照搬这个模式——一个 SCHEMA-style 契约文件 + 投影
builder 读它。不把 taxonomy 写死在 builder 代码里。

**Transferability**：强。Taxonomy-as-config 是我们"Paper/Route/Topic 是假设而非
定论"的落地机制。

---

# 16. What We Should Borrow

1. **No uncited claim（写入前置的引文纪律）**——但升级为构造性：投影生成的每个
   claim 必带 evidence id（→ paper + locator），而不是靠 lint 兜底。P8/P10。
2. **Sources immutable + pointed-to-not-copied + append-only 身份登记**——我们的
   paper 身份稳定（arXiv/DOI + 版本演进）、evidence 不可变；wiki 只锚 ID 不复制
   excerpt。P8。
3. **双层引用结构**（page 级 `sources[]` + claim 级 `(S-id)`）——我们的等价物：
   page 级 `evidence_ids[]` + 每 claim 一个 evidence id。P10。
4. **provenance-driven 陈旧信号**（源被 re-ingest 而页未更新 → stale）——我们的
   触发：evidence 版本/as-of 变了 → 标待重投影。比天数启发式诚实。P15-17。
5. **lint 机械/语义分层 + prose 绝不 auto-rewrite**——延续 superloopy 的
   Python=integrity / Claude=meaning，下放到 wiki 维护层。P13/P22。
6. **Query 诚实：refuse beyond pages + coverage verdict（Covered/Partial/Uncovered
   → 具体补缺口动作）**——P7 gap-driven 的问答形态。
7. **Conflicts never silently resolved**——投影渲染 contradiction state 而不是
   prose marker；矛盾是一等内容。P10。
8. **Status = 恰好一条推荐动作的 resume 入口**——知识层 resume（corroborate P3）。
9. **SCHEMA.md = 可编辑规则契约，taxonomy 是配置**——Paper/Route/Topic 不冻结，
   放 schema 契约里，V1 最小集合起步。
10. **Hard caps written down + defer overflow visibly**——cap 进配置（P13），我们
    能比 prompt 约定更硬（Python 强制）。

# 17. What We Should Not Borrow

1. **accumulate-maintain 页面模型（LLM 反复 merge/rewrite 页面）**——summary-of-
   summary 漂移的根本来源；我们用 re-projection from evidence。误区 3 的答案。
2. **S-id Source Registry 作为独立系统**——我们的引文命名空间 = evidence id，
   无需独立的注册表文件；但注册表的两个残余职能（外部新鲜度触发、evidence→依赖
   视图逆映射）要分别安放在 Paper Store 与投影层（见 §15 Decision 2）。借
   discipline，不借文件。
3. **精确 page taxonomy（concept/decision/component/reference/howto）**——是
   代码项目类型；我们的领域是论文。误区 1 的答案：不照抄，taxonomy 放 schema
   契约且从 Route/Topic 最小集合起步。
4. **inline `> ⚠ conflict:` prose marker**——我们渲染结构化 contradiction state。
5. **query 把 pages 当 working truth（不回源）**——我们 future run 必须回源验证；
   wiki 只当 prior/leads。误区 2 的答案。
6. **Spec Kit 集成 + after_plan/after_implement hooks**——我们不建 Spec Kit
   extension；知识抓取时机由我们的 loop 决定。
7. **`stale_after_days` 天数启发式**——我们只用 provenance 驱动的陈旧信号
   （evidence 版本变化触发重投影）。
8. **filename-as-identity + 启发式 link 修复**——跨 run 需要 stable identity
   （canonical slug + aliases）；歧义时静默丢链是不能接受的。C 的结论。
9. **"Human curates sources, LLM bookkeeps" 的劳动分工**——我们的 researcher 通过
   loop 策展，projection 是 deterministic 的；不把 bookkeeping 的忠实度押在
   Agent 自觉上。
10. **"Do not load every page 'for context'" 作为唯一上下文策略**——我们已有
    P21（context is a view of state）+ INDEX/细节分层（superloopy study）；这个
    reference 只是 corroborate。

# 18. Conflicts with PROJECT_VISION

1. **Wiki = Derived/Projection vs reference 的 accumulate-maintained pages（最核心）**：
   reference 把页面当作积累品，LLM 反复改写；PROJECT_VISION P15-17 要求 wiki 是
   投影、可重建。我们明确选 projection——并因此**放弃**它积累"无法从源推导"的
   决策/为什么层的能力（§11 derivability）。
2. **Evidence Store = SoT vs reference 的 pages-as-working-truth**：reference 的
   query 从 pages 答、不回源；我们未来 run 从 evidence 答、wiki 只给 leads。
   P8/P10 决定。
3. **P15-17（Wiki rebuildable / disposable）vs reference 的不可重建**：reference
   `rm -rf wiki/` 后靠 re-ingest 无法恢复页面的综合与决策层（那些只在页面里）；
   我们靠"纯 evidence 可推导 + deterministic 投影"让 wiki 可重建。B 的答案。
4. **对齐项**：P3 resume（status corroborate）、P7 gap-driven（coverage verdict）、
   P13 资源边界（hard caps）、P21 上下文是 state 的 view（slices、INDEX）、
   P22 harness 暴露 state（status/单条推荐动作）、"criteria over magic scores"
   （Covered/Partial/Uncovered 是明确分类不是分数）。这些都与 PROJECT_VISION 一致，
   是证据。
5. **derivability 取舍导致的张力（已收窄）**：reference 强调"决策为什么/拒绝的
   替代方案"不可从源推导、必须积累。我们澄清后**发现大部分想要的知识其实是
   evidence-backed 结论**——route 失败模式、为什么拒绝某 route，都是"对已接受
   evidence 的结论"，可投影（见 §10.3，与 PROJECT_VISION §3.4 一致）。真正的张力
   只剩**过程级 deliberation**（头脑风暴轨迹、评审会话细节），它们留在 Report/run
   state。若未来 run 需要跨 run 复用这种过程痕迹，再考虑显式决策日志（Questions
   Open Q4）。

# 19. Failure Modes / Architecture Risks（E + 六误区）

如果照搬 reference（或我们的投影做歪了），最可能在这些地方出问题：

1. **summary-of-summary 失真（误区 3）**：merge 模型下每 ingest 一次 re-summarize，
   反复 re-summarize 累积失真；引文只锚 doc 级，无法机械核对。**我们的防御**：
   页面 = 证据状态的函数，无中间态；evidence 不变则页面不变。
2. **wiki 变成第二事实源（误区 2）**：query 从 pages 答 + 不回源，页面成了实践
   中的真相；页面漂移 = 答案静默漂移。**我们的防御**：future run 回源验证；
   wiki 只当 leads。
3. **determinism 失效 + 可读性权衡**：若投影里混入逐次 LLM 判断（"重投影时重新
   解释"），同一证据状态会生成不同页面，重建性崩坏。**防御**：V1 投影页面是
   **结构化 claim-view**（每条 = claim + evidence-id + stance + 限定词，渲染为
   结构化 markdown 列表），语句级生成是确定性函数；**narrative / 解释性 prose
   只存在于 fresh-review 边界的 Report 里，不进 wiki**。必须接受这个显式
   trade-off：wiki 读起来像"证据景观索引"而不是散文——它的职责是组织 leads、
   让未来 run 的回源验证变成对 locator 的一次 O(1) 重读（P13 预算友好），不是
   提供阅读体验。这是本项目必须写进投影 builder 契约的硬约束。
4. **identity 漂移**：filename-as-id + 歧义时静默丢链（reference 已知弱点）；跨 run
   rename 会让 topic 分裂成两个页面、历史引用悬空。**防御**：canonical slug + alias
   表 + 重复页检测；paper 页用 arXiv/DOI。
5. **无界页面增长 / orphan 堆积**：cap 只限每次 ingest 触页数，不限总页数；orphans
   被 lint 报告但不解决。**防御**：投影按 evidence 驱动建页（无 evidence 即无页），
   页面数由证据量自然约束；orphan 校验机械化。
6. **陈旧静默（版本变化）**：evidence 版本变了（arXiv v1→v2、preprint→published），
   页面仍显示旧结论。**防御**：Paper Store 的 `current version / last verified`
   触发字段 + 显式 re-check 动作（§15 Decision 2）+ 重投影（evidence 版本/as-of
   是投影输入）。
7. **lint 不等于语义验证（误区 4）**：六项检查通过 ≠ 语义正确。reference 自己
   把语义排除在 auto-fix 外；我们更进一步——结构 lint 是投影一致性的副产品，
   语义 fidelity 只在 fresh review 边界判断。
8. **投影成本失控**：每次 evidence 变化就重建整库会贵。**防御**：投影是局部的
   （只重建受影响的 route/topic 视图）+ 触发在 review/synthesis 边界批量做
   （参考 spec-kit-loop 的 budget 门）。
9. **taxonomy 冻结**（误区 1）：若把 Paper/Route/Topic 硬编码，后期发现需要新页面
   类型要改代码。**防御**：SCHEMA 契约，taxonomy 是配置。
10. **vintage 盲区**：页面 `updated` 是单日期，但页面含不同 source 不同时间 ingestion
    的 claim——页面日期无法区分 claim 时效。**防御**：claim 级 vintage（as-of paper
    版本）——对时效敏感的 route/topic 结论必带，paper 事实用 paper version。
11. **把 wiki 更新设计成 Research Lifecycle Phase（误区 5）**：若"更新 wiki"变成
    loop 的一个新 phase，会污染研究生命周期。**防御**：投影是 delivery-side 的
    derived state 操作，挂在 review/synthesis 边界，不是 loop phase。
12. **V1 引入检索基建（误区 6）**：embedding/vector/graph 检索。**防御**：V1 纯
    markdown + 结构化 metadata + filesystem + deterministic 索引（INDEX 一行一页）；
   只有真实查询问题证明需要时才升级。
13. **源消失 / retraction**：论文从 Paper Store 移除、被 retract、URL 失效。
   Reference 完全没处理（它只处理 re-ingest 刷新，不处理源消失）。**防御**：
   re-projection 移除该 paper 的 evidence 与依赖的 wiki claim；source-level 悬空
   检测机械标记依赖视图；retraction 在 analysis 留痕并触发相关 route/topic 结论
   的 re-verification（见 §11）。

**最核心的风险陈述**：参考模型的漂移根因是"维护者是 LLM、真值是积累的页面"；
我们的风险则全部集中在"投影必须保持 deterministic、wiki 永不获得事实源地位、
且证据删除（源消失）时投影必须正确移除"这三条纪律上。守住这三条，其余风险
都是工程参数。

# 20. Questions Still Open

1. **跨 run stable identity 怎么做（C）**：route/topic 的 canonical slug + alias /
   rename 跟踪 / 重复页检测如何设计？paper 页用 arXiv/DOI 是稳的；topic 页的
   identity 是难点（同一主题在不同 run 的措辞不同）。这是 Domain Model 阶段最
   难的问题之一。
2. **页面 taxonomy 最终集合**：PROJECT_VISION P15 明确把 Paper 列为长期知识，因此
   **Paper 是知识页而不是"生成视图"**（§3 已修正）——它投影该论文的已接受
   evidence + 证据支持的论文角色结论。Paper/Route/Topic 三者是否都是必要的一级
   对象、集合要否增删，仍需真实 run 验证；taxonomy 放 schema 契约，可演进。
3. **投影确定性与可读性**：V1 已承诺结构化 claim-view（§19.3 的显式 trade-off）。
   开放问题是：claim-view 的**具体渲染格式**（每条含哪些字段），以及语句级生成
   "同一 evidence 状态 → 同一页面"在工程上如何做到（pinned 规则 / 纯函数 vs
   模板）；narrative 是否永远留在 Report、wiki 永不散文化。
4. **"为什么"层的归属（derivability 取舍）**：已澄清——route 失败模式 / 为什么
   拒绝某 route 是 evidence-backed 结论，属于投影内容（PROJECT_VISION §3.4 列
   失败模式为长期知识）；只有过程级 deliberation 留 run state。开放问题：若未来
   run 需要跨 run 复用"我们当时权衡过哪些替代方案"这种过程痕迹，是否需要显式的
   决策日志（P15 只列了结论层）。
5. **claim 级 vintage**：wiki claim 是否都带 as-of paper 版本，还是只对时效敏感
   的 route/topic 结论带？paper 事实用 paper version 是否足够？
6. **重建触发与成本**：evidence 变化即重建 vs review/synthesis 边界批量重建？
   局部重建（只影响视图）能否覆盖"跨 topic 的结论"？
7. **wiki 与 Report 的关系**：Report（本 run 交付）是否部分由 wiki（prior）+
   新 evidence 组成？二者如何共享 synthesis 而不重复？
8. **源删除 / retraction 语义**：被移除的论文对已接受的 evidence、依赖的 wiki
   claim、以及相关 route/topic 结论的具体影响流程（re-projection 移除 + 留痕 +
   触发 re-verification），是否应在 Domain Model 阶段定义为正式的 state 变迁？

# 21. Candidate ADRs Influenced by This Project

1. **ADR：Wiki 是 Accepted Evidence 的 Derived Projection——页面是证据状态的
   deterministic 函数，可丢弃、可重建，永不作为 Evidence Source of Truth。**
   （P15-17；对 reference 的核心背离，B/A 的答案。**衍生取舍：投影只覆盖
   evidence-backed 结论，过程级 deliberation 不在 wiki**——见 Q4 与 §10.3）
2. **ADR：每个 Wiki 陈述必须携带至少一个 accepted-evidence ID（claim 级引文），
   解析到 paper + locator；Python 构造性满足并 fail-closed 校验。**
   （P10/P22；Q6 选方案 B。**不设独立 S-id 注册表，但 Paper Store 保留
   current-version/last-verified 触发字段，投影层保留 evidence→视图逆映射索引**）
3. **ADR：Wiki 更新 = 从 accepted evidence 重投影（schema 契约驱动），不是 LLM
   增量重写页面；summary-of-summary 漂移是设计错误。**
   （P15-17；Q4 的答案；误区 3 的防御。**投影只保留矛盾、不解析矛盾；解析发生在
   fresh-review 边界**——见 §12 与 §19.3）
4. **ADR：矛盾与未解决问题作为一等 state 投影进 Wiki（渲染 Evidence.stance /
   analysis.contradictions），绝不静默解决。**
   （P10；Q5 的答案；借 reference"never silently resolved"原则）
5. **ADR：未来 Research Run 把 Wiki 当作 prior/leads 输入；每个被引用 claim 必须
   回源验证后才能成为新的 accepted evidence——验证目标是 Paper（重读 evidence
   locator 指向的原文段落），不是"用投影它的同一条 evidence 再检查一遍"（那只能
   证明投影忠实，不能证明 claim 为真）。**
   （P8；"Wiki helps decide what to investigate; papers decide what we may claim"；
   Q8 的答案）
6. **ADR：Wiki taxonomy 与维护规则是可编辑 schema 契约（非硬编码）；V1 从
   Paper / Route / Topic 三种知识页起步（P15 将三者都列为长期知识），集合可演进、
   以真实 run 验证。**
   taxonomy 的理由：Route = 跨论文结论（为何可行/被拒，引多篇 evidence），
   Topic = 主题景观（已知/矛盾/开放问题），Paper = 单篇论文的 evidence 聚合与
   论文角色结论——三者覆盖"单源事实 → 跨源综合 → 主题图谱"的知识密度梯度。
   （误区 1/9 的防御；Decision 8；§20 Q2 的 hypothesis 测试结论）
7. **ADR：Wiki 维护沿用 Python=integrity / Claude=meaning——Python 机械校验
   （evidence id 解析、投影一致、链接有效、陈旧标记），语义 fidelity 由 fresh
   review 判断；Wiki 更新不作为 Research Loop 的新 phase。**
   （延续 superloopy ADR；误区 4/5 的防御）

# 22. Five Sentences to Keep

> **1. A wiki statement must carry an accepted-evidence citation; no uncited claim.**

引文纪律从"lint 检查"升级为"构造性满足"：投影生成的每句必带 evidence id。

> **2. Wiki is derived, rebuildable state; accumulated LLM pages are a second source of truth.**

Reference 的 accumulate-maintain 模型会在实践中把页面变成事实源；我们选 projection。

> **3. Update is re-projection from evidence, not LLM re-summarizing old pages.**

Merge/rewrite 模型累积 summary-of-summary 失真；重建是唯一诚实的更新。

> **4. Conflicts are projected as first-class state, never silently resolved.**

结构化矛盾（Evidence.stance + analysis.contradictions）直接渲染，不靠 prose marker。

> **5. A future run uses the wiki to decide what to investigate; papers decide what may be claimed.**

Wiki = prior/leads；每个 claim 回源验证后才成为新的 accepted evidence。

# 23. One-Sentence Conclusion

spec-kit-wiki 是 Karpathy LLM Wiki 的一个精致实现，它证明了"LLM 维护的积累型
知识库"能有多强的纪律（no-uncited-claim、冲突保留、lint 机械/语义分层、query
诚实覆盖判定）——但它把页面当作积累品、让 query 把页面当 working truth、且
`rm -rf wiki/` 后不可重建，这正是我们 P15-17 要避免的三个点；因此它给我们的不是
"照做的 wiki"，而是一份**逐条对照清单**：哪些纪律照搬（引文构造性满足、身份分离、
机械/语义分层、诚实覆盖判定、schema 契约、cap 显式化），哪些机制必须反着来
（用 re-projection 替代 merge、用 evidence 引文替代 S-id registry、用渲染
contradiction state 替代 prose marker、用回源验证替代 pages-as-truth），让
"一次 Research Run 的 accepted evidence"真正变成"可跨 run 复用、可更新、可追溯、
可重建的本地知识"。
