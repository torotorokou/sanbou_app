from app.api.services.report.ledger.average_sheet import process as process_ave
from app.api.services.report.ledger.utils.dataframe_tools import (
    apply_summary_all_items,
)


def update_from_average_sheet(dfs, master_csv):
    csv_ave = process_ave(dfs)
    csv_ave["大項目"] = csv_ave["大項目"] + csv_ave["品目_台数他"]
    master_csv = apply_summary_all_items(master_csv, csv_ave)
    return master_csv
