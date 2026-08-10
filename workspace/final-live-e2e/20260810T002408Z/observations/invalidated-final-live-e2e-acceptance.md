# Final Large-Scale Live E2E Acceptance

## Environment

- Runtime baseline: GitHub `main` at `338683592c30d024a428c8cb7ab527997936d351` (`feat: integrate report writing guideline`). PR #15 was reviewed, passed 275 tests plus static/format/secret gates, marked Ready, squash-merged, and synchronized before this run.
- DeepXiv client: `deepxiv-sdk` 0.3.1.
- Writing guideline source: `.vibe/REPORT_WRITING_GUIDE.md`, loaded as UTF-8 through the formal `LocalV1Runtime.report_pipeline(..., writing_guideline_path=...)` composition path.
- Isolated ignored workspace: `workspace/final-live-e2e/20260810T002408Z/`. No file below this path is tracked by Git.
- Product changes during live acceptance: none.

## Run

- Run ID: `run_5fa1b3e5-cf40-4b40-bf6d-4d988920fe79`.
- Topic: LLM 推理中的 KV Cache 优化技术路线.
- Final state revision: 132.
- Lifecycle: `CLOSED`.
- Outcome: `COMPLETE`.
- Contract revision: 1.
- Required artifact: `REPORT`.
- Delivery basis: the single completed `PASS` CompletionCheck under Contract revision 1.
- Report SHA-256: `2bacc44f805c61158ab6aef69a1820530466a27f7dc747aeb501dd83339bcaaa`; the content digest, artifact metadata, current DeliveryBasis, and final Contract revision were consistent during deterministic delivery validation.

## Search

Six purposeful searches returned 60 hits. The query sequence was not predeclared; each later round responded to the current route map or an explicit Investigation Gap.

| Round | Query | Purpose | Hits |
| --- | --- | --- | ---: |
| 1 | `LLM KV cache optimization inference` | Broad discovery without assuming a final taxonomy; identify candidate mechanisms and primary papers. | 10 |
| 2 | `LLM KV cache eviction heavy hitter attention sink token selection H2O StreamingLLM SnapKV` | Fill the newly visible token-selection route and distinguish online heavy hitters, bounded streaming, and prompt-aware selection. | 10 |
| 3 | `LLM KV cache quantization KIVI KVQuant 2-bit per-channel per-token quality long context` | Establish the numerical-compression route, key/value asymmetry, quality conditions, and an intentional duplicate-identity observation. | 10 |
| 4 | `LLM KV cache architectural reduction multi query grouped query attention cross layer sharing latent attention MLA MLKV CLA` | Resolve whether training-time head/layer sharing is mechanistically distinct from inference-only compression. | 10 |
| 5 | `PagedAttention vLLM prefix cache RadixAttention LLM serving KV cache memory management offloading` | Close the serving-level reuse/offload gap by finding an exact paging/prefix-sharing primary system alongside LMCache and CacheGen. | 10 |
| 6 | `KV cache compression benchmark reasoning long generation quality degradation eviction quantization failure` | Close the quality-evidence gap with independent reasoning and long-generation failure studies. | 10 |

The first four rounds contained 39 unique candidates among 40 hits. The two fresh-context rounds contained 20 unique candidates with no cross-round duplicate; two of those had appeared in the earlier candidate pool. The complete six-round pool therefore contained 57 unique candidates among 60 hits.

Search results remained ephemeral observations. Only semantically selected papers were retained. MiniKV (`2411.18077`) appeared in both the broad and quantization rounds; deterministic arXiv identity normalization reused the exact existing Paper rather than creating a duplicate. Later search overlap did not fuzzy-merge titles.

The strategy evolved as intended:

1. Broad discovery exposed token selection, quantization, bounded-state architecture, and serving reuse as candidates.
2. Three targeted rounds established primary mechanisms and created a provisional three-route map.
3. Four explicit Gaps recorded weak architectural, serving, hybrid-composition, and quality-failure evidence.
4. A fresh Researcher resumed at the midpoint, analyzed already retained route candidates, searched only the unresolved serving and quality gaps, and refined the map to four routes.
5. All four Gaps were resolved before Completion was requested.

## Corpus

Fifteen unique papers were retained and inspected. All fifteen received run-specific PaperAnalysis; fourteen remained `ACTIVE`. One bounded-cache paper was analyzed and then `RETIRED` because its accessible method, baselines, and results were too underspecified to serve as route-level evidence.

The fourteen active core papers were:

