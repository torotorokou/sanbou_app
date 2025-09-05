
# 将軍CSV自動整形・集約ツール

from backend_shared.config.config_loader import SyogunCsvConfigLoader
from backend_shared.formatter.formatter_config import build_formatter_config, FormatterConfig
from backend_shared.formatter.formatter import CSVFormatter

# 1. 設定ファイル（YAML）からローダーを作成
loader = SyogunCsvConfigLoader()

# 2. build_formatter_configでFormatterConfigを作成（例: "shipment" = 出荷一覧）
config = build_formatter_config(loader, "shipment")

# 3. FormatterにConfigを渡して初期化
formatter = CSVFormatter(config)

# 4. DataFrameを整形（raw_dfはpandasのDataFrameでCSV読込済みのもの）
clean_df = formatter.format(raw_df)
