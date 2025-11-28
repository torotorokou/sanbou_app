"""
Configuration Loader Port

設定ファイル読み込みの抽象インターフェース。
"""

from typing import Protocol, Any


class ConfigLoaderPort(Protocol):
    """設定ファイルローダーの抽象インターフェース"""
    
    def load_config(self, config_name: str) -> dict[str, Any]:
        """
        設定ファイルを読み込む
        
        Args:
            config_name: 設定ファイル名
            
        Returns:
            設定内容の辞書
        """
        ...
    
    def get_columns_definition(self, csv_type: str) -> dict[str, dict]:
        """
        CSV タイプに対応するカラム定義を取得
        
        Args:
            csv_type: CSV タイプ（例: "shipment", "receive"）
            
        Returns:
            カラム定義の辞書
        """
        ...
