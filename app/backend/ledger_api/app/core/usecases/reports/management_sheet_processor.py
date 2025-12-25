"""
services.report.ledger.management_sheet

管理表（management_sheet）のサービス実装。
st_app依存を排し、services側のprocessors/utilsを利用する。
"""

from typing import Any

import pandas as pd
from backend_shared.application.logging import create_log_context, get_module_logger

from app.core.domain.reports.processors.management_sheet.average_sheet import (
    update_from_average_sheet,
)
from app.core.domain.reports.processors.management_sheet.balance_sheet import (
    update_from_balance_sheet,
)
from app.core.domain.reports.processors.management_sheet.factory_report import (
    update_from_factory_report,
)
from app.core.domain.reports.processors.management_sheet.manage_etc import manage_etc
from app.core.domain.reports.processors.management_sheet.scrap_senbetsu import (
    scrap_senbetsu,
)
from app.infra.report_utils import (
    get_template_config,
    load_all_filtered_dataframes,
    load_master_and_template,
)


def process(dfs: dict[str, Any]) -> pd.DataFrame:
    logger = get_module_logger(__name__)

    config = get_template_config()["management_sheet"]
    master_path = config["master_csv_path"]["management_sheet"]
    master_csv = load_master_and_template(master_path)

    template_key = "management_sheet"
    template_config = get_template_config()[template_key]
    template_name = template_config["key"]
    csv_keys = template_config["required_files"]
    logger.info(
        "テンプレート設定読込",
        extra=create_log_context(
            operation="generate_management_sheet",
            template_key=template_key,
            files=csv_keys,
        ),
    )

    df_dict = load_all_filtered_dataframes(dfs, csv_keys, template_name)
    df_receive = df_dict.get("receive")
    if df_receive is None:
        logger.warning(
            "management_sheet: receive データがNoneのため、scrap/日付処理はスキップします。"
        )
        df_receive = pd.DataFrame()

    master_csv = update_from_factory_report(dfs, master_csv)
    master_csv = update_from_balance_sheet(dfs, master_csv)
    master_csv = update_from_average_sheet(dfs, master_csv)
    if not df_receive.empty:
        master_csv = scrap_senbetsu(df_receive, master_csv)
        etc_df = manage_etc(df_receive)
    else:
        etc_df = pd.DataFrame()

    df_final = pd.concat([master_csv, etc_df], axis=0, ignore_index=True)
    return df_final
