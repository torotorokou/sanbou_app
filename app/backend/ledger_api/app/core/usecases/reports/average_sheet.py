"""
services.report.ledger.average_sheet

ABC平均表（average_sheet）のサービス実装。
st_app依存を排し、services側のprocessors/utilsを利用する。

最適化履歴:
- Step 1 (2025-12-08): 処理フローの可視化とタイミングログ追加
"""
from typing import Any, Dict
import time
import pandas as pd

from app.infra.report_utils import (
    get_template_config,
    load_all_filtered_dataframes,
    load_master_and_template,
)
from backend_shared.application.logging import get_module_logger, create_log_context
from app.core.domain.reports.processors.average_sheet.processors import (
    tikan,
    aggregate_vehicle_data,
    calculate_item_summary,
    summarize_item_and_abc_totals,
    calculate_final_totals,
    set_report_date_info,
    apply_rounding,
)


def process(dfs: Dict[str, Any]) -> pd.DataFrame:
    """
    ABC平均表（average_sheet）のメイン処理関数。
    
    処理フロー:
    ----------------------------------------
    入力:
      - dfs: Dict[str, pd.DataFrame]
        - receive: 入庫データ（業者名, 品名, 正味重量, 金額 等）
    
    処理ステップ:
      Step 1: テンプレート設定の取得
      Step 2: CSV読み込みとフィルタリング
      Step 3: マスターCSV読み込み
      Step 4: データ存在確認
      Step 5: 個別ドメイン処理
        - 5a: aggregate_vehicle_data - 台数データ集計
        - 5b: calculate_item_summary - 品目別集計
        - 5c: summarize_item_and_abc_totals - ABC業者合計
        - 5d: calculate_final_totals - 最終合計計算
        - 5e: set_report_date_info - 日付情報設定
        - 5f: apply_rounding - 四捨五入処理
      Step 6: 置換処理（tikan）
    
    出力:
      - pd.DataFrame: ABC平均表データ（セル, 値, 大項目 等）
    
    最適化ポイント:
      - 各ステップの処理時間を計測してボトルネック特定
      - マスターCSV読み込みを1回に集約予定
    ----------------------------------------
    """
    start_time = time.time()
    logger = get_module_logger(__name__)
    
    # ========================================
    # Step 1: テンプレート設定の取得
    # ========================================
    step_start = time.time()
    template_name = get_template_config()["average_sheet"]["key"]
    csv_name = get_template_config()["average_sheet"]["required_files"]
    logger.info(
        "Step 1: テンプレート設定読込完了",
        extra=create_log_context(
            operation="generate_average_sheet",
            csv_name=csv_name,
            elapsed_ms=round((time.time() - step_start) * 1000, 2)
        )
    )
    
    # ========================================
    # Step 2: CSV読み込みとフィルタリング
    # ========================================
    step_start = time.time()
    df_dict = load_all_filtered_dataframes(dfs, csv_name, template_name)
    logger.info(
        "Step 2: CSV読み込み完了",
        extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)}
    )

    # ========================================
    # Step 3: マスターCSV読み込み
    # ========================================
    step_start = time.time()
    df_receive = df_dict.get(csv_name[0])
    master_path = get_template_config()[template_name]["master_csv_path"]
    master_csv = load_master_and_template(master_path)
    logger.info(
        "Step 3: マスターCSV読込完了",
        extra=create_log_context(
            operation="generate_average_sheet",
            master_path=master_path,
            shape=master_csv.shape,
            elapsed_ms=round((time.time() - step_start) * 1000, 2)
        )
    )

    # ========================================
    # Step 4: データ存在確認
    # ========================================
    # ========================================
    # Step 5: 個別ドメイン処理
    # ========================================
    master_columns_keys = ["ABC業者_他", "kg売上平均単価", "品目_台数他"]

    try:
        # Step 5a: 台数データ集計
        step_start = time.time()
        logger.info("Step 5a: 台数データ集計開始")
        master_csv = aggregate_vehicle_data(df_receive, master_csv, master_columns_keys)
        logger.info(
            "Step 5a: 台数データ集計完了",
            extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)}
        )

        # Step 5b: 品目別集計
        step_start = time.time()
        logger.info("Step 5b: 品目別集計開始")
        master_csv = calculate_item_summary(df_receive, master_csv, master_columns_keys)
        logger.info(
            "Step 5b: 品目別集計完了",
            extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)}
        )

        # Step 5c: ABC業者合計
        step_start = time.time()
        logger.info("Step 5c: ABC業者合計開始")
        master_csv = summarize_item_and_abc_totals(master_csv, master_columns_keys)
        logger.info(
            "Step 5c: ABC業者合計完了",
            extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)}
        )

        # Step 5d: 最終合計計算
        step_start = time.time()
        logger.info("Step 5d: 最終合計計算開始")
        master_csv = calculate_final_totals(df_receive, master_csv, master_columns_keys)
        logger.info(
            "Step 5d: 最終合計計算完了",
            extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)}
        )

        # Step 5e: 日付情報設定
        step_start = time.time()
        logger.info("Step 5e: 日付情報設定開始")
        master_csv = set_report_date_info(df_receive, master_csv, master_columns_keys)
    except Exception as ex:
        # 各STEPのいずれかで失敗した箇所を特定するための詳細ログ
        import traceback as _tb

        logger.error(
            "average_sheet処理失敗",
            extra=create_log_context(operation="generate_average_sheet", error=str(ex), traceback=_tb.format_exc()),
            exc_info=True
        )
        raise

    # ========================================
    # Step 6: 置換処理
    # ========================================
    step_start = time.time()
    logger.info("Step 6: 置換処理（tikan）開始")
    master_csv = tikan(master_csv)
    logger.info(
        "Step 6: 置換処理完了",
        extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)}
    )

    # ========================================
    # 処理完了
    # ========================================
    total_elapsed = time.time() - start_time
    logger.info(
        "ABC平均表処理完了",
        extra={"total_elapsed_sec": round(total_elapsed, 3)}
    )
    
    return master_csv[STEP] set_report_date_info done")

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
            extra=create_log_context(operation="generate_average_sheet", error=str(ex), traceback=_tb.format_exc()),
            exc_info=True
        )
        raise

    master_csv = tikan(master_csv)
    logger.info(
        f"[DEBUG] tikan applied: columns={list(master_csv.columns)}, shape={master_csv.shape}"
    )
    return master_csv
