"""Runtime adapters for the core research state kernel."""

from .codec import (
    run_from_dict,
    run_from_json,
    run_to_dict,
    run_to_json,
)
from .persistence import (
    JsonResearchRunRepository,
    RevisionConflictError,
    RunAlreadyExistsError,
    RunNotFoundError,
)

__all__ = [
    "JsonResearchRunRepository",
    "RevisionConflictError",
    "RunAlreadyExistsError",
    "RunNotFoundError",
    "run_from_dict",
    "run_from_json",
    "run_to_dict",
    "run_to_json",
]
