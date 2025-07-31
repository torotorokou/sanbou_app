from backend_shared.src.csv_formatter.formatter_base import BaseCSVFormatter
from backend_shared.src.csv_formatter.formatter_impls import (
    ShipmentFormatter,
    ReceiveFormatter,
    YardFormatter,
    DefaultFormatter,
)
from backend_shared.src.csv_formatter.formatter_config import FormatterConfig

# =========================
# ファクトリ
# =========================


class CSVFormatterFactory:
    """
    CSV種別ごとのFormatterインスタンスを生成するファクトリクラス。

    Example:
        loader = SyogunCsvConfigLoader()
        config = build_formatter_config(loader, "shipment")
        formatter = CSVFormatterFactory.get_formatter("shipment", config)
        df_formatted = formatter.format(df)
    """

    @staticmethod
    def get_formatter(csv_type: str, config: FormatterConfig) -> BaseCSVFormatter:
        if csv_type == "shipment":
            return ShipmentFormatter(config)
        elif csv_type == "receive":
            return ReceiveFormatter(config)
        elif csv_type == "yard":
            return YardFormatter(config)
        else:
            return DefaultFormatter()


if __name__ == "__main__":
    # from backend_shared.config.config_loader import SyogunCsvConfigLoader
    # config_loader = SyogunCsvConfigLoader()
    # columns_def = config_loader.get_columns("shipment")
    # df = pd.read_csv("shipment.csv")
    # formatter = CSVFormatterFactory.get_formatter("shipment", columns_def)
    # df_formatted = formatter.format(df)
    pass
