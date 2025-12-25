"""
CSV Formatter Port

CSV フォーマット処理の抽象インターフェース。
"""

from typing import Protocol

import pandas as pd


class CsvFormatterPort(Protocol):
    """CSV フォーマッターの抽象インターフェース"""

    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrame を整形する

        Args:
            df: 整形対象の DataFrame

        Returns:
            整形済みの DataFrame
        """
        ...


class CsvValidatorPort(Protocol):
    """CSV バリデーターの抽象インターフェース"""

    def validate(self, df: pd.DataFrame) -> tuple[bool, list[str]]:
        """
        DataFrame をバリデーションする

        Args:
            df: バリデーション対象の DataFrame

        Returns:
            (検証結果, エラーメッセージリスト)
        """
        ...
