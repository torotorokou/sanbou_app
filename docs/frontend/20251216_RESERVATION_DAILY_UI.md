# 予約表（手入力）機能 - フロントエンド実装ドキュメント

**日付**: 2025-12-16  
**ブランチ**: feature/add-reservation-daily-ui  
**実装者**: Frontend Implementation

---

## 概要

予約表（手入力）機能のフロントエンドを実装しました。
React + TypeScript、FSD構成 + MVVM（Hooks = ViewModel） + Repositoryパターンを採用しています。

---

## 実装内容

### Phase A: ルーティングとサイドバー追加 ✅

**変更ファイル:**

- [app/frontend/src/app/routes/routes.ts](../../app/frontend/src/app/routes/routes.ts)
  - `RESERVATION_DAILY: '/database/reservation-daily'` を追加
- [app/frontend/src/app/navigation/sidebarMenu.tsx](../../app/frontend/src/app/navigation/sidebarMenu.tsx)
  - 「データベース」配下に「予約表」メニューを追加
- [app/frontend/src/app/routes/AppRoutes.tsx](../../app/frontend/src/app/routes/AppRoutes.tsx)
  - ReservationDailyPage のルートを追加
- [app/frontend/src/pages/database/ReservationDailyPage.tsx](../../app/frontend/src/pages/database/ReservationDailyPage.tsx)
  - 新規ページを作成
- [app/frontend/src/pages/database/index.ts](../../app/frontend/src/pages/database/index.ts)
  - Public API に追加

**動作確認:**

- サイドバーの「データベース」→「予約表」から遷移可能
- 左右2カラムのレイアウトで表示

---

### Phase B & C: カレンダー表示 + 手入力フォーム実装 ✅

#### ディレクトリ構成（FSD）

```
features/reservation-daily/
├── index.ts                            # Public API
├── ports/
│   └── ReservationDailyRepository.ts   # インターフェース定義
├── infrastructure/
│   └── ReservationDailyHttpRepository.ts # HTTP実装
├── model/
│   └── useReservationDailyViewModel.ts # ViewModel (状態管理)
└── ui/
    ├── ReservationCalendar.tsx         # カレンダーコンポーネント
    └── ReservationForm.tsx             # フォームコンポーネント
```

#### 型定義

**ReservationForecastDaily** (表示用データ)

```typescript
{
  date: string; // YYYY-MM-DD
  reserve_trucks: number; // 予約台数合計
  reserve_fixed_trucks: number; // 固定客台数
  reserve_fixed_ratio: number; // 固定客比率
  source: "manual" | "customer_agg"; // データソース
}
```

**ReservationManualInput** (入力データ)

```typescript
{
  reserve_date: string;                  // YYYY-MM-DD
  total_trucks: number;                  // 合計台数
  fixed_trucks: number;                  // 固定客台数
  note?: string;                         // 備考（任意）
}
```

#### Repository (インターフェース)

**ReservationDailyRepository**

- `getForecastDaily(from, to)` - 予測用日次データ取得
- `upsertManual(payload)` - 手入力データ保存/更新
- `deleteManual(date)` - 手入力データ削除

#### HTTP実装

**ReservationDailyHttpRepository**

- 既存の `apiClient` を使用
- シングルトンインスタンス `reservationDailyRepository` をエクスポート

#### ViewModel (状態管理)

**useReservationDailyViewModel**

**State:**

- `currentMonth` - 表示中の月
- `forecastData` - カレンダー表示用データ
- `selectedDate` - 選択中の日付
- `totalTrucks`, `fixedTrucks`, `note` - フォーム入力値
- `isLoading`, `isSaving` - ローディング状態
- `error`, `successMessage` - メッセージ

**Events:**

- `onChangeMonth(month)` - 月変更
- `onSelectDate(date)` - 日付選択（フォームに反映）
- `onChangeTotalTrucks(value)` - 合計台数変更
- `onChangeFixedTrucks(value)` - 固定客台数変更
- `onChangeNote(value)` - 備考変更
- `onSubmit()` - 保存（バリデーション→API呼び出し→再取得）
- `onDelete()` - 削除（API呼び出し→再取得）
- `clearMessages()` - メッセージクリア

**バリデーション:**

- `total_trucks >= 0`
- `fixed_trucks >= 0`
- `fixed_trucks <= total_trucks`
- `reserve_date` 必須

#### UI Components

**ReservationCalendar**

- Ant Design の `Calendar` を使用
- `dateCellRender` でバッジ表示
  - manual: 緑バッジ（success）
  - customer_agg: 青バッジ（processing）
- 日付クリックで選択
- 月切替で再取得

**ReservationForm**

- 選択日表示
- InputNumber × 2（合計台数、固定客台数）
- TextArea（備考）
- 保存ボタン（primary）
- 削除ボタン（danger、manual データがある場合のみ表示）
- バリデーションエラー表示

---

## APIエンドポイント（仮置き）

以下のエンドポイントを想定してHTTP実装を作成しています。
**バックエンド実装後に調整が必要です。**

### 1. 予測用日次データ取得

