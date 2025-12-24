# お知らせ機能 タグ・表示仕様書 (2025-12-23)

お知らせ機能で使用されている重要度タグおよび視覚的な表示ルールについての仕様をまとめます。

## 1. タグの種類と意味

お知らせには「重要度（Severity）」の属性があり、タグとして表示されます。

### 重要度 (Severity)
お知らせの内容の緊急性や重要度を表します。

| ラベル | 色 | キー | 用途・意味 |
| :--- | :--- | :--- | :--- |
| **重要** | 赤 (Red) | `critical` | システム障害、緊急メンテナンス、法的対応など、全ユーザーが即座に確認すべき内容。 |
| **注意** | 橙 (Orange) | `warn` | 仕様変更、一時的な機能制限、操作上の注意点など、確認を推奨する内容。 |
| **情報** | 青 (Blue) | `info` | 新機能の追加、一般的なアップデート、定期的なお知らせなど。 |

### バナー表示 (AnnouncementBanner)
ポータル画面上部に表示されるバナーも、重要度に応じて色とアイコンが変化します。

| 重要度 | アラートタイプ | アイコン |
| :--- | :--- | :--- |
| `critical` | エラー (Red) | `ExclamationCircleOutlined` (感嘆符) |
| `warn` | 警告 (Orange) | `WarningOutlined` (三角警告) |
| `info` | 情報 (Blue) | デフォルトアイコン |

---

## 2. 既読・未読の表示

ユーザーがまだ詳細を開いていないお知らせは、視覚的に強調されます。

- **未読状態**:
  - 左端に黄色の太線 (`#faad14`) が表示されます。
  - タイトルの左に黄色のドットが表示されます。
  - 背景色が薄い黄色 (`#fffbf0`) になります。
- **既読状態**:
  - 左端の線はなくなり、背景は薄いグレー (`#fafafa`) になります。

---

## 3. デバイスごとの表示ルール

モバイル端末での視認性を高めるため、デバイスサイズに応じて表示を切り替えています。

### モバイル (画面幅 767px 以下)
- **一覧ページ**:
  - **タグ（重要度）は非表示**になります（横幅を節約するため）。
  - タイトルと日付は2行に分けて表示されます。
  - フォントサイズが縮小されます（タイトル: 14px, 日付: 11px）。
- **詳細ページ**:
  - タイトルが中央揃えになります。
  - タグはタイトルの下に中央揃えで表示されます。

### デスクトップ (画面幅 768px 以上)
- **一覧ページ**:
  - タイトル、タグ、日付が1行に並んで表示されます。
- **詳細ページ**:
  - タイトルとタグが横並びで表示されます。

---

## 4. 実装リファレンス

- **型定義**: [app/frontend/src/features/announcements/domain/announcement.ts](app/frontend/src/features/announcements/domain/announcement.ts)
- **詳細UI**: [app/frontend/src/features/announcements/ui/AnnouncementDetail.tsx](app/frontend/src/features/announcements/ui/AnnouncementDetail.tsx)
- **一覧UI**: [app/frontend/src/features/announcements/ui/AnnouncementListItem.tsx](app/frontend/src/features/announcements/ui/AnnouncementListItem.tsx)
