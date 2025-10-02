import pandas as pd
from app.api.services.report.ledger.utils import load_master_and_template, get_template_config
from app.api.services.report.ledger.utils.summary_tools import set_value_fast_safe
from app.api.services.report.ledger.utils.date_tools import get_title_from_date


def manage_etc(df_receive: pd.DataFrame) -> pd.DataFrame:
    config = get_template_config()["management_sheet"]
    master_path = config["master_csv_path"]["etc"]
    master_csv = load_master_and_template(master_path)

    today = df_receive["伝票日付"][0]

    master_csv = set_value_fast_safe(master_csv, ["大項目"], ["日"], today.day)

    title = get_title_from_date(today)
    master_csv = set_value_fast_safe(master_csv, ["大項目"], ["タイトル"], title)

    return master_csv
