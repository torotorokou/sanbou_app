from __future__ import annotations

import os
from functools import lru_cache

DEFAULT_ASSET_ROUTE = "/manual_api/api/assets"


def _join_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


@lru_cache(maxsize=1)
def _get_asset_base_url() -> str:
    env_value = os.getenv("MANUAL_ASSET_BASE_URL")
    if env_value and env_value.strip():
        return env_value.strip()
    route = os.getenv("MANUAL_ASSET_ROUTE", DEFAULT_ASSET_ROUTE)
    return route.strip()


def build_manual_asset_url(relative_path: str) -> str:
    """Resolve a manual asset URL.

    - If ``relative_path`` is already an absolute URL (http/https), it is returned as-is.
    - Otherwise, it is resolved against ``MANUAL_ASSET_BASE_URL`` when provided.
    - If the environment variable is not set, ``/manual_api/api/assets`` is used, which
      is served directly by the manual API. This makes it easy to swap in a signed GCS
      URL provider in the future without touching the catalog dataset.
    """
    if not relative_path:
        raise ValueError("relative_path is required")

    if relative_path.startswith(("http://", "https://")):
        return relative_path

    base = _get_asset_base_url()
    return _join_url(base, relative_path)
