from fastapi import APIRouter

from app.api.schemas.chat import ChatRequest
from app.infra.adapters.gemini_client import GeminiClient
from backend_shared.application.logging import get_module_logger


logger = get_module_logger(__name__)
router = APIRouter()
ai_client = GeminiClient()


@router.post("/chat")
def chat(req: ChatRequest):
    logger.info(
        "Chat request received",
        extra={"query": req.query, "tags": req.tags, "pdf": req.pdf},
    )
    prompt = f"""
以下はPDFに関連する質問です。

質問: {req.query}
関連タグ: {", ".join(req.tags)}
関連PDF: {req.pdf or "指定なし"}

質問に対してわかりやすく丁寧に答えてください。
"""
    answer = ai_client.generate_content(prompt)

    return {
        "answer": answer,
        "sources": [
            {
                "pdf": req.pdf or "doc1.pdf",
                "section_title": "Gemini応答より",
                "highlight": req.query,
            }
        ],
    }


@router.get("/intro")
def get_intro():
    prompt = """
    あなたは、産業廃棄物に関する業務知識をナビゲートする参謀くんです。
    このアプリの初回説明として、以下の点を盛り込んで、自然な文章と改行で短く説明してください。

    - 自分は、産業廃棄物のプロAIである
    - 業務知識をサポートできる
    - ユーザーにカテゴリを選択してもらう導線を促す
    - フレンドリーかつ丁寧なトーン
    - こんにちは！など最初の挨拶は飛ばす。
    """
    message = ai_client.generate_content(prompt)
    return {"text": message}


# 疎通確認用
@router.get("/ping")
def ping():
    return {"status": "ai ok"}


# 最小動作確認用: backend_shared のインポートテスト
@router.post("/validate")
def validate(rows: list[dict]):
    """
    backend_shared パッケージの動作確認用エンドポイント。
    簡易的なバリデーションを実行して ok を返します。
    """
    # 簡易チェック: rows が空でないか
    if not rows:
        return {"ok": False, "errors": ["No rows provided"]}

    # backend_shared からのインポートテスト
    try:
        from backend_shared.domain import JobStatus  # noqa: F401

        # 正常にインポートできれば成功
        return {"ok": True, "errors": [], "imported": "backend_shared.domain.JobStatus"}
    except ImportError as e:
        return {"ok": False, "errors": [f"Import failed: {str(e)}"]}
