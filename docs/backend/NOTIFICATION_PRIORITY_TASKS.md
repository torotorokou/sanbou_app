# 通知基盤 - 優先実装タスク

**作成日**: 2024年12月24日  
**最終更新**: 2025年12月25日  
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
  - NoopNotificationSenderAdapter（Phase 3で実Email/LINE送信に置き換え予定）
- DI: config/di_providers.py（環境変数による切替）
- Tests: 12件のユニットテスト + DB統合テスト
- **DB永続化**: notification_outboxテーブル（UUID PK、JSONB meta、retry logic）← NEW
- **定期実行**: APScheduler統合（1分間隔、FastAPI lifecycle管理）← NEW

### ✅ Phase 2完了（2025-12-25）

- **Domain層拡張**:
  - FailureType enum（TEMPORARY / PERMANENT）
  - RecipientRef dataclass（recipient_key解析: `user:123`, `email:addr`, `aud:site:code`）
  - NotificationPreference dataclass（opt-in制御）
- **Ports層拡張**:
  - NotificationPreferencePort（通知許可管理）
  - RecipientResolverPort（チャネル固有ID解決）
  - mark_failed(failure_type), mark_skipped(reason)
- **Adapters層拡張**:
  - InMemoryNotificationPreferenceAdapter（テスト用）
  - DummyRecipientResolverAdapter（テスト用、LINE常にNone→skipped）
  - InMemoryOutboxAdapter TEMP/PERM対応
  - DbOutboxAdapter failure_type対応
- **UseCases層拡張**:
  - DispatchPendingNotificationsUseCase: Preference判定→Resolver解決→送信→失敗分類
- **DBマイグレーション**:
  - `20251225_001_add_notification_outbox_failure_type.py`（failure_type VARCHAR(20)）
- **テスト**: 16ケース全成功（既存13 + 新規3: Preference/Resolver/失敗分類）

### ⚠️ 制限事項（現状）

- 通知送信がNoop（実際に送信されない）← **Phase 3で解決予定**
- Resolver がDummy（LINE常にNone）← **Phase 3でDB実装予定**
- ビジネスロジックからの呼び出しなし ← **Phase 3で統合予定**
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

---

### ✅ Phase 2: LINE通知基盤準備（完了）

**完了日**: 2025年12月25日  
**所要期間**: 1日

#### 実装内容

1. **Recipient Key統一方針**

   - ✅ `user:{id}` - ユーザーID（将来的にLINE userId等に解決）
   - ✅ `email:{address}` - メールアドレス直接指定
   - ✅ `aud:{site}:{code}` - 視聴者コード
   - ✅ RecipientRef dataclass（parse/as_string）

2. **失敗分類（TEMPORARY / PERMANENT）**

   - ✅ FailureType enum追加
   - ✅ TEMPORARY: タイムアウト等 → リトライ対象（1→5→30→60分）
   - ✅ PERMANENT: ValidationError等 → 即failed、リトライなし
   - ✅ DBマイグレーション: failure_type VARCHAR(20) カラム追加
   - ✅ mark_failed(failure_type) シグネチャ更新

3. **通知許可管理（Opt-in）**

   - ✅ NotificationPreference dataclass（email_enabled, line_enabled）
   - ✅ NotificationPreferencePort追加
   - ✅ InMemoryPreferenceAdapter（テスト用: user:1,2,3）
   - ✅ DispatchUseCase: Preference判定 → 無効化ならmark_skipped()

4. **Recipient解決機構**

   - ✅ RecipientResolverPort追加
   - ✅ DummyResolverAdapter（テスト用: email→そのまま、LINE→None）
   - ✅ DispatchUseCase: Resolver解決 → None ならmark_skipped()

5. **mark_skipped ステータス**
   - ✅ NotificationStatus.SKIPPED追加
   - ✅ mark_skipped(reason) 実装（Outbox/DB両対応）
   - ✅ 用途: Preference無効化、Resolver解決失敗

#### テスト結果

- ✅ 16ケース全成功
  - Preference無効化でskipped検証
  - Resolver解決失敗でskipped検証
  - ValueError→PERMANENT, RuntimeError→TEMPORARY検証

#### 実装ファイル

- `app/core/domain/notification.py`: FailureType, RecipientRef, NotificationPreference追加
- `app/core/ports/notification_port.py`: PreferencePort, ResolverPort, mark_skipped追加
- `app/infra/adapters/notification/in_memory_preference_adapter.py`: NEW
- `app/infra/adapters/notification/dummy_resolver_adapter.py`: NEW
- `app/infra/adapters/notification/db_outbox_adapter.py`: failure_type, mark_skipped対応
- `app/core/usecases/notification/dispatch_pending_notifications_uc.py`: 拡張
- `app/config/di_providers.py`: Preference/Resolver DI追加
- `migrations_v2/alembic/versions/20251225_001_add_notification_outbox_failure_type.py`: NEW
- `tests/test_notification_infrastructure.py`: 3ケース追加

#### ドキュメント

- `docs/development/notification_line_foundation_COMPLETED.md`: 完了報告
- `docs/backend/NOTIFICATION_SYSTEM_GUIDE.md`: 完全ガイド（NEW）
- `docs/backend/NOTIFICATION_QUICKREF.md`: クイックリファレンス（NEW）

---

### 🔄 Phase 3: 実Email/LINE送信 + ビジネスロジック統合（次のフェーズ）

**優先度**: 🟡 MEDIUM  
**予定期間**: 3-5日

# UseCaseから通知を登録

class ConfirmOrderUseCase:
def **init**(
self,
order_repo: OrderRepository,
notification_uc: EnqueueNotificationsUseCase
):
self.\_order_repo = order_repo
self.\_notification_uc = notification_uc

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
```