```
GET /api/reservations/forecast-daily?from=YYYY-MM-DD&to=YYYY-MM-DD
```

**Response:**

```json
[
  {
    "date": "2025-01-15",
    "reserve_trucks": 100,
    "reserve_fixed_trucks": 60,
    "reserve_fixed_ratio": 0.6,
    "source": "manual"
  }
]
```

### 2. 手入力データ保存/更新

```
POST /api/reservations/daily-manual
```

**Request Body:**

```json
{
  "reserve_date": "2025-01-15",
  "total_trucks": 100,
  "fixed_trucks": 60,
  "note": "備考"
}
```

**Response:**

```json
{ "success": true }
```

### 3. 手入力データ削除

```
DELETE /api/reservations/daily-manual?date=YYYY-MM-DD
```

**Response:**

```json
{ "success": true }
```

---

## 変更ファイル一覧

### Phase A（ルーティング）

- `app/frontend/src/app/routes/routes.ts`
- `app/frontend/src/app/navigation/sidebarMenu.tsx`
- `app/frontend/src/app/routes/AppRoutes.tsx`
- `app/frontend/src/pages/database/ReservationDailyPage.tsx` (新規)
- `app/frontend/src/pages/database/index.ts`

### Phase B & C（機能実装）

- `app/frontend/src/features/reservation-daily/index.ts` (新規)
- `app/frontend/src/features/reservation-daily/ports/ReservationDailyRepository.ts` (新規)
- `app/frontend/src/features/reservation-daily/infrastructure/ReservationDailyHttpRepository.ts` (新規)
- `app/frontend/src/features/reservation-daily/model/useReservationDailyViewModel.ts` (新規)
- `app/frontend/src/features/reservation-daily/ui/ReservationCalendar.tsx` (新規)
- `app/frontend/src/features/reservation-daily/ui/ReservationForm.tsx` (新規)
- `app/frontend/src/pages/database/ReservationDailyPage.tsx` (更新)

---

## 動作確認手順

### 1. 画面遷移

1. サイドバーの「データベース」を開く
2. 「予約表」をクリック
3. 予約表画面が表示される

### 2. カレンダー表示

1. 当月のカレンダーが表示される
2. 既存データがある日付にはバッジが表示される
   - 緑バッジ: manual入力
   - 青バッジ: customer集計
3. 月切替ボタンで前月/次月に移動可能

### 3. 手入力・保存

1. カレンダーで日付をクリック
2. 左側のフォームに選択日が表示される
3. 「合計台数」「固定客台数」を入力
4. 「保存」ボタンをクリック
5. 成功メッセージが表示される
6. カレンダーに即反映される

### 4. 削除

1. manual入力がある日付を選択
2. 「削除」ボタンが表示される
3. クリックすると削除される
4. カレンダーから消える（customer集計があれば青バッジで表示）

---

## 未確定点・TODO

### バックエンドエンドポイント

以下のエンドポイントは仮置きです。実装後に調整が必要です：

- ✅ **仮**: `GET /api/reservations/forecast-daily`
  - **調整必要**: バックエンドの実際のパスに合わせる
- ✅ **仮**: `POST /api/reservations/daily-manual`
  - **調整必要**: バックエンドの実際のパスに合わせる
- ✅ **仮**: `DELETE /api/reservations/daily-manual`
  - **調整必要**: バックエンドの実際のパスに合わせる

### 調整箇所

エンドポイントが確定したら、以下のファイルを修正：

- [ReservationDailyHttpRepository.ts](../../app/frontend/src/features/reservation-daily/infrastructure/ReservationDailyHttpRepository.ts)

---

## 技術要件の遵守

✅ **React + TypeScript**: 全てTypeScriptで実装  
✅ **FSD構成**: features/reservation-daily 配下に配置  
✅ **MVVM**: useReservationDailyViewModel (ViewModel), UI Components (View)  
✅ **Repositoryパターン**: Port (interface) + Infrastructure (HTTP実装)  
✅ **既存ページ保全**: DatasetImportPage のスタイルを再利用、破壊的変更なし

---

## コミット履歴

```
48e5d392 - feat(ui): add reservation daily page routing and sidebar (Phase A)
8534a306 - feat(ui): implement reservation daily form and calendar (Phase B & C)
```

---

## 次のステップ

1. ⬜ **バックエンドAPI実装**

   - GET /reservations/forecast-daily
   - POST /reservations/daily-manual
   - DELETE /reservations/daily-manual

2. ⬜ **エンドポイント調整**

   - ReservationDailyHttpRepository.ts のパスを実際のAPIに合わせる

3. ⬜ **統合テスト**

   - バックエンドと接続して動作確認
   - エラーハンドリングの確認

4. ⬜ **UI改善（任意）**
   - カレンダーのツールチップ追加
   - データの無い日をグレーアウト
   - モバイル対応

---

## 参考資料

- [既存実装: DatasetImportPage](../../app/frontend/src/pages/database/DatasetImportPage.tsx)
- [DB実装: Reserve Tables Migration](../backend/20251216_RESERVE_TABLES_MIGRATION.md)
