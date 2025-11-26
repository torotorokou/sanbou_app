"""
Average Sheet Domain Model.

単価平均表のドメインモデル。
"""
from dataclasses import dataclass
from datetime import date
from typing import List, Optional
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
    shipment_items: List  # ShipmentItem型
    yard_items: List  # YardItem型
    receive_items: List  # ReceiveItem型

    @classmethod
    def from_dataframes(
        cls,
        df_shipment: Optional[pd.DataFrame],
        df_yard: Optional[pd.DataFrame],
        df_receive: Optional[pd.DataFrame],
    ) -> "AverageSheet":
        """DataFrameから単価平均表エンティティを生成"""
        from app.core.domain.reports.factory_report import ShipmentItem, YardItem
        from app.core.domain.reports.balance_sheet import ReceiveItem
        
        shipment_items: List[ShipmentItem] = []
        yard_items: List[YardItem] = []
        receive_items: List[ReceiveItem] = []
        report_date = date.today()

        # 日付抽出
        for df, col in [(df_shipment, "伝票日付"), (df_receive, "伝票日付")]:
            if df is not None and not df.empty and col in df.columns:
                first_date = df[col].dropna().iloc[0] if not df[col].isna().all() else None
                if pd.notna(first_date):
                    report_date = pd.to_datetime(first_date).date()
                    break

        # データ変換（balance_sheetパターン再利用）
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
                except (ValueError, TypeError):
                    continue

        if df_yard is not None and not df_yard.empty:
            for _, row in df_yard.iterrows():
                try:
                    yard_items.append(YardItem(
                        item_group=str(row.get("品目名", "")),
                        category_name=str(row.get("種類名", "")),
                        item_name=str(row.get("品名", "")),
                        net_weight=float(row.get("正味重量", 0.0)),
                    ))
                except (ValueError, TypeError):
                    continue

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
                except (ValueError, TypeError):
                    continue

        return cls(
            report_date=report_date,
            shipment_items=shipment_items,
            yard_items=yard_items,
            receive_items=receive_items,
        )

    def has_any_data(self) -> bool:
        """いずれかのデータが存在するか確認"""
        return len(self.shipment_items) > 0 or len(self.yard_items) > 0 or len(self.receive_items) > 0
