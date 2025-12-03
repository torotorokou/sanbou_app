"""
External API Adapter - 外部API呼び出し用アダプタ

機能:
  - core_api が他のマイクロサービスを呼び出す際のアダプタ
  - RAG API: 質問応答システム
  - Ledger API: レポート生成、ブロック単価計算
  - Manual API: マニュアル参照
  - AI API: テキスト分類

設計方針:
  - Clean Architecture: Portの実装として機能する
  - 他サービスへの依存をこのアダプタに集約
  - 各サービス用のClientクラスを内部で使用
  - エラーハンドリングはUseCase側で実装

BFFパターン:
  - core_api はフロントエンド向けのBFF(Backend For Frontend)
  - 複数のマイクロサービスを統合して単一のAPIを提供
  - フロントエンドは core_api のみを呼び出す
"""
from typing import List, Dict

from backend_shared.application.logging import get_module_logger
from app.infra.clients.rag_client import RAGClient
from app.infra.clients.ledger_client import LedgerClient
from app.infra.clients.manual_client import ManualClient
from app.infra.clients.ai_client import AIClient

logger = get_module_logger(__name__)


class ExternalApiAdapter:
    """
    Adapter for external API calls.
    Implements the external API port interface.
    """
    
    def __init__(self):
        self.rag_client = RAGClient()
        self.ledger_client = LedgerClient()
        self.manual_client = ManualClient()
        self.ai_client = AIClient()
    
    async def ask_rag(self, query: str) -> dict:
        """Ask RAG API a question."""
        logger.info("Calling RAG service", extra={"query": query})
        return await self.rag_client.ask(query)
    
    async def list_manuals(self) -> List[Dict]:
        """List all manuals from Manual API."""
        logger.info("Calling Manual service for list")
        return await self.manual_client.list_manuals()
    
    async def get_manual(self, manual_id: str) -> dict:
        """Get specific manual by ID."""
        logger.info("Calling Manual service", extra={"manual_id": manual_id})
        return await self.manual_client.get_manual(manual_id)
    
    async def generate_report(self, report_type: str, params: dict) -> dict:
        """Request report generation from Ledger API."""
        logger.info("Calling Ledger service", extra={"report_type": report_type})
        return await self.ledger_client.generate_report(report_type, params)
    
    async def classify_text(self, text: str) -> dict:
        """Classify text using AI API."""
        logger.info("Calling AI service", extra={"text_length": len(text)})
        return await self.ai_client.classify(text)
