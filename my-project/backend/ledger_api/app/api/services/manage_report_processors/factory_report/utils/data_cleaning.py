import pandas as pd
from typing import Union


def clean_cd_column(df: pd.DataFrame, col: str = "業者CD") -> pd.DataFrame:
    """
    業者CD列などのコード列をクリーニングする

    Parameters:
        df (pd.DataFrame): 対象のデータフレーム
        col (str): クリーニングするカラム名

    Returns:
        pd.DataFrame: クリーニング済みのデータフレーム
    """
    df = df.copy()
    valid = df[col].notna()

    # ① 一旦文字列として変換 → ② intに変換 → ③ Series全体に代入（dtypeを明示）
    cleaned = df.loc[valid, col].apply(lambda x: int(float(x)))
    df.loc[valid, col] = cleaned.astype("Int64")  # ← Nullable Int 型（Pandas公式推奨）
    return df


def clean_numeric_column(
    df: pd.DataFrame, col: str, fill_value: Union[int, float] = 0
) -> pd.DataFrame:
    """
    数値列をクリーニングする

    Parameters:
        df (pd.DataFrame): 対象のデータフレーム
        col (str): クリーニングするカラム名
        fill_value (Union[int, float]): 欠損値の補完値

    Returns:
        pd.DataFrame: クリーニング済みのデータフレーム
    """
    df = df.copy()
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(fill_value)
    return df


def clean_string_column(
    df: pd.DataFrame, col: str, fill_value: str = ""
) -> pd.DataFrame:
    """
    文字列列をクリーニングする

    Parameters:
        df (pd.DataFrame): 対象のデータフレーム
        col (str): クリーニングするカラム名
        fill_value (str): 欠損値の補完値

    Returns:
        pd.DataFrame: クリーニング済みのデータフレーム
    """
    df = df.copy()
    df[col] = df[col].astype(str).fillna(fill_value)
    return df
