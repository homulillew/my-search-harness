# Study Note: homulillew/search-harness（old-search-harness）

> 本 Note 是**对我们自己的第一次实现**的架构实验复盘。基线 = spec-kit-harness Study
> Note 沉淀出的克制 baseline：*Simple loop, Rich state, Policy/Mechanism 分离*。
> 它同时是 Positive Reference（实现了大量真实工程能力）与 Negative Reference（真实暴露
> 了第一版复杂度如何增长），因此本 Note 的核心问题不是「旧项目有哪些模块」，而是——
>
> **哪些本来应该属于 rich state 的复杂度，被错误变成了 control-flow complexity？**

## Snapshot

```
Repository: https://github.com/homulillew/search-harness
Commit:     4584c315796ebd198deb3639005a54c17a4c322e（v0 initial import）
Study date: 2026-08-08
License:    MIT（open-claude-research/；claude-research-pack/）
```

仓库内**同时存在两套并行实现**，这本身就是一个重要实验结论：

| 实现 | 形态 | 控制流放在哪 |
|---|---|---|
| `claude-research-pack/` | Claude Code Skill + 约 40 个脚本 | **prompt/SKILL 文档里**（S1.1–S5.9、dispatch 词表、回退边） |
| `open-claude-research/` | Python 包 + `orchestrator.py`（3638 行） | **Python 状态机里**（14 个生命周期 phase + 子循环） |

两套实现表达的是**同一个研究流程**，却把控制流分别塞进了「提示词结构」和「状态机代码」——
这正是本 Study 要拆解的一体两面。

---

## Why We Studied It

第一份 Study（spec-kit-harness）给了我们一个克制的 baseline：

```text
1 个循环（RESEARCH）
4 个动词（SEARCH / INSPECT / CURATE / STOP）
约 6 个 state 文件
所有研究语义都沉淀在 state 里，控制流极薄
```

old-search-harness 的价值在于回答：**我们第一次实现时，究竟在哪几个地方越过了这条
baseline，complexity 又是怎样一步步长出来的？**

回答分两层：

1. **它证明了我们 ADR 的核心信念**：确定性控制面 + 显式语义检查点确实可行——
   `evidence.py`、run lock、原子写、checkpoint 恢复、append-only 事件账本都是
   spec-kit 没有（因为 spec-kit 零代码）而旧项目真实跑通的工程能力。
2. **它同时演示了越界的方向**：当控制面开始「代做研究语义决策」时（用加权标量
   `sufficiency_score` 决定 continue/stop、把每个研究动作升级成 lifecycle phase、
   造出三四个互相嵌套的循环），复杂度从「状态丰富」退化成「控制流爆炸」。

本 Note 的主要篇幅用于第 2 层——它是我们未来 Architecture 阶段要避免的坑位清单。

---

## Architecture in One Diagram

```text
                              ┌──────────────────────────────────────────┐
                              │  两套实现：同一个流程的两种控制流投放方式     │
                              └──────────────────────────────────────────┘

 claude-research-pack（提示词即状态机）                 open-claude-research（Python 状态机）
 ┌──────────────────────────────────────┐              ┌──────────────────────────────────────┐
 │ SKILL.md = 用户说明 + 状态图 + 异常    │              │ next-action CLI                       │
 │  处理 + 调度协议（194 行）             │              │   │ 每步返回一个语义动作或推进确定性阶段 │
 │ S1 意图/规划   S2 检索  S3 理解闭环    │              │   ▼                                  │
 │ S4 报告  S5 校验/收尾                 │              │ state.json + run_manifest +          │
 │ 主路径 / 降级B / 兼容C 三条回退边      │              │ config.snapshot + events.jsonl        │
 │ dispatch 词表：decide/verify_report/  │              │ + versions/vNNN-<phase>.json          │
 │   done_check 各自回跳 S2/S3/S4        │              │   │                                  │
 │ 13 个 loop_engineer 脚本（跨 run 元层）│              │   ▼  状态机 phase（约 14 个）          │
 └──────────────────────────────────────┘              │ awaiting_scope → discover →          │
                                                        │ awaiting_citation_seed_selection →   │
                                                        │ expand_citations → read →            │
                                                        │ awaiting_evidence → awaiting_        │
                                                        │ reflection → prepare_report →        │
                                                        │ awaiting_report → awaiting_citation_ │
                                                        │ audit → finalize → complete          │
                                                        │   └─ 子循环1：reflect/search (0..N)   │
                                                        │   └─ 子循环2：revise (0..N)           │
                                                        │   └─ 元循环：retrospective/loop-engineer│
                                                        │   └─ 平行通道：GitHub 项目搜索+证据卡  │
                                                        │ 交付：双层报告 + citation_map +       │
                                                        │       审计附录 + hash delivery        │
                                                        └──────────────────────────────────────┘

                          ▲ spec-kit baseline（对照）
                          │ 1 循环 · 4 动词 · 6 state 文件
                          │ 所有研究语义都在 state，控制流极薄
```

