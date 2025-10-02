"""
工場日報（factory_report）メイン処理

本モジュールは、出荷・ヤード関連のCSVを読み込み、
処分・有価・ヤードの個別処理を適用して、工場日報の出力データフレームを生成します。

主な処理フロー:
    1) 必要CSVを読み込み、存在チェック
    2) 個別処理（処分・有価・ヤード）を適用
    3) 各処理結果を結合し、セル番号やラベルを付与
    4) 合計行の生成や日付挿入を行い、セル行順に整列して返却
"""

import pandas as pd
from app.st_app.utils.logger import app_logger
from app.st_app.utils.config_loader import get_template_config
from app.st_app.logic.manage.utils.csv_loader import load_all_filtered_dataframes
from app.st_app.logic.manage.processors.factory_report.factory_report_shobun import (
    process_shobun,
)
from app.st_app.logic.manage.processors.factory_report.factory_report_yuuka import (
    process_yuuka,
)
from app.st_app.logic.manage.processors.factory_report.factory_report_yard import (
    process_yard,
)
from app.st_app.logic.manage.processors.factory_report.make_cell_num import (
    make_cell_num,
)
from app.st_app.logic.manage.processors.factory_report.make_label import make_label
from app.st_app.logic.manage.utils.excel_tools import sort_by_cell_row
from app.st_app.logic.manage.processors.factory_report.etc import (
    generate_summary_dataframe,
    date_format,
)


def process(dfs: dict) -> pd.DataFrame:
    """
    工場日報テンプレート用のメイン処理関数。

    - 入力: dfs（キー: ファイル識別子, 値: pandas.DataFrame）
    - 出力: 工場日報の最終DataFrame
    - 備考: CSVが欠落している場合は該当処理をスキップします。
    """

    logger = app_logger()
    # deb_logger = debug_logger()  # 詳細デバッグが必要な場合に活用

    # --- テンプレート設定の取得 ---
    template_key = "factory_report"
    template_config = get_template_config()[template_key]
    template_name = template_config["key"]
    csv_keys = template_config["required_files"]
    logger.info(f"[テンプレート設定読込] key={template_key}, files={csv_keys}")

    # --- CSVの読み込み ---
    df_dict = load_all_filtered_dataframes(dfs, csv_keys, template_name)
    df_shipment = df_dict.get("shipment")
    df_yard = df_dict.get("yard")

    # --- DataFrameの存在確認（一括チェック） ---
    has_shipment = df_shipment is not None and not df_shipment.empty
    has_yard = df_yard is not None and not df_yard.empty

    if not has_shipment:
        logger.error("出荷データ(shipment)が存在しないか空です。")
    if not has_yard:
        logger.error("ヤードデータ(yard)が存在しないか空です。")

    # --- 個別処理 ---
    logger.info("▶️ 出荷処分データ処理開始")
    if has_shipment and df_shipment is not None:
        master_csv_shobun = process_shobun(df_shipment)
    else:
        logger.warning("出荷データが無いため、処分データ処理をスキップします。")
        master_csv_shobun = pd.DataFrame()

    logger.info("▶️ 出荷有価データ処理開始")
    if has_yard and has_shipment and df_yard is not None and df_shipment is not None:
        master_csv_yuka = process_yuuka(df_yard, df_shipment)
    else:
        logger.warning("必要データが不足のため、有価データ処理をスキップします。")
        master_csv_yuka = pd.DataFrame()

    logger.info("▶️ 出荷ヤードデータ処理開始")
    if has_yard and has_shipment and df_yard is not None and df_shipment is not None:
        master_csv_yard = process_yard(df_yard, df_shipment)
    else:
        logger.warning("必要データが不足のため、ヤードデータ処理をスキップします。")
        master_csv_yard = pd.DataFrame()

    # --- 結合 ---
    logger.info("🧩 各処理結果を結合中...")
    combined_df = pd.concat(
        [master_csv_yuka, master_csv_shobun, master_csv_yard], ignore_index=True
    )

    # セル番号の設定
    combined_df = make_cell_num(combined_df)

    # ラベルの追加
    combined_df = make_label(combined_df)

    # --- 合計・総合計行の追加/更新 ---
    combined_df = generate_summary_dataframe(combined_df)

    # 日付の挿入
    combined_df = date_format(combined_df, df_shipment)

    # --- セル行順にソート ---
    combined_df = sort_by_cell_row(combined_df, cell_col="セル")

    # --- インデックスをリセットして返す ---
    return combined_df.reset_index(drop=True)
