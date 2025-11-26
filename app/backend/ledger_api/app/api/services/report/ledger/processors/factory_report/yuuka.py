import pandas as pd

from app.api.services.report.utils import (
    app_logger,
    get_template_config,
)
from app.api.services.report.utils import load_master_and_template
from app.infra.report_utils.formatters import (
    summarize_value_by_cell_with_label,
)
from app.api.services.report.ledger.processors.factory_report.summary import (
    summary_apply_by_sheet,
)


def process_yuuka(df_yard: pd.DataFrame, df_shipment: pd.DataFrame) -> pd.DataFrame:
    logger = app_logger()

    # --- ① マスターCSVの読み込み ---
    config = get_template_config()["factory_report"]
    master_path = config["master_csv_path"]["yuuka"]
    try:
        master_csv = load_master_and_template(master_path)
    except Exception as e:
        logger.warning(
            f"マスターCSVの読み込みに失敗しました（有価）。パス: {master_path}。理由: {e}。空データで継続します。"
        )
        # 後段の format_table で参照される列を用意
        return pd.DataFrame(columns=["大項目", "セル", "値", "セルロック", "順番", "有価名"])  # 空

    # --- ② 有価の値集計処理（df_yard + df_shipmentを使用） ---
    updated_master_csv = apply_yuuka_summary(master_csv, df_yard, df_shipment)

    # --- ③ 品目単位で有価名をマージし、合計を計算 ---
    updated_with_sum = summarize_value_by_cell_with_label(
        updated_master_csv, cell_col="有価名", label_col="セル"
    )

    # フォーマット修正
    final_df = format_table(updated_with_sum)

    logger.info("✅ 出荷有価の帳票生成が完了しました。")
    return final_df


def apply_yuuka_summary(master_csv, df_yard, df_shipment):
    df_map = {"ヤード": df_yard, "出荷": df_shipment}

    sheet_key_pairs = [
        ("ヤード", ["品名"]),
        ("出荷", ["品名"]),
        ("出荷", ["業者名", "品名"]),
        ("出荷", ["現場名", "業者名", "品名"]),
    ]

    master_csv_updated = master_csv.copy()

    for sheet_name, key_cols in sheet_key_pairs:
        data_df = df_map[sheet_name]

        master_csv_updated = summary_apply_by_sheet(
            master_csv=master_csv_updated,
            data_df=data_df,
            sheet_name=sheet_name,
            key_cols=key_cols,
        )

    return master_csv_updated


def format_table(master_csv: pd.DataFrame) -> pd.DataFrame:
    # 必要列を抽出
    format_df = master_csv[["有価名", "セル", "値", "セルロック", "順番"]].copy()

    # 置換
    format_df.rename(columns={"有価名": "大項目"}, inplace=True)

    # カテゴリ列を追加
    format_df["カテゴリ"] = "有価"

    return format_df
