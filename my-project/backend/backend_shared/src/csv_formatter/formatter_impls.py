import pandas as pd
from backend_shared.src.csv_formatter.formatter_base import CommonCSVFormatter
from backend_shared.src.utils.dataframe_utils import (
    combine_date_and_time,
    remove_weekday_parentheses,
)
from backend_shared.src.csv_formatter.formatter_config import FormatterConfig


# =========================
# 各CSV種別のフォーマッター
class ShipmentFormatter(CommonCSVFormatter):
    """
    出荷一覧用フォーマッター

    - format() メソッドは親クラス（CommonCSVFormatter）で共通実装されています。
    - 個別の前処理・加工が必要な場合は individual_process(df) をオーバーライドしてください。
    """

    def __init__(self, config: FormatterConfig):
        super().__init__(config)

    def individual_process(self, df: pd.DataFrame) -> pd.DataFrame:
        return df


class ReceiveFormatter(CommonCSVFormatter):
    """
    受入一覧用フォーマッター

    - format() メソッドは親クラス（CommonCSVFormatter）で共通実装されています。
    - 受入一覧特有の加工（例: 日付整形）は individual_process(df) で記述してください。
    """

    def __init__(self, config: FormatterConfig):
        super().__init__(config)

    def individual_process(self, df: pd.DataFrame) -> pd.DataFrame:
        df = remove_weekday_parentheses(df, "伝票日付")
        df = combine_date_and_time(df, "伝票日付", "計量時間（総重量）")
        df = combine_date_and_time(df, "伝票日付", "計量時間（空車重量）")
        return df


class YardFormatter(CommonCSVFormatter):
    """
    ヤード一覧用フォーマッター

    - format() メソッドは親クラス（CommonCSVFormatter）で共通実装されています。
    - ヤード一覧特有の加工が必要な場合は individual_process(df) で記述してください。
    """

    def __init__(self, config: FormatterConfig):
        super().__init__(config)

    def individual_process(self, df: pd.DataFrame) -> pd.DataFrame:
        return df


class DefaultFormatter(CommonCSVFormatter):
    """
    デフォルトのフォーマッター（設定が無い場合など）

    - format() メソッドは親クラス（CommonCSVFormatter）で共通実装されています。
    - 個別の加工が不要な場合はこのクラスを利用してください。
    """

    def __init__(self):
        from backend_shared.src.csv_formatter.formatter_config import FormatterConfig

        empty_config = FormatterConfig(columns_def={}, unique_keys=[], agg_map={})
        super().__init__(empty_config)

    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        return df
