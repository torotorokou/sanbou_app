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


def dedupe_and_aggregate(
    df: pd.DataFrame, unique_keys: list, agg_map: dict
) -> pd.DataFrame:
    """
    unique_keys: 重複判定に使うカラム
    agg_map: {カラム名: 集約方法}
    1. unique_keysで重複グループを判定
    2. 重複グループごとにagg_mapで1行に集約
    3. 重複が無い行はそのまま返す
    """
    if not unique_keys or not agg_map:
        return df

    # 1. 重複グループID付与
    df = df.copy()
    df["_dup_group_id"] = pd.factorize(
        df[unique_keys].astype(str).agg("-".join, axis=1)
    )[0]

    # 2. 重複グループを抽出
    dup_counts = df["_dup_group_id"].value_counts()
    dup_ids = dup_counts[dup_counts > 1].index
    dup_df = df[df["_dup_group_id"].isin(dup_ids)]

    # 3. 重複グループごとにagg_mapで集約
    if not dup_df.empty:
        agg_df = (
            dup_df.groupby("_dup_group_id", dropna=False).agg(agg_map).reset_index()
        )
    else:
        agg_df = pd.DataFrame(columns=df.columns)

    # 4. 重複のない行
    nondup_df = df[~df["_dup_group_id"].isin(dup_ids)]

    # 5. 結合して不要なカラム削除
    result = pd.concat([nondup_df, agg_df], ignore_index=True)
    result = result.drop(columns=["_dup_group_id"])
    return result
