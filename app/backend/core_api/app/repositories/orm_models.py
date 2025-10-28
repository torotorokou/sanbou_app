"""
SQLAlchemy ORM models for database tables.
Schemas: core, jobs, forecast, raw

raw スキーマのモデルは syogun_csv_masters.yaml から動的に生成されます。
"""
from datetime import datetime, date as date_type
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, TIMESTAMP, JSON, func
from sqlalchemy.orm import declarative_base

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
# raw schema (shogun CSV data)
# YAMLから動的に生成されるモデル
# ========================================

# 動的モデルをインポート
from app.repositories.dynamic_models import (
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
    'ReceiveShogunFlash',
    'YardShogunFlash',
    'ShipmentShogunFlash',
    'get_shogun_model_class',
]
