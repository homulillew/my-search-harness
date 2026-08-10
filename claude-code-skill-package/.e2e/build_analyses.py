#!/usr/bin/env python3
"""FIXTURE / MECHANICAL SMOKE ONLY — not semantic Research Loop proof.

This script bulk-builds put-paper-analysis inputs for a fixed candidate pool. It exists
to exercise the harness command surface and produce a populated run for mechanical
end-to-end smoke, NOT to demonstrate an adaptive research loop. The real research loop
interleaves discovery, primary-source reading, synthesis, and reassessment per turn; this
batch builder instead stages search → retain-all → batch-analysis, which is the exact
anti-pattern P0-D forbids. Treat its output as fixture data, not as evidence that the
loop was run correctly.

Analyses below were drafted from a mix of abstracts, one read source, and WebFetch
summaries — i.e. discovery metadata, not uniform primary-source evidence. A real run must
satisfy the Primary Evidence Gate (inspect-source / read-source before detailed analysis)
for every representative paper before put-paper-analysis.
"""
import json

refmap = json.load(open('.e2e/paper_refs.json', encoding='utf-8'))
hits = {h['arxiv_id']: h for h in json.load(open('.e2e/candidates_merged.json', encoding='utf-8'))}

# Analyses keyed by arxiv_id. Content grounded in abstracts + read sources.
analyses = {
    "2608.01822": {  # SearchMaster - read full Method section
        "summary": "SearchMaster proposes a grounded and regulated self-play framework for training search agents. A single policy pi_theta simultaneously acts as Proposer (generating tasks from seed documents with evidence chains) and Solver (answering tasks via browser tools search/open/find), while a frozen Verifier judges correctness. The framework uses evidence-chain-grounded task generation and a search-depth reward to regulate browsing efficiency, preventing the agent from excessive inefficient querying.",
        "relevance_to_run": "Directly defines the self-play route for search-agent training, which is a core technical route of this survey. Its evidence-chain grounding and search-depth regulation address the key training/reward design requirement and the frontier-work requirement (2026-08).",
        "contributions": [
            "Single-policy self-play where the same model serves as both Proposer and Solver, eliminating the need for separate specialized models",
            "Evidence-Chain-Grounded (ECG) task generation that ties each generated task to a verifiable evidence chain in the document collection",
            "Search-depth reward component that penalizes inefficient browsing by rewarding correct answers achieved with fewer unique search queries",
            "Frozen Verifier design that provides stable judgment signals across self-play iterations",
        ],
        "key_results": [
            "Demonstrates that self-play with evidence-chain grounding produces solvable, verifiable tasks without human-labeled data",
            "Search-depth reward reduces average query count while maintaining answer accuracy, addressing the over-search problem",
            "The single-policy design enables parameter sharing between task generation and task solving, improving sample efficiency",
        ],
        "limitations": [
            "Self-play quality depends on the frozen Verifier's reliability; a weak Verifier can propagate incorrect judgment signals",
            "Evidence chains are constrained to the document collection D, potentially limiting coverage of topics outside D",
            "The Proposer-Solver role sharing may create a coupling where improvements in one role do not directly transfer to the other",
        ],
    },
    "2510.18821": {
        "summary": "Search Self-play proposes a self-play framework that pushes the frontier of agent capability without external supervision. It generates search tasks from unlabeled data and uses the agent's own search behavior to define training signals, enabling capability improvement without human annotations.",
        "relevance_to_run": "Foundational work on the self-play route for search agents; establishes that self-play can drive frontier capability without labels, a key motivation for the self-play technical route.",
        "contributions": [
            "Self-play training paradigm for search agents requiring no external supervision or labeled data",
            "Task generation from unlabeled documents enabling scalable training data",
        ],
        "key_results": [
            "Shows self-play can push agent capability frontier without human annotations",
        ],
        "limitations": [
            "Self-play without grounding risks generating trivially solvable or unsolvable tasks",
        ],
    },
    "2607.29468": {
        "summary": "Self-Play Meets Skill Evolution proposes a self-evolving search agent that converts procedural failures into reusable skills written to a memory bank, creating a bidirectional learning loop between task generation and skill evolution. Skills accumulate across episodes and guide future search behavior.",
        "relevance_to_run": "Extends the self-play route with skill memory, representing the self-evolving sub-route. Directly relevant to the self-play and self-evolution technical routes.",
        "contributions": [
            "Bidirectional learning loop coupling task generation with skill evolution",
            "Procedural-failure-to-skill conversion mechanism for accumulating reusable search strategies",
        ],
        "key_results": [
            "Skill memory improves search efficiency by reusing successful strategies across episodes",
        ],
        "limitations": [
            "Skill bank quality depends on the diversity of encountered failures",
        ],
    },
    "2608.01904": {
        "summary": "CoEvoKG introduces a framework using knowledge graphs as persistent memory for both task generation and reward computation, enabling closed-loop agent evolution. The knowledge graph stores evidence and generates training tasks, creating a co-evolutionary dynamic between the agent and the KG.",
        "relevance_to_run": "Represents the knowledge-graph-grounded self-evolution route; the KG-as-memory and KG-as-reward-design addresses the reward design and self-evolution requirements.",
        "contributions": [
            "Knowledge graph as persistent memory substrate for search agents",
            "KG-driven task generation and reward computation for closed-loop evolution",
        ],
        "key_results": [
            "KG-grounded rewards provide structured, verifiable training signal",
        ],
        "limitations": [
            "KG construction and maintenance overhead",
        ],
    },
    "2608.05102": {
        "summary": "ABSeeker trains long-horizon search agents via answer-backtracked credit assignment. It traces back from ground-truth answers to score intermediate search steps, enabling efficient credit assignment over long trajectories where outcome-only rewards are too sparse.",
        "relevance_to_run": "Defines the answer-backtracking credit-assignment route, a major technical route for search-agent training. Directly addresses the key training/reward design requirement.",
        "contributions": [
            "Answer-backtracking mechanism that propagates credit from ground-truth answers to intermediate steps",
            "Step-level scoring for long-horizon search trajectories overcoming outcome-reward sparsity",
        ],
        "key_results": [
            "Backtracked credit enables training on long-horizon tasks where outcome-only RL fails",
        ],
        "limitations": [
            "Requires ground-truth answers for backtracking, limiting applicability to verifiable tasks",
        ],
    },
    "2605.09287": {
        "summary": "PiCA defines process rewards as success probabilities dependent on historical context, identifying pivot steps as information peaks that guide search agents toward correct answers. Pivot steps are the turns where the most critical information is acquired.",
        "relevance_to_run": "Defines the pivot-based credit-assignment route; the information-peak concept is a discrimination criterion for the credit-assignment technical route.",
        "contributions": [
            "Pivot-step identification as information peaks in search trajectories",
            "Context-dependent process reward formulation",
        ],
        "key_results": [
            "Pivot-based rewards focus credit on the most informative steps",
        ],
        "limitations": [
            "Pivot identification may be noisy without accurate information-peak detection",
        ],
    },
    "2605.29697": {
        "summary": "Beyond Trajectory Rewards introduces a graph-distance contribution reward that scores search steps based on proximity to the answer node within a latent entity-relation graph, providing step-level credit without external process supervision.",
        "relevance_to_run": "Graph-based credit-assignment route; the graph-distance formulation is a distinct discrimination criterion within credit assignment.",
        "contributions": [
            "Graph-distance contribution reward using latent entity-relation graphs",
            "Step-level credit without external process labels",
        ],
        "key_results": [
            "Graph proximity provides a geometric credit signal correlated with answer progress",
        ],
        "limitations": [
            "Graph construction quality affects credit accuracy",
        ],
    },
    "2607.11172": {
        "summary": "STAMP traces first-exposure citations to credit supporting actions via sign-preserving advantage modulation. It identifies which search actions first introduced evidence later used in the answer, and modulates advantages while preserving their sign.",
        "relevance_to_run": "Provenance-based credit-assignment route; the first-exposure-citation concept is a discrimination criterion for credit assignment.",
        "contributions": [
            "First-exposure citation tracing for provenance-based credit",
            "Sign-preserving advantage modulation that avoids reward sign flipping",
        ],
        "key_results": [
            "Provenance tracing credits the specific actions that introduced useful evidence",
        ],
        "limitations": [
            "Citation tracing requires reliable evidence-to-action mapping",
        ],
    },
    "2604.14267": {
        "summary": "Enhancing LLM-based Search Agents via Contribution Weighted GRPO integrates process supervision into GRPO by using an LLM judge to score retrieval utility and reasoning correctness, subsequently rescaling outcome advantages along the trajectory based on per-step contributions.",
        "relevance_to_run": "Integrates process supervision with GRPO for search agents; relevant to both credit-assignment and GRPO-variant routes.",
        "contributions": [
            "LLM-judge-based contribution scoring for retrieval and reasoning",
            "Contribution-weighted advantage rescaling within GRPO",
        ],
        "key_results": [
            "Combining process and outcome signals improves search-agent performance over outcome-only GRPO",
        ],
        "limitations": [
            "LLM judge introduces its own biases and computational cost",
        ],
    },
    "2606.32017": {
        "summary": "TRIAGE proposes role-typed credit assignment that corrects standard GRPO's outcome-only signals by classifying agent actions into progress, exploration, or regression categories, applying role-specific credit rather than uniform outcome credit.",
        "relevance_to_run": "Role-typed credit-assignment route; the action-role taxonomy is a discrimination criterion for credit assignment.",
        "contributions": [
            "Action-role classification (progress/exploration/regression) for credit assignment",
            "Correction of GRPO's uniform outcome credit via role-specific signals",
        ],
        "key_results": [
            "Role-typed credit reduces redundant actions by distinguishing productive from regressive steps",
        ],
        "limitations": [
            "Role classification requires a reliable classifier",
        ],
    },
    "2606.29476": {
        "summary": "CRAFT uses importance-weighted sibling rollouts and asymmetric KL control to provide signed, counterfactual token-level credit at near-zero extra cost, enabling fine-grained credit assignment from free sibling rollouts.",
        "relevance_to_run": "Counterfactual credit-assignment route using sibling rollouts; relevant to credit-assignment and self-distillation routes.",
        "contributions": [
            "Importance-weighted sibling rollouts for counterfactual credit",
            "Asymmetric KL control providing signed token-level credit",
        ],
        "key_results": [
            "Sibling-based counterfactual credit is near-zero-cost and signed",
        ],
        "limitations": [
            "Sibling rollout quality depends on policy stochasticity",
        ],
    },
    "2605.10325": {
        "summary": "Verifiable Process Rewards for Agentic Reasoning converts symbolic or algorithmic oracles into dense turn-level supervision, solving long-horizon credit assignment challenges by providing verifiable per-step rewards rather than heuristic process labels.",
        "relevance_to_run": "Defines the verifiable-process-reward route; the oracle-to-reward conversion is a key reward-design mechanism.",
        "contributions": [
            "Conversion of symbolic/algorithmic oracles into dense turn-level rewards",
            "Verifiable process rewards avoiding heuristic label noise",
        ],
        "key_results": [
            "Oracle-derived rewards are verifiable and dense, addressing long-horizon sparsity",
        ],
        "limitations": [
            "Requires a symbolic or algorithmic oracle, limiting applicability to domains with verifiable correctness",
        ],
    },
    "2604.03675": {
        "summary": "OASES co-trains search policies and state evaluators to derive outcome-aligned process rewards that adapt to evolving agent behavior, providing reliable supervision as the policy improves.",
        "relevance_to_run": "Co-training route for search-evaluation; the outcome-alignment mechanism is a reward-design contribution.",
        "contributions": [
            "Joint co-training of search policy and state evaluator",
            "Outcome-aligned process rewards that adapt to policy evolution",
        ],
        "key_results": [
            "Co-trained evaluators stay aligned with outcomes as the policy improves",
        ],
        "limitations": [
            "Co-training stability and evaluator-policy coupling risks",
        ],
    },
    "2601.04888": {
        "summary": "SmartSearch employs dual-level credit assessment via process rewards to selectively refine low-quality intermediate search queries through a structured curriculum learning framework, improving query quality over training.",
        "relevance_to_run": "Process-reward-guided query refinement route; relevant to credit assignment and curriculum design.",
        "contributions": [
            "Dual-level credit assessment for query quality",
            "Curriculum-based selective refinement of low-quality queries",
        ],
        "key_results": [
            "Selective refinement improves intermediate query quality",
        ],
        "limitations": [
            "Curriculum design requires careful difficulty scheduling",
        ],
    },
    "2510.26575": {
        "summary": "InfoFlow addresses low reward density in deep search by decomposing tasks, injecting failure-guided hints, and using a dual-agent architecture to compress and refine exploration trajectories, increasing the density of useful training signal.",
        "relevance_to_run": "Reward-density-optimization route; directly addresses the sparse-reward problem in deep search.",
        "contributions": [
            "Task decomposition and failure-guided hint injection for reward density",
            "Dual-agent architecture for trajectory compression and refinement",
        ],
        "key_results": [
            "Reward density optimization mitigates sparse-signal problems in deep search",
        ],
        "limitations": [
            "Hint injection may bias exploration toward known failure modes",
        ],
    },
    "2602.03647": {
        "summary": "Search-R2 uses an Actor-Refiner framework with a hybrid reward coupling outcome correctness and dense process rewards to quantify and improve the density of retrieved evidence during search-integrated reasoning.",
        "relevance_to_run": "Actor-Refiner route with hybrid reward; relevant to reward design and search-integrated reasoning.",
        "contributions": [
            "Actor-Refiner collaboration for search-integrated reasoning",
            "Hybrid reward coupling outcome correctness with evidence density",
        ],
        "key_results": [
            "Evidence-density reward improves the informativeness of retrieved content",
        ],
        "limitations": [
            "Evidence-density metric design affects reward quality",
        ],
    },
    "2607.04713": {
        "summary": "RSPO leverages dense process rewards to guide training while guaranteeing consistency with true outcome rewards via a swapping mechanism, ensuring that process-reward optimization does not diverge from outcome objectives.",
        "relevance_to_run": "GRPO-variant route with reward-swapping consistency guarantee; relevant to reward design and policy optimization.",
        "contributions": [
            "Reward-swap mechanism guaranteeing process-outcome reward consistency",
            "Dense process reward guidance within multi-turn agent training",
        ],
        "key_results": [
            "Swapping guarantee prevents process rewards from diverging from outcomes",
        ],
        "limitations": [
            "Swapping mechanism adds implementation complexity",
        ],
    },
    "2607.16244": {
        "summary": "CIGPO injects per-turn information-gain rewards to prevent reward-variance collapse and zero-advantage lock-in in outcome-only GRPO, providing a dense signal for multi-turn evidence-reading agents.",
        "relevance_to_run": "GRPO-variant route addressing advantage collapse; relevant to reward design and the diagnosis of GRPO failure modes.",
        "contributions": [
            "Per-turn information-gain reward injection",
            "Prevention of reward-variance collapse and zero-advantage lock-in",
        ],
        "key_results": [
            "Information-gain rewards restore advantage variance in long multi-turn trajectories",
        ],
        "limitations": [
            "Information-gain estimation may be noisy",
        ],
    },
    "2605.21125": {
        "summary": "Advantage Collapse in GRPO diagnoses a failure mode where group-relative advantages collapse to zero as training progresses, reducing effective learning signal. It analyzes the causes and implications for multi-turn agent training.",
        "relevance_to_run": "Diagnostic work on GRPO failure modes; provides the theoretical basis for understanding why naive GRPO fails on long-horizon agents, relevant to route trade-offs.",
        "contributions": [
            "Formal diagnosis of advantage collapse in group-relative policy optimization",
            "Analysis of causes and implications for multi-turn agent training",
        ],
        "key_results": [
            "Identifies advantage collapse as a key failure mode in GRPO for long-horizon tasks",
        ],
        "limitations": [
            "Diagnostic focus; proposed mitigations may require further empirical validation",
        ],
    },
    "2607.21461": {
        "summary": "AREX presents a recursively self-improving research agent that alternates between evidence gathering and constraint-wise auditing to refine answers over long horizons, using compressed context updates and long-horizon RL to maintain coherence.",
        "relevance_to_run": "Defines the recursive-self-improvement route for deep-research agents; directly relevant to the deep-research technical route.",
        "contributions": [
            "Recursive evidence-gathering and constraint-auditing alternation",
            "Compressed context updates for long-horizon coherence",
            "Long-horizon RL training for research agents",
        ],
        "key_results": [
            "Recursive refinement improves answer quality over long research horizons",
        ],
        "limitations": [
            "Constraint auditing adds computational overhead per iteration",
        ],
    },
    "2605.16217": {
        "summary": "Argus deploys a Searcher and Navigator that cooperate via a shared evidence graph, using RL to optimize dispatch and synthesis while supporting parallel rollouts without retraining, enabling scalable deep research.",
        "relevance_to_run": "Evidence-graph-based deep-research route; the Searcher-Navigator cooperation is a distinct architecture within deep-research agents.",
        "contributions": [
            "Searcher-Navigator cooperation via shared evidence graph",
            "RL-optimized dispatch and synthesis with parallel rollout support",
        ],
        "key_results": [
            "Shared evidence graph enables parallel rollouts without retraining",
        ],
        "limitations": [
            "Evidence-graph synchronization across parallel rollouts adds complexity",
        ],
    },
    "2605.01489": {
        "summary": "SciResearcher introduces an automated framework for synthesizing scientific tasks and trains an 8B agent using agentic RL to achieve state-of-the-art frontier scientific reasoning performance.",
        "relevance_to_run": "Scientific-domain deep-research route; demonstrates domain-specific task synthesis and agentic RL for frontier reasoning.",
        "contributions": [
            "Automated scientific task synthesis framework",
            "8B agent trained via agentic RL for frontier scientific reasoning",
        ],
        "key_results": [
            "Achieves SOTA frontier scientific reasoning with an 8B model",
        ],
        "limitations": [
            "Task synthesis tailored to scientific domain may not transfer to general research",
        ],
    },
    "2604.17931": {
        "summary": "LiteResearcher enables scalable RL training by constructing a lightweight virtual world that mirrors real-world search dynamics without relying on expensive external API calls, reducing training cost.",
        "relevance_to_run": "Virtual-world training route for deep-research agents; addresses the cost/scalability trade-off in deep-research RL.",
        "contributions": [
            "Lightweight virtual world mirroring real-world search dynamics",
            "Scalable RL training without external API costs",
        ],
        "key_results": [
            "Virtual world reduces training cost while preserving search dynamics",
        ],
        "limitations": [
            "Virtual world fidelity to real search environments may be imperfect",
        ],
    },
    "2601.18467": {
        "summary": "OffSeeker demonstrates that fully offline training with curated trajectories and a task synthesis framework can rival models trained with costly online RL loops, challenging the assumption that online RL is necessary for deep-research agents.",
        "relevance_to_run": "Offline-RL route for deep-research agents; provides a key trade-off between online and offline training, relevant to route trade-offs.",
        "contributions": [
            "Offline training framework with curated trajectories for deep research",
            "Task synthesis enabling offline-only training",
        ],
        "key_results": [
            "Offline training rivals online RL at lower cost",
        ],
        "limitations": [
            "Offline trajectory quality and diversity are critical",
        ],
    },
    "2608.05987": {
        "summary": "AgentOPSD employs recursive Bayesian belief updates to convert sparse outcome rewards into dense turn-level credit without a critic, providing a critic-free self-distillation method for agentic RL.",
        "relevance_to_run": "Critic-free self-distillation route; relevant to credit assignment and self-distillation technical routes.",
        "contributions": [
            "Recursive Bayesian belief updates for turn-level credit",
            "Critic-free self-distillation for agentic RL",
        ],
        "key_results": [
            "Critic-free design reduces model requirements while providing dense credit",
        ],
        "limitations": [
            "Bayesian belief update accuracy depends on reward distribution assumptions",
        ],
    },
    "2608.07371": {
        "summary": "TRIAL allocates hindsight signals across decision turns via a unified scoring protocol, consistently outperforming GRPO benchmarks by leveraging trajectory-relative hindsight distillation.",
        "relevance_to_run": "Hindsight-distillation route; relevant to credit assignment and self-distillation.",
        "contributions": [
            "Trajectory-relative hindsight signal allocation across turns",
            "Unified scoring protocol outperforming GRPO",
        ],
        "key_results": [
            "Hindsight distillation outperforms standard GRPO on agentic tasks",
        ],
        "limitations": [
            "Hindsight signals require successful trajectories to distill from",
        ],
    },
    "2608.06128": {
        "summary": "Contextual Information Policy Optimization proposes an evidence-oriented RL framework that aligns policy optimization with external evidence to reduce confirmation bias in search agents, ensuring that search behavior is driven by evidence rather than prior beliefs.",
        "relevance_to_run": "Frontier 2026 work on evidence-aligned policy optimization; relevant to reward design and the frontier-work requirement.",
        "contributions": [
            "Evidence-oriented policy optimization reducing confirmation bias",
            "Alignment of RL optimization with external evidence signals",
        ],
        "key_results": [
            "Evidence alignment reduces confirmation bias in search agent behavior",
        ],
        "limitations": [
            "Evidence-alignment mechanism design is non-trivial",
        ],
    },
    "2608.00974": {
        "summary": "Search-GRT introduces Guided Retrieval Training, which restricts RL retrieval to ground-truth documents to mitigate sparse rewards and improve multi-hop QA performance, providing a curriculum-like guided training signal.",
        "relevance_to_run": "Frontier 2026 work on guided-retrieval training; relevant to reward design and curriculum learning for search agents.",
        "contributions": [
            "Guided Retrieval Training restricting RL to ground-truth documents",
            "Sparse-reward mitigation via retrieval guidance",
        ],
        "key_results": [
            "Guided retrieval improves multi-hop QA by reducing reward sparsity",
        ],
        "limitations": [
            "Requires ground-truth document labels, limiting scalability",
        ],
    },
    "2504.11536": {
        "summary": "ReTool applies reinforcement learning for strategic tool use in LLMs, training the model to decide when and how to use tools within a reasoning trajectory, establishing RL as a viable approach for tool-use policy optimization.",
        "relevance_to_run": "Foundational work on RL for tool use; relevant to the tool-use-RL technical route and the key training/reward design requirement.",
        "contributions": [
            "RL framework for strategic tool-use decisions in LLMs",
            "Integration of tool use into the RL reward and policy optimization loop",
        ],
        "key_results": [
            "Demonstrates RL can optimize tool-use policies in LLMs",
        ],
        "limitations": [
            "Tool-use reward design is task-specific",
        ],
    },
    "2509.12867": {
        "summary": "Tool-R1 proposes sample-efficient reinforcement learning for agentic tool use, reducing the number of rollouts needed to learn effective tool-use policies through improved reward shaping and trajectory utilization.",
        "relevance_to_run": "Sample-efficient tool-use-RL route; addresses the efficiency trade-off in tool-use training.",
        "contributions": [
            "Sample-efficient RL for agentic tool use",
            "Reward shaping and trajectory utilization for efficiency",
        ],
        "key_results": [
            "Reduces rollout count needed for effective tool-use policies",
        ],
        "limitations": [
            "Sample efficiency gains may vary across tool complexity",
        ],
    },
}

print(f"Analyses prepared: {len(analyses)}")

# Build individual analysis input files
import os
os.makedirs('.e2e/analyses', exist_ok=True)
count = 0
for aid, a in analyses.items():
    if aid not in refmap:
        print(f"WARNING: {aid} not in refmap, skipping")
        continue
    inp = {
        "paper_ref": refmap[aid],
        "summary": a["summary"],
        "relevance_to_run": a["relevance_to_run"],
        "contributions": a.get("contributions", []),
        "key_results": a.get("key_results", []),
        "limitations": a.get("limitations", []),
    }
    fn = f".e2e/analyses/{aid.replace('.','_')}.json"
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump(inp, f, ensure_ascii=False, indent=1)
    count += 1
print(f"Wrote {count} analysis input files to .e2e/analyses/")
