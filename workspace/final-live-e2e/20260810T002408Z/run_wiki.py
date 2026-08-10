from __future__ import annotations

import json
from pathlib import Path

from my_search_harness.runtime import (
    LocalV1Runtime,
    WikiDraft,
    WikiPageDraft,
    WikiProvenanceRef,
    WikiSemanticReview,
)


WORKSPACE = Path(__file__).resolve().parent
RUN_ID = "run_5fa1b3e5-cf40-4b40-bf6d-4d988920fe79"


class Builder:
    def build(self, projection):
        run = next(item for item in projection.runs if item.run_id == RUN_ID)
        approaches = {item.name: item for item in run.approaches}
        findings = {item.statement: item for item in run.findings}
        problems = {item.statement: item for item in run.open_problems}
        papers = {item.arxiv_id: item for item in run.papers}

        def refs(*research_refs: str):
            return tuple(
                WikiProvenanceRef(run_id=run.run_id, research_ref=ref)
                for ref in research_refs
            )

        quant = approaches["Low-bit numerical KV representation"]
        selection = approaches["Token-selective retention and bounded attention"]
        hierarchy = approaches["Serving memory management, KV reuse, and hierarchy"]
        architecture = approaches["Architectural KV head and layer sharing"]

        quant_finding = next(
            item
            for text, item in findings.items()
            if text.startswith("KIVI and KVQuant independently agree")
        )
        hybrid_finding = next(
            item
            for text, item in findings.items()
            if text.startswith("Hybrid compression is not mechanically composable")
        )
        eviction_finding = next(
            item
            for text, item in findings.items()
            if text.startswith("Token reduction is not one mechanism")
        )
        quality_finding = next(
            item
            for text, item in findings.items()
            if text.startswith("Independent benchmarks show")
        )
        hierarchy_finding = next(
            item
            for text, item in findings.items()
            if text.startswith("Serving memory management reduces")
        )
        reuse_finding = next(
            item
            for text, item in findings.items()
            if text.startswith("Exact reuse/offload gains are conditional")
        )
        architecture_finding = next(
            item
            for text, item in findings.items()
            if text.startswith("Architectural sharing is a distinct")
        )

        quant_problem = next(
            item
            for text, item in problems.items()
            if text.startswith("Can extreme low-bit KV formats")
        )
        eviction_problem = next(
            item
            for text, item in problems.items()
            if text.startswith("How can a bounded cache")
        )
        serving_problem = next(
            item
            for text, item in problems.items()
            if text.startswith("How should a serving controller")
        )
        architecture_problem = next(
            item
            for text, item in problems.items()
            if text.startswith("Can architectural KV sharing")
        )

        return WikiDraft(
            pages=(
                WikiPageDraft(
                    slug="kv-cache-quantization",
                    title="KV Cache Quantization",
                    markdown=(
                        "# KV Cache Quantization\n\n"
                        "KV cache quantization lowers bytes per retained key/value rather "
                        "than deleting historical positions. The established design split is "
                        "per-channel treatment for keys and per-token treatment for values, "
                        "with recent residuals, outlier protection, calibration, or sink "
                        "protection used to control error. KIVI is tuning-free and keeps a "
                        "full-precision recent window; KVQuant uses calibrated non-uniform "
                        "formats and sparse outliers. MiniKV shows that INT2 can be combined "
                        "with token selection, but also that the selector changes the "
                        "quantization-error distribution.\n\n"
                        "Use this page as a lead to the cited primary papers. Validate target "
                        "tasks, attention architecture, bit width, residual budget, hardware "
                        "kernels, and prompt/decode regime before transferring a result."
                    ),
                    contributing_refs=refs(
                        quant.ref,
                        quant_finding.ref,
                        hybrid_finding.ref,
                        quant_problem.ref,
                        papers["2402.02750"].ref,
                        papers["2401.18079"].ref,
                        papers["2411.18077"].ref,
                    ),
                ),
                WikiPageDraft(
                    slug="kv-cache-eviction",
                    title="KV Cache Eviction and Token Selection",
                    markdown=(
                        "# KV Cache Eviction and Token Selection\n\n"
                        "KV cache eviction shortens the retained sequence and can reduce both "
                        "memory and attention work, but removed evidence cannot be recovered. "
                        "H2O updates heavy-hitter scores during decoding; SnapKV selects prompt "
                        "clusters before generation; StreamingLLM keeps attention sinks plus "
                        "recent tokens; XKV allocates application-specific budgets across "
                        "layers. These are different policies with different assumptions, not "
                        "interchangeable names for one algorithm.\n\n"
                        "Quality thresholds vary by task, model, prompt, budget, and generation "
                        "length. Long reasoning can degrade sharply or fail to terminate under "
                        "aggressive budgets, so evaluation should include output length and "
                        "termination behavior as well as accuracy."
                    ),
                    contributing_refs=refs(
                        selection.ref,
                        eviction_finding.ref,
                        quality_finding.ref,
                        eviction_problem.ref,
                        papers["2306.14048"].ref,
                        papers["2309.17453"].ref,
                        papers["2404.14469"].ref,
                        papers["2412.05896"].ref,
                        papers["2512.12008"].ref,
                    ),
                ),
                WikiPageDraft(
                    slug="kv-cache-offloading",
                    title="KV Cache Offloading and Memory Hierarchy",
                    markdown=(
                        "# KV Cache Offloading and Memory Hierarchy\n\n"
                        "KV cache offloading belongs to a serving route that preserves or "
                        "transports cached state instead of necessarily compressing its "
                        "semantic content. PagedAttention reduces GPU allocation waste and "
                        "shares prefixes exactly. LMCache reuses exact KV across GPU, CPU, disk, "
                        "remote, and disaggregated tiers. CacheGen encodes KV for bandwidth-"
                        "limited cross-machine transfer and may trade a bounded amount of "
                        "quality for fewer bytes.\n\n"
                        "The controlling comparison is load versus recomputation. Cache hits, "
                        "context length, network and host bandwidth, concurrency, prefetch, and "
                        "TTFT targets determine whether lower-tier reuse helps. A result from a "
                        "memory-bound or high-reuse service should not be generalized to a cold, "
                        "compute-bound workload."
                    ),
                    contributing_refs=refs(
                        hierarchy.ref,
                        hierarchy_finding.ref,
                        reuse_finding.ref,
                        serving_problem.ref,
                        papers["2309.06180"].ref,
                        papers["2510.09665"].ref,
                        papers["2310.07240"].ref,
                    ),
                ),
                WikiPageDraft(
                    slug="architectural-kv-sharing",
                    title="Architectural KV Head and Layer Sharing",
                    markdown=(
                        "# Architectural KV Head and Layer Sharing\n\n"
                        "Architectural KV sharing reduces how many independent KV tensors a "
                        "model creates. CLA reuses KV activations across adjacent layers, while "
                        "MLKV shares heads within and across layer groups. This route requires "
                        "training or uptraining and therefore differs from inference-only "
                        "eviction and quantization.\n\n"
                        "Lower cache capacity does not by itself imply lower decode latency: "
                        "shared KV may still be fetched at every consuming layer. Existing "
                        "evidence is concentrated in smaller or specially trained models, so "
                        "modern long-context models, optimized kernels, and combinations with "
                        "inference-time compression remain research leads."
                    ),
                    contributing_refs=refs(
                        architecture.ref,
                        architecture_finding.ref,
                        architecture_problem.ref,
                        papers["2405.12981"].ref,
                        papers["2406.09297"].ref,
                    ),
                ),
            )
        )


