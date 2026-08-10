"""DeepXiv SDK adapter mapping, failures, and retain integration tests."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

from deepxiv_sdk import (  # type: ignore[import-untyped]
    APIError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

from my_search_harness.domain import PaperSource, SourceLocator

from my_search_harness.runtime import (
    CreateRunRequest,
    DeepXivPaperSearchProvider,
    DeepXivSourceAccessProvider,
    JsonResearchRunRepository,
    PaperSearchConfigurationError,
    PaperSearchProviderError,
    PaperSearchService,
    ProviderFailureKind,
    ResearchCommands,
    SourceAccessConfigurationError,
    SourceAccessFailureKind,
    SourceAccessProviderError,
)


def deepxiv_response() -> dict[str, object]:
    return {
        "status": "success",
        "total_count": 1,
        "result": [
            {
                "arxiv_id": "2608.00001v2",
                "title": "Agentic Search Systems",
                "authors": [
                    {"name": "Ada Example", "orgs": ["Example Lab"]},
                    {"name": "Lin Example", "orgs": []},
                ],
                "url": "https://arxiv.org/abs/2608.00001",
                "date": "2026-08-01T10:30:00Z",
                "abstract": "A primary-source abstract supplied by the provider.",
                "tldr": "Provider-generated interpretation.",
                "score": 0.91,
                "citation_count": 7,
                "categories": ["cs.IR", "cs.AI"],
            }
        ],
    }


class DeepXivPaperSearchProviderTests(TestCase):
    def _provider(self, reader: Mock) -> tuple[DeepXivPaperSearchProvider, Mock]:
        factory = Mock(return_value=reader)
        provider = DeepXivPaperSearchProvider(
            "fixture-token",
            reader_factory=factory,
        )
        return provider, factory

    def test_reader_receives_explicit_token_and_zero_retries(self) -> None:
        reader = Mock()

        _, factory = self._provider(reader)

        factory.assert_called_once_with(token="fixture-token", max_retries=0)

    def test_search_fixes_arxiv_source_and_maps_response(self) -> None:
        reader = Mock()
        reader.search.return_value = deepxiv_response()
        provider, _ = self._provider(reader)

        hits = provider.search("agentic search", limit=3)

        reader.search.assert_called_once_with(
            "agentic search",
            source="arxiv",
            size=3,
            offset=0,
            date_from=None,
            date_to=None,
        )
        self.assertEqual(1, len(hits))
        hit = hits[0]
        self.assertEqual("2608.00001v2", hit.arxiv_id)
        self.assertEqual("Agentic Search Systems", hit.title)
        self.assertEqual(("Ada Example", "Lin Example"), hit.authors)
        self.assertEqual("https://arxiv.org/abs/2608.00001", hit.canonical_url)
        self.assertEqual(2026, hit.publication_year)
        self.assertEqual(
            "A primary-source abstract supplied by the provider.", hit.abstract
        )
        self.assertEqual("Provider-generated interpretation.", hit.provider_summary)
        self.assertEqual(0.91, hit.provider_score)
        self.assertEqual(7, hit.citation_count)
        self.assertEqual(("cs.IR", "cs.AI"), hit.categories)
        self.assertIsNone(hit.doi)

    def test_search_maps_offset_and_date_range_mechanically(self) -> None:
        reader = Mock()
        reader.search.return_value = deepxiv_response()
        provider, _ = self._provider(reader)

        provider.search(
            "frontier cache",
            limit=20,
            offset=40,
            date_from="2025-01-01",
            date_to="2026-08-10",
        )

        reader.search.assert_called_once_with(
            "frontier cache",
            source="arxiv",
            size=20,
            offset=40,
            date_from="2025-01-01",
            date_to="2026-08-10",
        )

    def test_search_maps_individual_date_bounds(self) -> None:
        cases = (
            ("2025-01-01", None),
            (None, "2026-08-10"),
        )
        for date_from, date_to in cases:
            with self.subTest(date_from=date_from, date_to=date_to):
                reader = Mock()
                reader.search.return_value = deepxiv_response()
                provider, _ = self._provider(reader)

                provider.search(
                    "bounded cache",
                    limit=5,
                    date_from=date_from,
                    date_to=date_to,
                )

                reader.search.assert_called_once_with(
                    "bounded cache",
                    source="arxiv",
                    size=5,
                    offset=0,
                    date_from=date_from,
                    date_to=date_to,
                )

    def test_missing_optional_observation_metadata_maps_to_empty_values(self) -> None:
        reader = Mock()
        reader.search.return_value = {
            "status": "success",
            "total_count": 1,
            "result": [{"arxiv_id": "2608.00002", "title": "Minimal"}],
        }
        provider, _ = self._provider(reader)

        hit = provider.search("minimal", limit=1)[0]

        self.assertEqual((), hit.authors)
        self.assertIsNone(hit.publication_year)
        self.assertIsNone(hit.canonical_url)
        self.assertIsNone(hit.abstract)
        self.assertIsNone(hit.provider_summary)
        self.assertIsNone(hit.provider_score)
        self.assertIsNone(hit.citation_count)
        self.assertEqual((), hit.categories)

    def test_current_live_string_author_shape_maps_to_authors(self) -> None:
        reader = Mock()
        reader.search.return_value = {
            "status": "success",
            "total_count": 1,
            "result": [
                {
                    "arxiv_id": "2608.00003",
                    "title": "Current provider shape",
                    "authors": ["Ada Example", "Lin Example"],
                }
            ],
        }
        provider, _ = self._provider(reader)

        hit = provider.search("current shape", limit=1)[0]

        self.assertEqual(("Ada Example", "Lin Example"), hit.authors)

    def test_current_live_comma_separated_author_shape_maps_to_authors(self) -> None:
        reader = Mock()
        reader.search.return_value = {
            "status": "success",
            "total_count": 1,
            "result": [
                {
                    "arxiv_id": "2608.00004",
                    "title": "Current provider string shape",
                    "authors": "Ada Example, Lin Example",
                }
            ],
        }
        provider, _ = self._provider(reader)

        hit = provider.search("current string shape", limit=1)[0]

        self.assertEqual(("Ada Example", "Lin Example"), hit.authors)

    def test_successful_empty_result_returns_empty_tuple(self) -> None:
        reader = Mock()
        reader.search.return_value = {
            "status": "success",
            "total_count": 0,
            "result": [],
        }
        provider, _ = self._provider(reader)

        self.assertEqual((), provider.search("no matches", limit=10))

    def test_malformed_top_level_response_is_explicit_invalid_response(self) -> None:
        responses: tuple[object, ...] = (
            None,
            {},
            {"status": "error", "total_count": 0, "result": []},
            {"status": "success", "result": []},
            {"status": "success", "total_count": 0, "result": None},
        )
        for response in responses:
            with self.subTest(response=response):
                reader = Mock()
                reader.search.return_value = response
                provider, _ = self._provider(reader)

                with self.assertRaises(PaperSearchProviderError) as captured:
                    provider.search("query", limit=1)

                self.assertIs(
                    captured.exception.failure_kind,
                    ProviderFailureKind.INVALID_RESPONSE,
                )

    def test_malformed_critical_identity_is_explicit_invalid_response(self) -> None:
        for item in (
            {"title": "Missing ID"},
            {"arxiv_id": "2608.00001"},
            {"arxiv_id": "", "title": "Empty ID"},
        ):
            with self.subTest(item=item):
                reader = Mock()
                reader.search.return_value = {
                    "status": "success",
                    "total_count": 1,
                    "result": [item],
                }
                provider, _ = self._provider(reader)

                with self.assertRaises(PaperSearchProviderError) as captured:
                    provider.search("query", limit=1)

                self.assertIs(
                    captured.exception.failure_kind,
                    ProviderFailureKind.INVALID_RESPONSE,
                )

    def test_malformed_result_metadata_is_explicit_invalid_response(self) -> None:
        invalid_fields = {
            "authors": [42],
            "date": "not-a-date",
            "score": True,
            "citation_count": "many",
            "categories": [1],
        }
        for field, invalid_value in invalid_fields.items():
            with self.subTest(field=field):
                response = deepxiv_response()
                result = response["result"]
                assert isinstance(result, list)
                item = result[0]
                assert isinstance(item, dict)
                item[field] = invalid_value
                reader = Mock()
                reader.search.return_value = response
                provider, _ = self._provider(reader)

                with self.assertRaises(PaperSearchProviderError) as captured:
                    provider.search("query", limit=1)

                self.assertIs(
                    captured.exception.failure_kind,
                    ProviderFailureKind.INVALID_RESPONSE,
                )

    def test_official_sdk_exceptions_map_to_provider_neutral_kinds(self) -> None:
        cases = (
            (AuthenticationError("bad auth"), ProviderFailureKind.AUTHENTICATION),
            (RateLimitError("limited"), ProviderFailureKind.RATE_LIMIT),
            (ServerError("server"), ProviderFailureKind.UNAVAILABLE),
            (APIError("other"), ProviderFailureKind.OTHER),
        )
        for sdk_error, expected_kind in cases:
            with self.subTest(expected_kind=expected_kind):
                reader = Mock()
                reader.search.side_effect = sdk_error
                provider, _ = self._provider(reader)

                with self.assertRaises(PaperSearchProviderError) as captured:
                    provider.search("query", limit=1)

                self.assertIs(captured.exception.failure_kind, expected_kind)
                self.assertIsNone(captured.exception.__cause__)
                reader.search.assert_called_once()

    def test_missing_environment_token_fails_before_reader_creation(self) -> None:
        factory = Mock()
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(PaperSearchConfigurationError, "DEEPXIV_TOKEN"):
                DeepXivPaperSearchProvider.from_env(reader_factory=factory)

        factory.assert_not_called()

    def test_environment_token_configures_reader_without_auto_registration(
        self,
    ) -> None:
        reader = Mock()
        factory = Mock(return_value=reader)
        with patch.dict(os.environ, {"DEEPXIV_TOKEN": "fixture-token"}, clear=True):
            DeepXivPaperSearchProvider.from_env(reader_factory=factory)

        factory.assert_called_once_with(token="fixture-token", max_retries=0)

    def test_empty_constructor_token_fails_before_reader_creation(self) -> None:
        factory = Mock()

        with self.assertRaises(PaperSearchConfigurationError):
            DeepXivPaperSearchProvider(" ", reader_factory=factory)

        factory.assert_not_called()


class DeepXivRetainIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name) / "runs"
        self.repository = JsonResearchRunRepository(self.root)
        self.research = ResearchCommands(self.repository)
        self.created = self.research.create_run(
            CreateRunRequest(
                mission="Find and retain one arXiv paper",
                requirements=("Find a candidate",),
                scope="arXiv only",
                deliverable_description="Persistent paper bibliography",
                required_artifacts=frozenset(),
            )
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_search_observation_requires_explicit_retain_and_drops_provider_signals(
        self,
    ) -> None:
        reader = Mock()
        reader.search.return_value = deepxiv_response()
        provider = DeepXivPaperSearchProvider(
            "fixture-token",
            reader_factory=Mock(return_value=reader),
        )
        service = PaperSearchService(self.repository, provider)

        searched = service.search_papers(self.created.run_id, 1, "agentic search")
        after_search = self.repository.load(self.created.run_id)

        self.assertEqual({}, after_search.papers)
        self.assertEqual(
            "Provider-generated interpretation.", searched.hits[0].provider_summary
        )
        retained = self.research.retain_papers(
            self.created.run_id,
            searched.state_revision,
            searched.hits,
        )
        run = self.repository.load(self.created.run_id)
        paper = run.papers[retained.paper_refs[0]]

        self.assertEqual("Agentic Search Systems", paper.source.title)
        self.assertEqual(("Ada Example", "Lin Example"), paper.source.authors)
        self.assertEqual(2026, paper.source.publication_year)
        self.assertEqual("2608.00001v2", paper.source.arxiv_id)
        self.assertEqual("https://arxiv.org/abs/2608.00001", paper.source.canonical_url)
        self.assertIsNone(paper.source.doi)
        self.assertEqual({}, paper.source.other_identifiers)
        self.assertIsNone(paper.analysis)
        self.assertFalse(hasattr(paper, "provider_summary"))
        self.assertFalse(hasattr(paper.source, "provider_summary"))
        self.assertFalse(hasattr(paper.source, "provider_score"))
        self.assertFalse(hasattr(paper.source, "citation_count"))


class DeepXivSourceAccessProviderTests(TestCase):
    def _provider(self, reader: Mock) -> tuple[DeepXivSourceAccessProvider, Mock]:
        factory = Mock(return_value=reader)
        provider = DeepXivSourceAccessProvider(
            "fixture-token",
            reader_factory=factory,
        )
        return provider, factory

    @staticmethod
    def _source(arxiv_id: str | None = "2608.00001v2") -> PaperSource:
        return PaperSource(
            title="A retained paper",
            arxiv_id=arxiv_id,
        )

    def test_reader_receives_explicit_token_and_zero_retries(self) -> None:
        reader = Mock()

        _, factory = self._provider(reader)

        factory.assert_called_once_with(token="fixture-token", max_retries=0)

    def test_inspect_maps_list_sections_without_provider_summaries(self) -> None:
        reader = Mock()
        reader.head.return_value = {
            "title": "A retained paper",
            "token_count": 4321,
            "sections": [
                {"name": "1 Introduction", "tldr": "AI interpretation"},
                {"name": "2 Method", "tldr": "Another interpretation"},
            ],
        }
        provider, _ = self._provider(reader)

        outline = provider.inspect_source("paper_ref", self._source())

        reader.head.assert_called_once_with("2608.00001")
        self.assertEqual("paper_ref", outline.paper_ref)
        self.assertEqual(4321, outline.total_tokens)
        self.assertEqual(
            ("1 Introduction", "2 Method"),
            tuple(section.title for section in outline.sections),
        )
        self.assertEqual(
            SourceLocator(kind="section", value="2 Method"),
            outline.sections[1].locator,
        )
        self.assertFalse(hasattr(outline.sections[0], "tldr"))

    def test_inspect_maps_current_mapping_section_shape(self) -> None:
        reader = Mock()
        reader.head.return_value = {
            "sections": {
                "1 Introduction": {"tldr": "discarded"},
                "2 Method": {"tldr": "discarded"},
            }
        }
        provider, _ = self._provider(reader)

        outline = provider.inspect_source("paper_ref", self._source())

        self.assertEqual(
            ("1 Introduction", "2 Method"),
            tuple(section.title for section in outline.sections),
        )
        self.assertIsNone(outline.total_tokens)

    def test_whole_source_read_uses_raw_primary_content(self) -> None:
        reader = Mock()
        reader.raw.return_value = "# Paper\n\nPrimary source text."
        provider, _ = self._provider(reader)

        content = provider.read_source("paper_ref", self._source(), None)

        reader.raw.assert_called_once_with("2608.00001")
        self.assertEqual("paper_ref", content.paper_ref)
        self.assertIsNone(content.locator)
        self.assertEqual("# Paper\n\nPrimary source text.", content.content)

    def test_section_read_resolves_actual_section_and_returns_it(self) -> None:
        reader = Mock()
        reader.head.return_value = {
            "sections": [
                {"name": "1 Introduction"},
                {"name": "3 Experimental Method"},
            ]
        }
        reader.section.return_value = "Primary method content."
        provider, _ = self._provider(reader)

        content = provider.read_source(
            "paper_ref",
            self._source(),
            SourceLocator(kind="section", value="experimental method"),
        )

        reader.head.assert_called_once_with("2608.00001")
        reader.section.assert_called_once_with("2608.00001", "3 Experimental Method")
        self.assertEqual(
            SourceLocator(kind="section", value="3 Experimental Method"),
            content.locator,
        )
        self.assertEqual("Primary method content.", content.content)

    def test_ambiguous_or_missing_section_is_locator_not_found(self) -> None:
        cases = (
            (
                [
                    {"name": "2 Method Overview"},
                    {"name": "3 Method Details"},
                ],
                "method",
            ),
            ([{"name": "1 Introduction"}], "experiments"),
        )
        for sections, requested in cases:
            with self.subTest(requested=requested):
                reader = Mock()
                reader.head.return_value = {"sections": sections}
                provider, _ = self._provider(reader)

                with self.assertRaises(SourceAccessProviderError) as captured:
                    provider.read_source(
                        "paper_ref",
                        self._source(),
                        SourceLocator(kind="section", value=requested),
                    )

                self.assertIs(
                    SourceAccessFailureKind.LOCATOR_NOT_FOUND,
                    captured.exception.failure_kind,
                )
                reader.section.assert_not_called()

    def test_sdk_section_value_error_is_locator_not_found(self) -> None:
        reader = Mock()
        reader.head.return_value = {"sections": [{"name": "2 Method"}]}
        reader.section.side_effect = ValueError("not found")
        provider, _ = self._provider(reader)

        with self.assertRaises(SourceAccessProviderError) as captured:
            provider.read_source(
                "paper_ref",
                self._source(),
                SourceLocator(kind="section", value="2 Method"),
            )

        self.assertIs(
            SourceAccessFailureKind.LOCATOR_NOT_FOUND,
            captured.exception.failure_kind,
        )

    def test_non_section_locator_fails_preflight_without_reader_call(self) -> None:
        reader = Mock()
        provider, _ = self._provider(reader)

        with self.assertRaises(SourceAccessProviderError) as captured:
            provider.validate_read(
                self._source(),
                SourceLocator(kind="table", value="Table 2"),
            )

        self.assertIs(
            SourceAccessFailureKind.UNSUPPORTED_LOCATOR,
            captured.exception.failure_kind,
        )
        reader.assert_not_called()

    def test_missing_arxiv_identity_fails_preflight_without_reader_call(self) -> None:
        reader = Mock()
        provider, _ = self._provider(reader)

        with self.assertRaises(SourceAccessProviderError) as captured:
            provider.validate_inspect(self._source(arxiv_id=None))

        self.assertIs(
            SourceAccessFailureKind.SOURCE_UNAVAILABLE,
            captured.exception.failure_kind,
        )
        reader.assert_not_called()

    def test_empty_or_malformed_provider_payload_is_invalid_response(self) -> None:
        cases: tuple[tuple[str, object], ...] = (
            ("head", None),
            ("head", {}),
            ("head", {"sections": None}),
            ("head", {"sections": [{"title": "wrong key"}]}),
            ("head", {"sections": [], "token_count": True}),
            ("raw", ""),
            ("raw", " \n"),
            ("raw", {"content": "not a string response"}),
        )
        for method, response in cases:
            with self.subTest(method=method, response=response):
                reader = Mock()
                setattr(getattr(reader, method), "return_value", response)
                provider, _ = self._provider(reader)

                with self.assertRaises(SourceAccessProviderError) as captured:
                    if method == "head":
                        provider.inspect_source("paper_ref", self._source())
                    else:
                        provider.read_source("paper_ref", self._source(), None)

                self.assertIs(
                    SourceAccessFailureKind.INVALID_RESPONSE,
                    captured.exception.failure_kind,
                )

    def test_sdk_failures_map_to_source_unavailable(self) -> None:
        sdk_errors = (
            AuthenticationError("bad auth"),
            RateLimitError("limited"),
            ServerError("server"),
            NotFoundError("missing"),
            BadRequestError("bad id"),
            APIError("other"),
        )
        for sdk_error in sdk_errors:
            with self.subTest(sdk_error=type(sdk_error).__name__):
                reader = Mock()
                reader.head.side_effect = sdk_error
                provider, _ = self._provider(reader)

                with self.assertRaises(SourceAccessProviderError) as captured:
                    provider.inspect_source("paper_ref", self._source())

                self.assertIs(
                    SourceAccessFailureKind.SOURCE_UNAVAILABLE,
                    captured.exception.failure_kind,
                )
                self.assertIsNone(captured.exception.__cause__)

    def test_missing_environment_token_fails_before_reader_creation(self) -> None:
        factory = Mock()
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                SourceAccessConfigurationError, "DEEPXIV_TOKEN"
            ):
                DeepXivSourceAccessProvider.from_env(reader_factory=factory)

        factory.assert_not_called()

    def test_environment_token_configures_reader_without_hidden_retries(self) -> None:
        reader = Mock()
        factory = Mock(return_value=reader)
        with patch.dict(os.environ, {"DEEPXIV_TOKEN": "fixture-token"}, clear=True):
            DeepXivSourceAccessProvider.from_env(reader_factory=factory)

        factory.assert_called_once_with(token="fixture-token", max_retries=0)
