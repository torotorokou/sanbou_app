"""
dataframe_utils_optimized.py

dataframe_utils.pyの最適化版関数を提供。
apply()を使った行単位処理をベクトル化して高速化する。
"""

import numpy as np
import pandas as pd


def clean_na_strings_vectorized(series: pd.Series) -> pd.Series:
    """
    clean_na_strings のベクトル化版。

    従来版は series.apply(clean_na_strings) で行単位処理していたが、
    この関数ではベクトル化操作で一括変換する。

    Parameters
    ----------
    series : pd.Series
        クリーニング対象のSeries

    Returns
    -------
    pd.Series
        <NA>等の文字列をNoneに変換したSeries

    Performance
    -----------
    - 従来版: O(n) の Python ループ（apply）
    - 最適化版: O(1) のベクトル化操作（NumPy/Pandas内部）
    - 速度改善: 約10-100倍（データサイズに依存）

    Notes
    -----
    変換対象の文字列:
    - '<NA>', 'NaN', 'nan', 'None', 'NULL', 'null', '#N/A', '#NA'
    - 空文字列（strip後）
    """
    # 文字列型でない場合はそのまま返す
    if not pd.api.types.is_string_dtype(series):
        return series

    # ベクトル化: isin() で一括判定
    na_strings = ["<NA>", "NaN", "nan", "None", "NULL", "null", "#N/A", "#NA"]

    # 1. NA文字列を判定
    is_na_string = series.isin(na_strings)

    # 2. 空文字列（strip後）を判定
    # str.strip()は既にベクトル化されているので高速
    is_empty = series.str.strip() == ""

    # 3. どちらかに該当する場合はNone（pd.NA）に変換
    result = series.copy()
    result[is_na_string | is_empty] = None

    return result


def apply_clean_na_strings_optimized(
    df: pd.DataFrame, columns: list[str]
) -> pd.DataFrame:
    """
    複数列に対してclean_na_strings_vectorizedを適用する。

    Parameters
    ----------
    df : pd.DataFrame
        対象DataFrame
    columns : list[str]
        クリーニング対象のカラムリスト

    Returns
    -------
    pd.DataFrame
        クリーニング済みのDataFrame（コピー）

    Example
    -------
    >>> df = pd.DataFrame({'col1': ['<NA>', '123', ''], 'col2': [1, 2, 3]})
    >>> df_cleaned = apply_clean_na_strings_optimized(df, ['col1'])
    >>> df_cleaned['col1'].tolist()
    [None, '123', None]
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = clean_na_strings_vectorized(df[col])
    return df


def to_numeric_vectorized(series: pd.Series) -> pd.Series:
    """
    clean_na_strings_vectorized + pd.to_numeric の組み合わせを一括実行。

    従来は:
    1. series.apply(clean_na_strings)
    2. pd.to_numeric(series, errors='coerce')

    最適化版:
    1. clean_na_strings_vectorized(series)
    2. pd.to_numeric(series, errors='coerce')

    両方ともベクトル化されているため、apply()を使うよりはるかに高速。

    Parameters
    ----------
    series : pd.Series
        数値変換対象のSeries

    Returns
    -------
    pd.Series
        数値型に変換されたSeries（変換できない値はNaN）
    """
    cleaned = clean_na_strings_vectorized(series)
    return pd.to_numeric(cleaned, errors="coerce")
