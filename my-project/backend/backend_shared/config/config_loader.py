import yaml
from app.local_config.paths import CSV_DEF_PATH


class SyogunCsvConfigLoader:
    """
    統合型CSV定義ファイル（YAML）を読み込むためのクラス。
    必須カラム・カラム定義（英語名や型）も取得できます。
    """

    def __init__(self, config_path: str = CSV_DEF_PATH):
        """
        コンストラクタ。設定ファイルのパスを受け取ります。
        :param config_path: 設定ファイル（YAML）のパス
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """
        YAML設定ファイルを読み込んで辞書として返す（内部利用）。
        """
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_expected_headers(self, sheet_type: str) -> list:
        """
        指定したCSV種別の必須カラムリストを取得します。
        :param sheet_type: 'shipment', 'receive' など
        :return: 必須カラム名リスト
        """
        return self.config.get(sheet_type, {}).get("expected_headers", [])

    def get_columns(self, sheet_type: str) -> dict:
        """
        指定したCSV種別のカラム定義（日本語名→英語名・型辞書）を取得します。
        :param sheet_type: 'shipment', 'receive' など
        :return: {日本語カラム名: {en_name: ..., type: ...}}
        """
        return self.config.get(sheet_type, {}).get("columns", {})

    def get_column_meta(self, sheet_type: str, jp_col: str) -> dict:
        """
        指定したCSV種別・日本語カラム名の詳細（英語名・型など）を取得します。
        :param sheet_type: 'shipment', 'receive' など
        :param jp_col: 伝票日付など
        :return: {en_name: ..., type: ...} 形式の辞書
        """
        return self.get_columns(sheet_type).get(jp_col, {})

    def get_en_name_map(self, sheet_type: str) -> dict:
        """
        指定帳票の「日本語名→英語名」マッピング辞書を取得します。
        :return: 例 {'伝票日付': 'slip_date', ...}
        """
        return {
            jp: meta["en_name"]
            for jp, meta in self.get_columns(sheet_type).items()
            if "en_name" in meta
        }

    def get_type_map(self, sheet_type: str) -> dict:
        """
        指定帳票の「日本語名→型」マッピング辞書を取得します。
        :return: 例 {'伝票日付': 'datetime', ...}
        """
        return {
            jp: meta["type"]
            for jp, meta in self.get_columns(sheet_type).items()
            if "type" in meta
        }

    def get_unique_keys(self, sheet_type: str) -> list[list[str]]:
        """
        指定帳票の一意キー候補リストを取得します。
        :param sheet_type: 'shipment', 'receive' など
        :return: 一意キー候補のリスト（例: [['伝票日付', '品名', ...], ...]）
        """
        return self.config.get(sheet_type, {}).get("unique_keys", [])

    def get_unique_en_keys(self, sheet_type: str) -> list[str]:
        """
        指定帳票の一意キー（日本語）を英語カラム名に変換して返す。
        :param sheet_type: 'shipment', 'receive' など
        :return: 英語カラム名のリスト（例: ['slip_date', 'vendor_cd', ...]）
        """
        unique_keys_jp = self.config.get(sheet_type, {}).get("unique_keys", [])
        en_map = self.get_en_name_map(sheet_type)

        return [en_map[jp] for jp in unique_keys_jp if jp in en_map]

    def get_agg_map(self, sheet_type: str) -> dict:
        """
        指定帳票の「日本語カラム名→集約関数名（agg）」マッピングを取得します。
        :param sheet_type: 'shipment', 'receive' など
        :return: 例 {'金額': 'sum', '数量': 'sum', ...}
        """
        return {
            jp: meta["agg"]
            for jp, meta in self.get_columns(sheet_type).items()
            if "agg" in meta
        }
