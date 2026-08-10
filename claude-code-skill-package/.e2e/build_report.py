#!/usr/bin/env python3
"""FIXTURE / MECHANICAL SMOKE ONLY — not semantic Research Loop proof.

Builds a report manuscript (markdown + citations) for render-report from a fixed
landscape. It exercises the deterministic citation renderer and publish path for
mechanical end-to-end smoke and does NOT demonstrate the adaptive research loop or a
fresh semantic editorial pass. Treat the manuscript below as fixture data, not as
evidence of a correctly run research loop.
"""
import json

refmap = json.load(open('.e2e/paper_refs.json', encoding='utf-8'))
fam_refs = json.load(open('.e2e/family_refs.json', encoding='utf-8'))

# Citation ID -> paper_ref mapping
cmap = {
    "SM": refmap["2608.01822"],      # SearchMaster
    "SSP": refmap["2510.18821"],    # Search Self-play
    "SESE": refmap["2607.29468"],   # Self-Play Meets Skill Evolution
    "CoEvoKG": refmap["2608.01904"],# CoEvoKG
    "KGP": refmap["2605.05702"],    # KG Paths
    "ABS": refmap["2608.05102"],    # ABSeeker
    "PiCA": refmap["2605.09287"],   # PiCA
    "BTR": refmap["2605.29697"],    # Beyond Trajectory Rewards
    "STAMP": refmap["2607.11172"],  # STAMP
    "TRIAGE": refmap["2606.32017"], # TRIAGE
    "CRAFT": refmap["2606.29476"],  # CRAFT
    "CWGRPO": refmap["2604.14267"], # Contribution Weighted GRPO
    "VPR": refmap["2605.10325"],    # Verifiable Process Rewards
    "OASES": refmap["2604.03675"],  # OASES
    "SS": refmap["2601.04888"],     # SmartSearch
    "InfoFlow": refmap["2510.26575"],# InfoFlow
    "SR2": refmap["2602.03647"],    # Search-R2
    "RSPO": refmap["2607.04713"],   # RSPO
    "CIGPO": refmap["2607.16244"],  # CIGPO
    "AC": refmap["2605.21125"],     # Advantage Collapse
    "TGRPO": refmap["2605.26958"],  # Tournament-GRPO
    "APPO": refmap["2606.12384"],   # APPO
    "AREX": refmap["2607.21461"],   # AREX
    "Argus": refmap["2605.16217"],  # Argus
    "SciR": refmap["2605.01489"],   # SciResearcher
    "LiteR": refmap["2604.17931"],  # LiteResearcher
    "OffS": refmap["2601.18467"],   # OffSeeker
    "AOPSD": refmap["2608.05987"],  # AgentOPSD
    "TRIAL": refmap["2608.07371"],  # TRIAL
    "CIPO": refmap["2608.06128"],   # Contextual Information Policy Optimization
    "SGRT": refmap["2608.00974"],   # Search-GRT
    "ReTool": refmap["2504.11536"], # ReTool
    "ToolR1": refmap["2509.12867"], # Tool-R1
    "DRSurvey": refmap["2512.02038"],# Deep Research Survey
}

citations = [{"citation_id": cid, "paper_ref": pref} for cid, pref in cmap.items()]
print(f"Citations: {len(citations)}")

