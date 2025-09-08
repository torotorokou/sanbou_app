import pandas as pd
from app.st_app.utils.config_loader import clean_na_strings


def clean_cd_column(df: pd.DataFrame, col: str = "業者CD") -> pd.DataFrame:
    valid = df[col].notna()

    # ① 一旦文字列として変換 → ② <NA>をクリーンアップ → ③ intに変換 → ④ Series全体に代入（dtypeを明示）
    def safe_int_convert(x):
        cleaned_val = clean_na_strings(x)
        if cleaned_val is None:
            return None
        try:
            return int(float(cleaned_val))
        except (ValueError, TypeError):
            return None

    cleaned = df.loc[valid, col].apply(safe_int_convert)
    df.loc[valid, col] = cleaned.astype("Int64")  # ← Nullable Int 型（Pandas公式推奨）
    return df
