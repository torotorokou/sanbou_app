import pandas as pd
from app.core.domain.reports.processors.factory_report.summary import (
    summary_apply_by_sheet,
)
from app.infra.report_utils.formatters import summarize_value_by_cell_with_label
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


def process_yard(
    df_yard: pd.DataFrame, df_shipment: pd.DataFrame, master_csv: pd.DataFrame = None
) -> pd.DataFrame:
    """
    ヤードデータを処理する。

    Args:
        df_yard: ヤードデータ
        df_shipment: 出荷データ
        master_csv: ヤードマスターCSV（事前読み込み済み）。Noneの場合は空データを返す。

    Returns:
        pd.DataFrame: 整形済みのヤード帳票

    Notes:
        - Step 5最適化: master_csvを引数で受け取ることでI/O削減
    """

    # --- ① マスターCSVの確認 ---
    if master_csv is None or master_csv.empty:
        logger.warning(
            "マスターCSVが提供されていません（ヤード）。空データで継続します。"
        )
        return pd.DataFrame(
            columns=[
                "大項目",
                "セル",
                "値",
                "セルロック",
                "順番",
                "品目名",
                "種類名",
                "品名",
            ]
        )  # 空

    # --- ② ヤードの値集計処理（df_yard + df_shipmentを使用） ---
    updated_master_csv = apply_yard_summary(master_csv, df_yard, df_shipment)
    updated_master_csv = negate_template_values(updated_master_csv)

    # # --- ③ 品目名単位でマージし、合計を計算 ---
    updated_with_sum = summarize_value_by_cell_with_label(
        updated_master_csv, cell_col="品目名", label_col="セル"
    )

    # フォーマット修正
    final_df = format_table(updated_with_sum)

    logger.info("✅ 出荷ヤードの帳票生成が完了しました。")
    return final_df


def apply_yard_summary(master_csv, df_yard, df_shipment):
    """
    最適化: master_csvのcopy()を削減（summary_apply_by_sheetが新しいDataFrameを返すため不要）
    """
    df_map = {"ヤード": df_yard, "出荷": df_shipment}

    sheet_key_pairs = [
        ("ヤード", ["種類名"]),
        ("ヤード", ["種類名", "品名"]),
        ("出荷", ["業者名", "品名"]),
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
    format_df = master_csv[["品目名", "セル", "値", "セルロック", "順番"]].copy()

    # 列の置換
    format_df.rename(columns={"品目名": "大項目"}, inplace=True)

    # カテゴリ列を追加
    format_df["カテゴリ"] = "ヤード"

    return format_df


def negate_template_values(master_csv: pd.DataFrame) -> pd.DataFrame:
    # --- 条件フィルター：対象は「品目名=その他」かつ「種類名=処分費」
    condition = (master_csv["品目名"] == "その他") & (master_csv["種類名"] == "処分費")

    # --- 品名ごとにマイナス処理
    mask_sentubetsu = condition & (master_csv["品名"] == "選別")
    mask_kinko = condition & (master_csv["品名"] == "金庫")
    mask_gc = condition & (master_csv["品名"] == "GC軽鉄・ｽﾁｰﾙ類")

    # --- 対象の値をマイナスに（符号反転）
    master_csv.loc[mask_sentubetsu, "値"] = -master_csv.loc[mask_sentubetsu, "値"]
    master_csv.loc[mask_kinko, "値"] = -master_csv.loc[mask_kinko, "値"]
    master_csv.loc[mask_gc, "値"] = -master_csv.loc[mask_gc, "値"]

    return master_csv
