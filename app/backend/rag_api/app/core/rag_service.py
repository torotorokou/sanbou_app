import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings

from app.infrastructure.pdf.pdf_loader import (
    load_pdf_first_page,
    render_pdf_first_page,
    render_pdf_pages,
)
from app.core.file_ingest_service import (
    load_config,
    load_json_data,
    extract_categories_and_titles,
    load_question_templates,
)
from app.infrastructure.llm.ai_loader import OpenAIConfig, load_ai
from app.infrastructure.llm.openai_client import OpenAIClient, generate_answer
from app.utils.chunk_utils import load_vectorstore
from components.custom_button import centered_button


def controller_education_gpt_page():
    FAISS_PATH, PDF_PATH, JSON_PATH = load_config()
    json_data = load_json_data(JSON_PATH)
    templates = load_question_templates()
    categories = list(templates.keys())

    client = load_ai(OpenAIConfig)
    llm_client = OpenAIClient(client)
    vectorstore = load_vectorstore(api_key=client.api_key, FAISS_PATH=FAISS_PATH)

    st.title("📘 教育GPTアシスタント")
    st.markdown("SOLVESTについて質問できます。")

    with st.expander("📄 PDFプレビュー"):
        pdf_first_page = load_pdf_first_page(PDF_PATH)
        render_pdf_first_page(pdf_first_page[0])

    main_category = st.selectbox("まずカテゴリを選択してください", categories)
    category_template = templates.get(main_category, [])

    all_tags = sorted(set(
        tag.strip(" []'"")
        for t in category_template
        for tag in t.get("tag", [])
        if isinstance(tag, str)
    ))

    selected_tags = st.multiselect("次に、関心のあるトピック（タグ）を選択してください", all_tags)

    filtered_questions = [
        t["title"] for t in category_template
        if any(tag.strip(" []'"") in selected_tags for tag in t.get("tag", []))
    ] if selected_tags else []
    subcategory_options = ["自由入力"] + filtered_questions
    sub_category = st.selectbox("質問テンプレートを選択（または自由入力）", options=subcategory_options)

    if sub_category == "自由入力":
        user_input = st.text_area("質問内容を入力してください", height=100)
        query = user_input.strip()
    else:
        query = sub_category

    if centered_button("➡️ 送信") and query:
        with st.spinner("🤖 回答生成中..."):
            answer, sources = generate_answer(query, main_category, vectorstore, llm_client)
            st.session_state.last_response = answer
            st.session_state.sources = sources

    if "last_response" in st.session_state:
        st.success("✅ 回答")
        st.markdown(st.session_state.last_response)

    if "sources" in st.session_state:
        pages = {str(page) for _, page in st.session_state.sources}
        st.markdown("📄 **出典ページ:** " + ", ".join([f"Page {p}" for p in sorted(pages)]))
        render_pdf_pages(PDF_PATH, pages)


if __name__ == "__main__":
    controller_education_gpt_page()