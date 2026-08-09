"""End-to-end command tests for the core research loop vertical slice."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from my_search_harness.domain import (
    ArtifactKind,
    CompletionPassBasis,
    CompletionVerdict,
    InvestigationGap,
    LifecycleMode,
    LiteratureSource,
    Paper,
    PaperAnalysis,
    PaperResearchStatus,
    PaperSource,
    SourceRelation,
)
from my_search_harness.runtime import (
    CommandRejectedError,
    CompletionSubmissionConflictError,
    CreateRunRequest,
    JsonResearchRunRepository,
    NewBlockingGap,
    PaperSearchHit,
    PutLandscapeFinding,
    PutPaperAnalysis,
    ReopenBlockingGap,
    ResearchCommands,
    ResearchMutationBatch,
    RevisionConflictError,
)


class ResearchCommandsTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name) / "runs"
        self.repository = JsonResearchRunRepository(self.root)
        self.commands = ResearchCommands(self.repository)
        self.created = self.commands.create_run(
            CreateRunRequest(
                mission="Map the research area",
                requirements=("Explain the main result", "Identify limitations"),
                scope="A bounded V1 study",
                deliverable_description="A cited report",
                required_artifacts=frozenset({ArtifactKind.REPORT}),
            )
        )
        self.run_id = self.created.run_id

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _retain_paper(
        self,
        *,
        expected_revision: int = 1,
        doi: str | None = "10.1000/example",
        arxiv_id: str | None = None,
        title: str = "Example paper",
    ):
        return self.commands.retain_papers(
            self.run_id,
            expected_revision,
            (
                PaperSearchHit(
                    title=title,
                    authors=("Ada Example",),
                    publication_year=2026,
                    doi=doi,
                    arxiv_id=arxiv_id,
                    canonical_url="https://example.test/Paper",
                    other_identifiers={"catalog": "P-42"},
                ),
            ),
        )

    def _request_check(self, expected_revision: int = 1):
        return self.commands.request_completion_check(
            self.run_id,
            expected_revision,
            "The current landscape appears sufficient",
        )

    def _new_gap(self, description: str = "Investigate the remaining limitation"):
        return NewBlockingGap(
            description=description,
            requirement_refs=frozenset({self.created.requirement_refs[1]}),
        )

    def test_create_run_starts_at_revision_one_in_research(self) -> None:
        run = self.repository.load(self.run_id)

        self.assertEqual(1, self.created.state_revision)
        self.assertEqual(1, run.state_revision)
        self.assertIs(run.lifecycle, LifecycleMode.RESEARCH)
        self.assertEqual(1, run.contract.current_revision)
        self.assertEqual(1, len(run.contract.revisions))

    def test_create_run_allocates_stable_requirement_refs(self) -> None:
        self.assertEqual(2, len(self.created.requirement_refs))
        self.assertEqual(2, len(set(self.created.requirement_refs)))
        self.assertTrue(
            all(ref.startswith("requirement_") for ref in self.created.requirement_refs)
        )

    def test_create_run_is_recoverable_from_repository(self) -> None:
        run = self.repository.load(self.run_id)
        contract = run.contract.revisions[0].contract

        self.assertEqual("Map the research area", contract.mission)
        self.assertEqual(set(self.created.requirement_refs), set(contract.requirements))
        self.assertEqual({ArtifactKind.REPORT}, contract.deliverable.required_artifacts)

    def test_retain_new_hit_creates_active_unanalysed_paper(self) -> None:
        result = self._retain_paper()
        run = self.repository.load(self.run_id)
        paper = run.papers[result.paper_refs[0]]

        self.assertEqual(2, result.state_revision)
        self.assertEqual(1, len(run.papers))
        self.assertIs(paper.research_status, PaperResearchStatus.ACTIVE)
        self.assertIsNone(paper.analysis)
        self.assertEqual("10.1000/example", paper.source.doi)
        self.assertEqual({"catalog": "P-42"}, paper.source.other_identifiers)

    def test_retain_normalized_duplicate_doi_returns_existing_ref(self) -> None:
        first = self._retain_paper()
        second = self.commands.retain_papers(
            self.run_id,
            2,
            (
                PaperSearchHit(
                    title="Provider variant",
                    doi="https://doi.org/10.1000/EXAMPLE",
                ),
            ),
        )

        self.assertEqual(first.paper_refs, second.paper_refs)
        self.assertEqual(1, len(self.repository.load(self.run_id).papers))

    def test_retain_normalized_duplicate_arxiv_returns_existing_ref(self) -> None:
        first = self._retain_paper(doi=None, arxiv_id="2608.00001v2")
        second = self.commands.retain_papers(
            self.run_id,
            2,
            (
                PaperSearchHit(
                    title="Provider variant",
                    arxiv_id="https://arxiv.org/pdf/2608.00001.pdf",
                ),
            ),
        )

        self.assertEqual(first.paper_refs, second.paper_refs)
        self.assertEqual(1, len(self.repository.load(self.run_id).papers))

    def test_retain_safely_enriches_missing_doi(self) -> None:
        retained = self._retain_paper(doi=None, arxiv_id="2608.00001")
        enriched = self.commands.retain_papers(
            self.run_id,
            2,
            (
                PaperSearchHit(
                    title="Same paper",
                    arxiv_id="2608.00001v3",
                    doi="10.1000/enriched",
                ),
            ),
        )
        paper = self.repository.load(self.run_id).papers[retained.paper_refs[0]]

        self.assertEqual(retained.paper_refs, enriched.paper_refs)
        self.assertEqual("10.1000/enriched", paper.source.doi)

    def test_retain_rejects_conflicting_doi_on_arxiv_match(self) -> None:
        self._retain_paper(doi="10.1000/first", arxiv_id="2608.00001")

        with self.assertRaisesRegex(CommandRejectedError, "conflicting DOI"):
            self.commands.retain_papers(
                self.run_id,
                2,
                (
                    PaperSearchHit(
                        title="Conflicting identity",
                        doi="10.1000/second",
                        arxiv_id="2608.00001v2",
                    ),
                ),
            )

        run = self.repository.load(self.run_id)
        self.assertEqual(2, run.state_revision)
        self.assertEqual("10.1000/first", next(iter(run.papers.values())).source.doi)

    def test_retain_rejects_keys_resolving_to_two_papers(self) -> None:
        retained = self.commands.retain_papers(
            self.run_id,
            1,
            (
                PaperSearchHit(title="DOI paper", doi="10.1000/first"),
                PaperSearchHit(title="arXiv paper", arxiv_id="2608.00001"),
            ),
        )

        with self.assertRaisesRegex(CommandRejectedError, "multiple persistent"):
            self.commands.retain_papers(
                self.run_id,
                retained.state_revision,
                (
                    PaperSearchHit(
                        title="Ambiguous hit",
                        doi="10.1000/first",
                        arxiv_id="2608.00001",
                    ),
                ),
            )

        self.assertEqual(2, len(self.repository.load(self.run_id).papers))

    def test_rejected_retain_batch_does_not_persist_earlier_hit(self) -> None:
        retained = self.commands.retain_papers(
            self.run_id,
            1,
            (
                PaperSearchHit(title="DOI paper", doi="10.1000/first"),
                PaperSearchHit(title="arXiv paper", arxiv_id="2608.00001"),
            ),
        )
        before_path = self.root / self.run_id / "state.json"
        before_bytes = before_path.read_bytes()

        with self.assertRaises(CommandRejectedError):
            self.commands.retain_papers(
                self.run_id,
                retained.state_revision,
                (
                    PaperSearchHit(title="Would be new", doi="10.1000/new"),
                    PaperSearchHit(
                        title="Ambiguous hit",
                        doi="10.1000/first",
                        arxiv_id="2608.00001",
                    ),
                ),
            )

        self.assertEqual(before_bytes, before_path.read_bytes())
        self.assertEqual(2, len(self.repository.load(self.run_id).papers))

    def test_title_similarity_does_not_automatically_deduplicate(self) -> None:
        result = self.commands.retain_papers(
            self.run_id,
            1,
            (
                PaperSearchHit(title="Same title", authors=("One",)),
                PaperSearchHit(title="Same title", authors=("One",)),
            ),
        )

        self.assertNotEqual(result.paper_refs[0], result.paper_refs[1])
        self.assertEqual(2, len(self.repository.load(self.run_id).papers))

    def test_retain_papers_rejects_non_research_lifecycle(self) -> None:
        requested = self._request_check()

        with self.assertRaisesRegex(CommandRejectedError, "requires RESEARCH"):
            self.commands.retain_papers(
                self.run_id,
                requested.state_revision,
                (PaperSearchHit(title="Not allowed", doi="10.1000/not-allowed"),),
            )

        self.assertEqual(2, self.repository.load(self.run_id).state_revision)

    def test_research_mutation_commits_analysis_and_finding_once(self) -> None:
        retained = self._retain_paper()
        paper_ref = retained.paper_refs[0]
        result = self.commands.apply_research_mutation(
            self.run_id,
            2,
            ResearchMutationBatch(
                puts=(
                    PutPaperAnalysis(
                        paper_ref=paper_ref,
                        analysis=PaperAnalysis(
                            summary="A useful result",
                            relevance_to_run="Directly addresses the mission",
                        ),
                    ),
                    PutLandscapeFinding(
                        statement="The method improves the main metric",
                        sources=frozenset(
                            {
                                LiteratureSource(
                                    paper_ref=paper_ref,
                                    relation=SourceRelation.SUPPORTS,
                                )
                            }
                        ),
                    ),
                )
            ),
        )
        run = self.repository.load(self.run_id)
        analysis = run.papers[paper_ref].analysis

        self.assertEqual(3, result.state_revision)
        self.assertEqual(3, run.state_revision)
        self.assertIsNotNone(analysis)
        assert analysis is not None
        self.assertEqual("A useful result", analysis.summary)
        self.assertEqual(1, len(run.literature_landscape.findings))

    def test_finding_source_can_reference_retained_paper(self) -> None:
        retained = self._retain_paper()
        paper_ref = retained.paper_refs[0]
        result = self.commands.apply_research_mutation(
            self.run_id,
            2,
            ResearchMutationBatch(
                puts=(
                    PutLandscapeFinding(
                        statement="Grounded finding",
                        sources=frozenset(
                            {
                                LiteratureSource(
                                    paper_ref=paper_ref,
                                    relation=SourceRelation.QUALIFIES,
                                )
                            }
                        ),
                    ),
                )
            ),
        )
        finding = self.repository.load(self.run_id).literature_landscape.findings[
            result.finding_refs[0]
        ]

        self.assertEqual({paper_ref}, {source.paper_ref for source in finding.sources})

    def test_dangling_finding_source_rejects_whole_batch(self) -> None:
        retained = self._retain_paper()
        paper_ref = retained.paper_refs[0]
        missing_ref = Paper(source=PaperSource(title="Missing")).id

        with self.assertRaisesRegex(CommandRejectedError, "dangling paper"):
            self.commands.apply_research_mutation(
                self.run_id,
                2,
                ResearchMutationBatch(
                    puts=(
                        PutPaperAnalysis(
                            paper_ref=paper_ref,
                            analysis=PaperAnalysis(
                                summary="Must roll back",
                                relevance_to_run="Relevant",
                            ),
                        ),
                        PutLandscapeFinding(
                            statement="Invalid finding",
                            sources=frozenset(
                                {
                                    LiteratureSource(
                                        paper_ref=missing_ref,
                                        relation=SourceRelation.SUPPORTS,
                                    )
                                }
                            ),
                        ),
                    )
                ),
            )

        run = self.repository.load(self.run_id)
        self.assertEqual(2, run.state_revision)
        self.assertIsNone(run.papers[paper_ref].analysis)
        self.assertFalse(run.literature_landscape.findings)

    def test_research_mutation_rejects_missing_paper_target(self) -> None:
        missing_ref = Paper(source=PaperSource(title="Missing")).id

        with self.assertRaisesRegex(CommandRejectedError, "does not exist"):
            self.commands.apply_research_mutation(
                self.run_id,
                1,
                ResearchMutationBatch(
                    puts=(
                        PutPaperAnalysis(
                            paper_ref=missing_ref,
                            analysis=PaperAnalysis(
                                summary="Invalid",
                                relevance_to_run="Invalid",
                            ),
                        ),
                    )
                ),
            )

        self.assertEqual(1, self.repository.load(self.run_id).state_revision)

    def test_research_mutation_rejects_non_research_lifecycle(self) -> None:
        requested = self._request_check()

        with self.assertRaisesRegex(CommandRejectedError, "requires RESEARCH"):
            self.commands.apply_research_mutation(
                self.run_id,
                requested.state_revision,
                ResearchMutationBatch(
                    puts=(PutLandscapeFinding(statement="Not allowed"),)
                ),
            )

        self.assertEqual(2, self.repository.load(self.run_id).state_revision)

    def test_request_completion_check_enters_completion_lifecycle(self) -> None:
        result = self._request_check()
        run = self.repository.load(self.run_id)

        self.assertEqual(2, result.state_revision)
        self.assertIs(run.lifecycle, LifecycleMode.COMPLETION_CHECK)

    def test_request_completion_check_creates_one_pending_check(self) -> None:
        result = self._request_check()
        run = self.repository.load(self.run_id)
        check = run.completion_checks[result.completion_check_ref]

        self.assertEqual(1, len(run.completion_checks))
        self.assertIsNone(check.verdict)
        self.assertIsNone(check.completed_at)

    def test_request_basis_revision_is_resulting_revision(self) -> None:
        result = self._request_check()
        check = self.repository.load(self.run_id).completion_checks[
            result.completion_check_ref
        ]

        self.assertEqual(result.state_revision, check.basis_revision)

    def test_request_basis_contract_revision_is_current_contract(self) -> None:
        result = self._request_check()
        run = self.repository.load(self.run_id)

        self.assertEqual(
            run.contract.current_revision,
            run.completion_checks[result.completion_check_ref].basis_contract_revision,
        )

    def test_request_completion_check_rejects_non_research_lifecycle(self) -> None:
        requested = self._request_check()

        with self.assertRaisesRegex(CommandRejectedError, "requires RESEARCH"):
            self.commands.request_completion_check(
                self.run_id,
                requested.state_revision,
                "Duplicate request",
            )

        self.assertEqual(2, self.repository.load(self.run_id).state_revision)

    def test_submit_pass_enters_delivery(self) -> None:
        requested = self._request_check()
        result = self.commands.submit_completion_check(
            self.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("All requirements are covered",),
        )
        run = self.repository.load(self.run_id)

        self.assertEqual(3, result.state_revision)
        self.assertIs(run.lifecycle, LifecycleMode.DELIVERY)
        self.assertIs(
            run.completion_checks[result.completion_check_ref].verdict,
            CompletionVerdict.PASS,
        )

    def test_submit_pass_sets_completion_delivery_basis(self) -> None:
        requested = self._request_check()
        self.commands.submit_completion_check(
            self.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("All requirements are covered",),
        )
        basis = self.repository.load(self.run_id).delivery_basis

        self.assertIsInstance(basis, CompletionPassBasis)
        assert isinstance(basis, CompletionPassBasis)
        self.assertEqual(requested.completion_check_ref, basis.completion_check_ref)

    def test_submit_pass_rejects_blocking_gap_specs(self) -> None:
        requested = self._request_check()

        with self.assertRaisesRegex(CommandRejectedError, "must not include"):
            self.commands.submit_completion_check(
                self.run_id,
                2,
                requested.completion_check_ref,
                CompletionVerdict.PASS,
                ("Contradictory payload",),
                (self._new_gap(),),
            )

        run = self.repository.load(self.run_id)
        self.assertEqual(2, run.state_revision)
        self.assertIs(run.lifecycle, LifecycleMode.COMPLETION_CHECK)

    def test_same_pass_retry_returns_existing_fact_without_revision(self) -> None:
        requested = self._request_check()
        first = self.commands.submit_completion_check(
            self.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("All requirements are covered",),
        )
        retry = self.commands.submit_completion_check(
            self.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("All requirements are covered",),
        )

        self.assertEqual(first, retry)
        self.assertEqual(3, self.repository.load(self.run_id).state_revision)

    def test_conflicting_second_verdict_is_rejected(self) -> None:
        requested = self._request_check()
        self.commands.submit_completion_check(
            self.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("All requirements are covered",),
        )

        with self.assertRaises(CompletionSubmissionConflictError):
            self.commands.submit_completion_check(
                self.run_id,
                2,
                requested.completion_check_ref,
                CompletionVerdict.CONTINUE,
                ("Actually incomplete",),
            )

        self.assertEqual(3, self.repository.load(self.run_id).state_revision)

    def test_conflicting_second_reasons_are_rejected(self) -> None:
        requested = self._request_check()
        self.commands.submit_completion_check(
            self.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.PASS,
            ("Original reasons",),
        )

        with self.assertRaises(CompletionSubmissionConflictError):
            self.commands.submit_completion_check(
                self.run_id,
                3,
                requested.completion_check_ref,
                CompletionVerdict.PASS,
                ("Rewritten reasons",),
            )

    def test_submit_continue_returns_to_research(self) -> None:
        requested = self._request_check()
        result = self.commands.submit_completion_check(
            self.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.CONTINUE,
            ("A blocking limitation remains",),
            (self._new_gap(),),
        )

        self.assertEqual(3, result.state_revision)
        self.assertIs(
            self.repository.load(self.run_id).lifecycle, LifecycleMode.RESEARCH
        )

    def test_submit_continue_atomically_creates_new_blocking_gap(self) -> None:
        requested = self._request_check()
        result = self.commands.submit_completion_check(
            self.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.CONTINUE,
            ("A blocking limitation remains",),
            (self._new_gap(),),
        )
        run = self.repository.load(self.run_id)
        check = run.completion_checks[requested.completion_check_ref]

        self.assertEqual(1, len(run.investigation_gaps))
        self.assertEqual(set(result.blocking_gap_refs), check.blocking_gap_refs)
        gap = run.investigation_gaps[next(iter(check.blocking_gap_refs))]
        self.assertIsNone(gap.resolution)
        self.assertEqual(3, run.state_revision)

    def test_submit_continue_reopens_resolved_gap(self) -> None:
        seeded = self.repository.load(self.run_id)
        gap = InvestigationGap(
            description="Previously resolved",
            requirement_refs={self.created.requirement_refs[0]},
            resolution="Earlier answer",
        )
        seeded.investigation_gaps[gap.id] = gap
        seeded.state_revision = 2
        self.repository.save(seeded, expected_revision=1)
        requested = self._request_check(expected_revision=2)

        result = self.commands.submit_completion_check(
            self.run_id,
            3,
            requested.completion_check_ref,
            CompletionVerdict.CONTINUE,
            ("The prior answer no longer resolves the gap",),
            (ReopenBlockingGap(gap_ref=gap.id),),
        )
        run = self.repository.load(self.run_id)

        self.assertEqual(frozenset({gap.id}), result.blocking_gap_refs)
        self.assertIsNone(run.investigation_gaps[gap.id].resolution)
        self.assertEqual(1, len(run.investigation_gaps))

    def test_invalid_gap_spec_rolls_back_entire_submit(self) -> None:
        requested = self._request_check()
        missing_gap_ref = InvestigationGap(description="Missing").id

        with self.assertRaisesRegex(CommandRejectedError, "does not exist"):
            self.commands.submit_completion_check(
                self.run_id,
                2,
                requested.completion_check_ref,
                CompletionVerdict.CONTINUE,
                ("A blocking limitation remains",),
                (
                    self._new_gap("Would otherwise be created"),
                    ReopenBlockingGap(gap_ref=missing_gap_ref),
                ),
            )

        run = self.repository.load(self.run_id)
        check = run.completion_checks[requested.completion_check_ref]
        self.assertEqual(2, run.state_revision)
        self.assertFalse(run.investigation_gaps)
        self.assertIsNone(check.verdict)
        self.assertIs(run.lifecycle, LifecycleMode.COMPLETION_CHECK)

    def test_continue_retry_does_not_create_duplicate_gap(self) -> None:
        requested = self._request_check()
        spec = self._new_gap()
        first = self.commands.submit_completion_check(
            self.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.CONTINUE,
            ("A blocking limitation remains",),
            (spec,),
        )
        retry = self.commands.submit_completion_check(
            self.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.CONTINUE,
            ("A blocking limitation remains",),
            (spec,),
        )
        run = self.repository.load(self.run_id)

        self.assertEqual(first, retry)
        self.assertEqual(3, run.state_revision)
        self.assertEqual(1, len(run.investigation_gaps))

    def test_submit_continue_requires_blocking_gap(self) -> None:
        requested = self._request_check()

        with self.assertRaisesRegex(CommandRejectedError, "requires at least one"):
            self.commands.submit_completion_check(
                self.run_id,
                2,
                requested.completion_check_ref,
                CompletionVerdict.CONTINUE,
                ("Incomplete without structured gap",),
            )

    def test_submit_uncertain_returns_to_research(self) -> None:
        requested = self._request_check()
        result = self.commands.submit_completion_check(
            self.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.UNCERTAIN,
            ("The contract boundary is ambiguous",),
        )

        self.assertEqual(3, result.state_revision)
        self.assertIs(
            self.repository.load(self.run_id).lifecycle, LifecycleMode.RESEARCH
        )

    def test_submit_uncertain_creates_no_basis_or_gap(self) -> None:
        requested = self._request_check()
        self.commands.submit_completion_check(
            self.run_id,
            2,
            requested.completion_check_ref,
            CompletionVerdict.UNCERTAIN,
            ("The contract boundary is ambiguous",),
        )
        run = self.repository.load(self.run_id)

        self.assertIsNone(run.delivery_basis)
        self.assertFalse(run.investigation_gaps)
        self.assertFalse(
            run.completion_checks[requested.completion_check_ref].blocking_gap_refs
        )

    def test_submit_uncertain_rejects_blocking_gap_specs(self) -> None:
        requested = self._request_check()

        with self.assertRaisesRegex(CommandRejectedError, "must not include"):
            self.commands.submit_completion_check(
                self.run_id,
                2,
                requested.completion_check_ref,
                CompletionVerdict.UNCERTAIN,
                ("The contract boundary is ambiguous",),
                (self._new_gap(),),
            )

        self.assertEqual(2, self.repository.load(self.run_id).state_revision)

    def test_stale_expected_revision_is_rejected(self) -> None:
        with self.assertRaises(RevisionConflictError):
            self.commands.retain_papers(
                self.run_id,
                0,
                (PaperSearchHit(title="Stale", doi="10.1000/stale"),),
            )

        self.assertEqual(1, self.repository.load(self.run_id).state_revision)

    def test_rejected_command_preserves_authoritative_bytes(self) -> None:
        requested = self._request_check()
        state_path = self.root / self.run_id / "state.json"
        before_bytes = state_path.read_bytes()

        with self.assertRaises(CommandRejectedError):
            self.commands.submit_completion_check(
                self.run_id,
                requested.state_revision,
                requested.completion_check_ref,
                CompletionVerdict.PASS,
                ("Invalid PASS",),
                (self._new_gap(),),
            )

        self.assertEqual(before_bytes, state_path.read_bytes())

    def test_one_semantic_batch_advances_exactly_one_revision(self) -> None:
        retained = self.commands.retain_papers(
            self.run_id,
            1,
            (
                PaperSearchHit(title="First", doi="10.1000/first"),
                PaperSearchHit(title="Second", doi="10.1000/second"),
                PaperSearchHit(title="Third", doi="10.1000/third"),
            ),
        )
        run = self.repository.load(self.run_id)

        self.assertEqual(2, retained.state_revision)
        self.assertEqual(2, run.state_revision)
        self.assertEqual(3, len(run.papers))
