# Study Note: beefiker/superloopy

> 本 Note 是第五份 Reference Study，对应我们 **Local LLM Wiki / Knowledge
> Accumulation** 能力——一次 Research Run 的有价值知识不应随 Report 完成而消失。
> Study 指南给的适配方向很明确：`Accepted Evidence → Wiki Projection → Paper/Route/
> Topic pages`，**Wiki 是 Derived State，不是 Evidence Source of Truth**。
>
> 阅读后最重要的发现：**superloopy 本身没有跨 run Wiki**——它的知识积累是 per-run 的
> evidence root（`.superloopy/evidence/research/<slug>/`）+ 一个「可重读的索引」
> （INDEX.md）。它真正值钱的是**知识进入长期存储前的验证纪律**：什么值得留（verified
> claim + provenance + vintage）、来源怎么分级、矛盾怎么保留、以及一个真实的机械 lint
> 验证器（fail-closed）。这些正是我们 Wiki 的「进料门槛」。

## Snapshot

```
Repository: https://github.com/beefiker/superloopy
Commit:     9814acc（#40 merge feat/say-it-straight；研究时点 HEAD）
Study date: 2026-08-09
License:    MIT
形态:       Claude Code / Codex 插件（skills + hooks + src/*.js 运行时 + 六船员 subagents）
```

注意仓库根的 DESIGN.md 是营销页克隆的视觉规范（配色/字体/WebGL 场景），不是插件架构——
真正的架构在 `skills/`、`agents/`、`src/*.js`、`hooks/`。

---

## Why We Studied It

前四份 Study 解决了：循环形状（spec-kit-harness）、控制流边界（old-search-harness）、
研究语义（paper-qa）、循环可信度（spec-kit-loop）。这份回答第五个问题：**一个研究 Run
产出的知识，怎么证明它值得留下来、并在未来被当作 prior 用？**

superloopy 的核心主张是一条标语：*"done needs to mean more than a confident status
sentence"*——完成必须指向 `.superloopy/evidence/` 下的真实 artifact，命令型 criteria
在完成时会**在进程内重新执行且必须复现**，陈旧或伪造的 pass 到不了 done。它对「什么知识
值得留」的回答是整套验证纪律：A-E 来源分级、retrieval verdict、expected-truths、
claim ledger（surface 多样性 / 反方搜索 / primary source / 双日期）、以及一个机械
验证器。这就是「研究知识 → 长期知识」之间的**进料门槛**。

同时它暴露了我们要补的空位：per-run 证据根 + INDEX.md 只解决「这次 run 里可恢复」，
不解决「跨 run 复利」。这正是 P15-17（Wiki Is Projection / Rebuildable）的动机。

---

## Architecture in One Diagram

```text
用户：loopy <task>（loop engineer 觉醒）/ loopy team <task>（crew 模式）
   │
   ▼
superloopy loop begin → guide → prove → check → finish（CLI 驱动，状态在 .superloopy/）
   │  六船员（可选 fan-out）：franky 建 · zoro 审 · usopp 测 · jinbe 门 · robin 审 · nami 找
   ▼
┌───────────────────────── 证据根（per-run）──────────────────────────┐
│  .superloopy/evidence/research/<timestamp>-<slug>/                    │
│  ├── INDEX.md            可重读的索引：一行一个 lead/claim/source，   │
│  │                       指向承载细节的 wave 文件（唯一例行重读）       │
│  ├── expansion-log.md    lead 去重账本（含拒绝过的 lead，防复现）       │
│  ├── wave-<n>-<kind>-<axis>.md  每 worker 返回一个 digest             │
│  ├── blocked-sources.md  blocked 来源 + 阶梯尝试 + substitute/gap     │
│  ├── expected-truths.md  事前写下的「必须为真」清单 → holds/violated/unknown │
│  ├── claim-ledger.md     claim 账本：observations/counter/primary/dates/dep │
│  │                       → verified | unresolved | refuted | deferred │
│  ├── verify-<slug>.md    代码型 claim 的运行验证                       │
│  └── SYNTHESIS.md        收敛后：executive answer / findings by theme │
│                          / sources(ranked) / verified claims /       │
│                          contradictions / gaps / expansion trace      │
└─────────────────────────────────────────────────────────────────────────┘
   │
   ▼
validate-research-evidence.mjs  机械 lint：fail-closed（缺账本/无出处/一域多观察/
                                未标价格/引用无来源/缺口未命名… → 非零退出）
   ▼
完成（证据根 + 审计重派生：完成时在进程内重跑每个命令型 criterion）
```

