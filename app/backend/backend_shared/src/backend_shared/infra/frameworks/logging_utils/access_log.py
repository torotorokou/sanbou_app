"""Access log filters for Uvicorn/ASGI servers.

This module provides a reusable logging.Filter that suppresses access logs
for specific paths (e.g., "/health") while preserving all other logs,
including error and exception logs.

Design:
- Single Responsibility: Only concerns access log filtering logic.
- Open/Closed: Can extend excluded paths via arguments without modifying code.
- Liskov Substitution: Inherits from logging.Filter and respects its contract.
- Interface Segregation: Presents a small function to wire the filter.
- Dependency Inversion: Depends on Python's logging module, not Uvicorn internals.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class AccessLogFilterConfig:
    """Configuration for the access log filter.

    Attributes:
        excluded_paths: Paths for which access logs should be suppressed.
        logger_name: Name of the logger to filter; defaults to "uvicorn.access".
    """

    excluded_paths: tuple[str, ...] = ("/health",)
    logger_name: str = "uvicorn.access"


class PathExcludeAccessFilter(logging.Filter):
    """Filter that drops access logs for configured paths.

    This filter inspects the formatted log message emitted by Uvicorn's
    access logger. Since Uvicorn formats the message before logging, we
    need to match on the final message string (record.getMessage()).
    """

    def __init__(self, excluded_paths: Iterable[str]):
        super().__init__()
        # Build a regex that matches: "METHOD /path HTTP/"
        pattern = r"|".join(re.escape(p.rstrip("/")) for p in excluded_paths)
        if not pattern:
            # No exclusions; never filter out
            self._regex = None
        else:
            self._regex = re.compile(rf'"[A-Z]+ (?:{pattern})(?:/?)(?:[ \?])')

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        """Return True to keep the record, False to drop it.

        Drops the record if the message looks like an access log for an
        excluded path. All other records and loggers pass through.
        """

        # If no regex (no exclusions), keep all records
        if self._regex is None:
            return True

        try:
            message = record.getMessage()
        except Exception:
            # If formatting fails, err on the side of keeping the record
            return True

        # Match only if this looks like an access log line for excluded path(s)
        return not bool(self._regex.search(message))


def setup_uvicorn_access_filter(
    excluded_paths: Iterable[str] | None = None, logger_name: str = "uvicorn.access"
) -> PathExcludeAccessFilter:
    """Attach a PathExcludeAccessFilter to the uvicorn access logger.

    Args:
        excluded_paths: Paths to exclude from access logs. Defaults to ("/health",).
        logger_name: Target logger name. Defaults to "uvicorn.access".

    Returns:
        The filter instance attached to the logger.
    """

    paths = tuple(excluded_paths or ("/health",))
    logger = logging.getLogger(logger_name)

    # Idempotency: avoid stacking duplicate filters across reloads
    for existing in getattr(logger, "filters", []):
        if isinstance(existing, PathExcludeAccessFilter):
            return existing

    filt = PathExcludeAccessFilter(paths)
    logger.addFilter(filt)
    return filt
