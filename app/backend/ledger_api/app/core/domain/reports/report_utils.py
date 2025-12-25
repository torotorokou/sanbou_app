"""
Report共通ユーティリティモジュール

全レポートで共通する処理を集約:
- 日付抽出ロジック
- DataFrameからValue Objectへの変換処理
"""

from datetime import date
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from app.core.domain.reports.balance_sheet import ReceiveItem
    from app.core.domain.reports.factory_report import ShipmentItem, YardItem


def extract_report_date(
    *dataframes_with_columns: tuple[pd.DataFrame | None, str]
) -> date:
    """
    複数のDataFrameから優先順位に従って日付を抽出する

    Args:
        *dataframes_with_columns: (DataFrame, カラム名) のタプル（優先順）

    Returns:
        date: 抽出した日付、見つからない場合は当日

    Examples:
        >>> report_date = extract_report_date(
        ...     (df_shipment, "伝票日付"),
        ...     (df_receive, "伝票日付"),
        ...     (df_yard, "伝票日付")
        ... )
    """
    for df, column_name in dataframes_with_columns:
        if df is None or df.empty:
            continue

        if column_name not in df.columns:
            continue

        if df[column_name].isna().all():
            continue

        first_date = df[column_name].iloc[0]
        if pd.notna(first_date):
            return pd.to_datetime(first_date).date()

    # フォールバック: 今日の日付
    return date.today()


def convert_to_shipment_items(
    df_shipment: pd.DataFrame | None,
) -> list["ShipmentItem"]:
    """
    出荷DataFrameをShipmentItemリストに変換

    Args:
        df_shipment: 出荷データのDataFrame

    Returns:
        List[ShipmentItem]: 変換された出荷アイテムリスト
    """
    from app.core.domain.reports.factory_report import ShipmentItem

    shipment_items: list[ShipmentItem] = []

    if df_shipment is None or df_shipment.empty:
        return shipment_items

    for _, row in df_shipment.iterrows():
        try:
            shipment_items.append(
                ShipmentItem(
                    vendor_code=str(row.get("業者CD", "")),
                    vendor_name=str(row.get("業者名", "")),
                    item_name=str(row.get("品名", "")),
                    net_weight=float(row.get("正味重量", 0.0)),
                    site_name=(
                        str(row.get("現場名", ""))
                        if pd.notna(row.get("現場名"))
                        else None
                    ),
                )
            )
        except (ValueError, TypeError):
            # データ不正の場合はスキップ
            continue

    return shipment_items


def convert_to_yard_items(df_yard: pd.DataFrame | None) -> list["YardItem"]:
    """
    ヤードDataFrameをYardItemリストに変換

    Args:
        df_yard: ヤードデータのDataFrame

    Returns:
        List[YardItem]: 変換されたヤードアイテムリスト
    """
    from app.core.domain.reports.factory_report import YardItem

    yard_items: list[YardItem] = []

    if df_yard is None or df_yard.empty:
        return yard_items

    for _, row in df_yard.iterrows():
        try:
            yard_items.append(
                YardItem(
                    item_group=str(row.get("品目名", "")),
                    category_name=str(row.get("種類名", "")),
                    item_name=str(row.get("品名", "")),
                    net_weight=float(row.get("正味重量", 0.0)),
                )
            )
        except (ValueError, TypeError):
            continue

    return yard_items


def convert_to_receive_items(
    df_receive: pd.DataFrame | None, default_date: date
) -> list["ReceiveItem"]:
    """
    受入DataFrameをReceiveItemリストに変換

    Args:
        df_receive: 受入データのDataFrame
        default_date: デフォルトの伝票日付

    Returns:
        List[ReceiveItem]: 変換された受入アイテムリスト
    """
    from app.core.domain.reports.balance_sheet import ReceiveItem

    receive_items: list[ReceiveItem] = []

    if df_receive is None or df_receive.empty:
        return receive_items

    for _, row in df_receive.iterrows():
        try:
            slip_date = default_date
            if "伝票日付" in row and pd.notna(row["伝票日付"]):
                slip_date = pd.to_datetime(row["伝票日付"]).date()

            receive_items.append(
                ReceiveItem(
                    slip_date=slip_date,
                    site_name=str(row.get("現場名", "")),
                    net_weight=float(row.get("正味重量", 0.0)),
                    volume=(
                        float(row["体積"])
                        if "体積" in row and pd.notna(row["体積"])
                        else None
                    ),
                    item_name=(
                        str(row["品名"])
                        if "品名" in row and pd.notna(row["品名"])
                        else None
                    ),
                )
            )
        except (ValueError, TypeError):
            continue

    return receive_items
