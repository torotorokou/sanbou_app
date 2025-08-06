# backend/app/api/endpoints/block_unit_price_interactive.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

from app.api.st_app.logic.manage.block_unit_price_interactive import (
    BlockUnitPriceInteractive,
)

router = APIRouter()


class StartProcessRequest(BaseModel):
    """処理開始リクエスト"""

    files: Dict[str, Any]  # アップロードされたファイルデータ


class TransportSelectionRequest(BaseModel):
    """運搬業者選択リクエスト"""

    session_data: Dict[str, Any]  # 前のステップのセッションデータ
    selections: Dict[str, str]  # {業者名: 選択された運搬業者コード}


class FinalizeRequest(BaseModel):
    """最終確認リクエスト"""

    session_data: Dict[str, Any]  # 前のステップのセッションデータ
    confirmed: bool = True  # 確認フラグ


@router.post("/start")
async def start_block_unit_price_process(request: StartProcessRequest):
    """
    ブロック単価計算処理開始 (Step 0)

    初期処理を実行し、運搬業者選択肢を返す
    """
    try:
        processor = BlockUnitPriceInteractive()
        result = processor.start_process(request.files)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"処理開始エラー: {str(e)}")


@router.post("/select-transport")
async def select_transport_vendors(request: TransportSelectionRequest):
    """
    運搬業者選択処理 (Step 1)

    選択された運搬業者を適用し、確認用データを返す
    """
    try:
        processor = BlockUnitPriceInteractive()
        result = processor.process_selection(request.session_data, request.selections)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"運搬業者選択エラー: {str(e)}")


@router.post("/finalize")
async def finalize_calculation(request: FinalizeRequest):
    """
    最終計算処理 (Step 2)

    最終的なブロック単価計算を実行し、結果を返す
    """
    try:
        processor = BlockUnitPriceInteractive()
        result = processor.finalize_calculation(request.session_data, request.confirmed)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"最終計算エラー: {str(e)}")


@router.get("/status/{step}")
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
        raise HTTPException(status_code=404, detail="無効なステップです")

    return step_info[step]
