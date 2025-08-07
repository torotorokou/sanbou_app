"""
API基底レスポンスクラス

統一されたAPIレスポンス形式を提供する基底クラス群です。
成功・エラー両方のレスポンスに対して一貫した構造を提供します。
"""

from fastapi.responses import JSONResponse
from typing import Any, Optional


class BaseApiResponse:
    """
    API基底レスポンスクラス

    すべてのAPIレスポンスの基底となるクラスです。
    統一されたレスポンス形式を提供し、JSONResponseに変換する機能を持ちます。
    """

    status: str = "base"  # 各サブクラスで "success" or "error" に上書き

    def __init__(
        self,
        *,
        code: str,
        detail: str,
        result: Optional[Any] = None,
        hint: Optional[str] = None,
        status_code: int = 200,
    ):
        """
        基底レスポンスの初期化

        Args:
            code (str): レスポンスコード
            detail (str): 詳細メッセージ
            result (Any, optional): レスポンスデータ
            hint (str, optional): ヒントメッセージ
            status_code (int): HTTPステータスコード
        """
        self.code = code
        self.detail = detail
        self.result = result
        self.hint = hint
        self.status_code = status_code

    def to_json_response(self) -> JSONResponse:
        """
        JSONResponseオブジェクトに変換

        Returns:
            JSONResponse: FastAPI用のJSONレスポンス
        """
        # 基本的なレスポンス構造を構築
        content = {
            "status": self.status,
            "code": self.code,
            "detail": self.detail,
        }

        # 任意フィールドの追加
        if self.result is not None:
            content["result"] = self.result
        if self.hint is not None:
            content["hint"] = self.hint

        return JSONResponse(status_code=self.status_code, content=content)


class SuccessApiResponse(BaseApiResponse):
    """
    成功レスポンスクラス

    API処理が正常に完了した場合のレスポンスクラスです。
    """

    status = "success"  # 成功ステータス

    def __init__(
        self,
        *,
        code: str,
        detail: str,
        result: Optional[Any] = None,
        hint: Optional[str] = None,
        status_code: int = 200,
    ):
        """
        成功レスポンスの初期化

        Args:
            code (str): 成功コード
            detail (str): 成功メッセージ
            result (Any, optional): レスポンスデータ
            hint (str, optional): ヒントメッセージ
            status_code (int): HTTPステータスコード（デフォルト: 200）
        """
        super().__init__(
            code=code,
            detail=detail,
            result=result,
            hint=hint,
            status_code=status_code,
        )


class ErrorApiResponse(BaseApiResponse):
    """
    エラーレスポンスクラス

    API処理でエラーが発生した場合のレスポンスクラスです。
    """

    status = "error"  # エラーステータス

    def __init__(
        self,
        *,
        code: str,
        detail: str,
        result: Optional[Any] = None,
        hint: Optional[str] = None,
        status_code: int = 422,
    ):
        """
        エラーレスポンスの初期化

        Args:
            code (str): エラーコード
            detail (str): エラーメッセージ
            result (Any, optional): エラー詳細データ
            hint (str, optional): 解決のためのヒント
            status_code (int): HTTPステータスコード（デフォルト: 422）
        """
        super().__init__(
            code=code,
            detail=detail,
            result=result,
            hint=hint,
            status_code=status_code,
        )
