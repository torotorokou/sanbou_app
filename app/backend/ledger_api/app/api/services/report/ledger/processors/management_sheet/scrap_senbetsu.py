import pandas as pd
from app.api.services.report.ledger.utils import load_master_and_template, get_template_config
from app.api.services.report.ledger.utils.summary_tools import summary_apply
from app.api.services.report.ledger.utils.dataframe_tools import apply_summary_all_items


def scrap_senbetsu(df_receive: pd.DataFrame, master_csv: pd.DataFrame) -> pd.DataFrame:
    config = get_template_config()["management_sheet"]
    master_path = config["master_csv_path"]["scrap_senbetsu_map"]
    csv_ss = load_master_and_template(master_path)

    csv_ss = summary_apply(csv_ss, df_receive, ["品名CD"], "正味重量", "値")
    csv_ss_sum = csv_ss.groupby("大項目").sum().reset_index()

    master_csv = apply_summary_all_items(master_csv, csv_ss_sum)
    return master_csv
