import pandas as pd
from .base import BaseCSVFormatter

from backend_shared.csv_formatter.formatter import (
    ShipmentFormatter,
    BaseCSVFormatter,
    ReceiveFormatter,
    YardFormatter,
    DefaultFormatter,
)

# =========================
# ファクトリ（種別に応じてFormatterを返す）
# =========================


class CSVFormatterFactory:
    @staticmethod
    def get_formatter(csv_type: str) -> BaseCSVFormatter:
        if csv_type == "shipment":
            return ShipmentFormatter()
        elif csv_type == "receive":
            return ReceiveFormatter()
        elif csv_type == "yard":
            return YardFormatter()
        else:
            return DefaultFormatter()


# =========================
# 利用例
# =========================

if __name__ == "__main__":
    # 例: 使い方
    # df = pd.read_csv("shipment.csv")
    # formatter = CSVFormatterFactory.get_formatter("shipment")
    # df_formatted = formatter.format(df)
    pass
