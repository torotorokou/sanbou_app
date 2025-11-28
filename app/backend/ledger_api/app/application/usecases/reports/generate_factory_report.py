"""
Generate Factory Report UseCase.

工場日報生成のアプリケーションロジックを提供します。

👶 UseCase の責務:
1. CSV 読み込み（Port 経由）
2. ドメインモデル（FactoryReport Entity）の生成
3. ドメインロジック呼び出し（既存の services/report/ledger/factory_report.process）
4. Excel/PDF 生成
5. 保存と署名付き URL 返却（Port 経由）

外部依存（pandas, ファイルシステム等）は Port を通して抽象化されています。
DataFrame依存はドメイン層で緩和し、将来的な置き換えを容易にします。
"""

import logging
import time
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
import tempfile
from typing import Any, Dict, Optional

from fastapi import UploadFile
from fastapi.responses import JSONResponse

from app.core.ports.inbound import CsvGateway, ReportRepository
from app.core.ports.inbound.report_repository import ArtifactUrls
from app.core.domain.reports.factory_report import FactoryReport
from backend_shared.infra.adapters.fastapi.error_handlers import DomainError
from backend_shared.utils.date_filter_utils import (
    filter_by_period_from_min_date as shared_filter_by_period_from_min_date,
)

# 既存のドメインロジックを再利用（将来的には Entity に移行）
from app.application.usecases.reports.factory_report import process as factory_report_process
from app.infra.report_utils import write_values_to_template, get_template_config
from app.infra.utils.pdf_conversion import convert_excel_to_pdf

logger = logging.getLogger(__name__)


