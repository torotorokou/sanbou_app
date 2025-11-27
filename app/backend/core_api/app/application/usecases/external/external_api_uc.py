"""
UseCase: External API呼び出し系

外部マイクロサービスとの連携を担当。

設計方針:
  - Port経由でクライアントにアクセス
  - 複数サービスの呼び出しをオーケストレーション
"""
from typing import List, Dict, Any

from app.domain.ports.external_api_port import (
    IRAGClient,
    ILedgerClient,
    IManualClient,
    IAIClient,
)


class AskRAGUseCase:
    """RAG API質問UseCase"""
    
    def __init__(self, rag_client: IRAGClient):
        self._rag_client = rag_client
    
    async def execute(self, query: str) -> dict:
        """
        RAGに質問を送信
        
        Args:
            query: ユーザーの質問
            
        Returns:
            dict: RAGからの回答
        """
        return await self._rag_client.ask(query)


class GenerateLedgerReportUseCase:
    """Ledgerレポート生成UseCase（旧名、互換性のため残す）"""
    
    def __init__(self, ledger_client: ILedgerClient):
        self._ledger_client = ledger_client
    
    async def execute(self, report_type: str, params: dict) -> dict:
        """
        Ledgerレポートを生成
        
        Args:
            report_type: レポートタイプ
            params: パラメータ
            
        Returns:
            dict: レポート
        """
        return await self._ledger_client.generate_report(report_type, params)


class ListManualsUseCase:
    """マニュアル一覧取得UseCase"""
    
    def __init__(self, manual_client: IManualClient):
        self._manual_client = manual_client
    
    async def execute(self) -> List[Dict]:
        """
        マニュアル一覧を取得
        
        Returns:
            List[Dict]: マニュアル一覧
        """
        return await self._manual_client.list_manuals()


class GetManualUseCase:
    """特定マニュアル取得UseCase"""
    
    def __init__(self, manual_client: IManualClient):
        self._manual_client = manual_client
    
    async def execute(self, manual_id: str) -> dict:
        """
        特定のマニュアルを取得
        
        Args:
            manual_id: マニュアルID
            
        Returns:
            dict: マニュアル情報
        """
        return await self._manual_client.get_manual(manual_id)


class GenerateReportUseCase:
    """Ledgerレポート生成UseCase"""
    
    def __init__(self, ledger_client: ILedgerClient):
        self._ledger_client = ledger_client
    
    async def execute(self, report_type: str, params: dict) -> dict:
        """
        Ledgerレポートを生成
        
        Args:
            report_type: レポートタイプ
            params: パラメータ
            
        Returns:
            dict: レポート
        """
        return await self._ledger_client.generate_report(report_type, params)


class ClassifyTextUseCase:
    """テキスト分類UseCase"""
    
    def __init__(self, ai_client: IAIClient):
        self._ai_client = ai_client
    
    async def execute(self, text: str) -> dict:
        """
        テキストを分類
        
        Args:
            text: 分類対象テキスト
            
        Returns:
            dict: 分類結果
        """
        return await self._ai_client.classify(text)
