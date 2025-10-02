"""Logger utility for report services."""
from ._logger import app_logger as _app_logger


def app_logger():
    """アプリ共通ロガー（内部実装へ移行済み）"""
    return _app_logger()
