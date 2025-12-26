# レスポンシブページマトリクス

**作成日**: 2024-12-22  
**目的**: 各ページの3段階レスポンシブ対応を設計・追跡  
**スコープ**: pages/ 配下と主要レイアウト

---

## 📊 マトリクス概要

### ステータス凡例

- ✅ **適合**: 3段階で正しく実装済み
- 🟡 **要修正**: 4段階または直参照あり
- 🔴 **未対応**: レスポンシブ未実装または重大な問題
- ⚪ **対象外**: レスポンシブ不要

---

## 🏗️ レイアウトコンポーネント

### app/layout/

| コンポーネント | ステータス | Mobile (≤767)    | Tablet (768-1279)  | Desktop (≥1280)  | 備考                 |
| -------------- | ---------- | ---------------- | ------------------ | ---------------- | -------------------- |
| **Sidebar**    | 🟡 要修正  | Drawer, 強制閉じ | サイドバー, 閉じる | サイドバー, 開く | isTablet定義修正必要 |
| **MainLayout** | ✅ 適合    | padding: 12px    | padding: 16px      | padding: 24px    | 既に3段階対応        |

#### Sidebar の詳細設計

```typescript
Mobile (≤767px):
  - drawerMode: true
  - forceCollapse: true
  - defaultCollapsed: true
  - width: 0 (閉じた状態)
  - UI: ハンバーガーメニュー → Drawer

Tablet (768-1279px):  ★重要: 1024-1279も含む
  - drawerMode: false
  - forceCollapse: false
  - defaultCollapsed: true
  - width: 60px (折りたたみ) / 230px (展開)
  - UI: 固定サイドバー、デフォルト閉じ

Desktop (≥1280px):
  - drawerMode: false
  - forceCollapse: false
  - defaultCollapsed: false
  - width: 80px (折りたたみ) / 250px (展開)
  - UI: 固定サイドバー、デフォルト開く
```

**修正必要**: `useResponsive` の `isTablet` が 768-1023 になっているため、1024-1279px で Desktop 扱いになる

---

## 📄 Pages 一覧

### pages/home/

| ページ         | ステータス | Mobile       | Tablet      | Desktop     | 修正内容                    |
| -------------- | ---------- | ------------ | ----------- | ----------- | --------------------------- |
| **PortalPage** | 🟡 要修正  | 1列縦並び    | 2列グリッド | 3列グリッド | isLaptop を isTablet に統合 |
| **NewsPage**   | ✅ 適合    | シンプル表示 | 標準表示    | 標準表示    | 問題なし                    |

#### PortalPage の詳細

**現状の問題**:

```typescript
// 現在: 4段階判定
if (flags.isMobile) return mobile;
if (flags.isTablet) return tablet; // 768-1023
if (flags.isLaptop) return laptop; // 1024-1279
return desktop;
```

**修正後**:

```typescript
// 3段階統一
if (flags.isMobile) return mobile; // ≤767
if (flags.isTablet) return tablet; // 768-1279（1024-1279を含む）
return desktop; // ≥1280
```

**レイアウト設計**:

- Mobile: 1列縦並び、カード小さめ
- Tablet: 2列グリッド、カード標準
- Desktop: 3列グリッド、カード大きめ

---

### pages/report/

| ページ             | ステータス | Mobile         | Tablet        | Desktop       | 修正内容            |
| ------------------ | ---------- | -------------- | ------------- | ------------- | ------------------- |
| **ManagePage**     | 🟡 要修正  | 1列表示        | 2列表示       | 3列表示       | isLaptop → isTablet |
| **ReportPage**     | ✅ 適合    | モーダル全画面 | モーダル640px | モーダル720px | 問題なし            |
| **FactoryPage**    | ✅ 適合    | 標準           | 標準          | 標準          | 問題なし            |
| **LedgerBookPage** | ✅ 適合    | 標準           | 標準          | 標準          | 問題なし            |

#### ManagePage の詳細

**現状の問題**:

