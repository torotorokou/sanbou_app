from abc import ABC, abstractmethod
from typing import List


class PDFServiceBase(ABC):
    @abstractmethod
    def save_pdf_pages_and_get_urls(
        self,
        pdf_path: str,
        query_name: str,
        pages: List[int],
        save_dir: str,
        url_prefix: str,
    ) -> List[str]:
        pass

    @abstractmethod
    def merge_pdfs(self, pdf_file_paths: List[str], output_path: str) -> str:
        pass
