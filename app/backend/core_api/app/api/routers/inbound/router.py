"""
Inbound Router - 搬入データ取得エンドポイント

日次搬入量データの取得を提供。
主な特徴:
  - カレンダー連続データ(欠損日を0埋め)
  - 累積計算対応(全期間/月別/週別)
  - 営業日フラグ付き
  - ISO週番号対応

使用例:
  - グラフ表示用の日次データ取得
  - 月別/週別集計の基礎データ
  - トレンド分析用の累積データ

設計方針（Clean Architecture準拠）:
  - Router層の責務: Request → Input DTO → UseCase → Output DTO → Response
  - カスタム例外を使用(HTTPExceptionは使用しない)
  - バリデーションはUseCase層で実施
  - ビジネスロジックは一切含まない
"""

from datetime import date as date_type

from fastapi import APIRouter, Depends, Query

from app.config.di_providers import get_inbound_daily_uc
from app.core.domain.inbound import CumScope, InboundDailyRow
from app.core.usecases.inbound.dto import GetInboundDailyInput
from app.core.usecases.inbound.get_inbound_daily_uc import GetInboundDailyUseCase
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)

router = APIRouter(prefix="/inbound", tags=["inbound"])


@router.get("/daily", response_model=list[InboundDailyRow])
def get_inbound_daily(
    start: date_type = Query(..., description="開始日 (YYYY-MM-DD)"),
    end: date_type = Query(..., description="終了日 (YYYY-MM-DD)"),
    segment: str | None = Query(None, description="セグメントフィルタ（オプション）"),
    cum_scope: CumScope = Query(
        "none", description="累積計算スコープ（range|month|week|none）"
    ),
    uc: GetInboundDailyUseCase = Depends(get_inbound_daily_uc),
) -> list[InboundDailyRow]:
    """
    日次搬入量データを取得（カレンダー連続・0埋め済み）

    Router層の責務:
      1. Query Parameters → Input DTO 変換
      2. UseCase 呼び出し
      3. Output DTO → Response 変換

    Args:
        start: 開始日（必須）
        end: 終了日（必須）
        segment: セグメントフィルタ（オプション、None=全体）
        cum_scope: 累積計算スコープ（range|month|week|none）
        uc: GetInboundDailyUseCase（DI経由で注入）

    Returns:
        List[InboundDailyRow]: 日次搬入量データのリスト

    Raises:
        ValidationError: 入力値が不正（400 Bad Request）
        InfrastructureError: DB接続エラー等（500 Internal Server Error）
    """
    # 1. Request → Input DTO 変換
    input_dto = GetInboundDailyInput(
        start=start,
        end=end,
        segment=segment,
        cum_scope=cum_scope,
    )

    # 2. UseCase 実行
    output = uc.execute(input_dto)

    logger.info(
        f"GET /inbound/daily: {output.total_count} rows, "
        f"start={start}, end={end}, segment={segment}, cum_scope={cum_scope}"
    )

    # 3. Output DTO → Response 変換（この場合はdataをそのまま返却）
    return output.data
