"""Management Sheet Domain Model."""
from dataclasses import dataclass
from datetime import date
from typing import List
import pandas as pd


@dataclass
class ManagementSheet:
    """経営管理表エンティティ"""
    report_date: date
    shipment_items: List
    yard_items: List
    receive_items: List

    @classmethod
    def from_dataframes(cls, df_shipment, df_yard, df_receive):
        from app.core.domain.reports.report_utils import (
            extract_report_date,
            convert_to_shipment_items,
            convert_to_yard_items,
            convert_to_receive_items,
        )
        
        # 共通ユーティリティを使用して日付抽出とデータ変換
        report_date = extract_report_date(
            (df_shipment, "伝票日付"),
            (df_receive, "伝票日付"),
        )
        
        shipment_items = convert_to_shipment_items(df_shipment)
        yard_items = convert_to_yard_items(df_yard)
        receive_items = convert_to_receive_items(df_receive, report_date)

        return cls(report_date, shipment_items, yard_items, receive_items)
