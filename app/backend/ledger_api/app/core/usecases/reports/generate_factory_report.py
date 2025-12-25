"""
Generate Factory Report UseCase.

工場日報生成のアプリケーションロジックを提供します。

🔄 リファクタリング: Excel同期 + PDF非同期の2段階構成に対応
"""

from datetime import date
from io import BytesIO
from typing import Any

from app.application.usecases.reports.report_generation_utils import (
    generate_excel_from_dataframe,
)
from app.core.domain.reports.factory_report import FactoryReport
from app.core.usecases.reports.base_report_usecase import BaseReportUseCase
from app.core.usecases.reports.factory_report_processor import (
    process as factory_report_process,
)
from fastapi import BackgroundTasks, UploadFile
from fastapi.responses import JSONResponse


class GenerateFactoryReportUseCase(BaseReportUseCase):
    """工場日報生成 UseCase."""

    @property
    def report_key(self) -> str:
        return "factory_report"

    @property
    def report_name(self) -> str:
        return "工場日報"

    def execute(  # type: ignore[override]
        self,
        files: dict[str, UploadFile],
        period_type: str | None = None,
        background_tasks: BackgroundTasks | None = None,
        async_pdf: bool = True,
    ) -> JSONResponse:
        """
        工場日報生成の実行（filesパラメータを受け取る独自実装）。

        Args:
            files: アップロードされたCSVファイル辞書
            period_type: 期間指定
            background_tasks: FastAPIのBackgroundTasks（PDF非同期生成用）
            async_pdf: True=PDF非同期生成（デフォルト）, False=同期生成（従来互換）

        Returns:
            JSONResponse: 署名付きURLを含むレスポンス
        """
        # files辞書から個別のファイルを取り出してベースクラスのexecuteを呼び出す
        return super().execute(
            shipment=files.get("shipment"),
            yard=files.get("yard"),
            receive=files.get("receive"),
            period_type=period_type,
            background_tasks=background_tasks,
            async_pdf=async_pdf,
        )

    def create_domain_model(self, df_formatted: dict[str, Any]) -> FactoryReport:
        """ドメインモデル生成（Step 4）"""
        return FactoryReport.from_dataframes(
            df_shipment=df_formatted.get("shipment"),
            df_yard=df_formatted.get("yard"),
        )

    def execute_domain_logic(self, df_formatted: dict[str, Any]) -> Any:
        """ドメインロジック実行（Step 5）"""
        return factory_report_process(df_formatted)

    def generate_excel(self, result_df: Any, report_date: date) -> BytesIO:
        """Excel生成（Step 6）"""
        return generate_excel_from_dataframe(
            result_df=result_df,
            report_key=self.report_key,
            report_date=report_date,
        )
