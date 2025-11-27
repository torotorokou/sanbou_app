"""
services.report.ledger.balance_sheet

搬出入帳票のサービス実装。
"""
from typing import Any, Dict
import pandas as pd

from app.infra.report_utils import (
    app_logger,
    get_template_config,
    load_all_filtered_dataframes,
    load_master_and_template,
)
from app.application.domain.reports.processors.balance_sheet.balance_sheet_fact import (
    process_factory_report,
)
from app.application.domain.reports.processors.balance_sheet.balance_sheet_syobun import (
    calculate_total_disposal_cost,
)
from app.application.domain.reports.processors.balance_sheet.balance_sheet_yuukabutu import (
    calculate_total_valuable_material_cost,
)
from app.application.domain.reports.processors.balance_sheet.balance_sheet_inbound_truck_count import (
    inbound_truck_count,
)
from app.application.domain.reports.processors.balance_sheet.balacne_sheet_inbound_weight import (
    inbound_weight,
)
from app.application.domain.reports.processors.balance_sheet.balance_sheet_honest import (
    calculate_honest_sales_by_unit,
)
from app.application.domain.reports.processors.balance_sheet.balance_sheet_yuka_kaitori import (
    calculate_purchase_value_of_valuable_items,
)
from app.application.domain.reports.processors.balance_sheet.balance_sheet_etc import (
    calculate_misc_summary_rows,
)


def process(dfs: Dict[str, Any]) -> pd.DataFrame:
    """CSV群を統合し搬出入帳票の最終DataFrameを返す。"""
    logger = app_logger()

    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["factory"]
    master_csv = load_master_and_template(master_path)

    template_key = "balance_sheet"
    template_config = get_template_config()[template_key]
    template_name = template_config["key"]

    required_keys = template_config.get("required_files", [])
    optional_keys = template_config.get("optional_files", [])
    csv_keys = required_keys + optional_keys

    logger.info(f"[テンプレート設定読込] key={template_key}, files={csv_keys}")

    df_dict = load_all_filtered_dataframes(dfs, csv_keys, template_name)

    df_receive = df_dict.get("receive")
    df_shipment = df_dict.get("shipment")
    df_yard = df_dict.get("yard")

    if df_shipment is not None and not df_shipment.empty and "伝票日付" in df_shipment.columns:
        target_day = pd.to_datetime(df_shipment["伝票日付"].dropna().iloc[0])
    elif df_receive is not None and not df_receive.empty and "伝票日付" in df_receive.columns:
        target_day = pd.to_datetime(df_receive["伝票日付"].dropna().iloc[0])
    else:
        target_day = pd.Timestamp.today()

    logger.info("▶️ 搬出量データ処理開始")
    master_csv = process_factory_report(dfs, master_csv)

    logger.info("▶️ 処分費データ処理開始")
    if df_yard is not None and df_shipment is not None:
        master_csv.loc[master_csv["大項目"] == "処分費", "値"] = (
            calculate_total_disposal_cost(df_yard, df_shipment)
        )

    logger.info("▶️ 有価物データ処理開始")
    if df_yard is not None and df_shipment is not None:
        master_csv.loc[master_csv["大項目"] == "有価物", "値"] = (
            calculate_total_valuable_material_cost(df_yard, df_shipment)
        )

    if df_receive is not None:
        logger.info("▶️ 搬入台数データ処理開始")
        master_csv.loc[master_csv["大項目"] == "搬入台数", "値"] = inbound_truck_count(
            df_receive
        )

        logger.info("▶️ 搬入量データ処理開始")
        master_csv.loc[master_csv["大項目"] == "搬入量", "値"] = inbound_weight(
            df_receive
        )

        logger.info("▶️ オネストkg / m3 データ処理開始")
        honest_kg, honest_m3 = calculate_honest_sales_by_unit(df_receive)
        master_csv.loc[master_csv["大項目"] == "オネストkg", "値"] = honest_kg
        master_csv.loc[master_csv["大項目"] == "オネストm3", "値"] = honest_m3

        logger.info("▶️ 有価買取データ処理開始")
        master_csv.loc[master_csv["大項目"] == "有価買取", "値"] = (
            calculate_purchase_value_of_valuable_items(df_receive)
        )

    logger.info("▶️ 売上・仕入・損益まとめ処理開始")
    target_ts = pd.Timestamp(target_day)
    master_csv = calculate_misc_summary_rows(master_csv, target_ts)

    return master_csv
