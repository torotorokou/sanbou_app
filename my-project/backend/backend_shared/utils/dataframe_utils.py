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


# 伝票日付カラムがDataFrameに存在するかチェックする関数
def has_denpyou_date_column(df: pd.DataFrame, column_name: str = "伝票日付") -> bool:
    """
    DataFrameに伝票日付カラムが存在するか判定
    :param df: チェック対象のDataFrame
    :param column_name: チェックするカラム名（デフォルト: 伝票日付）
    :return: 存在すればTrue、なければFalse
    """
    return column_name in df.columns


def common_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """
    全てのカラム名・文字列データから、
    ・前後および内部の半角スペース（" "）
    ・前後および内部の全角スペース（"　"）
    を全て除去する。
    """
    # カラム名の空白除去
    df.columns = [col.strip().replace(" ", "").replace("　", "") for col in df.columns]

    # 各object型カラムの全スペース除去
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(" ", "", regex=False)  # 半角スペース全削除
            .str.replace("　", "", regex=False)  # 全角スペース全削除
        )
    return df
