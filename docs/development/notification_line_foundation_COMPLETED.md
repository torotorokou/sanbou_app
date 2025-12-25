# LINE通知基盤の仕込み - 完了報告

## 概要

LINE通知を後から安全に追加できるようにする最低限の仕込みを完了しました。
**実際のLINE APIコール、外部API連携、DB migrationは一切含まれていません**（InMemory/No-op実装のみ）。

## 実装内容

### 1. recipient_key 統一方針

すべての通知は以下の形式の `recipient_key` で管理されます：

- **`user:{id}`** - ユーザーID（例: `user:123`）
- **`email:{address}`** - メールアドレス（例: `email:admin@example.com`）
- **`aud:{site}:{code}`** - 視聴者コード（例: `aud:tokyo:A001`）

この方針により、将来的にLINE連携時に `user:123` → LINE userId への解決が可能になります。

実装箇所:
- [app/core/domain/notification.py](app/core/domain/notification.py) - RecipientRef dataclass

### 2. 失敗分類（TEMPORARY / PERMANENT）

送信失敗を2種類に分類し、リトライ可否を明確にしました：

#### TEMPORARY（一時的失敗）
- タイムアウト、ネットワークエラー、APIレート制限など
- **リトライ対象**: 1分 → 5分 → 30分 → 60分の指数バックオフ
- status = `pending` のまま、retry_count++ & next_retry_at 更新

#### PERMANENT（恒久的失敗）
- バリデーションエラー（ValueError）、認証失敗、不正な recipient_key など
- **リトライしない**: 即座に status = `failed` に遷移
- 再送するには手動での介入が必要

実装箇所:
- [app/core/domain/notification.py](app/core/domain/notification.py) - FailureType enum
- [app/infra/adapters/notification/in_memory_outbox_adapter.py](app/infra/adapters/notification/in_memory_outbox_adapter.py) - mark_failed ロジック
- [app/core/usecases/notification/dispatch_pending_notifications_uc.py](app/core/usecases/notification/dispatch_pending_notifications_uc.py) - 例外ハンドリング

### 3. Notification Preference（通知許可の拡張点）

ユーザー別・チャネル別の通知許可設定を導入しました（opt-in方式）：

```python
@dataclass
class NotificationPreference:
    recipient_key: str  # user:123 など
    email_enabled: bool = True
    line_enabled: bool = True
```

- **Preference未設定 = すべて有効**（デフォルト許可）
- Preferenceで無効化されたチャネルは status = `skipped` に遷移

テストデータ（InMemory実装）:
- `user:1` - LINE: ✅, Email: ✅
- `user:2` - LINE: ❌, Email: ✅（LINEはskipped）
- `user:3` - LINE: ✅, Email: ❌（Emailはskipped）

実装箇所:
- [app/core/domain/notification.py](app/core/domain/notification.py) - NotificationPreference dataclass
- [app/core/ports/notification_port.py](app/core/ports/notification_port.py) - NotificationPreferencePort
- [app/infra/adapters/notification/in_memory_preference_adapter.py](app/infra/adapters/notification/in_memory_preference_adapter.py)

### 4. Recipient Resolver（チャネル固有ID解決の拡張点）

`recipient_key` をチャネル固有のIDに解決する仕組みを導入：

```python
class RecipientResolverPort(ABC):
    def resolve(self, recipient_key: str, channel: str) -> Optional[str]:
        """recipient_key をチャネル固有IDに変換（解決不可なら None）"""
```

現在の動作（Dummy実装）:
- **email**: `email:addr@example.com` → `addr@example.com`（そのまま）
- **line**: 常に `None`（未連携扱い）→ status = `skipped`

LINE連携後の理想的な動作:
- `user:123` → DB照会 → LINE userId `U1234abcd...`（実LINEユーザーID）

実装箇所:
- [app/core/ports/notification_port.py](app/core/ports/notification_port.py) - RecipientResolverPort
- [app/infra/adapters/notification/dummy_resolver_adapter.py](app/infra/adapters/notification/dummy_resolver_adapter.py)

### 5. mark_skipped ステータス

明示的に「送信しない」ことを記録する新ステータス：

```python
def mark_skipped(self, id: UUID, reason: str, now: datetime) -> None:
    """通知をスキップ（preference無効化、resolver解決失敗など）"""
```

skipped 条件:
1. Preference でチャネルが無効化されている
2. Resolver が None を返す（LINE未連携など）

実装箇所:
- [app/core/ports/notification_port.py](app/core/ports/notification_port.py) - NotificationOutboxPort.mark_skipped
- [app/infra/adapters/notification/in_memory_outbox_adapter.py](app/infra/adapters/notification/in_memory_outbox_adapter.py)

## 処理フロー（DispatchPendingNotificationsUseCase）

```
1. outbox.list_pending() で送信対象を取得
2. 各 item について:
   a) recipient_key が user:* の場合、Preference をチェック
      → 無効化されていれば mark_skipped() して次へ
   b) resolver.resolve(recipient_key, channel) で解決
      → None なら mark_skipped() して次へ（LINE未連携など）
   c) sender.send(channel, payload, resolved_to) で送信
      → 成功: mark_sent()
      → ValueError: mark_failed(PERMANENT)
      → その他例外: mark_failed(TEMPORARY)
```

## テストカバレッジ

全16ケース成功（既存13 + 新規3）:

### 新規追加テスト（LINE通知基盤）
1. **test_preference_disabled_skips_notification**
   - `user:2` にLINE通知 → `line_enabled=false` → skipped
2. **test_resolver_returns_none_skips_notification**
   - `user:1` にLINE通知 → resolver returns None → skipped
