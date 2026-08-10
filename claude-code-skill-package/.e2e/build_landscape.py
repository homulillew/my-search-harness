#!/usr/bin/env python3
"""Build approach families, findings, open problems, and investigation gaps.

Taxonomy derived from the 30 analyzed papers, with discrimination criteria
for each technical route.
"""
import json

refmap = json.load(open('.e2e/paper_refs.json', encoding='utf-8'))

# === APPROACH FAMILIES (technical routes) ===
# Each: name, core_idea, representative_paper_refs
families = [
    {
        "name": "Self-Play & Self-Evolving Search Agents",
        "core_idea": "Train search agents via self-play where the same or coupled models generate, solve, and verify tasks without external supervision. Task generation is grounded in evidence chains or knowledge graphs, and search-depth or evidence-density rewards regulate browsing efficiency. The route includes self-evolving variants that accumulate reusable skills or co-evolve with a knowledge graph.",
        "representative_paper_refs": [
            refmap["2608.01822"],  # SearchMaster
            refmap["2510.18821"],  # Search Self-play
            refmap["2607.29468"],  # Self-Play Meets Skill Evolution
            refmap["2608.01904"],  # CoEvoKG
            refmap["2605.05702"],  # KG Paths as Intermediate Supervision
        ],
    },
    {
        "name": "Credit Assignment for Search Trajectories",
        "core_idea": "Address the sparse outcome-reward problem in long-horizon search by assigning step-level credit to intermediate search actions. Sub-routes differ by the credit signal source: answer-backtracking (ABSeeker), pivot/information-peak identification (PiCA), graph-distance proximity (Beyond Trajectory Rewards), provenance/first-exposure citation (STAMP), role-typed action classification (TRIAGE), and counterfactual sibling rollouts (CRAFT).",
        "representative_paper_refs": [
            refmap["2608.05102"],  # ABSeeker
            refmap["2605.09287"],  # PiCA
            refmap["2605.29697"],  # Beyond Trajectory Rewards
            refmap["2607.11172"],  # STAMP
            refmap["2606.32017"],  # TRIAGE
            refmap["2606.29476"],  # CRAFT
            refmap["2604.14267"],  # Contribution Weighted GRPO
        ],
    },
    {
        "name": "Process Reward Models for Search",
        "core_idea": "Provide dense per-step or per-turn supervision via process reward models, converting symbolic/algorithmic oracles (Verifiable Process Rewards), co-trained evaluators (OASES), or LLM judges into turn-level rewards. Sub-routes include query-refinement curricula (SmartSearch), reward-density optimization (InfoFlow), and actor-refiner evidence-density coupling (Search-R2).",
        "representative_paper_refs": [
            refmap["2605.10325"],  # Verifiable Process Rewards
            refmap["2604.03675"],  # OASES
            refmap["2601.04888"],  # SmartSearch
            refmap["2510.26575"],  # InfoFlow
            refmap["2602.03647"],  # Search-R2
        ],
    },
    {
        "name": "GRPO Variants for Multi-Turn Agents",
        "core_idea": "Adapt Group Relative Policy Optimization for multi-turn agentic settings, addressing failure modes such as advantage collapse and zero-advantage lock-in. Variants include reward-swap consistency guarantees (RSPO), information-gain injection (CIGPO), tournament-based relative rewards (Tournament-GRPO), procedural advantage scaling (APPO), and single-rollout asynchronous optimization (SAO). The advantage-collapse diagnosis provides the theoretical basis.",
        "representative_paper_refs": [
            refmap["2607.04713"],  # RSPO
            refmap["2607.16244"],  # CIGPO
            refmap["2605.21125"],  # Advantage Collapse
            refmap["2605.26958"],  # Tournament-GRPO
            refmap["2606.12384"],  # APPO
        ],
    },
    {
        "name": "Deep Research Agent Systems",
        "core_idea": "Build end-to-end deep-research agents that iteratively gather evidence and synthesize answers over long horizons. Architectures range from recursive self-improvement with constraint auditing (AREX), evidence-graph-based Searcher-Navigator cooperation (Argus), domain-specific scientific reasoning (SciResearcher), to cost-reducing virtual worlds (LiteResearcher) and offline training (OffSeeker).",
        "representative_paper_refs": [
            refmap["2607.21461"],  # AREX
            refmap["2605.16217"],  # Argus
            refmap["2605.01489"],  # SciResearcher
            refmap["2604.17931"],  # LiteResearcher
            refmap["2601.18467"],  # OffSeeker
        ],
    },
    {
        "name": "Self-Distillation & Hindsight for Agentic RL",
        "core_idea": "Convert sparse outcome rewards into dense supervision via self-distillation and hindsight techniques without external critics. Sub-routes include recursive Bayesian belief updates (AgentOPSD), trajectory-relative hindsight allocation (TRIAL), and hindsight critique of failed trajectories (HindSearch).",
        "representative_paper_refs": [
            refmap["2608.05987"],  # AgentOPSD
            refmap["2608.07371"],  # TRIAL
            refmap["2608.01597"],  # HindSearch
        ],
    },
    {
        "name": "RL for Tool Use in Agents",
        "core_idea": "Apply reinforcement learning to optimize tool-use policies in LLM agents, deciding when and how to invoke tools within reasoning. Foundational works establish RL viability (ReTool) and sample efficiency (Tool-R1), with frontier work on evidence-aligned policy optimization (Contextual Information Policy Optimization) and guided retrieval training (Search-GRT).",
        "representative_paper_refs": [
            refmap["2504.11536"],  # ReTool
            refmap["2509.12867"],  # Tool-R1
            refmap["2608.06128"],  # Contextual Information Policy Optimization
            refmap["2608.00974"],  # Search-GRT
        ],
    },
]

