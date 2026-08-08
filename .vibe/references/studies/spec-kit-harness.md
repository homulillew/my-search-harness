# Study Note: formin/spec-kit-harness

> 本 Note 基于实际阅读 commit 时的仓库源码与文档撰写。所有「借鉴」判断都服从
> PROJECT_VISION：`Claude Code = Agent Runtime / Loop Driver`，`Python Harness = Research Runtime`。

## Snapshot

```
Repository: https://github.com/formin/spec-kit-harness
Commit:     7c482844ff669b4f1ac93e3decfebef947f74e22
Study date: 2026-08-08
License:    MIT (© 2026 formin)
Version:    v1.0.0 (extension.yml)
```

---

## Why We Studied It

它是与「Research Harness」概念最直接接近的参考：把 Harness-1 论文
(arXiv:2606.02373) 的 *state-externalizing harness* 改造成一个 Spec Kit 扩展。
我们主要用它回答一个核心问题：

> 一个长程 Research Agent 的状态，应该如何从 Conversation 中外置？

关键前提：它**没有任何可执行代码**，全部行为由用户自己的 coding agent 按 prompt 文件执行
（"the agent is the interpreter"）。这对我们的架构决策既是证据、也是反面教材。

---

## Architecture in One Diagram

```text
User's coding agent = Policy（只做语义决策）
        │  每轮只输出一个动词：SEARCH / INSPECT / CURATE / STOP
        ▼
specs/<feature>/harness/*.md  （Harness = environment-side working memory）
├── budget.md          mission + budget 台账 + stop conditions + action log
├── candidates.md      候选池：dedup(source+topic)，append-only C001…，状态机
├── curated.md         重要度标记的 curated 集：cap 25，importance 分级，eviction
├── evidence.md        紧凑指针：source + locator + ≤25 词 excerpt
├── verification.md    逐 claim 的 verdict/method/confidence/evidence/date
└── observations.md    压缩去重日志：≤3 行/条，dup-of 标记
        │  只渲染 SLICES（绝不整文件）
        ▼
budget-aware context rendering
（/speckit.harness.status；explore 每轮开头也按 slice 加载）
```

外围：`/init` 建六个文件（幂等）；`/verify` 对抗式验证并回写；`/report` 把状态
合成到 `research.md` 的 requirement-coverage 表（这是唯一一次整文件读取）。

---

## Core Concepts

1. **Policy / Bookkeeping 分离**（Harness-1）：模型只用语义判断（搜什么、留什么、
   何时停）；去重、压缩、记账、eviction 全部是机械规则，由 state 文件承担。
2. **Conversation is disposable**：值得留的一切在学到的瞬间写入文件；`status`
   一步把工作画面重建进新 session。"State survives; context is rebuilt on demand."
3. **六类状态文件**，每个有明确的 invariants（见 Key State Model）。
4. **四个动词**：`SEARCH / INSPECT / CURATE / STOP`——policy 的自由度被刻意收窄，
   其余都是强制 bookkeeping。
5. **Slice-only rendering**：每个命令只加载受 token cap 约束的切片，counts 代替
   未显示的内容。
6. **对抗式验证**：verify 的目标是 *refute* claim（先问"如果它是假的会怎样"），
   回主源核对，而不是确认引用。
7. **Prompt-only enforcement（诚实声明）**：bookkeeping 是"by instruction, not by
   construction"，靠机械规则 + diff 可见性兜底。
8. **不碰产品工件**：harness 永不编辑 spec.md/plan.md/tasks.md，只回写
   `research.md` 的标记块，纠错以 suggested edit 形式回流。

---

## Important Files

| 文件 | 作用 |
|---|---|
| `commands/speckit.harness.explore.md` | 核心循环：render slice → policy 决策 → act → 强制 bookkeeping；stop rules |
| `commands/speckit.harness.init.md` | 创建六文件；幂等；mission/budget 覆盖解析 |
| `commands/speckit.harness.status.md` | budget-aware 渲染函数 + resume 入口；只读 |
| `commands/speckit.harness.verify.md` | 对抗式 claim 验证；refutation 传播 |
| `commands/speckit.harness.report.md` | 全量读取 → requirement→evidence 映射 → coverage 表 → research.md |
| `docs/concepts.md` | Harness-1 映射 + 与论文的刻意差异（含诚实 caveat） |
| `openwiki/architecture/overview.md` | 架构总览、六状态文件、config 优先级 |
| `config-template.yml` | 配置 schema：budget / curation / rendering / state / stop_conditions |
| `extension.yml` | manifest：5 commands + 2 hooks + defaults |

---

## Key Data Flow

