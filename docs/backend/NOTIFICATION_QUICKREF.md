# 通知システム クイックリファレンス

**最終更新**: 2025年12月25日

---

## 📋 チートシート

### 通知を送信する

```python
from app.core.usecases.notification.enqueue_notifications_uc import (
    EnqueueNotificationRequest
)

# Email通知
request = EnqueueNotificationRequest(
    channel="email",
    title="件名",
    body="本文",
    recipient_key="email:user@example.com",
    url="https://app.example.com/detail",
)

# LINE通知（user_id指定）
request = EnqueueNotificationRequest(
    channel="line",
    title="タイトル",
    body="本文",
    recipient_key="user:123",  # user_id → LINE userIdに自動解決
)

# Outboxに登録（UseCaseをDIから取得）
enqueue_uc.execute(requests=[request], now=datetime.now(timezone.utc))
```

### recipient_key形式

| 形式                | 例                        | 用途                       |
| ------------------- | ------------------------- | -------------------------- |
| `email:{address}`   | `email:admin@example.com` | メール直接送信             |
| `user:{id}`         | `user:123`                | ユーザーID（LINE等に解決） |
| `aud:{site}:{code}` | `aud:tokyo:A001`          | 視聴者コード               |

### ステータス遷移

```
pending → sent       （送信成功）
        → failed     （PERMANENT失敗、リトライなし）
        → pending    （TEMPORARY失敗、リトライあり）
        → skipped    （Preference無効化 or Resolver解決失敗）
```

---

## 🛠️ 運用コマンド

### Outbox確認

```sql
-- 全通知の状態集計
SELECT status, channel, COUNT(*)
FROM app.notification_outbox
GROUP BY status, channel;

-- Pending通知一覧
SELECT id, channel, recipient_key, title, created_at, retry_count
FROM app.notification_outbox
WHERE status = 'pending'
ORDER BY created_at DESC;

-- 最近の失敗通知
SELECT id, channel, recipient_key, last_error, failure_type
FROM app.notification_outbox
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;
```

### 手動リトライ

```sql
-- 特定の通知をリトライ対象に戻す
UPDATE app.notification_outbox
SET status = 'pending',
    next_retry_at = NULL
WHERE id = '<UUID>';
```

### データクリーンアップ

```sql
-- 7日以上前の完了通知を削除
DELETE FROM app.notification_outbox
WHERE status IN ('sent', 'skipped', 'failed')
  AND created_at < NOW() - INTERVAL '7 days';
```

---

## ⚙️ 環境変数

### 必須設定

```bash
# DB永続化
USE_DB_NOTIFICATION_OUTBOX=true

# スケジューラー
ENABLE_NOTIFICATION_SCHEDULER=true
NOTIFICATION_DISPATCH_INTERVAL_MINUTES=1
```

### Email送信（Phase 3）

```bash
ENABLE_EMAIL_NOTIFICATION=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@example.com
SMTP_PASSWORD=<SECRET>
```

### LINE送信（Phase 3）

```bash
ENABLE_LINE_NOTIFICATION=true
USE_DB_RECIPIENT_RESOLVER=true
LINE_CHANNEL_ACCESS_TOKEN=<SECRET>
```

---

## 🧪 テスト用データ

### InMemory Preference（テスト用）

| recipient_key | email_enabled | line_enabled |
| ------------- | ------------- | ------------ |
| `user:1`      | ✅            | ✅           |
| `user:2`      | ✅            | ❌           |
| `user:3`      | ❌            | ✅           |

### Dummy Resolver動作

- `email:addr@example.com` → `addr@example.com`（そのまま）
- `user:*` for LINE → `None`（未連携扱い → skipped）

---

## 🚨 トラブルシューティング

### 通知が送信されない

1. Schedulerログ確認

   ```bash
   docker compose logs core_api | grep "Dispatching"
   ```

2. Outbox確認

   ```sql
   SELECT * FROM app.notification_outbox
   WHERE status = 'pending' AND next_retry_at < NOW();
   ```

3. 環境変数確認
   ```bash
   docker compose exec core_api env | grep NOTIFICATION
   ```

### LINE通知がskipped

- **開発環境**: Dummy Resolver使用中（正常）
- **本番環境**: user_line_accounts テーブル確認
  ```sql
  SELECT * FROM app.user_line_accounts WHERE user_id = 123;
  ```

### PERMANENT失敗

```sql
-- エラー内容確認
SELECT recipient_key, last_error
FROM app.notification_outbox
WHERE failure_type = 'PERMANENT'
ORDER BY created_at DESC LIMIT 5;
```

→ recipient_key形式エラー or API token無効

---

## 📚 関連ドキュメント

- [完全ガイド](./NOTIFICATION_SYSTEM_GUIDE.md) - 詳細な実装・運用ガイド
- [完了報告](./notification_line_foundation_COMPLETED.md) - LINE基盤の実装詳細
- [優先タスク](./NOTIFICATION_PRIORITY_TASKS.md) - 実装ロードマップ
