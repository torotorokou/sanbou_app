"""
services.report.ledger.balance_sheet

搬出入帳票のサービス実装。
"""

import time
from typing import Any, Dict

import pandas as pd
from app.core.domain.reports.processors.balance_sheet.balacne_sheet_inbound_weight import (
    inbound_weight,
)
from app.core.domain.reports.processors.balance_sheet.balance_sheet_etc import (
    calculate_misc_summary_rows,
)
from app.core.domain.reports.processors.balance_sheet.balance_sheet_fact import (
    process_factory_report,
)
from app.core.domain.reports.processors.balance_sheet.balance_sheet_honest import (
    calculate_honest_sales_by_unit,
)
from app.core.domain.reports.processors.balance_sheet.balance_sheet_inbound_truck_count import (
    inbound_truck_count,
)
from app.core.domain.reports.processors.balance_sheet.balance_sheet_syobun import (
    calculate_total_disposal_cost,
)
from app.core.domain.reports.processors.balance_sheet.balance_sheet_yuka_kaitori import (
    calculate_purchase_value_of_valuable_items,
)
from app.core.domain.reports.processors.balance_sheet.balance_sheet_yuukabutu import (
    calculate_total_valuable_material_cost,
)
from app.core.usecases.reports.balance_sheet_base import build_balance_sheet_base_data
from app.infra.report_utils import (
    get_template_config,
    load_all_filtered_dataframes,
    load_master_and_template,
)
from backend_shared.application.logging import create_log_context, get_module_logger


