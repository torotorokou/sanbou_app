"""
IAP (Identity-Aware Proxy) デバッグエンドポイント

GCP IAP 経由でリクエストが FastAPI まで到達しているか、
IAP のヘッダが正しく転送されているかを確認するためのデバッグエンドポイント。

想定用途:
  - STG/PROD 環境で IAP 認証が機能しているか確認
  - Nginx から FastAPI までヘッダが正しく伝わっているか確認
  - IAP が付与する 3 つのヘッダの値を検証

注意:
  - このエンドポイントは開発/検証用途であり、本番環境では無効化または
    アクセス制限を設けることを推奨します。
  - JWT の検証は行っていません（ヘッダの受信確認のみ）。
"""

from typing import Any, Dict

from fastapi import APIRouter, Request

router = APIRouter(
    prefix="/debug",
    tags=["debug"],
)


@router.get("/iap-headers", summary="IAP ヘッダ確認用デバッグエンドポイント")
async def debug_iap_headers(request: Request) -> Dict[str, Any]:
    """
    IAP (Identity-Aware Proxy) が付与するヘッダをそのまま返すデバッグエンドポイント。

    Returns:
        Dict[str, Any]: IAP 関連ヘッダと全ヘッダ情報

    IAP が付与する主要ヘッダ:
      - X-Goog-Authenticated-User-Email: ログインユーザーのメールアドレス
        形式: "accounts.google.com:user@example.com"
      - X-Goog-Authenticated-User-Id: ログインユーザーの内部 ID
        形式: "accounts.google.com:123456789012345678901"
      - X-Goog-IAP-JWT-Assertion: IAP が発行した JWT トークン（署名付き）

    使い方:
      1. STG/PROD 環境で IAP 経由でログイン
      2. ブラウザから https://<your-domain>/core_api/debug/iap-headers にアクセス
      3. 返された JSON で各ヘッダの値を確認
    """
    headers = request.headers

    return {
        "x_goog_authenticated_user_email": headers.get(
            "x-goog-authenticated-user-email"
        ),
        "x_goog_authenticated_user_id": headers.get("x-goog-authenticated-user-id"),
        "x_goog_iap_jwt_assertion_exists": "x-goog-iap-jwt-assertion" in headers,
        "x_goog_iap_jwt_assertion_preview": (
            headers.get("x-goog-iap-jwt-assertion", "")[:50] + "..."
            if "x-goog-iap-jwt-assertion" in headers
            else None
        ),
        # デバッグ用: すべてのヘッダを返す（機密情報に注意）
        "all_headers": dict(headers),
    }
