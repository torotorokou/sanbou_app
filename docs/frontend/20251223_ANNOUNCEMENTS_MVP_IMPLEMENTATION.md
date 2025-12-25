# お知らせ機能 MVP 実装ドキュメント

**実装日**: 2025年12月23日  
**ブランチ**: `feature/announcements-mvp`  
**実装者**: Copilot (GitHub)  
**ステータス**: ✅ MVP完成（フロントエンドのみ、localStorage永続化）

---

## 📋 概要

社内ポータルシステムに「お知らせ（Announcements）」機能を追加しました。  
**MVP（Minimum Viable Product）** として、**フロントエンドのみ**で動作する最小構成を実装しています。

### 実現した機能

1. **トップページの重要通知バナー**

   - `pinned=true` かつ重要度が `warn` または `critical` のお知らせを1件表示
   - 「理解しました」ボタンで確認済み（ack）にし、再表示されないようにする
   - 「×」ボタンでも同様に確認済みにする

2. **お知らせ一覧ページ**

   - アクティブなお知らせを一覧表示
   - 重要度（info/warn/critical）とピン留めをバッジで視覚化
   - 未読のお知らせは背景色と左ボーダーで強調
   - クリックで詳細モーダルを開く（開いた時点で既読化）

3. **サイドバーの未読カウント**
   - 「お知らせ」メニューに未読数バッジを表示
   - 既読化されると自動的にカウントが減少

---

## 🏗️ アーキテクチャ

### Feature-Sliced Design (FSD)

既存の設計パターン（React: FSD + MVVM(Hooks=ViewModel) + Repository）に従い、以下の層構造で実装：

```
app/frontend/src/features/announcements/
├── domain/
│   └── announcement.ts          # 型定義、判定ロジック
├── ports/
│   └── AnnouncementRepository.ts # リポジトリインターフェース
├── infrastructure/
│   ├── seed.ts                  # ダミーデータ（3件）
│   ├── LocalAnnouncementRepository.ts  # ローカル実装
│   └── announcementUserStateStorage.ts # localStorage永続化
├── model/
│   ├── useAnnouncementBannerViewModel.ts       # バナー用VM
│   ├── useAnnouncementsListViewModel.ts        # 一覧用VM
│   └── useUnreadAnnouncementCountViewModel.ts  # 未読数用VM
├── ui/
│   ├── AnnouncementBanner.tsx          # バナーUI
│   ├── AnnouncementList.tsx            # 一覧UI
│   ├── AnnouncementDetailModal.tsx     # 詳細モーダルUI
│   └── NewsMenuLabel.tsx               # サイドバー用ラベル
└── index.ts                     # 公開API
```

### MVVM パターン

- **ViewModel（Hooks）**: ビジネスロジックと状態管理を担当
- **View（UIコンポーネント）**: 状態レス、propsのみで動作
- **Repository**: データ取得の抽象化（将来のHTTP化に対応）

---

## 📦 データモデル

### Announcement 型

```typescript
export interface Announcement {
  id: string; // 一意識別子
  title: string; // タイトル
  bodyMd: string; // 本文（Markdown形式）
  severity: "info" | "warn" | "critical"; // 重要度
  pinned: boolean; // ピン留め（トップページバナー対象）
  publishFrom: string; // 公開開始日時（ISO8601）
  publishTo: string | null; // 公開終了日時（null=無期限）
}
```

### ユーザー状態（localStorage）

```typescript
export interface AnnouncementUserState {
  readAtById: Record<string, string>; // 既読日時（ID→ISO8601）
  ackAtById: Record<string, string>; // 確認済み日時（ID→ISO8601）
}
```

**保存先**: `localStorage`  
**キー**: `announcements.v1.<userKey>`  
**userKey**: `user.userId` または `"local"`（未ログイン時）

---

## 🎯 判定ロジック

### アクティブ判定

```typescript
function isAnnouncementActive(announcement: Announcement): boolean {
  const now = new Date();
  const publishFrom = new Date(announcement.publishFrom);
  const publishTo = announcement.publishTo
    ? new Date(announcement.publishTo)
    : null;

  return publishFrom <= now && (publishTo === null || now <= publishTo);
}
```

### バナー表示対象判定

```typescript
function isBannerTarget(announcement: Announcement): boolean {
  return (
    announcement.pinned &&
    (announcement.severity === "warn" || announcement.severity === "critical")
  );
}
```

---

## 🔧 実装詳細

