import pandas as pd

from backend_shared.csv_formatter.formatter_factory import CSVFormatterFactory
from backend_shared.config.config_loader import SyogunCsvConfigLoader
from backend_shared.csv_formatter.formatter_config import (
    build_formatter_config,
)  # ← 追加


def format_and_rename_for_sql(
    name: str, df: pd.DataFrame, config_loader: SyogunCsvConfigLoader
) -> pd.DataFrame:
    config = build_formatter_config(config_loader, name)  # ← ここでConfigを作る
    formatter = CSVFormatterFactory.get_formatter(
        name, config
    )  # ← dictではなくConfigを渡す
    df_formatted = formatter.format(df)

    # 英語名リネームもConfigから取得した方が安全
    rename_map = {
        ja_col: props["en_name"]
        for ja_col, props in config.columns_def.items()  # ← configから取得
        if ja_col in df_formatted.columns
    }

    df_sql_ready = df_formatted.rename(columns=rename_map)
    return df_sql_ready
