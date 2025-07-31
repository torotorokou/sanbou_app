import logging
import os
import sys
from typing import Optional


def setup_logger(
    name: str, log_file: Optional[str] = None, level: int = logging.INFO
) -> logging.Logger:
    """
    ロガーをセットアップする

    Parameters:
        name (str): ロガー名
        log_file (Optional[str]): ログファイルパス
        level (int): ログレベル

    Returns:
        logging.Logger: 設定済みのロガー
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 既存のハンドラーをクリア
    if logger.hasHandlers():
        logger.handlers.clear()

    # フォーマッターの設定
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) %(message)s"
    )

    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラー（ログファイルが指定されている場合）
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def app_logger(to_console: bool = True) -> logging.Logger:
    """
    アプリケーション用ロガーを取得

    Parameters:
        to_console (bool): コンソール出力するかどうか

    Returns:
        logging.Logger: アプリケーション用ロガー
    """
    log_dir = "/backend/logs"
    log_file = os.path.join(log_dir, "factory_report_app.log") if to_console else None

    return setup_logger("factory_report_app", log_file, logging.INFO)


def debug_logger(to_console: bool = True) -> logging.Logger:
    """
    デバッグ用ロガーを取得

    Parameters:
        to_console (bool): コンソール出力するかどうか

    Returns:
        logging.Logger: デバッグ用ロガー
    """
    log_dir = "/backend/logs"
    log_file = os.path.join(log_dir, "factory_report_debug.log") if to_console else None

    return setup_logger("factory_report_debug", log_file, logging.DEBUG)
