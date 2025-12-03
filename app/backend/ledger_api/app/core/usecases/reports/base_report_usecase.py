"""
Base Report UseCase.

全レポート生成UseCaseの共通処理を提供する基底クラス。
各レポート固有のロジックは抽象メソッドとして定義し、サブクラスで実装する。
"""

import time
from abc import ABC, abstractmethod
from datetime import date
from io import BytesIO
from typing import Any, Dict, Optional

from fastapi import UploadFile
from fastapi.responses import JSONResponse

from app.core.ports.inbound import CsvGateway, ReportRepository
from backend_shared.infra.adapters.fastapi.error_handlers import DomainError
from backend_shared.application.logging import get_module_logger
from backend_shared.utils.date_filter_utils import (
    filter_by_period_from_max_date as shared_filter_by_period_from_max_date,
)
from app.application.usecases.reports.report_generation_utils import (
    generate_pdf_from_excel,
)

logger = get_module_logger(__name__)


class BaseReportUseCase(ABC):
    """
    レポート生成UseCaseの基底クラス。
    
    共通処理（CSV読み込み、整形、PDF生成、保存等）を実装し、
    レポート固有の処理は抽象メソッドとしてサブクラスに委譲する。
    """

    def __init__(
        self,
        csv_gateway: CsvGateway,
        report_repository: ReportRepository,
    ):
        """
        基底UseCaseの初期化。
        
        Args:
            csv_gateway: CSV読み込み・検証・整形の抽象インターフェース
            report_repository: レポート保存の抽象インターフェース
        """
        self.csv_gateway = csv_gateway
        self.report_repository = report_repository

    @property
    @abstractmethod
    def report_key(self) -> str:
        """レポートキー（例: "average_sheet"）"""
        pass

    @property
    @abstractmethod
    def report_name(self) -> str:
        """レポート名（例: "単価平均表"）"""
        pass

    @abstractmethod
    def create_domain_model(self, df_formatted: Dict[str, Any]) -> Any:
        """
        ドメインモデルを生成する（Step 4）。
        
        Args:
            df_formatted: 整形済みDataFrame辞書
            
        Returns:
            ドメインモデルインスタンス（report_dateプロパティを持つ）
        """
        pass

    @abstractmethod
    def execute_domain_logic(self, df_formatted: Dict[str, Any]) -> Any:
        """
        ドメインロジックを実行する（Step 5）。
        
        Args:
            df_formatted: 整形済みDataFrame辞書
            
        Returns:
            処理結果DataFrame
        """
        pass

    @abstractmethod
    def generate_excel(self, result_df: Any, report_date: date) -> BytesIO:
        """
        Excelを生成する（Step 6）。
        
        Args:
            result_df: 処理結果DataFrame
            report_date: レポート日付
            
        Returns:
            Excelバイナリストリーム
        """
        pass

    def execute(
        self,
        shipment: Optional[UploadFile] = None,
        yard: Optional[UploadFile] = None,
        receive: Optional[UploadFile] = None,
        period_type: Optional[str] = None,
    ) -> JSONResponse:
        """
        レポート生成の共通実行フロー。
        
        Args:
            shipment: 出荷データCSVファイル
            yard: ヤードデータCSVファイル
            receive: 受入データCSVファイル
            period_type: 期間フィルタ ("oneday" | "oneweek" | "onemonth")
            
        Returns:
            JSONResponse: 署名付きURLを含むレスポンス
        """
        start_time = time.time()
        file_keys = [
            k for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items() 
            if v is not None
        ]
        
        logger.info(
            f"{self.report_name}生成開始",
            extra={
                "usecase": self.report_key,
                "file_keys": file_keys,
                "period_type": period_type,
            },
        )
        
        try:
            # Step 1: CSV読み込み
            dfs = self._read_csv_files(shipment, yard, receive)
            
            # Step 2: 期間フィルタ（オプション）
            if period_type:
                dfs = self._apply_period_filter(dfs, period_type)
            
            # Step 3: CSV整形
            df_formatted = self._format_csv_data(dfs)
            
            # Step 4: ドメインモデル生成（サブクラス実装）
            domain_model = self._create_domain_model_with_logging(df_formatted)
            
            # Step 5: ドメインロジック実行（サブクラス実装）
            result_df = self._execute_domain_logic_with_logging(df_formatted)
            
            # Step 6: Excel生成（サブクラス実装）
            excel_bytes = self._generate_excel_with_logging(result_df, domain_model.report_date)
            
            # Step 7: PDF生成
            pdf_bytes = self._generate_pdf_with_logging(excel_bytes)
            
            # Step 8: 保存とURL生成
            artifact_urls = self._save_report_with_logging(
                domain_model.report_date,
                excel_bytes,
                pdf_bytes,
            )
            
            # Step 9: レスポンス返却
            return self._create_response(artifact_urls, domain_model.report_date, start_time)
            
        except DomainError:
            raise
        except Exception as ex:
            logger.exception(
                f"{self.report_name}生成失敗",
                extra={
                    "usecase": self.report_key,
                    "error": str(ex),
                    "elapsed_seconds": round(time.time() - start_time, 3),
                },
                exc_info=True,
            )
            raise DomainError(
                code="INTERNAL_ERROR",
                status=500,
                user_message=f"{self.report_name}の生成中に予期しないエラーが発生しました",
                title="内部エラー",
            ) from ex

    def _read_csv_files(
        self,
        shipment: Optional[UploadFile],
        yard: Optional[UploadFile],
        receive: Optional[UploadFile],
    ) -> Dict[str, Any]:
        """Step 1: CSV読み込み"""
        step_start = time.time()
        logger.debug("Step 1: CSV読み込み開始")
        
        files = {
            k: v
            for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items()
            if v is not None
        }
        
        dfs, error = self.csv_gateway.read_csv_files(files)
        if error:
            logger.warning(
                "Step 1: CSV読み込みエラー",
                extra={"error_type": type(error).__name__},
            )
            raise error
        
        assert dfs is not None
        logger.debug(
            "Step 1: CSV読み込み完了",
            extra={"elapsed_seconds": round(time.time() - step_start, 3)},
        )
        return dfs

    def _apply_period_filter(
        self,
        dfs: Dict[str, Any],
        period_type: str,
    ) -> Dict[str, Any]:
        """Step 2: 期間フィルタ適用"""
        step_start = time.time()
        logger.debug(
            "Step 2: 期間フィルタ適用開始",
            extra={"period_type": period_type},
        )
        
        try:
            filtered_dfs = shared_filter_by_period_from_max_date(dfs, period_type)
            logger.debug(
                "Step 2: 期間フィルタ適用完了",
                extra={
                    "period_type": period_type,
                    "elapsed_seconds": round(time.time() - step_start, 3),
                },
            )
            return filtered_dfs
        except Exception as e:
            logger.warning(
                "Step 2: 期間フィルタスキップ（エラー）",
                extra={"exception": str(e)},
            )
            return dfs

    def _format_csv_data(self, dfs: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: CSV整形"""
        step_start = time.time()
        logger.debug("Step 3: CSV整形開始")
        
        df_formatted = self.csv_gateway.format_csv_data(dfs)
        logger.debug(
            "Step 3: CSV整形完了",
            extra={"elapsed_seconds": round(time.time() - step_start, 3)},
        )
        return df_formatted

    def _create_domain_model_with_logging(self, df_formatted: Dict[str, Any]) -> Any:
        """Step 4: ドメインモデル生成（ログ付き）"""
        step_start = time.time()
        logger.debug("Step 4: ドメインモデル生成開始")
        
        domain_model = self.create_domain_model(df_formatted)
        
        logger.debug(
            "Step 4: ドメインモデル生成完了",
            extra={
                "report_date": domain_model.report_date.isoformat(),
                "elapsed_seconds": round(time.time() - step_start, 3),
            },
        )
        return domain_model

    def _execute_domain_logic_with_logging(self, df_formatted: Dict[str, Any]) -> Any:
        """Step 5: ドメインロジック実行（ログ付き）"""
        step_start = time.time()
        logger.debug("Step 5: ドメインロジック実行開始")
        
        result_df = self.execute_domain_logic(df_formatted)
        
        logger.debug(
            "Step 5: ドメインロジック実行完了",
            extra={"elapsed_seconds": round(time.time() - step_start, 3)},
        )
        return result_df

    def _generate_excel_with_logging(self, result_df: Any, report_date: date) -> BytesIO:
        """Step 6: Excel生成（ログ付き）"""
        step_start = time.time()
        logger.debug("Step 6: Excel生成開始")
        
        excel_bytes = self.generate_excel(result_df, report_date)
        
        logger.debug(
            "Step 6: Excel生成完了",
            extra={
                "size_bytes": len(excel_bytes.getvalue()),
                "elapsed_seconds": round(time.time() - step_start, 3),
            },
        )
        return excel_bytes

    def _generate_pdf_with_logging(self, excel_bytes: BytesIO) -> BytesIO:
        """Step 7: PDF生成"""
        step_start = time.time()
        logger.debug("Step 7: PDF生成開始")
        
        pdf_bytes = generate_pdf_from_excel(excel_bytes)
        
        logger.debug(
            "Step 7: PDF生成完了",
            extra={
                "size_bytes": len(pdf_bytes.getvalue()),
                "elapsed_seconds": round(time.time() - step_start, 3),
            },
        )
        return pdf_bytes

    def _save_report_with_logging(
        self,
        report_date: date,
        excel_bytes: BytesIO,
        pdf_bytes: BytesIO,
    ):
        """Step 8: 保存とURL生成"""
        step_start = time.time()
        logger.debug("Step 8: 保存とURL生成開始")
        
        artifact_urls = self.report_repository.save_report(
            report_key=self.report_key,
            report_date=report_date,
            excel_bytes=excel_bytes,
            pdf_bytes=pdf_bytes,
        )
        
        logger.debug(
            "Step 8: 保存とURL生成完了",
            extra={"elapsed_seconds": round(time.time() - step_start, 3)},
        )
        return artifact_urls

    def _create_response(
        self,
        artifact_urls,
        report_date: date,
        start_time: float,
    ) -> JSONResponse:
        """Step 9: レスポンス返却"""
        total_elapsed = time.time() - start_time
        logger.info(
            f"{self.report_name}生成完了",
            extra={
                "usecase": self.report_key,
                "report_date": report_date.isoformat(),
                "total_elapsed_seconds": round(total_elapsed, 3),
            },
        )
        
        # BFF互換のレスポンス形式
        artifact_dict = artifact_urls.to_dict()
        return JSONResponse(
            status_code=200,
            content={
                "message": f"{self.report_name}の生成が完了しました",
                "report_key": self.report_key,
                "report_date": report_date.isoformat(),
                "artifact": {
                    "excel_download_url": artifact_dict["excel_url"],
                    "pdf_preview_url": artifact_dict["pdf_url"],
                },
            },
        )
