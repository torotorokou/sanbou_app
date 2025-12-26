"""Session storage utilities for interactive report flows.

Provides a simple abstraction over session persistence so that
interactive flows can avoid leaking the serialized state to the
frontend.  By default, it falls back to an in-memory dictionary, but it
can make use of Redis when the ``REDIS_URL`` environment variable is
configured and the ``redis`` package is available.

The stored payload is expected to be JSON serialisable (the interactive
report generators already satisfy this constraint by serialising
DataFrames to JSON strings).
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any

from backend_shared.application.logging import get_module_logger


logger = get_module_logger(__name__)


DEFAULT_SESSION_TTL_SECONDS = int(os.getenv("INTERACTIVE_SESSION_TTL", "3600"))

try:  # pragma: no cover - optional dependency
    import redis  # type: ignore
except Exception:  # pragma: no cover - fallback if redis not installed
    redis = None


@dataclass
class _SessionEntry:
    value: dict[str, Any]
    expires_at: float


class _InMemorySessionBackend:
    """Thread-safe in-memory session backend used as a fallback."""

    def __init__(self) -> None:
        self._store: dict[str, _SessionEntry] = {}
        self._lock = threading.Lock()

    def save(self, data: dict[str, Any], ttl: int, session_id: str | None = None) -> str:
        sid = session_id or str(uuid.uuid4())
        entry = _SessionEntry(value=data, expires_at=time.time() + ttl)
        with self._lock:
            self._store[sid] = entry
        return sid

    def load(self, session_id: str) -> dict[str, Any] | None:
        now = time.time()
        with self._lock:
            entry = self._store.get(session_id)
            if not entry:
                return None
            if entry.expires_at < now:
                del self._store[session_id]
                return None
            return entry.value

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)


class _RedisSessionBackend:
    """Redis backed implementation.

    Uses synchronous redis client; the interactive service itself runs in
    normal FastAPI workers so blocking operations are acceptable.  The
    payload is stored as JSON for simplicity.
    """

    def __init__(self, url: str) -> None:
        if redis is None:  # pragma: no cover - optional dependency
            raise RuntimeError("redis package is not installed")
        self._client = redis.Redis.from_url(url, decode_responses=True)

    def save(self, data: dict[str, Any], ttl: int, session_id: str | None = None) -> str:
        sid = session_id or str(uuid.uuid4())
        payload = json.dumps(data)
        # setex overwrites existing keys and sets TTL atomically
        self._client.setex(sid, ttl, payload)
        return sid

    def load(self, session_id: str) -> dict[str, Any] | None:
        payload = self._client.get(session_id)
        if payload is None:
            return None
        return json.loads(payload)

    def delete(self, session_id: str) -> None:
        self._client.delete(session_id)


class SessionStore:
    """Facade that chooses an appropriate backend."""

    def __init__(self, default_ttl: int = DEFAULT_SESSION_TTL_SECONDS) -> None:
        self.default_ttl = default_ttl
        backend: Any | None = None
        redis_url = os.getenv("REDIS_URL") or os.getenv("INTERACTIVE_SESSION_REDIS_URL")
        if redis_url:
            try:
                backend = _RedisSessionBackend(redis_url)
            except Exception as exc:  # pragma: no cover - falls back to memory
                logger.warning(
                    f"redis backend not available ({exc}); falling back to in-memory store"
                )
                backend = None
        self._backend = backend or _InMemorySessionBackend()

    def save(
        self,
        data: dict[str, Any],
        *,
        ttl: int | None = None,
        session_id: str | None = None,
    ) -> str:
        ttl_to_use = ttl or self.default_ttl
        return self._backend.save(data, ttl_to_use, session_id=session_id)

    def load(self, session_id: str) -> dict[str, Any] | None:
        return self._backend.load(session_id)

    def delete(self, session_id: str) -> None:
        self._backend.delete(session_id)


# Singleton instance used by the interactive processing service
session_store = SessionStore()

"""Convenience alias for callers wanting access to the default TTL."""
default_session_ttl = session_store.default_ttl
