"""
Inbound domain package.
日次搬入量データのドメインモデル
"""
from app.core.domain.inbound.entities import InboundDailyRow, CumScope

__all__ = ["InboundDailyRow", "CumScope"]
