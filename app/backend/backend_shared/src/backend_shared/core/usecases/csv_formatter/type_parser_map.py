import pandas as pd

# csv_type_parser_map.py
from backend_shared.utils.dataframe_utils import (
    remove_weekday_parentheses,
    remove_commas_and_convert_numeric,
    parse_str_column,
    normalize_code_column,
    NA_STRING_VALUES,
)


def parse_int64_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Int64型（pandasのnullable int型）に変換する共通関数
    先頭ゼロを除去して正規化（例: "000123" → 123）
    
    :param df: 対象DataFrame
    :param col: 変換対象のカラム名
    :return: 変換後のDataFrame
    """
    return df.assign(
        **{
            col: pd.to_numeric(
                df[col]
                .astype(str)
                .str.replace(",", "")
                .str.lstrip("0")  # 先頭ゼロを除去
                .replace(NA_STRING_VALUES, ""),  # 空文字列もNaNとして扱う
                errors="coerce",
            ).astype("Int64")
        }
    )


# CSVの整形マップ
type_formatting_map = {
    "datetime": remove_weekday_parentheses,
    "int": remove_commas_and_convert_numeric,
    "Int64": remove_commas_and_convert_numeric,  # pandasのnullable int型
    "float": remove_commas_and_convert_numeric,
    "str": parse_str_column,
    "code": parse_str_column,  # コード型も文字列の整形を適用
}

# CSVの型変換マップ
type_parser_map = {
    # Int64型（pandasのnullable int型）
    # 先頭ゼロを除去して正規化（例: "000123" → 123）
    "int": parse_int64_column,
    "Int64": parse_int64_column,  # int と同じ処理を共通関数で実現
    "float": lambda df, col: df.assign(
        **{
            col: pd.to_numeric(
                df[col]
                .astype(str)
                .str.replace(",", "")
                .replace(NA_STRING_VALUES, ""),
                errors="coerce",
            )
        }
    ),
    "datetime": lambda df, col: df.assign(
        **{col: pd.to_datetime(df[col], errors="coerce")}
    ),
    "str": lambda df, col: df,  # 追加：str は型変換しない
    "code": normalize_code_column,  # コード型：先頭ゼロを除去して正規化
}
