"""
CsvKind Enum

将軍CSVの種別を表すEnum。
命名規則: {system}_{version}_{direction}
  - system: shogun
  - version: flash (速報版) / final (確定版)
  - direction: receive (受入) / shipment (出荷) / yard (ヤード)

この論理名は以下の全レイヤーで統一されます:
  - log.upload_file.csv_type カラム
  - stg.{csv_kind} テーブル名
  - API の csvKind フィールド
  - フロントエンドの CsvKind 型
"""
from enum import Enum


class CsvKind(str, Enum):
    """将軍CSV種別"""
    
    # 速報版（flash）
    SHOGUN_FLASH_RECEIVE = "shogun_flash_receive"
    SHOGUN_FLASH_SHIPMENT = "shogun_flash_shipment"
    SHOGUN_FLASH_YARD = "shogun_flash_yard"
    
    # 確定版（final）
    SHOGUN_FINAL_RECEIVE = "shogun_final_receive"
    SHOGUN_FINAL_SHIPMENT = "shogun_final_shipment"
    SHOGUN_FINAL_YARD = "shogun_final_yard"
    
    @property
    def system(self) -> str:
        """システム名を取得 (例: 'shogun')"""
        return self.value.split('_')[0]
    
    @property
    def version(self) -> str:
        """バージョンを取得 (例: 'flash', 'final')"""
        return self.value.split('_')[1]
    
    @property
    def direction(self) -> str:
        """方向を取得 (例: 'receive', 'shipment', 'yard')"""
        return self.value.split('_')[2]
    
    @property
    def is_flash(self) -> bool:
        """速報版かどうか"""
        return self.version == 'flash'
    
    @property
    def is_final(self) -> bool:
        """確定版かどうか"""
        return self.version == 'final'
    
    @property
    def table_name(self) -> str:
        """対応するstgテーブル名を取得 (例: 'stg.shogun_flash_receive')"""
        return f"stg.{self.value}"
