from abc import ABC, abstractmethod


class PDFServiceBase(ABC):
    @abstractmethod
    def save_pdf_pages_and_get_urls(
        self,
        pdf_path: str,
        query_name: str,
        pages: list[int],
        save_dir: str,
        url_prefix: str,
    ) -> list[str]:
        pass

    @abstractmethod
    def merge_pdfs(self, pdf_file_paths: list[str], output_path: str) -> str:
        pass