两套实现越界的方向互为镜像：pack 把控制流塞进**提示词**，OCR 把控制流塞进**代码**。
spec-kit 夹在中间——控制流薄，state 丰富，动词少。

---

## Core Concepts

1. **确定性控制面 + 显式语义检查点**（OCR 的核心模型）：`next-action` 一次只返回一个需要
   Claude Code 处理的语义动作；纯确定性阶段（discover/read/finalize）一次调用内自动穿过。
   这**就是**我们 PROJECT_VISION 的 ADR 形态，OCR 是第一版实证。
2. **研究闭环 / 报告闭环 / 演进闭环**：三个「闭环」——研究（证据够不够）、报告（结论可信、
   读者可读）、演进（同类失败不再发生）。三个循环互相嵌套，是「多个 competing loop」的源头。
3. **精确证据链**：`论断 → Evidence → Paper → Exact Section → Verbatim Excerpt → Stance/Boundary`，
   验证器拒绝不存在的论文、模糊章节、无法在缓存原文找到的摘录。
4. **非共识是一等产物**：三分类（direct_conflict 直接冲突 / scope_dependent 条件依赖 /
   evidence_gap 证据缺口）+ 六字段（主张、支持证据、反方证据、受影响论文、重要性、待解决问题）。
5. **rich state 的原始素材已存在，却未主导决策**：coverage 字段本身是 typed
   （covered=1.0 / partial=0.5 / missing=0.0），事件账本 append-only——但这些 rich state
   最终都被折叠进一个加权标量 `sufficiency_score` 去驱动循环。**素材对了，决策层错了。**
6. **论文与开源项目分开评价**：论文按主题契合/方法严谨/实验/失败分析等评分；GitHub 项目按
   搜索可观察性/运行入口/评测一致性评分。两套 rubric + 两套预算 + 两条并行发现管线。
7. **演进闭环 / LoopEngineer**：从事件、错误、覆盖与修订审计中提取改进候选，标
   `awaiting_human_approval`，不在活跃 run 中自动应用。

---

## Important Files

**open-claude-research（第一顺位）**

| 文件 | 角色 | 行数/关键点 |
|---|---|---|
| `src/open_claude_research/orchestrator.py` | next-action 状态机 | **3638 行**；每 phase 一个 handler 分支；内含 `_calculate_sufficiency`、`_consume_*` 系列 |
| `src/open_claude_research/evidence.py` | 证据账本 | locator/excerpt/stance 校验、非共识六字段门禁 |
| `src/open_claude_research/quality.py` | 机械审计 | `mechanical_compliance_score`（自证从 `quality_score` 改名）；claim 引用覆盖 ≥90%；严格章节匹配 |
| `src/open_claude_research/storage.py` | 原子写/版本/锁 | append-only 事件、内容哈希、`versions/vNNN-<phase>.json`、跨进程 run lock |
| `src/open_claude_research/models.py` | state 模型 | phase/iteration/revision/budget/evidence_id/非共识类别 |
| `src/open_claude_research/report_contract.py` | 报告契约 | required/optional/forbidden sections、作者引文→读者引文确定性渲染、内部 ID 泄漏检查 |
| `src/open_claude_research/adapters/deepxiv.py` | 检索适配器 | 薄封装、fail-closed envelope 校验（错误 envelope ≠ 空结果） |
| `src/open_claude_research/config/default.yaml` | 预算 | `api_budget: 400`、`max_iterations: 6`、`max_report_revisions: 10`、引用扩展/GitHub 各自预算 |
| `src/open_claude_research/config/quality.yaml` | 阈值 | `sufficiency.threshold: 0.82`、`primary_threshold: 0.65`、dimension 阈值 |

