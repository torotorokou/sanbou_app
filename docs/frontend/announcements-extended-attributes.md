# お知らせ機能 - 拡張属性実装ドキュメント

## 概要

お知らせ機能に以下の拡張属性を追加し、将来のバックエンド連携（メール/LINE送信）に備えた設計を実装しました。

**実装日**: 2025-12-23  
**ブランチ**: `feature/announcements-extended-attributes`  
**対象**: フロントエンドのみ（DBは触らず、seedデータで動作確認）

---

## 追加した属性

### 1. 重要度（severity）

既存の `'info' | 'warn' | 'critical'` を維持。

### 2. タグ（tags）

```typescript
tags?: string[];  // 任意、最大2〜3個表示推奨
```

- 一覧カードにバッジ表示（最大3個）
- 例: `['メンテナンス', 'システム']`

### 3. 公開期限（publishFrom / publishTo）

```typescript
publishFrom: string; // ISO8601 形式（既存）
publishTo: string | null; // ISO8601 形式、null=無期限（既存）
```

- `isAnnouncementActive()` 関数で期限判定
- 期限切れは一覧・トップに表示されない

### 4. 対象オーディエンス（audience）

```typescript
type Audience = "all" | "internal" | "site:narita" | "site:shinkiba";

audience: Audience;
```

- `isVisibleForAudience()` 関数で対象判定
- 現在は `CURRENT_AUDIENCE = 'site:narita'` で固定（TODO: 将来ユーザープロファイルから取得）
- `'all'` と `'internal'` は全員に表示
- `'site:narita'` / `'site:shinkiba'` は拠点が一致する場合のみ表示

### 5. 添付ファイル（attachments）

```typescript
interface Attachment {
  label: string;       // 表示ラベル
  url: string;         // リンクURL
  kind?: 'pdf' | 'link';  // 種別（任意）
}

attachments?: Attachment[];
```

- 一覧カードに「添付」バッジ表示
- 詳細画面に添付ファイルセクション表示
- リンクは `target="_blank" rel="noopener noreferrer"`

### 6. 通知設定（notification）

```typescript
type NotificationChannel = 'inApp' | 'email' | 'line';

interface NotificationPlan {
  channels: NotificationChannel[];  // 配信チャネル
  sendOnPublish: boolean;           // 公開時に送信するか
  scheduledAt?: string | null;      // スケジュール配信日時
  templateHint?: string | null;     // テンプレート指定（将来用）
}

notification?: NotificationPlan;
```

- **今回は表示のみ（送信機能は実装していません）**
- `notification` が無い場合は `inApp` のみとみなす

---

## 実装したフィルタロジック

### 期限フィルタ（isAnnouncementActive）

```typescript
// domain/announcement.ts
export function isAnnouncementActive(
  announcement: Announcement,
  now: Date = new Date(),
): boolean {
  const publishFrom = new Date(announcement.publishFrom);
  const publishTo = announcement.publishTo
    ? new Date(announcement.publishTo)
    : null;
  return publishFrom <= now && (publishTo === null || now <= publishTo);
}
```

### 対象フィルタ（isVisibleForAudience）

```typescript
// domain/announcement.ts
export function isVisibleForAudience(
  announcement: Announcement,
  currentAudience: Audience,
): boolean {
  const { audience } = announcement;

  if (audience === "all" || audience === "internal") {
    return true;
  }

  return audience === currentAudience;
}
```

### 適用箇所

- `LocalAnnouncementRepository.list()`: 期限フィルタのみ適用
- `useAnnouncementsListViewModel`: 対象フィルタ適用
- `useAnnouncementBannerViewModel`: 対象フィルタ適用、critical優先ソート
- `useUnreadAnnouncementCountViewModel`: 対象フィルタ適用

---

## UI変更点

### 一覧カード（AnnouncementListItem）

- タグバッジ追加（最大3個、グレー背景）
- 添付ありバッジ追加（📎アイコン付き、青背景）

### 詳細画面（AnnouncementDetail）

- 添付ファイルセクション追加（`attachments` がある場合のみ表示）
  - PDF: 赤アイコン + "PDF" タグ
  - リンク: リンクアイコン
  - ホバー時に背景色変更

---

## テストデータ（seed.ts）

| ID      | タイトル                 | 用途                                                         |
| ------- | ------------------------ | ------------------------------------------------------------ |
| ann-001 | システムメンテナンス     | warn + attachments(pdf) + notification(email, sendOnPublish) |
| ann-002 | 新機能リリース           | info + notification無し（互換確認）                          |
| ann-003 | セキュリティアップデート | critical + attachments(link) + notification(email)           |
| ann-004 | 年末年始の営業時間       | info + tags                                                  |
| ann-005 | サーバー増強作業完了     | info                                                         |
| ann-006 | 不正アクセス注意喚起     | warn + notification(line, scheduledAt)                       |
| ann-007 | 成田拠点向け             | info + audience=site:narita + tags                           |
| ann-008 | 新木場拠点向け           | info + audience=site:shinkiba + tags（表示されない）         |
| ann-009 | 社内向けドキュメント     | info + audience=internal + attachments                       |
| ann-010 | 期限切れテスト           | publishTo=過去（表示されない）                               |
| ann-011 | 未来開始テスト           | publishFrom=未来（表示されない）                             |

