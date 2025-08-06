from pathlib import Path
import pandas as pd
import os
from app.api.st_app.utils.config_loader import clean_na_strings
from app.local_config.paths import BASE_ST_APP_DIR


def load_master_and_template(master_path: str | Path) -> pd.DataFrame:
    """
    テンプレート設定内の master_csv_path（相対パス）を受け取り、DataFrameとして返す。
    ファイルが見つからない場合は、複数の場所を探索する。
    """
    base_dir = BASE_ST_APP_DIR

    # 相対パスの場合はベースディレクトリと結合
    if not os.path.isabs(str(master_path)):
        full_path = base_dir / Path(master_path)
    else:
        # 絶対パスの場合はそのまま使用（/work/app は既に修正済み）
        full_path = Path(master_path)

    print(f"[INFO] Loading master file from: {full_path}")

    # dtype_spec = {
    #     "大項目": str,
    #     "小項目1": str,
    #     "小項目2": str,
    #     "セル": str,
    #     "値": "object",
    # }

    # <NA>文字列をfloat変換エラーから守るため、na_valuesを指定
    na_values = ["<NA>", "NaN", "nan", "None", "NULL", "null", "#N/A", "#NA", ""]

    df = pd.read_csv(
        full_path,
        encoding="utf-8-sig",
        # dtype=dtype_spec,
        na_values=na_values,
        keep_default_na=True,
    )

    # 全カラムに対してNA文字列をクリーンアップ
    for col in df.columns:
        df[col] = df[col].apply(clean_na_strings)

    return df
