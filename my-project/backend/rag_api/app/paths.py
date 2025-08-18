

import os
from pathlib import Path

# プロジェクトのルートディレクトリ（Dockerコンテナ内の/appに固定 or 環境変数で上書き可）
BASE_DIR = Path(os.environ.get("APP_BASE_DIR", "/app"))

# 各種パス（環境変数で上書き可）
CONFIG_ENV = os.environ.get("CONFIG_ENV", str(BASE_DIR / "config/.env"))
LOCAL_DATA_DIR = Path(os.environ.get("LOCAL_DATA_DIR", str(BASE_DIR / "local_data/master")))

CATEGORY_QUESTION_TEMPLATES = Path(os.environ.get("CATEGORY_QUESTION_TEMPLATES", str(LOCAL_DATA_DIR / "category_question_templates.yaml")))
CATEGORY_QUESTION_TEMPLATES_WITH_TAGS = Path(os.environ.get("CATEGORY_QUESTION_TEMPLATES_WITH_TAGS", str(LOCAL_DATA_DIR / "category_question_templates_with_tags.yaml")))
SOLVEST_PDF = Path(os.environ.get("SOLVEST_PDF", str(LOCAL_DATA_DIR / "SOLVEST.pdf")))
SOLVEST_PLAN_PDF = Path(os.environ.get("SOLVEST_PLAN_PDF", str(LOCAL_DATA_DIR / "solvest_business_plan_20240305.pdf")))

# ベクトルストア
VECTORSTORE_DIR = Path(os.environ.get("VECTORSTORE_DIR", str(LOCAL_DATA_DIR / "vectorstore")))
SOLVEST_FAISS = Path(os.environ.get("SOLVEST_FAISS", str(VECTORSTORE_DIR / "solvest_faiss_with_tag")))
# SOLVEST_FAISS_CORRECTED = VECTORSTORE_DIR / "solvest_faiss_corrected"
# SOLVEST_FAISS_PLAN = VECTORSTORE_DIR / "solvest_faiss_plan"

# structured_output_with_tags.json のパス
STRUCTURED_OUTPUT_WITH_TAGS = Path(os.environ.get("STRUCTURED_OUTPUT_WITH_TAGS", str(LOCAL_DATA_DIR / "structured_output_with_tags.json")))

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