### Step A: feature骨組み

- `domain/announcement.ts`: 型定義、active判定、banner判定
- `ports/AnnouncementRepository.ts`: リポジトリインターフェース
- `infrastructure/seed.ts`: 3件のダミーデータ
- `infrastructure/LocalAnnouncementRepository.ts`: シードから取得
- `infrastructure/announcementUserStateStorage.ts`: localStorage永続化

### Step B: ViewModel

- `useAnnouncementBannerViewModel`: バナー用（1件選択＋ack処理）
- `useAnnouncementsListViewModel`: 一覧用（全件取得＋詳細開閉＋既読化）
- `useUnreadAnnouncementCountViewModel`: 未読数用（軽量）

### Step C: UI（状態レス）

- `AnnouncementBanner`: 重要度に応じたアラート表示
- `AnnouncementList`: 一覧表示（未読強調、バッジ表示）
- `AnnouncementDetailModal`: 詳細モーダル（簡易Markdownレンダリング）
- `NewsMenuLabel`: サイドバー用ラベル（未読バッジ付き）

### Step D: ページとルーティング統合

- `pages/home/NewsPage.tsx`: 一覧ページを実装版に置き換え
- `pages/home/PortalPage.tsx`: バナー表示を追加
- ルーティングは既存の `/news` を使用

### Step E: サイドバー未読バッジ統合

- `app/navigation/sidebarMenu.tsx`: `NewsMenuLabel` を統合
- 未読数バッジを動的に表示

---

## 🧪 テストシナリオ

### 1. トップページバナー

**前提条件**: 初回アクセス（localStorage未設定）

1. トップページ（`/`）にアクセス
2. 重要通知バナーが表示される（`ann-001` または `ann-003`）
3. 「理解しました」ボタンをクリック
4. バナーが消える
5. リロードしても再表示されない
6. localStorage を確認: `announcements.v1.local` に `ackAtById` が保存されている

### 2. お知らせ一覧

**前提条件**: トップページバナーで1件確認済み

1. サイドバーの「お知らせ」をクリック（未読バッジが `2` または `3` と表示）
2. お知らせ一覧ページ（`/news`）に遷移
3. 未読のお知らせが背景色＋左ボーダーで強調表示
4. 任意のお知らせをクリック
5. 詳細モーダルが開く（簡易Markdown表示）
6. モーダルを閉じる
7. 一覧に戻ると、クリックしたお知らせが既読（太字解除）になっている

### 3. サイドバー未読バッジ

**前提条件**: 一部既読状態

1. サイドバーの「お知らせ」メニューを確認
2. 未読数バッジが表示されている（例: `1` や `2`）
3. 一覧ページで全て既読にする
4. サイドバーに戻ると、バッジが消えている

---

## 🚀 次フェーズ（HTTP/DB対応）

### 実装予定

1. **バックエンドAPI作成**

   - `GET /api/announcements` - 一覧取得
   - `GET /api/announcements/:id` - 詳細取得
   - `POST /api/announcements/:id/read` - 既読化
   - `POST /api/announcements/:id/acknowledge` - 確認済み化

2. **DB設計**

   ```sql
   CREATE TABLE announcements (
     id UUID PRIMARY KEY,
     title TEXT NOT NULL,
     body_md TEXT NOT NULL,
     severity VARCHAR(10) NOT NULL CHECK (severity IN ('info', 'warn', 'critical')),
     pinned BOOLEAN DEFAULT FALSE,
     publish_from TIMESTAMP NOT NULL,
     publish_to TIMESTAMP,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE announcement_user_states (
     user_id VARCHAR(255) NOT NULL,
     announcement_id UUID NOT NULL,
     read_at TIMESTAMP,
     acknowledged_at TIMESTAMP,
     PRIMARY KEY (user_id, announcement_id),
     FOREIGN KEY (announcement_id) REFERENCES announcements(id)
   );
   ```

3. **HttpAnnouncementRepository 作成**

   - `LocalAnnouncementRepository` と同じインターフェースで実装
   - DI（依存性注入）で切り替え可能にする

4. **マイグレーション**
   - Alembic でテーブル作成
   - 初期データ投入（seed.ts のデータを移行）

### 差し替え箇所

```typescript
// 現在（MVP）
import { announcementRepository } from "@features/announcements/infrastructure/LocalAnnouncementRepository";

// 次フェーズ
import { announcementRepository } from "@features/announcements/infrastructure/HttpAnnouncementRepository";
```

