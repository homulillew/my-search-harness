#!/usr/bin/env python3
"""Diagnose DeepXiv frontier-paper corpus coverage, recall, and mapping loss."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from deepxiv_sdk import NotFoundError, Reader  # type: ignore[import-untyped]

from my_search_harness.runtime import DeepXivPaperSearchProvider


DATE_FROM = "2026-06-01"
DATE_TO = "2026-08-10"
ARXIV_VERSION = re.compile(r"v\d+$", re.IGNORECASE)

GOLD_PAPERS: tuple[dict[str, str], ...] = (
    {
        "title": "SearchMaster: Grounded and Regulated Self-Play for Search Agents",
        "arxiv_id": "2608.01822",
        "publication_date": "2026-08-03",
        "canonical_url": "https://arxiv.org/abs/2608.01822",
        "relevance": (
            "Search-agent training through grounded self-play, search-depth reward, "
            "tool-use regulation, and GRPO."
        ),
    },
    {
        "title": "DeepResearch Agent System",
        "arxiv_id": "2607.27562",
        "publication_date": "2026-07-30",
        "canonical_url": "https://arxiv.org/abs/2607.27562",
        "relevance": (
            "Deep-research and multi-tool search system whose training reports GRPO "
            "policy optimization."
        ),
    },
    {
        "title": "AREX: Towards a Recursively Self-Improving Agent for Deep Research",
        "arxiv_id": "2607.21461",
        "publication_date": "2026-07-23",
        "canonical_url": "https://arxiv.org/abs/2607.21461",
        "relevance": (
            "Deep-research agent trained with agentic mid-training and long-horizon "
            "reinforcement learning."
        ),
    },
)

TOPIC_QUERIES = (
    "reinforcement learning search agents",
    "search agent reinforcement learning",
    "deep research agent reinforcement learning",
    "agentic search policy learning",
)

EMERGING_QUERIES = (
    "search agents self-play",
    "search agent GRPO",
    "search-depth reward",
    "tool-use RL search",
    "agent search policy optimization",
    "credit assignment search agents",
    "trajectory reward search agents",
    "recursive self-improvement deep research",
    "long-horizon reinforcement learning deep research",
    "constraint verification research agent",
)

RERANK_QUERIES = (
    "reinforcement learning search agents",
    "search agents self-play",
    "deep research agent reinforcement learning",
)


def _base_arxiv_id(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return ARXIV_VERSION.sub("", value.strip().lower())


def _runtime_sha() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "UNKNOWN"


def _error(exc: BaseException) -> dict[str, str]:
    return {"status": "ERROR", "error_type": type(exc).__name__}


def _results(response: object) -> list[Mapping[str, object]]:
    if not isinstance(response, Mapping):
        return []
    values = response.get("result")
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, Mapping)]


def _gold_positions(values: Sequence[Mapping[str, object]]) -> dict[str, object]:
    positions: dict[str, object] = {}
    for gold in GOLD_PAPERS:
        gold_id = gold["arxiv_id"]
        match = next(
            (
                (index, value)
                for index, value in enumerate(values, start=1)
                if _base_arxiv_id(value.get("arxiv_id")) == gold_id
            ),
            None,
        )
        positions[gold_id] = (
            {"found": False, "rank": None, "score": None, "date": None}
            if match is None
            else {
                "found": True,
                "rank": match[0],
                "score": match[1].get("score"),
                "date": match[1].get("date"),
            }
        )
    return positions


def _date_range(values: Sequence[Mapping[str, object]]) -> dict[str, str | None]:
    dates = sorted(
        str(value["date"])
        for value in values
        if isinstance(value.get("date"), str) and str(value["date"]).strip()
    )
    return {
        "earliest": dates[0] if dates else None,
        "latest": dates[-1] if dates else None,
    }


def _search(
    reader: Reader,
    query: str,
    *,
    limit: int,
    offset: int = 0,
    fine_rerank: bool = False,
    date_from: str | None = DATE_FROM,
    date_to: str | None = DATE_TO,
) -> tuple[dict[str, object], object | None]:
    started = perf_counter()
    try:
        response = reader.search(
            query,
            size=limit,
            offset=offset,
            source="arxiv",
            date_from=date_from,
            date_to=date_to,
            use_fine_rerank=fine_rerank,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic classifies provider errors
        result: dict[str, object] = _error(exc)
        result["latency_seconds"] = round(perf_counter() - started, 3)
        return result, None
    values = _results(response)
    total_count = response.get("total_count") if isinstance(response, Mapping) else None
    result = {
        "status": "SUCCESS",
        "query": query,
        "limit": limit,
        "offset": offset,
        "date_from": date_from,
        "date_to": date_to,
        "use_fine_rerank": fine_rerank,
        "total_count": total_count,
        "returned_count": len(values),
        "gold": _gold_positions(values),
        "latency_seconds": round(perf_counter() - started, 3),
        "first_result_fields": sorted(values[0].keys()) if values else [],
        "date_samples": [
            value.get("date") for value in values[:5] if value.get("date") is not None
        ],
        "date_range": _date_range(values),
        "identities": [
            identity
            for value in values
            if (identity := _base_arxiv_id(value.get("arxiv_id"))) is not None
        ],
    }
    return result, response


def _corpus_coverage(reader: Reader) -> list[dict[str, object]]:
    coverage: list[dict[str, object]] = []
    for gold in GOLD_PAPERS:
        print(f"corpus probe {gold['arxiv_id']}", file=sys.stderr, flush=True)
        started = perf_counter()
        try:
            response = reader.head(gold["arxiv_id"])
        except NotFoundError:
            coverage.append(
                {
                    "arxiv_id": gold["arxiv_id"],
                    "status": "NOT_FOUND",
                    "latency_seconds": round(perf_counter() - started, 3),
                }
            )
        except Exception as exc:  # noqa: BLE001 - diagnostic classifies provider errors
            value: dict[str, object] = {
                "arxiv_id": gold["arxiv_id"],
                **_error(exc),
                "latency_seconds": round(perf_counter() - started, 3),
            }
            coverage.append(value)
        else:
            fields = sorted(response.keys()) if isinstance(response, Mapping) else []
            coverage.append(
                {
                    "arxiv_id": gold["arxiv_id"],
                    "status": "FOUND" if response else "NOT_FOUND",
                    "title": (
                        response.get("title") if isinstance(response, Mapping) else None
                    ),
                    "publish_at": (
                        response.get("publish_at")
                        if isinstance(response, Mapping)
                        else None
                    ),
                    "response_fields": fields,
                    "latency_seconds": round(perf_counter() - started, 3),
                }
            )
    return coverage


def _exact_title_recall(reader: Reader) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []
    for gold in GOLD_PAPERS:
        print(f"exact-title probe {gold['arxiv_id']}", file=sys.stderr, flush=True)
        result, _ = _search(reader, gold["title"], limit=100)
        observations.append(result)
    return observations


def _date_and_index_controls(reader: Reader) -> dict[str, object]:
    gold_controls: list[dict[str, object]] = []
    for gold in GOLD_PAPERS:
        print(f"date/index controls {gold['arxiv_id']}", file=sys.stderr, flush=True)
        exact_unfiltered, _ = _search(
            reader,
            gold["title"],
            limit=100,
            date_from=None,
            date_to=None,
        )
        id_unfiltered, _ = _search(
            reader,
            gold["arxiv_id"],
            limit=100,
            date_from=None,
            date_to=None,
        )
        exact_full_2026, _ = _search(
            reader,
            gold["title"],
            limit=100,
            date_from="2026-01-01",
            date_to=DATE_TO,
        )
        gold_controls.append(
            {
                "arxiv_id": gold["arxiv_id"],
                "exact_title_unfiltered": exact_unfiltered,
                "exact_id_unfiltered": id_unfiltered,
                "exact_title_full_2026": exact_full_2026,
            }
        )

    monthly_controls: list[dict[str, object]] = []
    for date_from, date_to in (
        ("2026-01-01", "2026-01-31"),
        ("2026-04-01", "2026-04-30"),
        ("2026-06-01", "2026-06-30"),
        ("2026-07-01", "2026-07-31"),
        ("2026-08-01", DATE_TO),
    ):
        result, _ = _search(
            reader,
            TOPIC_QUERIES[0],
            limit=100,
            date_from=date_from,
            date_to=date_to,
        )
        monthly_controls.append(result)

    april_control, _ = _search(
        reader,
        (
            "Enhancing LLM-based Search Agents via Contribution Weighted Group "
            "Relative Policy Optimization"
        ),
        limit=100,
        date_from="2026-04-01",
        date_to="2026-04-30",
    )
    semantic_unfiltered: list[dict[str, object]] = []
    for query in (*TOPIC_QUERIES, *EMERGING_QUERIES):
        result, _ = _search(
            reader,
            query,
            limit=100,
            date_from=None,
            date_to=None,
        )
        semantic_unfiltered.append(result)
    return {
        "gold_controls": gold_controls,
        "monthly_controls": monthly_controls,
        "known_april_exact_title_control": april_control,
        "semantic_unfiltered": semantic_unfiltered,
    }


def _semantic_recall(
    reader: Reader,
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    observations: list[dict[str, object]] = []
    comparison_response: dict[str, object] | None = None
    for query in (*TOPIC_QUERIES, *EMERGING_QUERIES):
        print(f"semantic probe {query}", file=sys.stderr, flush=True)
        result, raw = _search(reader, query, limit=100)
        observations.append(result)
        if query == TOPIC_QUERIES[0] and isinstance(raw, dict):
            comparison_response = raw
    return observations, comparison_response


def _pagination(
    reader: Reader, semantic: Sequence[dict[str, object]]
) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []
    for initial in semantic:
        total = initial.get("total_count")
        returned = initial.get("returned_count")
        if (
            initial.get("status") != "SUCCESS"
            or not isinstance(total, int)
            or not isinstance(returned, int)
            or total <= returned
        ):
            continue
        query = str(initial["query"])
        seen = set(initial.get("identities", []))
        pages: list[dict[str, object]] = [
            {
                "page": 1,
                "offset": 0,
                "returned_count": returned,
                "new_unique_count": len(seen),
                "gold": initial["gold"],
            }
        ]
        offset = returned
        page = 2
        while offset < total and offset <= 10_000:
            print(
                f"pagination probe {query} offset={offset}", file=sys.stderr, flush=True
            )
            result, _ = _search(reader, query, limit=100, offset=offset)
            identities = set(result.get("identities", []))
            new_identities = identities - seen
            pages.append(
                {
                    "page": page,
                    "offset": offset,
                    "returned_count": result.get("returned_count"),
                    "new_unique_count": len(new_identities),
                    "gold": result.get("gold"),
                    "status": result.get("status"),
                }
            )
            if (
                result.get("status") != "SUCCESS"
                or not identities
                or not new_identities
            ):
                break
            seen.update(identities)
            returned_count = result.get("returned_count")
            if not isinstance(returned_count, int) or returned_count == 0:
                break
            offset += returned_count
            page += 1
        observations.append({"query": query, "total_count": total, "pages": pages})
    return observations


def _unfiltered_pagination_control(reader: Reader) -> dict[str, object]:
    query = TOPIC_QUERIES[0]
    seen: set[str] = set()
    pages: list[dict[str, object]] = []
    for page, offset in enumerate((0, 100, 200), start=1):
        print(
            f"unfiltered pagination control {query} offset={offset}",
            file=sys.stderr,
            flush=True,
        )
        result, _ = _search(
            reader,
            query,
            limit=100,
            offset=offset,
            date_from=None,
            date_to=None,
        )
        identities = set(result.get("identities", []))
        new_identities = identities - seen
        pages.append(
            {
                "page": page,
                "offset": offset,
                "status": result.get("status"),
                "total_count": result.get("total_count"),
                "returned_count": result.get("returned_count"),
                "new_unique_count": len(new_identities),
                "gold": result.get("gold"),
                "date_range": result.get("date_range"),
            }
        )
        if result.get("status") != "SUCCESS" or not new_identities:
            break
        seen.update(new_identities)
    return {"query": query, "pages": pages}


def _fine_rerank(reader: Reader) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []
    for query in RERANK_QUERIES:
        print(f"rerank A/B recent {query}", file=sys.stderr, flush=True)
        variants: dict[str, dict[str, object]] = {}
        raw_identities: dict[tuple[bool, int], list[str]] = {}
        for enabled in (False, True):
            for limit in (20, 100):
                result, _ = _search(
                    reader,
                    query,
                    limit=limit,
                    fine_rerank=enabled,
                )
                variants[f"fine_{str(enabled).lower()}_top_{limit}"] = result
                raw_identities[(enabled, limit)] = list(result.get("identities", []))
        variants["top_20_overlap"] = {
            "count": len(
                set(raw_identities[(False, 20)]) & set(raw_identities[(True, 20)])
            )
        }
        variants["top_100_overlap"] = {
            "count": len(
                set(raw_identities[(False, 100)]) & set(raw_identities[(True, 100)])
            )
        }
        observations.append({"query": query, **variants})
        print(f"rerank A/B unfiltered {query}", file=sys.stderr, flush=True)
        unfiltered_variants: dict[str, dict[str, object]] = {}
        unfiltered_identities: dict[tuple[bool, int], list[str]] = {}
        for enabled in (False, True):
            for limit in (20, 100):
                result, _ = _search(
                    reader,
                    query,
                    limit=limit,
                    fine_rerank=enabled,
                    date_from=None,
                    date_to=None,
                )
                unfiltered_variants[f"fine_{str(enabled).lower()}_top_{limit}"] = result
                unfiltered_identities[(enabled, limit)] = list(
                    result.get("identities", [])
                )
        unfiltered_variants["top_20_overlap"] = {
            "count": len(
                set(unfiltered_identities[(False, 20)])
                & set(unfiltered_identities[(True, 20)])
            )
        }
        unfiltered_variants["top_100_overlap"] = {
            "count": len(
                set(unfiltered_identities[(False, 100)])
                & set(unfiltered_identities[(True, 100)])
            )
        }
        observations[-1]["unfiltered"] = unfiltered_variants
    return observations


class _StaticReader:
    def __init__(self, response: object) -> None:
        self._response = response

    def search(self, *args: object, **kwargs: object) -> object:
        return self._response


def _harness_mapping(token: str, response: object | None) -> dict[str, object]:
    if response is None:
        return {"status": "SKIPPED"}
    provider = DeepXivPaperSearchProvider(
        token,
        reader_factory=lambda **_: _StaticReader(response),
    )
    try:
        provider_result = provider.search(
            TOPIC_QUERIES[0],
            limit=100,
            date_from=DATE_FROM,
            date_to=DATE_TO,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic classifies mapping errors
        return _error(exc)
    hits = getattr(provider_result, "hits", provider_result)
    total_count = getattr(provider_result, "total_count", None)
    values = [asdict(hit) if is_dataclass(hit) else repr(hit) for hit in hits]
    return {
        "status": "SUCCESS",
        "total_count": total_count,
        "returned_count": len(values),
        "hit_fields": (
            sorted(values[0].keys()) if values and isinstance(values[0], dict) else []
        ),
        "rank_order": [
            value.get("arxiv_id") for value in values if isinstance(value, dict)
        ],
        "date_values": [
            value.get("publication_date")
            for value in values[:5]
            if isinstance(value, dict) and "publication_date" in value
        ],
    }


def diagnose() -> dict[str, object]:
    token = os.environ.get("DEEPXIV_TOKEN", "").strip()
    if not token:
        raise SystemExit("DEEPXIV_TOKEN is required")
    reader = Reader(token=token, max_retries=0)
    corpus = _corpus_coverage(reader)
    exact_titles = _exact_title_recall(reader)
    date_and_index_controls = _date_and_index_controls(reader)
    semantic, _ = _semantic_recall(reader)
    pagination = _pagination(reader, semantic)
    unfiltered_pagination = _unfiltered_pagination_control(reader)
    rerank = _fine_rerank(reader)
    _, raw_comparison = _search(
        reader,
        TOPIC_QUERIES[0],
        limit=100,
        date_from=None,
        date_to=None,
    )
    raw_values = _results(raw_comparison)
    direct_summary = {
        "status": "SUCCESS" if raw_comparison is not None else "SKIPPED",
        "total_count": (
            raw_comparison.get("total_count") if raw_comparison is not None else None
        ),
        "returned_count": len(raw_values),
        "first_result_fields": sorted(raw_values[0].keys()) if raw_values else [],
        "rank_order": [value.get("arxiv_id") for value in raw_values],
        "date_values": [value.get("date") for value in raw_values[:5]],
    }
    return {
        "environment": {
            "runtime_sha": _runtime_sha(),
            "deepxiv_sdk_version": importlib.metadata.version("deepxiv-sdk"),
            "current_date": DATE_TO,
            "token_present": True,
        },
        "gold_set": GOLD_PAPERS,
        "corpus_coverage": corpus,
        "exact_title_recall": exact_titles,
        "date_and_index_controls": date_and_index_controls,
        "semantic_recall": semantic,
        "pagination": pagination,
        "unfiltered_pagination_control": unfiltered_pagination,
        "fine_rerank": rerank,
        "raw_vs_harness": {
            "query": TOPIC_QUERIES[0],
            "direct_sdk": direct_summary,
            "harness_provider": _harness_mapping(token, raw_comparison),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = diagnose()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "output": str(args.output)}))
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
