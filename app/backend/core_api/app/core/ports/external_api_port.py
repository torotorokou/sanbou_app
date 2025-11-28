"""
Port: External API Clients

外部マイクロサービス呼び出しの抽象インターフェース。
"""
from typing import Protocol, List, Dict, Any


class IRAGClient(Protocol):
    """RAG API クライアントのPort"""
    
    async def ask(self, query: str) -> dict:
        """RAGに質問を送信"""
        ...


class ILedgerClient(Protocol):
    """Ledger API クライアントのPort"""
    
    async def generate_report(self, report_type: str, params: dict) -> dict:
        """Ledgerレポート生成"""
        ...
    
    async def get_health(self) -> dict:
        """Ledgerヘルスチェック"""
        ...


class IManualClient(Protocol):
    """Manual API クライアントのPort"""
    
    async def list_manuals(self) -> List[Dict]:
        """マニュアル一覧を取得"""
        ...
    
    async def get_manual(self, manual_id: str) -> dict:
        """特定のマニュアルを取得"""
        ...


class IAIClient(Protocol):
    """AI API クライアントのPort"""
    
    async def classify(self, text: str) -> dict:
        """テキストを分類"""
        ...
    
    async def get_health(self) -> dict:
        """AIヘルスチェック"""
        ...
