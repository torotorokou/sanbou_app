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

from app.application.ports import CsvGateway, ReportRepository
from app.application.ports.report_repository import ArtifactUrls
from app.application.domain.reports.balance_sheet import BalanceSheet
from backend_shared.infra.adapters.fastapi.error_handlers import DomainError
from backend_shared.utils.date_filter_utils import (
    filter_by_period_from_min_date as shared_filter_by_period_from_min_date,
)

# 既存のドメインロジックを再利用
from app.application.usecases.reports.balance_sheet import process as balance_sheet_process
from app.infra.report_utils import write_values_to_template, get_template_config
from app.infra.utils.pdf_conversion import convert_excel_to_pdf

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
        start_time = time.time()
        file_keys = [k for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items() if v is not None]
        
        logger.info(
            "搬出入収支表生成開始",
            extra={
                "usecase": "balance_sheet",
                "file_keys": file_keys,
                "period_type": period_type,
            },
        )
        
        try:
            # Step 1: CSV読み込み (Port 経由)
            step_start = time.time()
            logger.debug("Step 1: CSV読み込み開始")
            
            files = {k: v for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items() if v is not None}
            dfs, error = self.csv_gateway.read_csv_files(files)
            if error:
                logger.warning(
                    "Step 1: CSV読み込みエラー",
                    extra={"error_type": type(error).__name__},
                )
                return error.to_json_response()
            
            assert dfs is not None
            logger.debug(
                "Step 1: CSV読み込み完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )

            # Step 2: 期間フィルタ（オプション）
            if period_type:
                step_start = time.time()
                logger.debug(f"Step 2: 期間フィルタ適用開始", extra={"period_type": period_type})
                
                try:
                    dfs = shared_filter_by_period_from_min_date(dfs, period_type)
                    logger.debug(
                        "Step 2: 期間フィルタ適用完了",
                        extra={
                            "period_type": period_type,
                            "elapsed_seconds": round(time.time() - step_start, 3),
                        },
                    )
                except Exception as e:
                    logger.warning("Step 2: 期間フィルタスキップ（エラー）", extra={"exception": str(e)})

            # Step 3: 整形（Port 経由）
            step_start = time.time()
            logger.debug("Step 3: CSV整形開始")
            
            df_formatted = self.csv_gateway.format_csv_data(dfs)
            logger.debug(
                "Step 3: CSV整形完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )

            # Step 4: ドメインモデル生成
            step_start = time.time()
            logger.debug("Step 4: ドメインモデル生成開始")
            
            balance_sheet = BalanceSheet.from_dataframes(
                df_receive=df_formatted.get("receive"),
                df_shipment=df_formatted.get("shipment"),
                df_yard=df_formatted.get("yard"),
            )
            
            logger.debug(
                "Step 4: ドメインモデル生成完了",
                extra={
                    "receive_count": len(balance_sheet.receive_items),
                    "shipment_count": len(balance_sheet.shipment_items),
                    "yard_count": len(balance_sheet.yard_items),
                    "report_date": balance_sheet.report_date.isoformat(),
                    "elapsed_seconds": round(time.time() - step_start, 3),
                },
            )

            # Step 5: ドメインロジック実行（既存process関数）
            step_start = time.time()
            logger.debug("Step 5: ドメインロジック実行開始")
            
            result_df = balance_sheet_process(df_formatted)
            logger.debug(
                "Step 5: ドメインロジック実行完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )

            # Step 6: Excel生成
            step_start = time.time()
            logger.debug("Step 6: Excel生成開始")
            
            excel_bytes = self._generate_excel(result_df, balance_sheet.report_date)
            logger.debug(
                "Step 6: Excel生成完了",
                extra={
                    "size_bytes": len(excel_bytes.getvalue()),
                    "elapsed_seconds": round(time.time() - step_start, 3),
                },
            )

            # Step 7: PDF生成
            step_start = time.time()
            logger.debug("Step 7: PDF生成開始")
            
            pdf_bytes = self._generate_pdf(excel_bytes)
            logger.debug(
                "Step 7: PDF生成完了",
                extra={
                    "size_bytes": len(pdf_bytes.getvalue()),
                    "elapsed_seconds": round(time.time() - step_start, 3),
                },
            )

            # Step 8: 保存と署名付き URL 生成（Port 経由）
            step_start = time.time()
            logger.debug("Step 8: 保存とURL生成開始")
            
            artifact_urls = self.report_repository.save_report(
                report_key="balance_sheet",
                report_date=balance_sheet.report_date,
                excel_bytes=excel_bytes,
                pdf_bytes=pdf_bytes,
            )
            logger.debug(
                "Step 8: 保存とURL生成完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )

            # Step 9: レスポンス返却
            total_elapsed = time.time() - start_time
            logger.info(
                "搬出入収支表生成完了",
                extra={
                    "usecase": "balance_sheet",
                    "report_date": balance_sheet.report_date.isoformat(),
                    "total_elapsed_seconds": round(total_elapsed, 3),
                },
            )
            
            # BFF互換のレスポンス形式に変換
            artifact_dict = artifact_urls.to_dict()
            return JSONResponse(
                status_code=200,
                content={
                    "message": "搬出入収支表の生成が完了しました",
                    "report_date": balance_sheet.report_date.isoformat(),
                    "artifact": {
                        "excel_download_url": artifact_dict["excel_url"],
                        "pdf_preview_url": artifact_dict["pdf_url"],
                    },
                },
            )

        except DomainError:
            raise
        except Exception as ex:
            logger.exception(
                "搬出入収支表生成失敗",
                extra={
                    "usecase": "balance_sheet",
                    "error": str(ex),
                    "elapsed_seconds": round(time.time() - start_time, 3),
                },
                exc_info=True,
            )
            raise DomainError(
                code="INTERNAL_ERROR",
                status=500,
                user_message="搬出入収支表の生成中に予期しないエラーが発生しました",
                title="内部エラー",
            ) from ex

    def _generate_excel(self, result_df, report_date: date) -> BytesIO:
        """Excel生成"""
        template_config = get_template_config()["balance_sheet"]
        template_path = template_config["template_excel_path"]
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
