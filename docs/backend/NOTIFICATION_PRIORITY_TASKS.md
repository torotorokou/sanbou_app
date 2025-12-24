# 通知基盤 - 優先実装タスク

**作成日**: 2024年12月24日  
**前提**: 通知基盤の基礎実装完了（InMemory/Noop）

---

## 📋 現状

### ✅ Phase 1完了（2024-12-24）
- Domain層: NotificationChannel, NotificationStatus, NotificationPayload, NotificationOutboxItem
- Ports: NotificationOutboxPort, NotificationSenderPort
- UseCases: EnqueueNotificationsUseCase, DispatchPendingNotificationsUseCase
- Adapters: 
  - InMemoryNotificationOutboxAdapter（開発/テスト用）
  - **DbNotificationOutboxAdapter（本番用、PostgreSQL）** ← NEW
  - NoopNotificationSenderAdapter（Phase 2で実Email送信に置き換え予定）
- DI: config/di_providers.py（環境変数による切替）
- Tests: 12件のユニットテスト + DB統合テスト
- **DB永続化**: notification_outboxテーブル（UUID PK、JSONB meta、retry logic）← NEW
- **定期実行**: APScheduler統合（1分間隔、FastAPI lifecycle管理）← NEW

### ⚠️ 制限事項（現状）
- 通知送信がNoop（実際に送信されない）← Phase 2で解決予定
- ビジネスロジックからの呼び出しなし ← Phase 2で統合予定
- 開発環境でuvicorn --reloadによるscheduler干渉（本番環境では問題なし）

---

## 🎯 優先実装タスク

### ✅ Phase 1: DB永続化 + 定期実行（完了）
**完了日**: 2024年12月24日  
**所要期間**: 2日

#### 実装内容
1. **DB永続化**
   - ✅ Alembic migration: `20251224_005_create_notification_outbox_table.py`
   - ✅ NotificationOutboxORM model（UUID PK、JSONB meta、retry logic）
   - ✅ DbNotificationOutboxAdapter実装（enqueue, list_pending, mark_sent, mark_failed）
   - ✅ DI設定: 環境変数`USE_DB_NOTIFICATION_OUTBOX`による切替
   - ✅ Indexes: status, next_retry_at（conditional）, created_at DESC

2. **定期実行（APScheduler）**
   - ✅ APScheduler==3.10.4 追加
   - ✅ notification_dispatcher.py: BackgroundScheduler統合
   - ✅ FastAPI startup/shutdown events: スケジューラーライフサイクル管理
   - ✅ 環境変数: `ENABLE_NOTIFICATION_SCHEDULER=true`、`NOTIFICATION_DISPATCH_INTERVAL_MINUTES=1`
   - ✅ エラーハンドリング、ログ出力

#### テスト結果
- ✅ 10件の通知を正常にenqueue → dispatch → sent
- ✅ Retry logic動作確認（exponential backoff: 1min → 5min → 30min → 60min）
- ✅ 手動dispatch実行: 正常動作
- ⚠️ 開発環境（uvicorn --reload）: scheduler "missed run" warnings（本番環境では問題なし）

#### 実装ファイル
- `migrations_v2/alembic/versions/20251224_005_create_notification_outbox_table.py`
- `app/infra/db/orm_models.py`: NotificationOutboxORM追加
- `app/infra/adapters/notification/db_outbox_adapter.py`: DB実装
- `app/scheduler/notification_dispatcher.py`: スケジューラー統合
- `app/app.py`: startup/shutdown events
- `app/config/di_providers.py`: 環境変数ベースDI
- `requirements.txt`: APScheduler追加

#### ドキュメント
- `docs/database/DB_USER_MIGRATION_MYUSER_TO_SANBOU_APP_DEV.md`: DB権限問題解決記録

---

### 📌 Phase 1の技術的知見

#### DB Ownership問題の解決
**問題**: PostgreSQLで`myuser`（superuser）がschema ownerになっており、`sanbou_app_dev`（application user）との権限衝突が発生

**解決策**:
```sql
ALTER SCHEMA app OWNER TO sanbou_app_dev;
ALTER TABLE app.notification_outbox OWNER TO sanbou_app_dev;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app TO sanbou_app_dev;
```

**教訓**: 
- 常に環境変数の`POSTGRES_USER`を使用
- `myuser`をハードコードしない
- スキーマ/テーブル作成時にownerを明示

#### APScheduler + uvicorn --reload
**問題**: 開発環境でschedulerが"missed run"警告を出す

**原因**: uvicorn --reloadがコード変更検知で頻繁に再起動

**解決策**:
- 開発: 警告を許容、または手動実行で検証
- 本番: `--reload`なしで起動、schedulerは正常動作

---

---

### 🔄 Phase 2: 実Email送信 + ビジネスロジック統合（次のフェーズ）
**優先度**: 🟡 MEDIUM  
**予定期間**: 2-3日

#### 2-1. 実Email送信実装
**実装内容**:
- EmailNotificationSenderAdapterの実装（SendGrid or AWS SES推奨）
- 環境変数で送信設定（API key / SMTP credentials）
- エラーハンドリング、送信失敗時のリトライ
- DI設定: NoopNotificationSenderAdapter → EmailNotificationSenderAdapter
- HTMLテンプレート対応（オプション）

**SendGrid実装例**:
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

#### 2-2. ビジネスロジック統合
**実装内容**:
- 既存UseCaseから通知を発行
- 統合ポイント例:
  - 受注確定時 → メール通知
  - 在庫アラート → LINE通知
  - レポート生成完了 → メール通知
  - エラー発生時 → 管理者通知

**実装ファイル**:
- 各ビジネスUseCase（EnqueueNotificationsUseCaseを呼び出し）

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

## 📊 実装進捗状況

### ✅ Phase 1: 本番運用準備（完了 - 2024-12-24）
1. ✅ **DB永続化** (完了)
   - Alembic migration、ORM model、DbNotificationOutboxAdapter
   - UUID PK、JSONB meta、retry logic with exponential backoff
   - DI configuration with environment variable switching
   
2. ✅ **定期実行（APScheduler）** (完了)
   - BackgroundScheduler統合、FastAPI lifecycle管理
   - 1分間隔での自動dispatch
   - エラーハンドリング、構造化ログ出力

**成果**: 最小限の本番運用が可能な状態に到達 ✅

---

### 🔄 Phase 2: 実用化（次のステップ）
3. ⏳ **実Email送信** (未実装)
   - EmailNotificationSenderAdapter（SendGrid or AWS SES）
   - API key管理、エラーハンドリング
   - HTMLテンプレート対応（オプション）
   
4. ⏳ **ビジネスロジック統合** (未実装)
   - 既存UseCaseからの通知発行
   - 受注確定、レポート生成、エラー通知等

**目標**: 実際にユーザーに通知が届く状態にする

---

### 🌟 Phase 3: 機能拡張（将来的）
- LINE通知実装
- Webhook実装
- Push通知実装
- 通知テンプレート管理UI
- 送信履歴の可視化・検索
- 管理画面（通知送信、ステータス確認）

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
