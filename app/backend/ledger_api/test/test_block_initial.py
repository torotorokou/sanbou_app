"""Integration tests for /ledger_api/block_unit_price_interactive/initial.

本番と同じ構成で、出荷一覧のみをmultipartでバックエンドに渡し、
エラーなく所定のフィールドが返ることを確認する。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient


def _discover_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "requirements.txt").exists():
            return candidate
    raise RuntimeError("Unable to locate project root containing requirements.txt")


# --- Test app setup (env before import) ---
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = _discover_repo_root(CURRENT_DIR)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# BASE_ST_APP_DIR は MainPath の基準。実データ配置に合わせて設定。
ST_APP_BASE = REPO_ROOT / "app" / "st_app"
os.environ.setdefault("BASE_ST_APP_DIR", str(ST_APP_BASE))

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def _load_sample_shipment_bytes() -> tuple[str, bytes, str]:
    """テスト用の出荷一覧CSV（実データ）を読み出す。

    Returns:
        (filename, content, mime)
    """
    sample_path = REPO_ROOT / "app" / "test" / "出荷一覧_20250829_164653.csv"
    # バイナリ読み込み（BOM含む想定）
    content = sample_path.read_bytes()
    return ("shipment.csv", content, "text/csv")


def test_initial_endpoint_accepts_shipment_only_and_returns_rows(
    client: TestClient,
) -> None:
    # Arrange: multipart files payload（shipment のみ）
    file_tuple = _load_sample_shipment_bytes()
    files = {"shipment": file_tuple}

    # Act
    resp = client.post("/ledger_api/block_unit_price_interactive/initial", files=files)

    # Assert: HTTP 200 and essential fields
    assert resp.status_code == 200, resp.text
    data: Dict[str, Any] = resp.json()

    assert isinstance(data.get("session_id"), str) and data["session_id"], data
    assert isinstance(data.get("rows"), list) and len(data["rows"]) > 0, data

    # 丸源(業者CD=8327) の行が含まれており、候補に少なくとも『オネスト』が存在
    target_rows = [r for r in data["rows"] if r.get("vendor_code") in (8327, "8327")]
    assert (
        target_rows
    ), f"vendor_code=8327 の行が見つかりません: rows={data['rows'][:3]}..."

    row0 = target_rows[0]
    assert isinstance(row0.get("options"), list) and len(row0["options"]) >= 1
    assert any("オネスト" in str(opt) for opt in row0["options"])  # 運搬候補の一部確認

    # initial_index は options の範囲内
    ii = row0.get("initial_index")
    assert isinstance(ii, int) and 0 <= ii < len(
        row0["options"]
    )  # 候補数に応じた初期選択


def test_initial_endpoint_without_file_returns_422(client: TestClient) -> None:
    # Act
    resp = client.post("/ledger_api/block_unit_price_interactive/initial")

    # Assert: バリデーション/読込失敗をHTTP 422へ変換
    assert resp.status_code == 422
    body = resp.json()
    # 汎用エラーで良いが、構造は保持される
    assert "detail" in body