| Primary paper | Year | arXiv ID | Role in the accepted landscape |
| --- | ---: | --- | --- |
| H2O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models | 2023 | `2306.14048` | Online heavy-hitter plus recency eviction. |
| Efficient Streaming Language Models with Attention Sinks | 2023 | `2309.17453` | Bounded streaming through attention sinks plus recent tokens. |
| Efficient Memory Management for Large Language Model Serving with PagedAttention | 2023 | `2309.06180` | Exact paged allocation, copy-on-write sharing, and serving capacity. |
| CacheGen: KV Cache Compression and Streaming for Fast Large Language Model Serving | 2023 | `2310.07240` | Encoded cross-machine cache transfer under bandwidth constraints. |
| KVQuant: Towards 10 Million Context Length LLM Inference with KV Cache Quantization | 2024 | `2401.18079` | Calibrated low-bit KV, sparse outliers, and sink protection. |
| KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache | 2024 | `2402.02750` | Tuning-free asymmetric key/value quantization with a recent residual. |
| SnapKV: LLM Knows What You are Looking for Before Generation | 2024 | `2404.14469` | Prompt-aware static selection using an observation window. |
| Reducing Transformer Key-Value Cache Size with Cross-Layer Attention | 2024 | `2405.12981` | Natively trained cross-layer KV sharing. |
| MLKV: Multi-Layer Key-Value Heads for Memory Efficient Transformer Decoding | 2024 | `2406.09297` | Uptrained head-and-layer sharing and its throughput limitation. |
| MiniKV: Pushing the Limits of LLM Inference via 2-Bit Layer-Discriminative KV Cache | 2024 | `2411.18077` | Co-designed token selection, layer budgets, INT2, and kernels. |
| XKV: Personalized KV Cache Memory Reduction for Long-Context LLM Inference | 2024 | `2412.05896` | Application-specific layer-adaptive cache budgets. |
| Can LLMs Maintain Fundamental Abilities under KV Cache Compression? | 2025 | `2502.01941` | Independent multi-capability and long-generation quality benchmark. |
| LMCache: An Efficient KV Cache Layer for Enterprise-Scale LLM Inference | 2025 | `2510.09665` | Exact reuse and movement across GPU/CPU/disk/network tiers. |
| Hold Onto That Thought: Assessing KV Cache Compression On Reasoning | 2025 | `2512.12008` | Independent long self-generated reasoning and nontermination evidence. |

The retired paper was *A Method for Building Large Language Models with Predefined KV Cache Capacity* (2024, arXiv `2411.15785`). Its retirement preserved the research history without using weak evidence as a representative basis.

## Research structure

The final Landscape contains four mechanism-level Approach Families:

1. Token-selective retention and bounded attention.
2. Low-bit numerical KV representation.
3. Architectural KV head and layer sharing.
4. Serving memory management, KV reuse, and hierarchy.

It contains 15 sourced cross-paper Findings and four sourced Open Problems. The Findings distinguish resident footprint, read bandwidth, transfer cost, computation, and serving pressure; retain task/model/hardware/batch/bandwidth conditions; separate inference-only changes from training-time architecture changes; and record a genuine disagreement about reasoning-model robustness.

Four Investigation Gaps were created and resolved:

- Architectural evidence: resolved with CLA and MLKV; the underspecified bounded-cache candidate was retired.
- Serving reuse/offload: resolved with PagedAttention plus deeper LMCache analysis, separating exact paging, exact tiered reuse, and lossy transfer encoding.
- Layer-adaptive hybrids: resolved with XKV and MiniKV; layer allocation became a policy dimension inside selection, while MiniKV grounded co-designed selection-plus-INT2.
- Quality failures: resolved with two independent evaluations of fundamental abilities and long self-generated reasoning.

The key route relationship is dimensional rather than hierarchical. Selection reduces retained positions and often attention work; quantization reduces bytes per retained value; architecture reduces distinct generated KV tensors; serving management reduces allocation waste, repeated prefill, or transfer cost. These routes can sometimes compose, but MiniKV's failed SnapKV-plus-KIVI substitution shows that composition is not mechanically lossless. Capacity reduction also does not guarantee bandwidth or latency reduction: CLA/MLKV still read shared cache at consuming layers, while offload helps only when reuse and transfer beat recomputation.

## Resume

The deliberate interruption occurred at revision 55, after four searches and 40 hits, with 12 retained papers, six completed analyses, three provisional routes, six Findings, three Open Problems, and four open Gaps.

A new Codex context received only the workspace path, Run ID, and recovery instruction. It reconstructed the Contract, route map, analyzed-paper set, Gaps, and resource usage from normal Context/inspect plus persisted operational observations. It did not receive the earlier conversation. It then analyzed the retained architecture, hierarchy, and hybrid candidates; retired one weak source; ran two gap-driven searches; retained three additional papers; and completed the Landscape at revision 111.

