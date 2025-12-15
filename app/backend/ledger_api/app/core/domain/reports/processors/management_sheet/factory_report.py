from app.core.usecases.reports.factory_report_processor import process as process_fact
from app.infra.report_utils.dataframe.operations import apply_summary_all_items


def update_from_factory_report(dfs, master_csv):
    csv_fac = process_fact(dfs)
    master_csv = apply_summary_all_items(master_csv, csv_fac)
    return master_csv