```typescript
// features/report/manage/ui/ReportManagePageLayout.tsx
// 4段階判定
if (flags.isMobile) return mobile;
if (flags.isTablet) return tablet;
if (flags.isLaptop) return laptop;
return desktop;
```

**修正後**: 3段階統一

**レイアウト設計**:

- Mobile: 1列縦並び（Upload → Preview）
- Tablet: 2列横並び（Upload | Preview）
- Desktop: 3列（Selector | Upload | Preview）

---

### pages/analytics/

| ページ               | ステータス | Mobile               | Tablet       | Desktop             | 修正内容 |
| -------------------- | ---------- | -------------------- | ------------ | ------------------- | -------- |
| **SalesTreePage**    | ✅ 適合    | テーブル横スクロール | テーブル標準 | テーブル + フィルタ | 問題なし |
| **CustomerListPage** | ✅ 適合    | コンパクト表示       | 標準表示     | フル表示            | 問題なし |

**レイアウト設計**:

- Mobile: テーブル横スクロール、フィルタ折りたたみ
- Tablet: テーブル標準、フィルタ表示
- Desktop: フル機能、詳細フィルタ

---

### pages/dashboard/

| ページ                    | ステータス | Mobile | Tablet | Desktop | 修正内容 |
| ------------------------- | ---------- | ------ | ------ | ------- | -------- |
| **ManagementDashboard**   | ✅ 適合    | 1列    | 2列    | 3列     | 問題なし |
| **PlanningDashboard**     | ✅ 適合    | 1列    | 2列    | 3列     | 問題なし |
| **PricingDashboard**      | ✅ 適合    | 1列    | 2列    | 3列     | 問題なし |
| **CustomerListDashboard** | ✅ 適合    | 1列    | 2列    | 3列     | 問題なし |

#### ukeire/InboundForecastDashboardPage

| ページ                           | ステータス | Mobile    | Tablet      | Desktop     | 修正内容                 |
| -------------------------------- | ---------- | --------- | ----------- | ----------- | ------------------------ |
| **InboundForecastDashboardPage** | 🟡 要修正  | 1列縦並び | 上2列+下1列 | 上3列+下1列 | useResponsiveLayout 修正 |

**現状の問題**:

```typescript
// features/dashboard/ukeire/shared/model/useResponsiveLayout.ts
const mode: LayoutMode = flags.isMobile
  ? "mobile"
  : flags.isTablet || flags.isLaptop // ← この判定を統一
    ? "laptopOrBelow"
    : "desktop";
```

**修正後**:

```typescript
const mode: LayoutMode = flags.isMobile
  ? "mobile"
  : flags.isTablet // 768-1279（1024-1279を含む）
    ? "tablet"
    : "desktop";
```

**レイアウト設計**:

- Mobile (≤767): 全て1列縦並び（目標 → カレンダー → 日次 → 予測）
- Tablet (768-1279): 上段2列（目標 | カレンダー）、中段1列（日次）、下段1列（予測）
- Desktop (≥1280): 上段3列（目標 | 日次 | カレンダー）、下段1列（予測）

---

### pages/database/

| ページ                   | ステータス | Mobile               | Tablet | Desktop | 修正内容 |
| ------------------------ | ---------- | -------------------- | ------ | ------- | -------- |
| **DatasetImportPage**    | ✅ 適合    | シンプル             | 標準   | 標準    | 問題なし |
| **RecordListPage**       | ✅ 適合    | テーブル横スクロール | 標準   | フル    | 問題なし |
| **RecordManagerPage**    | ✅ 適合    | コンパクト           | 標準   | フル    | 問題なし |
| **ReservationDailyPage** | ✅ 適合    | 1列                  | 2列    | 3列     | 問題なし |

---

### pages/navi/

| ページ       | ステータス | Mobile | Tablet     | Desktop    | 修正内容 |
| ------------ | ---------- | ------ | ---------- | ---------- | -------- |
| **ChatPage** | ✅ 適合    | 全画面 | サイド表示 | サイド表示 | 問題なし |

