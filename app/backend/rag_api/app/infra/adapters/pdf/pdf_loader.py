"""
PDFファイルのページ画像取得ユーティリティ。
fitz（PyMuPDF）とPillowを利用してPDFページをPNG画像として返す。
"""

import io

import fitz
from PIL import Image


def get_pdf_page_image(pdf_path: str, page_num: int) -> io.BytesIO:
    """
    指定したPDFファイルのページ画像をPNG形式で取得する。

    Args:
        pdf_path (str): PDFファイルのパス
        page_num (int): ページ番号（0始まり）

    Returns:
        io.BytesIO: PNG画像データ
    """
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
