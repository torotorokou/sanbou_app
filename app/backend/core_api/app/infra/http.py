"""
内部API呼び出し用HTTPクライアント

Core APIが他のマイクロサービス(rag_api, ledger_api, manual_api)を
呼び出す際に使用するHTTPクライアントを提供。

特徴:
  - 短いタイムアウト(1.0s): 高速な失敗検出
  - リトライなし: シンプルなエラーハンドリング
  - リダイレクト自動追従: HTTP 30x対応

タイムアウト設定:
  - 内部API呼び出しは速度を優先
  - タイムアウト時は即座にエラーを返す
  - リトライは上位層(UseCase)で実装

使用例:
    # 同期呼び出し
    client = get_http_client()
    response = client.get(f"{RAG_API_BASE}/health")

    # 非同期呼び出し
    async with get_async_http_client() as client:
        response = await client.get(f"{RAG_API_BASE}/health")

注意:
  - 内部ネットワーク専用(外部API呼び出しには使用しない)
  - SSL証明書検証は無効(内部ネットワークのため)
"""

from __future__ import annotations

import os

import httpx

# ==========================================
# 環境変数から内部APIベーURLを取得
# ==========================================
# Docker Compose環境ではサービス名で解決される
# 例: rag_api:8000 → http://rag_api:8000
RAG_API_BASE = os.getenv("RAG_API_BASE", "http://rag_api:8000")
LEDGER_API_BASE = os.getenv("LEDGER_API_BASE", "http://ledger_api:8000")
MANUAL_API_BASE = os.getenv("MANUAL_API_BASE", "http://manual_api:8000")

# ==========================================
# タイムアウト設定
# ==========================================
# 内部API呼び出しは短いタイムアウトで高速に失敗させる
# 長時間実行タスクはジョブキューを使用する
INTERNAL_TIMEOUT = 1.0  # 1秒


def get_http_client() -> httpx.Client:
    """
    同期内部API呼び出し用HTTPクライアントを取得

    特徴:
      - タイムアウト: 1.0秒(短く設定し、高速に失敗させる)
      - リトライなし(シンプルなエラーハンドリング)
      - リダイレクト自動追従

    Returns:
        httpx.Client: 同期 HTTPクライアント

    使用例:
        client = get_http_client()
        response = client.get("http://rag_api:8000/health")
        data = response.json()

    注意:
        - withブロックで使用することを推奨(リソースの自動クリーンアップ)
    """
    return httpx.Client(timeout=INTERNAL_TIMEOUT, follow_redirects=True)


async def get_async_http_client() -> httpx.AsyncClient:
    """
    非同期内部API呼び出し用HTTPクライアントを取得

    特徴:
      - タイムアウト: 1.0秒
      - リトライなし
      - リダイレクト自動追従
      - asyncioとの統合(非同期処理向け)

    Returns:
        httpx.AsyncClient: 非同期 HTTPクライアント

    使用例:
        async with get_async_http_client() as client:
            response = await client.get("http://rag_api:8000/health")
            data = response.json()

    注意:
        - 必ず async with ブロックで使用(リソースリーク防止)
        - FastAPIの非同期エンドポイント内で使用
    """
    return httpx.AsyncClient(timeout=INTERNAL_TIMEOUT, follow_redirects=True)
