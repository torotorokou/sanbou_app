# レスポンシブ実装 変更前監査レポート

**作成日**: 2024-12-22  
**目的**: ブレイクポイント統一リファクタリング前の現状把握  
**スコープ**: `app/frontend/src/` 配下の全ファイル

---

## 📊 監査サマリー

### 検出された問題箇所

| カテゴリ | 検出件数 | 重要度 |
|---------|---------|--------|
| `window.innerWidth` / `matchMedia` 直参照 | 11件 | 🔴 高 |
| 境界値ハードコード (767/768/1024/1279/1280) | 45件 | 🟡 中 |
| レスポンシブフラグ使用 | 219件 | 🟢 低 |
| `isLaptop` を運用判定に使用 | 約15件 | 🔴 高 |

### 重大な問題

1. **`useResponsive` の `isTablet` が 768-1023px のみ**
   - 期待: 768-1279px
   - 実装: 768-1023px（1024-1279px が `isLaptop` に分離）
   - 影響: サイドバーが 1024-1279px で誤動作

2. **運用判定の不統一**
   - 一部ページ: `isMobile` / `isTablet` / `isLaptop` / `isDesktop` の4段階
   - 期待: `isMobile` / `isTablet` / `isDesktop` の3段階

---

## 🔍 詳細監査結果

### A. window.innerWidth / matchMedia 直参照（11件）

#### 🟢 許容（内部実装）
```
src/shared/constants/breakpoints.ts:40
src/shared/constants/breakpoints.ts:43
src/shared/hooks/ui/useResponsive.ts:82
src/shared/hooks/ui/useResponsive.ts:95
src/shared/hooks/ui/useResponsive.ts:104
src/shared/utils/responsiveTest.ts:77
```
→ これらは shared 層の基盤実装であり、問題なし

#### 🔴 修正必要（コンポーネント内直参照）
```typescript
// src/features/manual/ui/components/ManualDetailPage.tsx:20
const isMobile = (typeof window !== 'undefined') && isMobileWidth(window.innerWidth);
```
→ **修正**: `useResponsive()` に置き換え

#### 🟡 コメントのみ（実害なし）
```
src/features/report/selector/model/useReportLayoutStyles.ts:8
src/features/report/viewer/ui/ReportSampleThumbnail.tsx:15
src/features/report/manage/ui/ReportManagePageLayout.tsx:17
src/features/report/base/ui/ReportHeader.tsx:22
```
→ リファクタリング完了の記録コメント、削除不要

---

### B. 境界値ハードコード（45件）

#### 🟢 正当な定義箇所
```typescript
// src/shared/constants/breakpoints.ts
export const bp = {
  xs: 0,
  sm: 640,
  md: 768,    // ← 定義元なのでOK
  lg: 1024,   // ← 定義元なのでOK
  xl: 1280,   // ← 定義元なのでOK
} as const;
```

#### 🟢 適切な参照
```typescript
// src/plugins/vite-plugin-custom-media.ts:35-40
const md = ANT.md;   // 768
const lg = ANT.lg;   // 1024
const xl = ANT.xl;   // 1280
```
→ breakpoints.ts を参照しているのでOK

#### 🟡 コメント内の数値
```typescript
// src/shared/constants/breakpoints.ts:5
// mobile ≤767, tablet 768-1023, desktop-sm 1024-1279, desktop-xl ≥1280
```
→ 説明用コメントは許容

#### 🔴 修正必要（コンポーネント内ハードコード）
```typescript
// src/features/chat/ui/components/ChatMessageCard.tsx:51
if (windowWidth >= 1024) { ... }
```
→ **修正**: `flags.isLaptop` または `flags.isDesktop` に置き換え

```typescript
// src/features/reservation/reservation-calendar/ui/ReservationMonthlyStats.tsx:38
@media (min-width: 1280px) and (max-width: 1399px) { ... }
```
→ **検討**: CSS変数またはbreakpoints参照に置き換え

---

### C. レスポンシブフラグ使用（219件）

#### パターン1: 4段階判定（修正必要）
```typescript
// src/pages/report/ManagePage.tsx:34-37
if (flags.isMobile) return mobile;
if (flags.isTablet) return tablet;
if (flags.isLaptop) return laptop;  // ← これを削除し isTablet に統合
return desktop;
```

**該当ファイル**:
- `src/pages/report/ManagePage.tsx`
- `src/pages/home/PortalPage.tsx`
- `src/features/report/upload/ui/CsvUploadSection.tsx`
- `src/features/report/viewer/ui/ReportSampleThumbnail.tsx`
- `src/features/report/selector/model/useReportLayoutStyles.ts`
- `src/features/dashboard/ukeire/shared/model/useResponsiveLayout.ts`

#### パターン2: 3段階判定（適切）
```typescript
// 既に正しい実装
const { isMobile, isTablet } = useResponsive();
if (isMobile) { ... }
else if (isTablet) { ... }
else { ... }
```

**該当ファイル** (多数):
- `src/app/layout/Sidebar.tsx`
- `src/app/layout/MainLayout.tsx`
- `src/features/report/modal/ui/ReportStepperModal.tsx`
- など約70%が既に正しい実装

#### パターン3: `isNarrow` の使用
```typescript
// src/shared/hooks/ui/useResponsive.ts:70
isNarrow: w < bp.xl,  // <1280
```
→ これは `isMobile || isTablet` と等価なので、明示的に置き換えを推奨

---

### D. isLaptop を運用判定に使用（修正必須）

#### 🔴 重大な問題箇所

```typescript
// src/shared/hooks/ui/useResponsive.ts:67-68
isTablet: isMd,   // 768-1023  ← これが問題の根源
isLaptop: isLg,   // 1024-1279
```

