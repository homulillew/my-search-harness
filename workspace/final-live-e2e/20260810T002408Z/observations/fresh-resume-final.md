# Fresh-context research resume note

- Recorded: 2026-08-10T00:40:54Z
- Run: `run_5fa1b3e5-cf40-4b40-bf6d-4d988920fe79`
- Authoritative state: revision **111**, contract revision **1**, lifecycle **RESEARCH**
- Current corpus: **15** paper records; **14 active and analyzed**, **1 analyzed then retired** for insufficient method/result detail
- Landscape: **4** approach families, **15** findings, **4** open problems, **0** open investigation gaps
- Runtime accounting: **6** searches total (**2** follow-up), **15** source outlines, **44** targeted source reads

## Follow-up DeepXiv searches

1. `PagedAttention vLLM prefix cache RadixAttention LLM serving KV cache memory management offloading`
   - Retained and analyzed: *Efficient Memory Management for Large Language Model Serving with PagedAttention* (`2309.06180`).
2. `KV cache compression benchmark reasoning long generation quality degradation eviction quantization failure`
   - Retained and analyzed: *Hold Onto That Thought: Assessing KV Cache Compression On Reasoning* (`2512.12008`) and *Can LLMs Maintain Fundamental Abilities under KV Cache Compression?* (`2502.01941`).

## Resolved gaps and updated route map

1. **Architectural change:** CLA and MLKV establish trained/uptrained head-and-layer sharing as a fourth route. It reduces distinct KV tensors but does not itself eliminate per-layer reads. The weak predefined-capacity paper was analyzed and retired.
2. **Serving reuse/offload:** PagedAttention separates exact paged allocation and prefix sharing from LMCache's exact multi-tier reuse/offload and CacheGen's lossy transfer encoding. Benefits depend on memory-boundedness, reuse, bandwidth, and load-versus-recompute crossover.
3. **Layer-adaptive hybrids:** XKV is classified as layer-aware budget allocation inside token selection; MiniKV is a co-designed eviction-plus-INT2 composition. Its failed SnapKV-plus-KIVI variant shows that route composition is not plug-and-play.
4. **Quality failures:** Two independent evaluations now cover fundamental abilities and long self-generated reasoning. They show task/model/prompt/budget dependence, sharp degradation at aggressive budgets, longer or nonterminating reasoning traces, and a benchmark-dependent disagreement over whether reasoning-tuned models are more robust.

## Resume boundary

The follow-up research phase is complete, but completion has **not** been requested. Continue from revision 111 in RESEARCH. Native State and audit preserve search-attempt counts but not query strings; the queries remain recoverable from ignored operational observations, so this run was not blocked, though losing those observations would reduce resume fidelity. Raw source payloads were not persisted. No product-code change or blocking implementation bug was required.