**claude-research-pack（第二顺位，prompt 状态机形态）**

| 文件 | 角色 |
|---|---|
| `.claude/skills/ai-literature-research/SKILL.md` | 194 行；S1.1–S5.9 流程 + dispatch 词表 + 三条回退边 |
| `src/claude_reseach/loop_engineer/` | 13 个脚本：analyze/miners/patch_proposer/validator/evaluator/apply_patch/wiki_* |
| `scripts/`（skill 内） | 约 30 个：plan/observe/decide/compare/verify/summarize/report/export_pack… |

**文档（自我诊断，价值极高）**

| 文档 | 贡献 |
|---|---|
| `docs/ARCHITECTURE-COMPARISON-WITH-CLAUDE-RESEACH.md` | 对两套实现的自审：quality_score 误标、orchestrator>3000 行、推荐 4-plane 目标架构 |
| `docs/LEGACY-HARNESS-RETROSPECTIVE.md` | 旧 harness「研究过程没成为可检验工程状态」的缺口复盘；fixture 优先于扩 skill |
| `docs/PROJECT_OVERVIEW-CONDENSED.md` | 最新运行实况：251 候选 / 19 深读 / 53 原子证据 / 充分性 0.69（未过门） |

---

## Key Data Flow

```text
User topic
   │  next-action CLI
   ▼
state.json ← 每次转移原子更新；events.jsonl 只追加；versions/vNNN-<phase>.json 快照
   │
   ├─ 确定性阶段（一次调用穿过）→ DeepXiv 检索 / 引用扩展 / 渐进阅读 / 证据校验
   ├─ 语义检查点（等 Claude）→ scope 编译 / 种子选择 / 证据抽取+比较+非共识 / 缺口反思
   │                             / 报告撰写 / 对抗审计 / 复盘
   │              └── Claude 写一个 schema-bound artifact → next-action 校验后推进
   ▼
证据充分性门（sufficiency_score + hard gates）
   ├─ sufficient → prepare_report
   ├─ budget/迭代耗尽 → incomplete=true，仍进入 prepare_report（如实标记部分完成）
   └─ 否 → 回到 awaiting_reflection（补搜，0..N）
   ▼
报告闭环：作者版 → 机械审计 → 语义引文审计 → 修订（0..N）→ 读者版
   ▼
交付：final_report.md + final_report_authoring.md + citation_map.json
      + audit_appendix + 引用图 + SHA-256 manifest（原子替换）
```

关键观察：数据流**本体是健康的**（state 外置、事件账本、检查点、双层交付）。问题不在
「有没有 rich state」，而在**驱动循环的是谁**——一个加权标量 + 一组子循环，而不是
typed state 本身。

---

## Key State Model

**phase（实际枚举来自 orchestrator.py 分支）**：

```text
awaiting_scope → discover → awaiting_citation_seed_selection → expand_citations
→ read → awaiting_evidence → awaiting_reflection → prepare_report → awaiting_report
→ awaiting_citation_audit → finalize → complete
（另：blocked_integrity / blocked_insufficient_evidence 两个阻塞态）
```

**state.json 携带的字段**：phase、iteration、revision、budget、retrieval_history、
stop_reason、sufficiency_score、sufficient、incomplete、accepted_evidence_hashes…

