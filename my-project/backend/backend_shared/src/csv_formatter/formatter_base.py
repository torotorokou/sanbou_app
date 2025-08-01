import pandas as pd
from abc import ABC, abstractmethod

from backend_shared.src.utils.dataframe_utils import common_cleaning
from backend_shared.src.csv_formatter.formatter_core import (
    apply_column_formatting,
    apply_column_type_parsing,
    dedupe_and_aggregate,
)

from backend_shared.src.csv_formatter.formatter_config import FormatterConfig


# =========================
# 共通クラス・ABC
# =========================
class BaseCSVFormatter(ABC):
    @abstractmethod
    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        pass


# =========================
# 親クラスで共通処理を定義
# =========================
class CommonCSVFormatter(BaseCSVFormatter):
    def __init__(self, config: FormatterConfig):
        self.config = config
        print(f"{self.__class__.__name__} initialized")

    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.common_preprocess(df)
        df = self.individual_process(df)
        df = self.common_postprocess(df)
        return df

    def common_preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        # 空白除去
        df = common_cleaning(df)
        return df

    def individual_process(self, df: pd.DataFrame) -> pd.DataFrame:
        # デフォルトは何もしない（子クラスで上書き）
        return df

    def common_postprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        # print(columns_def)
        # configからカラム定義を取得
        columns_def = self.config.columns_def if self.config else {}
        if columns_def:
            df = apply_column_formatting(df, columns_def)
            df = apply_column_type_parsing(df, columns_def)
            # ここで集約
            print("resoliving duplicates by aggregation")
            df = dedupe_and_aggregate(
                df,
                self.config.unique_keys,
                self.config.agg_map,
            )

        return df
