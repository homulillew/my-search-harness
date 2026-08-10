# Frontier Search Recall Diagnostic

Status: **BLOCKED — DeepXiv search coverage/recall prevents reliable frontier research**

## Environment

- Runtime base SHA: `97964929340ce4d4523a29a626e0e66c3f9282a7`
- Branch: `agent/claude-code-skill-package`
- DeepXiv SDK: `0.3.1`
- Diagnostic cutoff: `2026-08-10`
- Token present: `true`
- Script: `scripts/diagnose_frontier_search.py`

The live before and after outputs were written only to `/tmp`; no token, provider TLDR,
raw hit corpus, or Research Run was persisted in the repository.

## Gold set

| Paper | arXiv | Exact date | Why in scope |
|---|---|---:|---|
| SearchMaster: Grounded and Regulated Self-Play for Search Agents | [`2608.01822`](https://arxiv.org/abs/2608.01822) | 2026-08-03 | Search-agent training with grounded self-play, a search-depth reward, tool-use regulation, and GRPO. |
| DeepResearch Agent System | [`2607.27562`](https://arxiv.org/abs/2607.27562) | 2026-07-30 | A deep-research and multi-tool search system reporting GRPO policy optimization. |
| AREX: Towards a Recursively Self-Improving Agent for Deep Research | [`2607.21461`](https://arxiv.org/abs/2607.21461) | 2026-07-23 | A deep-research agent using agentic mid-training and long-horizon reinforcement learning. |

The titles, identifiers, and dates were verified against canonical arXiv metadata before
the provider experiment. `CW-GRPO` ([`2604.14267`](https://arxiv.org/abs/2604.14267),
2026-04-15) was also used as an April date-filter control.

## Corpus coverage

Direct `Reader.head(arxiv_id)` found all three gold papers:

| arXiv | DeepXiv head | `publish_at` |
|---|---|---|
| `2608.01822` | FOUND | `2026-08-03T07:29:11` |
| `2607.27562` | FOUND | `2026-07-30T01:15:47` |
| `2607.21461` | FOUND | `2026-07-23T16:05:46` |

This rules out a simple whole-corpus ingestion miss for the gold set. It does not show
that the same records are present in the search index.

## Exact-title and identifier recall

With `date_from=2026-06-01`, `date_to=2026-08-10`, `limit=100`, every complete-title
query returned `total_count=0`, zero hits, and no gold rank. Removing dates did not fix
recall: complete-title and exact-arXiv-ID queries each returned 100 candidates but missed
the named gold paper in the first 100. Expanding the date window to all of 2026 also
missed each gold paper.

| Gold | Recent exact title | Unfiltered exact title | Unfiltered exact ID |
|---|---:|---:|---:|
| `2608.01822` | MISS (0 results) | MISS (top 100) | MISS (top 100) |
| `2607.27562` | MISS (0 results) | MISS (top 100) | MISS (top 100) |
| `2607.21461` | MISS (0 results) | MISS (top 100) | MISS (top 100) |

The April control succeeded: the complete `CW-GRPO` title placed `2604.14267` at rank 1
inside the April date window. For the same broad semantic control, January and April
returned 100 hits, while June, July, and August each returned zero. Across all unfiltered
semantic top-100 results, the newest observed dates were between 2026-05-15 and
2026-05-27. This is strong evidence of a search-index or date-filter freshness boundary
near late May, despite newer records being available through `head`.

## Semantic recall

All queries below used the 2026-06-01 through 2026-08-10 window and `limit=100`. Every
cell is a miss; every query returned `total_count=0` and zero candidates.

| Frontier query | SearchMaster | DeepResearch Agent System | AREX |
|---|---:|---:|---:|
| reinforcement learning search agents | — | — | — |
| search agent reinforcement learning | — | — | — |
| deep research agent reinforcement learning | — | — | — |
| agentic search policy learning | — | — | — |
| search agents self-play | — | — | — |
| search agent GRPO | — | — | — |
| search-depth reward | — | — | — |
| tool-use RL search | — | — | — |
| agent search policy optimization | — | — | — |
| credit assignment search agents | — | — | — |
| trajectory reward search agents | — | — | — |
| recursive self-improvement deep research | — | — | — |
| long-horizon reinforcement learning deep research | — | — | — |
| constraint verification research agent | — | — | — |

The same 14 queries without date filters each returned 100 hits, but none retrieved any
gold paper in the top 100. Query expansion therefore cannot compensate for the observed
frontier index gap.

## Pagination

No recent-window query qualified for normal pagination because each returned zero.
An explicit unfiltered pagination control exposed important provider semantics:

| Offset | Returned | Provider `total_count` | New unique identities | Gold found |
|---:|---:|---:|---:|---:|
| 0 | 100 | 100 | 100 | 0 |
| 100 | 100 | 200 | 98 | 0 |
| 200 | 100 | 300 | 99 | 0 |

`total_count` changes with offset and behaved as an accumulated/capped provider signal,
not a stable global cardinality. The Harness now exposes it exactly as reported, but the
Skill must combine it with returned count and identity novelty instead of treating it as
an authoritative number of all matches. Pagination found 297 unique identities and no
gold paper; the failure is not merely a first-page early-stop error.

## Fine rerank

The installed SDK signature was inspected directly. `Reader.search` supports
`use_fine_rerank`, whose SDK default is `False`. Three queries were compared at top 20
and top 100 with and without the recent date window.

| Query | Unfiltered top-20 overlap | Top-100 overlap | Gold with rerank | Representative top-100 latency off/on |
|---|---:|---:|---:|---:|
| reinforcement learning search agents | 20/20 | 100/100 | 0 | 0.201s / 0.187s |
| search agents self-play | 19/20 | 100/100 | 0 | 0.187s / 0.188s |
| deep research agent reinforcement learning | 20/20 | 100/100 | 0 | 0.186s / 0.199s |

Recent-window variants had no candidates with either setting. Fine rerank did not alter
top-100 recall and did not recover a gold paper, so no rerank product option or default
change is justified.

## Harness information loss

The same live unfiltered query preserved rank order exactly before and after the patch.

| Observation | Before | After |
|---|---|---|
| Provider-reported `total_count` | validated, then discarded | exposed on `PaperSearchResult` and CLI; added to success audit |
| Provider date | reduced to year | normalized to `YYYY-MM-DD`, exposed on each hit, retained on `PaperSource` |
| Rank order | preserved | preserved |
| Raw search hits in ResearchRun | not persisted | still not persisted |

The direct response used ISO timestamps such as `2026-05-16T03:32:48`; the Harness now
returns `2026-05-16` while retaining `publication_year=2026` for compatibility. Old
states without `publication_date` still decode with `None`.

## Before / after acceptance

| Measure | Before | After |
|---|---:|---:|
| Gold present through direct head | 3/3 | 3/3 |
| Gold found by recent exact-title search | 0/3 | 0/3 |
| Gold found by reasonable semantic frontier queries | 0/3 | 0/3 |
| Recent-window candidates per tested query | 0 | 0 |
| Unfiltered candidates per tested first page | 100 | 100 |
| `total_count` visible through Harness | no | yes |
| Full publication date visible through Harness | no | yes |
| SearchMaster semantic rank | none | none |

The patch improves observation fidelity and future search policy, but does not materially
change DeepXiv frontier discovery because the provider search endpoint still cannot
retrieve the recent gold papers.

## Root-cause verdict

1. **P0 — B. Provider semantic recall:** 3/3 head-visible papers miss complete-title,
   exact-ID, and semantic searches. Recent-window search returns no candidates.
2. **P0 — search-index freshness aspect of A. Provider coverage:** the records exist in
   source/head, but the searchable/date-filterable surface observed no June–August data.
3. **P1 — D. Harness information loss:** `total_count` and full dates were discarded.
   This is fixed and regression-tested.
4. **P1 — E. Skill query strategy:** the previous guidance did not require terminology-
   driven Frontier Sweep expansion. This is fixed as semantic policy.
5. **P1 — F. Skill pagination/early stopping:** prior guidance lacked a sufficiently
   explicit large observation funnel and `total_count`/novelty policy. This is fixed,
   although live pagination did not recover the gold set.
6. **P2 — C. Provider ranking:** rerank changed at most one top-20 position and no
   top-100 membership in this test. It is not the current frontier blocker.

## Changes justified by the diagnostic

- Add provider-neutral `PaperSearchPage` and expose provider `total_count` on
  `PaperSearchResult`, CLI JSON, and successful search audit events.
- Add optional `publication_date` to `PaperSearchHit` and retained `PaperSource`, preserve
  the existing year field, normalize provider timestamps, and keep codec compatibility.
- Expose retained dates in context and Wiki projections.
- Add Frontier Sweep, terminology expansion, larger candidate-funnel, pagination,
  exact-paper fallback, and pre-completion recency self-check guidance to the packaged
  Skill without changing Completion Checker authority.
- Keep the direct provider diagnostic in `scripts/`; do not add a second provider, fake
  chronological global sort, rerank API, cache, planner framework, or Domain entity.

## Remaining provider limitation

As of 2026-08-10, SearchMaster (`2608.01822`) is present through DeepXiv `head`, but
complete-title search cannot retrieve it, 14 reasonable semantic frontier queries cannot
retrieve it, three unfiltered pages cannot retrieve it, and fine rerank does not help.
The same pattern holds for the two July gold papers.

Reliable frontier research therefore requires a Human architecture decision: obtain a
provider-side search-index freshness/recall fix, change the primary discovery provider,
or authorize a second discovery provider. This change deliberately does none of those.
