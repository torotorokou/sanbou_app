"""
Dashboard UseCase DTO definitions

Input/Output DTOを明確に定義し、UseCase層とPresentation層の境界を明確にする
"""
from dataclasses import dataclass
from datetime import date as date_type
from typing import Optional, Dict, Any, Literal


# ========================================================================
# Type Aliases
# ========================================================================

Mode = Literal["daily", "monthly"]


# ========================================================================
# Input DTOs
# ========================================================================

@dataclass(frozen=True)
class BuildTargetCardInput:
    """
    ターゲットカードデータ取得UseCase - Input DTO
    
    Attributes:
        requested_date: 対象日付（月次表示の場合は月初日を推奨）
        mode: 表示モード（"daily": 特定日、"monthly": 月次ビュー）
    """
    requested_date: date_type
    mode: Mode = "daily"
    
    def validate(self) -> None:
        """
        入力値のバリデーション
        
        Raises:
            ValueError: バリデーションエラー
        """
        # Domain Serviceで詳細なバリデーションを実施するため、ここでは基本チェックのみ
        if not isinstance(self.requested_date, date_type):
            raise ValueError("requested_date must be a date object")
        
        if self.mode not in ("daily", "monthly"):
            raise ValueError(f"mode must be 'daily' or 'monthly', got: {self.mode}")


# ========================================================================
# Output DTOs
# ========================================================================

@dataclass(frozen=True)
class BuildTargetCardOutput:
    """
    ターゲットカードデータ取得UseCase - Output DTO
    
    Attributes:
        data: ターゲット/実績データ（達成率、差異等を含む）
        found: データが見つかったかどうか
    """
    data: Optional[Dict[str, Any]]
    found: bool
    
    @classmethod
    def from_domain(
        cls,
        data: Optional[Dict[str, Any]]
    ) -> "BuildTargetCardOutput":
        """
        ドメインモデルからOutput DTOを生成
        
        Args:
            data: ターゲット/実績データ（Noneの場合は見つからなかった）
            
        Returns:
            BuildTargetCardOutput
        """
        return cls(
            data=data,
            found=data is not None,
        )
