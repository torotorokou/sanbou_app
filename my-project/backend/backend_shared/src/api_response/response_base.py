"""
API基底レスポンス（互換レイヤー対応）

目的:
- 既存の SuccessApiResponse / ErrorApiResponse の呼び出し互換を維持
- 中身は Pydantic モデルに委譲し、/docs で正しいスキーマを公開
- 新規エンドポイントは response_model=ApiResponse[...] を利用可能に
"""

from typing import Any, Optional, Generic, TypeVar, Literal
from fastapi.responses import JSONResponse


# --- Pydantic v1/v2 互換インポート -------------------------------------------
try:
    from pydantic.generics import GenericModel  # Pydantic v1
    from pydantic import BaseModel

    _IS_PYDANTIC_V2 = False
except ImportError:
    # Pydantic v2
    from pydantic import BaseModel

    GenericModel = BaseModel  # v2では GenericModel を使わずとも動く簡易対応
    _IS_PYDANTIC_V2 = True


# --- 共通レスポンス契約（/docs に出す唯一のスキーマ） -------------------------
T = TypeVar("T")


class ApiResponse(GenericModel, Generic[T]):
    """
    FastAPI に公開する共通レスポンスモデル（契約）。
    - /docs へ自動反映
    - response_model=ApiResponse[YourResultModel] として使用
    """

    status: Literal["success", "error"]
    code: str
    detail: str
    result: Optional[T] = None
    hint: Optional[str] = None

    @classmethod
    def success(
        cls,
        *,
        code: str,
        detail: str,
        result: Optional[T] = None,
        hint: Optional[str] = None,
    ) -> "ApiResponse[T]":
        return cls(status="success", code=code, detail=detail, result=result, hint=hint)

    @classmethod
    def error(
        cls,
        *,
        code: str,
        detail: str,
        result: Optional[Any] = None,
        hint: Optional[str] = None,
    ) -> "ApiResponse[Any]":
        return cls(status="error", code=code, detail=detail, result=result, hint=hint)


# --- Pydanticモデル -> dict の互換ヘルパ --------------------------------------
def _model_to_dict(model: BaseModel) -> dict:
    """
    Pydantic v1/v2 の差異を吸収して dict へ変換。
    """
    if _IS_PYDANTIC_V2:
        return model.model_dump()
    return model.dict()


# --- 互換レイヤー: 既存クラス（内部で ApiResponse に委譲） -------------------
class BaseApiResponse:
    """
    【互換用】既存の使用箇所を壊さずに維持するための薄いラッパ。
    実体は ApiResponse に委譲し、to_json_response() もそのまま使える。
    直接のインスタンス化は非推奨（success/error のサブクラスを使用）。
    """

    # 各サブクラスで "success" or "error" を必ず上書き
    status: Literal["success", "error"]

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
        互換コンストラクタ
        - 旧コードの引数はそのまま受ける
        - 内部で ApiResponse に委譲
        """
        # サブクラスで status がセットされている前提
        if self.status not in ("success", "error"):
            raise ValueError(
                "BaseApiResponse.status は 'success' か 'error' を指定してください。"
            )

        if self.status == "success":
            self.payload = ApiResponse.success(
                code=code, detail=detail, result=result, hint=hint
            )
        else:
            self.payload = ApiResponse.error(
                code=code, detail=detail, result=result, hint=hint
            )

        self.status_code = status_code

    def to_json_response(self) -> JSONResponse:
        """
        旧コード互換: JSONResponse を返す。
        ※ 新規コードでは JSONResponse を直接返さず、
           FastAPI にモデル/辞書を返すことを推奨。
        """
        content = _model_to_dict(self.payload)
        return JSONResponse(status_code=self.status_code, content=content)


class SuccessApiResponse(BaseApiResponse):
    """
    【互換用】成功レスポンスクラス
    旧来の呼び出しを維持しつつ、内部は ApiResponse に委譲する。
    """

    status: Literal["success", "error"] = "success"

    def __init__(
        self,
        *,
        code: str,
        detail: str,
        result: Optional[Any] = None,
        hint: Optional[str] = None,
        status_code: int = 200,
    ):
        super().__init__(
            code=code,
            detail=detail,
            result=result,
            hint=hint,
            status_code=status_code,
        )


class ErrorApiResponse(BaseApiResponse):
    """
    【互換用】エラーレスポンスクラス
    旧来の呼び出しを維持しつつ、内部は ApiResponse に委譲する。
    """

    status: Literal["success", "error"] = "error"

    def __init__(
        self,
        *,
        code: str,
        detail: str,
        result: Optional[Any] = None,
        hint: Optional[str] = None,
        status_code: int = 422,
    ):
        super().__init__(
            code=code,
            detail=detail,
            result=result,
            hint=hint,
            status_code=status_code,
        )


# --- 旧名: ApiResponseModel を残したい場合のエイリアス（任意） ---------------
# 旧コードに ApiResponseModel が出てくる場合の下位互換。
# 新規コードでは ApiResponse[...] を直接使うことを推奨。
ApiResponseModel = ApiResponse  # 下位互換用の別名
