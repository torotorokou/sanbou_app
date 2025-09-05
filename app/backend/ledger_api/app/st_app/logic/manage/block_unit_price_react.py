# backend/app/st_app/logic/manage/block_unit_price_react.py

import pandas as pd
from typing import Dict, Any

from app.st_app.utils.logger import app_logger
from app.st_app.utils.config_loader import get_template_config
from app.st_app.logic.manage.utils.csv_loader import load_all_filtered_dataframes
from app.st_app.logic.manage.utils.load_template import load_master_and_template
from app.st_app.config.loader.main_path import MainPath
from app.st_app.logic.manage.readers.read_transport_discount import (
    ReadTransportDiscount,
)

from app.st_app.logic.manage.processors.block_unit_price.process0 import (
    make_df_shipment_after_use,
    apply_unit_price_addition,
    apply_transport_fee_by1,
)
from app.st_app.logic.manage.processors.block_unit_price.process2 import (
    apply_transport_fee_by_vendor,
    apply_weight_based_transport_fee,
)


def process(dfs: Dict[str, Any]) -> pd.DataFrame:
    """
    ブロック単価計算の主処理を行う関数（React用）

    Args:
        dfs: 入力データフレーム群

    Returns:
        pd.DataFrame: 計算結果を含むマスターCSV
    """
    logger = app_logger()
    logger.info("▶️ ブロック単価計算処理開始（React版）")

    # --- 設定とマスターデータの読み込み ---
    template_key = "block_unit_price"
    template_config = get_template_config()[template_key]
    template_name = template_config["key"]
    csv_keys = template_config["required_files"]
    logger.info(f"[テンプレート設定読込] key={template_key}, files={csv_keys}")

    # マスターデータ
    config = get_template_config()["block_unit_price"]
    master_path = config["master_csv_path"]["vendor_code"]
    master_csv = load_master_and_template(master_path)

    # 運搬費データ
    mainpath = MainPath()
    reader = ReadTransportDiscount(mainpath)
    df_transport_cost = reader.load_discounted_df()

    # 出荷データ
    df_dict = load_all_filtered_dataframes(dfs, csv_keys, template_name)
    df_shipment = df_dict.get("shipment")

    # データが存在しない場合の処理
    if df_shipment is None:
        logger.error("出荷データが見つかりません")
        return pd.DataFrame()

    # --- 一括処理の実行 ---
    logger.info("▶️ Step1: フィルタリング・単価追加・固定運搬費")
    df_shipment = make_df_shipment_after_use(master_csv, df_shipment)  # フィルタリング
    df_shipment = apply_unit_price_addition(master_csv, df_shipment)  # 単価追加
    df_shipment = apply_transport_fee_by1(df_shipment, df_transport_cost)  # 固定運搬費

    logger.info("▶️ Step2: 運搬費計算と最終処理")
    # React版では対話的な選択を行わず、デフォルト設定で運搬費を適用
    df_shipment = _apply_default_transport_selection(df_shipment, df_transport_cost)

    # 運搬費の計算と適用
    df_shipment = apply_transport_fee_by_vendor(df_shipment, df_transport_cost)
    df_shipment = apply_weight_based_transport_fee(df_shipment, df_transport_cost)

    # ブロック単価の簡易計算と最終処理（React版用の実装）
    logger.info("▶️ Step3: 最終処理とマスターCSV作成")
    master_csv = _create_final_master_csv(df_shipment, master_csv)

    logger.info("▶️ ブロック単価計算処理完了（React版）")
    return master_csv


def _apply_default_transport_selection(
    df_shipment: pd.DataFrame, df_transport: pd.DataFrame
) -> pd.DataFrame:
    """
    React版用のデフォルト運搬業者選択処理

    Streamlit版では対話的に選択していた運搬業者を、
    React版ではデフォルトのルールで自動選択する

    Args:
        df_shipment: 出荷データ
        df_transport: 運搬費データ

    Returns:
        pd.DataFrame: 運搬業者が選択された出荷データ
    """
    logger = app_logger()
    logger.info("▶️ デフォルト運搬業者選択処理")

    # デフォルトの運搬業者選択ロジック
    # 例：最初の運搬業者を選択、または最も安い運搬業者を選択
    if "運搬業者" not in df_shipment.columns:
        # 運搬業者列が存在しない場合、デフォルト値を設定
        if not df_transport.empty and "運搬業者" in df_transport.columns:
            default_vendor = df_transport["運搬業者"].iloc[0]
            df_shipment["運搬業者"] = default_vendor
            logger.info(f"デフォルト運搬業者を設定: {default_vendor}")
        else:
            df_shipment["運搬業者"] = "デフォルト"
            logger.info("運搬費データが不足のため、デフォルト値を設定")

    return df_shipment


def _create_final_master_csv(
    df_shipment: pd.DataFrame, master_csv: pd.DataFrame
) -> pd.DataFrame:
    """
    React版用の最終マスターCSV作成処理

    Args:
        df_shipment: 処理済み出荷データ
        master_csv: マスターデータ

    Returns:
        pd.DataFrame: 最終的なマスターCSV
    """
    logger = app_logger()
    logger.info("▶️ 最終マスターCSV作成処理")

    try:
        # 基本的な合計計算
        if "単価" in df_shipment.columns and "数量" in df_shipment.columns:
            df_shipment["合計金額"] = pd.to_numeric(
                df_shipment["単価"], errors="coerce"
            ).fillna(0) * pd.to_numeric(df_shipment["数量"], errors="coerce").fillna(0)

        # 運搬費を含む総合計算
        if "運搬費" in df_shipment.columns:
            df_shipment["総合計"] = df_shipment.get("合計金額", 0) + pd.to_numeric(
                df_shipment["運搬費"], errors="coerce"
            ).fillna(0)

        # 日付情報の追加
        if "伝票日付" in df_shipment.columns and not df_shipment.empty:
            first_date = df_shipment["伝票日付"].iloc[0]
            logger.info(f"処理日付: {first_date}")

        # マスターCSVが空の場合は出荷データを返す
        if master_csv.empty:
            logger.warning("マスターCSVが空のため、処理済み出荷データを返します")
            return df_shipment

        # マスターCSVに集計データを追加する基本的な処理
        # 業者別、品目別の集計など
        if "業者名" in df_shipment.columns:
            summary_by_vendor = (
                df_shipment.groupby("業者名")
                .agg({"合計金額": "sum", "運搬費": "sum", "総合計": "sum"})
                .reset_index()
            )

            logger.info(f"業者別集計結果: {len(summary_by_vendor)}件")

            # マスターCSVと結合または更新
            if "業者名" in master_csv.columns:
                master_csv = master_csv.merge(
                    summary_by_vendor, on="業者名", how="left", suffixes=("", "_new")
                )
            else:
                # マスターCSVに業者別集計を追加
                master_csv = pd.concat(
                    [master_csv, summary_by_vendor], ignore_index=True
                )

        return master_csv

    except Exception as e:
        logger.error(f"最終マスターCSV作成中にエラーが発生: {e}")
        # エラー時は元のマスターCSVを返す
        return master_csv