**版本与审计**：`versions/vNNN-<phase>.json` 不可变快照；`audits/sufficiency-iNN.json`、
`audits/evidence-iNN.json`；事件账本 `events.jsonl`（evidence_accepted / evidence_rejected /
source_integrity_failed…）。

**对照 baseline**：spec-kit 只有 6 个 state 文件 + 4 个动词；OCR 有约 14 个 phase、
10+ 种 artifact、3 个嵌套子循环、2 套并行发现管线。状态本身并不比 spec-kit「更 rich」，
而是被**切碎成互相引用的 artifact 群**——rich state 与 control-flow 的比例失衡。

---

## Design Decisions Worth Learning

### 前置：complexity 是怎么一步步长出来的（growth path）

```text
Step 0  单次 LLM 调用（检索→一次性报告）——旧 harness 缺口
        · 遗漏不可测、claim 无法回原文、失败无法复现
Step 1  pack 把流程拆成 S1–S5——动作有了编号（S2.1/S3.9/S5.3…）
        · 提示词开始承担「程序」职责
Step 2  每个 stage 长出子步骤 + 回退边（降级B / 兼容C / 回边 S2.1）
        · dispatch 词表出现，控制流正式进入 SKILL 文档
Step 3  脚本膨胀到约 40 个承担确定性工作
        · 但「谁先谁后」仍靠模型读 SKILL.md 解释 → 脆弱
Step 4  反作用力：OCR 把编排搬进 Python next-action + phase 机器
        · 确定性被 enforce 了，但研究方法论本身被硬编码成状态
Step 5  每个 phase 配 artifact + validator + budget + event
        · 子循环（reflect/search、revise）、元循环（LoopEngineer）、
          平行通道（GitHub）逐个加上 → orchestrator 3638 行
Step 6  结果：循环不再 simple；state 被切碎成 10+ 个 artifact；
        · spec-kit 用 4 动词 + 6 文件表达的流程，OCR 用 14 phase + 20 文件 + 3638 行
```

**生长机制只有一句话**：*每个新能力都被加成了控制流（新 phase/新循环/新回边），而不是
被加成了 state（新字段/新文件/新记录类型）。* spec-kit 的反向动作是：新能力 = state 里
新增一种记录，由既有动词消费。

---

### Decision 1 — 动作被升级成 Lifecycle Phase（核心病灶）

**Problem**：补搜、报告质量判断、引用扩展、自我改进——这些在 spec-kit 里都是「动作」
（Action）或「检查点」，在 OCR 里全被升级成了生命周期 phase，各有专属 phase handler。

**Design**：`reflect/search (0..N)`、`revise (0..N)` 两个子循环 + `awaiting_reflection` /
`awaiting_report` / `awaiting_citation_audit` 等 phase；补搜循环还要额外引入
`_calculate_sufficiency` 做 continue/stop 判断。

**Why**：在 Step 4 的「确定性化」浪潮里，给每个语义能力一个 phase + 一个 artifact +
一个 validator，看起来是最彻底地把控制权收归 Python。

**Trade-off**：收回了确定性，却把研究语义决策（「证据够不够、要不要补搜」）也收进了
机制层。phase 一多，`next_action` 就得在每个分支处理「能否推进、预算、子循环计数」，
orchestrator 因此单文件膨胀到 3638 行（旧项目自己的 P1 就是「拆分 orchestrator phase
handler」）。

**Transferability**：直接反面教材。我们的 lifecycle 沿用 spec-kit 的少数几个 phase
（PLAN / RESEARCH / REVIEW / SYNTHESIZE / DONE）；研究动作一律是 Action，由
Claude 在统一循环里发起，Python 只提供「执行动作 + 校验状态 + 记账」的原子操作。
**它有更简单的实现**：spec-kit 的 4 个动词 + 1 个循环已经证明了这一点。

---

### Decision 2 — typed coverage 已被采集，却折叠成加权标量 sufficiency_score

