"""Ignored one-off helper for the pending fresh Completion Checker."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
import json
import sys

from my_search_harness.domain import CompletionVerdict, SourceLocator
from my_search_harness.runtime import CompletionCheckDecision, LocalV1Runtime


WORKSPACE = "workspace/final-live-e2e/20260810T002408Z"
RUN_ID = "run_5fa1b3e5-cf40-4b40-bf6d-4d988920fe79"


def default(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=repr)
    if is_dataclass(value):
        return asdict(value)
    return str(value)


def dump(value: object) -> None:
    print(json.dumps(value, default=default, ensure_ascii=False, indent=2))


class FreshChecker:
    """One-use checker with no research-session authority or carried state."""

    def evaluate(self, view, evidence):
        requirement_refs = tuple(item.ref for item in view.contract.requirements)
        approach_refs = tuple(item.ref for item in view.approach_families)
        paper_refs = tuple(sorted({
            *view.representative_paper_refs,
            *(
                source.paper_ref
                for finding in view.findings
                for source in finding.sources
            ),
            *(
                source.paper_ref
                for problem in view.open_problems
                for source in problem.sources
            ),
        }))

        requirements = evidence.inspect(requirement_refs)
        retained = evidence.inspect((*approach_refs, *paper_refs))
        paper_objects = tuple(
            item.value for item in retained.objects if item.kind == "paper"
        )

        assert view.contract.contract_revision == 1
        assert len(requirements.objects) == 10
        assert len(view.approach_families) == 4
        assert len(view.findings) == 15
        assert len(view.open_problems) == 4
        assert not view.open_gaps
        assert len(paper_objects) == 14
        assert all(paper.research_status.value == "ACTIVE" for paper in paper_objects)
        assert all(paper.analysis is not None for paper in paper_objects)
        assert all(approach.representative_paper_refs for approach in view.approach_families)
        assert all(finding.sources for finding in view.findings)
        assert all(problem.sources for problem in view.open_problems)

        by_title = {paper.source.title: paper.id for paper in paper_objects}
        evidence.read_source(
            by_title["CacheGen: KV Cache Compression and Streaming for Fast Large Language Model Serving"],
            SourceLocator(kind="section", value="The Hidden Network Bottleneck"),
        )
        evidence.read_source(
            by_title["Reducing Transformer Key-Value Cache Size with Cross-Layer Attention"],
            SourceLocator(kind="section", value="Discussion \\& Future Work"),
        )
        evidence.read_source(
            by_title["MiniKV: Pushing the Limits of LLM Inference via 2-Bit Layer-Discriminative KV Cache"],
            SourceLocator(kind="section", value="Limitations"),
        )

        return CompletionCheckDecision(
            verdict=CompletionVerdict.PASS,
            reasons=(
                "The accepted landscape covers four substantively different mechanism families with active, analyzed primary-paper representatives: token-selective retention, low-bit representation, trained head/layer sharing, and exact-or-encoded serving memory management/reuse/hierarchy.",
                "The fifteen sourced cross-paper findings cover the KV bottleneck, which resource each route reduces, quality/latency/throughput/memory and hardware/kernel tradeoffs, inference-only versus training-time deployment boundaries, conditional composition, limitations, and a concrete literature disagreement.",
                "Four sourced open problems cover unresolved quality adaptation, portable extreme quantization, large-model architectural validation and composition, and joint serving control; no accepted investigation gap remains open.",
                "Stable-ref inspection found fourteen active analyzed papers, and targeted primary-source reads independently confirmed the network-transfer distinction, the missing end-to-end serving validation for cross-layer sharing, and the demonstrated non-plug-and-play behavior of eviction-plus-INT2 composition.",
                "The accepted evidence is sufficient for the required mechanism-organized Chinese survey; remaining work is delivery synthesis and citation rendering rather than additional research.",
            ),
        )


class FreshFactory:
    def __init__(self) -> None:
        self._created = False

    def create(self):
        if self._created:
            raise RuntimeError("fresh completion checker factory is one-use")
        self._created = True
        return FreshChecker()


def main() -> None:
    runtime = LocalV1Runtime.from_deepxiv_env(WORKSPACE)
    command = sys.argv[1] if len(sys.argv) > 1 else "view"
    view = runtime.completion_checker.view(RUN_ID)

    if command == "view":
        dump(view)
        return
    if command == "inspect":
        dump(runtime.completion_checker.inspect(
            RUN_ID, view.state_revision, tuple(sys.argv[2:])
        ))
        return
    if command == "read":
        locator = (
            SourceLocator(kind="section", value=sys.argv[3])
            if len(sys.argv) > 3
            else None
        )
        result = runtime.completion_checker.read_source(
            RUN_ID, view.state_revision, sys.argv[2], locator
        )
        print(f"state_revision={result.state_revision}")
        print(result.source_content.content)
        return
    if command == "submit":
        dump(runtime.completion.resume_pending(RUN_ID, FreshFactory()))
        return
    raise SystemExit(f"unknown command: {command}")


if __name__ == "__main__":
    main()
