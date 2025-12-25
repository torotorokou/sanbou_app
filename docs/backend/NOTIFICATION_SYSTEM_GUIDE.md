# 通知システム完全ガイド（Email / LINE）

**最終更新**: 2025年12月25日  
**ステータス**: Phase 2完了（LINE基盤準備完了）

---

## 📖 目次

1. [システム概要](#システム概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [実装状況](#実装状況)
4. [Email通知](#email通知)
5. [LINE通知](#line通知)
6. [開発者ガイド](#開発者ガイド)
7. [運用ガイド](#運用ガイド)
8. [トラブルシューティング](#トラブルシューティング)

---

## システム概要

### 目的

アプリケーションからユーザーへの通知を、信頼性高く、拡張可能な方法で送信する基盤システム。

### 対応チャネル

| チャネル  | ステータス                  | 用途                                   |
| --------- | --------------------------- | -------------------------------------- |
| **email** | ✅ 準備完了（Sender未実装） | システム通知、レポート送信             |
| **line**  | ✅ 基盤準備完了             | リアルタイム通知、ユーザー向けアラート |
| webhook   | 🔜 将来対応                 | 外部システム連携                       |
| push      | 🔜 将来対応                 | モバイルアプリ通知                     |

### 主要機能

- **Transactional Outbox Pattern**: DB永続化による確実な送信
- **リトライ機構**: 指数バックオフ（1→5→30→60分）
- **失敗分類**: TEMPORARY（リトライ可）/ PERMANENT（リトライ不可）
- **スケジュール送信**: 指定時刻での送信予約
- **通知許可管理**: ユーザー別・チャネル別のopt-in制御
- **Recipient解決**: 統一キー（`user:123`）からチャネル固有ID（LINE userId等）への変換

---

## アーキテクチャ

### Clean Architecture + DDD

```
┌─────────────────────────────────────────────────────────┐
│                     Use Cases                           │
│  ┌──────────────────┐  ┌──────────────────────────┐    │
│  │ Enqueue          │  │ DispatchPending          │    │
│  │ Notifications    │  │ Notifications            │    │
│  └──────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                       Ports                             │
│  ┌──────────────┐ ┌──────────────┐ ┌───────────────┐  │
│  │ Outbox       │ │ Sender       │ │ Preference    │  │
│  │ Port         │ │ Port         │ │ Port          │  │
│  └──────────────┘ └──────────────┘ └───────────────┘  │
│  ┌──────────────┐                                       │
│  │ Resolver     │                                       │
│  │ Port         │                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                     Adapters                            │
│  ┌──────────────┐ ┌──────────────┐ ┌───────────────┐  │
│  │ DB Outbox    │ │ Noop Sender  │ │ InMemory      │  │
│  │ (Prod)       │ │ (Dev)        │ │ Preference    │  │
│  └──────────────┘ └──────────────┘ └───────────────┘  │
│  ┌──────────────┐ ┌──────────────┐ ┌───────────────┐  │
│  │ InMemory     │ │ Email Sender │ │ Dummy         │  │
│  │ Outbox(Dev)  │ │ (TODO)       │ │ Resolver      │  │
│  └──────────────┘ └──────────────┘ └───────────────┘  │
│                    ┌──────────────┐                     │
│                    │ LINE Sender  │                     │
│                    │ (TODO)       │                     │
│                    └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   Infrastructure                        │
│  ┌──────────────┐ ┌──────────────┐ ┌───────────────┐  │
│  │ PostgreSQL   │ │ LINE API     │ │ SMTP Server   │  │
│  │ (Outbox)     │ │ (未実装)     │ │ (未実装)      │  │
│  └──────────────┘ └──────────────┘ └───────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Recipient Key統一方針

すべての通知は以下の形式で宛先を管理します：

| 形式                | 例                        | 用途                                      |
| ------------------- | ------------------------- | ----------------------------------------- |
| `user:{id}`         | `user:123`                | ユーザーID（将来的にLINE userId等に解決） |
| `email:{address}`   | `email:admin@example.com` | メールアドレス直接指定                    |
| `aud:{site}:{code}` | `aud:tokyo:A001`          | 視聴者コード（レポート送信等）            |

**利点**:

- チャネルに依存しない統一的な宛先管理
- 将来的な拡張が容易（`user:123` → LINE userId / Push token 等への解決）
- データベース設計の柔軟性

---

## 実装状況

### Phase 1: DB永続化 + 定期実行 ✅ 完了（2024-12-24）

- ✅ Alembic migration: `20251224_005_create_notification_outbox_table.py`
- ✅ NotificationOutboxORM model（UUID PK、JSONB meta、retry logic）
- ✅ DbNotificationOutboxAdapter（PostgreSQL永続化）
- ✅ APScheduler統合（1分間隔、FastAPI lifecycle管理）
- ✅ 環境変数制御: `USE_DB_NOTIFICATION_OUTBOX`, `ENABLE_NOTIFICATION_SCHEDULER`

### Phase 2: LINE通知基盤 ✅ 完了（2025-12-25）

#### 実装内容

**Domain層**:

- ✅ `FailureType` enum（TEMPORARY / PERMANENT）
- ✅ `RecipientRef` dataclass（recipient_key解析）
- ✅ `NotificationPreference` dataclass（opt-in制御）

**Ports層**:

- ✅ `NotificationPreferencePort`（通知許可管理）
- ✅ `RecipientResolverPort`（チャネル固有ID解決）
- ✅ `mark_failed(failure_type)`, `mark_skipped(reason)` 拡張

**Adapters層**:

- ✅ `InMemoryNotificationPreferenceAdapter`（テスト用）
- ✅ `DummyRecipientResolverAdapter`（テスト用）
- ✅ `InMemoryOutboxAdapter` TEMP/PERM対応
- ✅ `DbOutboxAdapter` failure_type対応

**UseCases層**:

- ✅ `DispatchPendingNotificationsUseCase` 拡張
  - Preference判定 → Resolver解決 → 送信 → 失敗分類

**DBマイグレーション**:

- ✅ `20251225_001_add_notification_outbox_failure_type.py`
  - `failure_type VARCHAR(20)` カラム追加

**テスト**:

- ✅ 16ケース全成功（既存13 + 新規3）
  - Preference無効化でskipped検証
  - Resolver解決失敗でskipped検証
  - ValueError→PERMANENT, RuntimeError→TEMPORARY検証

### Phase 3: 実Email/LINE送信 🔜 未実装

**残タスク**:

- Email Sender実装（SMTP連携）
- LINE Sender実装（Messaging API連携）
- DB Recipient Resolver実装（user_line_accounts テーブル）
- 環境変数制御

---

## Email通知

### 現状

- **Outbox**: ✅ 実装済み（DB永続化）
- **Sender**: ⚠️ Noop実装（実際に送信されない）
- **Recipient解決**: ✅ `email:addr@example.com` → そのまま使用

### 実装待ち: Email Sender

```python
# app/infra/adapters/notification/email_sender_adapter.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailNotificationSenderAdapter(NotificationSenderPort):
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send(self, channel: str, payload: NotificationPayload, recipient_key: str) -> None:
        if channel != "email":
            raise ValueError(f"Unsupported channel: {channel}")

        # MIME message構築
        msg = MIMEMultipart("alternative")
        msg["Subject"] = payload.title
        msg["From"] = self.username
        msg["To"] = recipient_key

        # HTML body
        html = f"""
        <html>
          <body>
            <h2>{payload.title}</h2>
            <p>{payload.body}</p>
            {f'<p><a href="{payload.url}">詳細を見る</a></p>' if payload.url else ''}
          </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        # SMTP送信
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
```

### 環境変数設定

```bash
# .env.production
USE_DB_NOTIFICATION_OUTBOX=true
ENABLE_EMAIL_NOTIFICATION=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@sanbou-app.com
SMTP_PASSWORD=<SET_IN_SECRETS>
```

### DI設定更新

```python
# app/config/di_providers.py
def get_notification_sender_port() -> NotificationSenderPort:
    enable_email = os.getenv("ENABLE_EMAIL_NOTIFICATION", "false").lower() == "true"

    if enable_email:
        return EmailNotificationSenderAdapter(
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USERNAME"),
            password=os.getenv("SMTP_PASSWORD"),
        )
    else:
        # Noop adapter (development/test)
        global _notification_sender_adapter
        if _notification_sender_adapter is None:
            _notification_sender_adapter = NoopNotificationSenderAdapter()
        return _notification_sender_adapter
```

---

## LINE通知

### 現状（Phase 2完了）

- **Outbox**: ✅ 実装済み（failure_type対応）
- **Preference**: ✅ 実装済み（opt-in制御）
- **Resolver**: ⚠️ Dummy実装（常にNone → skipped）
- **Sender**: ⚠️ Noop実装（実際に送信されない）

### アーキテクチャ

```
┌─────────────────────────────────────────────────┐
│ Business Logic                                  │
│ (例: CSVアップロード完了)                       │
└─────────────────────────────────────────────────┘
                    ↓
           recipient_key="user:123"
                    ↓
┌─────────────────────────────────────────────────┐
│ EnqueueNotificationsUseCase                     │
│ - Outboxに登録                                  │
└─────────────────────────────────────────────────┘
                    ↓
           Scheduler (1分間隔)
                    ↓
┌─────────────────────────────────────────────────┐
│ DispatchPendingNotificationsUseCase             │
│ ┌─────────────────────────────────────────┐   │
│ │ 1. Preference判定                        │   │
│ │    user:123 → line_enabled?             │   │
│ │    NG → mark_skipped()                  │   │
│ └─────────────────────────────────────────┘   │
│ ┌─────────────────────────────────────────┐   │
│ │ 2. Resolver解決                          │   │
│ │    user:123 → LINE userId               │   │
│ │    None → mark_skipped()                │   │
│ └─────────────────────────────────────────┘   │
│ ┌─────────────────────────────────────────┐   │
│ │ 3. Sender送信                            │   │
│ │    LINE Messaging API呼び出し           │   │
│ │    成功 → mark_sent()                   │   │
│ │    失敗 → mark_failed(TEMP/PERM)        │   │
│ └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 失敗分類

| 失敗タイプ    | 判定条件                                      | リトライ               | 例                                              |
| ------------- | --------------------------------------------- | ---------------------- | ----------------------------------------------- |
| **TEMPORARY** | RuntimeError, TimeoutError, ConnectionError等 | ✅ あり（1→5→30→60分） | タイムアウト、ネットワークエラー、APIレート制限 |
| **PERMANENT** | ValueError, 認証エラー等                      | ❌ なし（即failed）    | 不正なrecipient_key、LINE userId無効            |

### 実装待ち: user_line_accounts テーブル

```sql
-- migrations_v2/alembic/versions/202512XX_XXX_add_user_line_accounts.py
CREATE TABLE app.user_line_accounts (
    user_id INTEGER PRIMARY KEY REFERENCES app.users(id),
    line_user_id VARCHAR(255) NOT NULL UNIQUE,
    linked_at TIMESTAMP WITH TIME ZONE NOT NULL,
    unlinked_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    CONSTRAINT valid_line_user_id CHECK (line_user_id ~ '^U[a-f0-9]{32}$')
);

CREATE INDEX idx_user_line_accounts_line_user_id
ON app.user_line_accounts(line_user_id);

COMMENT ON TABLE app.user_line_accounts IS
'ユーザーとLINEアカウントの連携情報';

COMMENT ON COLUMN app.user_line_accounts.line_user_id IS
'LINE userId（形式: U[a-f0-9]{32}）';
```

### 実装待ち: DB Recipient Resolver

```python
# app/infra/adapters/notification/db_resolver_adapter.py
class DbRecipientResolverAdapter(RecipientResolverPort):
    def __init__(self, db: Session):
        self.db = db

    def resolve(self, recipient_key: str, channel: str) -> Optional[str]:
        ref = RecipientRef.parse(recipient_key)
        if not ref:
            return None

        if ref.kind == "user" and channel == "line":
            # DB照会: user_id → line_user_id
            result = self.db.execute(
                text("""
                    SELECT line_user_id
                    FROM app.user_line_accounts
                    WHERE user_id = :user_id
                      AND unlinked_at IS NULL
                """),
                {"user_id": int(ref.key)}
            ).fetchone()

            return result[0] if result else None

        elif ref.kind == "email":
            # Email: そのまま使用
            return ref.key

        elif ref.kind == "aud":
            # 視聴者: サイト別ロジック（TODO）
            return None

        return None
```

### 実装待ち: LINE Sender

```python
# app/infra/adapters/notification/line_sender_adapter.py
import requests

class LineNotificationSenderAdapter(NotificationSenderPort):
    def __init__(self, channel_access_token: str):
        self.channel_access_token = channel_access_token
        self.api_url = "https://api.line.me/v2/bot/message/push"

    def send(self, channel: str, payload: NotificationPayload, recipient_key: str) -> None:
        if channel != "line":
            raise ValueError(f"Unsupported channel: {channel}")

        # LINE userId検証
        if not recipient_key.startswith("U") or len(recipient_key) != 33:
            raise ValueError(f"Invalid LINE userId: {recipient_key}")

        # Flex Message構築（シンプル版）
        message = {
            "to": recipient_key,
            "messages": [
                {
                    "type": "text",
                    "text": f"{payload.title}\n\n{payload.body}"
                }
            ]
        }

        # URLがある場合は追加
        if payload.url:
            message["messages"].append({
                "type": "text",
                "text": f"詳細: {payload.url}"
            })

        # LINE Messaging API呼び出し
        response = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.channel_access_token}",
                "Content-Type": "application/json"
            },
            json=message,
            timeout=10
        )

        if response.status_code == 400:
            # Bad Request → PERMANENT
            raise ValueError(f"LINE API error: {response.text}")
        elif response.status_code == 429:
            # Rate limit → TEMPORARY
            raise RuntimeError(f"LINE API rate limit: {response.text}")
        elif response.status_code >= 500:
            # Server error → TEMPORARY
            raise RuntimeError(f"LINE API server error: {response.text}")

        response.raise_for_status()
```

### 環境変数設定

```bash
# .env.production
USE_DB_NOTIFICATION_OUTBOX=true
USE_DB_RECIPIENT_RESOLVER=true
ENABLE_LINE_NOTIFICATION=true
LINE_CHANNEL_ACCESS_TOKEN=<SET_IN_SECRETS>
```

### DI設定更新

```python
# app/config/di_providers.py
def get_recipient_resolver_port(db: Session = Depends(get_db)) -> RecipientResolverPort:
    use_db = os.getenv("USE_DB_RECIPIENT_RESOLVER", "false").lower() == "true"

    if use_db:
        return DbRecipientResolverAdapter(db)
    else:
        # Dummy adapter (development/test)
        global _recipient_resolver_adapter
        if _recipient_resolver_adapter is None:
            _recipient_resolver_adapter = DummyRecipientResolverAdapter()
        return _recipient_resolver_adapter

def get_notification_sender_port() -> NotificationSenderPort:
    enable_line = os.getenv("ENABLE_LINE_NOTIFICATION", "false").lower() == "true"
    enable_email = os.getenv("ENABLE_EMAIL_NOTIFICATION", "false").lower() == "true"

    # Multi-channel sender（将来実装）
    senders = []
    if enable_email:
        senders.append(EmailNotificationSenderAdapter(...))
    if enable_line:
        senders.append(LineNotificationSenderAdapter(...))

    if senders:
        return MultiChannelNotificationSenderAdapter(senders)
    else:
        # Noop adapter (development/test)
        global _notification_sender_adapter
        if _notification_sender_adapter is None:
            _notification_sender_adapter = NoopNotificationSenderAdapter()
        return _notification_sender_adapter
```

---

## 開発者ガイド

### 通知の送信方法

```python
from app.core.usecases.notification.enqueue_notifications_uc import (
    EnqueueNotificationRequest,
    EnqueueNotificationsUseCase
)

# DIコンテナから取得
enqueue_uc = get_enqueue_notifications_usecase()

# 通知リクエスト作成
requests = [
    EnqueueNotificationRequest(
        channel="email",
        title="CSVアップロード完了",
        body="受入データ 2025年12月分のアップロードが完了しました。",
        recipient_key="email:user@example.com",
        url="https://app.example.com/dataset/import",
        scheduled_at=None,  # 即座に送信
    ),
    EnqueueNotificationRequest(
        channel="line",
        title="データ処理完了",
        body="予測計算が完了しました。",
        recipient_key="user:123",  # user_id → LINE userIdに解決される
        url="https://app.example.com/dashboard",
    ),
]

# Outboxに登録
enqueue_uc.execute(requests=requests, now=datetime.now(timezone.utc))
```

### テストの書き方

```python
from app.infra.adapters.notification.in_memory_outbox_adapter import InMemoryNotificationOutboxAdapter
from app.infra.adapters.notification.in_memory_preference_adapter import InMemoryNotificationPreferenceAdapter
from app.infra.adapters.notification.dummy_resolver_adapter import DummyRecipientResolverAdapter

def test_notification_with_preference():
    """Preference無効化のテスト"""
    outbox = InMemoryNotificationOutboxAdapter()
    preference = InMemoryNotificationPreferenceAdapter()
    resolver = DummyRecipientResolverAdapter()
    sender = NoopNotificationSenderAdapter()

    # user:2 は LINE disabled（test data）
    item = NotificationOutboxItem.create_pending(
        channel="line",
        payload=NotificationPayload(title="Test", body="Body"),
        recipient_key="user:2",
        now=datetime.now(timezone.utc),
    )
    outbox.enqueue([item])

    # Dispatch
    dispatch_uc = DispatchPendingNotificationsUseCase(
        outbox=outbox,
        sender=sender,
        preference=preference,
        resolver=resolver,
    )
    sent_count = dispatch_uc.execute(now=datetime.now(timezone.utc))

    # 検証
    assert sent_count == 0
    assert outbox._items[item.id].status == NotificationStatus.SKIPPED
```

### ローカル開発環境

```bash
# docker-compose.dev.yml
services:
  core_api:
    environment:
      # DB永続化を使用
      USE_DB_NOTIFICATION_OUTBOX: "true"

      # スケジューラー有効化
      ENABLE_NOTIFICATION_SCHEDULER: "true"
      NOTIFICATION_DISPATCH_INTERVAL_MINUTES: "1"

      # Noop sender使用（実送信しない）
      ENABLE_EMAIL_NOTIFICATION: "false"
      ENABLE_LINE_NOTIFICATION: "false"

      # Dummy resolver使用
      USE_DB_RECIPIENT_RESOLVER: "false"
```

---

## 運用ガイド

### 監視ポイント

#### 1. Outbox滞留監視

```sql
-- Pending状態で1時間以上滞留している通知
SELECT
    id,
    channel,
    recipient_key,
    title,
    retry_count,
    last_error,
    created_at
FROM app.notification_outbox
WHERE status = 'pending'
  AND created_at < NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

#### 2. 失敗率監視

```sql
-- 直近1時間の失敗率
SELECT
    channel,
    COUNT(*) FILTER (WHERE status = 'sent') as sent_count,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
    COUNT(*) FILTER (WHERE status = 'skipped') as skipped_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'failed') /
        NULLIF(COUNT(*) FILTER (WHERE status IN ('sent', 'failed')), 0),
        2
    ) as failure_rate_pct
FROM app.notification_outbox
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY channel;
```

#### 3. リトライ回数分布

```sql
-- リトライ回数別の件数
SELECT
    retry_count,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (sent_at - created_at))) as avg_delay_seconds
FROM app.notification_outbox
WHERE status = 'sent'
  AND retry_count > 0
GROUP BY retry_count
ORDER BY retry_count;
```

### アラート設定

| メトリクス           | 閾値              | アクション             |
| -------------------- | ----------------- | ---------------------- |
| Pending滞留1時間以上 | 10件以上          | Slack通知 + 調査       |
| 失敗率               | 10%以上           | Slack通知 + 調査       |
| PERMANENT失敗        | 5件/時間以上      | Slack通知 + コード調査 |
| Scheduler停止        | 5分間dispatch無し | Slack通知 + 再起動     |

### データ保持期間

```sql
-- 7日以上前の sent/skipped/failed 通知を削除
DELETE FROM app.notification_outbox
WHERE status IN ('sent', 'skipped', 'failed')
  AND created_at < NOW() - INTERVAL '7 days';
```

**推奨**: 毎日深夜に実行（cron or APScheduler）

---

## トラブルシューティング

### 問題1: 通知が送信されない

#### 症状

- Outboxに登録されるが、status=pending のまま

#### 確認手順

1. **Schedulerが動作しているか**

   ```bash
   # ログ確認
   docker compose -p local_dev logs core_api | grep "Dispatching pending notifications"
   ```

2. **環境変数が正しいか**

   ```bash
   docker compose -p local_dev exec core_api env | grep NOTIFICATION
   ```

3. **Outbox内のnext_retry_atを確認**
   ```sql
   SELECT id, next_retry_at, NOW()
   FROM app.notification_outbox
   WHERE status = 'pending';
   ```

#### 解決策

- Scheduler未起動 → `ENABLE_NOTIFICATION_SCHEDULER=true`
- next_retry_at が未来 → リトライ待ち（正常）
- DB接続エラー → DBコンテナ確認

---

### 問題2: LINE通知がskippedになる

#### 症状

- status='skipped', last_error='Recipient not resolved for channel=line'

#### 確認手順

1. **Resolverの実装を確認**

   ```python
   # DummyResolverAdapter → 常にNone返す（開発環境）
   # DbResolverAdapter → DB照会（本番環境）
   ```

2. **user_line_accounts テーブルを確認**

   ```sql
   SELECT * FROM app.user_line_accounts
   WHERE user_id = 123 AND unlinked_at IS NULL;
   ```

3. **recipient_keyの形式を確認**
   ```python
   # 正: "user:123"
   # 誤: "123", "user_123", "U1234abcd..."
   ```

#### 解決策

- Dummy Resolver使用中 → 開発環境では正常（実LINE送信は本番のみ）
- LINE未連携 → ユーザーにLINE連携を促す
- recipient_key形式エラー → コード修正

---

### 問題3: PERMANENT失敗が多発

#### 症状

- status='failed', failure_type='PERMANENT', retry_count=0

#### 確認手順

1. **last_errorを確認**

   ```sql
   SELECT id, recipient_key, last_error
   FROM app.notification_outbox
   WHERE failure_type = 'PERMANENT'
   ORDER BY created_at DESC LIMIT 10;
   ```

2. **共通パターンを特定**
   - ValueError → recipient_key形式エラー、不正なデータ
   - 認証エラー → API token無効

#### 解決策

- recipient_key形式エラー → ビジネスロジック修正
- API token無効 → Secrets更新

---

### 問題4: スケジューラーが重複実行される

#### 症状

- ログに "Dispatching..." が重複して出力される
- 同じ通知が複数回送信される

#### 確認手順

1. **uvicorn --reload使用確認**

   ```bash
   # 開発環境でreload有効？
   ps aux | grep uvicorn
   ```

2. **core_apiコンテナ数確認**
   ```bash
   docker compose -p local_dev ps | grep core_api
   ```

#### 解決策

- uvicorn --reload使用中 → 正常（開発環境の制限）
- 本番環境で重複 → core_apiインスタンス数確認、Schedulerを1インスタンスのみに制限

---

## 参考リンク

- [完了報告: LINE通知基盤の仕込み](./notification_line_foundation_COMPLETED.md)
- [優先実装タスク](./NOTIFICATION_PRIORITY_TASKS.md)
- [Alembic Migration: 20251224_005](../../app/backend/core_api/migrations_v2/alembic/versions/20251224_005_create_notification_outbox_table.py)
- [Alembic Migration: 20251225_001](../../app/backend/core_api/migrations_v2/alembic/versions/20251225_001_add_notification_outbox_failure_type.py)
- [LINE Messaging API Docs](https://developers.line.biz/ja/docs/messaging-api/)
- [Python smtplib Docs](https://docs.python.org/3/library/smtplib.html)
