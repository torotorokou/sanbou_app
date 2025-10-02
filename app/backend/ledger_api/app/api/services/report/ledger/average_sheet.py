"""
services.report.ledger.average_sheet

ABC平均表（average_sheet）のサービス実装。
st_app依存を排し、services側のprocessors/utilsを利用する。
"""
from typing import Any, Dict
import pandas as pd

from app.api.services.report.ledger.utils import (
    app_logger,
    get_template_config,
)
from app.api.services.report.ledger.utils import load_all_filtered_dataframes
from app.api.services.report.ledger.utils import load_master_and_template
from app.api.services.report.ledger.processors.average_sheet.processors import (
    tikan,
    aggregate_vehicle_data,
    calculate_item_summary,
    summarize_item_and_abc_totals,
    calculate_final_totals,
    set_report_date_info,
    apply_rounding,
)


def process(dfs: Dict[str, Any]) -> pd.DataFrame:
    logger = app_logger()
    template_name = get_template_config()["average_sheet"]["key"]

    csv_name = get_template_config()["average_sheet"]["required_files"]
    logger.info(f"Processの処理に入る。{csv_name}")
    df_dict = load_all_filtered_dataframes(dfs, csv_name, template_name)

    df_receive = df_dict.get(csv_name[0])

    master_path = get_template_config()[template_name]["master_csv_path"]
    logger.info(f"[DEBUG] Loading master from: {master_path}")
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
        logger.info(
            f"[STEP] calculate_item_summary done: shape={master_csv.shape}"
        )

        logger.info("[STEP] summarize_item_and_abc_totals start")
        master_csv = summarize_item_and_abc_totals(master_csv, master_columns_keys)
        logger.info(
            f"[STEP] summarize_item_and_abc_totals done: shape={master_csv.shape}"
        )

        logger.info("[STEP] calculate_final_totals start")
        master_csv = calculate_final_totals(df_receive, master_csv, master_columns_keys)
        logger.info(
            f"[STEP] calculate_final_totals done: shape={master_csv.shape}"
        )

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

        logger.error(f"[ERROR] average_sheet processing failed at step: {ex}")
        logger.error("[ERROR] Traceback:\n" + _tb.format_exc())
        raise

    master_csv = tikan(master_csv)
    logger.info(
        f"[DEBUG] tikan applied: columns={list(master_csv.columns)}, shape={master_csv.shape}"
    )
    return master_csv
