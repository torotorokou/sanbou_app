import os


# --- 共通設定 ---

# アプリのベースディレクトリ
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # /backend/

# よく使うパス
CONFIG_DIR = os.path.join(BASE_DIR, "config")
LOG_DIR = os.path.join(BASE_DIR, "logs")
# データソースはinfra/data_sourcesに移動済み
DATA_DIR = os.path.join(BASE_DIR, "infra", "data_sources")

# Streamlit共通設定
DEFAULT_PORT = 8501  # 基本ポート