**レイアウト設計**:

- Mobile: チャット全画面
- Tablet: サイドパネル（幅40%）
- Desktop: サイドパネル（幅420px）

---

### pages/manual/

| ページ               | ステータス | Mobile                  | Tablet     | Desktop           | 修正内容                 |
| -------------------- | ---------- | ----------------------- | ---------- | ----------------- | ------------------------ |
| **ManualDetailPage** | 🔴 未対応  | window.innerWidth直参照 | 同左       | 同左              | useResponsive に置き換え |
| **SearchPage**       | ✅ 適合    | リスト表示              | リスト表示 | リスト+プレビュー | 問題なし                 |

#### ManualDetailPage の詳細

**現状の問題**:

```typescript
// src/features/manual/ui/components/ManualDetailPage.tsx:20
const isMobile =
  typeof window !== "undefined" && isMobileWidth(window.innerWidth);
```

**修正後**:

```typescript
import { useResponsive } from "@/shared";

const { flags } = useResponsive();
const isMobile = flags.isMobile;
```

---

### pages/settings/

| ページ           | ステータス | Mobile   | Tablet | Desktop | 修正内容 |
| ---------------- | ---------- | -------- | ------ | ------- | -------- |
| **SettingsPage** | ✅ 適合    | シンプル | 標準   | 標準    | 問題なし |

---

### pages/test/ & pages/utils/

| ページ               | ステータス | 備考           |
| -------------------- | ---------- | -------------- |
| **EnvTestPage**      | ⚪ 対象外  | テストページ   |
| **TestPage**         | ⚪ 対象外  | テストページ   |
| **TokenPreviewPage** | ⚪ 対象外  | デバッグツール |

---

## 🎨 Features レイヤー

### 修正が必要な Features

| Feature             | ファイル                       | ステータス | 修正内容                                |
| ------------------- | ------------------------------ | ---------- | --------------------------------------- |
| **report/upload**   | CsvUploadSection.tsx           | 🟡 要修正  | isLaptop → isTablet                     |
| **report/viewer**   | ReportSampleThumbnail.tsx      | 🟡 要修正  | isLaptop → isTablet                     |
| **report/selector** | useReportLayoutStyles.ts       | 🟡 要修正  | isLaptop → isTablet                     |
| **chat**            | ChatMessageCard.tsx            | 🔴 未対応  | windowWidth >= 1024 を flags に置き換え |
| **reservation**     | ReservationMonthlyStats.tsx    | 🟡 要修正  | CSS内数値をCSS変数に                    |
| **reservation**     | ReservationHistoryCalendar.tsx | 🟡 要修正  | CSS内数値をCSS変数に                    |

---

## 📋 修正優先順位

### 🔴 Priority 1: 緊急（根本修正）

1. **src/shared/hooks/ui/useResponsive.ts**

   - `isTablet` を `isMd || isLg` に変更
   - すべての派生ページが自動的に修正される

2. **src/shared/hooks/ui/useSidebar.ts**
   - `isTablet` 定義修正により自動的に修正
   - 念のため動作確認

### 🟡 Priority 2: ページ統一（4段階 → 3段階）

3. **pages/home/PortalPage.tsx**

   - isLaptop 判定を削除
   - isTablet に統合

4. **pages/report/ManagePage.tsx**

   - 同上

5. **features/report/upload/ui/CsvUploadSection.tsx**

   - 同上

6. **features/report/viewer/ui/ReportSampleThumbnail.tsx**

   - 同上

7. **features/report/selector/model/useReportLayoutStyles.ts**

   - 同上

8. **features/dashboard/ukeire/shared/model/useResponsiveLayout.ts**
   - mode 名を "laptopOrBelow" → "tablet" に変更

### 🟢 Priority 3: 直参照削除

9. **features/manual/ui/components/ManualDetailPage.tsx**

   - window.innerWidth → useResponsive()