class Validator:
    def validate(self, projection, draft):
        if {run.run_id for run in projection.runs} != {RUN_ID}:
            return WikiSemanticReview(
                approved=False,
                issues=("projection included an unexpected source run",),
            )
        if len(draft.pages) != 4:
            return WikiSemanticReview(
                approved=False,
                issues=("the four accepted mechanism routes were not all represented",),
            )
        return WikiSemanticReview(approved=True)


def main() -> None:
    runtime = LocalV1Runtime(
        WORKSPACE,
        paper_search_provider=None,
        source_access_provider=None,
    )
    publication = runtime.wiki_runtime(Builder(), Validator()).rebuild()
    queries = (
        "KV cache quantization",
        "KV cache eviction",
        "KV cache offloading",
    )
    results = []
    for query in queries:
        result = runtime.wiki_query.query(query)
        if not result.hits:
            raise AssertionError(f"Wiki query produced no hit: {query}")
        results.append(
            {
                "query": query,
                "hits": [
                    {
                        "title": hit.title,
                        "path": hit.path,
                        "provenance": [
                            {
                                "run_id": ref.run_id,
                                "research_ref": ref.research_ref,
                            }
                            for ref in hit.contributing_refs
                        ],
                    }
                    for hit in result.hits
                ],
            }
        )
    record = {
        "wiki_path": str(publication.wiki_path),
        "is_current": runtime.wiki_runtime(Builder(), Validator()).is_current(),
        "source_runs": [
            {"run_id": run.run_id, "state_revision": run.state_revision}
            for run in publication.manifest.source_runs
        ],
        "page_count": len(publication.manifest.pages),
        "pages": [
            {
                "title": page.title,
                "path": page.path,
                "content_sha256": page.content_sha256,
                "provenance_count": len(page.contributing_refs),
            }
            for page in publication.manifest.pages
        ],
        "queries": results,
        "projection_excludes": [
            "investigation gaps",
            "completion checks",
            "delivery basis",
            "report artifacts",
        ],
    }
    (WORKSPACE / "observations" / "wiki-acceptance.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
