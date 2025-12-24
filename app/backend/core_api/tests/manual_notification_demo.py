"""
通知基盤の動作確認スクリプト（手動実行用）

使い方:
    cd /home/koujiro/work_env/22.Work_React/sanbou_app/app/backend/core_api
    python -m tests.manual_notification_demo
"""
from datetime import datetime

from app.infra.adapters.notification.in_memory_outbox_adapter import (
    InMemoryNotificationOutboxAdapter,
)
from app.infra.adapters.notification.noop_sender_adapter import (
    NoopNotificationSenderAdapter,
)
from app.core.usecases.notification.enqueue_notifications_uc import (
    EnqueueNotificationRequest,
    EnqueueNotificationsUseCase,
)
from app.core.usecases.notification.dispatch_pending_notifications_uc import (
    DispatchPendingNotificationsUseCase,
)


def main():
    """通知基盤の動作デモ"""
    print("=== 通知基盤 動作確認 ===\n")

    # インスタンスを直接作成（DB不要）
    outbox = InMemoryNotificationOutboxAdapter()
    sender = NoopNotificationSenderAdapter()
    enqueue_uc = EnqueueNotificationsUseCase(outbox=outbox)
    dispatch_uc = DispatchPendingNotificationsUseCase(outbox=outbox, sender=sender)

    now = datetime.now()

    # Step 1: 通知を登録
    print("Step 1: 通知を登録（3件）")
    requests = [
        EnqueueNotificationRequest(
            channel="email",
            title="新しい受注が入りました",
            body="顧客: ABC株式会社\n金額: 1,234,567円",
            recipient_key="user_001",
            url="https://example.com/orders/123",
        ),
        EnqueueNotificationRequest(
            channel="line",
            title="在庫アラート",
            body="商品A の在庫が残り10個です",
            recipient_key="user_002",
        ),
        EnqueueNotificationRequest(
            channel="email",
            title="レポート生成完了",
            body="月次レポートが生成されました",
            recipient_key="user_001",
            url="https://example.com/reports/monthly",
        ),
    ]
    enqueue_uc.execute(requests=requests, now=now)
    print("✓ 3件の通知を登録しました\n")

    # Step 2: pending 状態を確認
    print("Step 2: pending 状態を確認")
    pending = outbox.list_pending(now=now)
    print(f"✓ pending 通知: {len(pending)}件")
    for item in pending:
        print(f"  - [{item.channel}] {item.payload.title} (recipient: {item.recipient_key})")
    print()

    # Step 3: 通知を送信（Noop）
    print("Step 3: 通知を送信（Noop実装のためログ出力のみ）")
    sent_count = dispatch_uc.execute(now=now)
    print(f"✓ {sent_count}件の通知を送信しました（実際は送信していません）\n")

    # Step 4: 送信後の状態を確認
    print("Step 4: 送信後の状態を確認")
    pending_after = outbox.list_pending(now=now)
    print(f"✓ 残りの pending 通知: {len(pending_after)}件")
    if pending_after:
        print("  （まだ pending があります - リトライ待ち等）")
    else:
        print("  （すべて処理されました）")
    print()

    print("=== 動作確認完了 ===")
    print("\n次のステップ:")
    print("- DB永続化: InMemoryNotificationOutboxAdapter を DB実装に差し替え")
    print("- 実送信: NoopNotificationSenderAdapter を実装に差し替え")
    print("  - Email: SMTP/SendGrid/AWS SES 等")
    print("  - LINE: LINE Messaging API")
    print("  - Webhook: requests 等で HTTP POST")
    print("  - Push: FCM/APNs 等")


if __name__ == "__main__":
    main()
