import pandas as pd
from app.infra.report_utils import get_template_config, load_master_and_template
from app.api.services.report.utils.formatters import summary_apply


def calculate_honest_sales_by_unit(df_receive: pd.DataFrame) -> tuple[int, int]:
    """「オネストkg」「オネストm3」の売上金額を受入データから計算する。"""

    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["uriage"]
    master_df = load_master_and_template(master_path)

    summary_m3 = summary_apply(
        master_df,
        df_receive,
        key_cols=["伝票区分名", "単位名"],
        source_col="金額",
        target_col="金額",
    )

    summary_kg = summary_apply(
        master_df,
        df_receive,
        key_cols=["伝票区分名"],
        source_col="金額",
        target_col="金額",
    )

    honest_row_m3 = summary_m3[summary_m3["項目"] == "オネストm3"]
    honest_m3_value = (
        honest_row_m3["金額"].fillna(0).values[0] if not honest_row_m3.empty else 0
    )

    honest_row_kg = summary_kg[summary_kg["項目"] == "オネストkg"]
    honest_kg_value = (
        honest_row_kg["金額"].fillna(0).values[0] if not honest_row_kg.empty else 0
    )

    honest_kg_total = honest_kg_value - honest_m3_value

    return honest_kg_total, honest_m3_value
