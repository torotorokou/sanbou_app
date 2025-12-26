"""
Average Sheet Domain Model.

単価平均表のドメインモデル。
"""

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class AverageSheet:
    """
    単価平均表エンティティ（Aggregate Root）

    出荷・ヤード・受入データから単価平均を算出するドメインエンティティ。

    Attributes:
        report_date: レポート対象日
        shipment_items: 出荷データリスト
        yard_items: ヤードデータリスト
        receive_items: 受入データリスト
    """

    report_date: date
    shipment_items: list  # ShipmentItem型
    yard_items: list  # YardItem型
    receive_items: list  # ReceiveItem型

    @classmethod
    def from_dataframes(
        cls,
        df_shipment: pd.DataFrame | None,
        df_yard: pd.DataFrame | None,
        df_receive: pd.DataFrame | None,
    ) -> "AverageSheet":
        """DataFrameから単価平均表エンティティを生成"""
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

        shipment_items = convert_to_shipment_items(df_shipment)
        yard_items = convert_to_yard_items(df_yard)
        receive_items = convert_to_receive_items(df_receive, report_date)

        return cls(
            report_date=report_date,
            shipment_items=shipment_items,
            yard_items=yard_items,
            receive_items=receive_items,
        )

    def has_any_data(self) -> bool:
        """いずれかのデータが存在するか確認"""
        return (
            len(self.shipment_items) > 0 or len(self.yard_items) > 0 or len(self.receive_items) > 0
        )
