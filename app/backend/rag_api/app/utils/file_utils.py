
from app.paths import SOLVEST_PDF, STRUCTURED_OUTPUT_WITH_TAGS, SOLVEST_FAISS, CONFIG_ENV, CATEGORY_QUESTION_TEMPLATES_WITH_TAGS
import os

PDF_PATH = SOLVEST_PDF
JSON_PATH = STRUCTURED_OUTPUT_WITH_TAGS
FAISS_PATH = SOLVEST_FAISS
ENV_PATH = CONFIG_ENV
YAML_PATH = CATEGORY_QUESTION_TEMPLATES_WITH_TAGS

def validate_path(path):
    """
    指定パスの存在チェック。存在しなければ例外を投げる。
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"ファイル/ディレクトリが見つかりません: {path}")