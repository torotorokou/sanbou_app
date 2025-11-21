"""
Ingest Router - CSVアップロードと予約登録エンドポイント

機能:
  1. CSVアップロード（受入実績データ）
  2. トラック予約の作成/更新

TODO: Clean Architecture移行待ち
  - 現状: Routerにビジネスロジックが混在
  - 目標: UseCaseパターンへ移行（UploadIngestCsvUseCase, CreateReservationUseCase）
  - DI経由でUseCaseを取得するよう変更予定
  - Port&Adapter化予定（テスタビリティ向上）
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import io

from app.deps import get_db
from app.application.usecases.ingest.ingest_uc import IngestUseCase
from app.presentation.schemas import ReservationCreate, ReservationResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/csv", summary="Upload CSV data")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    CSVファイルをアップロード（受入実績データ）
    
    処理フロー:
      1. CSVファイルバリデーション（拡張子チェック）
      2. pandas.read_csv() で読み込み
      3. 必須カラムのバリデーション（TODO）
      4. データ正規化（日付フォーマット、数値型変換等、TODO）
      5. IngestUseCase.upload_csv() でDB保存
    
    TODO:
      - CSVカラム仕様の明確化
      - 必須カラムのバリデーション実装
      - 日付・数値のパース処理実装
      - UploadIngestCsvUseCase への移行（Clean Architecture）
    
    期待カラム（例）:
      - date: 日付
      - trucks: 台数
      - weight: 重量
      - vendor: 仕入先
      - ...等
    
    Args:
        file: アップロードされたCSVファイル
        db: SQLAlchemy Session
    
    Returns:
        アップロード結果（行数等）
    
    Raises:
        HTTPException(400): CSVファイル以外がアップロードされた場合
        HTTPException(500): CSV処理失敗時
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        # TODO: Validate required columns
        # TODO: Parse and normalize data (e.g., date formats, numeric types)
        rows = df.to_dict(orient="records")

        uc = IngestUseCase(db)
        result = uc.upload_csv(rows)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")


@router.post("/reserve", response_model=ReservationResponse, summary="Create truck reservation")
def create_reservation(
    req: ReservationCreate,
    db: Session = Depends(get_db),
):
    """
    Create or update a truck reservation for a specific date.
    TODO: Migrate to UseCase pattern (CreateReservationUseCase)
    """
    uc = IngestUseCase(db)
    return uc.create_reservation(req)
