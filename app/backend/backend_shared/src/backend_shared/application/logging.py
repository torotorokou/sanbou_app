"""
Backend Shared UseCase Logging and Monitoring Utilities

全バックエンドサービスで共通利用するUseCaseトレース・監視機能。
構造化ログ出力、実行時間計測、メトリクス収集を提供します。

Features:
  - 実行時間の計測
  - 構造化ログの出力 (JSON format)
  - エラートラッキング (exc_info付き)
  - メトリクス収集 (success/error/validation_error カウント)

使用例:
    from backend_shared.application.logging import log_usecase_execution
    
    class GetCalendarMonthUseCase:
        @log_usecase_execution(usecase_name="GetCalendarMonth", log_args=True)
        def execute(self, year: int, month: int):
            return self.query.get_month_calendar(year, month)
"""
import logging
import time
import functools
from typing import Callable, Any, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


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
