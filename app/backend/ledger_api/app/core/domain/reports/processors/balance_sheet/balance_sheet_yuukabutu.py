import pandas as pd
from app.infra.report_utils import (
    get_template_config,
    load_master_and_template,
)
from app.infra.report_utils.formatters import summary_apply
from app.infra.report_utils.formatters.multiply_optimized import (
    multiply_columns_optimized,
)
from app.infra.report_utils.formatters.summary_optimized import summary_apply_optimized


def calculate_total_valuable_material_cost(
    df_yard: pd.DataFrame,
    df_shipment: pd.DataFrame,
    unit_price_table: pd.DataFrame,
) -> int:
    """
    有価物の合計を計算する。

    Args:
        df_yard: ヤードデータ
        df_shipment: 出荷データ
        unit_price_table: 単価テーブル（外部から受け取り、I/O削減）
    """
    shipment_summary_df = aggregate_valuable_material_by_vendor(df_shipment)
    sum_shipment = shipment_summary_df["値"].sum()

    yard_summary_df = calculate_valuable_material_cost_by_item(
        df_yard, unit_price_table
    )
    sum_yard = yard_summary_df["値"].sum()

    total_value = int(sum_shipment + sum_yard)
    return total_value


def aggregate_valuable_material_by_vendor(shipment_df: pd.DataFrame) -> pd.DataFrame:
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["yuka_shipment"]
    master_df = load_master_and_template(master_path)

    key_cols = ["業者名"]
    aggregated_df = summary_apply(
        master_df,
        shipment_df,
        key_cols=key_cols,
        source_col="金額",
        target_col="値",
    )
    return aggregated_df


def calculate_valuable_material_cost_by_item(
    df_yard: pd.DataFrame,
    unit_price_table: pd.DataFrame,
) -> pd.DataFrame:
    """
    ヤードの有価物を品名別に計算（数量×単価）。

    最適化版を使用:
    - summary_apply_optimized: master_csvのcopy()を1回だけ実行
    - multiply_columns_optimized: 不要なcopy()を削減
    - unit_price_tableを外部から受け取り、I/O削減
    """
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["yuka_yard"]
    master_df = load_master_and_template(master_path).copy()  # ここで1回だけcopy

    # ① ヤードデータから品名別に数量を集計
    master_with_quantity = summary_apply_optimized(
        master_df,
        df_yard,
        key_cols=["品名"],
        source_col="数量",
        target_col="数量",
    )

    # ② 単価テーブルから有価物の単価を取得（外部から受け取る）
    unit_price_df = unit_price_table[unit_price_table["必要項目"] == "有価物"]

    # ③ 単価をマージ
    master_with_price = summary_apply_optimized(
        master_with_quantity,
        unit_price_df,
        key_cols=["品名"],
        source_col="設定単価",
        target_col="設定単価",
    )

    # ④ 数量 × 単価 = 金額（値）
    result_df = multiply_columns_optimized(
        master_with_price, col1="設定単価", col2="数量", result_col="値"
    )

    result_df = result_df.rename(columns={"品名": "大項目"})
    return result_df
