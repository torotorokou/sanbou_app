import pandas as pd
from app.api.services.manage_report_processors.factory_report.utils.logger import (
    app_logger,
    debug_logger,
)
from app.api.services.manage_report_processors.factory_report.utils.config_loader import (
    get_template_config,
)
from app.api.services.manage_report_processors.factory_report.utils.csv_loader import (
    load_all_filtered_dataframes,
)
from app.api.services.manage_report_processors.factory_report.processors.factory_report_shobun import (
    process_shobun,
)
from app.api.services.manage_report_processors.factory_report.processors.factory_report_yuuka import (
    process_yuuka,
)
from app.api.services.manage_report_processors.factory_report.processors.factory_report_yard import (
    process_yard,
)
from app.api.services.manage_report_processors.factory_report.processors.make_cell_num import (
    make_cell_num,
)
from app.api.services.manage_report_processors.factory_report.processors.make_label import (
    make_label,
)
from app.api.services.manage_report_processors.factory_report.utils.excel_tools import (
    sort_by_cell_row,
)
from app.api.services.manage_report_processors.factory_report.processors.etc import (
    generate_summary_dataframe,
    upsert_summary_row,
    date_format,
)

# from logic.manage.utils.load_template import load_master_and_template
# from utils.date_tools import to_japanese_era, to_japanese_month_day
# from utils.value_setter import set_value_fast, set_value_fast_safe


def factory_report_main_process(dfs: dict) -> pd.DataFrame:
    """
    工場日報テンプレート用のメイン処理関数。
    各種CSVデータを読み込み、処分・有価・ヤード等の処理を適用し、
    最終的な工場日報データフレームを返します。
    Parameters
    ----------
    dfs : dict
        各CSVのデータフレーム辞書
    Returns
    -------
    pd.DataFrame
        統合・加工済みの工場日報データ
    """

    logger = app_logger()
    deb_logger = debug_logger()

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

    # --- 必要なデータフレームの存在確認 ---
    if df_shipment is None:
        logger.error("出荷データ (shipment) が見つかりません。")
        raise ValueError("出荷データ (shipment) が見つかりません。")

    if df_yard is None:
        logger.error("ヤードデータ (yard) が見つかりません。")
        raise ValueError("ヤードデータ (yard) が見つかりません。")

    # --- 個別処理 ---
    logger.info("▶️ 出荷処分データ処理開始")

    master_csv_shobun = process_shobun(df_shipment)

    logger.info("▶️ 出荷有価データ処理開始")

    master_csv_yuka = process_yuuka(df_yard, df_shipment)

    logger.info("▶️ 出荷ヤードデータ処理開始")
    master_csv_yard = process_yard(df_yard, df_shipment)

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
