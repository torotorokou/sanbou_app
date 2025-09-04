from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend_shared.config.config_loader import SyogunCsvConfigLoader


@dataclass
class FormatterConfig:
    """
    フォーマッタの設定情報を保持するデータクラス。
    columns_def: 各カラムの定義情報（型や必須など）
    unique_keys: ユニーク制約となるカラム名のリスト（複数可）
    agg_map: 集計時のカラムごとの集計方法（sum, max など）
    extra_settings: 任意の追加設定（dict形式で格納）
    """

    columns_def: Dict[str, Any]  # カラム定義情報
    unique_keys: List[List[str]]  # ユニークキーの組み合わせ
    agg_map: Dict[str, str]  # 集計方法マッピング
    extra_settings: Optional[Dict[str, Any]] = None  # 任意の追加設定

    def __init__(self, columns_def, unique_keys, agg_map, **extra_settings):
        self.columns_def = columns_def
        self.unique_keys = unique_keys
        self.agg_map = agg_map
        self.extra_settings = extra_settings if extra_settings else {}


def build_formatter_config(
    loader: SyogunCsvConfigLoader, sheet_type: str, **extra_settings
) -> FormatterConfig:
    """
    指定されたシートタイプに応じてFormatterConfigを生成する。
    loader: 設定ローダー（SyogunCsvConfigLoader）
    sheet_type: シート種別（例: 'ukeire', 'syukka' など）
    extra_settings: 必要に応じて追加設定をキーワード引数で渡す
    戻り値: FormatterConfig インスタンス
    """
    return FormatterConfig(
        columns_def=loader.get_columns(sheet_type),  # カラム定義を取得
        unique_keys=loader.get_unique_keys(sheet_type),  # ユニークキー情報を取得
        agg_map=loader.get_agg_map(sheet_type),  # 集計方法マッピングを取得
        **extra_settings,
    )
