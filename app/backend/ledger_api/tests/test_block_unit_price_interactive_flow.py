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
    assert body.get("status") == "success"
    session_data = body.get("session_data")
    assert session_data

    # apply (skip if no options)
    transport_options = body.get("data", {}).get("transport_options", [])
    selections = {}
    for opt in transport_options[:1]:
        vendor_name = opt.get("vendor_name") or opt.get("vendor_code")
        if vendor_name:
            selections[vendor_name] = opt.get("vendor_code", "")
    res2 = client.post(
        "/block_unit_price_interactive/apply",
        json={
            "session_data": session_data,
            "user_input": {"action": "select_transport", "selections": selections},
        },
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2.get("status") == "success"
    session_data2 = body2.get("session_data") or session_data

    # finalize
    res3 = client.post(
        "/block_unit_price_interactive/finalize",
        json={"session_data": session_data2, "confirmed": True},
    )
    assert res3.status_code == 200
    # content-type should be zip
    assert "application/zip" in res3.headers.get("content-type", "")
