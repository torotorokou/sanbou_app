import os
import re
import hashlib
import PyPDF2
from .pdf_service_base import PDFServiceBase
from backend_shared.core.domain.exceptions import ValidationError


class PDFService(PDFServiceBase):
    def safe_filename(self, s: str) -> str:
        base = re.sub(r"[^A-Za-z0-9_-]", "", s or "")
        if base:
            return base
        # 日本語などで空になった場合はハッシュで安定名を生成
        h = hashlib.md5((s or "").encode("utf-8")).hexdigest()[:8]
        return f"q_{h}"

    def save_pdf_pages_and_get_urls(
        self, pdf_path, query_name, pages, save_dir, url_prefix
    ):
        safe_name = self.safe_filename(query_name)
        os.makedirs(save_dir, exist_ok=True)
        pdf_urls = []
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                total = len(reader.pages)

                for p in pages:
                    # ページ番号を安全にint化
                    try:
                        p_int = int(str(p).strip())
                    except Exception:
                        continue
                    dummy_pdf_path = os.path.join(
                        save_dir, f"answer_{safe_name}_{p_int}.pdf"
                    )
                    writer = PyPDF2.PdfWriter()
                    try:
                        # 1-based の場合
                        if 1 <= p_int <= total:
                            writer.add_page(reader.pages[p_int - 1])
                        # 0-based の場合
                        elif 0 <= p_int < total:
                            writer.add_page(reader.pages[p_int])
                        else:
                            # 無効ページはスキップ（空白PDFを作らない）
                            continue
                    except Exception:
                        # ページ抽出に失敗した場合もスキップ
                        continue
                    with open(dummy_pdf_path, "wb") as out_f:
                        writer.write(out_f)
                    pdf_urls.append(f"{url_prefix}/answer_{safe_name}_{p_int}.pdf")
        except Exception:
            # 元PDFが開けない場合はすべて空白
            for p in pages:
                try:
                    p_int = int(str(p).strip())
                except Exception:
                    continue
                dummy_pdf_path = os.path.join(
                    save_dir, f"answer_{safe_name}_{p_int}.pdf"
                )
                if not os.path.exists(dummy_pdf_path):
                    writer = PyPDF2.PdfWriter()
                    writer.add_blank_page(width=595, height=842)
                    with open(dummy_pdf_path, "wb") as out_f:
                        writer.write(out_f)
                pdf_urls.append(f"{url_prefix}/answer_{safe_name}_{p_int}.pdf")
        return pdf_urls

    def merge_pdfs(self, pdf_file_paths, output_path):
        writer = PyPDF2.PdfWriter()
        added = 0
        for fpath in pdf_file_paths:
            try:
                with open(fpath, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        writer.add_page(page)
                        added += 1
            except Exception:
                # 入力PDFがおかしい場合はスキップ
                continue
        if added == 0:
            raise ValidationError("No valid pages to merge", field="pdf_file_paths")
        with open(output_path, "wb") as out_f:
            writer.write(out_f)
        return output_path
