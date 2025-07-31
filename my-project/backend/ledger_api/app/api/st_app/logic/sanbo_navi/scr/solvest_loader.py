# logic/sanbo_navi/scr/solvest_loader.py

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from app.api.st_app.logic.sanbo_navi.scr.prompts import SYSTEM_PROMPT_PLAN
from app.api.st_app.logic.sanbo_navi.scr.ai_loader import load_ai
import os

VECTORSTORE_PATH = "/backend/logic/sanbo_navi/local_data/master/vectorstore/solvest_faiss_plan"
ENV_PATH = "/backend/logic/sanbo_navi/config/.env"

openai_llm = load_ai()
embeddings = OpenAIEmbeddings()

vectorstore = FAISS.load_local(
    VECTORSTORE_PATH,
    embeddings,
    allow_dangerous_deserialization=True  # 🔐 pickle読み込みを許可（自己生成なら安全）
)

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

def get_solvest_answer(query: str) -> dict:
    """
    質問に対して、SOLVEST事業計画のベクトル検索とLLMによる解説を返す。
    """
    docs: list[Document] = retriever.get_relevant_documents(query)
    if not docs:
        return {"answer": "該当する情報が見つかりませんでした。", "sources": []}

    context = "\n".join([doc.page_content for doc in docs])

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_PLAN},
        {"role": "user", "content": f"次の資料をもとに質問に答えてください：\n{context}\n\n質問：{query}"},
    ]

    answer = openai_llm.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=messages,
        temperature=0.2,
    ).choices[0].message.content

    sources = [
        {
            "title": doc.metadata.get("title", ""),
            "page": doc.metadata.get("page", ""),
            "category": doc.metadata.get("category", []),
            "tag": doc.metadata.get("tag", []),
            "chunk_id": doc.metadata.get("chunk_id", "")
        }
        for doc in docs
    ]

    return {"answer": answer, "sources": sources}
