# -*- coding: utf-8 -*-
"""
Reservation repository implementation with PostgreSQL.
予約データ（手入力・顧客別・予測用ビュー）の取得・更新
"""
from datetime import date as date_type
from typing import List, Optional
import logging
import calendar

from sqlalchemy import text, select, update, delete
from sqlalchemy.orm import Session

from backend_shared.application.logging import get_module_logger
from app.core.ports.reservation_repository_port import ReservationRepository
from app.core.domain.reservation import (
    ReservationManualRow,
    ReservationForecastRow,
    ReservationCustomerRow,
)
from app.infra.db.orm_models import ReserveDailyManual, ReserveCustomerDaily

logger = get_module_logger(__name__)


class ReservationRepositoryImpl(ReservationRepository):
    """
    PostgreSQL implementation of ReservationRepository.
    """

    def __init__(self, db: Session):
        self.db = db

    # ========================================
    # Manual (手入力) Operations
    # ========================================

    def get_manual(self, reserve_date: date_type) -> Optional[ReservationManualRow]:
        """指定日の手入力予約データを取得（論理削除を除外）"""
        try:
            stmt = select(ReserveDailyManual).where(
                ReserveDailyManual.reserve_date == reserve_date,
                ReserveDailyManual.deleted_at == None  # 論理削除を除外
            )
            result = self.db.execute(stmt).scalar_one_or_none()
            
            if result is None:
                return None
            
            # Convert ORM to domain entity
            return ReservationManualRow.model_validate(result)
        except Exception as e:
            logger.error(f"Failed to get manual reservation: {e}", exc_info=True)
            raise

    def upsert_manual(self, data: ReservationManualRow) -> ReservationManualRow:
        """手入力予約データを登録・更新（論理削除を除外）"""
        try:
            # Check if exists (論理削除を除外)
            existing = self.db.execute(
                select(ReserveDailyManual).where(
                    ReserveDailyManual.reserve_date == data.reserve_date,
                    ReserveDailyManual.deleted_at == None
                )
            ).scalar_one_or_none()
            
            # 削除済みデータがあるか確認（復活用）
            deleted_existing = self.db.execute(
                select(ReserveDailyManual).where(
                    ReserveDailyManual.reserve_date == data.reserve_date,
                    ReserveDailyManual.deleted_at != None
                )
            ).scalar_one_or_none()

            if existing:
                # Update (active record)
                stmt = (
                    update(ReserveDailyManual)
                    .where(
                        ReserveDailyManual.reserve_date == data.reserve_date,
                        ReserveDailyManual.deleted_at == None
                    )
                    .values(
                        total_trucks=data.total_trucks,
                        fixed_trucks=data.fixed_trucks,
                        note=data.note,
                        updated_by=data.updated_by,
                    )
                    .returning(ReserveDailyManual)
                )
                result = self.db.execute(stmt).scalar_one()
            elif deleted_existing:
                # 削除済みデータを復活
                stmt = (
                    update(ReserveDailyManual)
                    .where(ReserveDailyManual.reserve_date == data.reserve_date)
                    .values(
                        total_trucks=data.total_trucks,
                        fixed_trucks=data.fixed_trucks,
                        note=data.note,
                        updated_by=data.updated_by,
                        deleted_at=None,  # 復活
                        deleted_by=None,
                    )
                    .returning(ReserveDailyManual)
                )
                result = self.db.execute(stmt).scalar_one()
            else:
                # Insert
                new_obj = ReserveDailyManual(
                    reserve_date=data.reserve_date,
                    total_trucks=data.total_trucks,
                    fixed_trucks=data.fixed_trucks,
                    note=data.note,
                    created_by=data.created_by,
                    updated_by=data.updated_by,
                )
                self.db.add(new_obj)
                self.db.flush()
                result = new_obj

            self.db.commit()
            self.db.refresh(result)
            return ReservationManualRow.model_validate(result)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to upsert manual reservation: {e}", exc_info=True)
            raise

    def delete_manual(self, reserve_date: date_type) -> bool:
        """指定日の手入力予約データを論理削除"""
        try:
            from datetime import datetime, timezone
            
            # 論理削除: deleted_atを設定
            stmt = (
                update(ReserveDailyManual)
                .where(
                    ReserveDailyManual.reserve_date == reserve_date,
                    ReserveDailyManual.deleted_at == None  # 既に削除済みは除外
                )
                .values(
                    deleted_at=datetime.now(timezone.utc),
                    deleted_by="system"  # TODO: Get from auth context
                )
            )
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to soft-delete manual reservation: {e}", exc_info=True)
            raise

    # ========================================
    # Forecast View (予測用) Operations
    # ========================================

    def get_forecast_month(
        self, year: int, month: int
    ) -> List[ReservationForecastRow]:
        """指定月の予測用予約データを取得（manual優先、なければcustomer集計）"""
        try:
            # Calculate month start and end dates
            _, last_day = calendar.monthrange(year, month)
            start_date = date_type(year, month, 1)
            end_date = date_type(year, month, last_day)

            # Query mart.v_reserve_daily_for_forecast view
            sql = text("""
                SELECT 
                    date,
                    reserve_trucks,
                    reserve_fixed_trucks,
                    reserve_fixed_ratio,
                    source
                FROM mart.v_reserve_daily_for_forecast
                WHERE date >= :start_date AND date <= :end_date
                ORDER BY date
            """)
            
            result = self.db.execute(
                sql, {"start_date": start_date, "end_date": end_date}
            )
            
            rows = []
            for row in result:
                rows.append(
                    ReservationForecastRow(
                        date=row.date,
                        reserve_trucks=row.reserve_trucks,
                        reserve_fixed_trucks=row.reserve_fixed_trucks,
                        reserve_fixed_ratio=float(row.reserve_fixed_ratio),
                        source=row.source,
                    )
                )
            
            return rows
        except Exception as e:
            logger.error(f"Failed to get forecast month: {e}", exc_info=True)
            raise