markdown = """# 基于强化学习的智能体搜索与深度研究训练：技术路线综述

## 1. 引言与研究范围

本综述系统梳理"基于强化学习（RL）的智能体训练用于智能体搜索（Agent Search）与深度研究（Deep Research）"领域的主要技术路线、代表性方法、训练与奖励设计、实证证据强度、路线权衡以及开放问题。研究范围涵盖同行评审与 arXiv 一手文献，时间覆盖至 2026 年 8 月前沿工作。

智能体搜索与深度研究的核心挑战在于：搜索轨迹通常是长时序（long-horizon）的，而最终答案的正确性只提供一个稀疏的终端奖励信号。如何将该稀疏信号转化为对中间搜索步骤的有效监督，是该领域训练方法的核心瓶颈。围绕这一瓶颈，文献演化出多条技术路线。

## 2. 主要技术路线与判别准则

### 2.1 自博弈与自演化搜索智能体（Self-Play & Self-Evolving Search Agents）

**核心机制**：同一模型或耦合模型在无外部监督下生成、求解并验证任务。任务生成以证据链或知识图谱为锚点，搜索深度或证据密度奖励用于约束浏览效率。

SearchMaster [cite:SM] 提出了一种基于证据链锚定（Evidence-Chain-Grounded, ECG）的自博弈框架：单一策略 π_θ 同时充当提议者（Proposer）与求解者（Solver），冻结的验证者（Verifier）判定正确性。搜索深度奖励惩罚低效浏览——即用更少的唯一查询达到正确答案。其方法部分（已通过 read-source 验证，16925 字符）明确描述了浏览器工具集 T={search, open, find} 与双角色奖励设计。

Search Self-play [cite:SSP] 最早建立了无标签自博弈可推动能力前沿的范式。Self-Play Meets Skill Evolution [cite:SESE] 将过程性失败转化为可复用技能写入记忆库，形成任务生成与技能演化的双向学习回路。CoEvoKG [cite:CoEvoKG] 使用知识图谱作为持久记忆，同时驱动任务生成与奖励计算，实现智能体与 KG 的协同演化。Knowledge-Graph Paths [cite:KGP] 将 KG 子图作为中间监督，引入航点覆盖奖励。

**判别准则**：该路线的子路线以"锚定基底"区分——证据链锚定（SearchMaster）、知识图谱锚定（CoEvoKG/KGP）、无锚定（Search Self-play）。锚定质量直接决定生成任务的可解性与可验证性。

### 2.2 搜索轨迹的信用分配（Credit Assignment for Search Trajectories）

**核心机制**：将稀疏终端结果奖励转化为对中间搜索步骤的步骤级信用。子路线以"信用信号来源"区分。

ABSeeker [cite:ABS] 从真值答案回溯，对中间搜索步骤评分，解决长时序轨迹中结果奖励过稀疏的问题。PiCA [cite:PiCA] 将过程奖励定义为依赖历史上下文的成功概率，识别"枢轴步骤"（信息峰值）引导智能体。Beyond Trajectory Rewards [cite:BTR] 在潜在实体-关系图中以图距离评分步骤。STAMP [cite:STAMP] 追踪首次曝光引用，通过符号保持的优势调制将信用归于引入有用证据的动作。TRIAGE [cite:TRIAGE] 将动作分类为进展/探索/回归三类，施加角色特定信用。CRAFT [cite:CRAFT] 利用重要性加权的兄弟 rollout 与非对称 KL 控制提供带符号的反事实 token 级信用。Contribution Weighted GRPO [cite:CWGRPO] 用 LLM 评判者评分检索效用与推理正确性，在 GRPO 内重缩放优势。

**判别准则**：信用来源——答案回溯（ABSeeker）、信息峰值（PiCA）、图距离（BTR）、出处追踪（STAMP）、角色分类（TRIAGE）、反事实兄弟（CRAFT）。是否需要真值答案是关键权衡：回溯与可验证方法依赖真值，结构化方法不依赖但依赖轨迹结构假设。

### 2.3 搜索的过程奖励模型（Process Reward Models for Search）

**核心机制**：通过过程奖励模型提供密集的逐步/逐轮监督。

Verifiable Process Rewards [cite:VPR] 将符号或算法预言机转化为密集的逐轮奖励，避免启发式标签噪声。OASES [cite:OASES] 协同训练搜索策略与状态评估器，导出与结果对齐且随策略演化自适应的过程奖励。SmartSearch [cite:SS] 通过双层级信用评估与课程学习选择性精修低质量中间查询。InfoFlow [cite:InfoFlow] 通过任务分解、失败引导提示注入与双智能体架构优化奖励密度。Search-R2 [cite:SR2] 使用 Actor-Refiner 框架，以混合奖励耦合结果正确性与证据密度。

**判别准则**：PRM 路线增加一个可漂移的奖励模型，而信用分配路线从轨迹或兄弟 rollout 中结构化地导出信用。两者目标一致（密集化监督），但 PRM 路线有模型漂移风险，结构化路线依赖轨迹结构假设。

### 2.4 多轮智能体的 GRPO 变体（GRPO Variants for Multi-Turn Agents）

**核心机制**：将群体相对策略优化（GRPO）适配于多轮智能体场景，解决优势坍缩（advantage collapse）等失效模式。

Advantage Collapse [cite:AC] 诊断了 GRPO 在长时序任务中群体相对优势坍缩至零、消除学习信号的失效模式。CIGPO [cite:CIGPO] 注入逐轮信息增益奖励以防止奖励方差坍缩与零优势锁定。RSPO [cite:RSPO] 利用密集过程奖励引导训练，同时通过交换机制保证与真实结果奖励的一致性。Tournament-GRPO [cite:TGRPO] 将评分准则引导的 LLM 判断转化为多轮群体锦标赛相对奖励。APPO [cite:APPO] 将信用分配转移至细粒度决策点，使用分支评分与过程级优势缩放。

**判别准则**：各变体以"对优势坍缩的应对方式"区分——信息增益注入（CIGPO）、交换一致性保证（RSPO）、锦标赛相对化（TGRPO）、过程级缩放（APPO）。优势坍缩诊断为这些变体提供了理论基础。

### 2.5 深度研究智能体系统（Deep Research Agent Systems）

**核心机制**：构建端到端的深度研究智能体，在长时序上迭代收集证据并综合答案。

AREX [cite:AREX] 提出递归自改进研究智能体，交替进行证据收集与约束审计，使用压缩上下文更新维持长时序连贯性。Argus [cite:Argus] 部署搜索者与导航者通过共享证据图协作，RL 优化调度与综合，支持并行 rollout 无需重训练。SciResearcher [cite:SciR] 引入科学任务自动合成框架，以智能体 RL 训练 8B 模型达到前沿科学推理 SOTA。LiteResearcher [cite:LiteR] 构建轻量虚拟世界镜像真实搜索动态，降低外部 API 成本。OffSeeker [cite:OffS] 证明完全离线训练可媲美昂贵的在线 RL 循环。

**判别准则**：架构——递归自改进（AREX）、证据图协作（Argus）、领域专用（SciResearcher）、虚拟世界降本（LiteResearcher）、离线训练（OffSeeker）。在线与离线训练构成关键成本-质量权衡轴。

### 2.6 智能体 RL 的自蒸馏与后见（Self-Distillation & Hindsight）

**核心机制**：无需外部评判者，通过自蒸馏与后见技术将稀疏结果奖励转化为密集监督。

AgentOPSD [cite:AOPSD] 采用递归贝叶斯信念更新，无评判者地将稀疏结果奖励转化为密集逐轮信用。TRIAL [cite:TRIAL] 通过统一评分协议在决策轮间分配后见信号，超越 GRPO 基线。

### 2.7 智能体工具使用的强化学习（RL for Tool Use in Agents）

**核心机制**：将 RL 应用于 LLM 智能体的工具使用策略优化。

ReTool [cite:ReTool] 建立 RL 优化工具使用策略的可行性。Tool-R1 [cite:ToolR1] 提出样本高效的智能体工具使用 RL。Contextual Information Policy Optimization [cite:CIPO] 提出证据导向的 RL 框架，对齐策略优化与外部证据以减少确认偏差。Search-GRT [cite:SGRT] 引入引导检索训练，将 RL 检索限制在真值文档以缓解稀疏奖励。

## 3. 关键训练与奖励设计

跨路线的核心训练/奖励设计可归纳为以下主题：

1. **信用分配密集化**：所有路线均致力于将稀疏终端信号密集化。信用分配路线（2.2）与 PRM 路线（2.3）从不同角度解决同一问题——前者结构化、后者模型化。

2. **搜索效率奖励**：SearchMaster [cite:SM] 的搜索深度奖励与 Search-R2 [cite:SR2] 的证据密度奖励均惩罚低效浏览，表明仅答案正确性不足以约束训练后智能体的过度搜索行为。

3. **优势坍缩缓解**：GRPO 变体（2.4）针对长时序多轮场景中优势坍缩至零的失效模式，通过信息增益、交换一致性、锦标赛相对化等手段恢复优势方差。

4. **证据锚定**：自博弈路线（2.1）以证据链或 KG 锚定任务生成，确保生成任务可解且可验证，避免无锚定自博弈产生平凡或不可解任务。

## 4. 实证结果与证据强度

各路线的实证证据强度不均。多数论文在各自基准上报告改进，但跨方法比较仅可从各论文基准间接推断——保留语料中缺乏信用分配子路线（答案回溯 vs. 图距离 vs. 出处 vs. 反事实）在统一搜索智能体基准上的直接头对头比较。SearchMaster [cite:SM] 的搜索深度奖励在降低平均查询数的同时维持答案准确率；OffSeeker [cite:OffS] 的离线训练在降低成本下媲美在线 RL；SciResearcher [cite:SciR] 以 8B 模型达到科学推理 SOTA。

## 5. 证据冲突与不可比性

1. **跨方法不可比**：信用分配子路线缺乏统一基准下的头对头比较，跨路线比较仅可从各论文基准间接推断。
2. **PRM 与结构化信用的权衡**：PRM 路线增加可漂移模型，结构化路线依赖轨迹结构假设——两者目标一致但失效模式不同，难以直接比较。
3. **在线与离线权衡**：OffSeeker [cite:OffS] 与 LiteResearcher [cite:LiteR] 挑战在线 RL 必要性，但离线轨迹质量与多样性是关键前提，与在线方法的可比性受轨迹质量约束。

## 6. 路线权衡

- **自博弈锚定 vs. 覆盖**：证据链/KG 锚定提高可验证性但可能限制文档集外覆盖；无锚定自博弈覆盖广但任务质量风险高。
- **在线 vs. 离线**：在线 RL 交互成本高但可探索真实环境；离线训练成本低但依赖策展轨迹质量。
- **PRM vs. 结构化信用**：PRM 提供显式可学习奖励但有漂移风险；结构化信用无模型但依赖轨迹结构假设。
- **搜索效率 vs. 答案质量**：搜索深度/证据密度奖励提高效率但可能过早终止有用探索。

## 7. 开放问题

1. **自博弈中验证者可靠性**：所有自博弈路线依赖验证者判定正确性，弱验证者传播错误监督，但缺乏在无真值下检测与恢复验证者失效的原则性方法。
2. **无真值的信用分配**：多数信用分配方法依赖真值答案或符号预言机，向开放式、不可验证研究任务扩展仍为开放问题。
3. **长时序上下文管理**：随着研究时序增长，上下文窗口需压缩或记忆管理，如何在 RL 中联合优化答案质量与上下文/记忆管理而无奖励干扰尚未解决。
4. **标准化评估**：缺乏在受控条件下同时评估答案质量与搜索效率（查询数、token 成本、证据精度）的统一基准。
5. **奖励黑客与过度搜索**：智能体可能发展过度搜索或利用奖励捷径；搜索深度奖励部分缓解，但多轮搜索 RL 中对抗奖励黑客的通用防御仍缺失。

## 8. 前沿工作覆盖

本综述覆盖至 2026 年 8 月前沿工作：最新保留论文日期为 2026-08-07，51 篇论文中 41 篇来自 2026 年。前沿工作包括 SearchMaster [cite:SM]（2026-08-03，自博弈）、ABSeeker [cite:ABS]（2026-08-05，答案回溯信用分配）、AREX [cite:AREX]（2026-07-23，递归自改进深度研究）、Contextual Information Policy Optimization [cite:CIPO]（2026-08-06，证据对齐策略优化）、Search-GRT [cite:SGRT]（2026-08-02，引导检索训练）等。

## 9. 结论

基于 RL 的智能体搜索与深度研究训练已形成以信用分配为核心、多路线并进的研究格局。自博弈与自演化路线解决了无监督训练数据问题；信用分配与过程奖励路线解决了稀疏奖励密集化问题；GRPO 变体解决了多轮场景的优势坍缩问题；深度研究系统路线将上述组件整合为端到端智能体。当前主要瓶颈在于：无真值场景的信用分配、验证者可靠性、长时序上下文管理、以及标准化评估的缺失。这些开放问题指明了未来研究方向。
"""

out = {"markdown": markdown, "citations": citations}
with open('.e2e/render_input.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(f"Saved render input: {len(markdown)} chars markdown, {len(citations)} citations")
