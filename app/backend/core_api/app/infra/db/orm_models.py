"""
SQLAlchemy ORM models for database tables.
Schemas: core, jobs, forecast, raw, app

raw スキーマのモデルは shogun_csv_masters.yaml から動的に生成されます。
"""
from datetime import datetime, date as date_type
from uuid import UUID
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, TIMESTAMP, JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ========================================
# jobs schema
# ========================================

class ForecastJob(Base):
    """jobs.forecast_jobs table."""
    __tablename__ = "forecast_jobs"
    __table_args__ = {"schema": "jobs"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_type = Column(String, nullable=False)
    target_from = Column(Date, nullable=False)
    target_to = Column(Date, nullable=False)
    status = Column(String, nullable=False)  # queued | running | done | failed
    attempts = Column(Integer, nullable=False, default=0)
    scheduled_for = Column(TIMESTAMP, nullable=True)
    actor = Column(String, nullable=True)
    payload_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())


# ========================================
# forecast schema
# ========================================

class PredictionDaily(Base):
    """forecast.predictions_daily table."""
    __tablename__ = "predictions_daily"
    __table_args__ = {"schema": "forecast"}

    date = Column(Date, primary_key=True)
    y_hat = Column(Numeric, nullable=False)
    y_lo = Column(Numeric, nullable=True)
    y_hi = Column(Numeric, nullable=True)
    model_version = Column(String, nullable=True)
    generated_at = Column(TIMESTAMP, nullable=False, default=func.now())


# ========================================
# core schema (ingest data)
# ========================================

class InboundActual(Base):
    """
    core.inbound_actuals table: CSV upload data.
    TODO: Define proper columns based on CSV spec.
    """
    __tablename__ = "inbound_actuals"
    __table_args__ = {"schema": "core"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    # TODO: Add other columns (trucks, weight, vendor, etc.)
    data_json = Column(JSON, nullable=True)  # Flexible storage for now
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())


class InboundReservation(Base):
    """core.inbound_reservations table: truck reservations."""
    __tablename__ = "inbound_reservations"
    __table_args__ = {"schema": "core"}

    date = Column(Date, primary_key=True)
    trucks = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())


# ========================================
# app schema (announcements)
# ========================================

class AnnouncementORM(Base):
    """app.announcements table: システムのお知らせ"""
    __tablename__ = "announcements"
    __table_args__ = {"schema": "app"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    body_md = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="info")
    tags = Column(JSON, nullable=True, default=list)
    publish_from = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    publish_to = Column(TIMESTAMP(timezone=True), nullable=True)
    audience = Column(String(50), nullable=False, default="all")
    attachments = Column(JSON, nullable=True, default=list)
    notification_plan = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Text, nullable=True)

    # Relationship
    user_states = relationship("AnnouncementUserStateORM", back_populates="announcement", cascade="all, delete-orphan")


class AnnouncementUserStateORM(Base):
    """app.announcement_user_states table: ユーザーごとのお知らせ既読・確認状態"""
    __tablename__ = "announcement_user_states"
    __table_args__ = {"schema": "app"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=False)
    announcement_id = Column(Integer, ForeignKey("app.announcements.id", ondelete="CASCADE"), nullable=False)
    read_at = Column(TIMESTAMP(timezone=True), nullable=True)
    ack_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Relationship
    announcement = relationship("AnnouncementORM", back_populates="user_states")


# ========================================
# stg schema (reservation data)
# ========================================

class ReserveDailyManual(Base):
    """stg.reserve_daily_manual table: 手入力の日次予約合計"""
    __tablename__ = "reserve_daily_manual"
    __table_args__ = {"schema": "stg"}

    reserve_date = Column(Date, primary_key=True)
    total_trucks = Column(Integer, nullable=False, default=0)
    fixed_trucks = Column(Integer, nullable=False, default=0)
    note = Column(Text, nullable=True)
    created_by = Column(Text, nullable=True)
    updated_by = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Text, nullable=True)


class ReserveCustomerDaily(Base):
    """stg.reserve_customer_daily table: 顧客ごとの予約一覧"""
    __tablename__ = "reserve_customer_daily"
    __table_args__ = {"schema": "stg"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    reserve_date = Column(Date, nullable=False)
    customer_cd = Column(Text, nullable=False)
    customer_name = Column(Text, nullable=True)
    planned_trucks = Column(Integer, nullable=False, default=0)
    is_fixed_customer = Column(Integer, nullable=False, default=False)  # Boolean stored as int
    note = Column(Text, nullable=True)
    created_by = Column(Text, nullable=True)
    updated_by = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())


# ========================================
# app schema - Notifications
# ========================================

class NotificationOutboxORM(Base):
    """app.notification_outbox table - 通知Outbox"""
    __tablename__ = "notification_outbox"
    __table_args__ = {"schema": "app"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    channel = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    recipient_key = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    url = Column(String(1000), nullable=True)
    meta = Column(JSONB, nullable=True)
    scheduled_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    failure_type = Column(String(20), nullable=True)


# ========================================
# raw schema (shogun CSV data)
# YAMLから動的に生成されるモデル
# ========================================

# 動的モデルをインポート
from app.infra.db.dynamic_models import (
    get_shogun_model_class,
    ReceiveShogunFlash,
    YardShogunFlash,
    ShipmentShogunFlash,
)

# 後方互換性のため、ここでも公開
__all__ = [
    'Base',
    'ForecastJob',
    'PredictionDaily',
    'InboundActual',
    'InboundReservation',
    'AnnouncementORM',
    'AnnouncementUserStateORM',
    'ReserveDailyManual',
    'ReserveCustomerDaily',
    'NotificationOutboxORM',
    'ReceiveShogunFlash',
    'YardShogunFlash',
    'ShipmentShogunFlash',
    'get_shogun_model_class',
]
