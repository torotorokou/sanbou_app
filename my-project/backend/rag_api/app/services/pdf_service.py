import os
import re
import PyPDF2
from .pdf_service_base import PDFServiceBase

class PDFService(PDFServiceBase):
    def safe_filename(self, s: str) -> str:
        return re.sub(r"[^A-Za-z0-9_-]", "", s)

    def save_pdf_pages_and_get_urls(self, pdf_path, query_name, pages, save_dir, url_prefix):
        safe_name = self.safe_filename(query_name)
        os.makedirs(save_dir, exist_ok=True)
        pdf_urls = []
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for p in pages:
                    dummy_pdf_path = os.path.join(save_dir, f"answer_{safe_name}_{p}.pdf")
                    if not os.path.exists(dummy_pdf_path):
                        writer = PyPDF2.PdfWriter()
                        if 1 <= p <= len(reader.pages):
                            writer.add_page(reader.pages[p - 1])
                        else:
                            writer.add_blank_page(width=595, height=842)
                        with open(dummy_pdf_path, "wb") as out_f:
                            writer.write(out_f)
                    pdf_urls.append(f"{url_prefix}/answer_{safe_name}_{p}.pdf")
        except Exception:
            # PDF読めない場合は空PDF
            for p in pages:
                dummy_pdf_path = os.path.join(save_dir, f"answer_{safe_name}_{p}.pdf")
                if not os.path.exists(dummy_pdf_path):
                    writer = PyPDF2.PdfWriter()
                    writer.add_blank_page(width=595, height=842)
                    with open(dummy_pdf_path, "wb") as out_f:
                        writer.write(out_f)
                pdf_urls.append(f"{url_prefix}/answer_{safe_name}_{p}.pdf")
        return pdf_urls

    def merge_pdfs(self, pdf_file_paths, output_path):
        writer = PyPDF2.PdfWriter()
        for fpath in pdf_file_paths:
            try:
                with open(fpath, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        writer.add_page(page)
            except Exception:
                writer.add_blank_page(width=595, height=842)
        with open(output_path, "wb") as out_f:
            writer.write(out_f)
        return output_path
