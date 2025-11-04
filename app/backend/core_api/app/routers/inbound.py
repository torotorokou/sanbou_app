"""
Inbound API Router
日次搬入量データの取得エンドポイント
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional
import logging
from datetime import date as date_type
from sqlalchemy.orm import Session

from app.deps import get_db
from app.domain.inbound import InboundDailyRow, CumScope
from app.repositories.inbound_pg_repo import InboundPgRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inbound", tags=["inbound"])


@router.get("/daily", response_model=List[InboundDailyRow])
def get_inbound_daily(
    start: date_type = Query(..., description="開始日 (YYYY-MM-DD)"),
    end: date_type = Query(..., description="終了日 (YYYY-MM-DD)"),
    segment: Optional[str] = Query(None, description="セグメントフィルタ（オプション）"),
    cum_scope: CumScope = Query("none", description="累積計算スコープ（range|month|week|none）"),
    db: Session = Depends(get_db),
) -> List[InboundDailyRow]:
    """
    日次搬入量データを取得（カレンダー連続・0埋め済み）
    
    Args:
        start: 開始日（必須）
        end: 終了日（必須）
        segment: セグメントフィルタ（オプション、None=全体）
        cum_scope: 累積計算スコープ
            - "range": 全期間累積
            - "month": 月ごとリセット
            - "week": 週ごとリセット
            - "none": 累積なし（cum_tonはNULL）
        db: データベース接続
    
    Returns:
        日次搬入量データのリスト（連続日・0埋め済み）
    
    Raises:
        HTTPException: バリデーションエラーまたはDB接続エラー
    """
    try:
        repo = InboundPgRepository(db)
        data = repo.fetch_daily(start, end, segment, cum_scope)
        
        logger.info(
            f"GET /inbound/daily: {len(data)} rows, "
            f"start={start}, end={end}, segment={segment}, cum_scope={cum_scope}"
        )
        return data

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Failed to fetch inbound daily: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
