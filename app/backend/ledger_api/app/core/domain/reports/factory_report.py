"""
Factory Report Domain Model.

工場日報のドメインモデル。
DataFrame依存を緩和し、ビジネスロジックをドメイン層に集約する。
"""

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class ShipmentItem:
    """
    出荷データの値オブジェクト（Value Object）

    Attributes:
        vendor_code: 業者コード
        vendor_name: 業者名
        item_name: 品名
        net_weight: 正味重量
        site_name: 現場名（オプション）
    """

    vendor_code: str
    vendor_name: str
    item_name: str
    net_weight: float
    site_name: str | None = None

    def __post_init__(self):
        """不変条件（Invariant）の検証"""
        if self.net_weight < 0:
            raise ValueError(f"正味重量は0以上である必要があります: {self.net_weight}")


@dataclass(frozen=True)
class YardItem:
    """
    ヤードデータの値オブジェクト（Value Object）

    Attributes:
        item_group: 品目名
        category_name: 種類名
        item_name: 品名
        net_weight: 正味重量
    """

    item_group: str
    category_name: str
    item_name: str
    net_weight: float

    def __post_init__(self):
        """不変条件（Invariant）の検証"""
        if self.net_weight < 0:
            raise ValueError(f"正味重量は0以上である必要があります: {self.net_weight}")


@dataclass(frozen=True)
class ReportCell:
    """
    レポート上のセル情報を表す値オブジェクト

    Attributes:
        category: カテゴリ（有価/ヤード/処分）
        main_item: 大項目（業者名、有価名、品目名など）
        cell: セル番号
        value: 値
        cell_lock: セルロック（編集可否）
        order: 順番
    """

    category: str
    main_item: str
    cell: str
    value: float
    cell_lock: bool
    order: int


@dataclass
class FactoryReport:
    """
    工場日報エンティティ（Aggregate Root）

    工場日報の生成と管理を担当するドメインエンティティ。
    出荷データとヤードデータから帳票を生成し、ビジネスルールを適用する。

    Attributes:
        report_date: レポート対象日
        shipment_items: 出荷データリスト
        yard_items: ヤードデータリスト
        cells: レポートセルのリスト
    """

    report_date: date
    shipment_items: list[ShipmentItem]
    yard_items: list[YardItem]
    cells: list[ReportCell]

    @classmethod
    def from_dataframes(
        cls,
        df_shipment: pd.DataFrame | None,
        df_yard: pd.DataFrame | None,
    ) -> "FactoryReport":
        """
        DataFrameから工場日報エンティティを生成する

        Args:
            df_shipment: 出荷データのDataFrame
            df_yard: ヤードデータのDataFrame

        Returns:
            FactoryReport: 工場日報エンティティ
        """
        from app.core.domain.reports.report_utils import (
            convert_to_shipment_items,
            convert_to_yard_items,
            extract_report_date,
        )

        # 共通ユーティリティを使用して日付抽出とデータ変換
        report_date = extract_report_date(
            (df_shipment, "伝票日付"),
            (df_yard, "伝票日付"),
        )

        shipment_items = convert_to_shipment_items(df_shipment)
        yard_items = convert_to_yard_items(df_yard)

        return cls(
            report_date=report_date,
            shipment_items=shipment_items,
            yard_items=yard_items,
            cells=[],  # 初期状態では空
        )

    def to_dataframe(self) -> pd.DataFrame:
        """
        レポートセル情報をDataFrameに変換する

        Returns:
            pd.DataFrame: レポートの最終形式DataFrame
        """
        if not self.cells:
            return pd.DataFrame(
                columns=["カテゴリ", "大項目", "セル", "値", "セルロック", "順番"]
            )

        data = [
            {
                "カテゴリ": cell.category,
                "大項目": cell.main_item,
                "セル": cell.cell,
                "値": cell.value,
                "セルロック": cell.cell_lock,
                "順番": cell.order,
            }
            for cell in self.cells
        ]

        return pd.DataFrame(data)

    def has_shipment_data(self) -> bool:
        """出荷データの存在確認"""
        return len(self.shipment_items) > 0

    def has_yard_data(self) -> bool:
        """ヤードデータの存在確認"""
        return len(self.yard_items) > 0

    def get_shipment_by_vendor(self, vendor_code: str) -> list[ShipmentItem]:
        """特定業者の出荷データを取得"""
        return [item for item in self.shipment_items if item.vendor_code == vendor_code]

    def get_yard_by_category(self, category_name: str) -> list[YardItem]:
        """特定種類名のヤードデータを取得"""
        return [item for item in self.yard_items if item.category_name == category_name]

    def calculate_total_shipment_weight(self) -> float:
        """出荷データの総重量を計算"""
        return sum(item.net_weight for item in self.shipment_items)

    def calculate_total_yard_weight(self) -> float:
        """ヤードデータの総重量を計算"""
        return sum(item.net_weight for item in self.yard_items)
