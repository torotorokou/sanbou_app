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
from app.infra.adapters.upload.raw_data_repository import RawDataRepository
from app.infra.adapters.materialized_view.materialized_view_refresher import MaterializedViewRefresher
from app.infra.adapters.dashboard.dashboard_target_repository import DashboardTargetRepository
from app.infra.adapters.forecast.job_repository import JobRepository
from app.infra.adapters.forecast.forecast_query_repository import ForecastQueryRepository
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


def get_repo_raw_default(db: Session = Depends(get_db)) -> ShogunCsvRepository:
    """raw層リポジトリ(raw schema, *_shogun_flash tables - デフォルト)"""
    return ShogunCsvRepository(db, schema="raw")


def get_repo_stg_flash(db: Session = Depends(get_db)) -> ShogunCsvRepository:
    """stg層リポジトリ(stg schema, *_shogun_flash tables)"""
    return ShogunCsvRepository(db, schema="stg")


def get_repo_raw_flash(db: Session = Depends(get_db)) -> ShogunCsvRepository:
    """
    raw層flash用 (raw schema, *_shogun_flash tables)
    デフォルトのテーブル名（*_shogun_flash）を使用
    """
    return ShogunCsvRepository(
        db,
        schema="raw",
        # table_map なし = デフォルトの *_shogun_flash を使用
    )


def get_repo_stg_final(db: Session = Depends(get_db)) -> ShogunCsvRepository:
    """
    stg層final用 (stg schema, *_shogun_final tables)
    """
    return ShogunCsvRepository(
        db,
        schema="stg",
        table_map={
            "receive": "shogun_final_receive",
            "yard": "shogun_final_yard",
            "shipment": "shogun_final_shipment",
        },
    )


def get_repo_raw_final(db: Session = Depends(get_db)) -> ShogunCsvRepository:
    """
    raw層final用 (raw schema, *_shogun_final tables)
    """
    return ShogunCsvRepository(
        db,
        schema="raw",
        table_map={
            "receive": "shogun_final_receive",
            "yard": "shogun_final_yard",
            "shipment": "shogun_final_shipment",
        },
    )


# ========================================================================
# UseCase Providers
# ========================================================================
from app.application.usecases.upload.upload_shogun_csv_uc import UploadShogunCsvUseCase
from backend_shared.infrastructure.config.config_loader import ShogunCsvConfigLoader
from backend_shared.usecases.csv_validator.csv_upload_validator_api import CSVValidationResponder

# CSV設定とバリデーターの初期化（アプリケーションスコープで共有）
_csv_config = ShogunCsvConfigLoader()
_required_columns = {
    "receive": _csv_config.get_expected_headers("receive"),
    "yard": _csv_config.get_expected_headers("yard"),
    "shipment": _csv_config.get_expected_headers("shipment"),
}
_validator = CSVValidationResponder(required_columns=_required_columns)


def get_raw_data_repo(db: Session = Depends(get_db)) -> RawDataRepository:
    """RawDataRepository提供 (raw schema専用)"""
    return RawDataRepository(db)


def get_mv_refresher(db: Session = Depends(get_db)) -> MaterializedViewRefresher:
    """
    MaterializedViewRefresher提供
    
    マテリアライズドビュー更新専用リポジトリ。
    CSVアップロード成功時にMVを自動更新するために使用。
    """
    return MaterializedViewRefresher(db)


def get_uc_default(
    raw_repo: ShogunCsvRepository = Depends(get_repo_raw_default),
    stg_repo: ShogunCsvRepository = Depends(get_repo_stg_flash),
    raw_data_repo: RawDataRepository = Depends(get_raw_data_repo),
    mv_refresher: MaterializedViewRefresher = Depends(get_mv_refresher)
) -> UploadShogunCsvUseCase:
    """デフォルト用のUploadShogunCsvUseCase (raw.shogun_flash_receive + stg.shogun_flash_receive)"""
    return UploadShogunCsvUseCase(
        raw_writer=raw_repo,
        stg_writer=stg_repo,
        csv_config=_csv_config,
        validator=_validator,
        raw_data_repo=raw_data_repo,
        mv_refresher=mv_refresher,
    )


def get_uc_flash(
    raw_repo: ShogunCsvRepository = Depends(get_repo_raw_flash),
    stg_repo: ShogunCsvRepository = Depends(get_repo_stg_flash),
    raw_data_repo: RawDataRepository = Depends(get_raw_data_repo),
    mv_refresher: MaterializedViewRefresher = Depends(get_mv_refresher)
) -> UploadShogunCsvUseCase:
    """Flash用のUploadShogunCsvUseCase (raw.shogun_flash_receive + stg.shogun_flash_receive)"""
    return UploadShogunCsvUseCase(
        raw_writer=raw_repo,
        stg_writer=stg_repo,
        csv_config=_csv_config,
        validator=_validator,
        raw_data_repo=raw_data_repo,
        mv_refresher=mv_refresher,
    )