**Problem**：补搜/停止判断需要一个「证据够不够」的答案。

**Design**：`_calculate_sufficiency` 把 5 个异构分量（dimension_coverage 0.35 /
primary_papers 0.15 / deep_read 0.15 / evidence 0.20 / non_consensus 0.15）加权求和，
减去 high-gap 惩罚，对阈值 0.82 判充分；同时保留一组 hard gates
（primary≥6 / deep_read≥5 / evidence≥12 / non_consensus 反向支撑≥2）。

**Why**：希望有一个可解释、可审计的「充分性数字」写进 state 与报告。

**Trade-off**：致命点在于——coverage 字段**本来就是 typed 的**（covered=1.0 /
partial=0.5 / missing=0.0，per dimension），这是正确的 rich state；但停止决策却读的是
「0.35×覆盖率 + 0.15×非共识 + …」这个标量。加权平均允许 5 类异构事物互相补偿，
0.82 这个阈值在语料变化时立即失准（0.69 那次运行因 primary=0 未过门，事后不得不
「用固定多主题样本校准」，而不是直接降阈值）。hard gates 是本 design 的「非补偿性」
补丁——但真正的教训是：**根本不该把 typed coverage 压成标量**。

**Transferability**：P13/P14 的直接证据。停止决策 = 每个关键标准单独判
（covered/partial/missing，非补偿）+ 显式 unresolved 清单 + budget stop；
**不做加权平均，不产出 sufficiency_score**。**更简单的实现**：spec-kit 的 typed
stop conditions（budget 耗尽 / 边际增益窗口 / mission 关键项已验证）已经存在。

---

### Decision 3 — 报告质量判断 = audit→revise 子循环，而不是单个检查点

**Problem**：「报告是否合格」需要一个可审计的回答。

**Design**：机械审计（quality.py，`mechanical_compliance_score`）→ 语义引文审计 → 针对性
修订（0..N）→ 再审计；`state.revision` 计数 + `max_report_revisions: 10` 兜底。

**Why**：把「报告不够好」变成「还能更好」的迭代，在报告闭环里再套一层状态机。

**Trade-off**：这是第二个嵌套子循环（第一个是 reflect/search）。审计本身的结论（typed
issues、critical failures）是 rich state 的正确素材，但「审计→改→再审计」的回边是纯
control-flow——它把 REVIEW 从一次语义检查点膨胀成一整个子状态机。

**Transferability**：P12 的直接证据。Review = 单个语义检查点，产出 typed verdicts
（CONTINUE / UNCERTAIN / PASS / explicit unresolved），一次决议；不造 audit→revise
子循环。**更简单的实现**：spec-kit 的 `/verify` 对抗式验证 + 一次回写。

---

### Decision 4 — 引用扩展从「一个 Action」升级成「两个 phase + 一个 artifact」

**Problem**：单次 DeepXiv 检索的召回不够，需要顺着引用再扩展。

**Design**：`citation-seed-select` / `citation-expand` 两个 phase + `citation-graph.json`
artifact（深度 1 的后向 References 解析 + 前向 RoC 检索确认身份）；graph 明示 retrieval
mode / confidence / 覆盖限制（因为 DeepXiv 没有穷尽式 citation-list API）。

**Why**：引用关系值得被固化成一张可审计的图。

**Trade-off**：一个「顺着引用再搜一次」的动作，变成了一对 phase + 一个 artifact + 一段
适配器代码。graph 的权威性受限于 API（文档不得不承认非穷尽），说明它的状态价值
（关系记录）远大于它的控制流价值（一个特殊 phase）。

**Transferability**：follow-reference 在 spec-kit 里就是 SEARCH 动词的一种查询类型。
我们沿用：**引用扩展是一个 Action**，产出「新候选」进 candidates 池；不设专属 phase，
不建 graph artifact。**更简单的实现**：spec-kit 已验证。

---

### Decision 5 — LoopEngineer / retrospective：元循环叠在研究循环之上

