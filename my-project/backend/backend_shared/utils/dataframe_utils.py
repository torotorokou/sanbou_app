"""
DataFrameの操作・変換を行うユーティリティモジュール。
初心者にも分かりやすいように日本語でコメント・ドックストリングを記載しています。
"""

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
    例：'2025/06/01' + '14:30:00' → '2025/06/01 14:30:00'
    :param df: 対象DataFrame
    :param date_col: 日付カラム名
    :param time_col: 時間カラム名
    :param new_col: 新しいカラム名（省略時はtime_colを上書き）
    :param format: 日時フォーマット（省略時は'%Y/%m/%d %H:%M:%S'）
    :return: 変換後のDataFrame
    """
    if new_col is None:
        new_col = time_col
    # 日付と時間の文字列を結合
    combined = (
        df[date_col].astype(str).str.strip()
        + " "
        + df[time_col].astype(str).str.strip()
    )
    default_format = "%Y/%m/%d %H:%M:%S"
    if format is None:
        format = default_format
    # 結合した文字列をdatetime型に変換
    df[new_col] = pd.to_datetime(combined, errors="coerce")
    return df


def remove_weekday_parentheses(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    指定したカラムの値から曜日の括弧部分（例: '2025/06/01(日)'）を削除し、datetime64[ns]型に変換する。
    :param df: 対象DataFrame
    :param column: 変換対象のカラム名
    :return: 変換後のDataFrame
    """
    # 正規表現で括弧と中身を除去
    df[column] = (
        df[column].astype(str).str.replace(r"\([^)]+\)", "", regex=True).str.strip()
    )
    default_format = "%Y/%m/%d"
    # 文字列をdatetime型に変換
    df[column] = pd.to_datetime(df[column], format=default_format, errors="coerce")
    return df


def remove_commas_and_convert_numeric(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    カンマ付き数値文字列（例: '1,200'）を除去し、float型に変換する。
    :param df: 対象DataFrame
    :param column: 変換対象のカラム名
    :return: 変換後のDataFrame
    """
    # カンマを除去してfloat型に変換
    df[column] = df[column].astype(str).str.replace(",", "").astype(float)
    return df


def convert_df_by_types(df: pd.DataFrame, type_dict: dict) -> pd.DataFrame:
    """
    指定された型辞書に従って、各列をPandas標準型に変換する。
    サポート型: int, float, str, datetime, category
    :param df: 対象DataFrame
    :param type_dict: {カラム名: 型名, ...} の辞書
    :return: 変換後のDataFrame
    """
    # 型変換のマッピング辞書
    type_map = {
        "int": lambda s: pd.to_numeric(s, errors="coerce").astype("Int64"),
        "float": lambda s: pd.to_numeric(s, errors="coerce").astype(float),
        "str": lambda s: s.astype(str),
        "datetime": lambda s: pd.to_datetime(s, errors="coerce"),
        "category": lambda s: s.astype("category"),
    }
    # 各カラムを指定された型に変換
    for col, typ in type_dict.items():
        if col in df.columns and typ in type_map:
            df[col] = type_map[typ](df[col])
    return df


def serialize_dates_info(dates_info: dict) -> dict:
    """
    日付情報の辞書をシリアライズ可能な形式に変換します。
    :param dates_info: 日付情報の辞書
    :return: 文字列化された日付情報
    """
    return {
        key: [str(d) for d in sorted(list(value))] for key, value in dates_info.items()
    }


# 伝票日付カラムがDataFrameに存在するかチェックする関数
def has_denpyou_date_column(df: pd.DataFrame, column_name: str = "伝票日付") -> bool:
    """
    DataFrameに伝票日付カラムが存在するか判定
    :param df: チェック対象のDataFrame
    :param column_name: チェックするカラム名（デフォルト: 伝票日付）
    :return: 存在すればTrue、なければFalse
    """
    return column_name in df.columns


