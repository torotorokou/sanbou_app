# 共通: DSNと基本import
import datetime as dt
import json
import math
import os

import numpy as np
import pandas as pd
import psycopg
from backend_shared.infra.db.url_builder import build_database_url


def _dsn() -> str:
    """データベース接続URLを取得（テスト用）"""
    # DB_DSN 環境変数のサポート（後方互換性）
    dsn = os.getenv("DB_DSN")
    if dsn:
        return dsn.strip()

    # backend_shared の共通関数を使用
    return build_database_url(driver=None, raise_on_missing=True)
