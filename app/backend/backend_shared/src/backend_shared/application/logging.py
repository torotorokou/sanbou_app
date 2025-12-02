"""
Backend Shared Logging Infrastructure

全バックエンドサービスで共通利用するログ基盤。
構造化ログ出力、Request ID トレーシング、実行時間計測を提供します。

Features:
  - 統一logging設定（JSON形式、Request ID自動付与）
  - Request ID による完全なリクエストトレーシング
  - UseCase実行ログ（デコレータ形式）
  - 実行時間の計測
  - エラートラッキング (exc_info付き)
  - メトリクス収集 (success/error/validation_error カウント)

使用例:
    # アプリケーション起動時（main.py / app.py）
    from backend_shared.application.logging import setup_logging
    setup_logging()
    
    # UseCase内でのログ出力
    from backend_shared.application.logging import log_usecase_execution
    
    class GetCalendarMonthUseCase:
        @log_usecase_execution(usecase_name="GetCalendarMonth", log_args=True)
        def execute(self, year: int, month: int):
            return self.query.get_month_calendar(year, month)
"""
import logging
import logging.config
import os
import time
import functools
from typing import Callable, Any, Optional, Dict
from datetime import datetime
from contextvars import ContextVar

# pythonjsonlogger は optional: なければ通常のフォーマッタを使用
try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False

logger = logging.getLogger(__name__)


# ========================================
# グローバル状態: Logging 設定済みフラグ
# ========================================
# setup_logging() の重複呼び出しを防ぐためのフラグ
_logging_configured: bool = False


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
def create_json_formatter() -> logging.Formatter:
    """
    JSON形式のログフォーマッタを作成
    
    Returns:
        JsonFormatter または Formatter
        
    Description:
        pythonjsonlogger がインストールされている場合はJSON形式、
        なければ通常のテキスト形式でログを出力します。
        
        JSONフィールド:
        - timestamp: ISO 8601形式のタイムスタンプ
        - level: ログレベル (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        - logger: ロガー名 (通常はモジュール名)
        - request_id: リクエストID (Middleware で設定)
        - message: ログメッセージ
        - その他: extra で渡された任意のフィールド
    """
    if HAS_JSON_LOGGER:
        # JSON形式
        log_format = "%(asctime)s %(levelname)s %(name)s %(request_id)s %(message)s"
        formatter = jsonlogger.JsonFormatter(
            log_format,
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
            datefmt="%Y-%m-%dT%H:%M:%S",  # ISO 8601 形式
        )
    else:
        # テキスト形式（fallback）
        log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(request_id)s] %(message)s"
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    return formatter


# ========================================
# Logging 設定関数
# ========================================
def setup_logging(log_level: str | None = None, force: bool = False) -> None:
    """
    アプリケーション全体の logging 設定を行う
    
    Args:
        log_level: ログレベル (DEBUG/INFO/WARNING/ERROR/CRITICAL)
                   省略時は環境変数 LOG_LEVEL または INFO
        force: True の場合、既に設定済みでも再設定を強制する（テスト用）
                   
    Description:
        以下の設定を行います:
        1. ルートロガーの設定（レベル、ハンドラ、フォーマッタ）
        2. Request ID Filter の追加
        3. Uvicorn / FastAPI ロガーの統合
        4. 既存ハンドラのクリア（重複防止）
        
    Note:
        アプリケーション起動時に1回だけ呼び出してください。
        複数回呼び出しても、2回目以降は無視されます（force=True でない限り）。
        
    Example:
        >>> from backend_shared.application.logging import setup_logging
        >>> setup_logging()  # app.py の最初で実行
        >>> setup_logging()  # 2回目は無視される
    """
    global _logging_configured
    
    # 既に設定済みの場合はスキップ（force=True でない限り）
    if _logging_configured and not force:
        return
    
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
    
    # Formatter の設定（JSON or Text）
    formatter = create_json_formatter()
    stream_handler.setFormatter(formatter)
    
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
        logger_instance = logging.getLogger(logger_name)
        logger_instance.handlers.clear()  # 既存ハンドラをクリア
        logger_instance.addHandler(stream_handler)  # 共通ハンドラを追加
        logger_instance.setLevel(numeric_level)
        logger_instance.propagate = False  # ルートロガーへの伝播を防ぐ（重複防止）
    
    # ========================================
    # サードパーティライブラリのログレベル調整
    # ========================================
    # httpx, httpcore などの詳細ログを抑制（本番環境でのノイズ削減）
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # 設定完了フラグを立てる
    _logging_configured = True
    
    # 設定完了ログ
    format_type = "json" if HAS_JSON_LOGGER else "text"
    root_logger.info(
        "Logging configuration initialized",
        extra={
            "log_level": log_level,
            "format": format_type,
            "output": "stdout",
        }
    )


