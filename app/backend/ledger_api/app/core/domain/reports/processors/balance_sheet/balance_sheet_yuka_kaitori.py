import pandas as pd
from app.infra.report_utils import get_template_config, load_master_and_template
from app.infra.report_utils.formatters.multiply_optimized import multiply_columns_optimized
from app.infra.report_utils.formatters.summary_optimized import summary_apply_optimized


def calculate_purchase_value_of_valuable_items(
    receive_df: pd.DataFrame,
    unit_price_table: pd.DataFrame,
) -> int:
    """
    有価買取の金額を計算する。
    
    最適化版を使用:
    - summary_apply_optimized: master_csvのcopy()を1回だけ実行
    - multiply_columns_optimized: 不要なcopy()を削減
    - unit_price_tableを外部から受け取り、I/O削減
    """
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["uriage_yuka_kaitori"]
    master_df = load_master_and_template(master_path).copy()

    master_with_quantity = summary_apply_optimized(
        master_df,
        receive_df,
        key_cols=["品名", "伝票区分名"],
        source_col="数量",
        target_col="数量",
    )

    # 単価テーブルを外部から受け取る（I/O削減）
    unit_price_df = unit_price_table[unit_price_table["必要項目"] == "有価買取"]

    master_with_prices = summary_apply_optimized(
        master_with_quantity,
        unit_price_df,
        key_cols=["品名"],
        source_col="設定単価",
        target_col="設定単価",
    )

    result_df = multiply_columns_optimized(
        master_with_prices, col1="設定単価", col2="数量", result_col="値"
    )

    total = int(result_df["値"].sum())
    return total
