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
    RateLimitError,
    ServerError,
)

from my_search_harness.runtime import (
    CreateRunRequest,
    DeepXivPaperSearchProvider,
    JsonResearchRunRepository,
    PaperSearchConfigurationError,
    PaperSearchProviderError,
    PaperSearchService,
    ProviderFailureKind,
    ResearchCommands,
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
            size=3,
            source="arxiv",
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
