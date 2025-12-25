"""Data cleaning utilities for report processing."""

import pandas as pd

from backend_shared.utils.dataframe_utils import clean_na_strings


def clean_cd_column(df: pd.DataFrame, col: str = "業者CD") -> pd.DataFrame:
    """業者CD等のコード列をクリーンアップしてInt64に変換"""
    valid = df[col].notna()

    def safe_int_convert(x):
        cleaned_val = clean_na_strings(x)
        if cleaned_val is None:
            return None
        try:
            return int(float(cleaned_val))
        except (ValueError, TypeError):
            return None

    cleaned = df.loc[valid, col].apply(safe_int_convert)
    df.loc[valid, col] = cleaned.astype("Int64")
    return df
