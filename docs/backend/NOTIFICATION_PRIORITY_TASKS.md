# 通知基盤 - 優先実装タスク

**作成日**: 2024年12月24日  
**前提**: 通知基盤の基礎実装完了（InMemory/Noop）

---

## 📋 現状

### ✅ 完了済み
- Domain層: NotificationChannel, NotificationStatus, NotificationPayload, NotificationOutboxItem
- Ports: NotificationOutboxPort, NotificationSenderPort
- UseCases: EnqueueNotificationsUseCase, DispatchPendingNotificationsUseCase
- Adapters: InMemoryNotificationOutboxAdapter, NoopNotificationSenderAdapter
- DI: config/di_providers.py
- Tests: 12件のユニットテスト

### ⚠️ 制限事項（現状）
- Outboxがプロセス内メモリ（再起動で消失）
- 通知送信がNoop（実際に送信されない）
- 定期実行の仕組みなし（手動実行のみ）
- ビジネスロジックからの呼び出しなし

---

## 🎯 優先実装タスク

### 1. 🔴 DB永続化（最優先）
**優先度**: 🔴 HIGH  
**理由**: InMemoryでは本番運用不可、プロセス再起動で通知が消失  
**期間**: 1-2日

**実装内容**:
- Alembic migration でOutboxテーブル作成
- DbNotificationOutboxAdapter 実装（SQLAlchemy ORM）
- DI設定の切り替え（InMemory → DB）
- 既存テストの実行確認

**テーブル設計**:
```sql
CREATE TABLE notification_outbox (
    id UUID PRIMARY KEY,
    channel VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    recipient_key VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    url VARCHAR(1000),
    meta JSONB,
    scheduled_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP,
    last_error TEXT
);

CREATE INDEX idx_notification_outbox_status ON notification_outbox(status);
CREATE INDEX idx_notification_outbox_next_retry ON notification_outbox(next_retry_at);
```

**実装ファイル**:
- `app/backend/core_api/migrations_v2/versions/YYYYMMDD_HHMMSS_create_notification_outbox.py`
- `app/backend/core_api/app/infra/adapters/notification/db_outbox_adapter.py`
- `app/backend/core_api/app/config/di_providers.py` (修正)

---

### 2. 🟡 定期実行の仕組み
**優先度**: 🟡 HIGH  
**理由**: Dispatchを定期的に実行しないと通知が送られない  
**期間**: 0.5-1日

**選択肢**:
1. **APScheduler** (推奨: 既存コードベースに統合しやすい)
2. Celery Beat (重量級、既にCeleryがあれば)
3. Cron + CLI コマンド (シンプル)

**実装内容（APScheduler案）**:
- FastAPI起動時にスケジューラー開始
- 1分ごとにDispatchPendingNotificationsUseCaseを実行
- エラーハンドリングとログ出力
- ENV=production のみ有効化

**実装ファイル**:
- `app/backend/core_api/app/scheduler/notification_dispatcher.py`
- `app/backend/core_api/app/app.py` (スケジューラー起動)
- `requirements.txt` (APScheduler追加)

**実装例**:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

scheduler = BackgroundScheduler()

def dispatch_notifications():
    """定期的に通知を送信"""
    try:
        uc = get_dispatch_pending_notifications_usecase()
        sent_count = uc.execute(now=datetime.now(), limit=100)
        logger.info(f"Dispatched {sent_count} notifications")
    except Exception as e:
        logger.error(f"Failed to dispatch notifications: {e}")

# 1分ごとに実行
scheduler.add_job(dispatch_notifications, 'interval', minutes=1)
scheduler.start()
```

---

### 3. 🟢 実送信実装（Email）
**優先度**: 🟢 MEDIUM  
**理由**: 実際に通知を届けるため（ただし送信先実装は段階的でOK）  
**期間**: 1-2日

**実装順序**:
1. Emailから開始（最も汎用的）
2. LINE（必要に応じて）
3. その他（Webhook/Push等）

**Email実装内容**:
- SMTP / SendGrid / AWS SES のいずれかを選択
- EmailNotificationSenderAdapter 実装
- 環境変数で送信設定（SMTP_HOST, SMTP_PORT等）
- HTMLテンプレート対応（オプション）

**実装ファイル**:
- `app/backend/core_api/app/infra/adapters/notification/email_sender_adapter.py`
- `app/backend/core_api/app/config/di_providers.py` (Senderの切り替え)
- `.env.example` (SMTP設定追加)

**SendGrid例**:
```python
import sendgrid
from sendgrid.helpers.mail import Mail

