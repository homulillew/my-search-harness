# Completion Guide

Completion is an independent verification boundary. The checker must be freshly created
after `request-completion` and must not inherit the Researcher's hidden chain of thought,
scratch material, or conversational confidence.

## Allowed evidence actions

The checker may only use:

- `completion-view` for the complete contract-facing projection;
- `completion-inspect` for exact retained objects behind stable references;
- `completion-read-source` for targeted verification of primary evidence;
- `submit-completion` to record one verdict.

It must not search, retain papers, add or edit analyses, create findings, resolve gaps,
write the report, or modify persistence. If new work is needed, return CONTINUE with
blocking gaps so a Researcher can perform it.

## Evaluation criteria

Evaluate the current contract revision, not an earlier version. Check all of the
following:

1. Each requirement is addressed by explicit structured research state.
2. Major technical routes within scope are represented and meaningfully distinguished.
3. Important claims have retained-paper provenance and suitable evidence locators.
4. Representative methods have been inspected deeply enough to support mechanism-level
   comparisons, not merely named from search results.
5. Experimental results preserve model, task, baseline, hardware, or other material
   conditions needed to interpret them.
6. Contradictory or non-comparable evidence is not flattened into a false consensus.
7. Limitations and unresolved questions that affect the deliverable are explicit.
8. Open Investigation Gaps do not block a contract requirement.
9. For latest/current/recent requests, the state demonstrates a reasonable frontier
   window, explicit date-filtered searches, pagination beyond a single ranked page where
   useful, and retained recent primary work.
10. The landscape can support the promised deliverable without inventing new research
    during report writing.

Do not demand a fixed number of papers. A mature narrow topic may need fewer sources than
a broad fragmented field. Conversely, a large hit count does not establish coverage.

## Verdicts

### PASS

Use PASS only when every contract requirement is adequately supported, remaining limits
are compatible with the deliverable, and no open gap blocks completion. Reasons should
summarize why the evidence is sufficient and note accepted boundaries.

### CONTINUE

Use CONTINUE when specific research work can repair the deficiency. Include one or more
blocking gap specifications that say what evidence or synthesis is missing and connect it
to affected requirement or approach references when possible. Do not prescribe a fixed
query; describe the knowledge deficit.

Examples include a missing major route, inadequate primary-source evidence, absent
frontier coverage, unresolved contradiction, or a representative paper that has not been
analyzed beyond its abstract.

### UNCERTAIN

Use UNCERTAIN when the available state does not justify PASS, but the checker also cannot
form a defensible concrete repair plan. Explain the uncertainty. UNCERTAIN returns control
to Research without manufacturing blocking gaps.

## Submission discipline

Submit exactly one verdict for the pending CompletionCheck and current state revision.
PASS and UNCERTAIN must not contain blocking-gap payloads. CONTINUE must contain at least
one valid new or reopened blocking gap. Once submitted, the request metadata and completed
verdict are immutable facts.
