"""Operational helper for the fresh-context acceptance follow-up.

This lives with ignored runtime output, not product code.  It intentionally uses
only the public capability facade and writes no raw source payloads to disk.
"""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum
import json
import os
import sys

from my_search_harness.runtime import (
    LocalV1Runtime,
    PutPaperAnalysis,
    ResearchMutationBatch,
)
from my_search_harness.domain import (
    LiteratureSource,
    PaperAnalysis,
    PaperResearchStatus,
    SourceLocator,
    SourceRelation,
)


WORKSPACE = "workspace/final-live-e2e/20260810T002408Z"
RUN_ID = "run_5fa1b3e5-cf40-4b40-bf6d-4d988920fe79"


def json_default(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=repr)
    return str(value)


def dump(value: object) -> None:
    print(json.dumps(asdict(value), ensure_ascii=False, indent=2, default=json_default))


def locator(section: str) -> SourceLocator:
    return SourceLocator(kind="section", value=section)


def literature_source(
    paper_ref: str,
    section: str,
    relation: SourceRelation = SourceRelation.SUPPORTS,
) -> LiteratureSource:
    return LiteratureSource(
        paper_ref=paper_ref,
        relation=relation,
        locator=locator(section),
    )


def main() -> None:
    runtime = LocalV1Runtime.from_deepxiv_env(WORKSPACE)
    command = sys.argv[1] if len(sys.argv) > 1 else "view"
    view = runtime.researcher.view(RUN_ID)
    if command == "search-retain":
        query = sys.argv[2]
        result = runtime.researcher.search_papers(
            RUN_ID, view.state_revision, query, limit=10
        )
        for index, hit in enumerate(result.hits):
            print(
                f"[{index}] {hit.title} | arXiv={hit.arxiv_id} | "
                f"year={hit.publication_year}"
            )
        answer = input("retain indices (comma-separated, blank for none): ").strip()
        if not answer:
            print(f"search_revision={result.state_revision}; retained=0")
            return
        indices = tuple(int(value.strip()) for value in answer.split(","))
        retained = runtime.researcher.retain_papers(
            RUN_ID,
            result.state_revision,
            tuple(result.hits[index] for index in indices),
        )
        print(
            f"search_revision={result.state_revision}; "
            f"retain_revision={retained.state_revision}; "
            f"paper_refs={','.join(retained.paper_refs)}"
        )
        return
    if command == "outline":
        result = runtime.researcher.inspect_source(
            RUN_ID, view.state_revision, sys.argv[2]
        )
        print(f"state_revision={result.state_revision}")
        for entry in result.outline.sections:
            print(f"{entry.title}\t{entry.locator.kind}\t{entry.locator.value}")
        return
    if command == "read":
        result = runtime.researcher.read_source(
            RUN_ID,
            view.state_revision,
            sys.argv[2],
            SourceLocator(kind="section", value=sys.argv[3]),
        )
        print(f"state_revision={result.state_revision}")
        print(result.source_content.content)
        return
    if command == "read-many":
        revision = view.state_revision
        for section in sys.argv[3:]:
            result = runtime.researcher.read_source(
                RUN_ID,
                revision,
                sys.argv[2],
                SourceLocator(kind="section", value=section),
            )
            revision = result.state_revision
            print(f"\n===== {section} | state_revision={revision} =====\n")
            print(result.source_content.content)
        return
    if command == "synthesize":
        paper_analyses = {
            "paper_a84b0325-0a16-4191-9486-1994d5ab75d9": PaperAnalysis(
                summary="Cross-Layer Attention (CLA) is a model-architecture intervention that computes KV projections in only a subset of layers and reuses those activations in adjacent layers. Its sharing factor is orthogonal to MHA, GQA, and MQA and requires native model training.",
                relevance_to_run="It establishes cross-layer sharing as a mechanism distinct from inference-only eviction or quantization: it reduces the number of layer-specific KV tensors, but does not directly reduce the attention kernel's per-layer reads.",
                contributions=(
                    "Defines configurable KV sharing across consecutive transformer layers and explains its composition with MHA, GQA, and MQA.",
                    "Maps sharing factor to cache reduction while identifying pipeline-parallel communication constraints and unchanged core-attention bandwidth.",
                    "Trains 1B- and 3B-parameter models from scratch to compare accuracy-memory Pareto frontiers.",
                ),
                key_results=(
                    "CLA reduces KV cache memory approximately by its sharing factor; MQA-CLA2 halves cache bytes per token relative to the matched-head MQA model.",
                    "At 1B and 3B scales, MQA-CLA2 is within less than 1% perplexity change of matched-head MQA in the tested regimes and improves the Pareto frontier relative to shrinking head dimension alone.",
                    "Sharing factors above two and non-uniform dense-front/back patterns produce worse accuracy-memory trade-offs than uniform CLA2 in the reported ablations.",
                ),
                limitations=(
                    "The evidence is from models trained from scratch at 1B and 3B parameters with 2K training sequences, not retrofits to production long-context models.",
                    "End-to-end long-context serving latency and throughput are explicitly left for future work.",
                    "Shared KV must still be reread at every consuming layer, so cache capacity falls without a direct reduction in core attention bandwidth or latency.",
                ),
                key_locators=(locator("Cross-Layer Attention"), locator("Pretraining Experiments"), locator("Discussion \\& Future Work")),
            ),
            "paper_bc121393-2a30-4f5f-b1c7-8a4a82ecd524": PaperAnalysis(
                summary="MLKV shares KV heads both within and across layers, reducing the layer dimension from all layers to a smaller number of KV-producing layer groups. The paper applies the design by uptraining small Pythia models rather than using an inference-only transformation.",
                relevance_to_run="It independently supports the architectural cross-layer-sharing route while supplying a cautionary counterpoint: theoretical cache savings do not automatically improve throughput or preserve quality.",
                contributions=(
                    "Generalizes MQA/GQA sharing from heads within a layer to KV heads shared among groups of layers.",
                    "Derives cache size as proportional to the number of KV-producing layer groups and KV head groups.",
                    "Measures accuracy, memory scaling, maximum batch size, and throughput after model uptraining.",
                ),
                key_results=(
                    "Memory scales linearly with the chosen total KV head count; in the small-model setup, the baseline reaches batch 48 while extreme MLKV variants reach batches around 940-1100.",
                    "MLKV generally underperforms GQA or MQA at the same KV-head count, and MLKV-1 degrades severely; moderate MLKV-6/12 settings offer the better measured trade-offs.",
                    "The generalized implementation shows no significant throughput speedup because shared cache contents are still fetched at every layer.",
                ),
                limitations=(
                    "Experiments cover only decoder-only 160M and 410M models, with limited downstream task diversity.",
                    "Models are uptrained rather than pretrained natively with MLKV, leaving training-procedure effects unresolved.",
                    "No optimized kernel demonstrates that the large capacity gains translate to per-token latency or throughput gains.",
                ),
                key_locators=(locator("Multi-Layer Key-Value (MLKV)"), locator("Results"), locator("Limitations")),
            ),
            "paper_f4b2e8fb-2153-4553-a2ae-7b3b0a7c501c": PaperAnalysis(
                summary="This paper proposes a Transformer with a predefined 2048-token KV capacity and a dynamic update mechanism intended to keep memory and inference time constant beyond that length.",
                relevance_to_run="It is a candidate trained bounded-state route, but the accessible primary source is too underspecified to support route-level generalization or quantitative comparison.",
                contributions=(
                    "States a fixed-capacity KV design goal and a dynamic cache update mechanism.",
                    "Reports a 1B-parameter experiment intended to compare memory, speed, and BLEU after the 2048-token capacity is reached.",
                ),
                key_results=(
                    "The paper claims constant memory and relatively constant inference speed beyond a 2048-token capacity.",
                    "It reports BLEU as comparable to a traditional cache, but the accessible result is incomplete and lacks enough detail for a reliable effect-size comparison.",
                ),
                limitations=(
                    "The accessible source does not specify the dynamic-update algorithm at reproducible depth.",
                    "Baseline configuration, task construction, complete numerical results, and quality evaluation are insufficiently reported.",
                    "The evidence should not be used as a representative primary basis for a major route.",
                ),
                key_locators=(locator("Introduction"), locator("Experimental Results")),
            ),
            "paper_32d63710-6b3b-4dcd-af13-16eb8470de87": PaperAnalysis(
                summary="XKV is an inference-only token-eviction method that measures application-specific, layer-varying importance distributions, then uses a lightweight mini-prefill and greedy optimization to allocate different cache budgets across layers.",
                relevance_to_run="It shows that layer-adaptive budget allocation is a policy within token-selective retention, not a separate representation mechanism; it also exposes application sampling and proxy-model overhead.",
                contributions=(
                    "Formalizes Dynamic Differences of Importance Distribution across layers and links a retained-information proxy to final accuracy.",
                    "Uses a lightweight no-cache mini-prefill plus greedy optimization to assign layer-specific capacities under an accuracy constraint.",
                    "Amortizes allocation by sampling application tasks in advance rather than recalibrating every request.",
                ),
                key_results=(
                    "Across 14 LongBench datasets on Llama-3.1-8B-Instruct and one RTX A6000, XKV reports 61.6% average KV memory reduction, at least 12.8 percentage points more than the best tested competitor under its accuracy bounds.",
                    "On NarrativeQA, cache memory falls from 4.00 GB to 1.54 GB, per-task time from 7.18 s to 3.40 s, and maximum batch size rises from 8 to 20; reported throughput improves up to 5.2x.",
                    "At extremely low 1.2%-1.6% retained ratios, all methods lose accuracy, while XKV is best on most of the reported datasets rather than lossless.",
                ),
                limitations=(
                    "Allocation depends on application-specific samples and statistics collected with a lightweight proxy model, so distribution shift can invalidate the budget.",
                    "Evaluation is limited to one model family, one GPU type, and selected LongBench tasks.",
                    "The method changes allocation across layers but still inherits irreversible token-eviction failure modes.",
                ),
                key_locators=(locator("Introduction"), locator("Experiments")),
            ),
            "paper_044ada55-7479-4b4b-a0fe-d790b292cecf": PaperAnalysis(
                summary="MiniKV is an inference-only co-design that combines persistent prefill heavy-hitter selection, a recent window, layer-wise budget allocation, asymmetric INT2 KV quantization, and fused selective-attention/dequantization kernels.",
                relevance_to_run="It directly tests composition between token eviction and numerical compression and shows that successful composition depends on selected-token distributions, cache budget, task, and kernel support.",
                contributions=(
                    "Enables sub-channel key quantization after eviction by selecting a persistent heavy-hitter set at the end of prefill.",
                    "Combines medium-rate token eviction with 2-bit KV quantization and optional pyramid layer allocation.",
                    "Adds a two-pass selective FlashAttention-style prefill kernel and fused decode dequantization to keep auxiliary memory linear.",
                ),
                key_results=(
                    "On LongBench with Llama-2 and Mistral models, MiniKV-Pyramid reaches 98.5% of full-model average for Llama-2-7B at a 0.33 GB cache in the stated 4096-prompt/512-generation comparison.",
                    "Long-context experiments show high eviction rates can fail; GSM8K requires roughly a 90% adaptive token budget to match full-cache reasoning accuracy.",
                    "System tests on one A100 show lower peak memory and higher throughput, but the selective prefill kernel is slower than FlashAttention in the reported microbenchmark while enabling attention-score collection without quadratic materialization.",
                ),
                limitations=(
                    "Persistent heavy hitters are observed mainly at medium budgets; the assumption weakens at tiny budgets and long-context quality drops under aggressive eviction.",
                    "LongBench generations are capped below 512 tokens, limiting evidence about long self-generated reasoning.",
                    "Composition is not plug-and-play: replacing H2O selection with SnapKV before KIVI drops the reported LongBench score from about 35 to 32.",
                ),
                key_locators=(locator("Method"), locator("Experiments"), locator("Limitations")),
            ),
            "paper_ecaebb02-f0c6-4b86-bcb5-3a2e9bbd38f2": PaperAnalysis(
                summary="LMCache is a serving-layer system for exact KV reuse across GPU, CPU, disk, remote, and disaggregated prefill/decode tiers. It groups paged caches into transfer chunks, overlaps layer-wise I/O with compute, prefetches asynchronously, and minimizes duplicate copies.",
                relevance_to_run="It expands the memory-hierarchy route beyond encoded transfer: the cache values stay exact, while capacity, hit rate, transfer granularity, and compute-I/O overlap determine TTFT and throughput.",
                contributions=(
                    "Defines a standardized connector and token-indexed cache layer across vLLM/SGLang and heterogeneous backends.",
                    "Batches small pages into larger chunks, pipelines layer loads, prefetches queued requests, and supports dynamic offloading with minimal copies.",
                    "Evaluates CPU offload, remote centralized storage, real traces, and prefill/decode disaggregation.",
                ),
                key_results=(
                    "On H100 serving setups, LMCache reports 1.9-8.1x lower TTFT and 2.3-14x higher throughput than its strongest tested baseline in single-node offload workloads, with model- and load-specific conditions.",
                    "Remote centralized storage improves throughput 1.3-3x in the tested 15 Gbps setup, and chunked CPU loading reaches 400 Gbps versus 88 Gbps for native vLLM offload.",
                    "At 32 Gbps on B200, loading beats recomputation only beyond roughly 256K input tokens; at 64/128 Gbps it wins across tested lengths.",
                ),
                limitations=(
                    "Benefits require cache reuse and sufficient lower-tier capacity; cold or low-hit workloads do not avoid prefill.",
                    "The load-versus-recompute crossover is bandwidth-, model-, and context-dependent, so static offloading can hurt latency.",
                    "Several baselines and production lessons are version- or deployment-specific, including black-box commercial comparisons and a 500 GB CPU-cache budget.",
                ),
                key_locators=(locator("Overview of LMCACHE"), locator("Performance Optimizations"), locator("Evaluation"), locator("Real-World Lessons and Experience")),
            ),
            "paper_364b2f1f-88b3-4f48-9a5f-cc93f911ef71": PaperAnalysis(
                summary="PagedAttention/vLLM separates logical KV blocks from non-contiguous physical GPU blocks, allocating them on demand and using copy-on-write sharing for prompts and beam branches. It preserves exact KV values while reducing reservation and fragmentation waste.",
                relevance_to_run="It establishes serving-time memory management as a route separate from lossy tensor compression: it improves usable capacity, batching, and sharing without changing model quality.",
                contributions=(
                    "Introduces an attention kernel that follows block tables over non-contiguous KV storage.",
                    "Applies virtual-memory ideas to dynamic block allocation, prompt/beam copy-on-write sharing, swapping, and recomputation.",
                    "Integrates paged cache management with continuous batching and distributed tensor-parallel execution.",
                ),
                key_results=(
                    "The paper reports effective memory utilization as low as 20.4% for contiguous preallocation baselines, while PagedAttention limits per-request waste to the final block.",
                    "On A100 OPT/LLaMA serving traces, vLLM sustains 1.7-2.7x higher request rates than the infeasible Orca oracle and 2.7-8x over maximum reservation at comparable latency.",
                    "Copy-on-write sharing saves 37.6-55.2% cache memory for beam search on the reported Alpaca setting and raises shared-prefix throughput up to 3.58x.",
                ),
                limitations=(
                    "Indirection and non-contiguous access require a custom fused attention kernel and introduce overhead.",
                    "Benefits shrink when workloads are compute-bound, such as short sequences with abundant memory.",
                    "Preemption uses coarse sequence-level eviction and must choose between CPU swapping and recomputation based on platform bandwidth and compute.",
                ),
                key_locators=(locator("3. Memory Challenges in LLM Serving"), locator("4. Method"), locator("6. Evaluation"), locator("8. Discussion")),
            ),
            "paper_c6e14a84-d38d-41c2-8ac3-2a7f6969a3b3": PaperAnalysis(
                summary="Hold Onto That Thought independently evaluates token-eviction strategies on long generated reasoning traces across conventional and reasoning-tuned 7B-14B models, multiple reasoning categories, and fixed cache budgets.",
                relevance_to_run="It supplies missing evidence that quality under compression cannot be inferred from prompt-only long-context tests: micro-budgets can collapse reasoning, lengthen output, and even induce nontermination.",
                contributions=(
                    "Benchmarks H2O, StreamingLLM, KNorm, R-KV, a decoding-updated SnapKV variant, and ShadowKV over 128-512 token budgets.",
                    "Separates non-reasoning and reasoning models across reading, logic, commonsense, and math tasks with up to 2048 generated tokens.",
                    "Relates accuracy to attention loss and measures the hidden effect of compression on generation length and throughput.",
                ),
                key_results=(
                    "Very small budgets cause large and method-dependent accuracy collapses; on DeepSeek-R1-Distill-Qwen-7B GSM8K, H2O rises from 0.21 at budget 128 to 0.52 at 512, while full cache is 0.70.",
                    "Attention-based H2O and the decoding SnapKV variant dominate other eviction heuristics on reasoning models, but usually still trail full cache; no one method dominates the non-reasoning model.",
                    "Aggressive eviction can produce longer or circular reasoning traces, so nominal memory savings can increase total inference compute and fail to terminate.",
                ),
                limitations=(
                    "The study covers token eviction rather than low-bit quantization or architecture changes.",
                    "Its SnapKV-D variant periodically updates during decode and is not the original fixed-prefill SnapKV algorithm.",
                    "Most dataset results use 100 examples per seed and a 2048-output cap on a specific A6000/kvpress implementation.",
                ),
                key_locators=(locator("Preliminaries"), locator("Experiments \\& Analysis"), locator("Conclusion")),
            ),
            "paper_04ebb6b3-c160-4e38-adae-ac28e5bfeb7d": PaperAnalysis(
                summary="KVFundaBench evaluates six fundamental capability categories under token-level KV eviction, including knowledge, arithmetic, commonsense, code, safety, and roughly 4K-token long generation; it also proposes ShotKV to preserve coherent in-context examples.",
                relevance_to_run="It independently demonstrates task-, prompt-, and model-dependent failure thresholds and provides direct long-generation evidence that popular unified eviction policies degrade sharply under aggressive compression.",
                contributions=(
                    "Builds a multi-capability benchmark over four model variants and six eviction methods rather than only long-prompt retrieval.",
                    "Analyzes sink-removed attention distributions to explain why arithmetic reasoning depends on a broader set of non-sink tokens.",
                    "Introduces separate prefill/decode compression that preserves whole high-scoring shots as semantic chunks.",
                ),
                key_results=(
                    "Tasks are mostly stable above a 40% retained ratio, but arithmetic, code, and safety drop sharply under more aggressive compression; sensitivity also varies by model type and prompt shot count.",
                    "On LG-GSM8K with about 4K generated tokens, StreamingLLM, H2O, and PyramidInfer lose more than 20 percentage points below a 30% retained ratio.",
                    "ShotKV retains 47.33% accuracy at 40% versus 46.00% full cache on LG-GSM8K and substantially exceeds the tested unified eviction baselines at 25%-30%, under the paper's setup.",
                ),
                limitations=(
                    "The benchmark studies eviction methods, not numerical quantization, exact offload, or architecture-changing cache reduction.",
                    "Experiments use selected 7B-8B models and one A40 environment, so exact thresholds are not universal.",
                    "Its conclusion that a reasoning-tuned model is more robust in averaged tasks differs from studies of self-generated reasoning traces, underscoring benchmark dependence.",
                ),
                key_locators=(locator("Benchmark Design"), locator("ShotKV"), locator("Conclusion")),
            ),
        }
        mutation = runtime.researcher.apply_research_mutation(
            RUN_ID,
            view.state_revision,
            ResearchMutationBatch(
                puts=tuple(
                    PutPaperAnalysis(paper_ref=paper_ref, analysis=analysis)
                    for paper_ref, analysis in paper_analyses.items()
                )
            ),
        )
        revision = mutation.state_revision
        retired = runtime.researcher.set_paper_research_status(
            RUN_ID,
            revision,
            "paper_f4b2e8fb-2153-4553-a2ae-7b3b0a7c501c",
            PaperResearchStatus.RETIRED,
        )
        revision = retired.state_revision

        selection_ref = "approach_e93e0d98-1e40-4eb8-8180-374ffcf9cedc"
        quant_ref = "approach_b566f492-f54c-455b-92ba-42f1e902f3ce"
        hierarchy_ref = "approach_1aa1ad25-f3d9-4369-ae7f-7eaad31a3509"
        updated = runtime.researcher.put_approach_family(
            RUN_ID,
            revision,
            name="Token-selective retention and bounded attention",
            core_idea="Reduce cache length by retaining task-, attention-, or semantic-chunk-important tokens plus local/sink context; selection can be fixed after prefill, updated during decode, or allocated unevenly across layers.",
            representative_paper_refs=frozenset({
                "paper_1b9422ce-9d25-4067-b427-900af360a482",
                "paper_a7559efd-8df9-46e8-9b90-3554e02405df",
                "paper_e18584f4-3b7d-4375-b4b6-3f6bf5a24296",
                "paper_32d63710-6b3b-4dcd-af13-16eb8470de87",
                "paper_044ada55-7479-4b4b-a0fe-d790b292cecf",
            }),
            approach_ref=selection_ref,
        )
        revision = updated.state_revision
        updated = runtime.researcher.put_approach_family(
            RUN_ID,
            revision,
            name="Low-bit numerical KV representation",
            core_idea="Reduce bytes per retained KV element with key/value-aware quantization, residual high-precision regions, outlier protection, calibration, and compressed attention kernels; hybrid systems may quantize an already selected subset.",
            representative_paper_refs=frozenset({
                "paper_78cb78ea-e9cf-432a-afa4-75dc56fb890c",
                "paper_8d0f73cb-928c-474e-b88c-373ed39179c8",
                "paper_044ada55-7479-4b4b-a0fe-d790b292cecf",
            }),
            approach_ref=quant_ref,
        )
        revision = updated.state_revision
        updated = runtime.researcher.put_approach_family(
            RUN_ID,
            revision,
            name="Serving memory management, KV reuse, and hierarchy",
            core_idea="Preserve exact or encoded KV state while eliminating allocation waste, sharing common prefixes, avoiding repeated prefill, and moving cache through GPU/CPU/disk/network tiers according to bandwidth, reuse, and SLOs.",
            representative_paper_refs=frozenset({
                "paper_25c10025-1f10-42d2-b517-dc754d1bc6f2",
                "paper_ecaebb02-f0c6-4b86-bcb5-3a2e9bbd38f2",
                "paper_364b2f1f-88b3-4f48-9a5f-cc93f911ef71",
            }),
            approach_ref=hierarchy_ref,
        )
        revision = updated.state_revision
        architecture = runtime.researcher.put_approach_family(
            RUN_ID,
            revision,
            name="Architectural KV head and layer sharing",
            core_idea="Reduce how many distinct KV projections and cache tensors a model creates by sharing KV heads within or across layers. This changes the trained architecture and capacity-quality frontier rather than compressing an existing cache at inference time.",
            representative_paper_refs=frozenset({
                "paper_a84b0325-0a16-4191-9486-1994d5ab75d9",
                "paper_bc121393-2a30-4f5f-b1c7-8a4a82ecd524",
            }),
        )
        revision = architecture.state_revision
        architecture_ref = architecture.entity_ref

        finding_specs = (
            (
                "Architectural sharing is a distinct training-time route: CLA and MLKV reduce the layer dimension of the cache and compose with MQA/GQA head sharing, but unchanged per-layer cache reads mean capacity reduction alone does not guarantee decode latency or throughput gains.",
                frozenset({architecture_ref}),
                frozenset({
                    literature_source("paper_a84b0325-0a16-4191-9486-1994d5ab75d9", "Cross-Layer Attention"),
                    literature_source("paper_bc121393-2a30-4f5f-b1c7-8a4a82ecd524", "Results", SourceRelation.QUALIFIES),
                }),
            ),
            (
                "Evidence for cross-layer sharing is not uniform: natively pretrained CLA2 improves the tested accuracy-memory Pareto frontier at 1B/3B scale, whereas uptrained 160M/410M MLKV generally underperforms MQA/GQA at equal KV-head count and extreme sharing becomes unusable.",
                frozenset({architecture_ref}),
                frozenset({
                    literature_source("paper_a84b0325-0a16-4191-9486-1994d5ab75d9", "Pretraining Experiments"),
                    literature_source("paper_bc121393-2a30-4f5f-b1c7-8a4a82ecd524", "Results", SourceRelation.QUALIFIES),
                    literature_source("paper_bc121393-2a30-4f5f-b1c7-8a4a82ecd524", "Limitations", SourceRelation.QUALIFIES),
                }),
            ),
            (
                "Serving memory management reduces a different cost than lossy compression: PagedAttention removes reservation/fragmentation and enables exact prefix sharing inside GPU memory, LMCache extends exact reuse and movement across storage tiers, and CacheGen reduces bytes transferred when cross-machine bandwidth is the bottleneck.",
                frozenset({hierarchy_ref}),
                frozenset({
                    literature_source("paper_364b2f1f-88b3-4f48-9a5f-cc93f911ef71", "4. Method"),
                    literature_source("paper_ecaebb02-f0c6-4b86-bcb5-3a2e9bbd38f2", "Overview of LMCACHE"),
                    literature_source("paper_25c10025-1f10-42d2-b517-dc754d1bc6f2", "CacheGen Design"),
                }),
            ),
            (
                "Exact reuse/offload gains are conditional: paged allocation helps most when serving is memory-bound, while lower-tier loading helps only with sufficient reuse and when transfer beats recomputation; LMCache's reported crossover moves with bandwidth and context length.",
                frozenset({hierarchy_ref}),
                frozenset({
                    literature_source("paper_364b2f1f-88b3-4f48-9a5f-cc93f911ef71", "8. Discussion", SourceRelation.QUALIFIES),
                    literature_source("paper_ecaebb02-f0c6-4b86-bcb5-3a2e9bbd38f2", "Evaluation", SourceRelation.QUALIFIES),
                }),
            ),
            (
                "Layer-adaptive allocation is a policy dimension inside token selection rather than a separate compression primitive: XKV calibrates application-specific per-layer budgets, whereas MiniKV's pyramid policy combines layer allocation with persistent-token selection and INT2 representation.",
                frozenset({selection_ref, quant_ref}),
                frozenset({
                    literature_source("paper_32d63710-6b3b-4dcd-af13-16eb8470de87", "Introduction"),
                    literature_source("paper_044ada55-7479-4b4b-a0fe-d790b292cecf", "Method"),
                }),
            ),
            (
                "Hybrid compression is not mechanically composable: MiniKV makes H2O-style persistent selection plus KIVI-style INT2 quantization work through co-designed grouping and kernels, yet substituting SnapKV selection causes a reported LongBench drop from about 35 to 32 because selected tokens differ in quantization sensitivity.",
                frozenset({selection_ref, quant_ref}),
                frozenset({
                    literature_source("paper_044ada55-7479-4b4b-a0fe-d790b292cecf", "Method"),
                    literature_source("paper_044ada55-7479-4b4b-a0fe-d790b292cecf", "Limitations", SourceRelation.QUALIFIES),
                }),
            ),
            (
                "Independent benchmarks show that cache quality is task-, model-, prompt-, budget-, and generation-regime-dependent: arithmetic, code, safety, and long self-generated reasoning can degrade far more than retrieval or knowledge tasks, and aggressive eviction may lengthen or prevent termination of reasoning traces.",
                frozenset({selection_ref}),
                frozenset({
                    literature_source("paper_04ebb6b3-c160-4e38-adae-ac28e5bfeb7d", "Benchmark Design"),
                    literature_source("paper_c6e14a84-d38d-41c2-8ac3-2a7f6969a3b3", "Experiments \\& Analysis"),
                    literature_source("paper_044ada55-7479-4b4b-a0fe-d790b292cecf", "Experiments", SourceRelation.QUALIFIES),
                }),
            ),
            (
                "The literature disagrees on whether reasoning-tuned models are intrinsically more robust: KVFundaBench reports stronger averaged robustness for one distilled reasoning model, while long-generation evaluation finds most eviction methods still substantially trail full cache; the difference follows task mix, output horizon, budget, and eviction policy rather than a universal model property.",
                frozenset({selection_ref}),
                frozenset({
                    literature_source("paper_04ebb6b3-c160-4e38-adae-ac28e5bfeb7d", "Benchmark Design", SourceRelation.SUPPORTS),
                    literature_source("paper_c6e14a84-d38d-41c2-8ac3-2a7f6969a3b3", "Experiments \\& Analysis", SourceRelation.CHALLENGES),
                }),
            ),
            (
                "Deployment boundary is now explicit: H2O, StreamingLLM, SnapKV, XKV, MiniKV, KIVI, KVQuant, PagedAttention, CacheGen, and LMCache operate on existing weights, while CLA/MLKV require pretraining or uptraining and alter the model architecture; the two classes can in principle be layered but need joint evaluation.",
                frozenset({selection_ref, quant_ref, hierarchy_ref, architecture_ref}),
                frozenset({
                    literature_source("paper_32d63710-6b3b-4dcd-af13-16eb8470de87", "Introduction"),
                    literature_source("paper_044ada55-7479-4b4b-a0fe-d790b292cecf", "Method"),
                    literature_source("paper_a84b0325-0a16-4191-9486-1994d5ab75d9", "Cross-Layer Attention", SourceRelation.QUALIFIES),
                    literature_source("paper_bc121393-2a30-4f5f-b1c7-8a4a82ecd524", "Limitations", SourceRelation.QUALIFIES),
                }),
            ),
        )
        finding_refs = []
        for statement, approach_refs, sources in finding_specs:
            finding = runtime.researcher.put_landscape_finding(
                RUN_ID,
                revision,
                statement=statement,
                approach_refs=approach_refs,
                sources=sources,
            )
            revision = finding.state_revision
            finding_refs.append(finding.entity_ref)

        updated_problem = runtime.researcher.put_open_problem(
            RUN_ID,
            revision,
            problem_ref="problem_5e452a59-92ab-40b4-a3ee-aa20e646d924",
            statement="How can a bounded cache adapt to saliency shifts across prefill and long generation, preserve semantic chunks and distant evidence, and avoid the longer or nonterminating reasoning traces observed under aggressive eviction?",
            approach_refs=frozenset({selection_ref}),
            sources=frozenset({
                literature_source("paper_a7559efd-8df9-46e8-9b90-3554e02405df", "Appendix D Long-Range Benchmark Evaluation"),
                literature_source("paper_e18584f4-3b7d-4375-b4b6-3f6bf5a24296", "SnapKV"),
                literature_source("paper_c6e14a84-d38d-41c2-8ac3-2a7f6969a3b3", "Experiments \\& Analysis"),
                literature_source("paper_04ebb6b3-c160-4e38-adae-ac28e5bfeb7d", "ShotKV"),
            }),
        )
        revision = updated_problem.state_revision
        updated_problem = runtime.researcher.put_open_problem(
            RUN_ID,
            revision,
            problem_ref="problem_ae7f9575-3621-4b8d-985a-c5fbbbd60e4f",
            statement="How should a serving controller jointly choose paging, cache encoding, storage tier, prefetch, eviction, and recomputation under changing bandwidth, cache-hit rates, concurrent load, and TTFT/ITL SLOs?",
            approach_refs=frozenset({hierarchy_ref}),
            sources=frozenset({
                literature_source("paper_25c10025-1f10-42d2-b517-dc754d1bc6f2", "CacheGen Design"),
                literature_source("paper_25c10025-1f10-42d2-b517-dc754d1bc6f2", "Evaluation", SourceRelation.QUALIFIES),
                literature_source("paper_ecaebb02-f0c6-4b86-bcb5-3a2e9bbd38f2", "Evaluation", SourceRelation.QUALIFIES),
                literature_source("paper_364b2f1f-88b3-4f48-9a5f-cc93f911ef71", "4. Method"),
            }),
        )
        revision = updated_problem.state_revision
        new_problem = runtime.researcher.put_open_problem(
            RUN_ID,
            revision,
            statement="Can architectural KV sharing be validated on modern large long-context models with end-to-end kernels and serving workloads, and then combined with inference-time quantization or selection without compounding quality loss?",
            approach_refs=frozenset({architecture_ref, selection_ref, quant_ref}),
            sources=frozenset({
                literature_source("paper_a84b0325-0a16-4191-9486-1994d5ab75d9", "Discussion \\& Future Work"),
                literature_source("paper_bc121393-2a30-4f5f-b1c7-8a4a82ecd524", "Limitations"),
                literature_source("paper_044ada55-7479-4b4b-a0fe-d790b292cecf", "Limitations", SourceRelation.QUALIFIES),
            }),
        )
        revision = new_problem.state_revision
        new_problem_ref = new_problem.entity_ref

        gap_resolutions = (
            (
                "gap_09b27824-b2ab-4b3b-a68f-2497425c6187",
                "Resolved by analyzing CLA and MLKV and adding the architectural head/layer-sharing family. Both require training or uptraining and reduce distinct KV tensors, unlike inference-only compression; both also show that cache capacity reduction need not reduce per-layer bandwidth. The predefined-capacity paper was analyzed but retired because its method and results are not sufficiently specified for representative use.",
            ),
            (
                "gap_c572bedb-1c96-4de5-bcc7-b09c86f2578a",
                "Resolved by targeted DeepXiv discovery and analysis of PagedAttention/vLLM plus LMCache. The memory-hierarchy family now distinguishes exact paged allocation/prefix sharing, heterogeneous exact reuse/offload, and CacheGen's encoded transfer; findings record their workload, bandwidth, and hit-rate conditions.",
            ),
            (
                "gap_0597a4b8-8903-4422-b74e-d394f727bfd4",
                "Resolved by analyzing XKV and MiniKV. Layer-adaptive budgets are classified as a policy inside token selection, while MiniKV is an explicit selection-plus-INT2 composition. New findings capture calibration costs, medium-budget assumptions, kernel co-design, and the failed SnapKV-plus-KIVI composition.",
            ),
            (
                "gap_95549d7e-02c6-48f8-b2ae-aa4f6398da23",
                "Resolved through two targeted, independent primary evaluations: Hold Onto That Thought tests up to 2048 generated reasoning tokens and identifies accuracy collapse, longer traces, and nontermination at small budgets; KVFundaBench covers six capabilities and roughly 4K-token generation, showing task-, model-, prompt-, and policy-specific degradation and a material disagreement about reasoning-model robustness.",
            ),
        )
        for gap_ref, resolution in gap_resolutions:
            result = runtime.researcher.resolve_investigation_gap(
                RUN_ID, revision, gap_ref, resolution
            )
            revision = result.state_revision

        print(json.dumps({
            "final_revision": revision,
            "architecture_ref": architecture_ref,
            "new_finding_refs": finding_refs,
            "new_problem_ref": new_problem_ref,
            "analyzed_in_batch": len(paper_analyses),
            "retired_paper_ref": "paper_f4b2e8fb-2153-4553-a2ae-7b3b0a7c501c",
            "resolved_gap_count": len(gap_resolutions),
        }, ensure_ascii=False, indent=2))
        return
    if command == "verify":
        gap_refs = (
            "gap_09b27824-b2ab-4b3b-a68f-2497425c6187",
            "gap_c572bedb-1c96-4de5-bcc7-b09c86f2578a",
            "gap_0597a4b8-8903-4422-b74e-d394f727bfd4",
            "gap_95549d7e-02c6-48f8-b2ae-aa4f6398da23",
        )
        paper_refs = tuple(item.ref for item in view.papers.items)
        inspected = runtime.researcher.inspect(
            RUN_ID,
            view.state_revision,
            gap_refs + ("approach_95517d76-bb4d-44d5-8d01-190178c69e1c",) + paper_refs,
        )
        papers = [item.value for item in inspected.objects if item.kind == "paper"]
        gaps = [item.value for item in inspected.objects if item.kind == "investigation_gap"]
        print(json.dumps({
            "state_revision": view.state_revision,
            "lifecycle": view.lifecycle.value,
            "contract_revision": view.contract.contract_revision,
            "counts": {
                "approach_families": view.approach_families.total,
                "findings": view.findings.total,
                "open_problems": view.open_problems.total,
                "open_gaps": view.open_gaps.total,
                "paper_records": view.papers.total,
                "active_papers": sum(p.research_status is PaperResearchStatus.ACTIVE for p in papers),
                "retired_papers": sum(p.research_status is PaperResearchStatus.RETIRED for p in papers),
                "analyzed_papers": sum(p.analysis is not None for p in papers),
                "active_analyzed_papers": sum(
                    p.research_status is PaperResearchStatus.ACTIVE and p.analysis is not None
                    for p in papers
                ),
            },
            "resource_usage": dict(view.resources.usage),
            "resolved_gaps": {
                gap.id: gap.resolution for gap in gaps
            },
            "all_sections_complete": all(
                page.continuation is None
                for page in (
                    view.approach_families,
                    view.findings,
                    view.open_problems,
                    view.open_gaps,
                    view.papers,
                )
            ),
        }, ensure_ascii=False, indent=2))
        return
    if command != "view":
        raise SystemExit(f"unsupported command: {command}")
    print(f"credential_available={bool(os.environ.get('DEEPXIV_TOKEN'))}")
    print("RESEARCH_VIEW")
    dump(view)
    refs = tuple(
        item.ref
        for page in (
            view.approach_families,
            view.findings,
            view.open_problems,
            view.open_gaps,
            view.papers,
        )
        for item in page.items
    )
    for start in range(0, len(refs), 20):
        print(f"INSPECT_BATCH={start}")
        dump(runtime.researcher.inspect(RUN_ID, view.state_revision, refs[start : start + 20]))


if __name__ == "__main__":
    main()
