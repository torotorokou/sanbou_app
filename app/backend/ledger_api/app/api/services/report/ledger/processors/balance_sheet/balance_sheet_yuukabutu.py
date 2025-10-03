import pandas as pd
from app.api.services.report.utils.config import get_template_config
from app.api.services.report.utils.io import load_master_and_template
from app.api.services.report.utils.formatters import summary_apply


def calculate_total_valuable_material_cost(
    df_yard: pd.DataFrame,
    df_shipment: pd.DataFrame,
) -> int:
    shipment_summary_df = aggregate_valuable_material_by_vendor(df_shipment)
    sum_shipment = shipment_summary_df["値"].sum()

    yard_summary_df = calculate_valuable_material_cost_by_item(df_yard)
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


def calculate_valuable_material_cost_by_item(df_yard: pd.DataFrame) -> pd.DataFrame:
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["yuka_yard"]
    master_df = load_master_and_template(master_path)

    master_with_quantity = summary_apply(
        master_df,
        df_yard,
        key_cols=["品名"],
        source_col="数量",
        target_col="数量",
    )

    result_df = summary_apply(
        master_with_quantity,
        master_with_quantity,
        key_cols=["品名"],
        source_col="数量",
        target_col="数量",
    )
    result_df = result_df.rename(columns={"品名": "大項目"})
    return result_df
