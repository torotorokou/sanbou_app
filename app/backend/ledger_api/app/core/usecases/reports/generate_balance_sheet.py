"""
Generate Balance Sheet UseCase.

搬出入収支表生成のアプリケーションロジックを提供します。
factory_reportと同じClean Architectureパターンを適用。
"""

import logging
import time
from datetime import date
from io import BytesIO
from pathlib import Path
import tempfile
from typing import Any, Dict, Optional

from fastapi import UploadFile
from fastapi.responses import JSONResponse

from app.core.ports import CsvGateway, ReportRepository
from app.core.ports.report_repository import ArtifactUrls
from app.core.domain.reports.balance_sheet import BalanceSheet
from backend_shared.adapters.fastapi.error_handlers import DomainError
from backend_shared.utils.date_filter_utils import (
    filter_by_period_from_min_date as shared_filter_by_period_from_min_date,
)

# 既存のドメインロジックを再利用
from app.api.services.report.ledger.balance_sheet import process as balance_sheet_process
from app.api.services.report.utils.io import write_values_to_template
from app.api.services.report.utils.config import get_template_config
from app.api.utils.pdf_conversion import convert_excel_to_pdf

logger = logging.getLogger(__name__)


class GenerateBalanceSheetUseCase:
    """搬出入収支表生成 UseCase."""

    def __init__(
        self,
        csv_gateway: CsvGateway,
        report_repository: ReportRepository,
    ):
        self.csv_gateway = csv_gateway
        self.report_repository = report_repository

    def execute(
        self,
        shipment: Optional[UploadFile] = None,
        yard: Optional[UploadFile] = None,
        receive: Optional[UploadFile] = None,
        period_type: Optional[str] = None,
    ) -> JSONResponse:
        """
        搬出入収支表を生成する。
        
        Args:
            shipment: 出荷データCSV
            yard: ヤードデータCSV
            receive: 受入データCSV
            period_type: 期間フィルタ ("oneday" | "oneweek" | "onemonth")
            
        Returns:
            JSONResponse: 署名付きURLを含むレスポンス
        """
        try:
            # Step 1: CSV読み込み
            print("[UseCase] Step 1: CSV読み込み")
            files = {
                k: v
                for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items()
                if v is not None
            }
            dfs = self.csv_gateway.read_csv_files(files)

            # Step 2: 期間フィルタ（オプション）
            if period_type:
                print(f"[UseCase] Step 2: 期間フィルタ適用 - {period_type}")
                try:
                    dfs = shared_filter_by_period_from_min_date(dfs, period_type)
                except Exception as e:
                    print(f"[UseCase] 期間フィルタスキップ: {e}")

            # Step 3: 整形
            print("[UseCase] Step 3: CSV整形")
            df_formatted = self.csv_gateway.format_csv_data(dfs)

            # Step 4: ドメインモデル生成
            print("[UseCase] Step 4: ドメインモデル生成")
            balance_sheet = BalanceSheet.from_dataframes(
                df_receive=df_formatted.get("receive"),
                df_shipment=df_formatted.get("shipment"),
                df_yard=df_formatted.get("yard"),
            )
            print(f"[UseCase] 受入データ件数: {len(balance_sheet.receive_items)}")
            print(f"[UseCase] 出荷データ件数: {len(balance_sheet.shipment_items)}")
            print(f"[UseCase] ヤードデータ件数: {len(balance_sheet.yard_items)}")
            print(f"[UseCase] レポート日付: {balance_sheet.report_date}")

            # Step 5: ドメインロジック実行（既存process関数）
            print("[UseCase] Step 5: ドメインロジック実行")
            result_df = balance_sheet_process(df_formatted)

            # Step 6: Excel生成
            print("[UseCase] Step 6: Excel生成")
            excel_bytes = self._generate_excel(result_df, balance_sheet.report_date)

            # Step 7: PDF生成
            print("[UseCase] Step 7: PDF生成")
            pdf_bytes = self._generate_pdf(excel_bytes)

            # Step 8: 保存とURL生成
            print("[UseCase] Step 8: 保存とURL生成")
            artifact_urls = self.report_repository.save_report(
                report_key="balance_sheet",
                report_date=balance_sheet.report_date,
                excel_bytes=excel_bytes,
                pdf_bytes=pdf_bytes,
            )

            # Step 9: レスポンス返却
            print(f"[UseCase] Step 9: 完了 - URLs: {artifact_urls.to_dict()}")
            return JSONResponse(
                status_code=200,
                content={
                    "message": "搬出入収支表の生成が完了しました",
                    "report_date": balance_sheet.report_date.isoformat(),
                    **artifact_urls.to_dict(),
                },
            )

        except DomainError:
            raise
        except Exception as ex:
            print(f"[UseCase] 予期しないエラー: {ex}")
            import traceback
            traceback.print_exc()
            raise DomainError(
                code="INTERNAL_ERROR",
                status=500,
                user_message="搬出入収支表の生成中に予期しないエラーが発生しました",
                title="内部エラー",
            ) from ex

    def _generate_excel(self, result_df, report_date: date) -> BytesIO:
        """Excel生成"""
        template_config = get_template_config()["balance_sheet"]
        template_path = template_config["template_path"]
        extracted_date = report_date.strftime("%Y年%m月%d日")
        
        excel_bytes = write_values_to_template(
            df=result_df,
            template_path=template_path,
            extracted_date=extracted_date,
        )
        return excel_bytes

    def _generate_pdf(self, excel_bytes: BytesIO) -> BytesIO:
        """PDF生成"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_excel:
            tmp_excel.write(excel_bytes.getvalue())
            tmp_excel_path = Path(tmp_excel.name)

        try:
            pdf_bytes_raw = convert_excel_to_pdf(tmp_excel_path)
            pdf_bytes = BytesIO(pdf_bytes_raw)
            return pdf_bytes
        finally:
            if tmp_excel_path.exists():
                tmp_excel_path.unlink()
