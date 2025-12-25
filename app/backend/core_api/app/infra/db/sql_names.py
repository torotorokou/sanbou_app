"""
SQL識別子定数

⚠️ DEPRECATED: このファイルは非推奨です
代わりに backend_shared.db.names を使用してください。

移行方法:
    from backend_shared.db.names import SCHEMA_MART, MV_RECEIVE_DAILY, fq

    sql = f"SELECT * FROM {fq(SCHEMA_MART, MV_RECEIVE_DAILY)}"

詳細:
    - docs/backend/20251211_DB_NAMES_IMPLEMENTATION_REPORT.md
    - docs/backend/20251211_DB_REALITY_CHECK.md

このファイルは後方互換性のために残されています。
新しいコードでは backend_shared.db.names を使用してください。
"""

import warnings

warnings.warn(
    "sql_names.py is deprecated. Use backend_shared.db.names instead.",
    DeprecationWarning,
    stacklevel=2,
)

# martスキーマのビュー/MV(集約済みデータ)
V_RECEIVE_DAILY = "mart.mv_receive_daily"  # 日次搬入集計MV (旧: v_receive_daily)
V_RECEIVE_WEEKLY = "mart.v_receive_weekly"  # 週次搬入集計ビュー
V_RECEIVE_MONTHLY = "mart.v_receive_monthly"  # 月次搬入集計ビュー

# refスキーマのビュー(参照データ)
V_CALENDAR = "ref.v_calendar_classified"  # カレンダービュー(営業日区分付き)
