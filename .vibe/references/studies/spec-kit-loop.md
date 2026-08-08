# Study Note: formin/spec-kit-loop

> 本 Note 是第四份 Reference Study，直接对应本项目的 **Loop Engineering** 问题：
> 当 Agent 可以长时间自主迭代时，怎样避免它自己做、自己检查、自己宣布完成？
> 前几份 Study 解决了 Harness 外壳（spec-kit-harness 的 baseline、old-search-harness
> 的越界、paper-qa 的研究语义），本份补的是**循环本身的可信度**——它是谁做的、谁判的、
> 谁宣布完成的。适配方向按 Study 指南：`Researcher → ready_for_review → Fresh Semantic
> Review → PASS / CONTINUE / UNCERTAIN`，而不是复制完整 Spec Kit Loop Workflow。

## Snapshot

```
Repository: https://github.com/formin/spec-kit-loop
Commit:     e216b4c（# 排除 repository-only 文件出 release 包；研究时点 HEAD）
Study date: 2026-08-09
License:    MIT（2026 formin）
形态:       Spec Kit 扩展（与 spec-kit-harness 同族），零可执行代码，纯 prompt 约束
```

五个命令：`define`（写契约）/ `run`（maker）/ `check`（checker）/ `guard`（closure）/
`status`（resume）。与 spec-kit-harness 是同一仓库族（`openwiki/`、`extension.yml`、
`config-template.yml` 同构），但解决的是**循环的可信度**而不是**研究状态的外置**。

---

## Why We Studied It

它是 Tier 1 中唯一直接回答「循环怎么保持诚实」的参考。spec-kit-harness 给了我们
循环的形状（简单循环 + 丰富状态 + 对抗验证），但没回答一个尖锐问题：**循环里谁有权说
「完成了」？**

Loop Engineering（Addy Osmani）命名了自主循环的三个失败模式，本扩展的每个 guardrail
都对着其中一个：

| 失败模式 | 含义 | 对应 guardrail |
|---|---|---|
| **Unattended verification** | 工作无人打分，或被生产它的模型打分（"the model that wrote the code is way too nice grading its own homework"） | maker/checker 分离 + `verdicts.md` 唯一写入权 + guard 标记低置信/非独立通过 |
| **Comprehension debt** | 循环改的东西超出你的理解，缺口逐轮累积 | `debt.md` 账本 + guard 的 debt sweep + `block_done_on_open_debt` |
| **Cognitive surrender** | 因为检查是工作，就慢慢接受循环产出的一切 | guard 的反投降提问 + 关闭循环前的人工签字门 |

这直接对应我们 PROJECT_VISION 的 **P11（Researcher Cannot Self-Declare DONE）** 与
**P12（Fresh Review Is Semantic Checkpoint）**。本份 Study 的价值在于：它给了这两条
原则一套可落地的机制与字段。

---

## Architecture in One Diagram

```text
/speckit.loop.define ──► 契约先行（无 checkable done-criteria 拒绝创建）
        │  五个 state 文件（全在磁盘，conversation disposable）：
        │    loop.md（契约+实时状态） · iterations.md（maker 追加记录）
        │    verdicts.md（checker 唯一可写） · debt.md（理解债务+签字日志）
        │    memory.md（跨 run 耐久决策）
        ▼
┌──────────────── THE LOOP ────────────────────────────────┐
│  /speckit.loop.run   maker：一个增量 → 外部化 → 自评(非结论) │
│       │  只写 iterations.md · 只把标准置为 maker-ready      │
│       ▼  迭代上限达到 → 停止制造，强制 check + guard        │
│  /speckit.loop.check  checker（fresh session）：对抗式、     │
│       │  对 primary source 尝试使之失败                     │
│       │  verdicts.md：pass | fail | uncertain (+confidence) │
│       │    pass → checker-pass · fail → 回 run ·            │
│       │    uncertain → 开 debt 项交给人                     │
│       └── 每判一次都记录，checker-pass ≠ done               │
└────────────────────────────────────────────────────────────┘
        ▼
/speckit.loop.guard   debt sweep + 无人核验标记 + 反投降提问
        │  done-gate（三者同时成立才允许 done）：
        │    ① 所有 done-criteria = checker-pass
        │    ② 无 blocking（高严重度）债务
        │    ③ 记录在案的人工签字（signoff 只能由人给）
        ▼
Phase: done
/speckit.loop.status  只读 bounded slice + 单一 next action（resume 入口）
```

