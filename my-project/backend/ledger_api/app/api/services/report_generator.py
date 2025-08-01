# backend/app/api/services/report_generator.py

import os
import pandas as pd
from io import BytesIO
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

from backend_shared.config.config_loader import ReportTemplateConfigLoader
from backend_shared.src.report_checker.check_csv_files import check_csv_files

# 先ほど作成したExcel出力機能をインポート

from app.api.st_app.utils.write_excel import write_values_to_template

from app.api.st_app.utils.config_loader import (
    get_template_config,
)


# reportlabがインストールされている場合のみPDF機能を有効化
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# factory_report.pyのprocess関数を直接呼び出す
from app.api.st_app.logic.manage.factory_report import process


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

    def __init__(self, report_key: str, output_dir: str, files: Dict[str, Any]):
        """
        Args:
            output_dir: 出力ディレクトリのパス
            files: CSVファイルのDataFrame辞書 {ファイル種別: DataFrame}
        """
        self.output_dir = output_dir
        self.files = files
        self.report_key = report_key
        self.config_loader_report = ReportTemplateConfigLoader()
        self.result_df = None  # main_processの結果を保存

    def preprocess(self, report_key: Optional[str] = None):
        """
        前処理：必要なファイルがそろっているかチェック

        Args:
            report_key: レポートの種類（例: "factory_report"）
        """
        if report_key is None:
            raise ValueError("report_key must be provided and must be a string.")

        # 設定ファイルから必要なファイル一覧を取得
        required = self.config_loader_report.get_required_files(report_key)
        optional = self.config_loader_report.get_optional_files(report_key)

        # ファイルチェック実行
        check_csv_files(self.files, required, optional)
        print(f"[INFO] 必須ファイルチェックOK: {required} がすべて揃っています。")
        return self.files

    def make_report_date(self, files: Dict[str, Any]) -> str:
        # 最初のDataFrameまたはdictを取得
        first_file = next(iter(files.values()))
        # DataFrameの場合
        if isinstance(first_file, pd.DataFrame):
            report_date = first_file["伝票日付"].iloc[0]
        # dictの場合
        elif isinstance(first_file, dict):
            report_date = first_file["伝票日付"][0]
        else:
            raise ValueError("対応していないデータ形式です")

        # 文字列→datetime変換（日付部分のみ取得）
        # 例: "2024-07-31 09:00:00" → "2024-07-31"
        if isinstance(report_date, str):
            dt = datetime.fromisoformat(report_date[:19].replace("/", "-"))
            return dt.date().isoformat()
        elif isinstance(report_date, pd.Timestamp):
            return report_date.date().isoformat()
        else:
            # 万一想定外フォーマットの場合はstrにして前10桁（YYYY-MM-DD）で返す
            return str(report_date)[:10]

    @abstractmethod
    def main_process(self, report_key: str) -> pd.DataFrame:
        """
        メインの帳票生成処理（サブクラスで実装必須）

        Returns:
            pd.DataFrame: 生成された帳票データ
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def generate_excel_bytes(self, df: pd.DataFrame, report_date: str) -> BytesIO:
        selected_template = self.report_key
        template_path = get_template_config()[selected_template]["template_excel_path"]

        output_excel = write_values_to_template(df, template_path, report_date)

        output_excel.seek(0)  # 念のため先頭に戻す
        return output_excel

    def postprocess(self) -> str:
        """後処理：ダウンロード名用の日付返却"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_download_pdf_name(self, file_name_jp: str, date_str: str) -> str:
        """PDF用のダウンロードファイル名を生成"""
        return f"{file_name_jp}_{date_str}.pdf"

    def get_download_excel_name(self, file_name_jp: str, date_str: str) -> str:
        """Excel用のダウンロードファイル名を生成"""
        return f"{file_name_jp}_{date_str}.xlsx"


class FactoryReportGenerator(BaseReportGenerator):
    """工場レポート生成クラス"""

    def main_process(self, report_key: str) -> pd.DataFrame:
        """
        工場レポートのメイン処理

        Returns:
            pd.DataFrame: 生成された工場レポートデータ
        """
        print("[INFO] 工場レポート生成開始")

        # processを呼び出し
        result_df = process(self.files)

        print(f"[INFO] 工場レポート生成完了: {len(result_df)}行")
        return result_df

    def _get_template_path(self) -> Optional[str]:
        """
        工場レポート用のテンプレートファイルパスを取得

        Returns:
            Optional[str]: テンプレートファイルのパス
        """
        try:
            # YAMLファイルからテンプレートパスを取得
            template_path = self.config_loader_report.get_template_excel_path(
                "factory_report"
            )

            if template_path and os.path.exists(template_path):
                print(f"[INFO] 工場レポートテンプレートファイル発見: {template_path}")
                return template_path
            else:
                print(
                    f"[WARNING] 工場レポートテンプレートファイルが存在しません: {template_path}"
                )
                return None

        except Exception as e:
            print(f"[ERROR] テンプレートパス取得エラー: {e}")
            return None


