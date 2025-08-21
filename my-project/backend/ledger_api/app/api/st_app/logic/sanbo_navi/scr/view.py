import streamlit as st
from pdf2image import convert_from_path

# --- PDF画像の読み込み ---
@st.cache_resource
def load_pdf_first_page(path, dpi=100):
    return convert_from_path(path, dpi=dpi, first_page=1, last_page=1)

@st.cache_resource
def load_pdf_page(path, page_number, dpi=100):
    return convert_from_path(
        path, dpi=dpi, first_page=page_number, last_page=page_number
    )[0]

# --- 1ページ目の表示（新規追加） ---
def render_pdf_first_page(pdf_image):
    st.image(pdf_image, caption="Page 1", use_container_width=True)

# --- PDFページ表示 ---
def render_pdf_pages(PDF_PATH, pages):
    if "cache_pdf_pages" not in st.session_state:
        st.session_state.cache_pdf_pages = {}

    # --- ページ解釈を強化（カンマ＋範囲） ---
    def debug(msg: str):
        print(f"[DEBUG][render_pdf_pages] {msg}")

    def add_positive(target: list[int], n: int):
        if n > 0:
            target.append(n)
        else:
            debug(f"skip non_positive: {n}")

    def handle_token(target: list[int], token: object):
        t = str(token).strip()
        if not t:
            debug(f"skip empty token: {token!r}")
            return
        if "-" in t:
            try:
                s, e = t.split("-", 1)
                start, end = int(s.strip()), int(e.strip())
                if start <= end:
                    for x in range(start, end + 1):
                        add_positive(target, x)
                else:
                    debug(f"skip range_start_gt_end: {t}")
            except Exception:
                try:
                    n = int(t)
                    add_positive(target, n)
                except Exception:
                    debug(f"skip not_int_or_range: {t}")
        else:
            try:
                n = int(t)
                add_positive(target, n)
            except Exception:
                debug(f"skip not_int: {t}")

    page_numbers: list[int] = []
    debug(f"before pages={pages!r}")
    if pages is None:
        page_numbers = []
    elif isinstance(pages, int):
        add_positive(page_numbers, pages)
    elif isinstance(pages, str):
        for tok in pages.split(","):
            handle_token(page_numbers, tok)
    elif isinstance(pages, list):
        for p in pages:
            if isinstance(p, str) and "," in p:
                for tok in p.split(","):
                    handle_token(page_numbers, tok)
            else:
                handle_token(page_numbers, p)
    else:
        debug(f"unsupported pages type: {type(pages).__name__}")
    page_numbers = sorted(set(page_numbers))
    debug(f"after pages={page_numbers}")

    with st.expander("📘 出典ページのプレビュー"):
        for p in page_numbers:
            if p >= 1:
                if p in st.session_state.cache_pdf_pages:
                    st.image(
                        st.session_state.cache_pdf_pages[p],
                        caption=f"Page {p} (cached)",
                        use_container_width=True,
                    )
                else:
                    with st.spinner(f"📄 Page {p} 読み込み中..."):
                        page_image = load_pdf_page(PDF_PATH, p)
                        st.session_state.cache_pdf_pages[p] = page_image
                        st.image(
                            page_image,
                            caption=f"Page {p}",
                            use_container_width=True,
                        )
