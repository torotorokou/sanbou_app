# backend/app/api/endpoints/block_unit_price_interactive.py
"""
ブロック単価計算インタラクティブAPIエンドポイント

ブロック単価計算処理を3つのステップに分けて実行するAPIエンドポイントです。
ユーザーの入力を段階的に受け取りながら、最終的な計算結果を返します。
"""

from typing import Any, Dict, Optional, Union

# 移行済みの実装ファイルからインポート
from app.core.usecases.reports.interactive import BlockUnitPriceInteractive
from app.core.usecases.reports.processors.interactive_report_processing_service import (
    InteractiveReportProcessingService,
)
from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.infra.adapters.fastapi.error_handlers import DomainError
from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from pydantic import BaseModel

router = APIRouter()
tag_name = "Block Unit Price"
logger = get_module_logger(__name__)


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
            code=code, status=422, user_message=detail, title="処理エラー"
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
    logger.info(
        "ブロック単価初期処理開始",
        extra=create_log_context(
            operation="block_unit_price_initial",
            has_request=request is not None,
            has_shipment=shipment is not None,
        ),
    )

    # 1) UploadFile 優先 (新方式)
    upload_files: Dict[str, UploadFile] = {}
    if shipment is not None:
        upload_files["shipment"] = shipment

    # 2) 後方互換: JSON 経由 (Base64 等)
    if not upload_files and request is not None:
        logger.warning(
            "非推奨: JSON経由のファイルアップロード",
            extra=create_log_context(operation="block_unit_price_initial"),
        )
        _ = BlockUnitPriceInteractive(files=request.files)
        return {"status": "deprecated", "message": "Use multipart upload instead."}

    try:
        service = InteractiveReportProcessingService()
        generator = BlockUnitPriceInteractive(files=upload_files)
        raw_result = service.initial(generator, upload_files)

        _raise_if_error_payload(raw_result)

        logger.info(
            "ブロック単価初期処理完了",
            extra=create_log_context(
                operation="block_unit_price_initial",
                session_id=raw_result.get("session_id"),
                rows_count=len(raw_result.get("rows", [])),
            ),
        )

        return raw_result
    except DomainError:
        raise
    except Exception as e:
        logger.exception(
            "ブロック単価初期処理失敗",
            extra=create_log_context(
                operation="block_unit_price_initial",
                error_type=type(e).__name__,
                error=str(e),
            ),
        )
        raise DomainError(
            code="INITIAL_FAILED",
            status=500,
            user_message=f"初期処理中にエラーが発生しました: {str(e)}",
            title="処理エラー",
        ) from e


@router.post("/apply", tags=[tag_name])
async def apply_transport_selection(request: TransportSelectionRequest):
    """
    運搬業者選択適用エンドポイント（2段階方式を使う場合）
    """
    logger.info(
        "運搬業者選択適用開始",
        extra=create_log_context(
            operation="block_unit_price_apply",
            session_id=request.session_id,
            selections_count=len(request.selections) if request.selections else 0,
        ),
    )

    if not request.session_id:
        raise DomainError(
            code="INPUT_INVALID",
            status=400,
            user_message="session_id が指定されていません",
            title="入力エラー",
        )

    try:
        service = InteractiveReportProcessingService()
        generator = BlockUnitPriceInteractive()

        user_input = {
            "action": "select_transport",
            "session_id": request.session_id,
            "selections": request.selections,
        }
        result = service.apply(generator, request.session_id, user_input)

        _raise_if_error_payload(result)

        logger.info(
            "運搬業者選択適用完了",
            extra=create_log_context(
                operation="block_unit_price_apply", session_id=request.session_id
            ),
        )

        return result
    except DomainError:
        raise
    except Exception as e:
        logger.exception(
            "運搬業者選択適用失敗",
            extra=create_log_context(
                operation="block_unit_price_apply",
                session_id=request.session_id,
                error_type=type(e).__name__,
                error=str(e),
            ),
        )
        raise DomainError(
            code="APPLY_FAILED",
            status=500,
            user_message=f"選択適用中にエラーが発生しました: {str(e)}",
            title="処理エラー",
        ) from e


@router.post("/finalize", tags=[tag_name])
async def finalize_calculation(
    request: FinalizeRequest, background_tasks: BackgroundTasks
) -> Any:
    """
    最終計算処理 (Step 2)
    - 一本化運用：{session_id, selections} を同送 → 選択適用→最終計算を一括実行
    - 互換運用   ：selections 無し → 既存の選択状態で最終計算のみ実行

    🔄 PDF非同期生成: BackgroundTasksでPDFをバックグラウンド生成
    """
    logger.info(
        "ブロック単価最終計算開始",
        extra=create_log_context(
            operation="block_unit_price_finalize",
            session_id=request.session_id,
            has_selections=bool(request.selections),
        ),
    )

    if not request.session_id:
        raise DomainError(
            code="INPUT_INVALID",
            status=400,
            user_message="session_id が指定されていません",
            title="入力エラー",
        )

    try:
        service = InteractiveReportProcessingService()
        generator = BlockUnitPriceInteractive()

        user_input = {
            "session_id": request.session_id,
            "selections": request.selections or {},
        }

        # selections があれば finalize 内で適用し、そのまま共通の ZIP レスポンスを返す
        response = service.finalize(
            generator,
            request.session_id,
            user_input,
            background_tasks=background_tasks,  # 🔄 BackgroundTasksを渡す
        )

        logger.info(
            "ブロック単価最終計算完了",
            extra=create_log_context(
                operation="block_unit_price_finalize", session_id=request.session_id
            ),
        )

        return response
    except DomainError:
        raise
    except Exception as e:
        logger.exception(
            "ブロック単価最終計算失敗",
            extra=create_log_context(
                operation="block_unit_price_finalize",
                session_id=request.session_id,
                error_type=type(e).__name__,
                error=str(e),
            ),
        )
        raise DomainError(
            code="FINALIZE_FAILED",
            status=500,
            user_message=f"最終計算中にエラーが発生しました: {str(e)}",
            title="処理エラー",
        ) from e


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
            title="入力エラー",
        )
    return step_info[step]
