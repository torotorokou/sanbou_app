# backend/app/api/services/report_generator.py

import pandas as pd
from io import BytesIO
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from backend_shared.config.config_loader import ReportTemplateConfigLoader
from backend_shared.src.report_checker.check_csv_files import check_csv_files

# 先ほど作成したExcel出力機能をインポート

from app.st_app.utils.write_excel import write_values_to_template

from app.st_app.utils.config_loader import (
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


from app.st_app.logic.manage.factory_report import process as process_factory_report
from app.st_app.logic.manage.factory_report import process as process_balance_sheet


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
        """
        Args:
            files: CSVファイルのDataFrame辞書 {ファイル種別: DataFrame}
        """
        self.files = files
        self.report_key = report_key
        self.config_loader_report = ReportTemplateConfigLoader()
        self.result_df = None  # main_processの結果を保存

    def print_start_report_key(self):
        print(f"[DEBUG] report_key: {self.report_key}開始")

    def print_finish_report_key(self):
        print(f"[DEBUG] report_key: {self.report_key}終了")
