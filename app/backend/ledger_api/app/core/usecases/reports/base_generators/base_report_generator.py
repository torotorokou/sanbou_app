# backend/app/api/services/report/base_report_generator.py

from abc import ABC, abstractmethod
from datetime import datetime
from io import BytesIO
from typing import Any

import pandas as pd
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)

from app.infra.adapters.csv import CsvFormatterService, CsvValidatorService
from app.infra.report_utils import get_template_config, write_values_to_template

# CSV処理サービス（application/usecases/csvから参照）
from backend_shared.config.config_loader import ReportTemplateConfigLoader
from backend_shared.core.usecases.report_checker.check_csv_files import check_csv_files


class BaseReportGenerator(ABC):
    """
    レポート生成の基底クラス

    全ての帳票生成クラスの共通機能を提供します：
    - 前処理（ファイルチェック）
    - メイン処理（サブクラスで実装）
    - PDF生成
    - Excel生成
    - 後処理（ファイル名生成）
    """

    def __init__(self, report_key: str, files: dict[str, Any]):
        # files はアップロード入力（Raw）を想定。必要に応じて使用可。
        self.files = files
        self.report_key = report_key
        self.config_loader_report = ReportTemplateConfigLoader()
        self.result_df = None  # main_processの結果を保存
        # 帳簿ごとの期間指定（"oneday" | "oneweek" | "onemonth" など）。未指定ならNone。
        self.period_type: str | None = None
        # デフォルトのバリデータ/フォーマッタ（必要に応じてサブクラスで置換）
        self._validator = CsvValidatorService()
        self._formatter = CsvFormatterService()

    def print_start_report_key(self):
        logger.debug(
            "Starting report generation", extra={"report_key": self.report_key}
        )

    def print_finish_report_key(self):
        logger.debug(
            "Finished report generation", extra={"report_key": self.report_key}
        )

    def preprocess(self, report_key: str | None = None):
        if report_key is None:
            raise ValueError("report_key must be provided and must be a string.")
        required = self.config_loader_report.get_required_files(report_key)
        optional = self.config_loader_report.get_optional_files(report_key)
        check_csv_files(self.files, required, optional)
        logger.info("Required file check passed", extra={"required_files": required})
        return self.files

    # --- 新インターフェース: validate / format / main_process ---
    # 既定実装では共通サービスを使ったバリデーション・整形を提供。
    def validate(self, dfs: dict[str, Any], file_inputs: dict[str, Any]):
        """
        デフォルト実装: 共通CsvValidatorServiceで検証。
        戻り値は None（成功）または ErrorApiResponse。
        """
        try:
            return self._validator.validate(dfs, file_inputs)
        except Exception as e:
            logger.error("Validation failed", extra={"error": str(e)}, exc_info=True)
            raise

    def format(self, dfs: dict[str, Any]) -> dict[str, Any]:
        """デフォルト実装: 共通CsvFormatterServiceで整形。"""
        try:
            return self._formatter.format(dfs)
        except Exception as e:
            logger.error("Formatting failed", extra={"error": str(e)}, exc_info=True)
            raise

    def make_report_date(self, df_formatted: dict[str, Any]) -> str:
        """
        帳票日付の作成（整形後データを前提）

        - 複数の候補列から最初に見つかった有効な日付を使用
        - 見つからない/空のときは今日の日付にフォールバック
        """
        if not df_formatted:
            # 空のときは本日付でフォールバック
            return datetime.now().date().isoformat()

        date_candidates = ["伝票日付", "日付", "date", "Date"]

        # DataFrame 優先で走査
        for value in df_formatted.values():
            if isinstance(value, pd.DataFrame) and not value.empty:
                # 候補列を順にチェック
                for col in date_candidates:
                    if col in value.columns and not value[col].empty:
                        first = value[col].iloc[0]
                        # 正規化
                        if isinstance(first, str):
                            try:
                                dt = datetime.fromisoformat(
                                    first[:19].replace("/", "-")
                                )
                                return dt.date().isoformat()
                            except Exception:
                                try:
                                    dt = pd.to_datetime(first)
                                    return dt.date().isoformat()
                                except Exception:
                                    continue
                        elif isinstance(first, pd.Timestamp):
                            return first.date().isoformat()
                        else:
                            try:
                                dt = pd.to_datetime(first)
                                return dt.date().isoformat()
                            except Exception:
                                continue

        # dict(list) 形式のフォールバック
        for value in df_formatted.values():
            if isinstance(value, dict):
                for col in date_candidates:
                    if col in value:
                        seq = value.get(col) or []
                        if len(seq) > 0:
                            first = seq[0]
                            try:
                                dt = pd.to_datetime(first)
                                return dt.date().isoformat()
                            except Exception:
                                continue

        # 最後のフォールバック: 今日
        return datetime.now().date().isoformat()

    @abstractmethod
    def main_process(self, df_formatted: dict[str, Any]) -> pd.DataFrame:
        """サブクラスで実装: 整形済みDataFrame群から最終DFを生成。"""
        raise NotImplementedError

    def generate_excel_bytes(self, df: pd.DataFrame, report_date: str) -> BytesIO:
        selected_template = self.report_key
        template_path = get_template_config()[selected_template]["template_excel_path"]
        output_excel = write_values_to_template(df, template_path, report_date)
        output_excel.seek(0)
        return output_excel

    def postprocess(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_download_pdf_name(self, file_name_jp: str, date_str: str) -> str:
        return f"{file_name_jp}_{date_str}.pdf"

    def get_download_excel_name(self, file_name_jp: str, date_str: str) -> str:
        return f"{file_name_jp}_{date_str}.xlsx"
