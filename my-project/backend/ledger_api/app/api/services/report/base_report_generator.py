# backend/app/api/services/base_report_generator.py

import pandas as pd
from io import BytesIO
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from backend_shared.config.config_loader import ReportTemplateConfigLoader
from backend_shared.src.report_checker.check_csv_files import check_csv_files
from app.api.st_app.utils.write_excel import write_values_to_template
from app.api.st_app.utils.config_loader import get_template_config


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

    def __init__(self, report_key: str, files: Dict[str, Any]):
        self.files = files
        self.report_key = report_key
        self.config_loader_report = ReportTemplateConfigLoader()
        self.result_df = None  # main_processの結果を保存

    def print_start_report_key(self):
        print(f"[DEBUG] report_key: {self.report_key}開始")

    def print_finish_report_key(self):
        print(f"[DEBUG] report_key: {self.report_key}終了")

    def preprocess(self, report_key: Optional[str] = None):
        if report_key is None:
            raise ValueError("report_key must be provided and must be a string.")
        required = self.config_loader_report.get_required_files(report_key)
        optional = self.config_loader_report.get_optional_files(report_key)
        check_csv_files(self.files, required, optional)
        print(f"[INFO] 必須ファイルチェックOK: {required} がすべて揃っています。")
        return self.files

    def make_report_date(self, files: Dict[str, Any]) -> str:
        first_file = next(iter(files.values()))
        if isinstance(first_file, pd.DataFrame):
            report_date = first_file["伝票日付"].iloc[0]
        elif isinstance(first_file, dict):
            report_date = first_file["伝票日付"][0]
        else:
            raise ValueError("対応していないデータ形式です")
        if isinstance(report_date, str):
            dt = datetime.fromisoformat(report_date[:19].replace("/", "-"))
            return dt.date().isoformat()
        elif isinstance(report_date, pd.Timestamp):
            return report_date.date().isoformat()
        else:
            return str(report_date)[:10]

    def main_process(self) -> pd.DataFrame:
        self.print_start_report_key()
        result = self._main_process_impl()
        self.print_finish_report_key()
        return result

    @abstractmethod
    def _main_process_impl(self) -> pd.DataFrame:
        pass

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
