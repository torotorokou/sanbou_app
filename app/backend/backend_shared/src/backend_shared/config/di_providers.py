"""
DI Providers

依存関係の組み立て・DI コンテナ。

環境差分（schema 切替・debug/raw/flash/final 等）はここで吸収する。
UseCase / Repository 実装 / DB セッションを組み立てる。

使用例:
    # FastAPI での使用
    from backend_shared.config.di_providers import (
        provide_database_session_manager,
        provide_csv_formatter,
    )
    
    # セッションマネージャーを取得
    db_manager = provide_database_session_manager(db_url)
    
    # CSV フォーマッターを取得
    formatter = provide_csv_formatter(csv_type="shipment")
"""

from typing import Optional
from sqlalchemy.orm import Session
from backend_shared.infra.frameworks.database import DatabaseSessionManager
from backend_shared.config.config_loader import ShogunCsvConfigLoader
from backend_shared.core.usecases.csv_formatter.formatter_config import (
    build_formatter_config,
)
from backend_shared.core.usecases.csv_formatter.formatter_factory import CSVFormatterFactory
from backend_shared.core.domain.reserve.repositories import ReserveRepository
from backend_shared.infra.adapters.reserve import PostgreSQLReserveRepository


def provide_database_session_manager(
    db_url: str, *, echo: bool = False, pool_pre_ping: bool = True
) -> DatabaseSessionManager:
    """
    DatabaseSessionManager を提供する
    
    Args:
        db_url: データベース接続 URL
        echo: SQL ログ出力を有効化するか
        pool_pre_ping: 接続プールの事前 ping を有効化するか
        
    Returns:
        DatabaseSessionManager インスタンス
    """
    return DatabaseSessionManager(db_url, echo=echo, pool_pre_ping=pool_pre_ping)


def provide_csv_config_loader() -> ShogunCsvConfigLoader:
    """
    CSV 設定ローダーを提供する
    
    Returns:
        ShogunCsvConfigLoader インスタンス
    """
    return ShogunCsvConfigLoader()


def provide_csv_formatter(csv_type: str, config_loader: Optional[ShogunCsvConfigLoader] = None):
    """
    CSV フォーマッターを提供する
    
    Args:
        csv_type: CSV タイプ（例: "shipment", "receive"）
        config_loader: 設定ローダー（省略時は新規作成）
        
    Returns:
        BaseCSVFormatter インスタンス
    """
    if config_loader is None:
        config_loader = provide_csv_config_loader()
    
    config = build_formatter_config(config_loader, csv_type)
    formatter = CSVFormatterFactory.get_formatter(csv_type, config)
    return formatter


def get_reserve_repository(session: Session) -> ReserveRepository:
    """
    ReserveRepository を提供する
    
    Args:
        session: SQLAlchemy セッション
        
    Returns:
        ReserveRepository インスタンス
    """
    return PostgreSQLReserveRepository(session)


__all__ = [
    "provide_database_session_manager",
    "provide_csv_config_loader",
    "provide_csv_formatter",
    "get_reserve_repository",
]
