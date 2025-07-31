import yaml
import pandas as pd
import os
from pathlib import Path
from typing import Optional, Union, Dict, Any


def get_factory_report_config_path(filename: str) -> str:
    """
    factory_reportの設定ファイルパスを取得

    Parameters:
        filename (str): 設定ファイル名

    Returns:
        str: 設定ファイルの絶対パス
    """
    config_dir = (
        "/backend/app/api/services/manage_report_processors/factory_report/config"
    )
    return os.path.join(config_dir, filename)


def load_yaml(filepath: str) -> Dict[str, Any]:
    """
    YAMLファイルを辞書形式で読み込む。

    Parameters:
        filepath (str): YAMLファイルのパス

    Returns:
        dict: YAMLから読み込まれた辞書データ
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"設定ファイルが見つかりません: {filepath}")

    with open(filepath, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_template_config() -> Dict[str, Any]:
    """
    テンプレート設定を取得

    Returns:
        dict: テンプレート設定辞書
    """
    config_path = get_factory_report_config_path("templates_config.yaml")
    return load_yaml(config_path)


def get_master_csv_config() -> Dict[str, Any]:
    """
    マスターCSV設定を取得

    Returns:
        dict: マスターCSV設定辞書
    """
    config_path = get_factory_report_config_path("master_csv_config.yaml")
    return load_yaml(config_path)


def get_required_columns_definition() -> Dict[str, Any]:
    """
    必須カラム定義を取得

    Returns:
        dict: 必須カラム定義辞書
    """
    config_path = get_factory_report_config_path("required_columns_definition.yaml")
    return load_yaml(config_path)


def get_data_file_path(filename: str, subdirectory: str = "master") -> str:
    """
    データファイルのパスを取得

    Parameters:
        filename (str): ファイル名
        subdirectory (str): サブディレクトリ名 (master, templates)

    Returns:
        str: データファイルの絶対パス
    """
    data_dir = f"/backend/app/api/services/manage_report_processors/factory_report/data/{subdirectory}"
    return os.path.join(data_dir, filename)


def load_master_csv(filename: str) -> pd.DataFrame:
    """
    マスターCSVファイルを読み込む

    Parameters:
        filename (str): CSVファイル名

    Returns:
        pd.DataFrame: 読み込まれたデータフレーム
    """
    filepath = get_data_file_path(filename, "master")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"マスターCSVファイルが見つかりません: {filepath}")

    return pd.read_csv(filepath, encoding="utf-8-sig", keep_default_na=False)


def get_template_excel_path() -> str:
    """
    テンプレートExcelファイルのパスを取得

    Returns:
        str: テンプレートExcelファイルの絶対パス
    """
    return get_data_file_path("factory_report.xlsx", "templates")