def get_uc_stg_final(
    raw_repo: ShogunCsvRepository = Depends(get_repo_raw_final),
    stg_repo: ShogunCsvRepository = Depends(get_repo_stg_final),
    raw_data_repo: RawDataRepository = Depends(get_raw_data_repo),
    mv_refresher: MaterializedViewRefresher = Depends(get_mv_refresher)
) -> UploadShogunCsvUseCase:
    """Final用のUploadShogunCsvUseCase (raw.*_shogun_final + stg.*_shogun_final)"""
    return UploadShogunCsvUseCase(
        raw_writer=raw_repo,
        stg_writer=stg_repo,
        csv_config=_csv_config,
        validator=_validator,
        raw_data_repo=raw_data_repo,
        mv_refresher=mv_refresher,
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
from app.infra.adapters.inbound.inbound_repository import InboundRepositoryImpl
from app.domain.ports.inbound_repository_port import InboundRepository


def get_inbound_repo(db: Session = Depends(get_db)) -> InboundRepository:
    """InboundRepository 提供"""
    return InboundRepositoryImpl(db)


def get_inbound_daily_uc(
    repo: InboundRepository = Depends(get_inbound_repo)
) -> GetInboundDailyUseCase:
    """GetInboundDailyUseCase提供"""
    return GetInboundDailyUseCase(query=repo)


# ========================================================================
# KPI UseCase Providers
# ========================================================================
from app.application.usecases.kpi.kpi_uc import KPIUseCase
from app.infra.adapters.kpi.kpi_query_adapter import KPIQueryAdapter


def get_kpi_query_adapter(db: Session = Depends(get_db)) -> KPIQueryAdapter:
    """KPIQueryAdapter提供"""
    return KPIQueryAdapter(db)


def get_kpi_uc(
    kpi_query: KPIQueryAdapter = Depends(get_kpi_query_adapter)
) -> KPIUseCase:
    """KPIUseCase提供"""
    return KPIUseCase(kpi_query=kpi_query)


# ========================================================================
# Customer Churn UseCase Providers
# ========================================================================
from app.application.usecases.customer_churn import AnalyzeCustomerChurnUseCase
from app.infra.adapters.customer_churn import CustomerChurnQueryAdapter


def get_customer_churn_query_adapter(db: Session = Depends(get_db)) -> CustomerChurnQueryAdapter:
    """CustomerChurnQueryAdapter提供"""
    return CustomerChurnQueryAdapter(db)


def get_analyze_customer_churn_uc(
    query_adapter: CustomerChurnQueryAdapter = Depends(get_customer_churn_query_adapter)
) -> AnalyzeCustomerChurnUseCase:
    """AnalyzeCustomerChurnUseCase提供"""
    return AnalyzeCustomerChurnUseCase(query_port=query_adapter)


# ========================================================================
# Sales Tree UseCase Providers
# ========================================================================
from app.application.usecases.sales_tree.fetch_summary_uc import FetchSalesTreeSummaryUseCase
from app.application.usecases.sales_tree.fetch_daily_series_uc import FetchSalesTreeDailySeriesUseCase
from app.application.usecases.sales_tree.fetch_pivot_uc import FetchSalesTreePivotUseCase
from app.application.usecases.sales_tree.export_csv_uc import ExportSalesTreeCSVUseCase
from app.application.usecases.sales_tree.fetch_detail_lines_uc import FetchSalesTreeDetailLinesUseCase
from app.infra.adapters.sales_tree.sales_tree_repository import SalesTreeRepository


def get_sales_tree_repo(db: Session = Depends(get_db)) -> SalesTreeRepository:
    """SalesTreeRepository提供"""
    return SalesTreeRepository(db)


def get_fetch_sales_tree_summary_uc(
    repo: SalesTreeRepository = Depends(get_sales_tree_repo)
) -> FetchSalesTreeSummaryUseCase:
    """FetchSalesTreeSummaryUseCase提供"""
    return FetchSalesTreeSummaryUseCase(query=repo)


def get_fetch_sales_tree_daily_series_uc(
    repo: SalesTreeRepository = Depends(get_sales_tree_repo)
) -> FetchSalesTreeDailySeriesUseCase:
    """FetchSalesTreeDailySeriesUseCase提供"""
    return FetchSalesTreeDailySeriesUseCase(query=repo)


def get_fetch_sales_tree_pivot_uc(
    repo: SalesTreeRepository = Depends(get_sales_tree_repo)
) -> FetchSalesTreePivotUseCase:
    """FetchSalesTreePivotUseCase提供"""
    return FetchSalesTreePivotUseCase(query=repo)


def get_export_sales_tree_csv_uc(
    repo: SalesTreeRepository = Depends(get_sales_tree_repo)
) -> ExportSalesTreeCSVUseCase:
    """ExportSalesTreeCSVUseCase提供"""
    return ExportSalesTreeCSVUseCase(query=repo)


def get_fetch_sales_tree_detail_lines_uc(
    repo: SalesTreeRepository = Depends(get_sales_tree_repo)
) -> FetchSalesTreeDetailLinesUseCase:
    """FetchSalesTreeDetailLinesUseCase提供"""
    return FetchSalesTreeDetailLinesUseCase(query=repo)


# ========================================================================
# Calendar UseCase Providers
# ========================================================================
from app.application.usecases.calendar.get_calendar_month_uc import GetCalendarMonthUseCase
from app.infra.adapters.calendar.calendar_repository import CalendarRepository


def get_calendar_repo(db: Session = Depends(get_db)) -> CalendarRepository:
    """CalendarRepository提供"""
    return CalendarRepository(db)


def get_calendar_month_uc(
    repo: CalendarRepository = Depends(get_calendar_repo)
) -> GetCalendarMonthUseCase:
    """GetCalendarMonthUseCase提供"""
    return GetCalendarMonthUseCase(query=repo)


# ========================================================================
# Upload Status UseCase Providers
# ========================================================================
from app.application.usecases.upload.get_upload_status_uc import GetUploadStatusUseCase
from app.application.usecases.upload.get_upload_calendar_uc import GetUploadCalendarUseCase
from app.application.usecases.upload.get_upload_calendar_detail_uc import GetUploadCalendarDetailUseCase
from app.application.usecases.upload.delete_upload_scope_uc import DeleteUploadScopeUseCase
from app.infra.adapters.upload.upload_calendar_query_adapter import UploadCalendarQueryAdapter


# RawDataRepository は既に定義されているので、それを再利用
# get_raw_data_repo() は既に定義済み（上部参照）


def get_upload_calendar_query_adapter(db: Session = Depends(get_db)) -> UploadCalendarQueryAdapter:
    """UploadCalendarQueryAdapter提供"""
    return UploadCalendarQueryAdapter(db)


def get_upload_status_uc(
    repo: RawDataRepository = Depends(get_raw_data_repo)
) -> GetUploadStatusUseCase:
    """GetUploadStatusUseCase提供"""
    return GetUploadStatusUseCase(query=repo)


def get_upload_calendar_uc(
    repo: RawDataRepository = Depends(get_raw_data_repo)
) -> GetUploadCalendarUseCase:
    """GetUploadCalendarUseCase提供"""
    return GetUploadCalendarUseCase(query=repo)


def get_upload_calendar_detail_uc(
    query: UploadCalendarQueryAdapter = Depends(get_upload_calendar_query_adapter)
) -> GetUploadCalendarDetailUseCase:
    """GetUploadCalendarDetailUseCase提供"""
    return GetUploadCalendarDetailUseCase(query=query)


def get_delete_upload_scope_uc(
    repo: RawDataRepository = Depends(get_raw_data_repo)
) -> DeleteUploadScopeUseCase:
    """DeleteUploadScopeUseCase提供"""
    return DeleteUploadScopeUseCase(query=repo)


# ========================================================================
# Ingest UseCase Providers
# ========================================================================
from app.application.usecases.ingest.upload_ingest_csv_uc import UploadIngestCsvUseCase
from app.application.usecases.ingest.create_reservation_uc import CreateReservationUseCase
from app.infra.adapters.ingest.ingest_repository import IngestRepository


def get_ingest_repo(db: Session = Depends(get_db)) -> IngestRepository:
    """IngestRepository提供"""
    return IngestRepository(db)


def get_upload_ingest_csv_uc(
    repo: IngestRepository = Depends(get_ingest_repo)
) -> UploadIngestCsvUseCase:
    """UploadIngestCsvUseCase提供"""
    return UploadIngestCsvUseCase(ingest_repo=repo)


def get_create_reservation_uc(
    repo: IngestRepository = Depends(get_ingest_repo)
) -> CreateReservationUseCase:
    """CreateReservationUseCase提供"""
    return CreateReservationUseCase(ingest_repo=repo)