关键观察：**这个扩展把所有「诚实」都编码成了「谁有权写哪个文件」**——maker 无权写
`verdicts.md`、无权设 checker-pass/done；checker 是唯一 grader；guard 是唯一能置
`done` 的命令，且必须同时满足三条。这是用「写权限」实现 P11/P12，而非靠 prompt 哀求。

---

## Core Concepts

1. **循环是预先写下的契约，不是随口的目标**：`define` 把「我会一直 prompt 到完成」变成
   「一个你设计过的循环」。无 checkable done-criteria 就拒绝创建——开环正是漂移的形状。
2. **maker 永不给自己最终 verdict**：`run` 生产与记录，最多标 `maker-ready`；`checker-pass`
   与 `done` 永远不属于 maker。自评是给 checker 的 hint，必须标注「这是 maker 自己的看法」。
3. **checker 必须独立**：与 maker 同上下文 = 继承 maker 的盲点。`checker.independent: true`
   时，checker 若发现自己与 maker 同会话，应拒绝打分并建议到 fresh session / sub-agent 重跑。
4. **对抗式打分，默认 fail**：checker 的作业是先让标准失败（primary source 上验证反面），
   不确定时默认 fail/uncertain——**无人看管的循环应少报而不是多报**。
5. **PASS / FAIL / UNCERTAIN 是 typed verdict，不是数字**：每条标准独立判；UNCERTAIN 不折算成
   「0.8 分」，而是变成一个交给人解决的 debt 项。confidence（high/medium/low）是**风险标记**，
   低置信 pass 会被 guard 标成「无人核验」，不参与任何加权。
6. **预算是对自主的硬限制**：`max_iterations` 是硬顶。迭代数达到 → 停止制造，强制 check +
   guard（人审）。「无界 making 是循环漂移的入口」。
7. **状态在磁盘，上下文可弃**：一切有价值的东西都在五个文件里；`status` 把一个 bounded
   slice 重新渲染进任何新会话。这是「conversation disposable」的完整表述。
8. **Closure 是人的行为**：checker 全过是必要不充分。`guard` 是唯一能把 phase 置 `done` 的
   命令，且只有当 checker-pass、无 blocking debt、有人工签字三者同时成立。

---

## Important Files

| 文件 | 角色 | 关键机制 |
|---|---|---|
| `commands/speckit.loop.define.md` | 写契约 | 非协商字段：Purpose / Done-criteria（每条可对 primary source 判过/败）/ Budget / Roles / Allowed tools / Isolation / Automation trigger / Guardrails |
| `commands/speckit.loop.run.md` | maker | 迭代上限硬门；一个增量一条记录；自评标 `maker-ready` 永不 `checker-pass`；显式 handoff |
| `commands/speckit.loop.check.md` | checker | 独立性门；对抗式（先让它失败）；pass/fail/uncertain + confidence；uncertain → 开 debt |
| `commands/speckit.loop.guard.md` | closure | debt sweep、无人核验标记、反投降提问、done-gate、signoff 只记录人给的动作 |
| `commands/speckit.loop.status.md` | resume | 只读；bounded slice（`iterations_slice` 6 / `debt_slice` 8 / `context_tokens` 4000）；恰好一个 next action |
| `config-template.yml` | 配置 | `max_iterations: 8`、`checker.votes: 1`、`guard.*`、`rendering.*`、`state.directory` |
| `docs/concepts.md` | 概念映射 | Loop Engineering 组件 ↔ 扩展落地；三个失败模式 ↔ guardrails；prompt-only 诚实局限 |
| `README.md` | 工作流定位 | loop 不替换核心阶段，只包裹 build-and-verify 部分；两个可选 hook |

