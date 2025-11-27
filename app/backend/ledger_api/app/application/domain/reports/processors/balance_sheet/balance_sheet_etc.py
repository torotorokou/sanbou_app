import pandas as pd
from app.infra.report_utils import get_template_config, load_master_and_template
from app.infra.report_utils.formatters import to_reiwa_format
from app.infra.report_utils.formatters import set_value_fast_safe


def calculate_misc_summary_rows(
    master_csv: pd.DataFrame, first_invoice_date: pd.Timestamp
) -> pd.DataFrame:
    """
    売上・仕入・損益の補足行を計算し、マスターに追加する。
    """

    def safe_int(val, default=0):
        try:
            if pd.isna(val):
                return default
            return int(val)
        except Exception:
            return default

    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["etc"]
    etc_df = load_master_and_template(master_path)

    reiwa_date = to_reiwa_format(first_invoice_date)
    etc_df = set_value_fast_safe(
        df=etc_df,
        match_columns=["大項目"],
        match_values=["月日"],
        value=reiwa_date,
        value_col="値",
    )

    honest_kg = safe_int(
        master_csv.loc[master_csv["大項目"] == "オネストkg", "値"].values[0]
    )
    honest_m3 = safe_int(
        master_csv.loc[master_csv["大項目"] == "オネストm3", "値"].values[0]
    )
    yuka_kaitori = safe_int(
        master_csv.loc[master_csv["大項目"] == "有価買取", "値"].values[0]
    )
    sales_total = honest_kg + honest_m3 - yuka_kaitori
    etc_df = set_value_fast_safe(etc_df, ["大項目"], ["売上計"], sales_total, "値")

    shobun_cost = safe_int(
        master_csv.loc[master_csv["大項目"] == "処分費", "値"].values[0]
    )
    yuka_cost = safe_int(
        master_csv.loc[master_csv["大項目"] == "有価物", "値"].values[0]
    )
    cost_total = shobun_cost - yuka_cost
    etc_df = set_value_fast_safe(etc_df, ["大項目"], ["仕入計"], cost_total, "値")

    profit_total = sales_total - cost_total
    etc_df = set_value_fast_safe(etc_df, ["大項目"], ["損益"], profit_total, "値")

    result_df = pd.concat([master_csv, etc_df], axis=0, ignore_index=True)

    return result_df