```text
/init
  → 解析 HARNESS_DIR（branch→specs/<feat>/，否则 fallback）
  → 一次性创建六文件（幂等，budget.md 存在则只 append mission）

/explore（每轮）
  render slice（budget 表+末5行 action log / top15 curated / ≤10 open candidates / 末8 observations，≤4000 token）
    → policy 输出一个动词
    → act（真实工具执行）
    → bookkeeping（每轮全做）：
        append observation（≤3 行，dup-of 标记）
        update candidates（dedup source+topic，标记 inspected）
        curate（curated.md 加行 ≤2 句 + evidence.md 加指针，超 cap 则 evict）
        account（budget 台账 spent++ / remaining--，action log 加行：是否产出新 curated）
    → 检查 stop conditions

/verify
  抽取 load-bearing claims（spec/plan/critical curated）
    → 对抗式核对主源（一次 budget 单位一个主源）
    → verification.md 记一行 + evidence 指针 + budget 扣减
    → refuted 则 curated 标记 refuted（不删），suggested edit 回流

/report
  读全部状态（唯一例外）+ spec.md
    → requirement→evidence 映射 → coverage 分类（covered-verified / covered-unverified / contradicted / uncovered）
    → 写入 research.md 的 <!-- harness:begin/end --> 块

/status（resume 入口）
  render 快照（mission / budgets / curated / open frontier / refuted / 未验证 critical / recent）
    → 输出恰好一个推荐动作
```

---

## Key State Model

六个状态文件各自只回答一个问题，职责严格分离：

| 文件 | 回答的问题 | Invariants |
|---|---|---|
| `budget.md` | 允许花多少、已花多少、何时停 | mission（可多个）、每资源 Budget/Spent/Remaining、context render cap、stop conditions、append-only action log |
| `candidates.md` | 发现了什么 | dedup key=source+topic；append-only C001…；状态机 `new→inspected→curated:<E-id>｜discarded(<reason>)` |
| `curated.md` | 决定保留什么 | cap 25；importance critical/high/medium/low；finding ≤2 句；evict lowest-first；refuted 标记不删 |
| `evidence.md` | 证据在哪 | 指针而非内容：source、locator、≤25 词 excerpt、supports；ID 与 curated 对应 |
| `verification.md` | 检查了什么 | 每行 claim + method + verdict(verified/refuted/unverifiable) + confidence + evidence + date |
| `observations.md` | 发生了什么 | append-only；≤3 行/条；dup-of 标记；绝不粘贴原始工具输出 |

`research.md` 不是状态：它由 report 派生，是 harness → 核心工作流的唯一桥。

---

## Design Decisions Worth Learning

### Decision 1 — 状态外置到纯 Markdown 文件，而非代码/DB

- **Problem**：长程研究的 working memory 放 conversation 里会随窗口溢出而丢失、重复搜索、claim 未验证就硬化进 plan。
- **Design**：`specs/<feature>/harness/*.md` 作为 environment-side working memory。
- **Why**：普通文件 durable、可 diff、可 code review、可被多个 agent/人共享；"recoverable search state"。
- **Trade-off**：Markdown 无法由机器强制 schema / atomic write / 并发一致性；invariant 依赖 prompt 与肉眼 diff。
- **Transferability to our project**：状态外置的思想**直接迁移**（我们 P2/P3 本就是为此）。但**载体不迁移**——我们 V1 用 JSON/JSONL + schema validation（P18/Engineering Quality），markdown 留给 wiki/report 这类投影。

### Decision 2 — Candidate / Curated / Evidence 三层分离

- **Problem**：把"相关论文"直接当"证据"会产生弱引用；搜索广度容易因分心丢失。
- **Design**：candidate 池（发现、去重、状态机）≠ curated 集（带重要度、有上限）≠ evidence 指针（证明在哪）。
- **Why**：三个层次回答三个不同问题——"值得看吗 / 值得留吗 / 凭什么支持这个 claim"。curated cap 把它保持为 working set 而非 scrapbook。
- **Trade-off**：多一层 bookkeeping；curated 用 importance 标签 + eviction，语义偏"通用信息筛选"。
- **Transferability to our project**：**强迁移**。它正是我们 P8「Paper ≠ Evidence」的实例化。但我们的 curated 语义应改为 **gap/RQ 键控**（curated entry 服务于哪个 Research Gap），而非通用 importance 标签。

### Decision 3 — Evidence 是指针，不是内容