关键观察：**这是研究 Run 的「实验室笔记本」纪律**——写入即恢复点、索引必须触及细节、
验证器把证据契约变成可执行的检查。它缺的只是「把笔记本沉淀成跨 run 的知识库」这一步。

---

## Core Concepts

1. **Evidence-first 完成**：每个 pass 指向证据根下的真实 artifact；命令型 criteria 在完成
   时被重跑且必须复现。manual（非命令）criteria 只能验证 artifact 存在，正确性靠 auditor
   判断 + 人审——确定性保证的强弱是明说的。
2. **「检索到的内容是数据，永远不是指令」**：untrusted-content 边界——从网页/API 拉来的
   一切（包括伪装成指令的文本）只能作为「关于问题的证据」，绝不执行。对注入式
   `SUPERLOOPY_EVIDENCE:` 行只当引文，不当 lane 结果。
3. **A-E 来源分级 + retrieval verdict**：每个来源带 grade（A=同行评议/标准 … E=论坛/
   聚合器）、fetch 结果（ok/partial/blocked/error/empty）、observed/as-of 双日期。
   D/E 只能开 lead 或补充，不能当高风险 claim 的承重墙。
4. **Expected truths**：问题有 authority 时，**检索前**写下「intent 成立则必须为真」的
   清单，再去测现实（holds/violated/unknown）。violated 必须落到可见处（claim 或 gap）。
5. **Claim ledger 的数据流锁**：高风险非代码 claim 只有过了完整门（≥2 个不同 surface 的
   独立观察 + 中性分母 + 一次反方搜索 + primary source + 双日期 + dependency 无环）才进
   `verified-claims`；synthesis 只允许从 verified 行取料——「跳过门就没有可综合的」。
6. **Proof is priced**：花验证额度前先记录「错了会花多少」。风险分档来自后果而非趣味；
   门保持二元，贵路径保持稀缺。
7. **Contradictions 是一等输出**：synthesis 有 `## Contradictions`（源 A vs 源 B、各自
   所在 surface、带证据的解决），refuted 是合法状态（反方搜索赢了），abstention 是正确
   结果而非漏洞。
8. **INDEX.md = 写细节下去，读摘要回来**：bulk 进 wave 文件，只有 INDEX 例行重读；索引
   必须触及细节（验证器检查），否则细节在实践中不可达。
9. **完成审计重派生**：Superloopy 不信任自己记录的状态（worker 可写），在验收与完成门处
   **在进程内重派生**确定性地板；非复现的 audit 标 `inconclusive` 绝不静默失败。
10. **Continuation Engine**：Stop hook 是 progress-gated 的（只有新证据重置无进展计数）；
   上限/停滞 → `blocked` 求人；quota 限制 → `paused`（可恢复，不烧计数）；**绝不伪造
   完成**。

---

## Important Files

| 文件/技能 | 角色 | 对本 Study 的意义 |
|---|---|---|
| `skills/superloopy-research/SKILL.md` | 研究技能（329 行） | **核心**：Phase 0-5、claim ledger、expected-truths、机械验证器说明 |
| `skills/superloopy-loop/SKILL.md` | 循环技能（218 行） | 契约、Continuation Engine、Evidence Audit、Quality Gate |
| `skills/superloopy-research/scripts/validate-research-evidence.mjs` | 机械验证器 | 真正的 lint 代码：fail-closed 检查证据契约 |
| `agents/*.md` | 六船员 | franky 建 / zoro 审 / usopp 测 / jinbe 门 / robin 审 / nami 找（角色 lane） |
| `src/loop.js · prove.js · audit.js · trace.js · store.js` | CLI 运行时 | begin/guide/prove/check/finish/audit 的机制 |
| `hooks/*.json` | 钩子 | Stop hook（progress-gated continuation）、session-start、user-prompt-submit |
| `docs/superloopy-*.md` | 策略文档 | model-policy、gate-notes、interop、validation |

