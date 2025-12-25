"""
balance_sheet_base.py

balance_sheet処理で使用するベースDataFrame構造を提供。
データの前処理とキャッシュを一元管理し、不要なI/Oとcopy()を削減する。

背景:
- 従来は各処理関数内で個別にマスターCSVや単価テーブルを読み込んでいた
- 型変換（astype, to_numeric）も重複して実行されていた
- summary_applyとmultiply_columnsでDataFrameのcopy()が多重実行されていた

改善:
- 一度だけ読み込み、型変換も一度だけ実行
- 処理関数には前処理済みのDataFrameを渡す
- 結果が変わらないことを保証しつつ、I/Oと計算コストを削減
"""

from dataclasses import dataclass
from typing import Any

import pandas as pd
from app.infra.report_utils import get_unit_price_table_csv
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


@dataclass
class BalanceSheetBaseData:
    """
    balance_sheet処理で使用する共通データを保持するコンテナ。

    各DataFrameは前処理済み（型変換・クリーニング済み）の状態で保持される。
    これにより、後続の処理関数で繰り返し前処理を行う必要がなくなる。

    Attributes:
        df_receive: 受入データ（前処理済み）
        df_shipment: 出荷データ（前処理済み）
        df_yard: ヤードデータ（前処理済み）
        unit_price_table: 単価テーブル（共通使用、1回だけ読み込み）
        target_day: 対象日（伝票日付から決定）
    """

    df_receive: pd.DataFrame | None
    df_shipment: pd.DataFrame | None
    df_yard: pd.DataFrame | None
    unit_price_table: pd.DataFrame
    target_day: pd.Timestamp


def build_balance_sheet_base_data(df_dict: dict[str, Any]) -> BalanceSheetBaseData:
    """
    balance_sheet処理用のベースDataFrameを構築する。

    この関数は以下を実行する:
    1. 必要なDataFrameの取得と型変換（業者CD, 品名等を文字列化）
    2. 単価テーブルの読み込み（1回のみ）
    3. 対象日の決定（伝票日付から）

    Args:
        df_dict: load_all_filtered_dataframesの出力
            - receive: 受入データ
            - shipment: 出荷データ
            - yard: ヤードデータ

    Returns:
        BalanceSheetBaseData: 前処理済みデータコンテナ

    Notes:
        - 型変換はここで一度だけ実行され、後続処理では不要
        - DataFrameのcopy()もここで実行し、後続処理での副作用を防ぐ
        - 結果として、従来の処理と完全に同じ出力を保証しつつ高速化
    """
    logger.info("ベースDataFrame構築開始")

    df_receive = df_dict.get("receive")
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

    # receive, yardは現状では特別な前処理不要だが、
    # 将来的な拡張のためcopy()だけ実行
    if df_receive is not None and not df_receive.empty:
        df_receive = df_receive.copy()

    if df_yard is not None and not df_yard.empty:
        df_yard = df_yard.copy()

    # ========================================
    # 単価テーブル読み込み（1回のみ）
    # ========================================
    # 従来は calculate_safe_disposal_costs, calculate_yard_disposal_costs,
    # calculate_valuable_material_cost_by_item で個別に読み込んでいた
    # → 3回のI/Oを1回に削減
    unit_price_table = get_unit_price_table_csv()
    logger.info(f"単価テーブル読み込み完了: {len(unit_price_table)} 件")

    # ========================================
    # 対象日決定
    # ========================================
    if (
        df_shipment is not None
        and not df_shipment.empty
        and "伝票日付" in df_shipment.columns
    ):
        target_day = pd.to_datetime(df_shipment["伝票日付"].dropna().iloc[0])
    elif (
        df_receive is not None
        and not df_receive.empty
        and "伝票日付" in df_receive.columns
    ):
        target_day = pd.to_datetime(df_receive["伝票日付"].dropna().iloc[0])
    else:
        target_day = pd.Timestamp.today()

    logger.info(f"ベースDataFrame構築完了: 対象日={target_day.strftime('%Y-%m-%d')}")

    return BalanceSheetBaseData(
        df_receive=df_receive,
        df_shipment=df_shipment,
        df_yard=df_yard,
        unit_price_table=unit_price_table,
        target_day=target_day,
    )
