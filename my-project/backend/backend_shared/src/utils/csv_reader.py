import pandas as pd


class SafeCsvReader:
    """
    CSVファイルを安全に読み込むためのユーティリティクラス。
    - <NA>やNaN, Noneなどは欠損値として扱う
    - 空白文字（""）はそのまま空白として保持
    - エンコーディングやその他のオプションも柔軟に指定可能
    """

    def __init__(self, na_values=None, keep_default_na=False, encoding="utf-8"):
        # <NA>やNaN, Noneは欠損値扱い、空白（""）はそのまま空白として保持
        # ここでna_valuesに""を追加しないことで、空白セルはNaNにならず空白のまま
        if na_values is None:
            na_values = ["<NA>", "NaN", "nan", "None"]
        self.na_values = na_values
        self.keep_default_na = (
            keep_default_na  # 必ずFalseで、pandasのデフォルトNA検出を無効化
        )
        self.encoding = encoding

    def read(self, file_obj, **kwargs):
        return pd.read_csv(
            file_obj,
            na_values=self.na_values,
            keep_default_na=self.keep_default_na,
            encoding=self.encoding,
            **kwargs,
        )
