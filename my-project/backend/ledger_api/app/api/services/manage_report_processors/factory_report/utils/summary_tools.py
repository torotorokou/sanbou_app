import pandas as pd
from typing import List, Any, Union
from app.api.services.manage_report_processors.factory_report.utils.logger import (
    app_logger,
)


def write_sum_to_target_cell(
    df: pd.DataFrame,
    target_keys: List[str],
    target_values: List[Any],
    value_column: str = "値",
) -> pd.DataFrame:
    """
    テンプレートの「合計」セルに値を書き込む。
    指定したキー構成に対応するセルに、合計値を設定する汎用関数。

    Parameters:
        df : pd.DataFrame
            対象データフレーム（通常はマスターCSV）
        target_keys : List[str]
            キー列名のリスト（例: ["業者CD", "業者名", "品名"]）
        target_values : List[Any]
            条件として一致させたい値のリスト（例: ["合計", None, None]）
        value_column : str
            合計を算出する対象の値列（デフォルト: "値"）

    Returns:
        pd.DataFrame : 合計が反映されたDataFrame
    """
    df = df.copy()
    total = pd.to_numeric(df[value_column], errors="coerce").sum()

    # 条件に一致する行を検索して値を設定
    mask = pd.Series([True] * len(df), index=df.index)
    for key, value in zip(target_keys, target_values):
        if value is not None:
            mask &= df[key] == value
        else:
            mask &= df[key].isna()

    if mask.any():
        df.loc[mask, value_column] = total

    return df


def summarize_value_by_cell_with_label(
    df: pd.DataFrame,
    value_col: str = "値",
    cell_col: str = "セル",
    label_col: str = "有価名",
    fill_missing_cells: bool = False,
) -> pd.DataFrame:
    """
    セルごとに数値を合計し、ラベル・セルロック・順番を付けて返す。
    セルがNaNの行はgroupbyから自動的に除外されます。

    Parameters:
        df (pd.DataFrame): 対象データフレーム
        value_col (str): 値列名
        cell_col (str): セル列名
        label_col (str): ラベル列名
        fill_missing_cells (bool): 欠損セルを補完するかどうか

    Returns:
        pd.DataFrame: 集計済みデータフレーム
    """
    df = df.copy()

    # セルごとに数値を合計
    numeric_values = pd.to_numeric(df[value_col], errors="coerce").fillna(0)
    df[value_col] = numeric_values

    # セルごとにグループ化して合計
    if cell_col in df.columns:
        # セルがNaNでない行のみを対象にグループ化
        valid_cells = df[df[cell_col].notna()]
        if not valid_cells.empty:
            grouped = (
                valid_cells.groupby(cell_col)
                .agg(
                    {
                        value_col: "sum",
                        label_col: "first",  # 最初の値を取得
                    }
                )
                .reset_index()
            )

            # 元のデータフレームの他の列も保持
            if "セルロック" in df.columns:
                cell_locks = (
                    valid_cells.groupby(cell_col)["セルロック"].first().reset_index()
                )
                grouped = grouped.merge(cell_locks, on=cell_col, how="left")

            if "順番" in df.columns:
                orders = valid_cells.groupby(cell_col)["順番"].first().reset_index()
                grouped = grouped.merge(orders, on=cell_col, how="left")

            return grouped

    return df


def safe_merge_by_keys(
    master_df: pd.DataFrame,
    data_df: pd.DataFrame,
    key_cols: List[str],
    how: str = "left",
) -> pd.DataFrame:
    """
    指定した複数のキー列を使って、安全にマージする関数。
    マスター側のキー列に欠損値（NaN）がある行はマージ対象から除外される。

    Parameters
    ----------
    master_df : pd.DataFrame
        マージ元（テンプレート）
    data_df : pd.DataFrame
        マージ対象のデータ
    key_cols : List[str]
        結合に使用するキー列（1〜3列想定）
    how : str
        マージ方法（デフォルト: "left"）

    Returns
    -------
    pd.DataFrame
        マージ済みのDataFrame（未マージ行も含まれる）
    """

    # ① キーに空欄がある行を除外してマージ（空文字は有効なキーとして扱う）
    master_valid = master_df.dropna(subset=key_cols)
    data_valid = data_df.dropna(subset=key_cols)

    if master_valid.empty or data_valid.empty:
        return master_df.copy()

    merged = pd.merge(master_valid, data_valid, on=key_cols, how=how)

    # ② キーが不完全（NaN含む）な行を保持して復元
    master_skipped = master_df[master_df[key_cols].isna().any(axis=1)]

    # ③ マージしたものと未マージのものを結合して返す
    final_df = pd.concat([merged, master_skipped], ignore_index=True)

    return final_df


def summary_update_column_if_notna(
    df: pd.DataFrame, source_col: str, target_col: str
) -> pd.DataFrame:
    """
    ソース列がNaNでない場合のみターゲット列を更新

    Parameters:
        df (pd.DataFrame): 対象データフレーム
        source_col (str): ソース列名
        target_col (str): ターゲット列名

    Returns:
        pd.DataFrame: 更新されたデータフレーム
    """
    df = df.copy()

    # ソース列が存在するかチェック
    if source_col not in df.columns:
        print(f"警告: ソース列 '{source_col}' が存在しません。更新をスキップします。")
        return df

    # ターゲット列が存在しない場合は作成
    if target_col not in df.columns:
        df[target_col] = None

    mask = df[source_col].notna()
    df.loc[mask, target_col] = df.loc[mask, source_col]
    return df