print(f"Approach families: {len(families)}")

# === FINDINGS (cross-paper judgments) ===
findings = [
    {
        "statement": "Outcome-only GRPO suffers from advantage collapse on long-horizon search tasks: as trajectories lengthen, group-relative advantages collapse toward zero, eliminating the learning signal. This is a shared failure mode diagnosed independently by the advantage-collapse analysis and addressed by CIGPO (information-gain injection), RSPO (reward-swap), and the credit-assignment family, indicating that naive outcome-only GRPO is insufficient for multi-turn search agents.",
        "approach_refs": [],  # will fill after family creation
        "sources": [
            {"paper_ref": refmap["2605.21125"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2607.16244"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2607.04713"], "relation": "SUPPORTS"},
        ],
    },
    {
        "statement": "Credit assignment is the central bottleneck for search-agent RL: across all analyzed routes, the core challenge is converting a sparse terminal outcome (answer correctness) into dense per-step or per-turn supervision. The diversity of solutions—answer-backtracking, pivot identification, graph distance, provenance tracing, role classification, and counterfactual siblings—indicates no single credit-assignment method dominates; the choice depends on whether ground-truth answers, graphs, or sibling rollouts are available.",
        "sources": [
            {"paper_ref": refmap["2608.05102"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2605.09287"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2605.29697"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2607.11172"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2606.32017"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2606.29476"], "relation": "SUPPORTS"},
        ],
    },
    {
        "statement": "Self-play with evidence grounding enables supervision-free search-agent training, but grounding quality determines task quality: SearchMaster's evidence-chain grounding and CoEvoKG's knowledge-graph grounding both show that the grounding substrate (evidence chains vs. KGs) directly affects whether generated tasks are solvable and verifiable. Ungrounded self-play (Search Self-play) risks trivial or unsolvable tasks, while grounded variants trade off coverage against verifiability.",
        "sources": [
            {"paper_ref": refmap["2608.01822"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2608.01904"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2510.18821"], "relation": "QUALIFIES"},
        ],
    },
    {
        "statement": "Online RL is not strictly necessary for deep-research agents: OffSeeker demonstrates that fully offline training with curated trajectories can rival costly online RL loops, and LiteResearcher's virtual world reduces external API costs. This challenges the prevailing assumption that online interaction is required, opening a cost-quality trade-off axis between online, offline, and virtual-world training.",
        "sources": [
            {"paper_ref": refmap["2601.18467"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2604.17931"], "relation": "SUPPORTS"},
        ],
    },
    {
        "statement": "Process reward models and credit assignment are converging toward the same goal via different means: PRM-based routes (Verifiable Process Rewards, OASES) train explicit reward models, while credit-assignment routes (ABSeeker, CRAFT) derive credit structurally from trajectories or siblings. Both aim to densify the supervision signal, but PRM routes add a model that can drift, while structural routes are model-free but depend on trajectory structure assumptions.",
        "sources": [
            {"paper_ref": refmap["2605.10325"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2604.03675"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2608.05102"], "relation": "QUALIFIES"},
            {"paper_ref": refmap["2606.29476"], "relation": "QUALIFIES"},
        ],
    },
    {
        "statement": "Search-depth and evidence-density rewards are emerging as efficiency regulators: SearchMaster's search-depth reward and Search-R2's evidence-density reward both penalize inefficient browsing, indicating a shared recognition that answer correctness alone is insufficient—search efficiency must be explicitly rewarded to prevent over-search behavior in trained agents.",
        "sources": [
            {"paper_ref": refmap["2608.01822"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2602.03647"], "relation": "SUPPORTS"},
        ],
    },
]

print(f"Findings: {len(findings)}")

# === OPEN PROBLEMS (field-level) ===
open_problems = [
    {
        "statement": "Verifier reliability in self-play: all self-play routes depend on a Verifier (frozen or co-evolving) to judge task correctness. A weak or drifting Verifier propagates incorrect supervision, but the field lacks a principled method for detecting Verifier failure during training and recovering from it without external ground truth.",
        "sources": [
            {"paper_ref": refmap["2608.01822"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2608.01904"], "relation": "SUPPORTS"},
        ],
    },
    {
        "statement": "Credit assignment without ground-truth answers: most credit-assignment methods (ABSeeker, Verifiable Process Rewards) require ground-truth answers or symbolic oracles, limiting applicability to verifiable domains. Extending credit assignment to open-ended, non-verifiable research tasks where no ground truth exists remains an open problem.",
        "sources": [
            {"paper_ref": refmap["2608.05102"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2605.10325"], "relation": "SUPPORTS"},
        ],
    },
    {
        "statement": "Long-horizon context management under RL: as research horizons grow, context windows fill and must be compressed (AREX) or managed via memory (CoEvoKG, skill evolution). How to train RL policies that jointly optimize answer quality and context/memory management without reward interference is unresolved.",
        "sources": [
            {"paper_ref": refmap["2607.21461"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2608.01904"], "relation": "SUPPORTS"},
        ],
    },
    {
        "statement": "Standardized evaluation of search-agent RL: the field lacks a unified benchmark that evaluates both answer quality and search efficiency (query count, token cost, evidence precision) under controlled conditions, making cross-method comparison unreliable.",
        "sources": [
            {"paper_ref": refmap["2608.01822"], "relation": "QUALIFIES"},
            {"paper_ref": refmap["2603.01152"], "relation": "SUPPORTS"},
        ],
    },
    {
        "statement": "Reward hacking and over-search in RL-trained search agents: as agents learn to maximize correctness rewards, they may develop over-search behaviors (excessive querying) or exploit reward shortcuts. Search-depth rewards partially address this, but a general defense against reward hacking in multi-turn search RL is missing.",
        "sources": [
            {"paper_ref": refmap["2608.01822"], "relation": "SUPPORTS"},
            {"paper_ref": refmap["2510.26575"], "relation": "SUPPORTS"},
        ],
    },
]

print(f"Open problems: {len(open_problems)}")

# === INVESTIGATION GAPS (run-level) ===
gaps = [
    {
        "description": "Empirical head-to-head comparison of credit-assignment sub-routes (answer-backtracking vs. graph-distance vs. provenance vs. counterfactual) on a common search-agent benchmark is not available in the retained corpus; cross-method comparison is currently only inferable from per-paper benchmarks.",
    },
    {
        "description": "The interaction between self-play task generation and credit assignment is under-explored: whether grounded self-play tasks produce better credit signals than externally provided tasks has not been directly studied in the retained papers.",
    },
    {
        "description": "Frontier 2026 work on evidence-aligned policy optimization (Contextual Information Policy Optimization) and guided retrieval training (Search-GRT) introduces new reward designs whose relationship to the credit-assignment and PRM routes needs explicit synthesis; the current analyses treat them as separate routes without cross-route comparison.",
    },
]

print(f"Investigation gaps: {len(gaps)}")

# Save all landscape inputs
import os
os.makedirs('.e2e/landscape', exist_ok=True)

for i, fam in enumerate(families):
    with open(f'.e2e/landscape/family_{i}.json', 'w', encoding='utf-8') as f:
        json.dump(fam, f, ensure_ascii=False, indent=1)

for i, finding in enumerate(findings):
    with open(f'.e2e/landscape/finding_{i}.json', 'w', encoding='utf-8') as f:
        json.dump(finding, f, ensure_ascii=False, indent=1)

for i, op in enumerate(open_problems):
    with open(f'.e2e/landscape/openproblem_{i}.json', 'w', encoding='utf-8') as f:
        json.dump(op, f, ensure_ascii=False, indent=1)

for i, gap in enumerate(gaps):
    with open(f'.e2e/landscape/gap_{i}.json', 'w', encoding='utf-8') as f:
        json.dump(gap, f, ensure_ascii=False, indent=1)

print("Saved all landscape inputs to .e2e/landscape/")
