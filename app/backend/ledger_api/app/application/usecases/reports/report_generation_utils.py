"""
帳票生成UseCase共通ユーティリティ

全てのレポートUseCaseで共通して使用される処理を提供します。
"""

import tempfile
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
from app.infra.report_utils import get_template_config, write_values_to_template
from app.infra.utils.pdf_conversion import convert_excel_to_pdf
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


def generate_pdf_from_excel(excel_bytes: BytesIO) -> BytesIO:
    """
    ExcelバイトストリームからPDFを生成する共通関数

    全てのレポートUseCaseで使用される一時ファイル経由のPDF変換処理を提供します。

    Args:
        excel_bytes: ExcelファイルのByteIOオブジェクト

    Returns:
        BytesIO: PDFファイルのバイトストリーム

    Raises:
        Exception: PDF変換に失敗した場合
    """
    # 一時ファイルにExcelを書き出し
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_excel:
        tmp_excel.write(excel_bytes.getvalue())
        tmp_excel_path = Path(tmp_excel.name)

    try:
        # PDFに変換
        pdf_bytes_raw = convert_excel_to_pdf(tmp_excel_path)

        # BytesIOにラップして返却
        pdf_bytes = BytesIO(pdf_bytes_raw)
        return pdf_bytes
    finally:
        # 一時ファイルを削除
        if tmp_excel_path.exists():
            tmp_excel_path.unlink()


def generate_excel_from_dataframe(
    result_df: pd.DataFrame,
    report_key: str,
    report_date: date,
) -> BytesIO:
    """
    DataFrameからExcelバイトストリームを生成する共通関数

    テンプレート設定を取得し、write_values_to_templateを使用してExcelを生成します。

    Args:
        result_df: レポートの最終DataFrame
        report_key: レポートキー（'factory_report', 'balance_sheet'等）
        report_date: レポート日付

    Returns:
        BytesIO: Excelファイルのバイトストリーム

    Raises:
        KeyError: report_keyが設定に存在しない場合
        Exception: Excel生成に失敗した場合
    """
    template_config = get_template_config()[report_key]
    template_path = template_config["template_excel_path"]

    # 日付文字列を生成（シート名用）
    extracted_date = report_date.strftime("%Y年%m月%d日")

    excel_bytes = write_values_to_template(
        df=result_df,
        template_path=template_path,
        extracted_date=extracted_date,
    )

    return excel_bytes
