"""DeepXiv SDK adapter for the arXiv paper search capability."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import NoReturn, Protocol

from deepxiv_sdk import (  # type: ignore[import-untyped]
    APIError,
    AuthenticationError,
    RateLimitError,
    Reader,
    ServerError,
)

from .paper_search import (
    PaperSearchConfigurationError,
    PaperSearchHit,
    PaperSearchProviderError,
    ProviderFailureKind,
)


class _Reader(Protocol):
    def search(
        self,
        query: str,
        *,
        size: int,
        source: str,
    ) -> object: ...


ReaderFactory = Callable[..., _Reader]


class DeepXivPaperSearchProvider:
    """Translate the DeepXiv 0.3.1 SDK into provider-neutral observations."""

    def __init__(
        self,
        token: str,
        *,
        reader_factory: ReaderFactory = Reader,
    ) -> None:
        if not isinstance(token, str) or not token.strip():
            raise PaperSearchConfigurationError("DEEPXIV_TOKEN is required")
        self._reader = reader_factory(token=token.strip(), max_retries=0)

    @classmethod
    def from_env(
        cls,
        *,
        reader_factory: ReaderFactory = Reader,
    ) -> DeepXivPaperSearchProvider:
        token = os.environ.get("DEEPXIV_TOKEN")
        if token is None or not token.strip():
            raise PaperSearchConfigurationError("DEEPXIV_TOKEN is required")
        return cls(token, reader_factory=reader_factory)

    def search(
        self,
        query: str,
        *,
        limit: int,
    ) -> tuple[PaperSearchHit, ...]:
        try:
            response = self._reader.search(query, size=limit, source="arxiv")
        except AuthenticationError:
            raise PaperSearchProviderError(
                ProviderFailureKind.AUTHENTICATION,
                "paper search provider rejected authentication",
            ) from None
        except RateLimitError:
            raise PaperSearchProviderError(
                ProviderFailureKind.RATE_LIMIT,
                "paper search provider rate limit was reached",
            ) from None
        except ServerError:
            raise PaperSearchProviderError(
                ProviderFailureKind.UNAVAILABLE,
                "paper search provider is unavailable",
            ) from None
        except APIError:
            raise PaperSearchProviderError(
                ProviderFailureKind.OTHER,
                "paper search provider request failed",
            ) from None
        except Exception:
            raise PaperSearchProviderError(
                ProviderFailureKind.OTHER,
                "paper search provider failed unexpectedly",
            ) from None

        return self._map_response(response)

    @classmethod
    def _map_response(cls, response: object) -> tuple[PaperSearchHit, ...]:
        if not isinstance(response, Mapping):
            cls._invalid_response("top-level response must be an object")
        if response.get("status") != "success":
            cls._invalid_response("top-level status must be success")
        total_count = response.get("total_count")
        if (
            not isinstance(total_count, int)
            or isinstance(total_count, bool)
            or total_count < 0
        ):
            cls._invalid_response("total_count must be a non-negative integer")
        results = response.get("result")
        if not isinstance(results, list):
            cls._invalid_response("result must be an array")

        return tuple(
            cls._map_hit(item, index=index) for index, item in enumerate(results)
        )

    @classmethod
    def _map_hit(cls, value: object, *, index: int) -> PaperSearchHit:
        path = f"result[{index}]"
        if not isinstance(value, Mapping):
            cls._invalid_response(f"{path} must be an object")

        arxiv_id = cls._required_string(value.get("arxiv_id"), f"{path}.arxiv_id")
        title = cls._required_string(value.get("title"), f"{path}.title")
        authors = cls._authors(value.get("authors"), f"{path}.authors")
        publication_year = cls._publication_year(value.get("date"), f"{path}.date")
        canonical_url = cls._optional_string(value.get("url"), f"{path}.url")
        abstract = cls._optional_string(value.get("abstract"), f"{path}.abstract")
        provider_summary = cls._optional_string(value.get("tldr"), f"{path}.tldr")
        provider_score = cls._optional_float(value.get("score"), f"{path}.score")
        citation_count = cls._optional_integer(
            value.get("citation_count"), f"{path}.citation_count"
        )
        categories = cls._categories(value.get("categories"), f"{path}.categories")

        return PaperSearchHit(
            title=title,
            authors=authors,
            publication_year=publication_year,
            doi=None,
            arxiv_id=arxiv_id,
            canonical_url=canonical_url,
            abstract=abstract,
            provider_summary=provider_summary,
            provider_score=provider_score,
            citation_count=citation_count,
            categories=categories,
        )

    @classmethod
    def _authors(cls, value: object, path: str) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            comma_names = tuple(name.strip() for name in value.split(","))
            if not comma_names or any(not name for name in comma_names):
                cls._invalid_response(
                    f"{path} must contain comma-separated non-empty names"
                )
            return comma_names
        if not isinstance(value, list):
            cls._invalid_response(f"{path} must be an array or comma-separated string")
        names: list[str] = []
        for index, author in enumerate(value):
            if isinstance(author, str):
                names.append(cls._required_string(author, f"{path}[{index}]"))
            elif isinstance(author, Mapping):
                names.append(
                    cls._required_string(author.get("name"), f"{path}[{index}].name")
                )
            else:
                cls._invalid_response(
                    f"{path}[{index}] must be a name string or author object"
                )
        return tuple(names)

    @classmethod
    def _publication_year(cls, value: object, path: str) -> int | None:
        if value is None:
            return None
        raw = cls._required_string(value, path)
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).year
        except ValueError:
            cls._invalid_response(f"{path} must be an ISO 8601 date")

    @classmethod
    def _categories(cls, value: object, path: str) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, list) or not all(
            isinstance(category, str) for category in value
        ):
            cls._invalid_response(f"{path} must be an array of strings")
        return tuple(value)

    @classmethod
    def _required_string(cls, value: object, path: str) -> str:
        if not isinstance(value, str) or not value.strip():
            cls._invalid_response(f"{path} must be a non-empty string")
        return value.strip()

    @classmethod
    def _optional_string(cls, value: object, path: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            cls._invalid_response(f"{path} must be a string or null")
        return value

    @classmethod
    def _optional_float(cls, value: object, path: str) -> float | None:
        if value is None:
            return None
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            cls._invalid_response(f"{path} must be numeric or null")
        return float(value)

    @classmethod
    def _optional_integer(cls, value: object, path: str) -> int | None:
        if value is None:
            return None
        if not isinstance(value, int) or isinstance(value, bool):
            cls._invalid_response(f"{path} must be an integer or null")
        return value

    @staticmethod
    def _invalid_response(message: str) -> NoReturn:
        raise PaperSearchProviderError(
            ProviderFailureKind.INVALID_RESPONSE,
            f"invalid paper search provider response: {message}",
        )
