# 達成率モード切り替え機能の実装

**実装日**: 2025-11-17  
**対象**: 受入ダッシュボード - 目標カード

## 概要

目標カードにおいて、以下2つの達成率表示モードをボタン一つで切り替え可能にしました。

### モードA: 「昨日までの累計目標」に対する達成率 (toDate)

- **月**: 昨日までの月累計実績 ÷ 昨日までの月累計目標
- **週**: 昨日までの週累計実績 ÷ 昨日までの週累計目標
- **日**: 昨日の実績 ÷ 昨日の目標

### モードB: 「期末（週末・月末）の総目標」に対する達成率 (toEnd)

- **月**: 昨日までの月累計実績 ÷ 月末の月目標トータル
- **週**: 昨日までの週累計実績 ÷ 週末の週目標トータル
- **日**: 昨日の実績 ÷ 昨日の目標（日目標は変更なし）

---

## 変更ファイル一覧

### 1. バックエンド

#### 1.1 SQL / Repository

**ファイル**: `app/backend/core_api/app/infra/adapters/dashboard/dashboard_target_repo.py`

**変更内容**:

- `get_by_date_optimized` メソッドのSQLクエリを拡張
- 以下の新しいフィールドを計算・返却：
  - `month_target_to_date_ton`: 月初〜昨日までの日次目標の合計
  - `month_target_total_ton`: 月全体の目標トータル（MAX(month_target_ton)）
  - `week_target_to_date_ton`: 週初〜昨日までの日次目標の合計
  - `week_target_total_ton`: 週全体の目標トータル（MAX(week_target_ton)）
  - `month_actual_to_date_ton`: 月初〜昨日までの実績合計（`v_receive_daily` より）
  - `week_actual_to_date_ton`: 週初〜昨日までの実績合計（`v_receive_daily` より）

**SQL処理の詳細**:

```sql
-- 昨日の日付を計算
yesterday AS (
  SELECT ((SELECT today FROM today) - INTERVAL '1 day')::date AS yesterday_date
)

-- 月累計目標（昨日まで）
month_target_to_date AS (
  SELECT COALESCE(SUM(v.day_target_ton), 0)::numeric AS month_target_to_date_ton
  FROM mart.v_target_card_per_day v
  WHERE v.ddate BETWEEN (SELECT month_start FROM bounds) AND (SELECT yesterday_date FROM yesterday)
)

-- 月トータル目標（期末）
month_target_total AS (
  SELECT COALESCE(MAX(v.month_target_ton), 0)::numeric AS month_target_total_ton
  FROM mart.v_target_card_per_day v
  WHERE v.ddate BETWEEN (SELECT month_start FROM bounds) AND (SELECT month_end FROM bounds)
)

-- （週の累計目標・トータル目標・実績も同様）
```

#### 1.2 Pydantic Schema

**ファイル**: `app/backend/core_api/app/presentation/schemas/__init__.py`

**変更内容**:
`TargetMetricsResponse` に以下のフィールドを追加：

```python
# New fields for achievement mode calculation
month_target_to_date_ton: Optional[float] = Field(default=None, description="Monthly cumulative target (month_start to yesterday)")
month_target_total_ton: Optional[float] = Field(default=None, description="Monthly total target (entire month)")
week_target_to_date_ton: Optional[float] = Field(default=None, description="Weekly cumulative target (week_start to yesterday)")
week_target_total_ton: Optional[float] = Field(default=None, description="Weekly total target (entire week)")
month_actual_to_date_ton: Optional[float] = Field(default=None, description="Monthly cumulative actual (month_start to yesterday)")
week_actual_to_date_ton: Optional[float] = Field(default=None, description="Weekly cumulative actual (week_start to yesterday)")
```

**互換性**: 既存フィールド（`month_target_ton`, `week_target_ton` 等）は維持されているため、他画面への影響はありません。

---

### 2. フロントエンド

#### 2.1 DTO

**ファイル**: `app/frontend/src/features/dashboard/ukeire/kpi-targets/infrastructure/targetMetrics.api.ts`