- **Problem**：把整段原文塞进状态会放大 context、且验证时只会信任缓存摘要。
- **Design**：evidence 只存 source + locator + ≤25 词 excerpt；"pointers, never content"。
- **Why**：状态渲染便宜；强制验证必须回到主源（"evidence.md 告诉你到哪看，不告诉你什么是真的"）。
- **Trade-off**：excerpt 信息量有限；locator 需"能扛住小改动"（函数名/锚点）。
- **Transferability to our project**：**强迁移**，与我们 P10「Evidence Must Be Traceable」一致（Paper ID / Section / Locator / Excerpt / Stance）。我们还可比它更强：把 excerpt/stance 做成 schema 字段由 Python 校验。

### Decision 4 — 每轮只渲染 bounded slice，带 token cap

- **Problem**：状态丰富后如果全塞回 context，外置就失去意义。
- **Design**：所有命令只加载 slice（budget 表+末5行日志、top15 curated、≤10 open candidates、末8 observations），`context_tokens: 4000` 软上限，超限先丢 low importance；counts 代替未显示内容。
- **Why**：长程研究的花费从"随对话长度增长"变成"随文件大小增长"（近似无限）。
- **Trade-off**：cap 是 prompt 里的软目标，无真实测量；slice 内容固定，无法按 Action 差异化。
- **Transferability to our project**：**强迁移**，直接支撑我们 P21「Context Is a View of State」。我们更进一步：Context Renderer 应**按 Action 渲染不同 slice**（搜索决策 vs 证据分析需不同视图），而 spec-kit 是固定四文件 slice。

### Decision 5 — Budget 台账 + typed stop conditions

- **Problem**：研究无界、agent 自己判"够了"。
- **Design**：`budget.md` 每资源 Budget/Spent/Remaining + action log；stop = 预算耗尽 ｜ marginal-gain window（默认 3 连动无新 curated）｜ mission answered 且 critical 全 verified ｜ 用户打断。
- **Why**："numbers bound the loop"；marginal-gain 是论文 stop 规则，避免重复搜索白烧预算。
- **Trade-off**：预算靠 agent 诚实记账（markdown 表）；"新 curated evidence"作 yield 信号对科研阅读可能过粗（一次有价值的深读可能不立即产出行）。
- **Transferability to our project**：**机制迁移、实现不迁移**。我们采纳"资源用数字约束 + 完成用条件判断"，但 budget 记账由 Python 做（原子扣减、防绕过）；yield/stop 信号应基于 **gap 是否被覆盖**（covered/partial/missing），而非简单的"有没有新 curated 行"。

### Decision 6 — 对抗式验证 + 持久 verdict + refutation 传播

- **Problem**：self-grading / confirmation bias；"我查过"会硬化成未检验的断言。
- **Design**：verify 显式要求先尝试 refute；verdict 留档（verified/refuted/unverifiable + method + confidence + evidence + date）；refuted 的 curated 标 `refuted (see V-xxx)` 但不删（记录死路防重蹈）。
- **Why**：验证不是重新读一遍作者引用的东西；记住死路是 harness 防止重复推导旧错误的方式。
- **Trade-off**：一次 budget 单位一个主源检查；`verified` 不允许 low confidence。
- **Transferability to our project**：**强迁移**，与 P11/P12 的独立 Review Gate 同源。spec-kit 用"同一 agent 遵守对抗性 prompt"近似独立；我们则用 **fresh-context reviewer** 真独立——这是我们从它的妥协中提炼出的增强点。

### Decision 7 — 单一只读 status 命令即 resume 入口

- **Problem**：session/context 丢失后一切从零。
- **Design**：`/status` 渲染完整工作画面 + 恰好一个推荐动作，是 resume 入口；conversation 可随时死，状态不死。
- **Why**："The files are the memory."
- **Trade-off**：推荐动作由渲染状态派生，逻辑简单但覆盖不了所有下一步。
- **Transferability to our project**：**强迁移**，直接支撑我们 P22「Harness Expose State, Not Hide It」的 `status`/`next` 接口设想。

### Decision 8 — 永不编辑产品工件，只回写带标记块 + suggested edits

- **Problem**：harness 与 authoring 混在一起会污染 spec/plan 的作者权与可追溯性。
- **Design**：只写 `research.md` 的 `<!-- harness:begin/end -->` 块；对 spec/plan 的纠错以 suggested edit 回流。
- **Why**：保持研究（evidence）与创作（spec/plan）分离，diff 干净。
- **Trade-off**：纠错多一步人工应用。
- **Transferability to our project**：**部分迁移**。对应我们「Wiki/Report 是 Evidence 的投影」+「Review 结论写回 State」。但我们的"产品工件"是 Evidence Store 与 Wiki，harness 自己应拥有 Evidence Store 的写权（它才是 runtime），而 Report 由投影生成。

