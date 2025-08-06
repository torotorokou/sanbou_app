"""
共有設定パス定義

共有ライブラリ用のパス設定を定義するモジュールです。
CSV定義ファイル、設定ファイル、一時保存ディレクトリなどのパスを管理します。
"""

# backend_shared/config/paths.py

# CSV設定ファイルのパス
SYOGUNCSV_DEF_PATH = (
    "/backend/config/csv_config/syogun_csv_masters.yaml"  # 昇軍CSV定義ファイル
)
MANAGER_CSV_DEF_PATH = (
    "/backend/config/report_config/manage_report_masters.yaml"  # 帳票管理設定ファイル
)

# CSV保存・一時ディレクトリ
SAVE_DIR_TEMP = "/backend/app/data/syogun_csv"  # 一時CSV保存ディレクトリ
