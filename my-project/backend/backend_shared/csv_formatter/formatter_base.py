import pandas as pd
from abc import ABC, abstractmethod

from backend_shared.utils.dataframe_utils import common_cleaning
from .formatter_core import (
    apply_column_formatting,
    apply_column_type_parsing,
)

from backend_shared.csv_formatter.formatter_config import FormatterConfig


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
        # configからカラム定義を取得
        columns_def = self.config.columns_def if self.config else {}
        if columns_def:
            df = apply_column_formatting(df, columns_def)
            df = apply_column_type_parsing(df, columns_def)
            # ここで集約
            df = resolve_duplicates_by_agg(
                df,
                self.config.unique_keys[0],  # 常に0番目だけ
                self.config.agg_map,
            )

        return df


def resolve_duplicates_by_agg(df, unique_keys, agg_map):
    duplicated_mask = df.duplicated(subset=unique_keys, keep=False)
    if not duplicated_mask.any():
        return df

    dup_df = df[duplicated_mask]
    agg_df = dup_df.groupby(unique_keys, dropna=False).agg(agg_map).reset_index()
    non_dup_df = df[~duplicated_mask]
    result = pd.concat([non_dup_df, agg_df], ignore_index=True)
    return result