---

## What We Should Borrow

> 每一条都按「解决什么问题 → 为什么有效 → 我们是否存在同样的问题 → 是否有更简单的实现」论证。

1. **六类状态的外置分离（budget/candidates/curated/evidence/verification/observations）**
   - 问题：长程调研的 context drift、重复搜索、证据与结论脱节。
   - 为什么有效：状态幸存于任何 session 死亡，可审计、可共享。
   - 我们是否有同样的问题：**有**——这就是 PROJECT_VISION §3.1 Context Drift 的核心。
   - 更简单的实现：暂无更简单的等价物；但我们改用类型化文件（JSON/JSONL+schema），并把"observation"从通用日志换成可追踪的 action 记录。

2. **Bounded slice 渲染（Context Renderer）**
   - 问题：rich state 重新撑爆 context，外置失效。
   - 为什么有效：花费随文件规模而非对话长度增长。
   - 我们是否有同样的问题：**有**（P21 Context Is a View of State）。
   - 更简单的实现：无更简单等价物；但我们要按 Action 渲染不同 slice（spec-kit 是固定 slice）。

3. **Budget 台账 + 明确 stop conditions**
   - 问题：bounded autonomy，防无限运行、防 premature stop。
   - 为什么有效：资源数字约束 + 条件判质量。
   - 我们是否有同样的问题：**有**（§31.4 Bounded Autonomy）。
   - 更简单的实现：无；但记账必须由 Python 原子执行，不能靠 prompt 诚实。

4. **Candidate → Curated → Evidence 分层**
   - 问题：paper ≠ evidence，弱引用/错误引用。
   - 为什么有效：发现、保留、证明三层各答一问。
   - 我们是否有同样的问题：**有**（P8）。
   - 更简单的实现：无更简单等价物；curated 语义改为 gap 键控。

5. **对抗式验证 + 持久 verdict + 记录死路**
   - 问题：self-grading、confirmation bias、重复推导旧错误。
   - 为什么有效：验证回主源、dead end 留档。
   - 我们是否有同样的问题：**有**（P11/P12）。
   - 更简单的实现：无；且我们要用 fresh-context reviewer 实现真正的独立，而不是同一 agent 的对抗性 prompt。

6. **Resume = 从状态重建，而非恢复对话**
   - 问题：session 终止后无法继续。
   - 为什么有效：所有重要知识在学到瞬间已落盘。
   - 我们是否有同样的问题：**有**（P3）。
   - 更简单的实现：无；等价于我们 P22 的 status/next 接口。

7. **「Evidence First」的报告生成：requirement → evidence 覆盖分类**
   - 问题：Citation Drift，报告由模糊记忆驱动。
   - 为什么有效：报告的每一行必须引用真实 evidence ID；没支撑的显式标 uncovered。
   - 我们是否有同样的问题：**有**（§3.5 Citation Drift）。
   - 更简单的实现：语义相同；把"spec requirement"换成"Research Question / Gap"，用 covered/partial/missing 分类。

---

## What We Should Not Borrow

1. **Prompt-only 执行模式（"agent is the interpreter"、零可执行代码）** —— 这是最不该迁移的一条。spec-kit 的 enforcement 完全是 prompt discipline，靠"规则机械 + diff 可见"兜底（他们自称 honest caveat）。我们的 ADR 明确 Python Harness 必须 *enforce*（schema validation、atomic write、dedup、budget 记账、evidence 引用校验都是代码），不能靠模型遵守 prompt。
2. **Spec Kit 集成机制**（feature 目录/branch 映射、extension.yml、hooks、`speckit.*` 命令体系）—— 我们不在 Spec Kit 之上构建。
3. **全 Markdown 的 runtime state 表示** —— 无 schema、无 atomic、invariant 靠约定。我们 V1 用 JSON/JSONL 承载可校验状态。
4. **预算靠 agent 在 markdown 表里手动计数** —— 我们由 Python 原子扣减，防止绕过 ledger。
5. **四个动词的字面集合（SEARCH/INSPECT/CURATE/STOP）与"curate 不耗预算"** —— 决策面收窄的原则要保留，但我们的 action 集合是搜索/阅读/follow-reference/抽取证据/gap 分析等科研动作，预算语义也不同。
6. **importance-tag + eviction cap 的 curated 语义** —— "25 条上限、最低重要度驱逐"是通用信息筛选逻辑，对 open-ended 文献调研过强/过粗；我们的 curated evidence 应按 gap/RQ 组织，cap 语义待定。
7. **marginal-gain stop rule 的"新 curated 行"信号** —— 科研中一次有价值的深读可能不立即产出 curated 行；stop 信号应基于 gap 覆盖条件。
8. **`report` = spec requirement coverage 表** —— 字面机制不迁移（我们不是 feature spec）；只迁移"报告由 evidence 驱动"的语义。

