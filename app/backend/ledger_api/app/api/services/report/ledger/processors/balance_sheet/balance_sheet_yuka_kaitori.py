import pandas as pd
from app.infra.report_utils import get_template_config, load_master_and_template
from app.api.services.report.utils.config import get_unit_price_table_csv
from app.api.services.report.utils.formatters import summary_apply
from app.api.services.report.utils.formatters import multiply_columns


def calculate_purchase_value_of_valuable_items(receive_df: pd.DataFrame) -> int:
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["uriage_yuka_kaitori"]
    master_df = load_master_and_template(master_path)

    master_with_quantity = summary_apply(
        master_df,
        receive_df,
        key_cols=["品名", "伝票区分名"],
        source_col="数量",
        target_col="数量",
    )

    unit_price_df = get_unit_price_table_csv()
    unit_price_df = unit_price_df[unit_price_df["必要項目"] == "有価買取"]

    master_with_prices = summary_apply(
        master_with_quantity,
        unit_price_df,
        key_cols=["品名"],
        source_col="設定単価",
        target_col="設定単価",
    )

    result_df = multiply_columns(
        master_with_prices, col1="設定単価", col2="数量", result_col="値"
    )

    total = int(result_df["値"].sum())
    return total