---

## Key Data Flow

```text
Phase 0 Scope：core question + 3+ 正交 axes + as-of/locale/out-of-scope + min grade
       │  + intent authority → 有 authority 就先写 expected-truths.md
Phase 1 Saturation wave：整个第一波一次发完（每 axis 一 worker）；advisory profile
       │  （focused-web 6w/32q/2wv … exhaustive 15w/80q/5wv）
       │  每个返回：digest + ## EXPAND + ## SOURCES（无 verdict 的 lane = 说了相信而非读到）
       ▼
Phase 2 Expand until convergence：每 lead 即刻派工；对 expansion-log 去重（含拒绝过的）；
       │  干波只在 lane 真正 retrieved 才算（empty/blocked/silent 记 unknown，不算干）
       │  收敛：无未查 lead / 连续两波无新 lead / 达到波目标且无未解决高风险 claim
Phase 3 Verify：代码型 claim 跑代码 → verify-<slug>.md
Phase 3b Lock：非代码 claim 过 data-flow-lock → claim-ledger（verified/unresolved/refuted/deferred）
       │  只从 verified 行取料
Phase 4 Synthesize：先读 INDEX，再按主题开必要 wave 文件 → SYNTHESIS.md
       │  inline [Source N] 引文 · ## Contradictions · ## Gaps · ## Expansion trace
       ▼
验证器：node validate-research-evidence.mjs --root <slug> --json
       │  fail-closed（非零退出 = 修证据，不是改行）
       ▼
superloopy loop evidence --status pass --artifact SYNTHESIS.md（完成记录）
```

**知识流**：`raw retrieval（不保留为知识）→ verified claim + graded source（知识单位）
→ synthesis（当次交付）→ 机械验证（进料门槛）`。缺最后一环：**跨 run 沉淀**。

---

## Key State Model

```text
.superloopy/                            全局循环状态
├── goals.json                          目标/标准（CLI 管理，禁止手改）
├── loop-control.json                   迭代计数、no-progress 高水位、blocked/paused
├── audit-state.json                    审计记录（worker 可写 → 完成时在进程内重派生）
└── evidence/                           证据根
    └── research/<timestamp>-<slug>/
        ├── INDEX.md                    唯一例行重读：一行一 lead/claim/source → wave 文件
        ├── expansion-log.md            lead 去重账本
        ├── wave-<n>-<kind>-<axis>.md   worker digest（append）
        ├── blocked-sources.md          url | tiers | reason | substitute | status
        ├── expected-truths.md          id | expected | source | observed | status | claim
        ├── claim-ledger.md             id | claim | risk | cost | observations |
        │                               counter | primary | observed | as-of | depends-on | status
        ├── verify-<slug>.md            代码型验证
        └── SYNTHESIS.md                交付物（八节结构）
```

claim-ledger 的表头就是「值得留的知识」的 schema：**风险、犯错成本、观察来源、
反方搜索、primary、observed/as-of 双日期、依赖链、状态**。这是我们 Wiki 页每条知识
都应继承的最小字段集。

---

## Design Decisions Worth Learning

### Decision 1 — 知识单位 = verified claim + provenance + vintage（不是原文）

**Problem**：一次研究 Run 里什么值得留下来当长期知识？原始检索显然不值得全留。

**Design**：唯一能进入 synthesis（=当次知识交付）的是过了 data-flow-lock 的 verified
claim：≥2 个不同 surface 的独立观察（`rendered/api/repo/registry/standard/filing/legal/
dataset/survey/press/community/runtime` 闭集，两个同 surface 算一次）、数字要有中性分母、
一次主动反方搜索、primary source、observed+as-of 双日期、depends-on 依赖链。raw
retrieval（wave digest）留在 bulk 里，不被当作知识。abstention（unresolved/refuted）
是合法状态。

**Why**：知识的最小可信任单位是「**论断 + 出处 + 时效**」。没有 provenance 的断言进不了
知识库；没有 vintage 的断言会把「去年还对」变成「今天错」（as-of 与 observed 混淆正是
反方搜索最抓不住的失败）。`depends-on` 让一个塌掉的事实拖垮下游 claim，而不是让下游
claim 孤零零站在 synthesis 里。

