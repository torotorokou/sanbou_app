"""最小インタラクティブE2Eテスト (pytest想定)

pytest 実行例:
  PYTHONPATH=backend:backend/backend_shared/src pytest -q backend/tests/test_block_unit_price_interactive_flow.py

注意: サーバ別起動が不要なように FastAPI TestClient を使用。
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_interactive_flow_minimal():
    # サンプルCSV（必要カラムを満たす）
    shipment_path = Path("tests/data/sample_shipment_block_unit_price.csv")
    assert shipment_path.exists()

    # initial
    with shipment_path.open("rb") as f:
        res = client.post(
            "/block_unit_price_interactive/initial",
            files={"shipment": (shipment_path.name, f, "text/csv")},
        )
    assert res.status_code == 200
    body = res.json()
    session_id = body.get("session_id")
    assert isinstance(session_id, str) and session_id

    rows = body.get("rows", [])
    selections_payload = {}
    for row in rows[:1]:
        entry_id = row.get("entry_id")
        if isinstance(entry_id, str):
            selections_payload[entry_id] = 0

    if selections_payload:
        res2 = client.post(
            "/block_unit_price_interactive/apply",
            json={
                "session_id": session_id,
                "selections": selections_payload,
            },
        )
        assert res2.status_code == 200
        body2 = res2.json()
        assert body2.get("session_id") == session_id

    res3 = client.post(
        "/block_unit_price_interactive/finalize",
        json={"session_id": session_id},
    )
    assert res3.status_code == 200
    # content-type should be zip
    assert "application/zip" in res3.headers.get("content-type", "")
