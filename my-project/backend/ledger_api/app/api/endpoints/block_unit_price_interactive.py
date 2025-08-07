"""
ブロック単価計算インタラクティブAPIエンドポイント

ブロック単価計算処理を3つのステップに分けて実行するAPIエンドポイントです。
ユーザーの入力を段階的に受け取りながら、最終的な計算結果を返します。
"""

# backend/app/api/endpoints/block_unit_price_interactive.py

from typing import Any, Dict

from api.services.csv_validator_facade import CsvValidatorService
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from src.api_response.response_base import ErrorApiResponse, SuccessApiResponse

# 統一レスポンスクラス
from src.api_response.response_error import (
    NoFilesUploadedResponse,
)

from app.api.services.csv_formatter_service import CsvFormatterService
from app.api.services.report.generator_factory import get_report_generator
from app.api.st_app.logic.manage.block_unit_price_interactive import (
    BlockUnitPriceInteractive,
)
from app.api.utils.excel_pdf_zip_utils import create_excel_bytes, generate_excel_pdf_zip
from backend_shared.src.utils.csv_reader import read_csv_files

# APIルーターの初期化
router = APIRouter()


class StartProcessRequest(BaseModel):
    """
    処理開始リクエストモデル

    Attributes:
        files (Dict[str, Any]): アップロードされたファイルデータ
    """

    files: Dict[str, Any]  # アップロードされたファイルデータ


class TransportSelectionRequest(BaseModel):
    """
    運搬業者選択リクエストモデル

    Attributes:
        session_data (Dict[str, Any]): 前のステップのセッションデータ
        selections (Dict[str, str]): 業者名と選択された運搬業者コードのマッピング
    """

    session_data: Dict[str, Any]  # 前のステップのセッションデータ
    selections: Dict[str, str]  # {業者名: 選択された運搬業者コード}


class FinalizeRequest(BaseModel):
    """
    最終確認リクエストモデル

    Attributes:
        session_data (Dict[str, Any]): 前のステップのセッションデータ
        confirmed (bool): 確認フラグ
    """

    session_data: Dict[str, Any]  # 前のステップのセッションデータ
    confirmed: bool = True  # 確認フラグ


# 統合API: CSVアップロード＋初期処理＋運搬業者選択肢返却
from fastapi import File, UploadFile


class UploadAndStartResponse(BaseModel):
    session_data: Dict[str, Any]
    transport_options: Dict[str, Any]


@router.post("/upload-and-start")
async def upload_and_start(
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
):
    """
    CSVファイルアップロードと初期処理（運搬業者選択肢返却）

    Args:
        shipment (UploadFile): 輸送データCSVファイル
        yard (UploadFile): ヤードデータCSVファイル
        receive (UploadFile): 受取データCSVファイル

    Returns:
        Dict: セッションデータと運搬業者選択肢

    Raises:
        HTTPException: 処理中にエラーが発生した場合
    """
    # アップロードされたファイルの整理
    files = {
        k: v
        for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items()
        if v is not None
    }
    print(f"Uploaded files: {list(files.keys())}")

    # ファイル未アップロードチェック
    if not files:
        print("No files uploaded.")
        return NoFilesUploadedResponse().to_json_response()

    # CSV読込処理
    dfs, error = read_csv_files(files)
    if error:
        return error.to_json_response()

    # CSVデータのバリデーション処理
    validator_service = CsvValidatorService()
    validation_error = validator_service.validate(dfs, files)
    if validation_error:
        print(f"Validation error: {validation_error}")
        return validation_error.to_json_response()

    # データフォーマット変換処理
    print("Formatting DataFrames...")
    formatter_service = CsvFormatterService()
    df_formatted = formatter_service.format(dfs)
    for csv_type, df in df_formatted.items():
        print(f"Formatted {csv_type}: shape={df.shape}")

    # 初期処理（運搬業者選択肢の生成）
    try:
        processor = BlockUnitPriceInteractive()
        result = processor.start_process(df_formatted)

        # ここで「APIレスポンス」ラップ
        if result.get("status") == "success":
            return SuccessApiResponse(
                code="STEP0_SUCCESS",
                detail="初期処理完了",
                result=result["data"],
            ).to_json_response()
    except Exception as e:
        return ErrorApiResponse(
            code="STEP0_ERROR",
            detail=f"初期処理中にエラーが発生しました: {str(e)}",
            status_code=500,
        ).to_json_response()


@router.post("/select-transport")
async def select_transport_vendors(request: TransportSelectionRequest):
    """
    運搬業者選択処理 (Step 1)

    選択された運搬業者を適用し、確認用データを返します。

    Args:
        request (TransportSelectionRequest): セッションデータと選択情報を含むリクエスト

    Returns:
        Dict: 運搬業者選択適用後の処理結果

    Raises:
        HTTPException: 処理中にエラーが発生した場合
    """
    try:
        # 運搬業者選択の処理実行
        processor = BlockUnitPriceInteractive()
        result = processor.process_selection(request.session_data, request.selections)

        # フロントエンドが期待する形式に合わせてレスポンスを整形
        if result.get("status") == "success":
            return {
                "status": "success",
                "message": result["message"],
                "session_data": result["data"]["session_data"],
                "selection_summary": result["data"]["selection_summary"],
            }
        else:
            return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"運搬業者選択エラー: {str(e)}")


@router.post("/finalize")
async def finalize_calculation(request: FinalizeRequest):
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
        # 最終計算の実行
        processor = BlockUnitPriceInteractive()
        result = processor.finalize_calculation(request.session_data, request.confirmed)

        # フロントエンドが期待する形式に合わせてレスポンスを整形
        if result.get("status") == "completed":
            return {
                "status": "completed",
                "message": result["message"],
                "data": result["data"],
            }
        elif result.get("status") == "cancelled":
            return {"status": "cancelled", "message": result["message"]}
        else:
            return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"最終計算エラー: {str(e)}")


@router.get("/status/{step}")
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


@router.post("/upload")
async def upload_csv(
    shipment: UploadFile = File(...),
    yard: UploadFile = File(...),
    receive: UploadFile = File(...),
):
    """
    CSVファイルアップロード処理

    複数のCSVファイルをアップロードし、データの整形とバリデーションを行います。

    Args:
        shipment (UploadFile): 輸送データCSVファイル
        yard (UploadFile): ヤードデータCSVファイル
        receive (UploadFile): 受取データCSVファイル

    Returns:
        Dict: アップロードと処理結果

    Raises:
        HTTPException: 処理中にエラーが発生した場合
    """
    # アップロードされたファイルの整理
    files = {
        k: v
        for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items()
        if v is not None
    }
    print(f"Uploaded files: {list(files.keys())}")

    # ファイル未アップロードチェック
    if not files:
        print("No files uploaded.")
        return NoFilesUploadedResponse().to_json_response()

    # CSV読込処理
    dfs, error = read_csv_files(files)
    if error:
        return error.to_json_response()

    # CSVデータのバリデーション処理
    validator_service = CsvValidatorService()
    validation_error = validator_service.validate(dfs, files)
    if validation_error:
        print(f"Validation error: {validation_error}")
        return validation_error.to_json_response()

    # データフォーマット変換処理
    print("Formatting DataFrames...")
    formatter_service = CsvFormatterService()
    df_formatted = formatter_service.format(dfs)
    for csv_type, df in df_formatted.items():
        print(f"Formatted {csv_type}: shape={df.shape}")

    # ...レスポンスを返す処理...