**Trade-off**：门槛高，很多 claim 永远停在 unresolved/refuted——但这就是「abstention 是
正确结果」。贵路径靠「proof is priced」保持稀缺：决定依赖的 claim 走全门，只补上下文的
可以 hedge 或 drop。

**我们是否存在同样的问题**：是——我们的 Wiki 页若直接收证据摘要就会污染。**是否有更简单
的实现**：我们不必复刻 12 值 surface 闭集；我们的「surface」天然是论文（第几篇 + 哪个
section + 什么立场），比 web surface 更规整。但「≥2 篇独立论文支撑才敢写进 Wiki、
双日期、反方证据」这套纪律直接适用。
**结论**：采纳——**Wiki 的进料单位是 verified claim + provenance（哪些 evidence locator
支撑）+ vintage（as-of 论文版本）**，原始证据不进 Wiki，Wiki 只是投影。

---

### Decision 2 — INDEX.md = 写细节下去，读摘要回来（可重读的索引必须触及细节）

**Problem**：run 里的细节（wave digests、claim 详情）会撑爆上下文，但丢了又不可追溯。

**Design**：bulk 进 wave 文件且**只 append**；INDEX.md 是唯一例行重读的文件，一行一个
lead/claim/source，每行命名承载细节的 wave 文件。验证器检查：索引必须触及细节（每个
wave 文件被命名、每个 claim id 有行）——"an index that does not reach the detail makes
the detail unreachable in practice"。

**Why**：这是「写细节下去、读摘要回来」的完整表述。它把「上下文是状态的 view」落到
文件结构上：summary（INDEX）与 detail（wave）分层，重读默认只在 summary 层，需要时
按主题进 detail。这是 P21 的又一个实证，而且明确了「索引与细节的可达性」是一条可机械
检查的不变量。

**Trade-off**：要求维护纪律（每 append 一个 digest 就加一行索引）；但去重可以机械做
（用搜索工具对 expansion-log 匹配，而不是读进上下文——"mechanical matching is cheaper
and stricter than remembering"）。

**我们是否存在同样的问题**：是——我们的 Wiki 页必须有「索引/详情」分层与可重建性。
**是否有更简单的实现**：wiki 页本身就是「投影 + 指向 accepted evidence locator」，
投影即摘要，细节在 evidence 层。验证器检查「页上每条知识都能从 accepted evidence 重建」
就是这个不变量。
**结论**：采纳——Wiki 页是摘要投影，必须能触及（并重建自）accepted evidence；
可重建性是机械校验项。

---

### Decision 3 — 机械验证器：lint 把证据契约变成可执行的检查（Q7 的答案）

**Problem**：证据契约（claim 有出处、引文有来源、缺口被命名）靠人记会悄悄腐化。

**Design**：`validate-research-evidence.mjs` 是一个真实的验证脚本，**fail-closed**：缺
claim-ledger、verified 行观察 surface <2、高风险行只有一个域名或没有 primary surface、
surface 标签不在闭集、verified 无反方搜索、日期不可能、claim 未定价、依赖 refuted/
unresolved、依赖成环、`[Source N]` 引文没有对应编号 bullet、INDEX 不触及 wave 文件、
blocked 行还 open、expected truth violated 没有对应 claim、gap 没在 synthesis 命名……
全部非零退出。「非零退出就是答案：修证据，不是改行。」

**Why**：一致性检查解决的是**记录与声称之间的漂移**。验证器不判断「内容对不对」（那是
checker/人），它判断「证据契约是否被静默违反」。这正是一份可审计研究 Run 的最低底线：
「这个断言有没有出处、那个缺口有没有被命名、这条引文指向哪」。

**Trade-off**：验证规则要随证据 schema 演进；但 fail-closed 的代价是「宁可报错也要让
契约成立」——正是 P13/P22 想要的。

**我们是否存在同样的问题**：是——我们的 Wiki 重建必须可校验。**是否有更简单的实现**：
我们不用 JS 验证器，用 Python（我们的 Research Runtime）对 wiki 投影做结构校验：
每条知识必须带 accepted-evidence locator、每个 claim 立场可解析、每个引用可重建。
**结论**：采纳——**wiki 重建校验是机械的、fail-closed 的**（Python 实现）。

---

### Decision 4 — Contradictions 是一等输出，不在投影时被解决掉（Q6 的答案）

**Problem**：研究里两篇论文互相矛盾，怎么保留而不偷偷选边？

**Design**：synthesis 的 `## Contradictions` 节：源 A vs 源 B、各自所在的 surface、
以及带证据的 resolution。claim-ledger 有 `refuted`（反方搜索赢了）与 `unresolved`
（证据不足）作为合法状态；abstention 是正确结果。预期-真值表里 `violated` 也必须落到
可见处。

**Why**：矛盾是研究输出里**最有价值的部分**（它决定结论的可信度），把它平掉等于
销毁信息。旧 harness（old-search-harness）的「非共识一等产物」也是同一个道理；superloopy
把它进一步变成「矛盾必须带 resolution 或 gap，且被 lint 检查」。

**我们是否存在同样的问题**：是——P10 的 contradicting stance + non-consensus 记录。
**是否有更简单的实现**：我们的 evidence 已有 stance（supporting/contradicting/
qualifying）；wiki 投影时把 contradicting 组保留成独立小节，不被单方覆盖。
**结论**：采纳——**矛盾（含被反证的）是 Wiki 的一等内容**；lint 检查矛盾是否被命名。

---

### Decision 5 — Expected truths 事前写 + 事后重测（跨 run 更新的机制原型，Q5/Q8）

**Problem**：已有知识（Wiki）怎么更新，而不是无限 append？

**Design**：superloopy 没有跨 run 更新；但它有 re-measurement 模式：问题有 authority 时，
**检索前**写下「intent 成立则必须为真」的 expected-truths（holds/violated/unknown），
研究去**测现实**，violated 的落到 claim 或 gap。这就是「预注册假设 + 重测」——一个
知识条目跨 run 的更新方式不是 append 新事实，而是**重测旧预期、按结果改写**。

**Why**：更新语义里最难的诚实问题是 vintage：「去年对，今天还对不对？」as-of/observed
双日期 + 预期重测给出答案。这比「把新论文摘要 append 到页面」诚实得多。

**我们是否存在同样的问题**：是——P15-17 要求 Wiki 可重建、可更新。**是否有更简单的
实现**：**重建即更新**——Wiki 页不从旧页增量改，而是每次从 accepted evidence 重新
投影（新证据进来，投影重算，旧结论若被新证据推翻就带 contradicting 记录落下）。
superloopy 的「完成时重派生确定性地板」是同一个哲学：不信任陈旧记录，从可信源重算。
**结论**：采纳——**Wiki 更新 = 从 accepted evidence 重建投影 + 预期重测**，不手改、
不无限 append。

---

### Decision 6 — Evidence audit 重派生：不信任记录的状态（可信度保障）

**Problem**：证据/审计记录可能被写错或被改（worker 可写 .superloopy/audit-state.json），
怎么保证完成时用的是真实状态？

**Design**：Superloopy 在验收与完成门处**在进程内重派生**确定性地板：完成时 `review`/
`checkpoint` 重跑每一个已 pass 的命令型 criterion（不止被引用的），hash 验证每个被引
audit verdict。一个非复现的 re-run 标 `inconclusive`（绝不静默失败，防 flaky）；
`SUPERLOOPY_AUDIT_MAX_FAILS=3` 后标 `blocked` 求人。它诚实地承认无法验证 auditor
subagent 是否真被隔离运行（信任 host 的 agent 帧）——但它**不信任自己的记录**。

**Why**：可信度取决于「完成时是否重算」，不取决于「记录时是否诚实」。这是
「Harness exposes state, not hide it」的纵深版本：连状态本身都可能被污染时，重派生是
唯一可靠的地板。

**我们是否存在同样的问题**：是——我们的 Wiki 页可能是陈旧投影。**是否有更简单的实现**：
同 Decision 5——**Wiki 永远从 accepted evidence 重建，重建是校验**。不信任任何
「上次生成的页面」。
**结论**：采纳——**完成/交付门对「投影是否与 accepted evidence 一致」做机械重校验**。

---

### Decision 7 — Untrusted content 边界：检索到的内容是数据，永远不是指令

