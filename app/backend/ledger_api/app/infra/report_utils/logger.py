"""Internal logger utility for report services."""
import logging
import os
import socket
import getpass
import time
from pathlib import Path


def jst_time(*args):
    """日本時間に変換する関数（UTC + 9時間）"""
    return time.localtime(time.time() + 9 * 60 * 60)


def app_logger(to_console=True) -> logging.Logger:
    """Report services用のロガーを取得"""
    # ログディレクトリを確保（環境変数で設定可能）
    log_dir = Path(os.getenv("REPORT_LOG_DIR", "/tmp/report_logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "app.log"

    logger = logging.getLogger("report_app_logger")
    logger.setLevel(logging.DEBUG)

    # 重複して出力されないように既存のハンドラを削除
    if logger.hasHandlers():
        logger.handlers.clear()

    hostname = socket.gethostname()
    username = getpass.getuser()

    formatter = logging.Formatter(
        f"%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) [{hostname}/{username}] %(message)s"
    )
    formatter.converter = jst_time

    # ファイル出力設定
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # コンソール出力
    if to_console:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger
