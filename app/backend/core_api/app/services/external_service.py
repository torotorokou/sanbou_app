"""
External service: orchestrates calls to internal microservices (RAG, Ledger, Manual, AI).
"""
from typing import List, Dict
import logging

from app.infra.clients.rag_client import RAGClient
from app.infra.clients.ledger_client import LedgerClient
from app.infra.clients.manual_client import ManualClient
from app.infra.clients.ai_client import AIClient

logger = logging.getLogger(__name__)


class ExternalService:
    """Service for calling external internal APIs."""

    def __init__(self):
        self.rag_client = RAGClient()
        self.ledger_client = LedgerClient()
        self.manual_client = ManualClient()
        self.ai_client = AIClient()

    async def ask_rag(self, query: str) -> dict:
        """
        Ask RAG API a question.
        
        Args:
            query: User query
            
        Returns:
            dict with 'answer' and 'sources'
        """
        logger.info("Calling RAG service", extra={"query": query})
        return await self.rag_client.ask(query)

    async def list_manuals(self) -> List[Dict]:
        """
        List all manuals from Manual API.
        
        Returns:
            List of manual metadata
        """
        logger.info("Calling Manual service for list")
        return await self.manual_client.list_manuals()

    async def get_manual(self, manual_id: str) -> dict:
        """Get specific manual by ID."""
        logger.info("Calling Manual service", extra={"manual_id": manual_id})
        return await self.manual_client.get_manual(manual_id)

    async def generate_report(self, report_type: str, params: dict) -> dict:
        """
        Request report generation from Ledger API.
        TODO: For heavy reports, queue as a job instead of sync call.
        
        Args:
            report_type: Type of report
            params: Report parameters
            
        Returns:
            Report metadata or job ID
        """
        logger.info("Calling Ledger service", extra={"report_type": report_type})
        return await self.ledger_client.generate_report(report_type, params)

    async def classify_text(self, text: str) -> dict:
        """
        Classify text using AI API.
        
        Args:
            text: Input text
            
        Returns:
            Classification result
        """
        logger.info("Calling AI service", extra={"text_length": len(text)})
        return await self.ai_client.classify(text)
