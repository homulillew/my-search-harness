# Runtime Adapter API

Invoke commands through:

```bash
${CLAUDE_SKILL_DIR}/scripts/harness --workspace PATH COMMAND [OPTIONS]
```

The adapter writes exactly one JSON object. Success goes to stdout with `"ok": true`.
Errors go to stderr with `"ok": false`, an error type, and a safe message; exit status is
nonzero and no traceback is printed. Credentials are never command arguments.

Commands that accept semantic structures use `--input FILE`. The file must contain one
JSON object with exactly the documented fields. This is typed command input, not JSON
Patch or raw state replacement.

## Environment and observation

```text
doctor
view --run-id RUN
inspect --run-id RUN --expected-revision REV --refs REF [REF ...]
audit-history --run-id RUN
wiki-query --query TEXT [--limit N]
```

`view` accepts optional `--input` containing a continuation object with
`state_revision`, `section`, and `after`. Wiki results are non-authoritative observations.

## Create and search

`create-run --input FILE`:

```json
{
  "mission": "Map the field",
  "requirements": ["Compare major routes", "Cover recent work"],
  "scope": "Peer-reviewed and arXiv primary literature",
  "deliverable_description": "Chinese technical-route survey",
  "required_artifacts": ["REPORT"]
}
```

`search-papers` requires `--run-id`, `--expected-revision`, `--query`; it supports
`--limit`, `--offset`, `--date-from`, and `--date-to`. Dates use `YYYY-MM-DD`. Search
output is observation-only, exposes the provider-reported `total_count`, and contains
all provider-neutral hit fields. Each hit exposes `publication_date` (`YYYY-MM-DD`) and
`publication_year` when available.

`retain-papers --input FILE` accepts either `{"hits": [...]}` or one complete prior
search result object containing a `hits` array. Each hit uses the fields emitted by
`search-papers`. Search hits remain observations. Retain changes state; search alone does
not add papers, while an explicit retain preserves both date fields on `PaperSource`.

## Web-discovered paper promotion

Claude Code native Web tools are host-level discovery capabilities, not Harness commands.
After `WebSearch` discovers a candidate, use `WebFetch` on its canonical arXiv,
OpenReview, DOI, or publisher page and construct the same provider-neutral hit shape for
`retain-papers`. Fill only metadata verified on that page; optional fields may be omitted.

```json
{
  "hits": [
    {
      "title": "SearchMaster: Grounded and Regulated Self-Play for Search Agents",
      "publication_year": 2026,
      "publication_date": "2026-08-03",
      "arxiv_id": "2608.01822",
      "canonical_url": "https://arxiv.org/abs/2608.01822",
      "other_identifiers": {},
      "categories": []
    }
  ]
}
```

This input promotes bibliographic identity into authoritative State; it does not promote
a Web snippet or page into technical evidence. Use `inspect-source` and `read-source`
before synthesis. Do not invent missing authors, dates, identifiers, abstracts, or venue
metadata, and do not create host-Web audit events in the Harness.

## Research evidence

```text
inspect-source --run-id RUN --expected-revision REV --paper-ref PAPER
read-source --run-id RUN --expected-revision REV --paper-ref PAPER
            [--locator-kind KIND --locator-value VALUE]
```

Source output is ephemeral. Persist selected meaning with the following commands.

`put-paper-analysis --input FILE`:

```json
{
  "paper_ref": "paper_...",
  "summary": "...",
  "relevance_to_run": "...",
  "contributions": ["..."],
  "key_results": ["..."],
  "limitations": ["..."],
  "key_locators": [{"kind": "section", "value": "Results"}]
}
```

`put-approach-family --input FILE` accepts `name`, `core_idea`,
`representative_paper_refs`, and optional `approach_ref` for update.

`merge-approach-family` uses `--target-approach-ref` and `--source-approach-ref`.

`put-finding --input FILE` and `put-open-problem --input FILE` accept `statement`,
optional `approach_refs`, optional `sources`, and optional existing `finding_ref` or
`problem_ref`. A source object is:

```json
{
  "paper_ref": "paper_...",
  "relation": "SUPPORTS",
  "locator": {"kind": "section", "value": "Experiments"}
}
```

`retire-finding --finding-ref REF` and `retire-open-problem --problem-ref REF` retire
their targets.

`put-gap --input FILE` accepts `description`, optional `requirement_refs`, optional
`approach_refs`, and optional `gap_ref`. `resolve-gap` uses `--gap-ref` and
`--resolution`; `reopen-gap` uses `--gap-ref`.

`set-paper-status --paper-ref REF --status ACTIVE|RETIRED` changes explicit research
status.

All research mutations also require `--run-id` and `--expected-revision`.

## Completion

```text
request-completion --run-id RUN --expected-revision REV --rationale TEXT
completion-view --run-id RUN
completion-inspect --run-id RUN --expected-revision REV --refs REF [REF ...]
completion-read-source --run-id RUN --expected-revision REV --paper-ref PAPER
                       [--locator-kind KIND --locator-value VALUE]
submit-completion --run-id RUN --expected-revision REV --input FILE
```

Submission input contains `completion_check_ref`, `verdict`, `reasons`, and optional
`blocking_gaps`. A new blocking gap contains `description`, `requirement_refs`, and
`approach_refs`; a reopened gap contains only `gap_ref`.

## Delivery

```text
delivery-view --run-id RUN
delivery-inspect --run-id RUN --expected-revision REV --refs REF [REF ...]
delivery-read-source --run-id RUN --expected-revision REV --paper-ref PAPER ...
render-report --run-id RUN --input FILE
publish-report --run-id RUN --expected-revision REV --input FILE
validate-delivery --run-id RUN
reopen-research --run-id RUN --expected-revision REV
close-run --run-id RUN --expected-revision REV
```

`render-report` input contains `markdown` and `citations`. Markdown uses tokens such as
`{{cite:method}}`; each citation declares `citation_id`, `paper_ref`, and optional
`locator`. The deterministic renderer validates references and adds the bibliography.

`publish-report` input contains a non-empty `content` string. It calls the Delivery
capability and never writes the artifact store directly. Validate before closing.

## Revision failures

Most commands use optimistic `expected_revision`. Search and source access record an
external attempt before calling the provider, so their safe error JSON may include a
new `state_revision`. Use it or call the lifecycle-appropriate view before retrying.