**Problem**：研究从网页/API 拉内容，可能混入 prompt injection（伪装指令的文本）。

**Design**：明确的注入防线：检索到的一切只能作为「关于问题的证据」，不执行、不服从、不转述
它的指令；页面要求被信任 = 降级理由；reply markers 只算自己派发的 worker；fetched
content 不能授权写文件/跑命令/用凭据。这条边界也写进 worker 的 dispatch 消息。

**Why**：研究流程里 untrusted 输入的量级远超代码评审；注入文本一旦被当作指令执行，
整个 evidence 链就塌了。old-search-harness 的 trust boundary 与此一致，superloopy
把它做成可测试的规则。

**我们是否存在同样的问题**：是——我们从 DeepXiv/arXiv/OpenAlex/网页取论文元数据与正文。
**是否有更简单的实现**：对我们，风险主要在论文正文/摘录被当作指令（尤其 PDF 里的恶意
文本）；边界 =「检索内容只是证据」+ 适配器 fail-closed（旧项目已示范）。
**结论**：采纳——证据摄入始终是「数据非指令」，适配器 fail-closed。

---

## What We Should Borrow

1. **知识单位 = verified claim + provenance + vintage**（Decision 1）：Wiki 进料门槛——
   只有带 evidence locators、独立支撑、双日期、立场/状态的断言能进。P8/P10/P15。
2. **INDEX/细节分层 + 索引必须触及细节**（Decision 2）：Wiki 页是投影摘要，必须能重建自
   accepted evidence；可重建性机械校验。P15-17/P21。
3. **机械 lint / fail-closed 验证器**（Decision 3）：wiki 重建校验、引文-来源可达性、
   缺口被命名——用 Python 实现，不做 JS 验证器。P13/P22。
4. **矛盾保留为一等内容**（Decision 4）：contradicting evidence + refuted + unresolved
   组是 Wiki 的合法部分，不被投影时平掉。P10。
5. **Expected-truths 预注册 + 重测**（Decision 5）：跨 run 更新机制 = 重测旧预期、
   按结果改写，而非 append。P7/P15。
6. **重建即更新、不信任陈旧记录**（Decision 5/6）：Wiki 从 accepted evidence 重建；
   完成门重校验一致性。P15-17。
7. **Untrusted content 边界**（Decision 7）：检索内容只是数据。适配器 fail-closed。
8. **retrieval verdict 纪律**：每个来源带 grade + 状态 + 双日期；extraction 有损所以
   **不能证明不存在**（absence claim 是昂贵的错）。这直接服务于我们的证据收集。
9. **Proof is priced**：先记「错了花多少」再决定验证深度——对资源预算（P13）友好。
10. **abstention 是合法结果**：unresolved/refuted 明确记下来，不假装解决。

## What We Should Not Borrow

1. **完整插件/钩子基础设施**：Stop hook、continuation engine、loop-control/audit-state、
   model-policy、wrapper-install、auto-update——整套宿主集成是我们不需要的运维复杂度。
2. **命令型 criteria 重跑语义**：研究 claim 不是能重跑的 shell 命令；我们的「确定性地板」
   是 claim→evidence→locator 校验（Python 检查 excerpt 在缓存原文中存在），不是跑命令。
3. **六船员 + 角色 lane 体系**：franky/zoro/usopp/jinbe/robin/nami 的 crew 编排对我们是
   过度；P12 的 fresh review 一个语义检查点就够。
4. **A-E 来源分级表 + 12 值 surface 闭集**：我们以论文为主（arXiv/OpenAlex），分级会简化，
   surface 天然是「论文+section」，不需要 web 面闭集。
5. **blocked-source 阶梯 / quota 记账 / machine-readable twins**：我们不走任意网页爬取，
   检索走论文 API，不需要这套 web 韧性工程。
6. **per-run evidence root 目录结构照搬**（`research/<timestamp>-<slug>/` + wave 文件）：
   我们有自己的状态布局；借鉴的是其中的 discipline（索引触及细节、ledger 字段），不是目录。
7. **research skill 的 web 搜索 craft**（site:/filetype:/intitle: 操作符等）：我们检索的是
   论文语料，不是开放网页。