class BalanceSheetGenerator(BaseReportGenerator):
    """バランスシート生成クラス（未実装）"""

    def main_process(self) -> pd.DataFrame:
        """
        バランスシートのメイン処理（サンプル実装）

        Returns:
            pd.DataFrame: 生成されたバランスシートデータ
        """
        print("[INFO] バランスシート生成開始（サンプル実装）")

        # サンプルデータを作成
        sample_data = pd.DataFrame(
            {
                "項目": ["売上", "費用", "利益"],
                "金額": [1000000, 600000, 400000],
                "比率": ["100%", "60%", "40%"],
            }
        )

        self.result_df = sample_data
        print(f"[INFO] バランスシート生成完了（サンプル）: {len(sample_data)}行")
        return sample_data


class AverageSheetGenerator(BaseReportGenerator):
    """平均シート生成クラス（未実装）"""

    def main_process(self) -> pd.DataFrame:
        """
        平均シートのメイン処理（サンプル実装）

        Returns:
            pd.DataFrame: 生成された平均シートデータ
        """
        print("[INFO] 平均シート生成開始（サンプル実装）")

        # サンプルデータを作成
        sample_data = pd.DataFrame(
            {
                "期間": ["1月", "2月", "3月"],
                "平均値": [150.5, 175.2, 163.8],
                "最高値": [200, 220, 195],
                "最低値": [100, 130, 125],
            }
        )

        self.result_df = sample_data
        print(f"[INFO] 平均シート生成完了（サンプル）: {len(sample_data)}行")
        return sample_data


class BlockUnitPriceGenerator(BaseReportGenerator):
    """ブロック単価生成クラス（未実装）"""

    def main_process(self) -> pd.DataFrame:
        """
        ブロック単価のメイン処理（サンプル実装）

        Returns:
            pd.DataFrame: 生成されたブロック単価データ
        """
        print("[INFO] ブロック単価生成開始（サンプル実装）")

        # サンプルデータを作成
        sample_data = pd.DataFrame(
            {
                "ブロック名": ["Aブロック", "Bブロック", "Cブロック"],
                "単価": [1500, 1800, 1200],
                "数量": [10, 8, 15],
                "合計": [15000, 14400, 18000],
            }
        )

        self.result_df = sample_data
        print(f"[INFO] ブロック単価生成完了（サンプル）: {len(sample_data)}行")
        return sample_data


class ManagementSheetGenerator(BaseReportGenerator):
    """管理シート生成クラス（未実装）"""

    def main_process(self) -> pd.DataFrame:
        """
        管理シートのメイン処理（サンプル実装）

        Returns:
            pd.DataFrame: 生成された管理シートデータ
        """
        print("[INFO] 管理シート生成開始（サンプル実装）")

        # サンプルデータを作成
        sample_data = pd.DataFrame(
            {
                "管理項目": ["品質", "コスト", "納期"],
                "目標値": [95, 1000000, 30],
                "実績値": [97, 950000, 28],
                "達成率": ["102%", "105%", "107%"],
            }
        )

        self.result_df = sample_data
        print(f"[INFO] 管理シート生成完了（サンプル）: {len(sample_data)}行")
        return sample_data


class BalanceManagementTableGenerator(BaseReportGenerator):
    """残高管理表生成クラス（未実装）"""

    def main_process(self) -> pd.DataFrame:
        """
        残高管理表のメイン処理（サンプル実装）

        Returns:
            pd.DataFrame: 生成された残高管理表データ
        """
        print("[INFO] 残高管理表生成開始（サンプル実装）")

        # サンプルデータを作成
        sample_data = pd.DataFrame(
            {
                "日付": ["2025-07-01", "2025-07-15", "2025-07-31"],
                "入金": [500000, 300000, 800000],
                "出金": [200000, 450000, 100000],
                "残高": [300000, 150000, 850000],
            }
        )

        self.result_df = sample_data
        print(f"[INFO] 残高管理表生成完了（サンプル）: {len(sample_data)}行")
        return sample_data


def get_report_generator(
    report_key: str, output_dir: str, files: Dict[str, Any]
) -> BaseReportGenerator:
    """
    帳簿種別に応じて適切なGeneratorを返す

    Args:
        report_key: レポートの種類（"factory_report", "balance_sheet"など）
        output_dir: 出力ディレクトリのパス
        files: CSVファイルのDataFrame辞書

    Returns:
        BaseReportGenerator: 対応するレポート生成クラスのインスタンス

    Example:
        # エンドポイントでの使用例
        generator = get_report_generator("factory_report", "/output", df_dict)
        generator.preprocess("factory_report")
        result_df = generator.main_process()
        pdf_name = generator.generate_pdf("report.pdf")
        excel_name = generator.generate_excel("report.xlsx")
    """
    generators = {
        "factory_report": FactoryReportGenerator,
        "balance_sheet": BalanceSheetGenerator,
        "average_sheet": AverageSheetGenerator,
        "block_unit_price": BlockUnitPriceGenerator,
        "management_sheet": ManagementSheetGenerator,
        "balance_management_table": BalanceManagementTableGenerator,
    }

    if report_key not in generators:
        available_keys = list(generators.keys())
        raise ValueError(
            f"Unsupported report type: {report_key}. Available types: {available_keys}"
        )

    generator_class = generators[report_key]
    return generator_class(report_key, output_dir, files)
