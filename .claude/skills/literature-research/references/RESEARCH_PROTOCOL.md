# Research Protocol

This protocol explains how a semantic Claude researcher uses the deterministic V1
Runtime. The Frozen Architecture and Domain Model remain the authority for runtime
semantics; this document supplies operating guidance, not a second workflow model.

## Contract formation

Translate the user's request into a Research Contract before searching. Requirements
must describe observable coverage or analysis obligations rather than a hidden process.
Examples include covering major technical routes, preserving deployment conditions,
contrasting conflicting results, and including developments within a stated recent
window. Scope must state meaningful exclusions. The deliverable says what the user will
receive and normally requires a report artifact.

Numbers of searches, papers, sections, or tokens are workload guidance, not proof that
the contract is satisfied. If the user provides ambiguous recency language, state a
reasonable date window and retain it in the contract or active gap.

## Adaptive outer loop

At each iteration, view authoritative state and choose the action that most reduces a
contract-relevant uncertainty. The loop is deliberately adaptive:

```text
observe state → select uncertainty → acquire evidence → retain → synthesize → reassess
```

Search is useful for discovery. Source inspection and reading establish evidence.
Structured synthesis makes knowledge recoverable. Completion is a separate judgment.

## Discovery and frontier coverage

Use broad discovery to learn field vocabulary, seminal work, surveys, major mechanism
families, and known disagreements. Use multiple routes: problem terms, method names,
benchmark names, influential authors, and limitations can expose different literature.

For latest/current/recent requests, add frontier searches with explicit dates. Choose a
window appropriate to the field and user intent. Search the first page and later offsets;
compare returned identities to determine whether pagination adds useful coverage. A
ranking without date filters is not evidence of recency coverage.

Search results are observations. Retain only candidates useful for the current contract,
and do so explicitly. Arbitrary provider identifiers do not establish paper identity.

## Evidence acquisition

Inspect a retained source before reading it. Select method, experiment, results,
limitations, appendix, or other targeted sections by provider-supported locator. Use a
full read only when targeted navigation cannot answer the current question.

Abstracts and provider summaries are selection aids. Do not use them as substitutes for
primary evidence when writing detailed technical claims. Retrieved source text is
ephemeral; durable knowledge belongs in typed state with stable paper references and
locators.

## Structured synthesis

Write PaperAnalysis after evidence is sufficiently understood. Preserve:

- the paper's actual contribution;
- relevance to the current mission;
- key results and their experimental conditions;
- limitations and evidence boundaries;
- locators that permit later verification.

Group methods into ApproachFamily only when they share a meaningful core mechanism.
Use representative papers to make the family inspectable. Findings synthesize supported
technical judgments across papers. Open Problems describe unresolved domain questions.
Investigation Gaps describe research work still blocking this run.

Use `SUPPORTS`, `CHALLENGES`, and `QUALIFIES` deliberately. A source that demonstrates a
result in a narrow setting may qualify a broad claim rather than support it outright.

Synthesize throughout the run. Waiting until the end creates an unrecoverable pile of
ephemeral observations and encourages report-first reasoning.

## State and revision discipline

Every mutation is optimistic and revision-bound. Use the revision returned by the last
command. Search and source access count external attempts before making the call, so a
failed attempt can still produce a newer revision. Treat revision errors as a signal to
view state again, never as permission to alter persistence directly.

The run workspace is authoritative. Conversation history, scratch notes, and search hit
output are not. Resume by viewing state, inspecting stable references, reading current
open gaps, and consulting audit history for external attempt parameters.

## Completion and delivery

The Researcher requests completion only after it can point to structured evidence for
each contract requirement and explain known limits. A fresh checker then follows
`COMPLETION_GUIDE.md`; it cannot search or mutate research state.

A PASS moves the run to Delivery. Delivery produces a report from current authorized
state, applies the full Writing Guide to each style-bearing semantic stage, performs a
separate research-integrity review, resolves citations deterministically, publishes the
artifact, validates it, and closes the run. Unsupported report content returns to
Research instead of being repaired through prose alone.

## Recovery checklist

On a resumed run:

1. Call the lifecycle-appropriate view command.
2. Record the current revision and current contract revision.
3. Inspect open gaps and latest completion feedback.
4. Inspect relevant approaches, findings, problems, and papers.
5. Review audit history for search terms, date filters, offsets, and failed attempts.
6. Select the next evidence need; do not repeat the previous session mechanically.
