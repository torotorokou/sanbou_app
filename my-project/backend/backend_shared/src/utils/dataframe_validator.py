"""
DataFrameのバリデーション処理を行う関数群モジュール。
初心者にも分かりやすいように日本語でコメント・ドックストリングを記載しています。
"""

import pandas as pd
from typing import Optional

from backend_shared.src.utils.dataframe_utils import (
    has_denpyou_date_column,
    remove_weekday_parentheses,
)


def check_missing_file(file_inputs: dict[str, Optional[object]]) -> Optional[str]:
    """
    ファイル入力のうち、未入力のものがあればそのキー（CSV種別名）を返す。
    すべて入力されていればNoneを返す。

    :param file_inputs: {csv_type: file_object or None}
    :return: 未入力のcsv_type名、またはNone
    """
    for csv_type, file in file_inputs.items():
        if file is None:
            return csv_type
    return None


def check_required_columns(
    dfs: dict[str, pd.DataFrame],
    required_columns: dict[str, list[str]],
) -> tuple[bool, str, list[str]]:
    """
    各DataFrameに必須カラムが存在するかをチェック。
    1つでも不足があればFalseと不足カラム情報を返す。

    :param dfs: {csv_type: DataFrame}
    :param required_columns: {csv_type: [必須カラム名, ...]}
    :return: (全てOKならTrue, 問題のcsv_type, 不足カラムリスト)
    """
    for csv_type, df in dfs.items():
        required = required_columns.get(csv_type, [])
        missing = [col for col in required if col not in df.columns]
        if missing:
            return False, csv_type, missing
    return True, "", []


def check_field_exists(dfs: dict[str, pd.DataFrame], field_name: str) -> Optional[str]:
    """
    全てのDataFrameに指定カラムが存在するかを確認。
    存在しない場合はそのcsv_type名を返す。

    :param dfs: {csv_type: DataFrame}
    :param field_name: チェックするカラム名
    :return: 存在しないcsv_type名、またはNone
    """
    for csv_type, df in dfs.items():
        if field_name not in df.columns:
            return csv_type
    return None


def check_field_consistency(
    dfs: dict[str, pd.DataFrame], field_name: str
) -> tuple[bool, dict[str, set]]:
    """
    指定カラムの値の一致性を確認。

    :param dfs: {csv_type: DataFrame}
    :param field_name: チェックするカラム名
    :return: (全て一致しているか, 各csv_typeごとの値セット)
    """
    values_by_type = {}
    for csv_type, df in dfs.items():
        if field_name not in df.columns:
            return False, {}

        df_proc = df.copy()
        if field_name == "伝票日付":
            df_proc = remove_weekday_parentheses(df_proc, field_name)

        values = set(df_proc[field_name].dropna().unique())
        values_by_type[csv_type] = values

    all_values = list(values_by_type.values())
    values_match = all(values == all_values[0] for values in all_values)
    return values_match, values_by_type


def check_denpyou_date_exists(dfs: dict[str, pd.DataFrame]) -> Optional[str]:
    """
    各DataFrameに「伝票日付」カラムが存在するかをチェック。
    存在しない場合はそのcsv_type名を返す。

    :param dfs: {csv_type: DataFrame}
    :return: 「伝票日付」カラムがないcsv_type名、またはNone
    """
    for name, df in dfs.items():
        if not has_denpyou_date_column(df):
            return name
    return None


def check_denpyou_date_consistency(
    dfs: dict[str, pd.DataFrame],
) -> tuple[bool, dict[str, set]]:
    """
    各DataFrameの「伝票日付」カラムの値の整合性をチェック。
    例：複数ファイル間で日付が一致しているか等。

    :param dfs: {csv_type: DataFrame}
    :return: (整合性OKならTrue, 詳細情報dict)
    """
    return check_field_consistency(dfs, "伝票日付")
