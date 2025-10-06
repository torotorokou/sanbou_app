"""Internal HTTP client for calling rag_api, ledger_api, manual_api."""
from __future__ import annotations

import os
from typing import Any
import httpx

# Environment variables for internal API base URLs
RAG_API_BASE = os.getenv("RAG_API_BASE", "http://rag_api:8000")
LEDGER_API_BASE = os.getenv("LEDGER_API_BASE", "http://ledger_api:8000")
MANUAL_API_BASE = os.getenv("MANUAL_API_BASE", "http://manual_api:8000")

# Timeout for internal sync calls (short)
INTERNAL_TIMEOUT = 1.0


def get_http_client() -> httpx.Client:
    """
    Returns a synchronous httpx client for internal API calls.
    Use timeout=1.0s, no retries for fast-fail.
    """
    return httpx.Client(timeout=INTERNAL_TIMEOUT, follow_redirects=True)


async def get_async_http_client() -> httpx.AsyncClient:
    """
    Returns an async httpx client for internal API calls.
    Use timeout=1.0s, no retries for fast-fail.
    """
    return httpx.AsyncClient(timeout=INTERNAL_TIMEOUT, follow_redirects=True)
