"""
Generate Average Sheet UseCase.

単価平均表生成のアプリケーションロジック。
"""
from datetime import date
from io import BytesIO
from pathlib import Path
import tempfile
from typing import Optional

from fastapi import UploadFile
from fastapi.responses import JSONResponse

from app.core.ports import CsvGateway, ReportRepository
from app.core.domain.reports.average_sheet import AverageSheet
from backend_shared.adapters.fastapi.error_handlers import DomainError
from backend_shared.utils.date_filter_utils import filter_by_period_from_min_date as shared_filter_by_period_from_min_date

from app.api.services.report.ledger.average_sheet import process as average_sheet_process
from app.api.services.report.utils.io import write_values_to_template
from app.api.services.report.utils.config import get_template_config
from app.api.utils.pdf_conversion import convert_excel_to_pdf

logger = logging.getLogger(__name__)


class GenerateAverageSheetUseCase:
    """単価平均表生成 UseCase."""

    def __init__(self, csv_gateway: CsvGateway, report_repository: ReportRepository):
        self.csv_gateway = csv_gateway
        self.report_repository = report_repository

    async def execute(
        self,
        shipment: Optional[UploadFile] = None,
        yard: Optional[UploadFile] = None,
        receive: Optional[UploadFile] = None,
        period_type: Optional[str] = None,
    ) -> JSONResponse:
        try:
            print("[UseCase] Step 1: CSV読み込み")
            files = {k: v for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items() if v is not None}
            dfs = await self.csv_gateway.read_csv_files(files)

            if period_type:
                print(f"[UseCase] Step 2: 期間フィルタ - {period_type}")
                try:
                    dfs = shared_filter_by_period_from_min_date(dfs, period_type)
                except Exception as e:
                    print(f"[UseCase] 期間フィルタスキップ: {e}")

            print("[UseCase] Step 3: CSV整形")
            df_formatted = self.csv_gateway.format_csv_data(dfs)

            print("[UseCase] Step 4: ドメインモデル生成")
            average_sheet = AverageSheet.from_dataframes(
                df_shipment=df_formatted.get("shipment"),
                df_yard=df_formatted.get("yard"),
                df_receive=df_formatted.get("receive"),
            )
            print(f"[UseCase] データ件数: 出荷{len(average_sheet.shipment_items)} ヤード{len(average_sheet.yard_items)} 受入{len(average_sheet.receive_items)}")

            print("[UseCase] Step 5: ドメインロジック実行")
            result_df = average_sheet_process(df_formatted)

            print("[UseCase] Step 6: Excel生成")
            excel_bytes = self._generate_excel(result_df, average_sheet.report_date)

            print("[UseCase] Step 7: PDF生成")
            pdf_bytes = self._generate_pdf(excel_bytes)

            print("[UseCase] Step 8: 保存とURL生成")
            artifact_urls = self.report_repository.save_report(
                report_key="average_sheet",
                report_date=average_sheet.report_date,
                excel_bytes=excel_bytes,
                pdf_bytes=pdf_bytes,
            )

            print(f"[UseCase] Step 9: 完了")
            return JSONResponse(
                status_code=200,
                content={
                    "message": "単価平均表の生成が完了しました",
                    "report_date": average_sheet.report_date.isoformat(),
                    **artifact_urls.to_dict(),
                },
            )
        except DomainError:
            raise
        except Exception as ex:
            print(f"[UseCase] エラー: {ex}")
            import traceback
            traceback.print_exc()
            raise DomainError(
                code="INTERNAL_ERROR",
                status=500,
                user_message="単価平均表の生成中に予期しないエラーが発生しました",
                title="内部エラー",
            ) from ex

    def _generate_excel(self, result_df, report_date: date) -> bytes:
        template_config = get_template_config()["average_sheet"]
        template_path = Path(template_config["template_path"])
        excel_buffer = BytesIO()
        write_values_to_template(template_path=template_path, result_df=result_df, target_date=report_date, output=excel_buffer)
        excel_buffer.seek(0)
        return excel_buffer.read()

    def _generate_pdf(self, excel_bytes: bytes) -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(excel_bytes)
            tmp_path = Path(tmp.name)
        try:
            pdf_buffer = BytesIO()
            convert_excel_to_pdf(tmp_path, pdf_buffer)
            pdf_buffer.seek(0)
            return pdf_buffer.read()
        finally:
            tmp_path.unlink(missing_ok=True)
