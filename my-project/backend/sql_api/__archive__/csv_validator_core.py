"""
API用の汎用的なCSVバリデーション機能を提供するクラス。
"""

# --- backend_shared/csv_validator/csv_validator_core.py ---
import pandas as pd
from typing import Optional

from backend_shared.utils.dataframe_validator import (
    DataFrameValidator,
    check_missing_file,
    check_required_columns,
    check_denpyou_date_exists,
    check_denpyou_date_consistency,
)


class CSVValidatorCore:
    """
    CSVファイルの検証を行うコアクラス。
    必須カラムのチェックや日付カラムの整合性チェックなど、
    複数の検証機能を提供します。
    初心者の方でも使いやすいように設計されています。

    リファクタリング後：汎用関数を呼び出すシンプルな構造になりました。
    """

    def __init__(self, required_columns: dict):
        """
        コンストラクタ。必須カラム定義を受け取り、バリデータを初期化します。
        :param required_columns: 各CSVタイプごとの必須カラム定義
        """
        self.validator = DataFrameValidator(required_columns)

    def check_missing_file(
        self, file_inputs: dict[str, Optional[object]]
    ) -> Optional[str]:
        """
        ファイル入力のうち、未入力のものがあればそのキー（CSV種別名）を返す。
        汎用関数への委譲メソッド。

        :param file_inputs: {csv_type: file_object or None}
        :return: 未入力のcsv_type名、またはNone
        """
        return check_missing_file(file_inputs)

    def check_required_columns(
        self, dfs: dict[str, pd.DataFrame]
    ) -> tuple[bool, str, list]:
        """
        各DataFrameに必須カラムが存在するかをチェック。
        汎用関数への委譲メソッド。

        :param dfs: {csv_type: DataFrame}
        :return: (全てOKならTrue, 問題のcsv_type, 不足カラムリスト)
        """
        return check_required_columns(dfs, self.validator)

    def check_denpyou_date_exists(self, dfs: dict[str, pd.DataFrame]) -> Optional[str]:
        """
        各DataFrameに「伝票日付」カラムが存在するかをチェック。
        汎用関数への委譲メソッド。

        :param dfs: {csv_type: DataFrame}
        :return: 「伝票日付」カラムがないcsv_type名、またはNone
        """
        return check_denpyou_date_exists(dfs)

    def check_denpyou_date_consistency(
        self, dfs: dict[str, pd.DataFrame]
    ) -> tuple[bool, dict]:
        """
        各DataFrameの「伝票日付」カラムの値の整合性をチェック。
        汎用関数への委譲メソッド。

        :param dfs: {csv_type: DataFrame}
        :return: (整合性OKならTrue, 詳細情報dict)
        """
        return check_denpyou_date_consistency(dfs, self.validator)
