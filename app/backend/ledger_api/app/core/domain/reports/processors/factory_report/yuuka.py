import pandas as pd

from app.infra.report_utils.formatters import (
    summarize_value_by_cell_with_label,
)
from app.core.domain.reports.processors.factory_report.summary import (
    summary_apply_by_sheet,
)
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


def process_yuuka(df_yard: pd.DataFrame, df_shipment: pd.DataFrame, master_csv: pd.DataFrame = None) -> pd.DataFrame:
    """
    有価データを処理する。
    
    Args:
        df_yard: ヤードデータ
        df_shipment: 出荷データ
        master_csv: 有価マスターCSV（事前読み込み済み）。Noneの場合は空データを返す。
    
    Returns:
        pd.DataFrame: 整形済みの有価帳票
    
    Notes:
        - Step 5最適化: master_csvを引数で受け取ることでI/O削減
    """

    # --- ① マスターCSVの確認 ---
    if master_csv is None or master_csv.empty:
        logger.warning(
            "マスターCSVが提供されていません（有価）。空データで継続します。"
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
    """
    最適化: master_csvのcopy()を削減（summary_apply_by_sheetが新しいDataFrameを返すため不要）
    """
    df_map = {"ヤード": df_yard, "出荷": df_shipment}

    sheet_key_pairs = [
        ("ヤード", ["品名"]),
        ("出荷", ["品名"]),
        ("出荷", ["業者名", "品名"]),
        ("出荷", ["現場名", "業者名", "品名"]),
    ]

    master_csv_updated = master_csv

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