# ========================================
# Helper 関数: Request ID の設定・取得
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
        >>> from backend_shared.application.logging import set_request_id
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
        >>> from backend_shared.application.logging import get_request_id
        >>> print(get_request_id())
        "550e8400-e29b-41d4-a716-446655440000"
    """
    return request_id_var.get()


# ========================================
# Helper 関数: 構造化ログコンテキスト作成
# ========================================
def create_log_context(
    operation: str,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    構造化ログのコンテキスト辞書を作成
    
    Args:
        operation: 操作名（例: "csv_upload", "build_target_card"）- 必須
        **kwargs: 追加のコンテキスト情報
        
    Returns:
        Dict[str, Any]: extra辞書として使用可能なコンテキスト
        
    Description:
        標準化された構造化ログを簡単に作成するためのヘルパー関数。
        Noneやセンシティブ情報を自動除外します。
        
    Example:
        >>> context = create_log_context(
        ...     operation="csv_upload",
        ...     file_type="FLASH",
        ...     uploaded_by="user@example.com"
        ... )
        >>> logger.info("CSV upload started", extra=context)
    """
    # センシティブなキーワードリスト
    sensitive_keywords = ["password", "token", "secret", "key", "credential"]
    
    # コンテキスト辞書を構築
    context = {"operation": operation}
    
    for key, value in kwargs.items():
        # センシティブ情報をスキップ
        if any(sensitive in key.lower() for sensitive in sensitive_keywords):
            continue
        
        # None値をスキップ
        if value is None:
            continue
        
        context[key] = value
    
    return context


def get_module_logger(name: str | None = None) -> logging.Logger:
    """
    モジュール用のロガーを取得
    
    Args:
        name: ロガー名（省略時は呼び出し元モジュール名を自動取得）
        
    Returns:
        logging.Logger: 設定済みのロガー
        
    Description:
        標準的な logging.getLogger(__name__) のラッパー。
        将来的にロガーのカスタマイズが必要になった場合に対応しやすくする。
        
    Example:
        >>> logger = get_module_logger(__name__)
        >>> logger.info("Processing started")
    """
    if name is None:
        # 呼び出し元のモジュール名を自動取得
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'unknown')
        else:
            name = 'unknown'
    
    return logging.getLogger(name)


