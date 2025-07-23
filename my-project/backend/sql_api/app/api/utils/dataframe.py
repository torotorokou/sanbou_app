import pandas as pd


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
