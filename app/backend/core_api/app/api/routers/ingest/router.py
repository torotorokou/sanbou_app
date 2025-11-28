"""
Ingest Router - CSVアップロードと予約登録エンドポイント

機能:
  1. CSVアップロード（受入実績データ）
  2. トラック予約の作成/更新

設計方針:
  - Port&Adapter パターン適用済み
  - Router層は薄く保つ（DI + UseCase呼び出しのみ）
  - ビジネスロジックはUseCaseに集約
  - カスタム例外を使用（HTTPExceptionは使用しない）
"""
from fastapi import APIRouter, Depends, UploadFile, File
import pandas as pd
import io
import logging

from app.core.usecases.ingest.upload_ingest_csv_uc import UploadIngestCsvUseCase
from app.core.usecases.ingest.create_reservation_uc import CreateReservationUseCase
from app.config.di_providers import get_upload_ingest_csv_uc, get_create_reservation_uc
from app.api.schemas import ReservationCreate, ReservationResponse
from app.shared.exceptions import ValidationError, InfrastructureError

router = APIRouter(prefix="/ingest", tags=["ingest"])
logger = logging.getLogger(__name__)


@router.post("/csv", summary="Upload CSV data")
async def upload_csv(
    file: UploadFile = File(...),
    uc: UploadIngestCsvUseCase = Depends(get_upload_ingest_csv_uc),
):
    """
    CSVファイルをアップロード（受入実績データ）
    
    処理フロー:
      1. CSVファイルバリデーション（拡張子チェック）
      2. pandas.read_csv() で読み込み
      3. UploadIngestCsvUseCase.execute() でDB保存
    
    Note:
      - 現状はスタブ実装（バリデーション・フォーマットは将来実装）
      - 完全実装には要件定義が必要:
        * CSVカラム仕様の明確化
        * 必須カラムの定義
        * 日付・数値のパース処理
    
    Args:
        file: アップロードされたCSVファイル
        uc: UploadIngestCsvUseCase (DI)
    
    Returns:
        アップロード結果（行数等）
    
    Raises:
        ValidationError: CSVファイル以外がアップロードされた場合
        InfrastructureError: CSV処理失敗時
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise ValidationError("Only CSV files are supported", field="file")

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        rows = df.to_dict(orient="records")

        logger.info(f"Processing CSV upload: {file.filename}, rows={len(rows)}")
        result = uc.execute(rows)
        return result
    except pd.errors.EmptyDataError:
        raise ValidationError("CSV file is empty", field="file")
    except pd.errors.ParserError as e:
        raise ValidationError(f"Failed to parse CSV: {str(e)}", field="file")
    except Exception as e:
        logger.error(f"Failed to process CSV: {str(e)}", exc_info=True)
        raise InfrastructureError(f"Failed to process CSV", cause=e)


@router.post("/reserve", response_model=ReservationResponse, summary="Create truck reservation")
def create_reservation(
    req: ReservationCreate,
    uc: CreateReservationUseCase = Depends(get_create_reservation_uc),
):
    """
    トラック予約の作成/更新
    
    Note:
      - 現状はスタブ実装（予約ビジネスルールは将来実装）
      - 完全実装には要件定義が必要:
        * 予約上限チェック
        * 重複予約のハンドリング
        * 予約履歴の記録
    
    Args:
        req: 予約作成リクエスト
        uc: CreateReservationUseCase (DI)
    
    Returns:
        予約作成結果
    """
    return uc.execute(req)
