"""
Balance Sheet Domain Model.

搬出入収支表のドメインモデル。
"""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

import pandas as pd


@dataclass(frozen=True)
class ReceiveItem:
    """
    受入データの値オブジェクト

    Attributes:
        slip_date: 伝票日付
        site_name: 現場名
        net_weight: 正味重量
        volume: 体積（m3）
        item_name: 品名
    """

    slip_date: date
    site_name: str
    net_weight: float
    volume: Optional[float] = None
    item_name: Optional[str] = None

    def __post_init__(self):
        if self.net_weight < 0:
            raise ValueError(f"正味重量は0以上である必要があります: {self.net_weight}")
        if self.volume is not None and self.volume < 0:
            raise ValueError(f"体積は0以上である必要があります: {self.volume}")


@dataclass
class BalanceSheet:
    """
    搬出入収支表エンティティ（Aggregate Root）

    受入・出荷・ヤードデータから収支表を生成するドメインエンティティ。

    Attributes:
        report_date: レポート対象日
        receive_items: 受入データリスト
        shipment_items: 出荷データリスト（factory_reportから再利用）
        yard_items: ヤードデータリスト（factory_reportから再利用）
    """

    report_date: date
    receive_items: List[ReceiveItem]
    shipment_items: List  # ShipmentItem型だが循環参照回避のためList
    yard_items: List  # YardItem型

    @classmethod
    def from_dataframes(
        cls,
        df_receive: Optional[pd.DataFrame],
        df_shipment: Optional[pd.DataFrame],
        df_yard: Optional[pd.DataFrame],
    ) -> "BalanceSheet":
        """
        DataFrameから搬出入収支表エンティティを生成

        Args:
            df_receive: 受入データのDataFrame
            df_shipment: 出荷データのDataFrame
            df_yard: ヤードデータのDataFrame

        Returns:
            BalanceSheet: 搬出入収支表エンティティ
        """
        from app.core.domain.reports.report_utils import (
            convert_to_receive_items,
            convert_to_shipment_items,
            convert_to_yard_items,
            extract_report_date,
        )

        # 共通ユーティリティを使用して日付抽出とデータ変換
        report_date = extract_report_date(
            (df_shipment, "伝票日付"),
            (df_receive, "伝票日付"),
        )

        receive_items = convert_to_receive_items(df_receive, report_date)
        shipment_items = convert_to_shipment_items(df_shipment)
        yard_items = convert_to_yard_items(df_yard)

        return cls(
            report_date=report_date,
            receive_items=receive_items,
            shipment_items=shipment_items,
            yard_items=yard_items,
        )

    def has_receive_data(self) -> bool:
        """受入データの存在確認"""
        return len(self.receive_items) > 0

    def has_shipment_data(self) -> bool:
        """出荷データの存在確認"""
        return len(self.shipment_items) > 0

    def has_yard_data(self) -> bool:
        """ヤードデータの存在確認"""
        return len(self.yard_items) > 0

    def calculate_total_receive_weight(self) -> float:
        """受入データの総重量を計算"""
        return sum(item.net_weight for item in self.receive_items)

    def calculate_total_receive_volume(self) -> float:
        """受入データの総体積を計算"""
        return sum(
            item.volume for item in self.receive_items if item.volume is not None
        )

    def count_receive_trucks(self) -> int:
        """受入台数をカウント（簡易実装: 受入件数）"""
        return len(self.receive_items)
