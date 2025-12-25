"""
CSVフォーマッター基底クラス

CSVデータのフォーマット処理を行う基底クラスと共通フォーマッタークラスです。
前処理、個別処理、後処理の3段階でデータを変換します。
"""

from abc import ABC, abstractmethod

import pandas as pd
from backend_shared.core.usecases.csv_formatter.formatter_config import FormatterConfig
from backend_shared.core.usecases.csv_formatter.formatter_core import (
    apply_column_cleaning,
    apply_column_type_parsing,
    dedupe_and_aggregate,
)
from backend_shared.utils.dataframe_utils import common_cleaning


# =========================
# 抽象基底クラス
# =========================
class BaseCSVFormatter(ABC):
    """
    CSVフォーマッター抽象基底クラス

    すべてのCSVフォーマッターが実装すべきインターフェースを定義します。
    """

    @abstractmethod
    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameをフォーマット

        Args:
            df (pd.DataFrame): 入力DataFrame

        Returns:
            pd.DataFrame: フォーマット済みDataFrame
        """
        pass


# =========================
# 共通フォーマッタークラス
# =========================
class CommonCSVFormatter(BaseCSVFormatter):
    """
    共通CSVフォーマッター

    CSVデータの共通フォーマット処理を実行するクラスです。
    前処理→個別処理→後処理の3段階でデータを変換します。
    """

    def __init__(self, config: FormatterConfig):
        """
        フォーマッターの初期化

        Args:
            config (FormatterConfig): フォーマット設定
        """
        self.config = config
        print(f"{self.__class__.__name__} initialized")

    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        フォーマット処理の実行

        前処理→個別処理→後処理の順でDataFrameを変換します。

        Args:
            df (pd.DataFrame): 入力DataFrame

        Returns:
            pd.DataFrame: フォーマット済みDataFrame
        """
        # 1. 共通前処理（空白除去など）
        df = self.common_preprocess(df)

        # 2. 個別処理（サブクラスで実装）
        df = self.individual_process(df)

        # 3. 共通後処理（型変換、重複除去など）
        df = self.common_postprocess(df)

        return df

    def common_preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        共通前処理

        空白文字の除去など、すべてのCSVに共通する前処理を実行します。

        Args:
            df (pd.DataFrame): 入力DataFrame

        Returns:
            pd.DataFrame: 前処理済みDataFrame
        """
        # 空白除去処理
        df = common_cleaning(df)
        return df

    def individual_process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        個別処理

        各CSVタイプ固有の処理を実行します。
        サブクラスで必要に応じてオーバーライドしてください。

        Args:
            df (pd.DataFrame): 入力DataFrame

        Returns:
            pd.DataFrame: 個別処理済みDataFrame
        """
        # デフォルトは何もしない（子クラスで上書き）
        return df

    def common_postprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        共通後処理

        カラムクリーニング、型変換、重複除去・集約処理を実行します。

        Args:
            df (pd.DataFrame): 入力DataFrame

        Returns:
            pd.DataFrame: 後処理済みDataFrame
        """
        # 設定からカラム定義を取得
        columns_def = self.config.columns_def if self.config else {}

        if columns_def:
            # カラム単位のクリーニング処理
            df = apply_column_cleaning(df, columns_def)

            # カラム型変換処理
            df = apply_column_type_parsing(df, columns_def)

            # 重複データの除去と集約処理
            print("resoliving duplicates by aggregation")
            df = dedupe_and_aggregate(
                df,
                self.config.unique_keys,
                self.config.agg_map,
            )

        return df
