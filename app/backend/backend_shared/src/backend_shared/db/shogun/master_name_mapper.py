"""
将軍マスタ名前マッパー（後方互換性ラッパー）

⚠️ 非推奨: このクラスは後方互換性のために残されています。
新しいコードでは ShogunCsvConfigLoader を直接使用してください。

master.yaml（shogun_csv_masters.yaml）を読み込み、
DB英語名 ⇔ 日本語名の変換を提供します。
"""
import warnings
from functools import lru_cache

from backend_shared.config.config_loader import ShogunCsvConfigLoader
from backend_shared.config.paths import SHOGUNCSV_DEF_PATH


class ShogunMasterNameMapper:
    """
    将軍マスタ名前マッパー（後方互換性ラッパー）
    
    ⚠️ 非推奨: このクラスは ShogunCsvConfigLoader への単純なラッパーです。
    新規コードでは ShogunCsvConfigLoader を直接使用してください。
    
    master.yamlを使ってDB英語名⇔日本語名の変換を行います。
    
    機能:
    - データセット名の日本語表示（shogun_final_receive → "受入一覧"）
    - カラム名の英語→日本語変換（slip_date → "伝票日付"）
    - カラム名の日本語→英語変換（"伝票日付" → slip_date）
    
    使用例（非推奨）:
        mapper = ShogunMasterNameMapper()
        label = mapper.get_dataset_label("shogun_final_receive")
        
    推奨される新しい方法:
        loader = ShogunCsvConfigLoader()
        label = loader.get_dataset_label("shogun_final_receive")
    """
    
    def __init__(self, config_path: str = SHOGUNCSV_DEF_PATH):
        """
        コンストラクタ
        
        Args:
            config_path: master.yamlのパス（デフォルトは共有定義パス）
        """
        warnings.warn(
            "ShogunMasterNameMapper is deprecated. "
            "Use ShogunCsvConfigLoader directly instead.",
            DeprecationWarning,
            stacklevel=2
        )
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
        """データセットキーから日本語ラベルを取得（ShogunCsvConfigLoaderに委譲）"""
        return self._config_loader.get_dataset_label(dataset_key)
    
    def get_ja_column_name(self, master_key: str, en_name: str) -> str:
        """英語カラム名から日本語カラム名を取得（ShogunCsvConfigLoaderに委譲）"""
        return self._config_loader.get_ja_column_name(master_key, en_name)
    
    def get_en_column_name(self, master_key: str, ja_name: str) -> str:
        """日本語カラム名から英語カラム名を取得（ShogunCsvConfigLoaderに委譲）"""
        return self._config_loader.get_en_column_name(master_key, ja_name)
    
    def get_all_columns(self, master_key: str) -> dict:
        """全カラム定義を取得（ShogunCsvConfigLoaderに委譲）"""
        return self._config_loader.get_all_columns(master_key)
    
    def get_en_to_ja_map(self, master_key: str) -> dict:
        """英語名→日本語名のマッピング辞書を取得（ShogunCsvConfigLoaderに委譲）"""
        return self._config_loader.get_en_to_ja_map(master_key)
    
    def get_ja_to_en_map(self, master_key: str) -> dict:
        """日本語名→英語名のマッピング辞書を取得（ShogunCsvConfigLoaderに委譲）"""
        return self._config_loader.get_ja_to_en_map(master_key)
    
    def get_ja_to_en_map(self, master_key: str) -> dict:
        """日本語名→英語名のマッピング辞書を取得（ShogunCsvConfigLoaderに委譲）"""
        return self._config_loader.get_ja_to_en_map(master_key)
