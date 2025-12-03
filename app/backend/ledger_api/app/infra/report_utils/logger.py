"""Internal logger utility for report services.

【廃止予定】このモジュールは後方互換性のために残されています。
新しいコードでは backend_shared.application.logging を直接使用してください。

 Migration Guide:
   OLD: from app.infra.report_utils import app_logger
        logger = app_logger()
   
   NEW: from backend_shared.application.logging import get_module_logger
        logger = get_module_logger(__name__)
"""
import logging
import warnings
from backend_shared.application.logging import get_module_logger

# 非推奨警告を発行
warnings.warn(
    "app_logger() is deprecated. Use backend_shared.application.logging.get_module_logger() instead.",
    DeprecationWarning,
    stacklevel=2
)


def app_logger(to_console=True) -> logging.Logger:
    """Report services用のロガーを取得
    
    【廃止予定】このロガーはbackend_sharedの統一ログ基盤に移行されました。
    後方互換性のためにラッパーとして残されています。
    
    Args:
        to_console: 使用されません（互換性のためのダミー引数）
        
    Returns:
        logging.Logger: backend_sharedの標準ロガー
        
    Deprecated:
        代わりに get_module_logger(__name__) を使用してください。
    """
    # backend_sharedの統一ログ基盤を使用
    # setup_logging()は既にmain.pyで実行されているため、ここでは呼ばない
    return get_module_logger("ledger_api.report")
