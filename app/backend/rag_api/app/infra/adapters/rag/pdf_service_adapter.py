import hashlib
import os
import re

import pypdf
from app.core.ports.rag.pdf_service_port import PDFServiceBase
from backend_shared.application.logging import get_module_logger
from backend_shared.core.domain.exceptions import ValidationError

logger = get_module_logger(__name__)


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
        logger.info(
            "Saving PDF pages",
            extra={
                "pdf_path": pdf_path,
                "pages_count": len(pages),
                "save_dir": save_dir,
            },
        )
        safe_name = self.safe_filename(query_name)
        os.makedirs(save_dir, exist_ok=True)
        pdf_urls = []
        try:
            with open(pdf_path, "rb") as f:
                reader = pypdf.PdfReader(f)
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
                    writer = pypdf.PdfWriter()
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
        except Exception as e:
            logger.error(
                "Failed to read PDF",
                exc_info=True,
                extra={"pdf_path": pdf_path, "error": str(e)},
            )
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
                    writer = pypdf.PdfWriter()
                    writer.add_blank_page(width=595, height=842)
                    with open(dummy_pdf_path, "wb") as out_f:
                        writer.write(out_f)
                pdf_urls.append(f"{url_prefix}/answer_{safe_name}_{p_int}.pdf")
        logger.info(
            "PDF pages saved successfully", extra={"pdf_urls_count": len(pdf_urls)}
        )
        return pdf_urls

    def merge_pdfs(self, pdf_file_paths, output_path):
        logger.info(
            "Merging PDFs",
            extra={"file_count": len(pdf_file_paths), "output_path": output_path},
        )
        writer = pypdf.PdfWriter()
        added = 0
        for fpath in pdf_file_paths:
            try:
                with open(fpath, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    for page in reader.pages:
                        writer.add_page(page)
                        added += 1
            except Exception as e:
                # 入力PDFがおかしい場合はスキップ
                logger.warning(
                    "Failed to read PDF for merge",
                    extra={"fpath": fpath, "error": str(e)},
                )
                continue
        if added == 0:
            logger.error("No valid pages to merge")
            raise ValidationError("No valid pages to merge", field="pdf_file_paths")
        with open(output_path, "wb") as out_f:
            writer.write(out_f)
        logger.info("PDFs merged successfully", extra={"pages_merged": added})
        return output_path