3. **test_sender_failure_temporary_vs_permanent**
   - ValueError → PERMANENT（failed、リトライなし）
   - RuntimeError → TEMPORARY（pending、リトライあり）

テスト実行結果:
```bash
$ pytest tests/test_notification_infrastructure.py -v
16 passed in 0.07s
```

## 次フェーズの要件（LINE本格対応）

以下を追加すれば、実際のLINE通知が動作します：

### 1. DB設計（user_line_accounts テーブル）

```sql
CREATE TABLE user_line_accounts (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    line_user_id VARCHAR(255) NOT NULL UNIQUE,
    linked_at TIMESTAMP NOT NULL,
    unlinked_at TIMESTAMP,
    CONSTRAINT valid_line_user_id CHECK (line_user_id ~ '^U[a-f0-9]{32}$')
);
```

### 2. DbRecipientResolverAdapter

```python
class DbRecipientResolverAdapter(RecipientResolverPort):
    def resolve(self, recipient_key: str, channel: str) -> Optional[str]:
        ref = RecipientRef.parse(recipient_key)
        if ref.kind == "user" and channel == "line":
            # DB照会: user_id → line_user_id
            result = self._db.execute(
                text("SELECT line_user_id FROM user_line_accounts WHERE user_id = :id AND unlinked_at IS NULL"),
                {"id": int(ref.key)}
            ).fetchone()
            return result[0] if result else None
        elif ref.kind == "email":
            return ref.key
        # ... その他のチャネル
```

### 3. LineNotificationSenderAdapter

```python
class LineNotificationSenderAdapter(NotificationSenderPort):
    def send(self, channel: str, payload: NotificationPayload, recipient_key: str) -> None:
        if channel != "line":
            raise ValueError(f"Unsupported channel: {channel}")
        
        # LINE Messaging API呼び出し
        response = requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers={
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "to": recipient_key,  # LINE userId
                "messages": [
                    {
                        "type": "text",
                        "text": f"{payload.title}\n\n{payload.body}"
                    }
                ]
            }
        )
        response.raise_for_status()
```

### 4. DI設定更新

```python
def get_recipient_resolver_port(db: Session = Depends(get_db)) -> RecipientResolverPort:
    use_db = os.getenv("USE_DB_RECIPIENT_RESOLVER", "false").lower() == "true"
    return DbRecipientResolverAdapter(db) if use_db else DummyRecipientResolverAdapter()

def get_notification_sender_port() -> NotificationSenderPort:
    enable_line = os.getenv("ENABLE_LINE_NOTIFICATION", "false").lower() == "true"
    return LineNotificationSenderAdapter() if enable_line else NoopNotificationSenderAdapter()
```

### 5. 環境変数

```bash
# 本番環境
USE_DB_RECIPIENT_RESOLVER=true
ENABLE_LINE_NOTIFICATION=true
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token

# 開発環境（現状維持）
USE_DB_RECIPIENT_RESOLVER=false  # Dummy実装
ENABLE_LINE_NOTIFICATION=false   # Noop実装
```

## コミット履歴

```
b5967c2c feat(notification): Update DB adapter for failure_type support
9134e5be feat(db): Add failure_type column to notification_outbox
e7e4adb4 docs: LINE通知基盤の仕込み完了報告
c7224bb0 feat: Step6 - テストケース追加(preference/resolver/failure分類)
0f66830a feat: Step4&5 - UseCase+DI統合(preference→resolver→dispatch)
18dd1c57 feat: Step3 - InMemory adapter実装(Preference/Resolver/Outbox拡張)
f29e4f26 feat: Step2 - ports拡張(PreferencePort/ResolverPort/mark_skipped)
0ca01e1b feat: Step1 - domain層追加(FailureType/RecipientRef/Preference)
```

## DBマイグレーション

### 適用済みマイグレーション

```bash
$ make al-cur-env ENV=local_dev
20251225_001 (head)
```

### マイグレーション内容

**20251225_001_add_notification_outbox_failure_type.py**
- `app.notification_outbox` テーブルに `failure_type VARCHAR(20)` カラムを追加
- デフォルト値: NULL（pending/sent/skipped 時）
- 既存の failed レコードには 'TEMPORARY' を自動設定（互換性維持）

### テーブル構造

```sql
                              Table "app.notification_outbox"
    Column     |           Type           | Nullable |         Default         
---------------+--------------------------+----------+-------------------------
 id            | uuid                     | not null | 
 channel       | character varying(50)    | not null | 
 status        | character varying(50)    | not null | 
 recipient_key | character varying(255)   | not null | 
 title         | character varying(500)   | not null | 
 body          | text                     | not null | 
 url           | character varying(1000)  |          | NULL
 meta          | jsonb                    |          | 
 scheduled_at  | timestamp with time zone |          | 
 created_at    | timestamp with time zone | not null | 
 sent_at       | timestamp with time zone |          | 
 retry_count   | integer                  | not null | 0
 next_retry_at | timestamp with time zone |          | 
 last_error    | text                     |          | 
 failure_type  | character varying(20)    |          | NULL  ← NEW!
```

## まとめ

- ✅ recipient_key 統一方針確立（`user:` / `email:` / `aud:`）
- ✅ 失敗分類（TEMP/PERM）とskipped運用
- ✅ Preference（opt-in通知許可）拡張点
- ✅ Resolver（チャネルID解決）拡張点
- ✅ テスト完備（16ケース成功）
- ✅ Clean Architecture + DDD 厳守
- ✅ 外部API・DB migration一切なし（InMemory/No-op のみ）

**次フェーズで上記5項目を実装すれば、実LINE通知が動作します。**
