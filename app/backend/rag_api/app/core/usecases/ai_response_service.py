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
from app.utils.file_utils import PDF_PATH
from app.paths import get_pdf_url_prefix
from app.core.ports.pdf_service_port import PDFServiceBase


class AIResponseService:
    """
    AI回答生成サービス

    AIによる回答生成とPDF処理を組み合わせたレスポンス作成を担当します。
    """

    def __init__(self, pdf_service: PDFServiceBase):
        self.pdf_service = pdf_service

    def generate_ai_response(
        self, query: str, category: str, tags: List[str]
    ) -> Dict[str, Any]:
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
        print(
            "[DEBUG][AIResponseService] input:",
            {"query": query, "category": category, "tags": tags},
        )
        answer = None
        sources: list[Any] = []
        pages = None
        error_code: str | None = None
        error_detail: str | None = None
        
        try:
            # 遅延インポート：テストや軽量実行時に不要な依存を避ける
            from app.infra.adapters.llm import ai_loader  # type: ignore
            result = ai_loader.get_answer(query, category, tags)
            
            # エラーレスポンスのチェック
            if "error" in result:
                error_msg = result.get("error", "不明なエラー")
                error_code = result.get("error_code", "OPENAI_ERROR")
                print("[DEBUG][AIResponseService] ai_loader returned error:", error_msg)
                print("[DEBUG][AIResponseService] error_code:", error_code)
                
                # エラーコードに応じたメッセージ生成
                if error_code == "OPENAI_INSUFFICIENT_QUOTA":
                    error_detail = (
                        "OpenAI APIの利用上限を超過しているため、現在回答を生成できません。"
                        "管理者にお問い合わせください。"
                    )
                elif error_code == "OPENAI_RATE_LIMIT":
                    error_detail = (
                        "OpenAI APIのレート制限に達しました。しばらく時間をおいて再度お試しください。"
                    )
                else:
                    error_detail = (
                        f"AI回答の生成中にエラーが発生しました: {error_msg}"
                    )
                
                # エラー情報を返却（answer=None, error_code/error_detailを含む）
                return {
                    "answer": None,
                    "sources": [],
                    "pdf_url": None,
                    "error_code": error_code,
                    "error_detail": error_detail,
                }
            else:
                answer = result.get("answer")
                sources = result.get("sources", [])
                pages = result.get("pages")
                print("[DEBUG][AIResponseService] ai_loader result pages:", pages)
        except Exception as ae:
            # 予期しない例外：汎用エラーとして扱う
            print("[DEBUG][AIResponseService] ai_loader failed:", repr(ae))
            return {
                "answer": None,
                "sources": [],
                "pdf_url": None,
                "error_code": "OPENAI_ERROR",
                "error_detail": f"AI回答の生成中に予期しないエラーが発生しました: {str(ae)}",
            }

        # PDF保存先ディレクトリ
        static_dir = os.environ.get("PDFS_DIR") or "/backend/static/pdfs"
        debug_dir = os.path.join(static_dir, "debug")
        os.makedirs(static_dir, exist_ok=True)
        os.makedirs(debug_dir, exist_ok=True)
        pdf_path = str(PDF_PATH)

        # ページリスト正規化
        page_list = self._normalize_pages(pages)
        print("[DEBUG][AIResponseService] normalized pages:", page_list)

        # 個別PDF生成（デバッグ用ディレクトリに保存）
        pdf_url: str | None = None
        try:
            pdf_urls = self.pdf_service.save_pdf_pages_and_get_urls(
                pdf_path=pdf_path,
                query_name=query,
                pages=page_list,
                save_dir=debug_dir,  # デバッグディレクトリに保存
                url_prefix=f"{get_pdf_url_prefix()}/debug",  # デバッグ用URL
            )
            print("[DEBUG][AIResponseService] per-page pdf URLs:", pdf_urls)

            # ページが無い、または保存できたPDFが無い場合は結合をスキップ
            if not pdf_urls:
                pdf_url = None
            else:
                # PDF結合（ユーザー向けは本体ディレクトリに保存）
                jst = ZoneInfo("Asia/Tokyo")
                timestamp = datetime.now(jst).strftime("%Y%m%d_%H%M%S")
                merged_pdf_name = f"merged_response_{timestamp}.pdf"
                merged_pdf_path = os.path.join(static_dir, merged_pdf_name)
                pdf_file_paths = [
                    os.path.join(debug_dir, url.split("/")[-1]) for url in pdf_urls
                ]
                try:
                    self.pdf_service.merge_pdfs(pdf_file_paths, merged_pdf_path)
                    print("[DEBUG][AIResponseService] merged pdf:", merged_pdf_path)
                    pdf_url = f"{get_pdf_url_prefix()}/{merged_pdf_name}"
                except Exception as me:
                    print("[DEBUG][AIResponseService] merge failed:", repr(me))
                    pdf_url = None
        except Exception as se:
            # PDF保存段階での失敗もanswerは返す
            print("[DEBUG][AIResponseService] save pages failed:", repr(se))
            pdf_url = None

        return {"answer": answer, "sources": sources, "pdf_url": pdf_url}

    def _normalize_pages(self, pages) -> List[int]:
        """ページリストを正規化

        - カンマ区切りや範囲指定(1-3)を展開して、正の整数の昇順ユニークなリストを返す。
        - 不正トークンは無視しつつデバッグログを出力する。
        """
        before_repr = repr(pages)
        normalized: List[int] = []

        def debug_skip(token: object, reason: str) -> None:
            print(f"[DEBUG][normalize_pages] skip token={token!r} reason={reason}")

        def add_if_positive(n: int) -> None:
            if isinstance(n, int) and n > 0:
                normalized.append(n)
            else:
                debug_skip(n, "non_positive")

        def handle_token(token: object) -> None:
            t = str(token).strip()
            if not t:
                debug_skip(token, "empty")
                return
            if "-" in t:
                try:
                    start_s, end_s = t.split("-", 1)
                    start, end = int(start_s.strip()), int(end_s.strip())
                    if start <= end:
                        for x in range(start, end + 1):
                            add_if_positive(x)
                    else:
                        debug_skip(t, "range_start_gt_end")
                except Exception:
                    try:
                        n = int(t)
                        add_if_positive(n)
                    except Exception:
                        debug_skip(t, "not_int_or_range")
            else:
                try:
                    n = int(t)
                    add_if_positive(n)
                except Exception:
                    debug_skip(t, "not_int")

        # None → []
        if pages is None:
            print(f"[DEBUG][normalize_pages] before={before_repr}, after=[]")
            return []

        # 単一の整数
        if isinstance(pages, int):
            add_if_positive(pages)
        # 文字列（カンマ分割 → 各トークン処理）
        elif isinstance(pages, str):
            for tok in pages.split(","):
                handle_token(tok)
        # リスト（要素内のカンマも処理）
        elif isinstance(pages, list):
            for p in pages:
                if isinstance(p, str) and "," in p:
                    for tok in p.split(","):
                        handle_token(tok)
                else:
                    handle_token(p)
        else:
            # 未知型は無視
            debug_skip(type(pages).__name__, "unsupported_type")

        after = sorted(set(normalized))
        print(f"[DEBUG][normalize_pages] before={before_repr}, after={after}")
        return after
