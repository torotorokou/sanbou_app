# backend/app/api/services/report/base_report_generator.py

from abc import ABC, abstractmethod
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

import pandas as pd

from app.api.services.csv_formatter_service import CsvFormatterService
from app.api.services.csv_validator_facade import CsvValidatorService
from app.api.st_app.utils.config_loader import get_template_config
from app.api.st_app.utils.write_excel import write_values_to_template
from backend_shared.config.config_loader import ReportTemplateConfigLoader
from backend_shared.src.report_checker.check_csv_files import check_csv_files


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
        # files はアップロード入力（Raw）を想定。必要に応じて使用可。
        self.files = files
        self.report_key = report_key
        self.config_loader_report = ReportTemplateConfigLoader()
        self.result_df = None  # main_processの結果を保存
        # デフォルトのバリデータ/フォーマッタ（必要に応じてサブクラスで置換）
        self._validator = CsvValidatorService()
        self._formatter = CsvFormatterService()

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

    # --- 新インターフェース: validate / format / main_process ---
    # 既定実装では共通サービスを使ったバリデーション・整形を提供。
    def validate(self, dfs: Dict[str, Any], file_inputs: Dict[str, Any]):
        """
        デフォルト実装: 共通CsvValidatorServiceで検証。
        戻り値は None（成功）または ErrorApiResponse。
        """
        try:
            return self._validator.validate(dfs, file_inputs)
        except Exception as e:
            print(f"[ERROR] validate failed: {e}")
            raise

    def format(self, dfs: Dict[str, Any]) -> Dict[str, Any]:
        """デフォルト実装: 共通CsvFormatterServiceで整形。"""
        try:
            return self._formatter.format(dfs)
        except Exception as e:
            print(f"[ERROR] format failed: {e}")
            raise

    def make_report_date(self, df_formatted: Dict[str, Any]) -> str:
        """
        帳票日付の作成（整形後データを前提）

        引数は整形後の DataFrame 群（df_formatted）に統一します。
        代表となる1つ目のDFから列「伝票日付」の先頭値を取得して日付文字列(YYYY-MM-DD)に正規化します。
        """
        if not df_formatted:
            raise ValueError("df_formatted が空です。帳票日付を決定できません。")

        first_value = next(iter(df_formatted.values()))

        # 値の取り出しをできるだけ柔軟に
        report_date: Any
        if isinstance(first_value, pd.DataFrame):
            if "伝票日付" not in first_value.columns:
                raise KeyError("整形後データに『伝票日付』列が見つかりません。")
            if len(first_value) == 0:
                raise ValueError("『伝票日付』列は存在しますが、行が空です。")
            report_date = first_value["伝票日付"].iloc[0]
        elif isinstance(first_value, dict):
            # まれに dict(list) 形式を許容
            if "伝票日付" not in first_value or len(first_value["伝票日付"]) == 0:
                raise KeyError("整形後データ(dict)に『伝票日付』が見つかりません。")
            report_date = first_value["伝票日付"][0]
        else:
            raise ValueError("整形後データの形式に対応していません。")

        # 文字列 / pandas.Timestamp / その他を吸収
        if isinstance(report_date, str):
            # 'YYYY/MM/DD', 'YYYY-MM-DDTHH:MM:SS' 等を想定
            try:
                dt = datetime.fromisoformat(report_date[:19].replace("/", "-"))
                return dt.date().isoformat()
            except Exception:
                # to_datetimeで再挑戦
                try:
                    dt = pd.to_datetime(report_date)
                    return dt.date().isoformat()
                except Exception:
                    return str(report_date)[:10]
        elif isinstance(report_date, pd.Timestamp):
            return report_date.date().isoformat()
        else:
            return str(report_date)[:10]

    @abstractmethod
    def main_process(self, df_formatted: Dict[str, Any]) -> pd.DataFrame:
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
