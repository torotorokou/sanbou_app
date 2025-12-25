"""
Notification Dispatcher - Scheduled Background Job

定期的にpending状態の通知をDispatchする。
APSchedulerを使用してFastAPI起動時にスケジューラーを開始。
"""

import os
from datetime import UTC

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)

# グローバルスケジューラー（シングルトン）
_scheduler: BackgroundScheduler | None = None


def dispatch_pending_notifications_job():
    """
    スケジュールジョブ: pending通知を送信

    DI経由でUseCaseを取得して実行。
    エラーが発生してもジョブは継続（次回実行に影響しない）。
    """
    logger.info("Notification dispatch job started")
    try:
        from datetime import datetime

        from app.config.di_providers import (
            get_notification_outbox_port,
            get_notification_sender_port,
        )
        from app.core.usecases.notification.dispatch_pending_notifications_uc import (
            DispatchPendingNotificationsUseCase,
        )
        from app.deps import get_db

        # DBセッション取得
        db = next(get_db())
        try:
            # アダプター取得（環境変数でInMemory/DB切り替え）
            outbox = get_notification_outbox_port(db)
            sender = get_notification_sender_port()

            # UseCase実行
            uc = DispatchPendingNotificationsUseCase(outbox=outbox, sender=sender)
            now = datetime.now(UTC)
            sent_count = uc.execute(now=now)

            logger.info(
                "Notification dispatch completed",
                extra={"sent_count": sent_count, "job": "dispatch_notifications"},
            )
        finally:
            db.close()

    except Exception as e:
        logger.error(
            f"Notification dispatch job failed: {e}",
            extra={"error": str(e), "job": "dispatch_notifications"},
            exc_info=True,
        )


def start_notification_scheduler():
    """
    通知ディスパッチャースケジューラーを開始

    環境変数でスケジューラーの有効/無効を制御:
    - ENABLE_NOTIFICATION_SCHEDULER=true: スケジューラー有効
    - ENABLE_NOTIFICATION_SCHEDULER=false or 未設定: スケジューラー無効

    起動時に1度だけ呼び出す（app.py の startup イベント）。
    """
    global _scheduler

    # 環境変数チェック
    enabled = os.getenv("ENABLE_NOTIFICATION_SCHEDULER", "false").lower() == "true"
    if not enabled:
        logger.info(
            "Notification scheduler is disabled (ENABLE_NOTIFICATION_SCHEDULER=false)"
        )
        return

    if _scheduler is not None:
        logger.warning("Notification scheduler already started")
        return

    # スケジューラー初期化
    _scheduler = BackgroundScheduler()

    # ジョブ登録: 1分間隔でpending通知を処理
    interval_minutes = int(os.getenv("NOTIFICATION_DISPATCH_INTERVAL_MINUTES", "1"))
    _scheduler.add_job(
        func=dispatch_pending_notifications_job,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="dispatch_pending_notifications",
        name="Dispatch Pending Notifications",
        replace_existing=True,
        max_instances=1,  # 同時実行を防ぐ
    )

    # スケジューラー開始
    _scheduler.start()
    logger.info(
        f"Notification scheduler started (interval={interval_minutes}min)",
        extra={"interval_minutes": interval_minutes},
    )


def stop_notification_scheduler():
    """
    通知ディスパッチャースケジューラーを停止

    シャットダウン時に1度だけ呼び出す（app.py の shutdown イベント）。
    """
    global _scheduler

    if _scheduler is None:
        return

    _scheduler.shutdown(wait=True)
    _scheduler = None
    logger.info("Notification scheduler stopped")


def get_scheduler_status() -> dict:
    """
    スケジューラーのステータスを取得（デバッグ用）

    Returns:
        dict: スケジューラーの状態情報
    """
    if _scheduler is None:
        return {"running": False, "jobs": []}

    return {
        "running": _scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": (
                    job.next_run_time.isoformat() if job.next_run_time else None
                ),
            }
            for job in _scheduler.get_jobs()
        ],
    }
