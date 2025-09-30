"""
ブロック単価計算インタラクティブAPIエンドポイント

ブロック単価計算処理を3つのステップに分けて実行するAPIエンドポイントです。
ユーザーの入力を段階的に受け取りながら、最終的な計算結果を返します。
"""

# backend/app/api/endpoints/block_unit_price_interactive.py

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
# StreamingResponse not required here; finalize may return JSON or StreamingResponse dynamically
from pydantic import BaseModel

from app.api.services.report.interactive_report_processing_service import (
    InteractiveReportProcessingService,
)
from app.api.dto.block_unit_price import (
    TransportCandidateResponseDTO,
    TransportCandidateRowDTO,
)
from app.st_app.logic.manage.block_unit_price_interactive_main import (
    BlockUnitPriceInteractive,
)

# APIルーターの初期化
router = APIRouter()
tag_name = "Block Unit Price"


class StartProcessRequest(BaseModel):  # レガシー JSON 経由 (互換用)
    files: Dict[str, Any]


class TransportSelectionRequest(BaseModel):
    """
    運搬業者選択リクエストモデル

    Attributes:
        session_id (str): 前のステップのセッションID
        selections (Dict[str, str]): 業者名と選択された運搬業者コードのマッピング
    """

    session_id: str
    selections: Dict[str, str]  # {業者名: 選択された運搬業者コード}


class FinalizeRequest(BaseModel):
    """最終確認リクエストモデル"""

    session_id: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None
    confirmed: bool = True


class GenericApplyRequest(BaseModel):
    """任意ステップ適用リクエスト"""

    session_id: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None
    user_input: Dict[str, Any]


@router.post("/initial", tags=[tag_name])
async def start_block_unit_price_process(
    request: StartProcessRequest | None = None,
    # 推奨: multipart/form-data で UploadFile を受け取る
    receive: UploadFile | None = File(None),
    yard: UploadFile | None = File(None),
    shipment: UploadFile | None = File(None),
):
    """
    ブロック単価計算処理開始 (Step 0)

    初期処理を実行し、運搬業者選択肢を返します。

    Args:
        request (StartProcessRequest): ファイルデータを含むリクエスト

    Returns:
        Dict: 処理結果と運搬業者選択肢

    Raises:
        HTTPException: 処理中にエラーが発生した場合
    """

    try:
        # 1) UploadFile 優先 (新方式)
        upload_files: Dict[str, UploadFile] = {}
        for key, f in {"shipment": shipment}.items():
            if f is not None:
                upload_files[key] = f

        # 2) 後方互換: JSON 経由 (Base64 等) は既存ロジックで使う: files=dict
        if not upload_files and request is not None:
            # 既存 BlockUnitPriceInteractive は DataFrame 受領想定なので

            generator = BlockUnitPriceInteractive(files=request.files)
            # interactive service initial は通常 UploadFile を想定するため、
            # ここでは直接 initial_step を呼べるよう format 済み dict を前提とするケースを簡易対応
            # → 実運用ではアップロード方式へ移行推奨
            return {"status": "deprecated", "message": "Use multipart upload instead."}

        service = InteractiveReportProcessingService()
        generator = BlockUnitPriceInteractive(files={})
        raw_result = service.initial(generator, upload_files)

        if not isinstance(raw_result, dict):
            return raw_result

        if raw_result.get("status") != "success":
            print("[DEBUG] initial result (error):", raw_result)
            return raw_result

        data_payload = raw_result.get("data")
        rows_payload: List[TransportCandidateRowDTO] = []
        if isinstance(data_payload, dict):
            rows_source = data_payload.get("rows", [])
            if isinstance(rows_source, list):
                for item in rows_source:
                    if isinstance(item, TransportCandidateRowDTO):
                        rows_payload.append(item)
                    elif isinstance(item, dict):
                        try:
                            rows_payload.append(TransportCandidateRowDTO(**item))
                        except Exception as dto_err:  # noqa: BLE001
                            print("[WARN] failed to parse transport row DTO:", dto_err, item)

        session_id_value = raw_result.get("session_id")
        if session_id_value is None and isinstance(data_payload, dict):
            session_id_value = data_payload.get("session_id")
        if session_id_value is None:
            raise HTTPException(status_code=500, detail="session_id を取得できませんでした")

        response_dto = TransportCandidateResponseDTO(
            session_id=str(session_id_value),
            rows=rows_payload,
        )

        return response_dto.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"処理開始エラー: {str(e)}")




@router.post("/finalize", tags=[tag_name])
async def finalize_calculation(request: FinalizeRequest) -> Any:
    """
    最終計算処理 (Step 2)

    最終的なブロック単価計算を実行し、結果を返します。

    Args:
        request (FinalizeRequest): セッションデータと確認フラグを含むリクエスト

    Returns:
        Dict: 最終的な計算結果

    Raises:
        HTTPException: 処理中にエラーが発生した場合
    """
    try:
        if not request.confirmed:
            raise HTTPException(
                status_code=400, detail="未確認のため finalize できません"
            )
        service = InteractiveReportProcessingService()
        generator = BlockUnitPriceInteractive()
        session_payload: Any = request.session_id or request.session_data
        if session_payload is None:
            raise HTTPException(status_code=400, detail="session_id が指定されていません")
        response = service.finalize(generator, session_payload)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"最終計算エラー: {str(e)}")


@router.get("/status/{step}", tags=[tag_name])
async def get_step_info(step: int):
    """
    各ステップの説明情報を取得

    指定されたステップ番号に対応する処理の説明情報を返します。

    Args:
        step (int): ステップ番号 (0, 1, 2)

    Returns:
        Dict: ステップの詳細情報

    Raises:
        HTTPException: 無効なステップ番号が指定された場合
    """
    # 各ステップの情報定義
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

    # ステップ番号の有効性チェック
    if step not in step_info:
        raise HTTPException(status_code=404, detail="無効なステップです")

    return step_info[step]


@router.post("/apply", tags=[tag_name])
async def apply_generic_step(request: GenericApplyRequest):
    """汎用ステップ適用エンドポイント

    user_input.action もしくは user_input.step に対応するハンドラを呼び出し、
    任意回数の対話ステップをサポートする。
    """
    try:
        service = InteractiveReportProcessingService()
        generator = BlockUnitPriceInteractive()
        session_payload: Any = request.session_id or request.session_data
        if session_payload is None:
            raise HTTPException(status_code=400, detail="session_id が指定されていません")
        result = service.apply(generator, session_payload, request.user_input)
        return result
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"汎用ステップ適用エラー: {e}")
