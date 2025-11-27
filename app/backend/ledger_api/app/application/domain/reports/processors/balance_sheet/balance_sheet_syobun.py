import pandas as pd
from app.infra.report_utils import get_template_config, load_master_and_template
from app.infra.report_utils import get_unit_price_table_csv
from app.infra.report_utils.formatters import summary_apply
from app.infra.report_utils.formatters import multiply_columns


def calculate_total_disposal_cost(
    df_yard: pd.DataFrame,
    df_shipment: pd.DataFrame,
) -> int:
    cost_by_vendor = int(calculate_disposal_costs(df_shipment)["値"].sum())
    cost_safe_shipment = int(calculate_safe_disposal_costs(df_shipment)["値"].sum())
    cost_safe_yard = int(calculate_yard_disposal_costs(df_yard)["値"].sum())
    total_cost = cost_by_vendor + cost_safe_shipment + cost_safe_yard
    return total_cost


def calculate_disposal_costs(df_shipment: pd.DataFrame) -> pd.DataFrame:
    # NOTE: df_shipment が呼び出し元でスライスされたビューの可能性があるため、
    # ここで明示的にコピーしてから列を書き換えることで SettingWithCopyWarning を回避する。
    df_shipment = df_shipment.copy()
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["shobun_cost"]
    master_csv_cost = load_master_and_template(master_path)

    df_shipment["業者CD"] = df_shipment["業者CD"].astype(str)
    master_csv_cost["業者CD"] = master_csv_cost["業者CD"].astype(str)

    key_cols = ["業者CD"]
    source_col = "金額"
    master_csv_cost = summary_apply(master_csv_cost, df_shipment, key_cols, source_col)
    return master_csv_cost


def calculate_safe_disposal_costs(df_shipment: pd.DataFrame) -> pd.DataFrame:
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["syobun_cost_kinko"]
    master_df = load_master_and_template(master_path)

    key_cols = ["業者名", "品名"]
    master_with_weight = summary_apply(
        master_df,
        df_shipment,
        key_cols=key_cols,
        source_col="正味重量",
        target_col="正味重量",
    )

    unit_price_df = get_unit_price_table_csv()
    master_with_price = summary_apply(
        master_with_weight,
        unit_price_df,
        key_cols=key_cols,
        source_col="設定単価",
        target_col="設定単価",
    )

    master_csv_kinko = multiply_columns(
        master_with_price, col1="設定単価", col2="正味重量", result_col="値"
    )
    return master_csv_kinko


def calculate_yard_disposal_costs(yard_df: pd.DataFrame) -> pd.DataFrame:
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["syobun_cost_kinko_yard"]
    master_df = load_master_and_template(master_path)

    key_cols = ["種類名", "品名"]
    master_with_weight = summary_apply(
        master_df,
        yard_df,
        key_cols=key_cols,
        source_col="正味重量",
        target_col="正味重量",
    )

    unit_price_df = get_unit_price_table_csv()
    master_with_price = summary_apply(
        master_with_weight,
        unit_price_df,
        key_cols=key_cols,
        source_col="設定単価",
        target_col="設定単価",
    )

    master_csv_kinko_yard = multiply_columns(
        master_with_price, col1="設定単価", col2="正味重量", result_col="値"
    )
    return master_csv_kinko_yard
