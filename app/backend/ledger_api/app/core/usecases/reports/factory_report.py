"""
services.report.ledger.factory_report

工場日報（factory_report）のサービス実装。
st_app依存を排し、services側のprocessors/utilsを利用する。
"""
from typing import Any, Dict
import time
import pandas as pd

from app.infra.report_utils import (
    get_template_config,
    load_all_filtered_dataframes,
)
from app.infra.report_utils.excel import sort_by_cell_row
from backend_shared.application.logging import get_module_logger, create_log_context
from app.core.domain.reports.processors.factory_report.shobun import (
    process_shobun,
)
from app.core.domain.reports.processors.factory_report.yuuka import (
    process_yuuka,
)
from app.core.domain.reports.processors.factory_report.yard import (
    process_yard,
)
from app.core.domain.reports.processors.factory_report.make_cell_num import (
    make_cell_num,
)
from app.core.domain.reports.processors.factory_report.make_label import (
    make_label,
)
from app.core.domain.reports.processors.factory_report.etc import (
    generate_summary_dataframe,
    date_format,
)
from app.core.usecases.reports.factory_report_base import (
    build_factory_report_base_data,
)


def process(dfs: Dict[str, Any]) -> pd.DataFrame:
    """
    工場日報テンプレート用のメイン処理関数。
    
    処理フロー:
    ----------------------------------------
    入力:
      - dfs: Dict[str, pd.DataFrame]
        - shipment: 出荷データ（業者CD, 業者名, 品名, 金額, 正味重量 等）
        - yard: ヤードデータ（種類名, 品名, 数量, 正味重量 等）
    
    処理ステップ:
      1. テンプレート設定読み込み（factory_report用）
      2. CSV群のフィルタリング（load_all_filtered_dataframes）
      3. 各ドメイン処理:
         a. 処分データ（process_shobun: shipmentから業者別集計）
         b. 有価データ（process_yuuka: yard + shipmentで有価物集計）
         c. ヤードデータ（process_yard: yard + shipmentでヤード在庫集計）
      4. 結合・整形:
         a. 各処理結果をconcat
         b. セル番号設定（make_cell_num）
         c. ラベル追加（make_label）
         d. 合計・総合計行追加（generate_summary_dataframe）
         e. 日付挿入（date_format）
         f. セル行順ソート（sort_by_cell_row）
    
    出力:
      - pd.DataFrame: 工場日報用DataFrame
        - カラム: ["セル", "ラベル", "値", "順番", ...（その他項目）]
    
    パフォーマンスメモ:
      - 🔥 ホットスポット候補:
        * process_shobun, process_yuuka, process_yard（内部でsummary_apply多用）
        * load_all_filtered_dataframes（CSV読み込み・フィルタ）
      - ⚡ 最適化ポイント:
        * ベースDataFrameの事前作成
        * 各process_*関数内のcopy()削減
        * summary_apply最適化版の適用
    ----------------------------------------
    備考: CSVが欠落している場合は該当処理をスキップします。
    """

    logger = get_module_logger(__name__)
    start_time = time.time()
    logger.info("工場日報処理開始")

    logger = get_module_logger(__name__)
    start_time = time.time()
    logger.info("工場日報処理開始")

    # ========================================
    # Step 1: テンプレート設定の取得
    # ========================================
    step_start = time.time()
    template_key = "factory_report"
    template_config = get_template_config()[template_key]
    template_name = template_config["key"]
    csv_keys = template_config["required_files"]
    logger.info(
        "Step 1: テンプレート設定読込完了",
        extra=create_log_context(
            operation="generate_factory_report", 
            template_key=template_key, 
            files=csv_keys,
            elapsed_ms=round((time.time() - step_start) * 1000, 2)
        )
    )

    # ========================================
    # Step 2: CSV読み込みとフィルタリング
    # ========================================
    step_start = time.time()
    df_dict = load_all_filtered_dataframes(dfs, csv_keys, template_name)
    df_shipment = df_dict.get("shipment")
    df_yard = df_dict.get("yard")
    logger.info(
        "Step 2: CSV読み込み完了",
        extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)}
    )

    # ========================================
    # Step 2b: ベースDataFrame構築（型変換）
    # ========================================
    # 🔥 最適化ポイント: 
    #   - 業者CDの型変換を一度だけ実行（従来は各関数内で重複実行）
    #   - DataFrameのcopy()を最小限に
    step_start = time.time()
    base_data = build_factory_report_base_data(df_dict)
    logger.info(
        "Step 2b: ベースDataFrame構築完了",
        extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)}
    )

    # ========================================
    # Step 3: DataFrame存在確認
    # ========================================
    # base_dataから前処理済みDataFrameを取得
    df_shipment = base_data.df_shipment
    df_yard = base_data.df_yard
    # ========================================
    # Step 3: DataFrame存在確認
    # ========================================
    has_shipment = df_shipment is not None and not df_shipment.empty
    has_yard = df_yard is not None and not df_yard.empty

    if not has_shipment:
        logger.error("出荷データ(shipment)が存在しないか空です。")
    if not has_yard:
        logger.error("ヤードデータ(yard)が存在しないか空です。")

    # ========================================
    # Step 4: 個別ドメイン処理
    # ========================================
    # Step 4a: 処分データ処理
    step_start = time.time()
    logger.info("Step 4a: 出荷処分データ処理開始")
    if has_shipment and df_shipment is not None:
        master_csv_shobun = process_shobun(df_shipment)
        logger.info(
            "Step 4a: 処分データ処理完了",
            extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)}
        )
    else:
        logger.warning("出荷データが無いため、処分データ処理をスキップします。")
        master_csv_shobun = pd.DataFrame()

    # Step 4b: 有価データ処理
    step_start = time.time()
    logger.info("Step 4b: 出荷有価データ処理開始")
    if has_yard and has_shipment and df_yard is not None and df_shipment is not None:
        master_csv_yuka = process_yuuka(df_yard, df_shipment)
        logger.info(
            "Step 4b: 有価データ処理完了",
            extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)}
        )
    else:
        logger.warning("必要データが不足のため、有価データ処理をスキップします。")
        master_csv_yuka = pd.DataFrame()

    # Step 4c: ヤードデータ処理
    step_start = time.time()
    logger.info("Step 4c: 出荷ヤードデータ処理開始")
    if has_yard and has_shipment and df_yard is not None and df_shipment is not None:
        master_csv_yard = process_yard(df_yard, df_shipment)
        logger.info(
            "Step 4c: ヤードデータ処理完了",
            extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)}
        )
    else:
        logger.warning("必要データが不足のため、ヤードデータ処理をスキップします。")
        master_csv_yard = pd.DataFrame()

    # ========================================
    # Step 5: 結合・整形処理
    # ========================================
    step_start = time.time()
    logger.info("Step 5: 結合・整形処理開始")
    combined_df = pd.concat(
        [master_csv_yuka, master_csv_shobun, master_csv_yard], ignore_index=True
    )

    # セル番号の設定
    combined_df = make_cell_num(combined_df)

    # ラベルの追加
    combined_df = make_label(combined_df)

    # --- 合計・総合計行の追加/更新 ---
    combined_df = generate_summary_dataframe(combined_df)

    # 日付の挿入
    combined_df = date_format(combined_df, df_shipment)

    # --- セル行順にソート ---
    combined_df = sort_by_cell_row(combined_df)

    logger.info(
        "Step 5: 結合・整形処理完了",
        extra={"elapsed_ms": round((time.time() - step_start) * 1000, 2)}
    )

    # ========================================
    # 処理完了
    # ========================================
    total_elapsed = time.time() - start_time
    logger.info(
        "工場日報処理完了",
        extra={"total_elapsed_sec": round(total_elapsed, 3)}
    )

    # --- インデックスをリセットして返す ---
    return combined_df.reset_index(drop=True)
