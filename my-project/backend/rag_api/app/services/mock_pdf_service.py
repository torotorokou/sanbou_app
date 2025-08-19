"""
テスト用PDFサービス（モック実装）

単体テストやE2Eテスト時に、実際のPDF処理を行わずに
モックデータで処理を代用するためのサービス実装です。
"""

from typing import List
from .pdf_service_base import PDFServiceBase

class MockPDFService(PDFServiceBase):
    """
    テスト用のモックPDFサービス
    
    実際のPDFファイル処理を行わず、固定のダミーデータを返します。
    単体テストやCI/CD環境での利用を想定しています。
    """
    
    def save_pdf_pages_and_get_urls(
        self, 
        pdf_path: str, 
        query_name: str, 
        pages: List[int], 
        save_dir: str, 
        url_prefix: str
    ) -> List[str]:
        """
        モック実装: 固定のダミーURLリストを返す
        """
        return [f"{url_prefix}/mock_page_{p}.pdf" for p in pages]
    
    def merge_pdfs(self, pdf_file_paths: List[str], output_path: str) -> str:
        """
        モック実装: 実際のPDF結合は行わず、パスのみ返す
        """
        return output_path