ViewModel と UI は変更不要（Repository の差し替えのみ）。

---

## 📝 受け入れ条件（✅ 完了）

- [x] TypeScript型チェックが通る（`npx tsc --noEmit`）
- [x] トップページに重要通知バナーが表示される
- [x] 「理解しました」で確認済みになり、リロードしても再表示されない
- [x] お知らせ一覧で詳細を開くと既読化される
- [x] サイドバーに未読数バッジが表示される
- [x] 既存機能に影響がない（エラー・警告なし）

---

## 🔗 関連ファイル

### 新規作成ファイル（14ファイル）

| ファイルパス                                                            | 説明             |
| ----------------------------------------------------------------------- | ---------------- |
| `features/announcements/domain/announcement.ts`                         | 型定義、判定関数 |
| `features/announcements/ports/AnnouncementRepository.ts`                | リポジトリIF     |
| `features/announcements/infrastructure/seed.ts`                         | ダミーデータ     |
| `features/announcements/infrastructure/LocalAnnouncementRepository.ts`  | ローカル実装     |
| `features/announcements/infrastructure/announcementUserStateStorage.ts` | localStorage     |
| `features/announcements/model/useAnnouncementBannerViewModel.ts`        | バナーVM         |
| `features/announcements/model/useAnnouncementsListViewModel.ts`         | 一覧VM           |
| `features/announcements/model/useUnreadAnnouncementCountViewModel.ts`   | 未読数VM         |
| `features/announcements/ui/AnnouncementBanner.tsx`                      | バナーUI         |
| `features/announcements/ui/AnnouncementList.tsx`                        | 一覧UI           |
| `features/announcements/ui/AnnouncementDetailModal.tsx`                 | 詳細モーダル     |
| `features/announcements/ui/NewsMenuLabel.tsx`                           | サイドバー用     |
| `features/announcements/index.ts`                                       | 公開API          |

### 変更ファイル（3ファイル）

| ファイルパス                     | 変更内容                             |
| -------------------------------- | ------------------------------------ |
| `pages/home/NewsPage.tsx`        | 未実装モーダル削除、実装版に置き換え |
| `pages/home/PortalPage.tsx`      | バナー表示追加                       |
| `app/navigation/sidebarMenu.tsx` | 未読バッジ追加                       |

---

## 💡 ベストプラクティス

### 1. Repository パターンによる抽象化

```typescript
// ✅ Good: インターフェースに依存
const { announcements } = useAnnouncementsListViewModel(userKey);

// ❌ Bad: 直接実装に依存
const announcements = ANNOUNCEMENT_SEEDS.filter(...);
```

### 2. ViewModel でロジック集約

```typescript
// ✅ Good: ViewModel に既読化ロジックを集約
const { openDetail } = useAnnouncementsListViewModel(userKey);
openDetail(id); // 内部で既読化処理

// ❌ Bad: UI コンポーネントにロジックを散らす
onClick={() => {
  markAsRead(userKey, id);
  setSelected(id);
  setOpen(true);
}}
```

### 3. 状態レスな UI コンポーネント

```typescript
// ✅ Good: props のみで動作
<AnnouncementList items={announcements} onOpen={openDetail} isUnread={isUnread} />

// ❌ Bad: 内部で状態管理
const AnnouncementList = () => {
  const [items, setItems] = useState([]);
  useEffect(() => { fetchItems(); }, []);
  // ...
};
```

---

## 🐛 既知の制限事項

1. **Markdown レンダリングが簡易的**

   - 見出し、リスト、強調のみ対応
   - 画像、リンク、コードブロックは未対応
   - → 次フェーズで `react-markdown` 導入を検討

2. **リアルタイム更新なし**

   - ページリロードまたは遷移時のみデータ取得
   - → 将来的に WebSocket または polling で対応

3. **マルチユーザー対応が不完全**
   - localStorage はブラウザ単位
   - → DB化後は正式にユーザーID単位で管理

---

## 📚 参考資料

- [Feature-Sliced Design](https://feature-sliced.design/)
- [MVVM パターン](https://ja.wikipedia.org/wiki/Model_View_ViewModel)
- [Repository パターン](https://martinfowler.com/eaaCatalog/repository.html)

---

**更新履歴**

| 日付       | 変更内容              | 担当    |
| ---------- | --------------------- | ------- |
| 2025-12-23 | 初版作成（MVP完成時） | Copilot |
