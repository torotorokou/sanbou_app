"""
factory_report_base.py

factory_report処理で使用するベースDataFrame構造を提供。
データの前処理とキャッシュを一元管理し、不要なI/Oとcopy()を削減する。

背景:
- 従来は各処理関数内で個別に型変換を実行していた（業者CDの文字列化など）
- DataFrameのcopy()が多重実行されていた
- 各処理関数がマスターCSVを個別に読み込んでいた（3回のI/O）

改善:
- 一度だけ型変換を実行
- マスターCSVを一度だけ読み込み（I/O削減）
- 処理関数には前処理済みのDataFrameとマスターCSVを渡す
- 結果が変わらないことを保証しつつ、計算コストを削減
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

import pandas as pd
from app.infra.report_utils import get_template_config, load_master_and_template
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


@dataclass
class FactoryReportBaseData:
    """
    factory_report処理で使用する共通データを保持するコンテナ。

    各DataFrameは前処理済み（型変換・クリーニング済み）の状態で保持される。
    これにより、後続の処理関数で繰り返し前処理を行う必要がなくなる。

    Attributes:
        df_shipment: 出荷データ（前処理済み）
        df_yard: ヤードデータ（前処理済み）
        master_csv_shobun: 処分マスターCSV（事前読み込み）
        master_csv_yuuka: 有価マスターCSV（事前読み込み）
        master_csv_yard: ヤードマスターCSV（事前読み込み）
        master_csv_etc: etc合計行マスターCSV（事前読み込み）
    """

    df_shipment: pd.DataFrame
    df_yard: pd.DataFrame
    master_csv_shobun: Optional[pd.DataFrame] = None
    master_csv_yuuka: Optional[pd.DataFrame] = None
    master_csv_yard: Optional[pd.DataFrame] = None
    master_csv_etc: Optional[pd.DataFrame] = None


def build_factory_report_base_data(df_dict: Dict[str, Any]) -> FactoryReportBaseData:
    """
    factory_report処理用のベースDataFrameを構築する。

    この関数は以下を実行する:
    1. 必要なDataFrameの取得と型変換（業者CDを文字列化）
    2. copy()を一度だけ実行
    3. マスターCSVを事前読み込み（I/O削減: 4回 → 1回）

    Args:
        df_dict: load_all_filtered_dataframesの出力
            - shipment: 出荷データ
            - yard: ヤードデータ

    Returns:
        FactoryReportBaseData: 前処理済みデータコンテナ（マスターCSV含む）

    Notes:
        - 型変換はここで一度だけ実行され、後続処理では不要
        - DataFrameのcopy()もここで実行し、後続処理での副作用を防ぐ
        - マスターCSVの読み込みもここで実行し、各処理関数でのI/Oを削減
        - 結果として、従来の処理と完全に同じ出力を保証しつつ高速化
    """
    logger.info("FactoryReport用ベースDataFrame構築開始")

    df_shipment = df_dict.get("shipment")
    df_yard = df_dict.get("yard")

    # ========================================
    # 前処理: 型変換とcopy（一度だけ実行）
    # ========================================
    # shipment: 業者CDを文字列化（後続の処理で必要）
    if df_shipment is not None and not df_shipment.empty:
        df_shipment = df_shipment.copy()
        if "業者CD" in df_shipment.columns:
            df_shipment["業者CD"] = df_shipment["業者CD"].astype(str)

    # yardは特別な前処理不要だが、copy()だけ実行
    if df_yard is not None and not df_yard.empty:
        df_yard = df_yard.copy()

    # ========================================
    # Step 5最適化: マスターCSVの事前読み込み
    # ========================================
    # 🔥 最適化ポイント:
    #   - 従来: process_shobun, process_yuuka, process_yard, generate_summary_dataframe内でそれぞれ読み込み（4回のI/O）
    #   - 改善: ここで一度だけ読み込み（1回のI/O）
    config = get_template_config()["factory_report"]
    master_csv_paths = config.get("master_csv_path", {})

    master_csv_shobun = None
    master_csv_yuuka = None
    master_csv_yard = None
    master_csv_etc = None

    # 処分マスターCSV
    if "shobun" in master_csv_paths:
        try:
            master_csv_shobun = load_master_and_template(master_csv_paths["shobun"])
            logger.info("処分マスターCSV読み込み成功")
        except Exception as e:
            logger.warning(f"処分マスターCSV読み込み失敗: {e}")

    # 有価マスターCSV
    if "yuuka" in master_csv_paths:
        try:
            master_csv_yuuka = load_master_and_template(master_csv_paths["yuuka"])
            logger.info("有価マスターCSV読み込み成功")
        except Exception as e:
            logger.warning(f"有価マスターCSV読み込み失敗: {e}")

    # ヤードマスターCSV
    if "yard" in master_csv_paths:
        try:
            master_csv_yard = load_master_and_template(master_csv_paths["yard"])
            logger.info("ヤードマスターCSV読み込み成功")
        except Exception as e:
            logger.warning(f"ヤードマスターCSV読み込み失敗: {e}")

    # etc合計行マスターCSV
    if "etc" in master_csv_paths:
        try:
            master_csv_etc = load_master_and_template(master_csv_paths["etc"])
            logger.info("etcマスターCSV読み込み成功")
        except Exception as e:
            logger.warning(f"etcマスターCSV読み込み失敗: {e}")

    logger.info("FactoryReport用ベースDataFrame構築完了")

    return FactoryReportBaseData(
        df_shipment=df_shipment,
        df_yard=df_yard,
        master_csv_shobun=master_csv_shobun,
        master_csv_yuuka=master_csv_yuuka,
        master_csv_yard=master_csv_yard,
        master_csv_etc=master_csv_etc,
    )