**影響を受けるファイル**:
1. `src/shared/hooks/ui/useSidebar.ts`
   - 現在: `isTablet` のみ判定 → 1024-1279px が漏れる
   - 修正: `isTablet || isLaptop` または `isTablet` の定義を変更

2. `src/pages/report/ManagePage.tsx`
3. `src/pages/home/PortalPage.tsx`
4. `src/features/dashboard/ukeire/shared/model/useResponsiveLayout.ts`
5. `src/features/report/upload/ui/CsvUploadSection.tsx`
6. `src/features/report/viewer/ui/ReportSampleThumbnail.tsx`
7. `src/features/report/selector/model/useReportLayoutStyles.ts`

---

## 🎯 修正対象の優先順位

### 優先度1（緊急・根本修正）

1. **`useResponsive.ts` の `isTablet` 定義変更**
   ```typescript
   // 修正前
   isTablet: isMd,   // 768-1023
   
   // 修正後
   isTablet: isMd || isLg,  // 768-1279
   ```

2. **`useSidebar.ts` の判定ロジック修正**
   ```typescript
   // 現在の問題: isTablet（768-1023）のみ判定
   if (isTablet) { ... }
   
   // 修正後: isTablet（768-1279）で判定
   if (isTablet) { ... }  // isTablet の定義変更により自動的に修正
   ```

### 優先度2（統一性の向上）

3. **4段階判定を3段階に統一**
   - 対象: 約6ファイル
   - 作業: `isLaptop` 判定を `isTablet` に統合

4. **`window.innerWidth` 直参照の削除**
   - 対象: 1ファイル（ManualDetailPage.tsx）
   - 作業: `useResponsive()` に置き換え

### 優先度3（クリーンアップ）

5. **境界値ハードコードの置き換え**
   - 対象: ChatMessageCard.tsx など数件
   - 作業: breakpoints 参照に置き換え

6. **CSS内の数値をCSS変数に統一**
   - 対象: ReservationMonthlyStats.tsx など
   - 作業: 既存CSS変数を活用

---

## 📋 修正チェックリスト

### Phase 1: 基盤修正
- [ ] `useResponsive.ts`: `isTablet` を `isMd || isLg` に変更
- [ ] `useResponsive.ts`: 型定義とコメントを更新
- [ ] `useSidebar.ts`: 判定ロジック確認（自動的に修正される）
- [ ] `breakpoints.spec.ts`: テスト更新

### Phase 2: ページ修正（4段階 → 3段階）
- [ ] `pages/report/ManagePage.tsx`
- [ ] `pages/home/PortalPage.tsx`
- [ ] `features/report/upload/ui/CsvUploadSection.tsx`
- [ ] `features/report/viewer/ui/ReportSampleThumbnail.tsx`
- [ ] `features/report/selector/model/useReportLayoutStyles.ts`
- [ ] `features/dashboard/ukeire/shared/model/useResponsiveLayout.ts`

### Phase 3: 直参照削除
- [ ] `features/manual/ui/components/ManualDetailPage.tsx`

### Phase 4: ハードコード置き換え
- [ ] `features/chat/ui/components/ChatMessageCard.tsx`
- [ ] `features/reservation/reservation-calendar/ui/ReservationMonthlyStats.tsx`
- [ ] `features/reservation/reservation-calendar/ui/ReservationHistoryCalendar.tsx`

### Phase 5: 最終検証
- [ ] ripgrep で残差確認: `window.innerWidth` 0件（shared除く）
- [ ] ripgrep で残差確認: `\b(767|768|1024|1279|1280)\b` 必要最小限
- [ ] ripgrep で残差確認: `isLaptop` を運用分岐に使用 0件
- [ ] 手動テスト: 767/768/1279/1280 での動作確認

---

## 🔬 技術的詳細

### 現在の isTablet 問題の図解

```
画面幅:    0     640    768    1024    1280
          │      │      │       │       │
範囲:     ├──xs──┼──sm──┼──md──┼──lg───┼─xl─→
          │      │      │       │       │
現在:     ├─isMobile────┤isTablet│isLaptop│isDesktop
          │  ≤767       │768-1023│1024-1279│≥1280
          │              │        │         │
期待:     ├─isMobile────┼─isTablet────────┼isDesktop
          │  ≤767       │  768-1279       │≥1280
          │              │                 │
問題:                   ▲ ここが分断されている！
```

### 修正後の構造

```
画面幅:    0     640    768    1024    1280
          │      │      │       │       │
範囲:     ├──xs──┼──sm──┼──md──┼──lg───┼─xl─→
          │      │      │       │       │
運用:     ├─isMobile────┼─isTablet────────┼isDesktop
          │  ≤767       │  768-1279       │≥1280
          │              │                 │
詳細:     ├─isXs┼─isSm─┼─isMd─┼─isLg──┼─isXl
          │(任意使用可) │                 │
```

---

## 📚 関連ドキュメント

- **修正方針**: `docs/architecture/RESPONSIVE_BREAKPOINT_POLICY.md`（次ステップで作成）
- **ページマトリクス**: `docs/audits/RESPONSIVE_PAGE_MATRIX.md`（次ステップで作成）
- **既存監査**: `docs/BREAKPOINT_AUDIT_20251222.md`

---

## ⚠️ 注意事項

1. **shared 層の `window.innerWidth` 参照は正当**
   - `useResponsive.ts` 内部実装として必須
   - `responsiveTest.ts` はデバッグ用ツール

2. **コメント内の数値は許容**
   - 説明用の数値は削除不要

3. **段階的修正が必須**
   - まず `useResponsive.ts` を修正
   - 次にページ単位で順次適用
   - 一括修正は避ける

4. **後方互換性の考慮**
   - `isLaptop` は詳細判定用に残す
   - ただし運用分岐には使用しない
