import pandas as pd
from typing import Optional


def combine_date_and_time(
    df: pd.DataFrame,
    date_col: str,
    time_col: str,
    new_col: Optional[str] = None,
    format: Optional[str] = None,
) -> pd.DataFrame:
    """
    日付カラムと時間カラムを結合し、新しいカラムにdatetime64[ns]型で変換する。
    """
    if new_col is None:
        new_col = time_col
    combined = (
        df[date_col].astype(str).str.strip()
        + " "
        + df[time_col].astype(str).str.strip()
    )
    default_format = "%Y/%m/%d %H:%M:%S"
    if format is None:
        format = default_format
    df[new_col] = pd.to_datetime(combined, errors="coerce")
    return df


def remove_weekday_parentheses(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    指定したカラムの値から曜日の括弧部分（例: '2025/06/01(日)'）を削除し、datetime64[ns]型に変換する。
    """
    df[column] = (
        df[column].astype(str).str.replace(r"\([^)]+\)", "", regex=True).str.strip()
    )
    default_format = "%Y/%m/%d"
    df[column] = pd.to_datetime(df[column], format=default_format, errors="coerce")
    return df


def remove_commas_and_convert_numeric(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    カンマ付き数値文字列（例: '1,200'）を除去し、float型に変換する。
    """
    df[column] = df[column].astype(str).str.replace(",", "").astype(float)
    return df


def convert_df_by_types(df: pd.DataFrame, type_dict: dict) -> pd.DataFrame:
    """
    指定された型辞書に従って、各列をPandas標準型に変換する。
    サポート型: int, float, str, datetime, category
    """
    type_map = {
        "int": lambda s: pd.to_numeric(s, errors="coerce").astype("Int64"),
        "float": lambda s: pd.to_numeric(s, errors="coerce").astype(float),
        "str": lambda s: s.astype(str),
        "datetime": lambda s: pd.to_datetime(s, errors="coerce"),
        "category": lambda s: s.astype("category"),
    }
    for col, typ in type_dict.items():
        if col in df.columns and typ in type_map:
            df[col] = type_map[typ](df[col])
    return df
