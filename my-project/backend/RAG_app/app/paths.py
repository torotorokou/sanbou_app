
import os
from pathlib import Path

# プロジェクトのルートディレクトリ
BASE_DIR = Path(__file__).resolve().parents[2]

import os
# 各種パス
CONFIG_ENV = os.environ.get("CONFIG_ENV", "/app/config/.env")
LOCAL_DATA_DIR = BASE_DIR / "local_data" / "master"

CATEGORY_QUESTION_TEMPLATES = LOCAL_DATA_DIR / "category_question_templates.yaml"
CATEGORY_QUESTION_TEMPLATES_WITH_TAGS = LOCAL_DATA_DIR / "category_question_templates_with_tags.yaml"
SOLVEST_PDF = LOCAL_DATA_DIR / "SOLVEST.pdf"
SOLVEST_PLAN_PDF = LOCAL_DATA_DIR / "solvest_business_plan_20240305.pdf"

# ベクトルストア
VECTORSTORE_DIR = LOCAL_DATA_DIR / "vectorstore"
SOLVEST_FAISS = VECTORSTORE_DIR / "solvest_faiss_with_tag"
# SOLVEST_FAISS_CORRECTED = VECTORSTORE_DIR / "solvest_faiss_corrected"
# SOLVEST_FAISS_PLAN = VECTORSTORE_DIR / "solvest_faiss_plan"

# structured_output_with_tags.json のパス
STRUCTURED_OUTPUT_WITH_TAGS = LOCAL_DATA_DIR / "structured_output_with_tags.json"
