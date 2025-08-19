"""
AI回答生成サービス

generate-answerエンドポイント用のAI回答生成を担当するサービスです。

【フロントエンド開発者向け説明】
このサービスは以下の処理を行います：
1. ユーザーの質問をAIに送信して回答を生成
2. 回答に関連するPDFページを抽出・結合
3. 個別PDFはデバッグ用ディレクトリに保存（開発者用）
4. ユーザー向けには結合されたPDF URLのみを返却

レスポンス形式：
{
  "status": "success",
  "code": "S200", 
  "detail": "AI回答生成成功",
  "result": {
    "answer": "AIが生成した回答テキスト",
    "sources": [["参照PDF名", ページ番号], ...],
    "pdf_url": "https://example.com/static/pdfs/merged_response_20250819_114538.pdf"
  }
}

注意：pdf_urlは常に結合されたPDFを指し、個別ページは含まれません。
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Any
from app.infrastructure.llm import ai_loader
from app.utils.file_utils import PDF_PATH
from app.paths import get_pdf_url_prefix
from .pdf_service_base import PDFServiceBase


class AIResponseService:
    """
    AI回答生成サービス
    
    AIによる回答生成とPDF処理を組み合わせたレスポンス作成を担当します。
    """
    
    def __init__(self, pdf_service: PDFServiceBase):
        self.pdf_service = pdf_service
    
    def generate_ai_response(self, query: str, category: str, tags: List[str]) -> Dict[str, Any]:
        """
        AI回答とPDFを生成
        
        Args:
            query: ユーザーのクエリ
            category: カテゴリ
            tags: タグリスト
            
        Returns:
            AIレスポンスデータ（answer, sources, pdf_url）
        """
        # AI回答生成
        result = ai_loader.get_answer(query, category, tags)
        answer = result["answer"]
        sources = result["sources"]
        pages = result["pages"]
        
        # PDF保存先ディレクトリ
        static_dir = os.environ.get("PDFS_DIR") or "/backend/static/pdfs"
        debug_dir = os.path.join(static_dir, "debug")
        os.makedirs(static_dir, exist_ok=True)
        os.makedirs(debug_dir, exist_ok=True)
        pdf_path = str(PDF_PATH)
        
        # ページリスト正規化
        page_list = self._normalize_pages(pages)
        
        # 個別PDF生成（デバッグ用ディレクトリに保存）
        pdf_urls = self.pdf_service.save_pdf_pages_and_get_urls(
            pdf_path=pdf_path,
            query_name=query,
            pages=page_list,
            save_dir=debug_dir,  # デバッグディレクトリに保存
            url_prefix=f"{get_pdf_url_prefix()}/debug",  # デバッグ用URL
        )
        
        # PDF結合（ユーザー向けは本体ディレクトリに保存）
        jst = ZoneInfo('Asia/Tokyo')
        timestamp = datetime.now(jst).strftime("%Y%m%d_%H%M%S")
        merged_pdf_name = f"merged_response_{timestamp}.pdf"
        merged_pdf_path = os.path.join(static_dir, merged_pdf_name)
        pdf_file_paths = [os.path.join(debug_dir, url.split("/")[-1]) for url in pdf_urls]
        self.pdf_service.merge_pdfs(pdf_file_paths, merged_pdf_path)
        
        pdf_url = f"{get_pdf_url_prefix()}/{merged_pdf_name}"
        
        return {
            "answer": answer,
            "sources": sources,
            "pdf_url": pdf_url,
        }
    
    def _normalize_pages(self, pages) -> List[int]:
        """ページリストを正規化"""
        page_list = []
        if pages:
            if isinstance(pages, str):
                if "-" in pages:
                    start, end = pages.split("-")
                    try:
                        start = int(start)
                        end = int(end)
                        page_list = list(range(start, end + 1))
                    except Exception:
                        page_list = [pages]
                else:
                    page_list = [pages]
            elif isinstance(pages, list):
                for p in pages:
                    if isinstance(p, str) and "-" in p:
                        try:
                            start, end = p.split("-")
                            start = int(start)
                            end = int(end)
                            page_list.extend(range(start, end + 1))
                        except Exception:
                            page_list.append(p)
                    else:
                        page_list.append(p)
        return page_list
