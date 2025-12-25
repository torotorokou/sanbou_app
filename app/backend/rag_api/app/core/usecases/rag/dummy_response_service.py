"""
ダミーレスポンス生成サービス

test-answerエンドポイント用のダミーデータ生成を担当するサービスです。

【フロントエンド開発者向け説明】
このサービスは開発・テスト用のダミーAPIです：
1. 実際のAI処理は行わず、固定のダミー回答を返却
2. 既存PDFファイルから最大5つを選択して結合
3. 個別PDFはデバッグディレクトリにコピー保存（開発者用）
4. ユーザー向けには結合されたPDF URLのみを返却

レスポンス形式：
{
  "status": "success",
  "code": "S200",
  "detail": "ダミーAI回答生成成功",
  "result": {
    "answer": "ダミー回答: {ユーザーの質問}（カテゴリ: {カテゴリ}）",
    "sources": [["dummy1.pdf", 3], ["dummy2.pdf", 4], ...],
    "pdf_url": "https://example.com/static/pdfs/merged_response_20250819_114538.pdf"
  }
}

使用場面：
- フロントエンド開発時のモックデータとして
- AI APIの応答待ちなしでUI動作テストが可能
- 本番API切り替え前の統合テスト用
"""

import os
from typing import Any, Dict

from app.config.paths import get_pdf_url_prefix
from app.core.ports.rag.pdf_service_port import PDFServiceBase
from backend_shared.utils.datetime_utils import now_in_app_timezone


class DummyResponseService:
    """
    ダミーレスポンス生成サービス

    test-answerエンドポイント用のダミーデータを生成します。
    PDFファイルの結合やダミー回答の作成を担当します。
    """

    def __init__(self, pdf_service: PDFServiceBase):
        self.pdf_service = pdf_service

    def generate_dummy_response(self, query: str, category: str) -> Dict[str, Any]:
        """
        ダミーレスポンスを生成

        Args:
            query: ユーザーのクエリ
            category: カテゴリ

        Returns:
            ダミーレスポンスデータ（answer, sources, pdf_url）
        """
        # PDF保存先ディレクトリ
        pdfs_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../static/pdfs")
        )
        debug_dir = os.path.join(pdfs_dir, "debug")
        os.makedirs(pdfs_dir, exist_ok=True)
        os.makedirs(debug_dir, exist_ok=True)

        # PDFファイル一覧取得（先頭5つ）
        pdf_files = [f for f in os.listdir(pdfs_dir) if f.lower().endswith(".pdf")]
        pdf_files.sort()
        selected_files = pdf_files[:5]

        # 固定ページ番号
        pages = list(range(3, 8))[: len(selected_files)]
        sources = [
            [selected_files[i] if i < len(selected_files) else "dummy.pdf", pages[i]]
            for i in range(len(pages))
        ]

        # デバッグ用：選択されたPDFをデバッグディレクトリにコピー（参考用）
        debug_file_paths = []
        for fname in selected_files:
            src_path = os.path.join(pdfs_dir, fname)
            debug_path = os.path.join(debug_dir, f"debug_{fname}")
            # ファイルが存在し、デバッグファイルがまだなければコピー
            if os.path.exists(src_path) and not os.path.exists(debug_path):
                import shutil

                shutil.copy2(src_path, debug_path)
            debug_file_paths.append(src_path)  # 元ファイルパスを使用

        # PDF結合処理（ユーザー向けは本体ディレクトリに保存）
        timestamp = now_in_app_timezone().strftime("%Y%m%d_%H%M%S")
        merged_pdf_name = f"merged_response_{timestamp}.pdf"
        merged_pdf_path = os.path.join(pdfs_dir, merged_pdf_name)
        pdf_file_paths = debug_file_paths  # 元ファイルから結合

        self.pdf_service.merge_pdfs(pdf_file_paths, merged_pdf_path)

        pdf_url = f"{get_pdf_url_prefix()}/{merged_pdf_name}"

        return {
            "answer": f"ダミー回答: {query}（カテゴリ: {category}）",
            "sources": sources,
            "pdf_url": pdf_url,
        }