---

## Conflicts with PROJECT_VISION

1. **最根本的冲突：enforcement 机制。** spec-kit 是纯 prompt 协议；我们的 VISION（§3.2、§5、P5、ADR）要求 Python Harness 以确定性机制 *enforce* bookkeeping。**借其状态模型与渲染思想，不借其执行机制。** 这恰好印证了我们 VISION 里"Python 负责 deterministic control"的必要性——参考项目已示范了纯 prompt 模式的局限。
2. **它不区分 Agent Runtime 与 Research Runtime**：因为它的"runtime"就是用户的 agent，没有第二层。所以它无法回答"两层 runtime 如何分工"——这个边界我们必须自己设计（我们的 ADR 已定，它只是旁证）。
3. **curated 的 importance 标签 vs 我们的 gap 键控**：它的保留语义是"重要度排序 + 上限驱逐"，偏信息筛选；我们的 Evidence 必须能回答"支持/反驳/限定哪个 RQ 或 Gap"（P10 Stance）。不冲突，但语义要换。
4. **stop 信号 vs 我们的 Review Gate**：它用 budget + marginal-gain + mission-answered 的代理条件收尾；我们要求独立 Review Gate 语义判定 PASS/CONTINUE/UNCERTAIN。它没有 fresh-context reviewer 概念——这是我们从它缺失处提炼的增强。
5. **report 载体**：它写 `research.md` coverage 表；我们产出 Survey Report + Wiki 两类投影，但都遵循"Evidence First, Synthesis Second"，方向一致。

---

## Questions Still Open

1. **纯 prompt 兜底是否足够？** spec-kit 用"diff 可见性"作为最强的 prompt-only 保证。我们能否定义"最小强制集"——哪些 invariants 必须 Python 硬强制，哪些允许由 Claude 负责并靠人工 Review 兜底？(对 ADR 的落地很关键)
2. **marginal-gain 类 stop 信号能否适配科研？** 若 yield 信号改为"gap 覆盖变化"，会不会漏掉"深读改变理解但未立即落证据"的有价值迭代？是否需要独立于证据产出的理解变化信号？
3. **context_tokens cap 的测量**：spec-kit 是软目标无真实测量。我们的 Context Renderer 如何**真实计量**渲染的 token 数并硬限制？
4. **locator 的鲁棒性**："能扛住小改动"的 locator 在论文场景（section/页码/引文锚点）如何定义？PDF 解析后的 locator 漂移怎么办？
5. **多 mission/多 RQ 共享一份 harness**：spec-kit 允许 append mission。我们的多 RQ 调研是该共享一份 state 还是按 RQ 隔离？shared state 下 gap 归属会变复杂。
6. **curated 上限与 eviction 是否该存在**：文献调研的 evidence 池该不该有 cap？cap 会否与"hard evidence"目标冲突？

---

## Candidate ADRs Influenced by This Project

1. **ADR：State 表示为类型化文件集合（JSON/JSONL），按关注点拆分**——借鉴六文件分离，但用 schema 校验，而非 markdown。由 Decision 1/2 支撑。
2. **ADR：Context Renderer 是头等组件**——按 Action 渲染 bounded slice，`status`/`next` 接口暴露状态；token 真实计量。由 Decision 4/7 与 P21/P22 共同支撑。
3. **ADR：Budget 与 Stop Condition 是 Python 强制的类型化台账**——资源数字约束、gap 覆盖条件判质量、原子记账。由 Decision 5 支撑，反其 prompt-only 而行。
4. **ADR：Evidence 模型 {paper_id, section, locator, excerpt, stance} + Verification 记录 {claim, verdict, method, confidence}**——指针而非内容、可追溯、可校验。由 Decision 3/6 支撑。
5. **ADR：Review Gate 为 fresh-context 独立语义检查点**，Refutation/Uncertain 写回 State 并记录死路。由 Decision 6 与 P11/P12 支撑——spec-kit 用"对抗性 prompt"近似独立，我们升级为真独立。

---

## 一句话结论

> spec-kit-harness 证明了**"状态外置 + 分层 evidence + 预算化循环 + 可恢复会话"**这套形态可行且收益清晰；
> 但它用纯 prompt 承担 enforcement，正是我们 VISION 决定用 Python 硬强制去替代的那个薄弱环节。
> 借其**状态模型与渲染思想**，不借其**执行机制**。
