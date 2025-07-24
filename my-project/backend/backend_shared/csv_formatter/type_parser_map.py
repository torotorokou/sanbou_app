import pandas as pd

# csv_type_parser_map.py
from backend_shared.utils.dataframe_utils import (
    remove_weekday_parentheses,
    remove_commas_and_convert_numeric,
    parse_str_column,
)


# CSVの整形マップ
type_formatting_map = {
    "datetime": remove_weekday_parentheses,
    "int": remove_commas_and_convert_numeric,
    "float": remove_commas_and_convert_numeric,
    "str": parse_str_column,
}

# CSVの型変換マップ
type_parser_map = {
    "int": lambda df, col: df.assign(
        **{col: pd.to_numeric(df[col], errors="coerce", downcast="integer")}
    ),
    "float": lambda df, col: df.assign(
        **{col: pd.to_numeric(df[col], errors="coerce")}
    ),
    "datetime": lambda df, col: df.assign(
        **{col: pd.to_datetime(df[col], errors="coerce")}
    ),
    "str": lambda df, col: df,  # 追加：str は型変換しない
}