**状态流转**（loop.md 的 done-criteria 表）：`pending → maker-ready → checker-pass |
checker-fail → human-signed`；`uncertain` 保持 `maker-ready` 并开 debt 项。

---

## Key Data Flow

```text
define：purpose + 可检查 done-criteria + budget + roles ──► 五个 state 文件
   │
run（maker，每轮一个增量）：
   │  读 loop.md + 最近 iterations.md + memory.md（以文件为准，不用会话记忆）
   │  worktree 隔离（可选）→ 改 → 追加 iterations.md 记录
   │  更新 loop.md：迭代计数 +1，目标标准 → maker-ready
   │  若 迭代数 ≥ max_iterations：停止，报告需 check + guard（人审）
   ▼
check（checker，fresh session）：
   │  读契约与 maker 声称（作为待验证的 claim，不是证据）
   │  对每条标准：尝试使之失败 → 记 pass/fail/uncertain（+confidence）
   │  追加 verdicts.md → 更新 loop.md（pass→checker-pass / fail→checker-fail /
   │    uncertain→保持 maker-ready + 开 debt）
   │  全部 checker-pass 也不置 done，推荐 guard
   ▼
guard：debt sweep + 无人核验标记 + 反投降提问 → done-gate
   │  ① 所有标准 checker-pass ② 无 blocking debt ③ 人工 signoff 记录在案
   ▼
Phase: done（只有 guard 能置）
status：任意时刻（含 fresh session）渲染 bounded slice + 单一 next action
```

---

## Key State Model

五文件全部持久化，是「研究过程成为可检验工程状态」的又一个实证（与 spec-kit-harness
同族，但更细）：

```text
specs/<feature>/loop/
├── loop.md       契约 + 实时状态：done-criteria 表（ID/标准/如何验证/状态）、
│                 Budget（迭代数/max）、Roles、Allowed tools、Automation trigger、
│                 Guardrails、Phase（defined→maker-ready→checked→done）
├── iterations.md  maker 追加记录（append-only）：本轮目标标准、改动、自评(hint)、
│                 开放问题/风险、handoff
├── verdicts.md    checker 唯一可写：ID/迭代/标准/primary-source 方法/verdict/
│                 confidence/日期
├── debt.md        理解债务账本（acknowledged 不删除）+ 签字日志
└── memory.md      跨 run 耐久决策/约定/dead ends（M-xxx 条目）
```

对照前几份：spec-kit-harness 用 6 个文件表达「研究状态」，spec-kit-loop 用 5 个文件
表达「循环可信度」。两者互补——harness 管「知道什么」，loop 管「谁做的、谁判的、凭什么说
完成」。

---

## Design Decisions Worth Learning

### Decision 1 — maker/checker 分离由「写权限」enforce，而非 prompt 约定

**Problem**：自主循环的核心风险是无人核验——「写代码的模型给自己作业打分太宽松」。

**Design**：`run`（maker）只写 `iterations.md`，只能把标准置 `maker-ready`；`check`
（checker）是 `verdicts.md` 唯一写入者、唯一能设 `checker-pass`；`guard` 是唯一能置
`done` 的命令。**每个命令能写哪些文件，就是诚实保证本身**。

**Why**：把「谁有权说什么」编码进命令结构，比在 prompt 里写「请公正打分」可靠得多。
自评永远被标记为 maker 自己的看法（hint），不作为结论进入状态机。

**Trade-off**：诚实说，它是 prompt-only——命令是给 agent 的指示，不是可执行代码。如果
maker 无视指令去写 verdicts.md，没有运行时阻止（它自己承认："rules are mechanical and
append-only, so drift is visible in the diff, but not impossible"）。可见性是它能给的最强
保证，但**不是**强制。

