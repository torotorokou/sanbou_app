"""
factory_report_base.py

factory_report処理で使用するベースDataFrame構造を提供。
データの前処理とキャッシュを一元管理し、不要なI/Oとcopy()を削減する。

背景:
- 従来は各処理関数内で個別に型変換を実行していた（業者CDの文字列化など）
- DataFrameのcopy()が多重実行されていた

改善:
- 一度だけ型変換を実行
- 処理関数には前処理済みのDataFrameを渡す
- 結果が変わらないことを保証しつつ、計算コストを削減
"""
from typing import Any, Dict
import pandas as pd
from dataclasses import dataclass

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
    """
    df_shipment: pd.DataFrame
    df_yard: pd.DataFrame


def build_factory_report_base_data(df_dict: Dict[str, Any]) -> FactoryReportBaseData:
    """
    factory_report処理用のベースDataFrameを構築する。
    
    この関数は以下を実行する:
    1. 必要なDataFrameの取得と型変換（業者CDを文字列化）
    2. copy()を一度だけ実行
    
    Args:
        df_dict: load_all_filtered_dataframesの出力
            - shipment: 出荷データ
            - yard: ヤードデータ
    
    Returns:
        FactoryReportBaseData: 前処理済みデータコンテナ
    
    Notes:
        - 型変換はここで一度だけ実行され、後続処理では不要
        - DataFrameのcopy()もここで実行し、後続処理での副作用を防ぐ
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
    
    logger.info("FactoryReport用ベースDataFrame構築完了")
    
    return FactoryReportBaseData(
        df_shipment=df_shipment,
        df_yard=df_yard,
    )
