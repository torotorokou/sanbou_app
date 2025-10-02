"""Data cleaning utilities wrapper."""
from ._data_cleaning import clean_cd_column as _clean_cd_column, clean_na_strings


def clean_cd_column(df, col: str = "業者CD"):
    return _clean_cd_column(df, col)