**我们是否存在同样的问题**：是——这正是我们 P11/P12 要 enforce 的。**是否有更简单的实现**：
我们与它不同，我们有 Python Research Runtime（ADR 已定）。**Python 可以真正 enforce**
「谁写 verdicts」：把 verdict 文件做成仅 fresh review 会话可写的结构，或 review 动作由
Runtime 校验 maker/reviewer 身份。这是我们对 spec-kit-loop 的**正向量化**——它的诚实
保证是提示性的，我们能让它是机械性的。
**结论**：采纳写权限分离原则，用 Python enforce；maker/checker 分离落进 ADR。

---

### Decision 2 — PASS / FAIL / UNCERTAIN + confidence，而不是 numeric score

**Problem**：怎么判断「完成」？

**Design**：每条 done-criteria 由 checker 对 primary source 独立判 `pass`/`fail`/
`uncertain`，附 confidence（high/medium/low）。`uncertain` 不折算成分数，而是开一个
debt 项交给人；低置信 `pass` 会被 guard 标记为「无人核验」要求人工确认。checker 不确定时
默认 `fail`/`uncertain`。

**Why**：与 old-search-harness 的 `sufficiency_score`（5 类异构指标加权求和 + 阈值）正面
对照。数字允许「覆盖率不够、非共识来凑」的补偿；typed verdict 每条独立，任何一条不满足
都如实呈现。**UNCERTAIN 是诚实的出口**——「以现有条件无法判定」就明说并交给可判定的人，
而不是给一个中间分假装解决了。

**Trade-off**：typed verdict 表达不了「差一点点」的连续程度；但循环不需要连续程度，它需要
「这条标准满足了没有」。

**我们是否存在同样的问题**：是（P13/P14）。**是否有更简单的实现**：spec-kit-loop 的
PASS/FAIL/UNCERTAIN 就是我们 P12 的 CONTINUE/UNCERTAIN/PASS 的直接来源。confidence 作为
风险标记（低置信 pass → 需要人工确认）值得保留，但不做加权。
**结论**：采纳。Review 的产物是 typed verdicts + confidence 风险标记 + explicit
unresolved 清单；不产出任何「完成度数字」。

---

### Decision 3 — 可检查的 done-criteria 是契约的强制字段

**Problem**：循环的停止条件从哪里来？

**Design**：`define` **拒绝创建没有 checkable done-criteria 的循环**。每条标准必须是
checker 能对 primary source 通过或失败的东西：「npm test 退出 0」可以，「It works」不行。
标准表还写死「checker 如何验证它」（method 列），让验证方法在契约里预承诺。

**Why**：这是防无限循环的第一道闸（Q7 的答案之一）。开环——「迭代到完成为止」但「完成」
不可检查——正是漂移的形状。**把「完成」预先定义成可验证的谓词**，循环才有边界。

**Trade-off**：对 research 场景，标准可检查化比代码场景难——证据覆盖、非共识是否充分，
不如「测试通过」那样二值。但可以做到 typed（每维度 covered/partial/missing + 关键标准
非补偿），这是 spec-kit-harness 已验证的形态。

**我们是否存在同样的问题**：是——我们 PLAN 阶段必须产出可检查的 criteria。**是否有更简单
的实现**：把「每条 criteria 如何验证」也写进契约（method 列）是个低成本高价值习惯。
**结论**：采纳「PLAN 阶段 done-criteria 必须可检查、且写明验证方法」进 ADR。

---

### Decision 4 — 预算是对自主的硬限制，触发强制人审

**Problem**：怎么防止循环无限运行（Q7）？

**Design**：`max_iterations` 是硬顶（默认 8）。`run` 的预算门：`Iterations run >=
max_iterations` → 不再制造，报告「循环现在需要 check + guard（人审），而不是继续 make」。
批量运行（`n=<k>`）也仍要停下来做 checker handoff。

