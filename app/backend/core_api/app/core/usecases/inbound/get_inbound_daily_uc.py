"""
UseCase: Get Inbound Daily Data

日次搬入量データ取得UseCase

設計方針（Clean Architecture準拠）:
  1. Input/Output DTOを明確に定義
  2. execute(input) -> output の標準形式を採用
  3. バリデーションはInput DTOで実施
  4. Portを通じてInfra層に依存（依存性逆転）
  5. ビジネスロジックはDomain層に委譲
"""
import logging

from backend_shared.application.logging import get_module_logger
from app.core.usecases.inbound.dto import (
    GetInboundDailyInput,
    GetInboundDailyOutput,
)
from app.core.ports.inbound_repository_port import InboundRepository

logger = get_module_logger(__name__)


class GetInboundDailyUseCase:
    """
    日次搬入量データ取得UseCase
    
    責務:
      - Input DTOのバリデーション
      - Repository（Port）を通じたデータ取得
      - Output DTOへの変換
    
    依存:
      - InboundRepository（Port）: データ取得の抽象インターフェース
    """
    
    def __init__(self, query: InboundRepository):
        """
        Args:
            query: InboundRepository実装（DI経由で注入）
        """
        self._query = query
    
    def execute(self, input_dto: GetInboundDailyInput) -> GetInboundDailyOutput:
        """
        日次搬入量データを取得
        
        処理フロー:
          1. Input DTOのバリデーション
          2. Repository経由でデータ取得
          3. Output DTOに変換して返却
        
        Args:
            input_dto: GetInboundDailyInput
            
        Returns:
            GetInboundDailyOutput（日次搬入量データ + メタ情報）
            
        Raises:
            ValueError: Input DTOのバリデーションエラー
            InfrastructureError: DB接続エラー等（Repository層から伝播）
        """
        # 開始ログ
        logger.info(
            "Inbound daily data query started",
            extra={
                "operation": "get_inbound_daily",
                "start": input_dto.start,
                "end": input_dto.end,
                "segment": input_dto.segment,
                "cum_scope": input_dto.cum_scope,
            }
        )
        
        # 1. バリデーション
        input_dto.validate()
        
        # 2. Repository経由でデータ取得
        data = self._query.fetch_daily(
            start=input_dto.start,
            end=input_dto.end,
            segment=input_dto.segment,
            cum_scope=input_dto.cum_scope,
        )
        
        # 完了ログ
        logger.info(
            "Inbound daily data query completed",
            extra={
                "operation": "get_inbound_daily",
                "start": input_dto.start,
                "end": input_dto.end,
                "segment": input_dto.segment,
                "cum_scope": input_dto.cum_scope,
                "row_count": len(data),
            }
        )
        
        # 3. Output DTOに変換
        return GetInboundDailyOutput.from_domain(
            data=data,
            start=input_dto.start,
            end=input_dto.end,
        )
