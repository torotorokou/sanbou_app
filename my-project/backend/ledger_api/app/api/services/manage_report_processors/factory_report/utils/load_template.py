import pandas as pd
import os
from pathlib import Path
from typing import Union


def load_master_and_template(master_path: Union[str, Path]) -> pd.DataFrame:
    """
    マスターCSVファイルを読み込んでDataFrameとして返す。

    Parameters:
        master_path (Union[str, Path]): マスターCSVファイルのパス

    Returns:
        pd.DataFrame: 読み込まれたデータフレーム
    """
    # 絶対パスでない場合は、factory_reportのdataディレクトリからの相対パスとして処理
    if not os.path.isabs(master_path):
        base_dir = "/backend/app/api/services/manage_report_processors/factory_report/data/master"
        full_path = os.path.join(base_dir, master_path)
    else:
        full_path = str(master_path)

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"マスターファイルが見つかりません: {full_path}")

    dtype_spec = {
        "大項目": str,
        "小項目1": str,
        "小項目2": str,
        "セル": str,
        "値": "object",
        "業者名": str,
        "業者CD": str,
        "品名": str,
        "セルロック": "object",
        "順番": "object",
    }

    return pd.read_csv(
        full_path, encoding="utf-8-sig", dtype=dtype_spec, keep_default_na=False
    )


def load_template_excel(template_path: Union[str, Path] = None) -> str:
    """
    テンプレートExcelファイルのパスを取得

    Parameters:
        template_path (Union[str, Path], optional): テンプレートファイルのパス

    Returns:
        str: テンプレートExcelファイルの絶対パス
    """
    if template_path is None:
        template_path = "/backend/app/api/services/manage_report_processors/factory_report/data/templates/factory_report.xlsx"

    if not os.path.isabs(template_path):
        base_dir = "/backend/app/api/services/manage_report_processors/factory_report/data/templates"
        full_path = os.path.join(base_dir, template_path)
    else:
        full_path = str(template_path)

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {full_path}")

    return full_path
