"""
ローカル設定パス定義

アプリケーション固有のパス設定を定義するモジュールです。
帳票出力ディレクトリ、デバッグディレクトリなどのパスを管理します。
"""

# 帳票出力関連のパス設定
MANAGE_REPORT_OUTPUT_DIR = (
    "/backend/app/api/endpoints/static/manage_report"  # 帳票出力ディレクトリ
)
MANAGE_REPORT_URL_BASE = "/ledger_api/static/manage_report"  # 帳票出力用URL基底パス
DEBUG_MANAGE_REPORTDIR = (
    "/backend/app/data/csv/debug/manage_report"  # デバッグ用帳票保存ディレクトリ
)

# Streamlitアプリケーション関連のパス設定
BASE_ST_APP_DIR = "/backend/app/st_app"  # Streamlitアプリケーション基底ディレクトリ
