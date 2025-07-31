import pandas as pd
from typing import List, Tuple, Optional
from app.api.services.manage_report_processors.factory_report.utils.logger import (
    app_logger,
)
from app.api.services.manage_report_processors.factory_report.utils.summary_tools import (
    safe_merge_by_keys,
    summary_update_column_if_notna,
)


def apply_negation_filters(
    df: pd.DataFrame, match_df: pd.DataFrame, key_cols: List[str], logger=None
) -> pd.DataFrame:
    """
    match_df の key_cols に `Not値` または `NOT値` があれば、その値を除外するフィルタを df に適用。

    Parameters:
        df (pd.DataFrame): フィルタ対象のデータフレーム
        match_df (pd.DataFrame): フィルタ条件を含むデータフレーム
        key_cols (List[str]): キー列のリスト
        logger: ロガー

    Returns:
        pd.DataFrame: フィルタリング済みのデータフレーム
    """
    filter_conditions = {}
    for col in key_cols:
        if col not in df.columns:
            if logger:
                logger.warning(f"⚠️ データに列 '{col}' が存在しません。スキップします。")
            continue

        if col in match_df.columns:
            unique_vals = match_df[col].dropna().unique()
            neg_vals = [
                v[3:]
                for v in unique_vals
                if isinstance(v, str) and v.lower().startswith("not")
            ]
            if neg_vals:
                filter_conditions[col] = neg_vals
                if logger:
                    logger.info(
                        f"🚫 '{col}' に対して否定フィルタ: {', '.join(neg_vals)} を適用しました"
                    )

    for col, ng_values in filter_conditions.items():
        df = df[~df[col].isin(ng_values)]

    return df


def process_sheet_partition(
    master_csv: pd.DataFrame, sheet_name: str, expected_level: int, logger=None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    指定シートから key_level 一致行と不一致行を分離。

    Parameters:
        master_csv (pd.DataFrame): マスターCSV
        sheet_name (str): シート名
        expected_level (int): 期待するキーレベル
        logger: ロガー

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (一致行, 不一致行)
    """
    sheet_df = (
        master_csv[master_csv["CSVシート名"] == sheet_name].copy()
        if "CSVシート名" in master_csv.columns
        else master_csv.copy()
    )

    if "key_level" in sheet_df.columns:
        # デバッグ情報追加
        print("🔍 process_sheet_partition デバッグ:")
        print(f"  sheet_name: '{sheet_name}'")
        print(f"  expected_level: {expected_level} (型: {type(expected_level)})")
        print(f"  sheet_df の行数: {len(sheet_df)}")
        print(f"  key_level カラムの値: {sheet_df['key_level'].unique()}")
        print(f"  key_level カラムの型: {sheet_df['key_level'].dtype}")
        print(
            f"  key_level の一意な値と型: {[(v, type(v)) for v in sheet_df['key_level'].unique()]}"
        )

        match_df = sheet_df[sheet_df["key_level"] == expected_level].copy()
        remain_df = sheet_df[sheet_df["key_level"] != expected_level].copy()

        print(f"  match_df の行数: {len(match_df)}")
        print(f"  remain_df の行数: {len(remain_df)}")
    else:
        # key_levelカラムがない場合は全体を対象とする
        match_df = sheet_df.copy()
        remain_df = pd.DataFrame()

    return match_df, remain_df


def summary_apply_by_sheet(
    master_csv: pd.DataFrame,
    data_df: pd.DataFrame,
    sheet_name: str,
    key_cols: List[str],
    source_col: str = "正味重量",
    target_col: str = "値",
) -> pd.DataFrame:
    """
    指定されたシートとキー列に基づいて集計処理を適用

    Parameters:
        master_csv (pd.DataFrame): マスターCSV
        data_df (pd.DataFrame): データ
        sheet_name (str): シート名
        key_cols (List[str]): キー列のリスト
        source_col (str): ソース列名
        target_col (str): ターゲット列名

    Returns:
        pd.DataFrame: 処理済みのマスターCSV
    """
    logger = app_logger()
    logger.info(f"▶️ シート: {sheet_name}, キー: {key_cols}, 集計列: {source_col}")

    # デバッグ：入力データの詳細ログ
    logger.info(f"🔍 data_df のカラム: {data_df.columns.tolist()}")
    logger.info(f"🔍 '{source_col}' カラムの存在: {source_col in data_df.columns}")
    if source_col in data_df.columns:
        logger.info(
            f"🔍 '{source_col}' カラムのサンプル値: {data_df[source_col].head().tolist()}"
        )

    # 該当シートの key_level フィルタ
    expected_level = len(key_cols)
    match_df, remain_df = process_sheet_partition(
        master_csv, sheet_name, expected_level, logger
    )

    if match_df.empty:
        logger.info(
            f"⚠️ key_level={expected_level} に一致する行がありません。スキップします。"
        )
        return master_csv

    # not検索を適用（Not値のある行を除外）
    filtered_data_df = apply_negation_filters(
        data_df.copy(), match_df, key_cols, logger
    )

    # デバッグ：フィルタ後のデータ
    logger.info(
        f"🔍 フィルタ後 filtered_data_df のカラム: {filtered_data_df.columns.tolist()}"
    )
    logger.info(
        f"🔍 フィルタ後 '{source_col}' カラムの存在: {source_col in filtered_data_df.columns}"
    )

    # マージ用 key を再定義（Not〇〇を含む列を除外）
    merge_key_cols = []
    for col in key_cols:
        if col in match_df.columns and col in filtered_data_df.columns:
            has_neg = any(
                isinstance(val, str) and val.lower().startswith("not")
                for val in match_df[col].dropna().unique()
            )
            if not has_neg:
                merge_key_cols.append(col)
            else:
                logger.info(f"⚠️ '{col}' に 'Not' 指定があるためマージキーから除外")

    if not merge_key_cols:
        logger.warning("❌ 有効なマージキーが存在しません。処理をスキップします。")
        return master_csv

    # 集計
    if source_col in filtered_data_df.columns:
        logger.info(f"✅ '{source_col}' カラムが存在するため集計処理を実行")
        agg_df = filtered_data_df.groupby(merge_key_cols, as_index=False)[
            [source_col]
        ].sum()

        # マージ
        merged_df = safe_merge_by_keys(match_df, agg_df, merge_key_cols)
        merged_df = summary_update_column_if_notna(merged_df, source_col, target_col)

        # 正味重量の削除
        if source_col in merged_df.columns:
            merged_df.drop(columns=[source_col], inplace=True)

        # 最終結合（元データの他シート + 残余 + マージ結果）
        if "CSVシート名" in master_csv.columns:
            master_others = master_csv[master_csv["CSVシート名"] != sheet_name]
            final_df = pd.concat(
                [master_others, remain_df, merged_df], ignore_index=True
            )
        else:
            final_df = pd.concat([remain_df, merged_df], ignore_index=True)

        return final_df
    else:
        logger.warning(
            f"⚠️ '{source_col}' カラムが存在しないため集計処理をスキップします"
        )
        return master_csv