No meaningless search was duplicated. The native State and audit preserved attempt counts but not query text; the four earlier queries were recoverable from ignored operational notes. This limitation did not materially hurt this run, but loss of those operational notes would reduce resume fidelity. It remains a documented non-blocking limitation rather than a reason to add a Search Entity or lifecycle.

Context scalability remained healthy. The midpoint Research View, bounded Completion View, page limits, and stable-ref inspection all fit within the configured 100k-character bound. No unlimited Context, full `state.json` injection, or new reading lifecycle was needed.

## Completion

One CompletionCheck was requested at revision 112 and evaluated by a one-use fresh Checker with no prior research conversation. Its authority surface contained only Completion View, stable-ref inspect, targeted retained-source reads, and typed submission. It inspected all ten requirements, all four approaches, and all fourteen active analyzed papers. It made nine targeted source-read attempts while independently checking serving, architectural, hybrid, quantization, and reasoning evidence.

Verdict sequence: `PASS`.

No `CONTINUE` occurred. This was not forced: the Checker found that all four accepted Gaps had already been genuinely remediated and that remaining work was delivery synthesis rather than missing research. It created no blocking Gap. The runtime's `CONTINUE → RESEARCH → Gap` behavior remains covered by the full test suite, but was not artificially exercised in this live run.

## Resource usage

Final authoritative counters and audit counts match exactly:

| External action | State counter | Audit events |
| --- | ---: | ---: |
| `paper_search_attempts` | 6 | 6 |
| `source_inspect_attempts` | 15 | 15 |
| `source_read_attempts` | 62 | 62 |

The 62 reads comprise 44 Research-phase targeted reads, nine fresh-Checker attempts, four attempts during an initially interrupted integrity pass, and five attempts in the successful integrity pass. One of the four interrupted-pass calls returned `LOCATOR_NOT_FOUND` because the acceptance actor used an unescaped section spelling. The failed attempt correctly consumed resource usage and advanced revision; the report was not published. Reusing the provider's exact outline locator allowed a clean rerun. This was an acceptance-actor locator error, not a Runtime bug.

The audit also contains one `run_created`, six `papers_retained`, 23 `research_mutation`, seven `approach_family_maintained`, four `investigation_gap_maintained`, four `investigation_gap_resolved`, one `paper_status_changed`, one completion request, one completion submission, one report publication, and one run closure.

## Report

- Ignored runtime artifact: `workspace/final-live-e2e/20260810T002408Z/runs/run_5fa1b3e5-cf40-4b40-bf6d-4d988920fe79/artifacts/report.md`.
- Size: 12,444 total characters, including approximately 4,971 CJK characters plus technical names, citation locators, and the deterministic bibliography.
- Citations: 49 rendered citation occurrences resolving to 14 primary-paper bibliography entries.
- Outline: problem/comparison coordinates; token selection; low-bit representation; architecture sharing; serving memory management/reuse; comparison and composition; evidence boundaries/disagreement; grounded unresolved questions; conclusion.
- Publication: citation rendering rejected internal refs and generated the bibliography; integrity disposition was `PASS`; `validate_delivery` recognized the required `REPORT` before closure.

The full 2,783-character `.vibe/REPORT_WRITING_GUIDE.md` content, SHA-256 `b047578608ec81ef136b65b854fc4f3f15cc9bc090143366dfa33ec4baedd7c3`, entered Narrative Planner, Composer, Editorial Integrator, exactly one Fresh Editor, and Reviser unchanged. Each stage recorded the same length and digest. `ResearchIntegrityReviewer.review` had no style-guideline parameter and independently re-read five key source sections.

The report is organized by mechanism and engineering decision rather than paper order. Ordinary concepts use natural Chinese while formal algorithm/model names remain in English. First-use terminology is normalized; internal Domain shorthand and stable refs do not appear. One comparison table is used because four routes are compared across four independent dimensions. Quantitative claims retain model, hardware, batch, task, or bandwidth conditions, and incompatible speedup numbers are explicitly not ranked. Citations sit beside the corresponding claims, and the four unresolved questions are grounded without dropping experimental qualifiers for prose fluency.

## Wiki

Wiki rebuild succeeded after the Run reached `CLOSED + COMPLETE`. The current manifest projects this Run at revision 132 and contains four independently written mechanism pages:

- Architectural KV Head and Layer Sharing.
- KV Cache Eviction and Token Selection.
- KV Cache Offloading and Memory Hierarchy.
- KV Cache Quantization.

