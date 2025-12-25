"""
設定ファイルローダー

YAML形式の設定ファイルを読み込み、CSV処理や帳票生成に必要な
設定情報を提供するローダークラス群です。
"""

import yaml

from backend_shared.config.paths import MANAGER_CSV_DEF_PATH, SHOGUNCSV_DEF_PATH


class ShogunCsvConfigLoader:
    """
    将軍CSV定義ファイルローダー

    統合型CSV定義ファイル（YAML）を読み込み、CSV処理に必要な
    カラム定義、型情報、一意キーなどの設定情報を提供します。
    """

    def __init__(self, config_path: str = SHOGUNCSV_DEF_PATH):
        """
        コンストラクタ

        Args:
            config_path (str): 設定ファイル（YAML）のパス
        """
        self.config_path = config_path
        # 設定ファイルの読み込み
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """
        YAML設定ファイルを読み込んで辞書として返す（内部利用）

        Returns:
            dict: 設定情報の辞書
        """
        with open(self.config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_expected_headers(self, sheet_type: str) -> list:
        """
        指定したCSV種別の必須カラムリストを取得

        Args:
            sheet_type (str): CSV種別 ('shipment', 'receive' など)

        Returns:
            list: 必須カラム名リスト
        """
        return self.config.get(sheet_type, {}).get("expected_headers", [])

    def get_columns(self, sheet_type: str) -> dict:
        """
        指定したCSV種別のカラム定義（日本語名→英語名・型辞書）を取得

        Args:
            sheet_type (str): CSV種別 ('shipment', 'receive' など)

        Returns:
            dict: カラム定義辞書 {日本語カラム名: {en_name: ..., type: ...}}
        """
        return self.config.get(sheet_type, {}).get("columns", {})

    def get_column_meta(self, sheet_type: str, jp_col: str) -> dict:
        """
        指定したCSV種別・日本語カラム名の詳細（英語名・型など）を取得

        Args:
            sheet_type (str): CSV種別 ('shipment', 'receive' など)
            jp_col (str): 日本語カラム名（伝票日付など）

        Returns:
            dict: カラムメタデータ {en_name: ..., type: ...} 形式の辞書
        """
        return self.get_columns(sheet_type).get(jp_col, {})

    def get_en_name_map(self, sheet_type: str) -> dict:
        """
        指定帳票の「日本語名→英語名」マッピング辞書を取得

        Args:
            sheet_type (str): CSV種別

        Returns:
            dict: 日本語名→英語名のマッピング辞書（例: {'伝票日付': 'slip_date', ...}）
        """
        return {
            jp: meta["en_name"]
            for jp, meta in self.get_columns(sheet_type).items()
            if "en_name" in meta
        }

    def get_type_map(self, sheet_type: str) -> dict:
        """
        指定帳票の「日本語名→型」マッピング辞書を取得

        Args:
            sheet_type (str): CSV種別

        Returns:
            dict: 日本語名→型のマッピング辞書（例: {'伝票日付': 'datetime', ...}）
        """
        return {
            jp: meta["type"]
            for jp, meta in self.get_columns(sheet_type).items()
            if "type" in meta
        }

    def get_unique_keys(self, sheet_type: str) -> list[list[str]]:
        """
        指定帳票の一意キー候補リストを取得

        Args:
            sheet_type (str): CSV種別 ('shipment', 'receive' など)

        Returns:
            list[list[str]]: 一意キー候補のリスト（例: [['伝票日付', '品名', ...], ...]）
        """
        return self.config.get(sheet_type, {}).get("unique_keys", [])

    def get_unique_en_keys(self, sheet_type: str) -> list[str]:
        """
        指定帳票の一意キー（日本語）を英語カラム名に変換して返す

        Args:
            sheet_type (str): CSV種別 ('shipment', 'receive' など)

        Returns:
            list[str]: 英語カラム名のリスト（例: ['slip_date', 'vendor_cd', ...]）
        """
        # 日本語の一意キーを取得
        unique_keys_jp = self.config.get(sheet_type, {}).get("unique_keys", [])
        # 日本語→英語のマッピングを取得
        en_map = self.get_en_name_map(sheet_type)

        # 日本語キーを英語キーに変換
        return [en_map[jp] for jp in unique_keys_jp if jp in en_map]

    def get_agg_map(self, sheet_type: str) -> dict:
        """
        指定帳票の「日本語カラム名→集約関数名（agg）」マッピングを取得

        Args:
            sheet_type (str): CSV種別 ('shipment', 'receive' など)

        Returns:
            dict: 集約関数マッピング辞書（例: {'金額': 'sum', '数量': 'sum', ...}）
        """
        return {
            jp: meta["agg"]
            for jp, meta in self.get_columns(sheet_type).items()
            if "agg" in meta
        }


class ReportTemplateConfigLoader:
    """
    帳票テンプレート設定ローダー

    帳票生成に必要なテンプレート情報（必須ファイル、ラベル、
    テンプレートパスなど）を管理するクラスです。
    """

    def __init__(self, path=MANAGER_CSV_DEF_PATH):
        """
        コンストラクタ

        Args:
            path (str): 設定ファイルのパス
        """
        # 設定ファイルの読み込み
        with open(path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def get_required_files(self, report_key: str) -> list[str]:
        """
        帳票ごとの必須CSVファイルリストを取得

        Args:
            report_key (str): 帳票キー

        Returns:
            list[str]: 必須CSVファイル名のリスト

        Raises:
            KeyError: 指定された帳票キーが存在しない場合
        """
        if report_key not in self.config:
            raise KeyError(f"{report_key}はテンプレート定義に存在しません")
        return self.config[report_key].get("required_files", [])

    def get_optional_files(self, report_key: str) -> list[str]:
        """
        帳票ごとの任意CSVファイルリストを取得

        Args:
            report_key (str): 帳票キー

        Returns:
            list[str]: 任意CSVファイル名のリスト（存在しない場合は空リスト）
        """
        return self.config[report_key].get("optional_files", [])

    def get_label(self, report_key: str) -> str:
        """
        帳票の日本語ラベルを取得

        Args:
            report_key (str): 帳票キー

        Returns:
            str: 帳票の日本語ラベル
        """
        return self.config[report_key].get("label", "")

    def get_template_excel_path(self, report_key: str) -> str:
        """
        帳票のExcelテンプレートファイルパスを取得

        Args:
            report_key (str): 帳票キー

        Returns:
            str: Excelテンプレートファイルのパス
        """
        return self.config[report_key].get("template_excel_path", "")

    def get_all_config(self) -> dict:
        """
        全ての帳票設定を取得

        Returns:
            dict: 全ての帳票設定の辞書
        """
        return self.config

    def get_report_config(self, report_key: str) -> dict:
        """
        特定の帳票設定を取得

        Args:
            report_key (str): 帳票キー

        Returns:
            dict: 指定された帳票の設定辞書

        Raises:
            KeyError: 指定された帳票キーが存在しない場合
        """
        if report_key not in self.config:
            raise KeyError(f"{report_key}はテンプレート定義に存在しません")
        return self.config[report_key]
