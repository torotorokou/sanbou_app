"""
Integration-like tests for finalize using state from /initial.

本番フローに近づけるため、/initial を叩いて session_id を取得し、
session_store から state を復元して finalize を実行する。

フロントエンドから返ってくる想定のペイロード形：
{
  "session_id": "bup-20251001024922-abacea",
  "selections": {
    "bup_6a52ef74e0": "エコライン（ウイング）・合積",
    "bup_341b74d0b3": "シェノンビ",
    "bup_628d4147af": "エコライン（ウイング）",
    "bup_87502c2a3a": "エコライン",
    "bup_c468456d27": "シェノンビ・合積"
  }
}
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


def _discover_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "requirements.txt").exists():
            return candidate
    raise RuntimeError("Unable to locate project root containing requirements.txt")


CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = _discover_repo_root(CURRENT_DIR)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ST_APP_BASE = REPO_ROOT / "app" / "st_app"
if not ST_APP_BASE.exists():  # pragma: no cover - misconfigured workspace guard
    raise RuntimeError(f"st_app directory not found: {ST_APP_BASE}")
os.environ.setdefault("BASE_ST_APP_DIR", str(ST_APP_BASE))

from app.api.services.report.session_store import session_store  # noqa: E402
from app.main import app  # noqa: E402
from app.st_app.logic.manage.block_unit_price_interactive_main import (  # noqa: E402
    BlockUnitPriceInteractive,
)


def _load_sample_shipment_bytes() -> tuple[str, bytes, str]:
    shuka = {1: "出荷一覧_20250630_180038.csv", 2: "出荷一覧_20250829_164653.csv"}

    sample_path = REPO_ROOT / "app" / "test" / shuka[2]
    content = sample_path.read_bytes()
    return ("shipment.csv", content, "text/csv")


def _initial_session_and_rows(client: TestClient) -> tuple[str, list[dict[str, Any]]]:
    files = {"shipment": _load_sample_shipment_bytes()}
    resp = client.post("/ledger_api/block_unit_price_interactive/initial", files=files)
    assert resp.status_code == 200, resp.text
    data: dict[str, Any] = resp.json()
    session_id = data["session_id"]
    rows = data.get("rows", [])
    assert isinstance(rows, list) and rows, "initial rows should not be empty"
    return session_id, rows


def _make_fixed_frontend_payload(session_id: str) -> dict[str, Any]:
    """
    前に提示したフロントエンドの戻り値そのままの selections を組み立てて返す。
    entry_id が実データに存在しない可能性はあるが、ここでは形を合わせることを目的とする。
    """
    return {
        "session_id": session_id,
        "selections": {
            "bup_6a52ef74e0": "エコライン（ウイング）・合積",
            "bup_341b74d0b3": "シェノンビ",
            "bup_628d4147af": "エコライン（ウイング）",
            "bup_87502c2a3a": "エコライン",
            "bup_c468456d27": "シェノンビ・合積",
        },
    }


def test_finalize_success_from_initial_state_with_fixed_frontend_selections():
    """
    initial から取得した session_id を使い、フロント想定形
    {session_id, selections} をそのまま finalize に渡す成功パス。
    """
    client = TestClient(app)
    session_id, _rows = _initial_session_and_rows(client)

    serialized = session_store.load(session_id)
    assert isinstance(serialized, dict)

    gen = BlockUnitPriceInteractive()
    state = gen.deserialize_state(serialized)

    # Debug: show df_transport_cost columns/head（任意）
    df_transport_cost = state.get("df_transport_cost")
    if df_transport_cost is not None:
        print("[DBG test] transport_cost columns:", list(df_transport_cost.columns))
        try:
            print(
                "[DBG test] transport_cost head:", df_transport_cost.head(3).to_dict()
            )
        except Exception:
            pass

    # フロントの想定形に合わせて selections を固定で用意
    frontend_payload = _make_fixed_frontend_payload(session_id)

    # マスターの表記ゆれに起因する不安定さを避けるため最小限のモックを当てる
    def _apply_vendor(df_after, df_transport):
        import pandas as _pd

        df_result = df_after.copy()
        if "運搬費" not in df_result.columns:
            df_result["運搬費"] = 0
        try:
            t = df_transport.copy()
            if "運搬費" in t.columns:
                t["運搬費"] = _pd.to_numeric(t["運搬費"], errors="coerce").fillna(0)
            lookup = {
                (str(r.get("業者CD")), str(r.get("運搬業者"))): float(
                    r.get("運搬費", 0) or 0
                )
                for _, r in t.iterrows()
            }

            def _calc(row):
                key = (str(row.get("業者CD")), str(row.get("運搬業者")))
                return lookup.get(key, 0.0)

            df_result["運搬費"] = df_result.apply(_calc, axis=1)
        except Exception:
            pass
        return df_result

    from unittest.mock import patch

    with (
        patch(
            "app.st_app.logic.manage.block_unit_price_interactive_main.apply_transport_fee_by_vendor",
            side_effect=_apply_vendor,
        ),
        patch(
            "app.st_app.logic.manage.block_unit_price_interactive_main.apply_weight_based_transport_fee",
            side_effect=lambda df_after, _df_transport: df_after,
        ),
    ):
        final_df, payload = gen.finalize_with_optional_selections(
            state,
            frontend_payload,
        )
        assert isinstance(payload, dict)
        # finalize の結果が返っていること（成功・失敗の厳密判定はここでは行わない）
        assert payload.get("step") == 2
        assert payload.get("session_id") == session_id
        assert final_df is not None


def test_state_passed_to_finalize_matches_saved_serialized_state(
    monkeypatch: pytest.MonkeyPatch,
):
    """/initial で保存されたシリアライズ state が /finalize 実行時に読み出されるものと一致することを検証。

    仕組み: session_store.load をラップして、読み出し結果が initial 直後に取得した serialized と等しいことを検査する。
    /finalize は apply→finalize の順に内部で2回 load される可能性があるため、すべての呼び出しで検査する。
    """
    client = TestClient(app)
    session_id, _rows = _initial_session_and_rows(client)

    # initial 直後の保存済み serialized を取得（これが「正」となる）
    serialized_expected = session_store.load(session_id)
    assert isinstance(serialized_expected, dict) and serialized_expected

    # フロント想定形の selections を使用
    frontend_payload = _make_fixed_frontend_payload(session_id)

    # spy: session_store.load をラップ
    calls: list[dict[str, Any]] = []
    orig_load = session_store.load

    def _spy_load(sid: str):
        loaded = orig_load(sid)
        calls.append({"sid": sid, "loaded": loaded})
        # シリアライズ dict の完全一致を期待
        assert loaded == serialized_expected
        return loaded

    monkeypatch.setattr(
        "app.api.services.report.session_store.session_store.load", _spy_load
    )

    # /finalize エンドポイントを叩く（StreamingResponse だが 200 のみ確認）
    resp = client.post(
        "/ledger_api/block_unit_price_interactive/finalize",
        json=frontend_payload,  # ← フロント想定の {session_id, selections}
    )
    assert resp.status_code == 200
    # apply→finalizeで 1回以上 load が呼ばれていること
    assert len(calls) >= 1
