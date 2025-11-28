"""
CSVフォーマッターサービス

CSVデータのフォーマット変換を行うサービスクラスです。
設定ファイルに基づいて、CSVタイプごとに適切なフォーマッターを適用します。
"""

from backend_shared.config.config_loader import ShogunCsvConfigLoader
from backend_shared.core.usecases.csv_formatter.formatter_factory import CSVFormatterFactory
from backend_shared.core.usecases.csv_formatter.formatter_config import build_formatter_config


class CsvFormatterService:
    """
    CSVフォーマット変換サービス

    複数のCSVファイルに対して、それぞれのタイプに応じた
    フォーマット処理を実行するサービスクラスです。
    """

    def __init__(self):
        """
        サービスの初期化

        設定ローダーを初期化し、フォーマット処理の準備を行います。
        """
        # 昇軍CSV設定ローダーの初期化
        self.loader = ShogunCsvConfigLoader()

    def format(self, dfs):
        """
        複数のDataFrameをフォーマット

        各CSVタイプに対応するフォーマッターを使用して、
        DataFrameを適切な形式に変換します。

        Args:
            dfs (Dict[str, DataFrame]): CSVタイプをキーとするDataFrameの辞書

        Returns:
            Dict[str, DataFrame]: フォーマット済みのDataFrameの辞書
        """
        df_formatted = {}

        # 各CSVタイプに対してフォーマット処理を実行
        for csv_type, df in dfs.items():
            # CSVタイプに応じた設定を構築
            config = build_formatter_config(self.loader, csv_type)
            # 適切なフォーマッターを取得
            formatter = CSVFormatterFactory.get_formatter(csv_type, config)
            # DataFrameをフォーマット
            df_formatted[csv_type] = formatter.format(df)

        return df_formatted