Queries for `KV cache quantization`, `KV cache eviction`, and `KV cache offloading` each returned the expected page. Every hit's provenance points to this Run and to allowed Approach, Finding, OpenProblem, and Paper refs. The builder received only the authoritative Wiki projection, not report prose, and did not copy the report. The projection type excludes Investigation Gaps, Completion history, DeliveryBasis, and report artifacts. The Wiki is therefore a rebuildable future research lead, not primary evidence or proof.

## Architecture

| # | Assertion | Result |
| ---: | --- | --- |
| 1 | Search Hit remains an Observation. | Yes. Sixty hits produced only 15 explicitly retained Papers. |
| 2 | Search does not automatically write Paper. | Yes. Only `retain_papers` changed the corpus; audit has six separate retain actions. |
| 3 | Provider TLDR does not enter authoritative research knowledge. | Yes. It was used for triage only and is absent from persisted Paper/PaperAnalysis state. |
| 4 | Raw SourceContent is not persisted. | Yes. Reads were ephemeral; only authored analyses, locators, and grounded structures remain. |
| 5 | Researcher cannot self-submit PASS. | Yes. Researcher capabilities expose request but not completion submission. |
| 6 | Checker cannot broad-search. | Yes. The fresh evidence surface has no paper-search capability. |
| 7 | Checker cannot research-mutate. | Yes. It has no retain or research-mutation capability. |
| 8 | Delivery can only organize accepted State. | Yes. Delivery began only from the current Completion PASS basis and received the bounded Delivery View. |
| 9 | Report does not become a Research source. | Yes. It is a derived artifact outside `ResearchRun`; no Finding/OpenProblem cites it. |
| 10 | Wiki does not become Research proof. | Yes. It is a rebuildable projection/lead and cannot enter LiteratureSource grounding. |
| 11 | Context does not reinterpret State. | Yes. Views and inspect supplied typed projections and stable refs without semantic scoring or readiness flags. |
| 12 | No new Reading Lifecycle appeared. | Yes. Inspect/read remained resource-accounted actions with ephemeral provider payloads. |
| 13 | Duplicate Paper can mechanically deduplicate. | Yes. The repeated normalized arXiv ID for MiniKV reused one Paper; no fuzzy-title merge was introduced. |
| 14 | Stale expected revision is reliably rejected. | Yes. command boundaries retain optimistic revision checks; the full suite covers rejected stale writes and unchanged state. |
| 15 | Failed provider attempts are correctly charged. | Yes. The live `LOCATOR_NOT_FOUND` advanced revision and `source_read_attempts` while publishing no artifact. |
| 16 | Resume relies on State rather than conversation. | Yes. A no-history Codex resumed from Run ID, workspace, Context/inspect, and persisted operational observations. |
| 17 | `CLOSED` is recoverable from `state.json` alone. | Yes. `events.jsonl` was temporarily moved, revision 132 loaded as `CLOSED + COMPLETE`, and the event file was restored intact. |
| 18 | Stale DeliveryBasis cannot close a newer Contract. | Yes. closure validates the basis Contract revision; this Run's PASS basis and current Contract were both revision 1. Regression coverage rejects both stale PASS and partial authorization. |
| 19 | Completion `CONTINUE` can create/reopen Gaps. | Yes in formal regression coverage. The live Checker honestly returned PASS, so no artificial CONTINUE was introduced. |
| 20 | The final report comes entirely from accepted Research State. | Yes. It cites only the 14 active current-run papers and synthesizes accepted analyses, Findings, route relations, and Open Problems; integrity reads verified critical claims before publication. |

The audit log is observational, not reconstructive. During recovery acceptance the exact `events.jsonl` was moved aside, `JsonResearchRunRepository` loaded revision 132 as `CLOSED + COMPLETE` from `state.json`, and the event file was then restored.

## Bugs

No blocking Runtime bug or Frozen Architecture inconsistency was found. No product patch, Domain change, new lifecycle, persistent entity, readiness flag, or regression test was added during this acceptance.

The one failed source locator was local acceptance-actor input and demonstrated correct provider-failure accounting and artifact non-publication. The remaining non-blocking limitation is that native audit/state preserve search-attempt counts but not query text; ignored operational observations were sufficient for natural resume. Adding a persistent Search Entity, CandidatePaper state, or Search lifecycle is not justified by this run.

Final verification from the documentation branch: 275 unittest tests passed; mypy passed for 38 source files; Black check passed for 38 files; `git diff --check` passed; the tracked-tree secret scan found no credential; the raw acceptance workspace remained ignored and untracked.

## Final verdict

PASS — Runtime ready for Skill packaging

Runtime Freeze candidate. Ready for standalone Claude Code Skill packaging.