**変更内容**:
`TargetMetricsDTO` にバックエンドレスポンスと1:1対応する新フィールドを追加：

```typescript
export interface TargetMetricsDTO {
  // ... 既存フィールド ...

  // New fields for achievement mode calculation
  month_target_to_date_ton: number | null;
  month_target_total_ton: number | null;
  week_target_to_date_ton: number | null;
  week_target_total_ton: number | null;
  month_actual_to_date_ton: number | null;
  week_actual_to_date_ton: number | null;
}
```

#### 2.2 ViewModel

**ファイル**: `app/frontend/src/features/dashboard/ukeire/kpi-targets/application/useTargetsVM.ts`

**変更内容**:

1. **新しい型の追加**:

```typescript
export type AchievementMode = "toDate" | "toEnd";
```

2. **UseTargetsVMParams の拡張**:

```typescript
export type UseTargetsVMParams = {
  mode: AchievementMode;
  // Cumulative targets (昨日まで)
  monthTargetToDate: number | null;
  weekTargetToDate: number | null;
  dayTarget: number | null;
  // Total targets (期末トータル)
  monthTargetTotal: number | null;
  weekTargetTotal: number | null;
  // Actuals (昨日までの累計)
  todayActual: number | null;
  weekActual: number | null;
  monthActual: number | null;
};
```

3. **モードに応じた目標値の切り替え**:

```typescript
const monthTarget = mode === "toDate" ? monthTargetToDate : monthTargetTotal;
const weekTarget = mode === "toDate" ? weekTargetToDate : weekTargetTotal;
```

4. **ラベルの動的変更**:

```typescript
{
  key: "month",
  label: mode === "toDate" ? "当月目標（昨日まで）" : "当月最終目標",
  target: monthTarget,
  actual: monthActual,
}
```

**設計のポイント**:

- 達成率の計算は TargetCard コンポーネントに任せる（変更なし）
- ViewModel は「どの目標値を使うか」の切り替えのみを担当
- SOLID原則に従い、責務を分離

#### 2.3 エクスポート

**ファイル**: `app/frontend/src/features/dashboard/ukeire/kpi-targets/index.ts`

**変更内容**:

```typescript
export {
  useTargetsVM,
  type AchievementMode,
  type UseTargetsVMParams,
} from "./application/useTargetsVM";
```

**ファイル**: `app/frontend/src/features/dashboard/ukeire/index.ts`

**変更内容**:

```typescript
export {
  useTargetsVM,
  type AchievementMode,
  type UseTargetsVMParams,
} from "./kpi-targets/application/useTargetsVM";
```

#### 2.4 Page Component

**ファイル**: `app/frontend/src/pages/dashboard/ukeire/InboundForecastDashboardPage.tsx`

**変更内容**:

1. **import の追加**:

```typescript
import { useState } from "react";
import { Button, Space } from "antd";
import {
  useTargetsVM,
  type AchievementMode,
} from "@/features/dashboard/ukeire";
```

2. **state の追加**:

```typescript
const [achievementMode, setAchievementMode] =
  useState<AchievementMode>("toDate");
```

3. **useTargetsVM の呼び出し**:

```typescript
const targetCardVM = useTargetsVM({
  mode: achievementMode,
  monthTargetToDate: targetMetrics?.month_target_to_date_ton ?? null,
  weekTargetToDate: targetMetrics?.week_target_to_date_ton ?? null,
  dayTarget: targetMetrics?.day_target_ton ?? null,
  monthTargetTotal: targetMetrics?.month_target_total_ton ?? null,
  weekTargetTotal: targetMetrics?.week_target_total_ton ?? null,
  todayActual: targetMetrics?.day_actual_ton_prev ?? null,
  weekActual: targetMetrics?.week_actual_to_date_ton ?? null,
  monthActual: targetMetrics?.month_actual_to_date_ton ?? null,
});
```

4. **モード切り替えボタンの追加**:

```tsx
{
  /* モード切り替えボタン */
}
<div style={{ marginBottom: layout.gutter }}>
  <Space wrap>
    <Button
      type={achievementMode === "toDate" ? "primary" : "default"}
      onClick={() => setAchievementMode("toDate")}
      size={layout.mode === "mobile" ? "small" : "middle"}
    >
      昨日までの目標に対する達成率
    </Button>
    <Button
      type={achievementMode === "toEnd" ? "primary" : "default"}
      onClick={() => setAchievementMode("toEnd")}
      size={layout.mode === "mobile" ? "small" : "middle"}
    >
      月末・週末目標に対する達成率
    </Button>
  </Space>
</div>;
```

5. **TargetCard の呼び出し変更**:

```tsx
<TargetCard rows={targetCardVM.rows} isoWeek={isoWeek} />
```

---

## 動作確認手順

### 前提条件

- Docker環境が起動している（`make up ENV=local_dev`）
- PostgreSQL に `mart.v_target_card_per_day` と `mart.v_receive_daily` が存在する
- 目標データと実績データが登録されている

### 確認手順

#### 1. バックエンドAPIの動作確認

```bash
# ターミナルで以下を実行
curl -X GET "http://localhost:8001/core_api/dashboard/target?date=2025-11-01&mode=monthly" | jq
```

**期待される結果**:

- レスポンスに以下のフィールドが含まれること
  - `month_target_to_date_ton`
  - `month_target_total_ton`
  - `week_target_to_date_ton`
  - `week_target_total_ton`
  - `month_actual_to_date_ton`
  - `week_actual_to_date_ton`
- 値が数値またはnullであること

**サンプルレスポンス**:

```json
{
  "ddate": "2025-11-16",
  "month_target_ton": 5000.0,
  "week_target_ton": 1200.0,
  "day_target_ton": 200.0,
  "month_actual_ton": 4500.0,
  "week_actual_ton": 1100.0,
  "day_actual_ton_prev": 180.0,
  "month_target_to_date_ton": 3200.0,
  "month_target_total_ton": 5000.0,
  "week_target_to_date_ton": 800.0,
  "week_target_total_ton": 1200.0,
  "month_actual_to_date_ton": 3000.0,
  "week_actual_to_date_ton": 750.0,
  "iso_year": 2025,
  "iso_week": 46,
  "iso_dow": 7,
  "day_type": "sun_hol",
  "is_business": false
}
```

#### 2. フロントエンドUIの動作確認

1. **ブラウザで受入ダッシュボードを開く**

   ```
   http://localhost:3000/dashboard/ukeire
   ```

2. **モード切り替えボタンの表示確認**

   - 月ナビゲーションの下に2つのボタンが表示されること
   - 「昨日までの目標に対する達成率」（デフォルトで選択）
   - 「月末・週末目標に対する達成率」

3. **デフォルトモード（toDate）の確認**

   - 目標カードのラベルが以下であること：
     - "当月目標（昨日まで）"
     - "週目標（昨日まで）"
     - "日目標"
   - 達成率が「昨日までの累計実績 ÷ 昨日までの累計目標」で計算されていること

4. **モード切り替え（toEnd）の確認**

   - 「月末・週末目標に対する達成率」ボタンをクリック
   - 目標カードのラベルが以下に変更されること：
     - "当月最終目標"
     - "週最終目標"
     - "日目標"
   - 目標値（分母）が月末・週末のトータル目標に変更されること
   - 達成率が再計算されること（分母が変わるため、通常は達成率が下がる）

5. **レスポンシブ対応の確認**
   - モバイル: ボタンが small サイズで表示されること
   - デスクトップ: ボタンが middle サイズで表示されること
   - 両モードでレイアウトが崩れないこと

#### 3. 達成率計算の検証

**例**: 11月の場合（昨日 = 11/16と仮定）

