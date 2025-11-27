"""
安全なCSVファイル読み込みユーティリティ

CSVファイルを安全に読み込むためのユーティリティクラスと関数群です。
エンコーディング処理、欠損値処理、エラーハンドリングを統合的に行います。
"""

import pandas as pd

from backend_shared.adapters.presentation.response_error import CSVReadErrorResponse
from backend_shared.adapters.presentation.response_base import ErrorApiResponse


class SafeCsvReader:
    """
    安全なCSVファイルリーダー

    CSVファイルを安全に読み込むためのユーティリティクラスです。
    欠損値の適切な処理、エンコーディング対応、空白文字の保持などを行います。

    特徴:
    - <NA>やNaN, Noneなどは欠損値として扱う
    - 空白文字（""）はそのまま空白として保持
    - エンコーディングやその他のオプションも柔軟に指定可能
    """

    def __init__(self, na_values=None, keep_default_na=False, encoding="utf-8"):
        """
        CSVリーダーの初期化

        Args:
            na_values (list, optional): 欠損値として扱う値のリスト
            keep_default_na (bool): pandasのデフォルトNA検出を使用するかどうか
            encoding (str): ファイルエンコーディング
        """
        # 欠損値として扱う値を定義（空白文字は含めない）
        if na_values is None:
            na_values = ["<NA>", "NaN", "nan", "None"]
        self.na_values = na_values

        # pandasのデフォルトNA検出を無効化（空白セルをNaNにしないため）
        self.keep_default_na = keep_default_na
        self.encoding = encoding

    def read(self, file_obj, **kwargs):
        """
        CSVファイルを読み込んでDataFrameを返す

        Args:
            file_obj: ファイルオブジェクト
            **kwargs: pandas.read_csvの追加パラメータ

        Returns:
            pd.DataFrame: 読み込まれたDataFrame
        """
        return pd.read_csv(
            file_obj,
            na_values=self.na_values,
            keep_default_na=self.keep_default_na,
            encoding=self.encoding,
            **kwargs,
        )


def read_csv_files(files: dict) -> tuple[dict | None, ErrorApiResponse | None]:
    """
    複数のCSVファイルを一括読み込み

    アップロードされた複数のCSVファイルを安全に読み込み、
    DataFrameの辞書として返します。エラーが発生した場合は
    エラーレスポンスを返します。

    Args:
        files (dict): ファイル名をキーとするUploadFileの辞書

    Returns:
        tuple: (DataFrameの辞書, エラーレスポンスまたはNone)
            成功時: (DataFrameの辞書, None)
            失敗時: (None, エラーレスポンス)
    """
    # 安全なCSVリーダーを初期化
    csv_reader = SafeCsvReader()
    dfs = {}

    # 各ファイルを順次読み込み
    for k, f in files.items():
        try:
            # ファイルポインタをリセット
            f.file.seek(0)
            # CSVファイルを読み込み
            dfs[k] = csv_reader.read(f.file)
            # ファイルポインタを再度リセット（後続処理のため）
            f.file.seek(0)
        except Exception as e:
            print(f"[ERROR] reading CSV for {k}: {e}")
            # エラー発生時はエラーレスポンスを返す
            return None, CSVReadErrorResponse(file_name=k, exception=e)

    # 全ファイル読み込み成功
    return dfs, None
