"""
CSVフォーマッターファクトリ

CSV種別に応じた適切なフォーマッターインスタンスを生成するファクトリクラスです。
"""

from backend_shared.core.usecases.csv_formatter.formatter_base import BaseCSVFormatter
from backend_shared.core.usecases.csv_formatter.formatter_config import FormatterConfig
from backend_shared.core.usecases.csv_formatter.formatter_impls import (
    DefaultFormatter,
    ReceiveFormatter,
    ShipmentFormatter,
    YardFormatter,
)


# =========================
# フォーマッターファクトリ
# =========================


class CSVFormatterFactory:
    """
    CSVフォーマッターファクトリ

    CSV種別ごとの適切なFormatterインスタンスを生成するファクトリクラスです。
    各CSVタイプに対応する専用フォーマッターを提供し、統一されたインターフェースで
    フォーマット処理を実行できます。

    Example:
        # 使用例
        loader = ShogunCsvConfigLoader()
        config = build_formatter_config(loader, "shipment")
        formatter = CSVFormatterFactory.get_formatter("shipment", config)
        df_formatted = formatter.format(df)
    """

    @staticmethod
    def get_formatter(csv_type: str, config: FormatterConfig) -> BaseCSVFormatter:
        """
        CSV種別に応じたフォーマッターを取得

        Args:
            csv_type (str): CSV種別 ("shipment", "receive", "yard" など)
            config (FormatterConfig): フォーマッター設定

        Returns:
            BaseCSVFormatter: 指定されたCSV種別に対応するフォーマッターインスタンス
        """
        # CSV種別に応じて適切なフォーマッターを返す
        if csv_type == "shipment":
            return ShipmentFormatter(config)
        elif csv_type == "receive":
            return ReceiveFormatter(config)
        elif csv_type == "yard":
            return YardFormatter(config)
        else:
            # 未知のCSV種別の場合はデフォルトフォーマッターを返す
            return DefaultFormatter()


if __name__ == "__main__":
    # テスト用のサンプルコード（コメントアウト）
    # from backend_shared.infrastructure.config.config_loader import ShogunCsvConfigLoader
    # config_loader = ShogunCsvConfigLoader()
    # columns_def = config_loader.get_columns("shipment")
    # df = pd.read_csv("shipment.csv")
    # formatter = CSVFormatterFactory.get_formatter("shipment", columns_def)
    # df_formatted = formatter.format(df)
    pass