**Problem**：「同类失败下次不再发生」需要一个自学习机制。

**Design**：`retrospective → complete` 作为生命周期 phase + `loop_engineer.py`
（从事件/错误/覆盖/修订审计提取候选，标 `awaiting_human_approval`）+ `loop-analyze`
CLI（不推进 phase 但写候选 artifact）。pack 版本更重：13 个 loop_engineer 脚本
（miners / patch_proposer / validator / evaluator / apply_patch / wiki_*）。

**Why**：复盘是个好习惯；把复盘自动化看似顺理成章。

**Trade-off**：这是第三个循环（演进闭环），与研究循环竞争注意力与 artifact 空间。
候选从不自动应用（诚实），于是它实际贡献的是「候选分析」而非「改进」——用一整层
机制换一个可以在 fixture/测试/config 里更便宜地达到的目标。

**Transferability**：与我们 PROJECT_VISION 的非目标（自修改 Harness）直接冲突。
失败沉淀走 **fixture + regression test + config**（旧项目 retrospective 自己都承认：
「先补足 baseline 与 fixture，而非继续扩写 skill」），**不建元循环**。

---

### Decision 6 — 真正值得保留的工程 backbone（Positive 面）

**Problem**：确定性控制面需要状态安全（并发、崩溃、审计）。

**Design**：原子写 + append-only 事件账本 + `versions/vNNN-<phase>.json` 不可变快照 +
跨进程 run lock（单写者，竞争者非阻塞失败）+ config.snapshot 约束运行身份 + 恢复以
state checkpoint 为准而非重读用户提示。

**Why**：让「研究过程成为可检验的工程状态」——这是旧 harness 缺口（一次性 LLM 调用）
的正面答案，spec-kit 因零代码而完全没有。

**Trade-off**：方向全对，但**规模过度**——「version 一切 artifact + hash-chain 一切 +
delivery secret 扫描」对研究场景是超配（对应 REFERENCE_PROJECTS 的
「premature hash/audit complexity」警告）。区分：run lock / 原子写 / 事件账本 / 检查点
是必须的；每个生成 artifact 都做不可变版本索引，不是。

**Transferability**：全盘采纳**原则**（P3 / P5 的实证），裁掉**规模**。我们的 Python
Runtime 提供：单写锁、原子写、append-only 事件账本、resume 检查点；只对会变化的核心
状态（state、证据账本）做版本，不对每次生成物做。

---

### Decision 7 — 精确证据链 + 非共识一等产物（第二块 Positive）

**Problem**：综述的两大可信度缺口——claim 无法回到原文、分歧被模糊化。

**Design**：exact-section locator + verbatim excerpt + stance 的原子证据，验证器拒绝
「缓存原文里找不到的摘录」；非共识三分类（直接冲突/条件依赖/证据缺口）+ 六字段。

**Why**：比 spec-kit 的紧凑指针（source + locator + ≤25 词 excerpt）更强的证据不变量；
非共识是论文调研里最高价值的产出（spec-kit 的 importance 标签替代不了）。

**Trade-off**：verbatim 校验要求缓存全文 + 校验代码，成本高于指针式证据。

**Transferability**：这是旧项目里**我们应当整体迁移**的部分——P8 / P10 已有对应原则，
旧项目给出了可落地的 schema。候选 ADR：evidence 采用 exact-section locator + 可校验
excerpt + stance；非共识（三分类 + 六字段）作为一等 state 记录。

---

### Decision 8 — 双层报告 + 确定性数字引文（第三块 Positive，延后）

**Problem**：内部证据 ID（Pxxx/Gxxx）会污染读者文本；引用无法还原到精确章节。

**Design**：作者版 `[@P001#Exact Section]` → 读者版紧凑数字引文 + `citation_map.json`
可逆还原 + 内部 ID 泄漏检查；引用绑定到它支持的最小论断。

**Why**：把「写作时内部 ID」与「读者可追踪」解耦，且是确定性渲染（不是模型自由发挥）。