**Why**：`run` 的 docstring 明说：「这个天花板是 feature：无界 making 是循环漂移的入口。」
预算不只控制成本，它**强制在自主退场时交回给人/检查**——这正是 P5（Harness 拥有确定性
记账）与 P13（数字约束资源）的循环语义。

**Trade-off**：固定迭代上限对复杂任务可能过早触发；但 budget 的作用不是「足够」，而是
「必须停下来重新评估」。spec-kit-harness 的 Budget ledger（Budget/Spent/Remaining）与
此互补：它是账本，loop 把「达到上限」变成「强制 review」。

**我们是否存在同样的问题**：是。**是否有更简单的实现**：把「迭代/预算耗尽」作为
REVIEW 的触发条件之一（与我们 lifecycle 的 stop conditions 合并），而不是单独的
max_iterations 概念。old-search-harness 的 `budget_exhausted → incomplete=true` 已有雏形。
**结论**：采纳「预算耗尽强制 review」；budget 进 state（P5），是 stop condition 之一。

---

### Decision 5 — 状态在磁盘，status 是 resume 入口，且只给一个 next action

**Problem**：循环跨会话、跨崩溃、跨交接如何恢复？

**Design**：一切有价值的状态在五个文件里（契约、每次迭代、每个 verdict、每笔债务）。
`status` 只读、渲染 bounded slice（iterations/debt 有各自 slice 数，context_tokens 4000
软顶），并以**恰好一个 next action** 收尾——由快照推导（checker-fail → run；maker-ready
→ check；全过但 sign-off 未落 → guard；迭代满 → guard）。

**Why**：这同时实现了三件事：会话可弃（P3 恢复的是研究过程）、上下文是状态的 view
（P21，只渲染 slice）、Harness 暴露状态而非隐藏它（P22，status 给出下一步）。

**Trade-off**：单一 next action 的推导规则对复杂状态可能过于简化；但对 resume 而言，
「下一步做什么」的确定性正是让新会话能接手的关键。

**我们是否存在同样的问题**：是（P3/P21/P22）。**是否有更简单的实现**：spec-kit-harness
的 `/status` 已经示范过「只读 + bounded slice + resume」。spec-kit-loop 加了「单一 next
action 由状态推导」——这个确定性推荐正是我们 `/status` 该有的。
**结论**：采纳「状态推导单一 next action」进 P22 的实现。

---

### Decision 6 — comprehension debt 作为债务账本（research 侧要裁剪）

**Problem**：自主循环改的东西超过人理解的部分会逐轮累积（理解债务）。

**Design**：`debt.md` 是理解债务账本 + 签字日志。每次循环改了一个人还没理解的东西，
就是一笔债务；债务是 acknowledge 而不是 delete；`block_done_on_open_debt` 让高严重度
债务阻止 `done`。guard 的 debt sweep 会遍历每轮迭代，把没被证明被人 review 过的改动补成
债务行；反投降提问（「迭代 4 改了 X——一句话，为什么必须改？」）把 human 拉回循环。

**Why**：对抗认知投降——「因为检查是工作，就接受循环产出」。债务账本让「我还没理解」成为
一等状态，而不是默认假装理解了。

**Trade-off**：对 coding 是合理的；对 research，它映射不干净——文献调研里
「人还没理解」的东西是「未解决的 gap / unresolved 项」，不是「代码改了没看懂」。而且
Study 指南明确警告：**不要把 comprehension debt 变成 research 的一等子系统**。

**我们是否存在同样的问题**：部分。**是否有更简单的实现**：research 侧的等价物就是我们
P12 的 explicit unresolved 清单 + open questions——它们天然是「还没被理解/解决」的记录。
不需要一个独立 debt 账本。
**结论**：采纳其**精神**（未理解/未解决是一等状态，不假装解决），不采纳其**机制**
（不建 comprehension-debt 子系统）。

---

### Decision 7 — closure 是独立门：checker-pass 必要不充分

**Problem**：什么时候真正允许宣布完成？

