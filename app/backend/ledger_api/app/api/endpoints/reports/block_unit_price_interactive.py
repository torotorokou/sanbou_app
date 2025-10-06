# backend/app/api/endpoints/block_unit_price_interactive.py
"""
ブロック単価計算インタラクティブAPIエンドポイント

ブロック単価計算処理を3つのステップに分けて実行するAPIエンドポイントです。
ユーザーの入力を段階的に受け取りながら、最終的な計算結果を返します。
"""

from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from backend_shared.api.error_handlers import DomainError
from app.api.services.report.core.processors.interactive_report_processing_service import (
    InteractiveReportProcessingService,
)
# 移行済みの実装ファイルからインポート
from app.api.services.report.ledger.interactive import (
    BlockUnitPriceInteractive,
)

router = APIRouter()
tag_name = "Block Unit Price"


class StartProcessRequest(BaseModel):  # レガシー JSON 経由 (互換用)
    files: Dict[str, Any]


class TransportSelectionRequest(BaseModel):
    session_id: str
    selections: Dict[str, Union[int, str]]


class FinalizeRequest(BaseModel):
    session_id: str
    # 一本化運用のため、任意で selections を同送可能
    selections: Optional[Dict[str, Union[int, str]]] = None


def _raise_if_error_payload(result: Any) -> None:
    """
    サービスから返ってきた結果が {status: "error"} なら DomainError を投げる。
    """
    if isinstance(result, dict) and result.get("status") == "error":
        code = result.get("code", "PROCESSING_ERROR")
        detail = result.get("detail") or result.get("message") or "処理に失敗しました"
        raise DomainError(
            code=code,
            status=422,
            user_message=detail,
            title="処理エラー"
        )


@router.post("/initial", tags=[tag_name])
async def start_block_unit_price_process(
    request: StartProcessRequest | None = None,
    # multipart/form-data で UploadFile を受け取る（出荷一覧のみ）
    shipment: UploadFile | None = File(None),
):
    """
    ブロック単価計算処理開始 (Step 0)
    初期処理を実行し、運搬業者選択肢を返します。
    """
    # 1) UploadFile 優先 (新方式)
    upload_files: Dict[str, UploadFile] = {}
    if shipment is not None:
        upload_files["shipment"] = shipment

    # 2) 後方互換: JSON 経由 (Base64 等)
    if not upload_files and request is not None:
        _ = BlockUnitPriceInteractive(files=request.files)
        return {"status": "deprecated", "message": "Use multipart upload instead."}

    service = InteractiveReportProcessingService()
    generator = BlockUnitPriceInteractive(files=upload_files)
    raw_result = service.initial(generator, upload_files)

    _raise_if_error_payload(raw_result)
    return raw_result


@router.post("/apply", tags=[tag_name])
async def apply_transport_selection(request: TransportSelectionRequest):
    """
    運搬業者選択適用エンドポイント（2段階方式を使う場合）
    """
    if not request.session_id:
        raise DomainError(
            code="INPUT_INVALID",
            status=400,
            user_message="session_id が指定されていません",
            title="入力エラー"
        )

    service = InteractiveReportProcessingService()
    generator = BlockUnitPriceInteractive()

    user_input = {
        "action": "select_transport",
        "session_id": request.session_id,
        "selections": request.selections,
    }
    result = service.apply(generator, request.session_id, user_input)

    _raise_if_error_payload(result)
    return result


@router.post("/finalize", tags=[tag_name])
async def finalize_calculation(request: FinalizeRequest) -> Any:
    """
    最終計算処理 (Step 2)
    - 一本化運用：{session_id, selections} を同送 → 選択適用→最終計算を一括実行
    - 互換運用   ：selections 無し → 既存の選択状態で最終計算のみ実行
    """
    if not request.session_id:
        raise DomainError(
            code="INPUT_INVALID",
            status=400,
            user_message="session_id が指定されていません",
            title="入力エラー"
        )

    service = InteractiveReportProcessingService()
    generator = BlockUnitPriceInteractive()

    user_input = {
        "session_id": request.session_id,
        "selections": request.selections or {},
    }

    # selections があれば finalize 内で適用し、そのまま共通の ZIP レスポンスを返す
    response = service.finalize(generator, request.session_id, user_input)  # type: ignore[arg-type]
    return response


@router.get("/status/{step}", tags=[tag_name])
async def get_step_info(step: int):
    """
    各ステップの説明情報を取得
    """
    step_info = {
        0: {
            "step": 0,
            "title": "初期処理",
            "description": "ファイルの読み込みと基本処理を実行します",
            "next_action": "運搬業者を選択してください",
        },
        1: {
            "step": 1,
            "title": "運搬業者選択",
            "description": "各業者に対して運搬業者を選択します",
            "next_action": "選択内容を確認してください",
        },
        2: {
            "step": 2,
            "title": "最終計算",
            "description": "選択内容に基づいて最終的な計算を実行します",
            "next_action": "処理完了",
        },
    }

    if step not in step_info:
        raise DomainError(
            code="INPUT_INVALID",
            status=404,
            user_message="無効なステップです",
            title="入力エラー"
        )
    return step_info[step]