# ========================================
# Helper 関数: 時間計測コンテキストマネージャー
# ========================================
class TimedOperation:
    """
    時間計測付きコンテキストマネージャー
    
    with文で囲んだブロックの実行時間を自動計測し、ログに記録します。
    
    Example:
        >>> with TimedOperation("database_query", logger=logger, threshold_ms=1000):
        ...     result = db.execute_slow_query()
        # ログ: "database_query completed in 1234ms"
        
        >>> with TimedOperation("csv_processing", logger=logger) as timer:
        ...     process_csv(file)
        ...     timer.add_context(rows=1000)
        # ログ: "csv_processing completed in 567ms" extra={"rows": 1000}
    """
    
    # ビジネスエラーとして扱う例外タイプ（WARNING レベル）
    BUSINESS_ERRORS = (ValueError, KeyError, TypeError, AttributeError)
    
    def __init__(
        self,
        operation_name: str,
        logger: logging.Logger | None = None,
        level: int = logging.INFO,
        threshold_ms: float | None = None,
        **context: Any
    ):
        """
        Args:
            operation_name: 操作名
            logger: ロガー（省略時は backend_shared.application.logging のロガー）
            level: ログレベル（デフォルト: INFO）
            threshold_ms: 閾値（ミリ秒）。実行時間がこれを超えた場合のみログ出力
            **context: 追加のコンテキスト情報
        """
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.level = level
        self.threshold_ms = threshold_ms
        self.context = context
        self.start_time: float | None = None
        self.duration_ms: float | None = None
    
    def __enter__(self) -> "TimedOperation":
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is None:
            return
        
        elapsed = time.perf_counter() - self.start_time
        self.duration_ms = round(elapsed * 1000, 2)
        
        # 閾値チェック
        if self.threshold_ms is not None and self.duration_ms < self.threshold_ms:
            return  # 閾値未満の場合はログ出力しない
        
        # ログコンテキストを構築
        log_context = create_log_context(
            operation=self.operation_name,
            duration_ms=self.duration_ms,
            **self.context
        )
        
        # エラーがあれば適切なレベルでログ出力、なければ指定されたレベルでログ出力
        if exc_type is not None:
            log_context["error_type"] = exc_type.__name__
            log_context["error_message"] = str(exc_val)
            
            # ビジネスエラー（予期されたエラー）は WARNING レベル
            if isinstance(exc_val, self.BUSINESS_ERRORS):
                self.logger.warning(
                    f"{self.operation_name} failed with business error after {self.duration_ms}ms",
                    extra=log_context,
                    exc_info=False  # スタックトレース不要
                )
            else:
                # システムエラー（予期しないエラー）は ERROR レベル
                self.logger.error(
                    f"{self.operation_name} failed after {self.duration_ms}ms",
                    extra=log_context,
                    exc_info=True  # スタックトレース付き
                )
        else:
            self.logger.log(
                self.level,
                f"{self.operation_name} completed in {self.duration_ms}ms",
                extra=log_context
            )
    
    def add_context(self, **kwargs: Any) -> None:
        """
        実行中にコンテキスト情報を追加
        
        Args:
            **kwargs: 追加のコンテキスト情報
        """
        self.context.update(kwargs)


# ========================================
# ログレベル定数（可読性向上）
# ========================================
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"


# ========================================
# UseCase ログデコレータ（既存機能）
# ========================================


