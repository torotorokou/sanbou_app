# app/utils/config_loader.py

import yaml
from fastapi import HTTPException


def load_csv_path_config(
    csv_type: str, yaml_path: str = "/app/config/csv_paths.yaml"
) -> dict:
    """
    CSV種別（ukeire, shukka など）に対応するパス設定をYAMLから読み込む。

    Args:
        csv_type (str): 対象のCSV種別キー
        yaml_path (str): 設定ファイルのパス（デフォルトは固定）

    Returns:
        dict: 指定されたcsv_typeに対応する設定ディクショナリ
    """
    try:
        with open(yaml_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config["csv_paths"][csv_type]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"設定ファイル読み込みエラー: {e}")