| 項目         | toDate モード               | toEnd モード                 |
| ------------ | --------------------------- | ---------------------------- |
| **月目標**   | 3,200t（11/1〜11/16の累計） | 5,000t（11月全体のトータル） |
| **月実績**   | 3,000t（11/1〜11/16の累計） | 3,000t（同じ）               |
| **月達成率** | 3000 ÷ 3200 = **93.8%**     | 3000 ÷ 5000 = **60.0%**      |

**検証ポイント**:

- toDate モードでは「進捗に対する達成度」が分かる
- toEnd モードでは「最終目標に対する進捗度」が分かる
- 同じ実績でも分母が違うため、達成率が異なることを確認

#### 4. エラーハンドリングの確認

1. **APIエラー時**

   - バックエンドを停止 → 「目標データ取得エラー」アラートが表示されること

2. **データ未取得時**

   - ローディング中に「データ読み込み中」アラートが表示されること

3. **NULL値の処理**
   - 目標や実績がNULLの場合、UIで "—" が表示されること
   - 達成率計算が正常に動作すること（0除算エラーが出ないこと）

#### 5. 既存機能への影響確認

- 月ナビゲーションが正常に動作すること
- カレンダー表示が正常に動作すること
- 日次搬入量グラフが正常に動作すること
- 予測カードが正常に動作すること

---

## 技術的なポイント

### 1. 既存テーブルを活用

- `mart.v_target_card_per_day` を利用し、新しいテーブルやカラムの追加は不要
- SQLクエリで集計処理を行い、バックエンドで完結

### 2. 責務の分離

- **Backend**: 目標・実績の集計ロジック
- **ViewModel (useTargetsVM)**: モードに応じた値の切り替え
- **UI (TargetCard)**: 達成率の計算と表示

### 3. 型安全性

- TypeScript の型システムを活用
- `AchievementMode` 型で "toDate" | "toEnd" のみを許可
- DTO/Schema で1:1の型対応

### 4. レスポンシブ対応

- ボタンサイズをレイアウトモードに応じて調整
- Space コンポーネントの wrap で改行対応

### 5. キャッシュ対応

- `useTargetMetrics` のクライアント側キャッシュ（60秒TTL）が有効
- `BuildTargetCardUseCase` のサーバー側キャッシュも有効
- モード切り替え時はキャッシュされたデータを再利用（APIリクエストなし）

---

## トラブルシューティング

### 問題: 達成率が計算されない

**原因**: APIレスポンスに新フィールドが含まれていない

**解決策**:

1. バックエンドのコードが最新か確認
2. Dockerコンテナを再起動
   ```bash
   make down ENV=local_dev
   make up ENV=local_dev
   ```

### 問題: ボタンが表示されない

**原因**: import が不足している

**解決策**:

1. フロントエンドのビルドエラーを確認
   ```bash
   cd app/frontend
   npm run build
   ```
2. ブラウザのキャッシュをクリア（Ctrl+Shift+R）

### 問題: モード切り替え時に値が変わらない

**原因**: useTargetsVM のパラメータマッピングが間違っている

**解決策**:

1. `InboundForecastDashboardPage.tsx` の useTargetsVM 呼び出しを確認
2. `targetMetrics` のフィールド名が正しいか確認
3. ブラウザの開発者ツールで API レスポンスを確認

---

## まとめ

### 実装の特徴

- ✅ 既存のビュー `mart.v_target_card_per_day` をそのまま活用
- ✅ ALTER TABLE などのスキーマ変更は不要
- ✅ クリーンアーキテクチャに準拠（Domain/Application/UI/Infrastructure の分離）
- ✅ SOLID原則に従った実装（単一責任、開放閉鎖原則）
- ✅ 型安全性の確保（TypeScript + Pydantic）
- ✅ 既存機能への影響なし（後方互換性あり）

### 今後の拡張案

- localStorage を使ったモードの永続化
- モードごとの色分け・可視化の強化
- 週次・日次ビューでのモード対応
- モード切り替え時のアニメーション追加

---

**作成者**: GitHub Copilot  
**レビュー**: 要レビュー  
**関連Issue**: N/A
