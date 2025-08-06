from backend_shared.config.config_loader import SyogunCsvConfigLoader
from backend_shared.src.csv_formatter.formatter_factory import CSVFormatterFactory
from backend_shared.src.csv_formatter.formatter_config import build_formatter_config


class CsvFormatterService:
    def __init__(self):
        self.loader = SyogunCsvConfigLoader()

    def format(self, dfs):
        df_formatted = {}
        for csv_type, df in dfs.items():
            config = build_formatter_config(self.loader, csv_type)
            formatter = CSVFormatterFactory.get_formatter(csv_type, config)
            df_formatted[csv_type] = formatter.format(df)
        return df_formatted
