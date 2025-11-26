"""Block Unit Price Domain Model."""
from dataclasses import dataclass
from datetime import date
from typing import List
import pandas as pd


@dataclass
class BlockUnitPrice:
    """ブロック単価表エンティティ"""
    report_date: date
    shipment_items: List
    yard_items: List
    receive_items: List

    @classmethod
    def from_dataframes(cls, df_shipment, df_yard, df_receive):
        from app.application.domain.reports.factory_report import ShipmentItem, YardItem
        from app.application.domain.reports.balance_sheet import ReceiveItem
        
        shipment_items, yard_items, receive_items = [], [], []
        report_date = date.today()

        for df, col in [(df_shipment, "伝票日付"), (df_receive, "伝票日付")]:
            if df is not None and not df.empty and col in df.columns and not df[col].isna().all():
                report_date = pd.to_datetime(df[col].dropna().iloc[0]).date()
                break

        if df_shipment is not None and not df_shipment.empty:
            for _, row in df_shipment.iterrows():
                try:
                    shipment_items.append(ShipmentItem(
                        vendor_code=str(row.get("業者CD", "")),
                        vendor_name=str(row.get("業者名", "")),
                        item_name=str(row.get("品名", "")),
                        net_weight=float(row.get("正味重量", 0.0)),
                        site_name=str(row.get("現場名", "")) if pd.notna(row.get("現場名")) else None,
                    ))
                except:
                    pass

        if df_yard is not None and not df_yard.empty:
            for _, row in df_yard.iterrows():
                try:
                    yard_items.append(YardItem(
                        item_group=str(row.get("品目名", "")),
                        category_name=str(row.get("種類名", "")),
                        item_name=str(row.get("品名", "")),
                        net_weight=float(row.get("正味重量", 0.0)),
                    ))
                except:
                    pass

        if df_receive is not None and not df_receive.empty:
            for _, row in df_receive.iterrows():
                try:
                    slip_date = report_date
                    if "伝票日付" in row and pd.notna(row["伝票日付"]):
                        slip_date = pd.to_datetime(row["伝票日付"]).date()
                    receive_items.append(ReceiveItem(
                        slip_date=slip_date,
                        site_name=str(row.get("現場名", "")),
                        net_weight=float(row.get("正味重量", 0.0)),
                        volume=float(row["体積"]) if "体積" in row and pd.notna(row["体積"]) else None,
                        item_name=str(row["品名"]) if "品名" in row and pd.notna(row["品名"]) else None,
                    ))
                except:
                    pass

        return cls(report_date, shipment_items, yard_items, receive_items)