class SendGridNotificationSenderAdapter(NotificationSenderPort):
    def __init__(self, api_key: str, from_email: str):
        self._client = sendgrid.SendGridAPIClient(api_key)
        self._from_email = from_email
    
    def send(self, channel, payload, recipient_key):
        if channel != "email":
            raise ValueError(f"Unsupported channel: {channel}")
        
        message = Mail(
            from_email=self._from_email,
            to_emails=recipient_key,  # recipient_keyはメールアドレス
            subject=payload.title,
            plain_text_content=payload.body
        )
        
        self._client.send(message)
```

---

### 4. 🟢 ユースケース統合
**優先度**: 🟢 MEDIUM  
**理由**: 実際のビジネスロジックから通知を発行  
**期間**: 0.5-1日

**統合ポイント（例）**:
- 受注確定時 → メール通知
- 在庫アラート → LINE通知
- レポート生成完了 → メール通知
- エラー発生時 → 管理者通知

**実装例**:
```python
# UseCaseから通知を登録
class ConfirmOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        notification_uc: EnqueueNotificationsUseCase
    ):
        self._order_repo = order_repo
        self._notification_uc = notification_uc
    
    def execute(self, order_id: str):
        order = self._order_repo.get(order_id)
        order.confirm()
        self._order_repo.save(order)
        
        # 通知を登録
        now = datetime.now()
        requests = [
            EnqueueNotificationRequest(
                channel="email",
                title="受注確定のお知らせ",
                body=f"注文 {order_id} が確定しました",
                recipient_key=order.customer_email,
                url=f"https://example.com/orders/{order_id}"
            )
        ]
        self._notification_uc.execute(requests=requests, now=now)
```

---

## 📊 実装順序と優先度

### フェーズ1: 本番運用準備（必須）
1. 🔴 **DB永続化** (1-2日)
2. 🟡 **定期実行** (0.5-1日)

**判断基準**: これが完了すれば最小限の本番運用が可能

### フェーズ2: 実用化（推奨）
3. 🟢 **Email実装** (1-2日)
4. 🟢 **ユースケース統合** (0.5-1日)

**判断基準**: 実際にユーザーに通知が届く

### フェーズ3: 機能拡張（任意）
- LINE実装
- Webhook実装
- Push通知実装
- 通知テンプレート管理
- 送信履歴の可視化
- 管理画面

---

## ⚙️ 技術選定

### DB永続化
- **選択**: PostgreSQL（既存DBを活用）
- **ORM**: SQLAlchemy（既存と統一）
- **Migration**: Alembic（既存と統一）

### 定期実行
- **選択**: APScheduler（推奨）
  - 理由: 軽量、Pythonネイティブ、FastAPIと統合しやすい
  - 代替: Celery Beat（既にCeleryがある場合）

### Email送信
- **選択候補**:
  1. SendGrid（推奨: 信頼性高、無料枠あり）
  2. AWS SES（AWSユーザー向け）
  3. SMTP（シンプル、開発環境向け）

---

## 🧪 テスト戦略

### DB永続化のテスト
- トランザクションテスト（commit/rollback）
- 同時実行テスト（複数プロセス）
- パフォーマンステスト（大量通知）

### 定期実行のテスト
- スケジューラー起動/停止
- エラー時のリトライ
- ログ出力確認

### Email送信のテスト
- モック送信（テスト環境）
- 実送信（ステージング環境）
- エラーハンドリング

---

## 🔒 セキュリティ考慮事項

### 機密情報管理
- SMTP/SendGrid APIキーは環境変数化
- recipient_keyの検証（メールアドレス形式等）
- ペイロードのサニタイゼーション

### レート制限
- 送信レート制限（1分あたりN件）
- リトライ回数上限（例: 3回）
- バックオフ時間の調整

### 監視
- 送信成功率のモニタリング
- 失敗通知のアラート
- Outboxの滞留監視

---

## 📈 成功基準

### フェーズ1完了
- ✅ Outboxテーブルが作成されている
- ✅ DB永続化アダプタが動作する
- ✅ 定期実行が1分ごとに動作する
- ✅ プロセス再起動しても通知が残る

### フェーズ2完了
- ✅ Email送信が実際に動作する
- ✅ ビジネスロジックから通知を発行できる
- ✅ ユーザーに通知が届く

---

## 🎯 次のアクション

**即座に開始**: DB永続化（Outboxテーブル作成）

1. Alembic migration ファイル作成
2. DbNotificationOutboxAdapter 実装
3. テスト実行
4. DI切り替え

**推定時間**: 4-6時間（テスト含む）

---

## 📚 参考資料

- [Transactional Outbox Pattern](https://microservices.io/patterns/data/transactional-outbox.html)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [SendGrid Python SDK](https://github.com/sendgrid/sendgrid-python)
