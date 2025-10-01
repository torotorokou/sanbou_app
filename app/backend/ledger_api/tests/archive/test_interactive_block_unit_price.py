from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8001/ledger_api")
API_BASE = f"{BASE_URL}/block_unit_price_interactive"

SAMPLE_CSV = Path("/backend/app/data/csv/出荷一覧_20240501.csv")


def log(title, obj):
    print(f"\n==== {title} ====")
    if isinstance(obj, (dict, list)):
        print(json.dumps(obj, ensure_ascii=False, indent=2)[:6000])
    else:
        print(str(obj)[:6000])


def call_initial():
    if not SAMPLE_CSV.exists():
        print("Sample CSV missing:", SAMPLE_CSV, file=sys.stderr)
        sys.exit(1)
    with SAMPLE_CSV.open("rb") as f:
        r = requests.post(
            f"{API_BASE}/initial",
            files={"shipment": (SAMPLE_CSV.name, f, "text/csv")},
            timeout=30,
        )
    return r


def call_apply(session_id, selections):
    payload = {
        "session_id": session_id,
        "selections": selections,
    }
    r = requests.post(f"{API_BASE}/apply", json=payload, timeout=30)
    return r


def call_finalize(session_id):
    payload = {"session_id": session_id}
    r = requests.post(f"{API_BASE}/finalize", json=payload, timeout=60)
    if r.status_code == 200 and r.headers.get("content-type", "").startswith(
        "application/zip"
    ):
        out = Path("interactive_result.zip")
        out.write_bytes(r.content)
        print(f"ZIP saved -> {out} ({out.stat().st_size} bytes)")
    return r


def main():
    print("Using BASE_URL=", BASE_URL)
    r0 = call_initial()
    log("INITIAL RAW", r0.text)
    try:
        j0 = r0.json()
    except Exception:
        print("Invalid JSON; abort")
        return
    log("INITIAL JSON", j0)
    session_id = j0.get("session_id")
    if not session_id:
        print("session_id missing; stop.")
        return
    rows = j0.get("rows", [])
    selections = {}
    for row in rows[:2]:
        entry_id = row.get("entry_id")
        if isinstance(entry_id, str):
            selections[entry_id] = 0

    if selections:
        r1 = call_apply(session_id, selections)
        log("APPLY RAW", r1.text)
        try:
            j1 = r1.json()
        except Exception:
            j1 = {}
        log("APPLY JSON", j1)

    r2 = call_finalize(session_id)
    print("FINAL status", r2.status_code)
    if r2.headers.get("content-type", "").startswith("application/zip"):
        print("Finalize returned ZIP.")
    else:
        print("Finalize body:", r2.text[:1000])


if __name__ == "__main__":
    main()