**Trade-off**：额外一层 artifact（citation_map）+ 渲染代码；属于 SYNTHESIZE 后期能力。

**Transferability**：值得借鉴，但**延后到报告阶段**（我们的 P15–17 Wiki 是 Projection，
报告同理是 state 的 Projection，不是独立真相源）。第一阶段循环不必做。

---

## What We Should Borrow

1. **证据账本 + 非共识一等产物**（Decision 7）：exact-section locator + verbatim excerpt +
   stance + 三分类六字段。P8/P10 的直接可落地 schema。spec-kit 只有指针式证据，
   OCR 把证据链做成了硬门禁——这是旧项目对 spec-kit baseline 的**正向越界**。
2. **工程 backbone 原则**（Decision 6）：单写锁、原子写、append-only 事件账本、
   checkpoint resume、config.snapshot。P3/P5 的实证，证明「Python 真能 enforce 这些」。
3. **Fail-closed 适配器校验**：DeepXiv 即使 HTTP 200 也要检查嵌套 envelope 的
   status/error，错误 envelope ≠ 空搜索。我们的 adapter 层直接沿用。
4. **恢复以 state 为准，而非重读用户提示**：P3 的完整表述，OCR 已实现。
5. **自审文档纪律**：`ARCHITECTURE-COMPARISON-WITH-CLAUDE-RESEACH.md` 承认 quality_score
   误标、orchestrator 过大——这种诚实复盘是我们自己的定期 retro 要仿效的实践。
6. **配置外置**：预算/阈值全部进 yaml（default.yaml / quality.yaml），不硬编码。
   我们保留「配置外置」，但**拒绝标量阈值**（见下）。

## What We Should Not Borrow

1. **Phase 爆炸**（Decision 1）：动作被升级成 lifecycle phase。循环必须保持 spec-kit 的
   少数 phase；动作进 Action 清单，不进状态机。
2. **巨型 orchestrator / phase-handler 调度**：3638 行单文件状态机。我们的 Python =
   薄确定性动作 + 状态校验，不是「研究流程的解释器」。
3. **加权标量 sufficiency_score**（Decision 2）：即使有 hard gates，加权平均本身就是
   false precision（P13/P14 违反）。typed criteria + 非补偿关键标准取代。
4. **audit→revise 子循环**（Decision 3）：报告质量 = 单个 REVIEW 语义检查点。
5. **引用扩展作为 phase + graph artifact**（Decision 4）：follow-reference = Action。
6. **LoopEngineer / retrospective 元循环**（Decision 5）：与我们非目标冲突；
   失败进 fixture/测试/config。
7. **强制 GitHub 项目通道**：`linked_repo_budget / inspection_budget / 项目 rubric`
   与检索韧性逻辑（DeepXiv 失败不取消 GitHub）——一整套并行管线。
   GitHub 项目搜索可以是**后续的可选 Action**，不是生命周期强制通道。
8. **Version 一切 + hash-chain 一切**：只版本会变化的核心状态；不版本每次生成物。
9. **SKILL 即状态机**（S1.1–S5.9 + dispatch 词表 + 回退边）：prompt discipline 超过
   几个动词就崩；我们的 enforce 在 Python，prompt 保持精简。
10. **同一流程两套并行实现**：pack + OCR 并存 = 同一工作流的两份维护。
    我们只有一种心智模型：Claude 驱动循环，Python enforce 状态与动作。

## Conflicts with PROJECT_VISION

1. **P13/P14（Criteria over magic scores / 非补偿关键标准）↔ 加权标量 + 阈值**：旧项目
   从 `quality_score: 100.0`（误标）改名为 `mechanical_compliance_score`（承认它只是
   机械合规分），却仍保留 `sufficiency_score` 这个研究层面的标量。加权平均让
   「覆盖率不够、非共识来凑」成为可能——正是 P14 要禁止的补偿性。
