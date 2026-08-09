"""Provider-neutral paper search observation and action boundary."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from my_search_harness.domain.model import LifecycleMode

from .persistence import JsonResearchRunRepository, RevisionConflictError


_PAPER_SEARCH_ATTEMPTS = "paper_search_attempts"


@dataclass(slots=True, frozen=True, kw_only=True)
class PaperSearchHit:
    """Ephemeral provider observation; not authoritative research state."""

    title: str
    authors: tuple[str, ...] = ()
    publication_year: int | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    canonical_url: str | None = None
    other_identifiers: Mapping[str, str] = field(default_factory=dict)
    abstract: str | None = None
    provider_summary: str | None = None
    provider_score: float | None = None
    citation_count: int | None = None
    categories: tuple[str, ...] = ()


class ProviderFailureKind(StrEnum):
    AUTHENTICATION = "AUTHENTICATION"
    RATE_LIMIT = "RATE_LIMIT"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    OTHER = "OTHER"


class PaperSearchProviderError(RuntimeError):
    """Provider-neutral failure raised by a paper search adapter."""

    def __init__(self, failure_kind: ProviderFailureKind, message: str) -> None:
        super().__init__(message)
        self.failure_kind = failure_kind


class PaperSearchConfigurationError(RuntimeError):
    """Paper search cannot be configured locally without external I/O."""


class PaperSearchRejectedError(RuntimeError):
    """Paper search is invalid for the current local state or request."""


class PaperSearchAttemptError(RuntimeError):
    """An accounted provider attempt failed after its revision was committed."""

    def __init__(
        self,
        *,
        state_revision: int,
        failure_kind: ProviderFailureKind,
    ) -> None:
        super().__init__(f"paper search attempt failed: {failure_kind.value}")
        self.state_revision = state_revision
        self.failure_kind = failure_kind


class PaperSearchProvider(Protocol):
    def search(
        self,
        query: str,
        *,
        limit: int,
    ) -> tuple[PaperSearchHit, ...]: ...


@dataclass(slots=True, frozen=True, kw_only=True)
class PaperSearchResult:
    state_revision: int
    hits: tuple[PaperSearchHit, ...]


class PaperSearchService:
    """Authorize, account, and execute exactly one provider search attempt."""

    def __init__(
        self,
        repository: JsonResearchRunRepository,
        provider: PaperSearchProvider | None,
    ) -> None:
        self._repository = repository
        self._provider = provider

    def search_papers(
        self,
        run_id: str,
        expected_revision: int,
        query: str,
        *,
        limit: int = 10,
    ) -> PaperSearchResult:
        current = self._repository.load(run_id)
        if current.state_revision != expected_revision:
            raise RevisionConflictError(
                f"expected revision {expected_revision}, found "
                f"{current.state_revision}"
            )
        if current.lifecycle is not LifecycleMode.RESEARCH:
            raise PaperSearchRejectedError(
                f"search_papers requires RESEARCH; found {current.lifecycle.value}"
            )
        if not isinstance(query, str) or not query.strip():
            raise PaperSearchRejectedError("query must be a non-empty string")
        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or limit < 1
            or limit > 100
        ):
            raise PaperSearchRejectedError("limit must be an integer from 1 to 100")
        if self._provider is None:
            raise PaperSearchRejectedError("paper search provider is not configured")

        current_usage = current.resources.usage.get(_PAPER_SEARCH_ATTEMPTS, 0)
        local_limit = current.resources.limits.get(_PAPER_SEARCH_ATTEMPTS)
        if local_limit is not None and current_usage >= local_limit:
            raise PaperSearchRejectedError("paper search attempt limit is exhausted")

        attempted = deepcopy(current)
        attempted.state_revision = current.state_revision + 1
        attempted.resources.usage[_PAPER_SEARCH_ATTEMPTS] = current_usage + 1
        self._repository.save(attempted, expected_revision)

        try:
            hits = self._provider.search(query.strip(), limit=limit)
        except PaperSearchProviderError as exc:
            raise PaperSearchAttemptError(
                state_revision=attempted.state_revision,
                failure_kind=exc.failure_kind,
            ) from None
        except Exception:
            raise PaperSearchAttemptError(
                state_revision=attempted.state_revision,
                failure_kind=ProviderFailureKind.OTHER,
            ) from None

        if not isinstance(hits, tuple) or not all(
            isinstance(hit, PaperSearchHit) for hit in hits
        ):
            raise PaperSearchAttemptError(
                state_revision=attempted.state_revision,
                failure_kind=ProviderFailureKind.INVALID_RESPONSE,
            )
        return PaperSearchResult(
            state_revision=attempted.state_revision,
            hits=hits,
        )
