"""
将軍データセットキー定義

将軍システムの6種類のデータセットキーをEnum/Literalで定義し、
typoを防止します。
"""
from enum import Enum
from typing import Literal


class ShogunDatasetKey(str, Enum):
    """
    将軍データセットキー
    
    6種類のデータセット:
    - flash/final × receive/shipment/yard
    
    使用例:
        key = ShogunDatasetKey.SHOGUN_FINAL_RECEIVE
        key_str = "shogun_final_receive"  # 文字列としても扱える
    """
    
    # Final系（確定データ）
    SHOGUN_FINAL_RECEIVE = "shogun_final_receive"
    SHOGUN_FINAL_SHIPMENT = "shogun_final_shipment"
    SHOGUN_FINAL_YARD = "shogun_final_yard"
    
    # Flash系（速報データ）
    SHOGUN_FLASH_RECEIVE = "shogun_flash_receive"
    SHOGUN_FLASH_SHIPMENT = "shogun_flash_shipment"
    SHOGUN_FLASH_YARD = "shogun_flash_yard"
    
    @property
    def is_final(self) -> bool:
        """確定データ（final）かどうか"""
        return "final" in self.value
    
    @property
    def is_flash(self) -> bool:
        """速報データ（flash）かどうか"""
        return "flash" in self.value
    
    @property
    def data_type(self) -> Literal["receive", "shipment", "yard"]:
        """データ種別（receive/shipment/yard）"""
        if "receive" in self.value:
            return "receive"
        elif "shipment" in self.value:
            return "shipment"
        else:
            return "yard"
    
    def get_view_name(self) -> str:
        """
        対応するDB view名を取得
        
        Returns:
            str: DB view名（例: "v_active_shogun_final_receive"）
            
        Note:
            db/names.py で定義された定数を参照（Single Source of Truth）
        """
        from backend_shared.db.names import (
            V_ACTIVE_SHOGUN_FINAL_RECEIVE,
            V_ACTIVE_SHOGUN_FINAL_SHIPMENT,
            V_ACTIVE_SHOGUN_FINAL_YARD,
            V_ACTIVE_SHOGUN_FLASH_RECEIVE,
            V_ACTIVE_SHOGUN_FLASH_SHIPMENT,
            V_ACTIVE_SHOGUN_FLASH_YARD,
        )
        
        # Enumの各値に対応するview名を定数から取得
        view_map = {
            self.SHOGUN_FINAL_RECEIVE: V_ACTIVE_SHOGUN_FINAL_RECEIVE,
            self.SHOGUN_FINAL_SHIPMENT: V_ACTIVE_SHOGUN_FINAL_SHIPMENT,
            self.SHOGUN_FINAL_YARD: V_ACTIVE_SHOGUN_FINAL_YARD,
            self.SHOGUN_FLASH_RECEIVE: V_ACTIVE_SHOGUN_FLASH_RECEIVE,
            self.SHOGUN_FLASH_SHIPMENT: V_ACTIVE_SHOGUN_FLASH_SHIPMENT,
            self.SHOGUN_FLASH_YARD: V_ACTIVE_SHOGUN_FLASH_YARD,
        }
        return view_map[self]
    
    def get_master_key(self) -> str:
        """
        master.yaml のキーを取得
        
        Returns:
            str: master.yamlのキー（例: "receive", "shipment", "yard"）
        """
        return self.data_type


# Type alias for type hints
ShogunDatasetKeyType = Literal[
    "shogun_final_receive",
    "shogun_final_shipment",
    "shogun_final_yard",
    "shogun_flash_receive",
    "shogun_flash_shipment",
    "shogun_flash_yard",
]