def process(dfs: Dict[str, Any]) -> pd.DataFrame:
    """
    CSV群を統合し搬出入帳票の最終DataFrameを返す。

    処理フロー:
    ----------------------------------------
    入力:
      - dfs: Dict[str, pd.DataFrame]
        - receive: 受入データ（伝票日付, 受入番号, 正味重量, 単価区分 等）
        - shipment: 出荷データ（伝票日付, 業者CD, 業者名, 品名, 金額, 正味重量 等）
        - yard: ヤードデータ（種類名, 品名, 数量, 正味重量 等）

    処理ステップ:
      1. マスターCSV読み込み（balance_sheet用テンプレート）
      2. CSV群のフィルタリング（load_all_filtered_dataframes）
      3. 対象日の決定（shipment or receive の伝票日付）
      4. 各ドメイン計算処理:
         a. 搬出量データ（process_factory_report: yardとshipmentから工場日報処理）
         b. 処分費（calculate_total_disposal_cost: yard + shipment）
         c. 有価物（calculate_total_valuable_material_cost: yard + shipment）
         d. 搬入台数（inbound_truck_count: receive）
         e. 搬入量（inbound_weight: receive）
         f. オネストkg/m3（calculate_honest_sales_by_unit: receive）
         g. 有価買取（calculate_purchase_value_of_valuable_items: receive）
      5. 売上・仕入・損益まとめ（calculate_misc_summary_rows）

    出力:
      - pd.DataFrame: マスターCSVの各行に計算結果を反映した帳票用DataFrame
        - カラム: ["大項目", "値", ...（その他テンプレート項目）]

    パフォーマンスメモ:
      - 🔥 ホットスポット候補:
        * load_all_filtered_dataframes（CSV読み込み・フィルタ）
        * process_factory_report（工場日報処理：内部でsummary_apply多用）
        * 各calculate系関数（summary_apply, multiply_columns）
      - ⚡ 最適化ポイント:
        * ベースDataFrameの事前作成
        * summary_apply内のmerge/groupby処理のベクトル化
        * 不要なcopy()削減
    ----------------------------------------
    """
    logger = get_module_logger(__name__)
    start_time = time.time()
    logger.info("搬出入帳票処理開始")

    logger = get_module_logger(__name__)
    start_time = time.time()
    logger.info("搬出入帳票処理開始")

    # ========================================
    # Step 1: マスターCSV読み込み
    # ========================================
    step_start = time.time()
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["factory"]
    master_csv = load_master_and_template(master_path)
    logger.info(
        "Step 1: マスターCSV読み込み完了",
        extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)},
    )

    # ========================================
    # Step 2: テンプレート設定とCSVフィルタリング
    # ========================================
    step_start = time.time()
    template_key = "balance_sheet"
    template_config = get_template_config()[template_key]
    template_name = template_config["key"]

    required_keys = template_config.get("required_files", [])
    optional_keys = template_config.get("optional_files", [])
    csv_keys = required_keys + optional_keys

    logger.info(
        "Step 2: テンプレート設定読込",
        extra=create_log_context(
            operation="generate_balance_sheet",
            template_key=template_key,
            files=csv_keys,
        ),
    )

    df_dict = load_all_filtered_dataframes(dfs, csv_keys, template_name)

    df_receive = df_dict.get("receive")
    df_shipment = df_dict.get("shipment")
    df_yard = df_dict.get("yard")
    logger.info(
        "Step 2: CSVフィルタリング完了",
        extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)},
    )

    # ========================================
    # Step 2b: ベースDataFrame構築（型変換・単価テーブル読み込み）
    # ========================================
    # 🔥 最適化ポイント:
    #   - 単価テーブルの読み込みを1回に集約（従来は3回読み込んでいた）
    #   - 型変換を一度だけ実行（業者CDの文字列化など）
    #   - DataFrameのcopy()を最小限に
    step_start = time.time()
    base_data = build_balance_sheet_base_data(df_dict)
    logger.info(
        "Step 2b: ベースDataFrame構築完了",
        extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)},
    )

    # ========================================
    # Step 3: 対象日決定（base_dataから取得）
    # ========================================
    step_start = time.time()
    target_day = base_data.target_day

    # ========================================
    # Step 3: 対象日決定
    # ========================================
    step_start = time.time()

    # ========================================
    # Step 3: 対象日決定（base_dataから取得）
    # ========================================
    step_start = time.time()
    target_day = base_data.target_day

    logger.info(
        "Step 3: 対象日決定完了",
        extra={
            "target_day": target_day.strftime("%Y-%m-%d"),
            "elapsed_ms": round((time.time() - step_start) * 1000, 2),
        },
    )

    # ========================================
    # Step 4: ドメイン計算処理
    # ========================================
    # 注: base_dataから取得したDataFrameと単価テーブルを使用
    # （型変換済み・単価テーブルは1回だけ読み込み済み）
    df_receive = base_data.df_receive
    df_shipment = base_data.df_shipment
    df_yard = base_data.df_yard
    unit_price_table = base_data.unit_price_table  # 🔥 最適化: 1回だけ読み込み

    # Step 4a: 搬出量データ処理（工場日報）
    step_start = time.time()
    logger.info("Step 4a: 搬出量データ処理開始")
    master_csv = process_factory_report(dfs, master_csv)
    logger.info(
        "Step 4a: 搬出量データ処理完了",
        extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)},
    )

    # Step 4b: 処分費データ処理
    step_start = time.time()
    logger.info("Step 4b: 処分費データ処理開始")
    # Step 4b: 処分費データ処理
    step_start = time.time()
    logger.info("Step 4b: 処分費データ処理開始")
    if df_yard is not None and df_shipment is not None:
        master_csv.loc[master_csv["大項目"] == "処分費", "値"] = (
            calculate_total_disposal_cost(df_yard, df_shipment, unit_price_table)
        )
    logger.info(
        "Step 4b: 処分費データ処理完了",
        extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)},
    )

    # Step 4c: 有価物データ処理
    step_start = time.time()
    logger.info("Step 4c: 有価物データ処理開始")
    if df_yard is not None and df_shipment is not None:
        master_csv.loc[master_csv["大項目"] == "有価物", "値"] = (
            calculate_total_valuable_material_cost(
                df_yard, df_shipment, unit_price_table
            )
        )
    logger.info(
        "Step 4c: 有価物データ処理完了",
        extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)},
    )

    # Step 4d-g: 受入データ関連処理
    if df_receive is not None:
        # Step 4d: 搬入台数
        step_start = time.time()
        logger.info("Step 4d: 搬入台数データ処理開始")
        # Step 4d: 搬入台数
        step_start = time.time()
        logger.info("Step 4d: 搬入台数データ処理開始")
        master_csv.loc[master_csv["大項目"] == "搬入台数", "値"] = inbound_truck_count(
            df_receive
        )
        logger.info(
            "Step 4d: 搬入台数データ処理完了",
            extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)},
        )

        # Step 4e: 搬入量
        step_start = time.time()
        logger.info("Step 4e: 搬入量データ処理開始")
        master_csv.loc[master_csv["大項目"] == "搬入量", "値"] = inbound_weight(
            df_receive
        )
        logger.info(
            "Step 4e: 搬入量データ処理完了",
            extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)},
        )

        # Step 4f: オネストkg / m3
        step_start = time.time()
        logger.info("Step 4f: オネストkg/m3データ処理開始")
        honest_kg, honest_m3 = calculate_honest_sales_by_unit(df_receive)
        master_csv.loc[master_csv["大項目"] == "オネストkg", "値"] = honest_kg
        master_csv.loc[master_csv["大項目"] == "オネストm3", "値"] = honest_m3
        logger.info(
            "Step 4f: オネストkg/m3データ処理完了",
            extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)},
        )

        # Step 4g: 有価買取
        step_start = time.time()
        logger.info("Step 4g: 有価買取データ処理開始")
        master_csv.loc[master_csv["大項目"] == "有価買取", "値"] = (
            calculate_purchase_value_of_valuable_items(df_receive, unit_price_table)
        )
        logger.info(
            "Step 4g: 有価買取データ処理完了",
            extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)},
        )

    # ========================================
    # Step 5: 売上・仕入・損益まとめ処理
    # ========================================
    step_start = time.time()
    logger.info("Step 5: 売上・仕入・損益まとめ処理開始")
    # ========================================
    # Step 5: 売上・仕入・損益まとめ処理
    # ========================================
    step_start = time.time()
    logger.info("Step 5: 売上・仕入・損益まとめ処理開始")
    target_ts = pd.Timestamp(target_day)
    master_csv = calculate_misc_summary_rows(master_csv, target_ts)
    logger.info(
        "Step 5: 売上・仕入・損益まとめ処理完了",
        extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)},
    )

    # ========================================
    # 処理完了
    # ========================================
    total_elapsed = time.time() - start_time
    logger.info(
        "搬出入帳票処理完了", extra={"total_elapsed_sec": round(total_elapsed, 3)}
    )

    return master_csv
