"""
Port: IShogunCsvWriter

UseCase が利用する CSV 保存の抽象インターフェース。
Adapter (Repository) はこのインターフェースを実装します。

設計方針:
  - UseCase は具体的な Repository に依存せず、Port に依存
  - テストでは Mock 実装を差し替え可能
"""
from abc import ABC, abstractmethod
from typing import Protocol
import pandas as pd


class IShogunCsvWriter(Protocol):
    """将軍CSV保存のPort（抽象インターフェース）"""
    
    def save_csv_by_type(self, csv_type: str, df: pd.DataFrame) -> int:
        """
        CSV種別に応じて適切なテーブルに保存
        
        Args:
            csv_type: CSV種別 ('receive', 'yard', 'shipment')
            df: 保存するDataFrame（英語カラム名）
            
        Returns:
            int: 保存した行数
        """
        ...
