"""
Logging Configuration - テクニカルログ基盤

【概要】
アプリケーション全体の統一的なロギング設定を提供します。
GCP Cloud Logging に対応した構造化ログ（JSON形式）を標準出力へ出力します。

【主な機能】
1. グローバルlogging設定の統一
2. JSON形式のログフォーマット（pythonjsonlogger）
3. Request ID のログへの自動付与（ContextVar経由）
4. Uvicorn / FastAPI ロガーの統合
5. ログレベルの環境変数による制御

【設計方針】
- コンテナ実行前提: 標準出力（stdout）のみに出力
- Cloud Logging 対応: JSON形式で構造化ログを出力
- Request ID 自動付与: ContextVar から取得して全ログに含める
- 環境変数制御: LOG_LEVEL で本番/開発環境を切り替え

【使用例】
```python
# アプリケーション起動時に1回だけ呼び出す
from app.config.logging import setup_logging

setup_logging()

# 各モジュールで通常通り使用
import logging
logger = logging.getLogger(__name__)
logger.info("Processing started", extra={"user_id": 123})
```
"""
import logging
import logging.config
import os
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger


# ========================================
# ContextVar: Request ID の保持
# ========================================
# リクエスト単位でrequest_idを保持するためのContextVar
# Middleware で設定され、Filter で取得される
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


# ========================================
# Custom Filter: Request ID 付与
# ========================================
class RequestIdFilter(logging.Filter):
    """
    Request ID をログレコードに自動付与する Filter
    
    ContextVar から request_id を取得し、LogRecord に追加します。
    これにより、フォーマッタで %(request_id)s を使用できるようになります。
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        ログレコードに request_id 属性を追加
        
        Args:
            record: ログレコード
            
        Returns:
            True (常にログを通過させる)
        """
        # ContextVar から request_id を取得（なければ "-"）
        record.request_id = request_id_var.get()
        return True


# ========================================
# JSON Formatter の定義
# ========================================
def create_json_formatter() -> jsonlogger.JsonFormatter:
    """
    JSON形式のログフォーマッタを作成
    
    Returns:
        JsonFormatter: pythonjsonlogger のフォーマッタ
        
    Description:
        以下のフィールドを含むJSON形式のログを出力します:
        - timestamp: ISO 8601形式のタイムスタンプ
        - level: ログレベル (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        - logger: ロガー名 (通常はモジュール名)
        - request_id: リクエストID (Middleware で設定)
        - message: ログメッセージ
        - その他: extra で渡された任意のフィールド
    """
    # フォーマット指定: これらのフィールドが JSON に含まれる
    log_format = "%(asctime)s %(levelname)s %(name)s %(request_id)s %(message)s"
    
    # JsonFormatter のカスタマイズ
    formatter = jsonlogger.JsonFormatter(
        log_format,
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
        datefmt="%Y-%m-%dT%H:%M:%S",  # ISO 8601 形式
    )
    
    return formatter


# ========================================
# Logging 設定関数
# ========================================
def setup_logging(log_level: str | None = None) -> None:
    """
    アプリケーション全体の logging 設定を行う
    
    Args:
        log_level: ログレベル (DEBUG/INFO/WARNING/ERROR/CRITICAL)
                   省略時は環境変数 LOG_LEVEL または INFO
                   
    Description:
        以下の設定を行います:
        1. ルートロガーの設定（レベル、ハンドラ、フォーマッタ）
        2. Request ID Filter の追加
        3. Uvicorn / FastAPI ロガーの統合
        4. 既存ハンドラのクリア（重複防止）
        
    Note:
        アプリケーション起動時に1回だけ呼び出してください。
        複数回呼び出すと、ハンドラが重複してログが多重出力されます。
    """
    # ログレベルの決定
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # 数値レベルに変換
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # ルートロガーの取得
    root_logger = logging.getLogger()
    
    # 既存ハンドラのクリア（重複防止）
    root_logger.handlers.clear()
    
    # レベル設定
    root_logger.setLevel(numeric_level)
    
    # StreamHandler の作成（標準出力）
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(numeric_level)
    
    # JSON Formatter の設定
    json_formatter = create_json_formatter()
    stream_handler.setFormatter(json_formatter)
    
    # Request ID Filter の追加
    request_id_filter = RequestIdFilter()
    stream_handler.addFilter(request_id_filter)
    
    # ルートロガーにハンドラを追加
    root_logger.addHandler(stream_handler)
    
    # ========================================
    # Uvicorn / FastAPI ロガーの統合
    # ========================================
    # Uvicorn の各ロガーに対して、同じハンドラ・フィルタを適用
    uvicorn_loggers = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    ]
    
    for logger_name in uvicorn_loggers:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()  # 既存ハンドラをクリア
        logger.addHandler(stream_handler)  # 共通ハンドラを追加
        logger.setLevel(numeric_level)
        logger.propagate = False  # ルートロガーへの伝播を防ぐ（重複防止）
    
    # ========================================
    # サードパーティライブラリのログレベル調整
    # ========================================
    # httpx, httpcore などの詳細ログを抑制（本番環境でのノイズ削減）
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # 設定完了ログ
    root_logger.info(
        "Logging configuration initialized",
        extra={
            "log_level": log_level,
            "format": "json",
            "output": "stdout",
        }
    )


# ========================================
# Helper 関数: Request ID の設定
# ========================================
def set_request_id(request_id: str) -> None:
    """
    Request ID を ContextVar に設定
    
    Args:
        request_id: リクエストID（UUID等）
        
    Description:
        Middleware からこの関数を呼び出して request_id を設定します。
        以降、同じコンテキスト内の全ログに自動で request_id が付与されます。
        
    Example:
        >>> from app.config.logging import set_request_id
        >>> set_request_id("550e8400-e29b-41d4-a716-446655440000")
    """
    request_id_var.set(request_id)


def get_request_id() -> str:
    """
    Request ID を ContextVar から取得
    
    Returns:
        str: リクエストID（未設定の場合は "-"）
        
    Description:
        現在のコンテキストの request_id を取得します。
        主にテスト用途やデバッグ用途で使用します。
        
    Example:
        >>> from app.config.logging import get_request_id
        >>> print(get_request_id())
        "550e8400-e29b-41d4-a716-446655440000"
    """
    return request_id_var.get()


# ========================================
# ログレベル定数（可読性向上）
# ========================================
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"
