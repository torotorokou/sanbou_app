"""
DI Providers - Dependency Injection Container

このファイルはアプリケーション全体のDIを集約します。
- Repository の生成（schema/table_map の切替）
- UseCase の生成（将来的に拡張）

設計方針:
  - Router から new を排除し、DI 経由でインスタンスを取得
  - 環境差分（debug/raw、flash/final）をここで吸収
  - SET LOCAL search_path によるスキーマ切替を活用
"""
import logging
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.deps import get_db
from app.infra.adapters.upload.shogun_csv_repository import ShogunCsvRepository
from app.infra.adapters.misc.shogun_flash_debug_repo import ShogunFlashDebugRepository
from app.infra.adapters.dashboard.dashboard_target_repo import DashboardTargetRepository
from app.infra.adapters.forecast.job_repo import JobRepository
from app.infra.adapters.forecast.forecast_query_repo import ForecastQueryRepository
from app.infra.clients.rag_client import RAGClient
from app.infra.clients.ledger_client import LedgerClient
from app.infra.clients.manual_client import ManualClient
from app.infra.clients.ai_client import AIClient

logger = logging.getLogger(__name__)


# ========================================================================
# Repository Providers (schema/table switching via search_path + table_map)
# ========================================================================
# 注意: SET LOCAL search_path はトランザクションスコープ
#      Session.commit() または rollback() で自動的にリセットされる
#
# 安全性:
#  - SET LOCAL は接続プールで再利用されても安全（トランザクション終了でリセット）
#  - 複数リクエスト間で影響しない（各リクエスト = 新規トランザクション）
#  - この方式により、コード差分ゼロでスキーマ切替が可能


def get_repo_default(db: Session = Depends(get_db)) -> ShogunCsvRepository:
    """デフォルトリポジトリ(raw schema)を返す"""
    db.execute(text("SET LOCAL search_path TO raw, public"))
    return ShogunCsvRepository(db)


def get_shogun_csv_repo_target(db: Session = Depends(get_db)) -> ShogunCsvRepository:
    """
    /upload/syogun_csv_target 用 (debug schema)
    """
    db.execute(text("SET LOCAL search_path TO debug, public"))
    return ShogunCsvRepository(db)


def get_repo_debug_flash(db: Session = Depends(get_db)) -> ShogunCsvRepository:
    """
    /upload/shogun_flash 用 (debug schema + テーブル名変更)
    table_map: receive/yard/shipment → receive_flash/yard_flash/shipment_flash
    """
    db.execute(text("SET LOCAL search_path TO debug, public"))
    return ShogunCsvRepository(
        db,
        table_map={
            "receive": "receive_flash",
            "yard": "yard_flash",
            "shipment": "shipment_flash",
        },
    )


def get_repo_debug_final(db: Session = Depends(get_db)) -> ShogunCsvRepository:
    """
    /upload/shogun_final 用 (debug schema + テーブル名変更)
    table_map: receive/yard/shipment → receive_final/yard_final/shipment_final
    """
    db.execute(text("SET LOCAL search_path TO debug, public"))
    return ShogunCsvRepository(
        db,
        table_map={
            "receive": "receive_final",
            "yard": "yard_final",
            "shipment": "shipment_final",
        },
    )


# ========================================================================
# UseCase Providers
# ========================================================================
from app.application.usecases.upload.upload_syogun_csv_uc import UploadSyogunCsvUseCase
from backend_shared.infrastructure.config.config_loader import SyogunCsvConfigLoader
from backend_shared.usecases.csv_validator.csv_upload_validator_api import CSVValidationResponder

# CSV設定とバリデーターの初期化（アプリケーションスコープで共有）
_csv_config = SyogunCsvConfigLoader()
_required_columns = {
    "receive": _csv_config.get_expected_headers("receive"),
    "yard": _csv_config.get_expected_headers("yard"),
    "shipment": _csv_config.get_expected_headers("shipment"),
}
_validator = CSVValidationResponder(required_columns=_required_columns)


def get_uc_default(repo: ShogunCsvRepository = Depends(get_repo_default)) -> UploadSyogunCsvUseCase:
    """デフォルトスキーマ用のUploadSyogunCsvUseCase"""
    return UploadSyogunCsvUseCase(
        csv_writer=repo,
        csv_config=_csv_config,
        validator=_validator,
    )


def get_uc_target(repo: ShogunCsvRepository = Depends(get_shogun_csv_repo_target)) -> UploadSyogunCsvUseCase:
    """Targetスキーマ用のUploadSyogunCsvUseCase"""
    return UploadSyogunCsvUseCase(
        csv_writer=repo,
        csv_config=_csv_config,
        validator=_validator,
    )


def get_uc_debug_flash(repo: ShogunCsvRepository = Depends(get_repo_debug_flash)) -> UploadSyogunCsvUseCase:
    """Debug Flash用のUploadSyogunCsvUseCase"""
    return UploadSyogunCsvUseCase(
        csv_writer=repo,
        csv_config=_csv_config,
        validator=_validator,
    )


def get_uc_debug_final(repo: ShogunCsvRepository = Depends(get_repo_debug_final)) -> UploadSyogunCsvUseCase:
    """Debug Final用のUploadSyogunCsvUseCase"""
    return UploadSyogunCsvUseCase(
        csv_writer=repo,
        csv_config=_csv_config,
        validator=_validator,
    )


# ========================================================================
# Dashboard UseCase Providers
# ========================================================================
from app.application.usecases.dashboard.build_target_card_uc import BuildTargetCardUseCase


def get_dashboard_target_repo(db: Session = Depends(get_db)) -> DashboardTargetRepository:
    """DashboardTargetRepository提供"""
    return DashboardTargetRepository(db)


def get_build_target_card_uc(
    repo: DashboardTargetRepository = Depends(get_dashboard_target_repo)
) -> BuildTargetCardUseCase:
    """BuildTargetCardUseCase提供"""
    return BuildTargetCardUseCase(query=repo)


# ========================================================================
# Forecast UseCase Providers
# ========================================================================
from app.application.usecases.forecast.forecast_job_uc import (
    CreateForecastJobUseCase,
    GetForecastJobStatusUseCase,
    GetPredictionsUseCase,
)


def get_job_repo(db: Session = Depends(get_db)) -> JobRepository:
    """JobRepository提供"""
    return JobRepository(db)


def get_forecast_query_repo(db: Session = Depends(get_db)) -> ForecastQueryRepository:
    """ForecastQueryRepository提供"""
    return ForecastQueryRepository(db)


def get_create_forecast_job_uc(
    job_repo: JobRepository = Depends(get_job_repo)
) -> CreateForecastJobUseCase:
    """CreateForecastJobUseCase提供"""
    return CreateForecastJobUseCase(job_repo=job_repo)


def get_forecast_job_status_uc(
    job_repo: JobRepository = Depends(get_job_repo)
) -> GetForecastJobStatusUseCase:
    """GetForecastJobStatusUseCase提供"""
    return GetForecastJobStatusUseCase(job_repo=job_repo)


def get_predictions_uc(
    query_repo: ForecastQueryRepository = Depends(get_forecast_query_repo)
) -> GetPredictionsUseCase:
    """GetPredictionsUseCase提供"""
    return GetPredictionsUseCase(query_repo=query_repo)


# ========================================================================
# External API UseCase Providers
# ========================================================================
from app.application.usecases.external.external_api_uc import (
    AskRAGUseCase,
    GenerateLedgerReportUseCase,
    GenerateReportUseCase,
    ListManualsUseCase,
    GetManualUseCase,
    ClassifyTextUseCase,
)


def get_rag_client() -> RAGClient:
    """RAGClient提供"""
    return RAGClient()


def get_ledger_client() -> LedgerClient:
    """LedgerClient提供"""
    return LedgerClient()


def get_manual_client() -> ManualClient:
    """ManualClient提供"""
    return ManualClient()


def get_ai_client() -> AIClient:
    """AIClient提供"""
    return AIClient()


def get_ask_rag_uc(client: RAGClient = Depends(get_rag_client)) -> AskRAGUseCase:
    """AskRAGUseCase提供"""
    return AskRAGUseCase(rag_client=client)


def get_ledger_report_uc(
    client: LedgerClient = Depends(get_ledger_client)
) -> GenerateLedgerReportUseCase:
    """GenerateLedgerReportUseCase提供"""
    return GenerateLedgerReportUseCase(ledger_client=client)


def get_list_manuals_uc(
    client: ManualClient = Depends(get_manual_client)
) -> ListManualsUseCase:
    """ListManualsUseCase提供"""
    return ListManualsUseCase(manual_client=client)


def get_get_manual_uc(
    client: ManualClient = Depends(get_manual_client)
) -> GetManualUseCase:
    """GetManualUseCase提供"""
    return GetManualUseCase(manual_client=client)


def get_generate_report_uc(
    client: LedgerClient = Depends(get_ledger_client)
) -> GenerateReportUseCase:
    """GenerateReportUseCase提供"""
    return GenerateReportUseCase(ledger_client=client)


def get_classify_text_uc(client: AIClient = Depends(get_ai_client)) -> ClassifyTextUseCase:
    """ClassifyTextUseCase提供"""
    return ClassifyTextUseCase(ai_client=client)


# ========================================================================
# Inbound UseCase Providers
# ========================================================================
from app.application.usecases.inbound.get_inbound_daily_uc import GetInboundDailyUseCase
from app.infra.adapters.inbound.inbound_pg_repository import InboundPgRepository


def get_inbound_repo(db: Session = Depends(get_db)) -> InboundPgRepository:
    """InboundPgRepository提供"""
    return InboundPgRepository(db)


def get_inbound_daily_uc(
    repo: InboundPgRepository = Depends(get_inbound_repo)
) -> GetInboundDailyUseCase:
    """GetInboundDailyUseCase提供"""
    return GetInboundDailyUseCase(query=repo)