---

## Repository 境界の維持

### 設計方針

- **Repository**: アクティブ（期限内）なお知らせのみ返す
- **ViewModel**: 対象（audience）フィルタを適用
- 将来のAPI化時、サーバー側でユーザー属性に基づくフィルタを実装可能

### インターフェース（ports/AnnouncementRepository.ts）

```typescript
export interface AnnouncementRepository {
  list(): Promise<Announcement[]>;
  get(id: string): Promise<Announcement | null>;
}
```

- 変更なし、互換性維持
- 将来 `HttpAnnouncementRepository` に差し替え可能

---

## 将来のバックエンド実装（Outbox パターン推奨）

### DB設計

```sql
-- announcements テーブル
ALTER TABLE announcements ADD COLUMN notification_plan JSONB;

-- notification_outbox テーブル（新規作成）
CREATE TABLE notification_outbox (
  id SERIAL PRIMARY KEY,
  announcement_id INTEGER REFERENCES announcements(id),
  channel VARCHAR(20) NOT NULL,  -- 'email' | 'line'
  status VARCHAR(20) DEFAULT 'pending',  -- 'pending' | 'sent' | 'failed'
  sent_at TIMESTAMP,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Worker処理フロー

1. **publish時**: `notification_outbox` にレコードを積む
2. **Worker**: 定期的にポーリング（例: 1分ごと）
3. **送信**: `status='pending'` のレコードを処理
4. **更新**: 送信成功 → `status='sent'`, `sent_at=NOW()`、失敗 → `status='failed'`, `error_message`

### Clean Architecture

```
application/
  ports/
    NotificationDispatcherPort.ts  # インターフェース

infrastructure/
  adapters/
    EmailAdapter.ts                # SendGrid/SES/etc
    LineAdapter.ts                 # LINE Messaging API
```

### 実装TODO

- [ ] バックエンドに `notification_plan` カラム追加
- [ ] `notification_outbox` テーブル作成
- [ ] Worker実装（Celery/BullMQ/etc）
- [ ] EmailAdapter実装
- [ ] LineAdapter実装
- [ ] フロントの `CURRENT_AUDIENCE` をユーザープロファイルから取得

---

## 既存機能への影響

### 確認済み（影響なし）

- ✅ 既読/未読機能（localStorage）
- ✅ ACK機能（バナーの「理解した」）
- ✅ 詳細モーダル表示
- ✅ タブフィルタ（全て/未読）

### 追加されたフィルタ

- ✅ 期限切れは一覧/トップから自動除外
- ✅ 対象外（audience不一致）は一覧/トップから自動除外
- ✅ 未読数も対象フィルタ適用済み

---

## 動作確認チェックリスト

- [ ] 一覧画面でタグバッジが表示される
- [ ] 一覧画面で添付ありバッジが表示される
- [ ] 詳細画面で添付ファイルセクションが表示される
- [ ] 添付リンクをクリックして別タブで開ける
- [ ] 期限切れ（ann-010）が一覧に表示されない
- [ ] 未来開始（ann-011）が一覧に表示されない
- [ ] 対象外（ann-008: site:shinkiba）が一覧に表示されない
- [ ] トップバナーにcriticalが優先表示される
- [ ] 既読/未読機能が正常動作する

---

## 制限事項

### 現在の制限

1. **対象判定**: `CURRENT_AUDIENCE` が定数（`'site:narita'`）
   - 将来: ユーザープロファイル/認証情報から取得
2. **通知送信**: 実装していない（表示のみ）
   - 将来: バックエンドWorkerで実装
3. **テンプレート**: `templateHint` は保持のみ
   - 将来: メール/LINEテンプレート切替に使用

### API移行時の注意点

- `CURRENT_AUDIENCE` の取得ロジックを追加
- サーバー側で audience フィルタを実装推奨（パフォーマンス向上）
- `notification_plan` の保存/取得APIを実装

---

## 関連ファイル

### Domain

- `features/announcements/domain/announcement.ts`

### Infrastructure

- `features/announcements/infrastructure/seed.ts`
- `features/announcements/infrastructure/LocalAnnouncementRepository.ts`

### ViewModel

- `features/announcements/model/useAnnouncementsListViewModel.ts`
- `features/announcements/model/useAnnouncementBannerViewModel.ts`
- `features/announcements/model/useUnreadAnnouncementCountViewModel.ts`

### UI

- `features/announcements/ui/AnnouncementListItem.tsx`
- `features/announcements/ui/AnnouncementDetail.tsx`

---

## 参考資料

- [Feature-Sliced Design](https://feature-sliced.design/)
- [Outbox Pattern](https://microservices.io/patterns/data/transactional-outbox.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
