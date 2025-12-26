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

    機能:
    - データセット名の日本語表示（shogun_final_receive → "受入一覧"）
    - カラム名の英語→日本語変換（slip_date → "伝票日付"）
    - カラム名の日本語→英語変換（"伝票日付" → slip_date）
    - 型情報、一意キー、集約関数などの設定取得
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
            jp: meta["type"] for jp, meta in self.get_columns(sheet_type).items() if "type" in meta
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
            jp: meta["agg"] for jp, meta in self.get_columns(sheet_type).items() if "agg" in meta
        }

    def get_dataset_label(self, dataset_key: str) -> str:
        """
        データセットキーから日本語ラベルを取得

        Args:
            dataset_key: データセットキー（例: "shogun_final_receive"）

        Returns:
            str: 日本語ラベル（例: "受入一覧"）
                 定義がない場合はdataset_keyをそのまま返す

        例:
            get_dataset_label("shogun_final_receive") => "受入一覧"
            get_dataset_label("shogun_flash_shipment") => "出荷一覧"
        """
        # dataset_key から master_key を抽出
        master_key = self._extract_master_key(dataset_key)

        if not master_key:
            return dataset_key

        try:
            config = self.config.get(master_key, {})
            label = config.get("label", dataset_key)
            return label
        except Exception:
            return dataset_key

    def get_ja_column_name(self, master_key: str, en_name: str) -> str:
        """
        英語カラム名から日本語カラム名を取得

        Args:
            master_key: master.yamlのキー（例: "receive", "shipment", "yard"）
            en_name: 英語カラム名（例: "slip_date"）

        Returns:
            str: 日本語カラム名（例: "伝票日付"）
                 定義がない場合は en_name をそのまま返す

        例:
            get_ja_column_name("receive", "slip_date") => "伝票日付"
            get_ja_column_name("shipment", "vendor_name") => "業者名"
        """
        try:
            columns = self.get_columns(master_key)
            # columns: {日本語名: {en_name: ..., type: ...}, ...}
            # 逆引き: en_name から日本語名を探す
            for ja_name, meta in columns.items():
                if meta.get("en_name") == en_name:
                    return ja_name
            return en_name
        except Exception:
            return en_name

    def get_en_column_name(self, master_key: str, ja_name: str) -> str:
        """
        日本語カラム名から英語カラム名を取得

        Args:
            master_key: master.yamlのキー（例: "receive", "shipment", "yard"）
            ja_name: 日本語カラム名（例: "伝票日付"）

        Returns:
            str: 英語カラム名（例: "slip_date"）
                 定義がない場合は ja_name をそのまま返す

        例:
            get_en_column_name("receive", "伝票日付") => "slip_date"
            get_en_column_name("shipment", "業者名") => "vendor_name"
        """
        try:
            meta = self.get_column_meta(master_key, ja_name)
            en_name = meta.get("en_name", ja_name)
            return en_name
        except Exception:
            return ja_name

    def get_all_columns(self, master_key: str) -> dict:
        """
        指定したmaster_keyの全カラム定義を取得

        Args:
            master_key: master.yamlのキー（例: "receive", "shipment", "yard"）

        Returns:
            dict: カラム定義辞書 {日本語名: {en_name: ..., type: ...}, ...}

        例:
            get_all_columns("receive")
            => {
                "伝票日付": {"en_name": "slip_date", "type": "datetime", "agg": "first"},
                "業者CD": {"en_name": "vendor_cd", "type": "Int64", "agg": "first"},
                ...
            }
        """
        try:
            return self.get_columns(master_key)
        except Exception:
            return {}

    def get_en_to_ja_map(self, master_key: str) -> dict:
        """
        英語名→日本語名のマッピング辞書を取得

        Args:
            master_key: master.yamlのキー（例: "receive", "shipment", "yard"）

        Returns:
            dict: {英語名: 日本語名} の辞書

        例:
            get_en_to_ja_map("receive")
            => {
                "slip_date": "伝票日付",
                "vendor_cd": "業者CD",
                ...
            }
        """
        try:
            columns = self.get_columns(master_key)
            return {
                meta["en_name"]: ja_name for ja_name, meta in columns.items() if "en_name" in meta
            }
        except Exception:
            return {}

    def get_ja_to_en_map(self, master_key: str) -> dict:
        """
        日本語名→英語名のマッピング辞書を取得

        Args:
            master_key: master.yamlのキー（例: "receive", "shipment", "yard"）

        Returns:
            dict: {日本語名: 英語名} の辞書

        例:
            get_ja_to_en_map("receive")
            => {
                "伝票日付": "slip_date",
                "業者CD": "vendor_cd",
                ...
            }
        """
        try:
            columns = self.get_columns(master_key)
            return {
                ja_name: meta["en_name"] for ja_name, meta in columns.items() if "en_name" in meta
            }
        except Exception:
            return {}

    @staticmethod
    def _extract_master_key(dataset_key: str) -> str:
        """
        データセットキーから master_key を抽出

        Args:
            dataset_key: データセットキー（例: "shogun_final_receive"）

        Returns:
            str: master_keyまたは空文字列（抽出できない場合）

        内部ロジック:
            shogun_final_receive -> receive
            shogun_flash_shipment -> shipment
            shogun_final_yard -> yard
        """
        if "receive" in dataset_key:
            return "receive"
        elif "shipment" in dataset_key:
            return "shipment"
        elif "yard" in dataset_key:
            return "yard"
        return ""


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