**Design**：done-gate 三条件同时成立：① 所有 done-criteria `checker-pass`；② 无 blocking
debt；③ 人工 signoff 记录在案。`guard` 是唯一能置 `done` 的命令；signoff 只能记录人实际
给的动作，agent 不能代签。反投降提问回答不了 → 正确结果是「还没 done」，不是签字。

**Why**：这是 P11（Researcher Cannot Self-Declare DONE）与 P12 的完整闭环：maker 不能、
checker 只能给 verdict、closure 需要一个独立于两者的 gate。

**Trade-off**：指南明确——「human sign-off 对代码发布很重要，但不意味着每次文献 Research
Run 都必须人工签字才能结束」。我们的 REVIEW 是 fresh semantic checkpoint（P12），
人审只在最终 DONE/PARTIAL 交付时作为接受动作，不该是每个 RESEARCH 迭代的强制门槛。

**我们是否存在同样的问题**：是。**是否有更简单的实现**：把「人审」降级为「fresh semantic
review（可以是 Claude 的子 agent，fresh context）」，仅最终交付时由用户接受。
**结论**：采纳「closure 需要独立于 maker 的门」，但人审频率按指南裁剪（不是每次 run）。

---

## What We Should Borrow

1. **maker/checker 分离 + 写权限 enforce**（Decision 1）：Research（maker）与 Review
   （checker）角色分离；verdict 只能由 review 写。我们用 Python enforce 文件写入权，
   比它的 prompt-only 更强。对应 P11/P12。
2. **typed verdicts PASS / FAIL / UNCERTAIN + confidence 风险标记**（Decision 2）：Review
   产物 = 每条 criteria 独立 verdict + confidence + explicit unresolved。P13/P14。
3. **checkable done-criteria + 写明验证方法**（Decision 3）：PLAN 阶段强制。P7/P11。
4. **预算作为自主的硬限制**（Decision 4）：预算/迭代耗尽 → 强制 review，不是继续 make。
   P5/P13。
5. **状态在磁盘 + status 渲染 bounded slice + 单一 next action**（Decision 5）：P3/P21/P22
   的完整实现示范。
6. **UNCERTAIN 是诚实出口**：不确定就明说并开 unresolved，不折算中间分。P12。
7. **「谁有权说什么」的可见性**：即使 prompt-only，把 skip guardrail 变成可见选择而不是
   静默默认——我们 Python enforce 后同样保留「跳过 review 是显式动作」的可见性。

## What We Should Not Borrow

1. **五个独立 loop 命令**（define/run/check/guard/status）：我们不需要五个命令。maker/checker
   分离是生命周期里 RESEARCH 与 REVIEW 两个 phase 的语义，不是五个 CLI。
2. **Spec Kit 工作流本身**（spec/plan/tasks + hooks）：我们是研究 harness，不是编码 loop。
3. **coding-task 特定 criteria**（`npm test` 退出 0 / `/health` 返回 200）：我们的
   done-criteria 是 evidence 覆盖 / 非共识 / 关键标准 typed 判据。
4. **Worktree 隔离**：我们不在 git worktree 里跑并行迭代；隔离由 state 文件 + 原子写承担。
5. **强制人工 signoff 才能结束研究 run**（指南明示）：人审只在最终交付接受；研究迭代的
   review 是 fresh semantic checkpoint，不必每次等人类。
6. **comprehension debt 作为一等 research 子系统**（指南明示）：等价物是 explicit
   unresolved 清单，不建独立债务账本。
7. **automation trigger 记录（scheduler/CI）**：我们不调度循环。

## Conflicts with PROJECT_VISION

1. **一致强化 P11/P12**：spec-kit-loop 几乎就是 P11/P12 的机制化——「Researcher Cannot
   Self-Declare DONE」（maker 无权设 done）、「Fresh Review Is Semantic Checkpoint」
   （checker 独立 + adversarial）。无冲突，是证据。
