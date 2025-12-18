"""
将軍マスタ名前マッパー

master.yaml（shogun_csv_masters.yaml）を読み込み、
DB英語名 ⇔ 日本語名の変換を提供します。
"""
from functools import lru_cache
from typing import Optional

from backend_shared.config.config_loader import ShogunCsvConfigLoader
from backend_shared.config.paths import SHOGUNCSV_DEF_PATH


class ShogunMasterNameMapper:
    """
    将軍マスタ名前マッパー
    
    master.yamlを使ってDB英語名⇔日本語名の変換を行います。
    
    機能:
    - データセット名の日本語表示（shogun_final_receive → "受入一覧"）
    - カラム名の英語→日本語変換（slip_date → "伝票日付"）
    - カラム名の日本語→英語変換（"伝票日付" → slip_date）
    
    使用例:
        mapper = ShogunMasterNameMapper()
        
        # データセット名の取得
        label = mapper.get_dataset_label("shogun_final_receive")
        # => "受入一覧"
        
        # カラム名変換（英→日）
        ja_name = mapper.get_ja_column_name("receive", "slip_date")
        # => "伝票日付"
        
        # カラム名変換（日→英）
        en_name = mapper.get_en_column_name("receive", "伝票日付")
        # => "slip_date"
    """
    
    def __init__(self, config_path: str = SHOGUNCSV_DEF_PATH):
        """
        コンストラクタ
        
        Args:
            config_path: master.yamlのパス（デフォルトは共有定義パス）
        """
        self.config_path = config_path
        self._config_loader = self._get_config_loader()
    
    @lru_cache(maxsize=1)
    def _get_config_loader(self) -> ShogunCsvConfigLoader:
        """
        ConfigLoaderをキャッシュして取得（1プロセス1回のみ読み込み）
        
        Returns:
            ShogunCsvConfigLoader: 設定ローダーインスタンス
        """
        return ShogunCsvConfigLoader(self.config_path)
    
    def get_dataset_label(self, dataset_key: str) -> str:
        """
        データセットキーから日本語ラベルを取得
        
        Args:
            dataset_key: データセットキー（例: "shogun_final_receive"）
        
        Returns:
            str: 日本語ラベル（例: "受入一覧"）
                 master.yamlに定義がない場合はdataset_keyをそのまま返す
        
        例:
            get_dataset_label("shogun_final_receive") => "受入一覧"
            get_dataset_label("shogun_flash_shipment") => "出荷一覧"
        """
        # dataset_key から master.yaml のキーを抽出
        # shogun_final_receive -> receive
        # shogun_flash_shipment -> shipment
        master_key = self._extract_master_key(dataset_key)
        
        if not master_key:
            return dataset_key
        
        try:
            config = self._config_loader.config.get(master_key, {})
            label = config.get("label", dataset_key)
            return label
        except Exception:
            # 読み込みエラー時はフォールバック
            return dataset_key
    
    def get_ja_column_name(self, master_key: str, en_name: str) -> str:
        """
        英語カラム名から日本語カラム名を取得
        
        Args:
            master_key: master.yamlのキー（例: "receive", "shipment", "yard"）
            en_name: 英語カラム名（例: "slip_date"）
        
        Returns:
            str: 日本語カラム名（例: "伝票日付"）
                 master.yamlに定義がない場合は en_name をそのまま返す
        
        例:
            get_ja_column_name("receive", "slip_date") => "伝票日付"
            get_ja_column_name("shipment", "vendor_name") => "業者名"
        """
        try:
            columns = self._config_loader.get_columns(master_key)
            # columns: {日本語名: {en_name: ..., type: ...}, ...}
            # 逆引き: en_name から日本語名を探す
            for ja_name, meta in columns.items():
                if meta.get("en_name") == en_name:
                    return ja_name
            # 見つからない場合はフォールバック
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
                 master.yamlに定義がない場合は ja_name をそのまま返す
        
        例:
            get_en_column_name("receive", "伝票日付") => "slip_date"
            get_en_column_name("shipment", "業者名") => "vendor_name"
        """
        try:
            meta = self._config_loader.get_column_meta(master_key, ja_name)
            en_name = meta.get("en_name", ja_name)
            return en_name
        except Exception:
            return ja_name
    
    def get_all_columns(self, master_key: str) -> dict[str, dict]:
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
            return self._config_loader.get_columns(master_key)
        except Exception:
            return {}
    
    def get_en_to_ja_map(self, master_key: str) -> dict[str, str]:
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
            columns = self._config_loader.get_columns(master_key)
            return {
                meta["en_name"]: ja_name
                for ja_name, meta in columns.items()
                if "en_name" in meta
            }
        except Exception:
            return {}
    
    def get_ja_to_en_map(self, master_key: str) -> dict[str, str]:
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
            columns = self._config_loader.get_columns(master_key)
            return {
                ja_name: meta["en_name"]
                for ja_name, meta in columns.items()
                if "en_name" in meta
            }
        except Exception:
            return {}
    
    @staticmethod
    def _extract_master_key(dataset_key: str) -> Optional[str]:
        """
        データセットキーから master.yaml のキーを抽出
        
        Args:
            dataset_key: データセットキー（例: "shogun_final_receive"）
        
        Returns:
            Optional[str]: master.yamlのキー（例: "receive"）
                          抽出できない場合はNone
        
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
        return None
