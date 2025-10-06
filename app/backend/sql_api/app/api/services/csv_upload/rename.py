import pandas as pd

from backend_shared.csv_formatter.formatter_config import build_formatter_config
from backend_shared.config.config_loader import SyogunCsvConfigLoader


def rename_for_sql(
    name: str, df: pd.DataFrame, config_loader: SyogunCsvConfigLoader
) -> pd.DataFrame:
    """
    YAML定義に基づいて日本語カラム名を英語カラム名にリネームする。
    """
    config = build_formatter_config(config_loader, name)

    rename_map = {
        ja_col: props["en_name"]
        for ja_col, props in config.columns_def.items()
        if ja_col in df.columns
    }

    return df.rename(columns=rename_map)