class GenerateFactoryReportUseCase:
    """工場日報生成 UseCase."""

    def __init__(
        self,
        csv_gateway: CsvGateway,
        report_repository: ReportRepository,
    ):
        """
        UseCase の初期化.

        Args:
            csv_gateway: CSV 読み込み・検証・整形の抽象インターフェース
            report_repository: レポート保存の抽象インターフェース

        👶 依存性注入（DI）により、テスト時はモック実装を渡せます。
        """
        self.csv_gateway = csv_gateway
        self.report_repository = report_repository

    def execute(
        self,
        files: Dict[str, UploadFile],
        period_type: Optional[str] = None,
    ) -> JSONResponse:
        """
        工場日報生成の実行.

        Args:
            files: アップロードされた CSV ファイル（shipment, yard, receive 等）
            period_type: 期間指定（"oneday" | "oneweek" | "onemonth"）

        Returns:
            JSONResponse: 署名付き URL を含むレスポンス

        Raises:
            DomainError: ビジネスルール違反や処理失敗時
        """
        start_time = time.time()
        file_keys = list(files.keys())
        
        logger.info(
            "工場日報生成開始",
            extra={
                "usecase": "GenerateFactoryReportUseCase",
                "file_keys": file_keys,
                "period_type": period_type,
            },
        )

        try:
            # Step 1: CSV 読み込み（Port 経由）
            step_start = time.time()
            logger.debug("Step 1: CSV読み込み開始", extra={"file_keys": file_keys})
            
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

            # Step 2: 検証（Port 経由）
            step_start = time.time()
            logger.debug("Step 2: CSV検証開始")
            
            validation_error = self.csv_gateway.validate_csv_structure(dfs, files)
            if validation_error:
                logger.warning("Step 2: CSV検証エラー")
                return validation_error.to_json_response()
            
            logger.debug(
                "Step 2: CSV検証完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )

            # Step 2.5: 期間フィルタ適用（オプション）
            if period_type:
                step_start = time.time()
                logger.debug(
                    "Step 2.5: 期間フィルタ適用開始",
                    extra={"period_type": period_type},
                )
                try:
                    dfs = shared_filter_by_period_from_min_date(dfs, period_type)
                    logger.debug(
                        "Step 2.5: 期間フィルタ完了",
                        extra={
                            "period_type": period_type,
                            "elapsed_seconds": round(time.time() - step_start, 3),
                        },
                    )
                except Exception as e:
                    logger.warning(
                        "Step 2.5: 期間フィルタスキップ（エラー）",
                        extra={"exception": str(e)},
                    )

            # Step 3: 整形（Port 経由）
            step_start = time.time()
            logger.debug("Step 3: CSV整形開始")
            
            try:
                df_formatted = self.csv_gateway.format_csv_data(dfs)
                logger.debug(
                    "Step 3: CSV整形完了",
                    extra={"elapsed_seconds": round(time.time() - step_start, 3)},
                )
            except DomainError:
                raise
            except Exception as ex:
                logger.error(
                    "Step 3: CSV整形エラー",
                    extra={"exception": str(ex)},
                    exc_info=True,
                )
                raise DomainError(
                    code="REPORT_FORMAT_ERROR",
                    status=500,
                    user_message=f"帳票データの整形中にエラーが発生しました: {str(ex)}",
                    title="データ整形エラー",
                ) from ex

            # Step 4: ドメインモデル生成
            step_start = time.time()
            logger.debug("Step 4: ドメインモデル生成開始")
            
            try:
                factory_report = FactoryReport.from_dataframes(
                    df_shipment=df_formatted.get("shipment"),
                    df_yard=df_formatted.get("yard"),
                )
                logger.info(
                    "Step 4: ドメインモデル生成完了",
                    extra={
                        "shipment_count": len(factory_report.shipment_items),
                        "yard_count": len(factory_report.yard_items),
                        "report_date": factory_report.report_date.isoformat(),
                        "elapsed_seconds": round(time.time() - step_start, 3),
                    },
                )
            except Exception as ex:
                logger.error(
                    "Step 4: ドメインモデル生成エラー",
                    extra={"exception": str(ex)},
                    exc_info=True,
                )
                raise DomainError(
                    code="DOMAIN_MODEL_ERROR",
                    status=500,
                    user_message=f"ドメインモデルの生成中にエラーが発生しました: {str(ex)}",
                    title="ドメインモデルエラー",
                ) from ex

            # Step 5: ドメインロジック実行（既存の process 関数を利用）
            # 注: 現時点では既存のDataFrame処理を維持し、段階的に移行
            step_start = time.time()
            logger.debug("Step 5: ドメインロジック実行開始")
            
            try:
                result_df = factory_report_process(df_formatted)
                logger.debug(
                    "Step 5: ドメインロジック実行完了",
                    extra={"elapsed_seconds": round(time.time() - step_start, 3)},
                )
            except Exception as ex:
                logger.error(
                    "Step 5: ドメインロジックエラー",
                    extra={"exception": str(ex)},
                    exc_info=True,
                )
                raise DomainError(
                    code="REPORT_GENERATION_ERROR",
                    status=500,
                    user_message=f"工場日報の生成中にエラーが発生しました: {str(ex)}",
                    title="レポート生成エラー",
                ) from ex

            # Step 6: Excel 生成
            step_start = time.time()
            logger.debug("Step 6: Excel生成開始")
            excel_bytes = self._generate_excel(result_df, factory_report.report_date)
            logger.debug(
                "Step 6: Excel生成完了",
                extra={
                    "size_bytes": len(excel_bytes.getvalue()),
                    "elapsed_seconds": round(time.time() - step_start, 3),
                },
            )

            # Step 7: PDF 生成
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
                report_key="factory_report",
                report_date=factory_report.report_date,
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
                "工場日報生成完了",
                extra={
                    "usecase": "GenerateFactoryReportUseCase",
                    "report_date": factory_report.report_date.isoformat(),
                    "total_elapsed_seconds": round(total_elapsed, 3),
                },
            )
            
            # BFF互換のレスポンス形式に変換
            artifact_dict = artifact_urls.to_dict()
            return JSONResponse(
                status_code=200,
                content={
                    "message": "工場日報の生成が完了しました",
                    "report_date": factory_report.report_date.isoformat(),
                    "artifact": {
                        "excel_download_url": artifact_dict["excel_url"],
                        "pdf_preview_url": artifact_dict["pdf_url"],
                    },
                },
            )

        except DomainError:
            # DomainError はそのまま再 raise
            raise
        except Exception as ex:
            total_elapsed = time.time() - start_time
            logger.exception(
                "工場日報生成中に予期しないエラー",
                extra={
                    "usecase": "GenerateFactoryReportUseCase",
                    "total_elapsed_seconds": round(total_elapsed, 3),
                    "exception_type": type(ex).__name__,
                    "exception_message": str(ex),
                },
            )
            raise DomainError(
                code="INTERNAL_ERROR",
                status=500,
                user_message="工場日報の生成中に予期しないエラーが発生しました",
                title="内部エラー",
            ) from ex

    def _extract_report_date(self, df_formatted: Dict[str, Any]) -> date:
        """
        整形後データからレポート日付を抽出.

        複数の候補列から最初に見つかった有効な日付を使用します。
        見つからない場合は今日の日付にフォールバックします。
        """
        if not df_formatted:
            return datetime.now().date()

        date_candidates = ["伝票日付", "日付", "date", "Date"]

        for df in df_formatted.values():
            if not hasattr(df, "columns") or df.empty:
                continue

            for col in date_candidates:
                if col not in df.columns:
                    continue

                first_value = df[col].iloc[0]
                if isinstance(first_value, str):
                    try:
                        from datetime import datetime as dt
                        return dt.strptime(first_value, "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        continue
                elif hasattr(first_value, "date"):
                    return first_value.date()

        # フォールバック: 今日の日付
        return datetime.now().date()

    def _generate_excel(self, result_df: Any, report_date: date) -> BytesIO:
        """
        DataFrame から Excel バイトストリームを生成.

        既存の write_values_to_template を利用します。
        """
        template_key = "factory_report"
        template_config = get_template_config()[template_key]
        template_path = template_config["template_excel_path"]
        
        # 日付文字列を生成（シート名用）
        extracted_date = report_date.strftime("%Y年%m月%d日")

        excel_bytes = write_values_to_template(
            df=result_df,
            template_path=template_path,
            extracted_date=extracted_date,
        )

        return excel_bytes

    def _generate_pdf(self, excel_bytes: BytesIO) -> BytesIO:
        """
        Excel バイトストリームから PDF を生成.

        既存の convert_excel_to_pdf を利用します（一時ファイル経由）。
        """
        # 一時ファイルに Excel を書き出し
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_excel:
            tmp_excel.write(excel_bytes.getvalue())
            tmp_excel_path = Path(tmp_excel.name)

        try:
            # PDF に変換
            pdf_bytes_raw = convert_excel_to_pdf(tmp_excel_path)
            
            # BytesIO にラップして返却
            pdf_bytes = BytesIO(pdf_bytes_raw)
            return pdf_bytes
        finally:
            # 一時ファイルを削除
            if tmp_excel_path.exists():
                tmp_excel_path.unlink()
