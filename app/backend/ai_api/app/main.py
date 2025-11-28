from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import requests
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from backend_shared.infra.frameworks.logging_utils import setup_uvicorn_access_filter
from backend_shared.core.domain.exceptions import ExternalServiceError, InfrastructureError

# .envからAPIキーを読み込む
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI(
    title="AI 応答API",
    description="PDF連動のAI応答や自然言語処理を提供するAPI群です。",
    version="1.0.0",
    root_path="/ai_api",  # ベースパスを統一
)

# Exception handlers for backend_shared exceptions
@app.exception_handler(ExternalServiceError)
async def handle_external_service_error(request: Request, exc: ExternalServiceError):
    status_code = 502 if exc.status_code is None else (504 if exc.status_code >= 500 else 502)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": "EXTERNAL_SERVICE_ERROR",
                "message": f"{exc.service_name}: {exc.message}",
                "service": exc.service_name,
                "status_code": exc.status_code,
            }
        },
    )

@app.exception_handler(InfrastructureError)
async def handle_infrastructure_error(request: Request, exc: InfrastructureError):
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "INFRASTRUCTURE_ERROR",
                "message": exc.message,
            }
        },
    )

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ログ設定: /health のアクセスログのみ抑制（エラーは従来通り出力）
setup_uvicorn_access_filter(excluded_paths=("/health",))

# ===== エンドポイントをrouterで分離 =====
router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    tags: List[str] = []
    pdf: str = ""


@router.post("/chat")
def chat(req: ChatRequest):
    prompt = f"""
以下はPDFに関連する質問です。

質問: {req.query}
関連タグ: {", ".join(req.tags)}
関連PDF: {req.pdf or "指定なし"}

質問に対してわかりやすく丁寧に答えてください。
"""
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
            f"?key={GEMINI_API_KEY}"
        )
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
        response.raise_for_status()
        data = response.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"]

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
    except requests.exceptions.RequestException as e:
        # Gemini API通信エラー
        raise ExternalServiceError(
            service_name="Gemini API",
            message=f"Chat endpoint communication failed: {str(e)}",
            status_code=getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
            cause=e
        )
    except (KeyError, IndexError) as e:
        # レスポンス形式が不正
        raise ExternalServiceError(
            service_name="Gemini API",
            message=f"Unexpected response format: {str(e)}",
            cause=e
        )


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
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
            f"?key={GEMINI_API_KEY}"
        )
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
        response.raise_for_status()
        data = response.json()
        message = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"text": message}
    except requests.exceptions.RequestException as e:
        # Gemini API通信エラー
        raise ExternalServiceError(
            service_name="Gemini API",
            message=f"Intro endpoint communication failed: {str(e)}",
            status_code=getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
            cause=e
        )
    except (KeyError, IndexError) as e:
        # レスポンス形式が不正
        raise ExternalServiceError(
            service_name="Gemini API",
            message=f"Unexpected response format: {str(e)}",
            cause=e
        )


# 疎通確認用
@router.get("/ping")
def ping():
    return {"status": "ai ok"}


# 最小動作確認用: backend_shared のインポートテスト
@router.post("/validate")
def validate(rows: List[dict]):
    """
    backend_shared パッケージの動作確認用エンドポイント。
    簡易的なバリデーションを実行して ok を返します。
    """
    # 簡易チェック: rows が空でないか
    if not rows:
        return {"ok": False, "errors": ["No rows provided"]}
    
    # backend_shared からのインポートテスト
    try:
        from backend_shared.domain import JobStatus
        # 正常にインポートできれば成功
        return {"ok": True, "errors": [], "imported": "backend_shared.domain.JobStatus"}
    except ImportError as e:
        return {"ok": False, "errors": [f"Import failed: {str(e)}"]}


# ====== ルーターをパス指定で登録 ======
app.include_router(router, prefix="")  # /ai_api直下に登録


# ヘルスチェック
@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
