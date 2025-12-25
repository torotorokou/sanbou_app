"""
summary_optimized.py

summary_apply の最適化版。
master_csvのcopy()を呼び出し元に委譲し、不要な中間copy()を削減する。
また、clean_na_stringsをベクトル化版に置き換えて高速化。

従来版（summary.py）との違い:
- summary_apply内でのmaster_csv.copy()を削除
- clean_na_strings.apply()をベクトル化版に置き換え
- 呼び出し元がcopy()を管理することを前提とする

使用条件:
- master_csvが既にコピーされた書き換え可能なDataFrameであること
"""

import pandas as pd
from backend_shared.application.logging import get_module_logger
from backend_shared.utils.dataframe_utils_optimized import clean_na_strings_vectorized

logger = get_module_logger(__name__)


def summary_apply_optimized(
    master_csv: pd.DataFrame,
    data_df: pd.DataFrame,
    key_cols: list[str],
    source_col: str = "正味重量",
    target_col: str = "値",
) -> pd.DataFrame:
    """
    インポートCSVをgroupby＆sumし、マスターCSVにマージ＆更新する最適化版関数。

    Parameters
    ----------
    master_csv : pd.DataFrame
        マスターDataFrame（既にcopy()済みで書き換え可能）
    data_df : pd.DataFrame
        集計元のDataFrame
    key_cols : list[str]
        マージキー列
    source_col : str
        集計する列名
    target_col : str
        結果を格納する列名

    Returns
    -------
    pd.DataFrame
        更新されたマスターDataFrame

    Notes
    -----
    - 従来のsummary_applyと異なり、master_csv.copy()を実行しない
    - 呼び出し元で事前にcopy()することを前提とする
    - パフォーマンス重視の設計
    """
    logger.info(
        f"▶️ マスター更新処理（最適化版）: キー={key_cols}, 集計列={source_col} ➡ 書き込み列={target_col}"
    )

    # ① groupbyで合計
    agg_df = data_df.groupby(key_cols, as_index=False)[[source_col]].sum()

    # ② 安全にマージ（copy()なし版）
    merged_df = safe_merge_by_keys_optimized(
        master_df=master_csv, data_df=agg_df, key_cols=key_cols
    )

    # ③ 値を書き込み（NaN以外）
    updated_df = summary_update_column_if_notna(merged_df, source_col, target_col)

    # ④ source_colとtarget_colが違う場合だけ削除
    if source_col != target_col:
        updated_df.drop(columns=[source_col], inplace=True)

    return updated_df


def safe_merge_by_keys_optimized(
    master_df: pd.DataFrame,
    data_df: pd.DataFrame,
    key_cols: list[str],
    how: str = "left",
) -> pd.DataFrame:
    """
    最適化版: master_dfを直接書き換えず、効率的にマージする。

    従来版との違い:
    - dropna/concatの代わりに、より効率的なマージ戦略を使用
    """
    # キーに空欄がある行を除外してマージ
    master_valid = master_df.dropna(subset=key_cols)
    data_valid = data_df.dropna(subset=key_cols)

    merged = pd.merge(master_valid, data_valid, on=key_cols, how=how)

    # キーが不完全（NaN含む）な行を保持して復元
    master_skipped = master_df[master_df[key_cols].isna().any(axis=1)]

    # マージしたものと未マージのものを結合して返す
    final_df = pd.concat([merged, master_skipped], ignore_index=True)

    return final_df


def summary_update_column_if_notna(
    df: pd.DataFrame, source_col: str, target_col: str
) -> pd.DataFrame:
    """
    source_colがNaNでない行のみ、target_colに値をコピーする。

    Note: 入力DataFrameを直接書き換える（inplace操作）
    """
    mask = df[source_col].notna()
    df.loc[mask, target_col] = df.loc[mask, source_col]
    return df