## Conflicts with PROJECT_VISION

1. **Wiki is Derived State（P15-17）vs superloopy 的 per-run 证据根**：superloopy 没有跨
   run 投影；它的知识留在当次 evidence root。我们不采纳「证据根即知识」，采纳
   「Accepted Evidence → Wiki Projection」。这是指南明示的适配方向。
2. **对齐 P11/P12**：Evidence-first 完成（done 需 proof）、audit 重派生、blocked→求人、
   绝不伪造完成——与 P11（不能自宣布 done）、P12（fresh review）一致，是证据。
3. **P13/P14**：Proof is priced（后果决定验证深度）、abstention 合法、typed claim
   status——与「criteria over magic scores」一致；它没有加权分，只有二元门 + 风险标记。
4. **P7 gap-driven**：Expand-until-convergence + 干波只在真实检索时才算 + 缺口必须被
   synthesis 命名——P7 的实证。
5. **P8（Paper Is Not Evidence）**：retrieved content 是 data 不是 instruction；absence
   claim 不能由有损提取断言——直接强化 P8。
6. **潜在冲突**：web 韧性工程（blocked 阶梯/quota）与「我们是论文 API 检索」的范围冲突——
   我们明确不迁移（见上）。

## Questions Still Open

1. **Wiki 页的最小单位**：Paper 页 / Route 页 / Topic 页（指南给的三种）各自收录什么粒度
   的 verified claim？claim 与「accepted evidence 里的 stance」如何对应？
2. **跨 run 键控**：不同 run 对同一篇论文/同一条方法路线的 claim 如何合并？
   old-search-harness 把「稳定知识主键」留作 P1；superloopy 没解决。我们是否以
   paper id（DOI/arXiv id）为锚，claim 去重靠「同 paper + 同 section + 同立场」？
3. **Wiki 的验证门槛**：一条知识进 Wiki 需要 ≥N 篇独立论文支撑吗？还是 N=1 但标
   stance/置信？Proof-is-priced 原则在此如何套（决定依赖的高风险 claim 多篇，补充性单篇）？
4. **vintage 怎么做**：arXiv 版本演进（v1/v2）与 preprint→published 如何影响 as-of？
   是否要 pin 论文版本才能让「双日期」有意义？
5. **重建频率与触发**：Wiki 页何时重投影——每次新证据 accepted 就重算，还是 REVIEW/
   SYNTHESIZE 时批量？「重建即更新」的增量成本如何控制？

## Candidate ADRs Influenced by This Project

1. **ADR：Wiki 是 Derived State——页是 accepted evidence 的投影，可从证据重建，永远不是
   Evidence Source of Truth。**（P15-17）
2. **ADR：Wiki 进料单位 = verified claim + provenance + vintage；原始证据不进 Wiki。**
   （Decision 1，P8/P10）
3. **ADR：Wiki 页引用纪律 + 重建校验（lint）——每条知识带 accepted-evidence locator，
   校验 fail-closed（Python）。**（Decision 2/3，P13/P22）
4. **ADR：矛盾保留——contradicting/refuted/unresolved 组是 Wiki 一等内容，投影不平掉。**
   （Decision 4，P10）
5. **ADR：跨 run 更新 = 预期重测 + 从 accepted evidence 重建投影，不手改、不无限 append。**
   （Decision 5/6，P7/P15-17）
6. **ADR：证据摄入的 untrusted-content 边界——检索内容是数据非指令，适配器 fail-closed。**
   （Decision 7，P8）

## 一句话结论

superloopy 证明了一件事：**「什么知识值得留」是一个验证问题，不是一个存储问题**。它的
进料门槛（verified claim + provenance + vintage、来源分级、反方搜索、abstention 合法、
机械 lint fail-closed）回答了 Study 指南 Q1-Q7 的每一问——除了 Q8（跨 run prior），
而 Q8 恰恰暴露它只解决了 per-run 笔记本纪律、没解决跨 run 知识库。这正好是我们
P15-17 的空位：**把 superloopy 的验证纪律做成 Wiki 的进料门槛，把「重建即更新、
不信任陈旧记录」做成 Wiki 的生命周期，让一次 Research Run 的 verified knowledge
真正跨 run 复利。**