def log_usecase_execution(
    usecase_name: Optional[str] = None,
    log_args: bool = True,
    log_result: bool = False,
    track_time: bool = True,
) -> Callable:
    """
    UseCaseの実行をログに記録するデコレータ
    
    Args:
        usecase_name: UseCase名（省略時はクラス名.メソッド名）
        log_args: 引数をログに記録するか
        log_result: 戻り値をログに記録するか（大きなデータの場合は注意）
        track_time: 実行時間を計測するか
        
    Returns:
        デコレータ関数
        
    Example:
        >>> @log_usecase_execution(usecase_name="GetCalendarMonth")
        >>> def execute(self, year: int, month: int):
        >>>     return self.query.get_month_calendar(year, month)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # UseCase名の決定
            uc_name = usecase_name
            if not uc_name:
                # クラスメソッドの場合: ClassName.method_name
                if args and hasattr(args[0], '__class__'):
                    class_name = args[0].__class__.__name__
                    uc_name = f"{class_name}.{func.__name__}"
                else:
                    uc_name = func.__name__
            
            # 実行開始ログ
            log_data: Dict[str, Any] = {
                "usecase": uc_name,
                "timestamp": datetime.utcnow().isoformat(),
                "event": "start",
            }
            
            if log_args and kwargs:
                # センシティブな情報を除外（password, token など）
                safe_kwargs = {
                    k: v for k, v in kwargs.items()
                    if not any(sensitive in k.lower() for sensitive in ["password", "token", "secret"])
                }
                log_data["input_args"] = safe_kwargs
            
            logger.info(f"[UseCase] {uc_name} started", extra=log_data)
            
            # 実行時間計測
            start_time = time.perf_counter() if track_time else None
            
            try:
                # UseCase実行
                result = func(*args, **kwargs)
                
                # 実行完了ログ
                elapsed_time = time.perf_counter() - start_time if start_time else None
                
                log_data.update({
                    "event": "success",
                    "elapsed_ms": round(elapsed_time * 1000, 2) if elapsed_time else None,
                })
                
                if log_result and result is not None:
                    # 大きすぎる結果はログしない
                    if isinstance(result, (list, dict)):
                        log_data["result_size"] = len(result)
                    else:
                        log_data["result"] = str(result)[:200]  # 最大200文字
                
                logger.info(f"[UseCase] {uc_name} completed", extra=log_data)
                
                return result
                
            except Exception as e:
                # エラーログ
                elapsed_time = time.perf_counter() - start_time if start_time else None
                
                log_data.update({
                    "event": "error",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "elapsed_ms": round(elapsed_time * 1000, 2) if elapsed_time else None,
                })
                
                logger.error(f"[UseCase] {uc_name} failed", extra=log_data, exc_info=True)
                
                raise
        
        return wrapper
    return decorator


class UseCaseMetrics:
    """
    UseCaseのメトリクス収集クラス（オプション）
    
    将来的に Prometheus, CloudWatch などに統合可能。
    現在はメモリ内でカウントのみ保持。
    
    使用例:
        metrics = UseCaseMetrics()
        metrics.increment("GetCalendarMonth", "success")
        print(metrics.get_metrics("GetCalendarMonth"))  # {'success': 1}
    """
    
    _instance = None
    _metrics: Dict[str, Dict[str, int]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._metrics = {}
        return cls._instance
    
    def increment(self, usecase_name: str, status: str = "success") -> None:
        """
        UseCaseの実行カウントをインクリメント
        
        Args:
            usecase_name: UseCase名
            status: 実行ステータス (success, error, validation_error)
        """
        if usecase_name not in self._metrics:
            self._metrics[usecase_name] = {}
        
        if status not in self._metrics[usecase_name]:
            self._metrics[usecase_name][status] = 0
        
        self._metrics[usecase_name][status] += 1
    
    def get_metrics(self, usecase_name: Optional[str] = None) -> Dict[str, Any]:
        """
        メトリクスを取得
        
        Args:
            usecase_name: 特定のUseCaseのメトリクスを取得（省略時は全て）
            
        Returns:
            メトリクスの辞書
        """
        if usecase_name:
            return self._metrics.get(usecase_name, {})
        return self._metrics.copy()
    
    def reset(self) -> None:
        """全メトリクスをリセット"""
        self._metrics.clear()
        logger.info("UseCase metrics reset")


def track_usecase_metrics(usecase_name: Optional[str] = None) -> Callable:
    """
    UseCaseのメトリクスを収集するデコレータ
    
    Args:
        usecase_name: UseCase名（省略時はクラス名.メソッド名）
        
    Returns:
        デコレータ関数
        
    Example:
        >>> @track_usecase_metrics()
        >>> def execute(self, year: int, month: int):
        >>>     return self.query.get_month_calendar(year, month)
    """
    metrics = UseCaseMetrics()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # UseCase名の決定
            uc_name = usecase_name
            if not uc_name:
                if args and hasattr(args[0], '__class__'):
                    class_name = args[0].__class__.__name__
                    uc_name = f"{class_name}.{func.__name__}"
                else:
                    uc_name = func.__name__
            
            try:
                result = func(*args, **kwargs)
                metrics.increment(uc_name, "success")
                return result
            except ValueError as e:
                # バリデーションエラー
                metrics.increment(uc_name, "validation_error")
                raise
            except Exception as e:
                # その他のエラー
                metrics.increment(uc_name, "error")
                raise
        
        return wrapper
    return decorator


def combined_usecase_decorator(
    usecase_name: Optional[str] = None,
    log_args: bool = True,
    log_result: bool = False,
    track_metrics: bool = True,
) -> Callable:
    """
    ログとメトリクスを同時に適用する統合デコレータ
    
    Args:
        usecase_name: UseCase名
        log_args: 引数をログに記録するか
        log_result: 戻り値をログに記録するか
        track_metrics: メトリクスを収集するか
        
    Returns:
        デコレータ関数
        
    Example:
        >>> @combined_usecase_decorator(usecase_name="GetCalendarMonth")
        >>> def execute(self, year: int, month: int):
        >>>     # ログとメトリクスが自動的に記録される
        >>>     return self.query.get_month_calendar(year, month)
    """
    def decorator(func: Callable) -> Callable:
        # ログデコレータを適用
        decorated = log_usecase_execution(
            usecase_name=usecase_name,
            log_args=log_args,
            log_result=log_result,
            track_time=True,
        )(func)
        
        # メトリクスデコレータを適用
        if track_metrics:
            decorated = track_usecase_metrics(usecase_name=usecase_name)(decorated)
        
        return decorated
    
    return decorator
