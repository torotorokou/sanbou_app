import os
from pathlib import Path


def _resolve_root() -> str:
    """アプリ基底ディレクトリを解決 (後方互換)。

    優先順位:
        1. APP_ROOT_DIR (新)
        2. APP_BASE_DIR (旧)
        3. /backend (デフォルト)
    """
    return os.environ.get("APP_ROOT_DIR") or os.environ.get("APP_BASE_DIR") or "/backend"


BASE_DIR = Path(_resolve_root())
print(
    "APP_ROOT_DIR:",
    os.environ.get("APP_ROOT_DIR"),
    "(fallback APP_BASE_DIR=",
    os.environ.get("APP_BASE_DIR"),
    ") =>",
    BASE_DIR,
)

# 各種パス（環境変数で上書き可）
CONFIG_ENV = os.environ.get("CONFIG_ENV", str(BASE_DIR / "config/.env"))
LOCAL_DATA_DIR = Path(os.environ.get("LOCAL_DATA_DIR", str(BASE_DIR / "local_data/master")))

# YAML: with_tags に統一。旧名は互換のため同一パスを指す。
CATEGORY_QUESTION_TEMPLATES_WITH_TAGS = Path(
    os.environ.get(
        "CATEGORY_QUESTION_TEMPLATES_WITH_TAGS",
        str(LOCAL_DATA_DIR / "category_question_templates_with_tags.yaml"),
    )
)
CATEGORY_QUESTION_TEMPLATES = Path(
    os.environ.get(
        "CATEGORY_QUESTION_TEMPLATES",
        str(CATEGORY_QUESTION_TEMPLATES_WITH_TAGS),
    )
)
SOLVEST_PDF = Path(os.environ.get("SOLVEST_PDF", str(LOCAL_DATA_DIR / "SOLVEST.pdf")))
SOLVEST_PLAN_PDF = Path(
    os.environ.get("SOLVEST_PLAN_PDF", str(LOCAL_DATA_DIR / "solvest_business_plan_20240305.pdf"))
)

# ベクトルストア
VECTORSTORE_DIR = Path(os.environ.get("VECTORSTORE_DIR", str(LOCAL_DATA_DIR / "vectorstore")))
SOLVEST_FAISS = Path(
    os.environ.get("SOLVEST_FAISS", str(VECTORSTORE_DIR / "solvest_faiss_with_tag"))
)
# SOLVEST_FAISS_CORRECTED = VECTORSTORE_DIR / "solvest_faiss_corrected"
# SOLVEST_FAISS_PLAN = VECTORSTORE_DIR / "solvest_faiss_plan"

# structured_output_with_tags.json のパス
STRUCTURED_OUTPUT_WITH_TAGS = Path(
    os.environ.get(
        "STRUCTURED_OUTPUT_WITH_TAGS",
        str(LOCAL_DATA_DIR / "structured_output_with_tags.json"),
    )
)


# --- API ルートパス関連（環境変数を動的参照） -------------------------------
def get_api_root_path() -> str:
    """
    FastAPI の root_path に合わせるための接頭辞。
    .env などの環境変数 API_ROOT_PATH を動的に参照（デフォルト: "/rag_api"）。
    """
    return os.environ.get("API_ROOT_PATH", "/rag_api")


def get_pdf_url_prefix() -> str:
    """
    静的に公開している /pdfs のURL接頭辞（例: "/rag_api/pdfs"）。
    ルートパスが空のときは "/pdfs" を返す。
    """
    root = get_api_root_path().rstrip("/")
    return f"{root}/pdfs" if root else "/pdfs"