10. **features/chat/ui/components/ChatMessageCard.tsx**
    - windowWidth >= 1024 → flags.isLaptop または flags.isTablet

### 🔵 Priority 4: CSS統一

11. **features/reservation/reservation-calendar/ui/ReservationMonthlyStats.tsx**

    - @media (min-width: 1280px) → CSS変数

12. **features/reservation/reservation-calendar/ui/ReservationHistoryCalendar.tsx**
    - 同上

---

## ✅ 検証計画

### 手動検証（各ページ）

**検証ブレイクポイント**:

- 767px (Mobile最大)
- 768px (Tablet最小)
- 1024px (旧Laptop開始、新Tablet継続)
- 1279px (Tablet最大)
- 1280px (Desktop最小)

**確認項目**:

1. サイドバー開閉状態
2. レイアウト（1列/2列/3列）
3. フォントサイズ
4. 間隔・余白
5. モーダル幅
6. テーブル表示

### 自動テスト（追加推奨）

```typescript
// src/shared/hooks/ui/useResponsive.spec.ts
describe("useResponsive 3-tier boundaries", () => {
  it("767px should be Mobile", () => {
    const flags = makeFlags(767);
    expect(flags.isMobile).toBe(true);
    expect(flags.isTablet).toBe(false);
  });

  it("768px should be Tablet", () => {
    const flags = makeFlags(768);
    expect(flags.isMobile).toBe(false);
    expect(flags.isTablet).toBe(true);
  });

  it("1024px should still be Tablet", () => {
    const flags = makeFlags(1024);
    expect(flags.isTablet).toBe(true);
    expect(flags.isDesktop).toBe(false);
  });

  it("1279px should be Tablet", () => {
    const flags = makeFlags(1279);
    expect(flags.isTablet).toBe(true);
    expect(flags.isDesktop).toBe(false);
  });

  it("1280px should be Desktop", () => {
    const flags = makeFlags(1280);
    expect(flags.isTablet).toBe(false);
    expect(flags.isDesktop).toBe(true);
  });
});
```

---

## 📊 進捗トラッキング

### 全体統計

| ステータス | ページ数 | 割合 |
| ---------- | -------- | ---- |
| ✅ 適合    | 18       | 75%  |
| 🟡 要修正  | 5        | 21%  |
| 🔴 未対応  | 1        | 4%   |
| ⚪ 対象外  | 3        | -    |

### 修正進捗

- [ ] Priority 1: useResponsive.ts 修正
- [ ] Priority 1: useSidebar.ts 確認
- [ ] Priority 2: PortalPage.tsx
- [ ] Priority 2: ManagePage.tsx
- [ ] Priority 2: CsvUploadSection.tsx
- [ ] Priority 2: ReportSampleThumbnail.tsx
- [ ] Priority 2: useReportLayoutStyles.ts
- [ ] Priority 2: useResponsiveLayout.ts
- [ ] Priority 3: ManualDetailPage.tsx
- [ ] Priority 3: ChatMessageCard.tsx
- [ ] Priority 4: ReservationMonthlyStats.tsx
- [ ] Priority 4: ReservationHistoryCalendar.tsx

---

## 🎯 Definition of Done (ページごと)

各ページが以下を満たすこと:

- [ ] 3段階（Mobile/Tablet/Desktop）のみで分岐
- [ ] `window.innerWidth` 直参照なし
- [ ] 境界値ハードコードなし
- [ ] `isLaptop` を運用判定に使用していない
- [ ] 767/768/1279/1280 で正しく動作
- [ ] レイアウト崩れなし
- [ ] パフォーマンス問題なし

---

## 📚 関連ドキュメント

- **ポリシー**: `docs/architecture/RESPONSIVE_BREAKPOINT_POLICY.md`
- **監査結果**: `docs/audits/RESPONSIVE_AUDIT.md`
- **実装ガイド**: `docs/architecture/20250911_RESPONSIVE_GUIDE.md`

---

**最終更新**: 2024-12-22  
**次回更新**: 各修正完了時
