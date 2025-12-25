"""
services.report.ledger.average_sheet

ABC平均表（average_sheet）のサービス実装。
st_app依存を排し、services側のprocessors/utilsを利用する。
"""

from typing import Any

import pandas as pd
from backend_shared.application.logging import create_log_context, get_module_logger

from app.core.domain.reports.processors.average_sheet.processors import (
    aggregate_vehicle_data,
    apply_rounding,
    calculate_final_totals,
    calculate_item_summary,
    set_report_date_info,
    summarize_item_and_abc_totals,
    tikan,
)
from app.infra.report_utils import (
    get_template_config,
    load_all_filtered_dataframes,
    load_master_and_template,
)


def process(dfs: dict[str, Any]) -> pd.DataFrame:
    logger = get_module_logger(__name__)
    template_name = get_template_config()["average_sheet"]["key"]

    csv_name = get_template_config()["average_sheet"]["required_files"]
    logger.info(
        "average_sheet process開始",
        extra=create_log_context(operation="generate_average_sheet", csv_name=csv_name),
    )
    df_dict = load_all_filtered_dataframes(dfs, csv_name, template_name)

    df_receive = df_dict.get(csv_name[0])

    master_path = get_template_config()[template_name]["master_csv_path"]
    logger.info(
        "マスターCSV読込",
        extra=create_log_context(
            operation="generate_average_sheet", master_path=master_path
        ),
    )
    master_csv = load_master_and_template(master_path)
    logger.info(
        f"[DEBUG] master_csv loaded with shape={getattr(master_csv, 'shape', None)} and columns={list(master_csv.columns) if hasattr(master_csv, 'columns') else 'N/A'}"
    )

    if df_receive is None or df_receive.empty:
        logger.warning("average_sheet: receive データが空のため処理をスキップします")
        return master_csv

    logger.info(
        f"[DEBUG] df_receive shape={getattr(df_receive, 'shape', None)}, head_cols={list(df_receive.columns)[:8]}"
    )

    master_columns_keys = ["ABC業者_他", "kg売上平均単価", "品目_台数他"]

    try:
        logger.info("[STEP] aggregate_vehicle_data start")
        master_csv = aggregate_vehicle_data(df_receive, master_csv, master_columns_keys)
        logger.info(
            f"[STEP] aggregate_vehicle_data done: shape={master_csv.shape}, 値.dtype={master_csv['値'].dtype if '値' in master_csv.columns else 'N/A'}"
        )

        logger.info("[STEP] calculate_item_summary start")
        master_csv = calculate_item_summary(df_receive, master_csv, master_columns_keys)
        logger.info(f"[STEP] calculate_item_summary done: shape={master_csv.shape}")

        logger.info("[STEP] summarize_item_and_abc_totals start")
        master_csv = summarize_item_and_abc_totals(master_csv, master_columns_keys)
        logger.info(
            f"[STEP] summarize_item_and_abc_totals done: shape={master_csv.shape}"
        )

        logger.info("[STEP] calculate_final_totals start")
        master_csv = calculate_final_totals(df_receive, master_csv, master_columns_keys)
        logger.info(f"[STEP] calculate_final_totals done: shape={master_csv.shape}")

        logger.info("[STEP] set_report_date_info start")
        master_csv = set_report_date_info(df_receive, master_csv, master_columns_keys)
        logger.info("[STEP] set_report_date_info done")

        logger.info("[STEP] apply_rounding start")
        master_csv = apply_rounding(master_csv, master_columns_keys)
        logger.info(
            f"[STEP] apply_rounding done: 値.dtype={master_csv['値'].dtype if '値' in master_csv.columns else 'N/A'}"
        )

    except Exception as ex:
        # 各STEPのいずれかで失敗した箇所を特定するための詳細ログ
        import traceback as _tb

        logger.error(
            "average_sheet処理失敗",
            extra=create_log_context(
                operation="generate_average_sheet",
                error=str(ex),
                traceback=_tb.format_exc(),
            ),
            exc_info=True,
        )
        raise

    master_csv = tikan(master_csv)
    logger.info(
        f"[DEBUG] tikan applied: columns={list(master_csv.columns)}, shape={master_csv.shape}"
    )
    return master_csv