2. **P6（Policy/Mechanism）的落点**：spec-kit-loop 的诚实保证是 prompt 层的（policy）；
   我们要把它做成 Python enforce（mechanism）——谁写 verdicts 由 Runtime 决定。这符合
   我们的 ADR（Python = 确定性记账），不是越界（它没有把研究语义决策交给机制，只是
   把关「谁有权写什么」）。
3. **「Closure is a human act」vs 研究场景**：部分冲突。我们接受「closure 需要独立门」，
   但研究 run 的 closure = fresh semantic review（P12），不是每次强制人工签字。
4. **budget 强制人审 vs 自主研究循环**：我们采纳「预算耗尽强制 review」，但 review 是
   fresh Claude 子 agent，不一定等人类——人审只出现在最终 DONE/PARTIAL。

## Questions Still Open

1. **verdict 写入权怎么用 Python enforce**？选项：(a) verdict 文件由 Runtime 管理，只有
   review 动作可写（review 需要 fresh session 凭据/参数）；(b) 只是状态机检查「maker 阶段
   不能写 verdict」；(c) 全凭约定。倾向 (a)+(b)，但别过度机制化（old-search-harness 教训：
   别把该是 policy 的东西做成 mechanism 爆炸）。
2. **REVIEW 的 fresh 到什么程度**？P12 说 fresh review。是「全新会话」还是「一个不带 maker
   上下文、只读 bounded state slice 的子 agent」？后者更像 spec-kit-loop 的
   fresh-session 约定，且不依赖人类。candidate ADR。
3. **typed verdicts 的粒度**：PASS/CONTINUE/UNCERTAIN 每维度一个，还是每 claim 一个？
   old-search-harness 的六字段非共识给了 per-item 形态；spec-kit-loop 是 per-criterion。
   我们的 review 可能是两者混合（criteria 级 verdict + claim 级 unresolved）。
4. **confidence 标记要不要**：high/medium/low 作为「无人核验」风险标记有价值，但会不会
   变成又一个 false-precision？倾向要，但只作风险旗标不作加权。

## Candidate ADRs Influenced by This Project

1. **ADR：Maker（RESEARCH）/ Checker（REVIEW）分离由 Python enforce——verdict 与
   done 状态只能由 fresh review 写入；maker 无权 self-grade。**（Decision 1、7，P11/P12）
2. **ADR：Review 产物是 typed verdicts（PASS / CONTINUE / UNCERTAIN）+ confidence 风险
   标记 + explicit unresolved 清单；禁止任何完成度数字。**（Decision 2，P13/P14）
3. **ADR：PLAN 阶段 done-criteria 必须可检查、每条写明验证方法；无 checkable criteria
   的 mission 不开始。**（Decision 3，P7/P11）
4. **ADR：预算/迭代耗尽是强制 Review 的触发条件（stop condition），不是「继续 make」。**
   （Decision 4，P5/P13）
5. **ADR：`/status` 是 resume 入口，只读、渲染 bounded slice、由状态推导单一 next
   action。**（Decision 5，P3/P21/P22）
6. **ADR：研究侧的「理解债务」= explicit unresolved 清单 + open questions，不建独立
   comprehension-debt 子系统；人审只在最终交付作为接受动作。**（Decision 6、7）

## 一句话结论

spec-kit-loop 是 P11/P12 的机制化样板：**循环的可信度不在循环跑得多好，而在「谁有权说
完成」**——maker 生产、checker 独立对抗式打分（typed PASS/FAIL/UNCERTAIN + confidence）、
guard 做 closure 门、状态全在磁盘、预算硬顶强制 review。它把我们在 spec-kit-harness
（stop conditions）、old-search-harness（对抗审计但 score-gate 出错）、paper-qa
（相关性分只作过滤）三份 Study 里零散看到的东西，收敛成一张可落地的契约与状态图。我们的
增量是：把它的 prompt-only 诚实保证，用 Python Runtime 变成机械强制——这是
`Claude Code = Agent Runtime / Python = Research Runtime` ADR 在这一轮得到的最直接背书。
