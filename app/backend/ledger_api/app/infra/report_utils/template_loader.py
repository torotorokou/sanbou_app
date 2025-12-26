import os
from pathlib import Path

import pandas as pd

from backend_shared.application.logging import get_module_logger
from backend_shared.utils.dataframe_utils import clean_na_strings


logger = get_module_logger(__name__)


def load_master_and_template(master_path: str | Path) -> pd.DataFrame:
    """
    テンプレート設定内の master_csv_path（相対パス）を受け取り、DataFrameとして返す。
    ファイルが見つからない場合は、複数の場所を探索する。
    """
    """
    master_path: YAMLで指定したデータマスターのパス (例: data/master/abc_average_write_targets.csv)

    BASE_API_DIR環境変数を使用
    """
    base_dir = Path(os.getenv("BASE_API_DIR", "/backend/app/api"))

    # 相対パスの場合はベースディレクトリと結合
    if not os.path.isabs(str(master_path)):
        full_path = base_dir / Path(master_path)
    else:
        # 絶対パスの場合はそのまま使用（/work/app は既に修正済み）
        full_path = Path(master_path)

    logger.info(f"Loading master file from: {full_path}")

    # <NA>文字列をfloat変換エラーから守るため、na_valuesを指定
    na_values = ["<NA>", "NaN", "nan", "None", "NULL", "null", "#N/A", "#NA", ""]

    df = pd.read_csv(
        full_path,
        encoding="utf-8-sig",
        na_values=na_values,
        keep_default_na=True,
    )

    # 全カラムに対してNA文字列をクリーンアップ
    for col in df.columns:
        df[col] = df[col].apply(clean_na_strings)

    return df
