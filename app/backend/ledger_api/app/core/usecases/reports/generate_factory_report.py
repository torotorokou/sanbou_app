"""
Generate Factory Report UseCase.

工場日報生成のアプリケーションロジックを提供します。
"""

from datetime import date
from io import BytesIO
from typing import Any, Dict, Optional

from fastapi import UploadFile
from fastapi.responses import JSONResponse

from app.core.ports.inbound import CsvGateway, ReportRepository
from app.core.domain.reports.factory_report import FactoryReport
from app.core.usecases.reports.base_report_usecase import BaseReportUseCase
from app.core.usecases.reports.factory_report import process as factory_report_process
from app.application.usecases.reports.report_generation_utils import (
    generate_excel_from_dataframe,
)


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
        files: Dict[str, UploadFile],
        period_type: Optional[str] = None,
    ) -> JSONResponse:
        """
        工場日報生成の実行（filesパラメータを受け取る独自実装）。
        
        Args:
            files: アップロードされたCSVファイル辞書
            period_type: 期間指定
            
        Returns:
            JSONResponse: 署名付きURLを含むレスポンス
        """
        # files辞書から個別のファイルを取り出してベースクラスのexecuteを呼び出す
        return super().execute(
            shipment=files.get("shipment"),
            yard=files.get("yard"),
            receive=files.get("receive"),
            period_type=period_type,
        )

    def create_domain_model(self, df_formatted: Dict[str, Any]) -> FactoryReport:
        """ドメインモデル生成（Step 4）"""
        return FactoryReport.from_dataframes(
            df_shipment=df_formatted.get("shipment"),
            df_yard=df_formatted.get("yard"),
        )

    def execute_domain_logic(self, df_formatted: Dict[str, Any]) -> Any:
        """ドメインロジック実行（Step 5）"""
        return factory_report_process(df_formatted)

    def generate_excel(self, result_df: Any, report_date: date) -> BytesIO:
        """Excel生成（Step 6）"""
        return generate_excel_from_dataframe(
            result_df=result_df,
            report_key=self.report_key,
            report_date=report_date,
        )


