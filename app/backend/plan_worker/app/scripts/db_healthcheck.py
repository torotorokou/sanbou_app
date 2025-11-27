"""Database health check CLI script for Docker HEALTHCHECK."""
import json
import sys

from app.infrastructure.db.health import ping_db


def main() -> int:
    """
    Check database connectivity and print JSON status.

    Returns:
        0 if database is healthy, 1 otherwise
    """
    h = ping_db(timeout_sec=2)
    payload = {
        "status": "ok" if h.ok else "ng",
        "db": "ok" if h.ok else "ng",
        "db_latency_ms": h.latency_ms,
        "db_version": h.version,
        "error": h.error,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if h.ok else 1


if __name__ == "__main__":
    sys.exit(main())