2. **P6（Policy/Mechanism 分离）↔ mechanism 代做研究决策**：sufficiency gate 决定
   continue/stop，是**机制层在做政策决策**。Python 应 enforce 结构（输入完整、
   状态合法、证据存在、预算未超），不应回答「证据够不够」——那是 Claude 的语义判断，
   以 typed 标准 + 显式 unresolved 呈现。
3. **非目标（自修改 Harness）↔ LoopEngineer**：直接冲突。
4. **P15–17（Wiki 是 Projection）↔ 双层报告 + citation_map + 审计附录**：报告作为
   state 的 projection 是对的；但旧项目把交付做成了「独立权威 artifact 群」，
   与我们「报告是投影、可重建」的取向有张力。报告仍应可重建，而非第二真相源。
5. **scope（论文优先）↔ 强制 GitHub 通道**：GitHub 项目搜索应延后为可选 Action。

## Questions Still Open

1. **不用标量，如何「判充分」**？typed per-dimension coverage + 非补偿关键标准 +
   budget stop + 显式 unresolved 清单——这套组合是否足以支撑 continue/stop，而不需要
   任何汇总数字？这是要写进 ADR 的最尖锐问题。（候选答案：需要，且 spec-kit 已示范
   stop conditions 是 typed 的。）
2. **非共识做到多深**？三分类 + 六字段是旧项目最高价值产物，但成本不低。最小可行：
   Evidence stance（supporting/contradicting/qualifying）+ 每 gap 一个 unresolved 记录
   是否就够？还是六字段版本从一开始就值得？倾向后者，但留待 Architecture 阶段定。
3. **verbatim excerpt 校验是否第一版就要**？「摘录必须能在缓存原文中逐字找到」比
   spec-kit 的指针强，但要全文缓存 + 校验代码。第一版证据是「指针」还是「指针+可校验
   摘录」？
4. **双层报告何时做**？确定为 SYNTHESIZE 后期能力，但第一阶段是否先做
   「作者版 + ID 不外泄」的最简形态？
5. **GitHub 通道如何回归**？旧项目证明它可行但昂贵（29 个项目没救活 0.69 那次运行）。
   作为可选 Action 的形态与触发条件，留到后续 reference（superloopy）再对照。

## Candidate ADRs Influenced by This Project

1. **ADR：Lifecycle 用少数 phase（PLAN/RESEARCH/REVIEW/SYNTHESIZE/DONE），研究动作一律是
   Action；禁止把动作升级成 phase。**（Decision 1、4）
2. **ADR：证据充分性用 typed criteria + 非补偿关键标准 + budget stop + 显式 unresolved；
   禁止加权标量 score。**（Decision 2）
3. **ADR：Review 是单个语义检查点（typed verdicts），不设 audit→revise 子循环。**
   （Decision 3）
4. **ADR：Evidence 采用 exact-section locator + 可校验 excerpt + stance；非共识（三分类 +
   六字段）为一等 state 记录。**（Decision 7）
5. **ADR：Python Harness 提供确定性 actions + 单写锁 + 原子写 + 事件账本 + checkpoint；
   不解释研究语义，机制层不做政策决策。**（Decision 6、P6）
6. **ADR：系统自改进为非目标；失败沉淀进 fixture/regression test/config。**（Decision 5）
7. **ADR：报告是 state 的 projection（可重建），不是独立权威 artifact 群。**（P15–17，
   Decision 8 的边界）

## 一句话结论

old-search-harness 证明了两件事：**确定性控制面 + 显式语义检查点可行且值得**（证据链、
非共识、run lock、事件账本都是真的）；同时**当新能力被不断加进控制流而不是加进 state 时，
复杂度会从「状态丰富」退化成「控制流爆炸」**——14 个 phase、3638 行 orchestrator、
三个嵌套循环、10+ 个互相引用的 artifact，换来的却是 spec-kit 用 4 动词 + 6 文件表达的
同一个流程。我们的 Architecture 阶段的及格线，就是 spec-kit 的克制 baseline +
OCR 的工程 backbone，且**不重演它任何一处 control-flow 越界**。
