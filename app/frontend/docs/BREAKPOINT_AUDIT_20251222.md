# フロントエンド ブレイクポイント監査レポート

**作成日**: 2024-12-22  
**目的**: サイドバーの不具合調査 - 複数のブレイクポイント定義の混在状況を特定

---

## 📊 エグゼクティブサマリー

### 主要な問題

1. **統一定義は存在するが、実装に一貫性がない**
2. **useResponsive の判定ロジックに問題がある可能性**
3. **複数の互換レイヤーが混乱を招いている**

### 影響度

- 🔴 **高**: サイドバーの自動開閉が期待通りに動作しない
- 🟡 **中**: 異なるブレイクポイント定義の混在
- 🟢 **低**: 廃止予定の定数が残存（機能への影響なし）

---

## 🎯 ブレイクポイント定義の現状

### 1. **正式な統一定義** ✅

**ファイル**: `src/shared/constants/breakpoints.ts`

```typescript
export const bp = {
  xs: 0,
  sm: 640, // 小型デバイス
  md: 768, // タブレット開始
  lg: 1024, // 大型タブレット/小型ノートPC
  xl: 1280, // デスクトップ開始
} as const;
```

**3段階の実運用定義（Lean-3）**:

```typescript
export const BP = {
  mobileMax: bp.md - 1, // 767
  tabletMin: bp.md, // 768
  desktopMin: bp.xl, // 1280
} as const;
```

**判定関数**:

```typescript
// ≤767px
export const isMobile = (w: number) => w <= BP.mobileMax;

// 768–1279px
export const isTabletOrHalf = (w: number) =>
  w >= BP.tabletMin && w < BP.desktopMin;

// ≥1280px
export const isDesktop = (w: number) => w >= BP.desktopMin;
```

---

### 2. **useResponsive フック** 🔍

**ファイル**: `src/shared/hooks/ui/useResponsive.ts`

**判定ロジック**:

```typescript
export function makeFlags(w: number): ResponsiveFlags {
  const isXs = w < bp.sm; // < 640
  const isSm = w >= bp.sm && w < bp.md; // 640-767
  const isMd = w >= bp.md && w < bp.lg; // 768-1023
  const isLg = w >= bp.lg && w < bp.xl; // 1024-1279
  const isXl = w >= bp.xl; // ≥1280

  return {
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,
    // グルーピング
    isMobile: isXs || isSm, // ≤767
    isTablet: isMd, // 768-1023  ⚠️ 問題箇所
    isLaptop: isLg, // 1024-1279
    isDesktop: isXl, // ≥1280
    isNarrow: w < bp.xl, // <1280
  };
}
```

#### ⚠️ **重大な問題を発見**

**期待値 vs 実装の不一致**:

| 定義        | 期待範囲 | 実装範囲     | 差分             |
| ----------- | -------- | ------------ | ---------------- |
| `isMobile`  | ≤767     | ≤767         | ✅ 一致          |
| `isTablet`  | 768-1279 | **768-1023** | ❌ **256px不足** |
| `isDesktop` | ≥1280    | ≥1280        | ✅ 一致          |

**問題**: `isTablet`が`isLaptop`（1024-1279px）を含まない！

---

### 3. **useSidebar の設定** 🎛️

**ファイル**: `src/shared/hooks/ui/useSidebar.ts`

```typescript
const { isMobile, isTablet, isDesktop } = useResponsive();

if (isMobile) {
  // ≤767px: Drawerモード、強制的に閉じる
  return { defaultCollapsed: true, forceCollapse: true, drawerMode: true };
}
if (isTablet) {
  // 768-1023px: デフォルトで閉じる ⚠️ 1024-1279px が漏れる
  return { defaultCollapsed: true, forceCollapse: false };
}
// ≥1280px: デフォルトで開く
return { defaultCollapsed: false, forceCollapse: false };
```

#### 🐛 **バグの原因**

**1024-1279px の端末では**:

- `isTablet = false` (1024-1279pxは対象外)
- `isDesktop = false` (1280px未満)
- → **デスクトップ設定（開く）にフォールバック** ❌

**期待動作**: 1024-1279pxでは閉じた状態  
**実際の動作**: 1024-1279pxで開いた状態

---

## 📁 ブレイクポイント使用箇所の分類

### A. 正しく統一フックを使用 ✅

- `Sidebar.tsx`: `useResponsive()` 使用
- `MainLayout.tsx`: `useResponsive()` 使用
- `ReportManagePageLayout.tsx`: `flags` 経由で判定
- 全91件中約80%が正しく実装

### B. 廃止予定定数の残存 🟡

```typescript
// ❌ 非推奨
features/dashboard/ukeire/shared/tokens.ts:
  export const BREAKPOINTS = bp;

features/analytics/sales-pivot/filters/ui/config/layout.config.ts:
  export const BREAKPOINTS = bp;
```

→ コメントで非推奨マーク済み、影響は限定的

### C. 直接的な数値参照 ⚠️

```typescript
// cssVars.ts
--breakpoint-mobile: ${ANT.md - 1}px; /* ≤767 */
--breakpoint-tablet: ${ANT.xl - 1}px; /* 768–1279 */
--breakpoint-auto-collapse: ${ANT.xl}px; /* 1280 */
```

→ CSS変数として適切に定義済み

### D. コンポーネント内のハードコード 🔴

```typescript
// ReportStepperModal.tsx
const modalWidth = isMobile ? '95vw' : isTablet ? 640 : 720;

// ChatMessageCard.tsx
if (windowWidth >= 1024) { ... }

// ManualDetailPage.tsx
const isMobile = (typeof window !== 'undefined') &&
  isMobileWidth(window.innerWidth);
```

→ 少数だが存在、リファクタリング対象

---

## 🔬 根本原因の分析

### 1. **命名の曖昧さ**

- `isTablet`: 文字通り「タブレット」なのか、「デスクトップ以外」なのか不明確
- Lean-3定義では「768-1279px = tablet」だが、実装では「768-1023px」

### 2. **5段階と3段階の混在**

- Tailwind準拠の5段階: xs/sm/md/lg/xl
- 運用上の3段階: mobile/tablet/desktop
- `isTablet`と`isLaptop`の境界が曖昧

### 3. **useSidebarの論理的欠陥**

```typescript
if (isMobile) { ... }
if (isTablet) { ... }  // ← isLaptop が抜ける
return { ... };         // ← フォールバック
```

**正しくは**:

```typescript
if (isMobile) { ... }
if (isTablet || isLaptop) { ... }  // 768-1279px
return { ... };  // ≥1280px
```

---

## 🛠️ 推奨される修正方針

### 🎯 **優先度1: 緊急修正（今すぐ）**

#### A. useResponsiveの修正

```typescript
export function makeFlags(w: number): ResponsiveFlags {
  // ... 既存の5段階判定 ...

  return {
    // 5段階詳細
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,
    tier,

    // 3段階グルーピング（修正版）
    isMobile: isXs || isSm, // ≤767
    isTablet: isMd || isLg, // 768-1279 ← isLgを含める！
    isLaptop: isLg, // 1024-1279（細かい判定用）
    isDesktop: isXl, // ≥1280
    isNarrow: w < bp.xl, // <1280
  };
}
```

#### B. useSidebarの修正

```typescript
// 明示的に3段階判定
const { flags } = useResponsive();
const isNarrowScreen = flags.isMobile || flags.isTablet; // ≤1279

if (flags.isMobile) {
  return { defaultCollapsed: true, forceCollapse: true, drawerMode: true };
}
if (isNarrowScreen) {
  // 768-1279px
  return { defaultCollapsed: true, forceCollapse: false };
}
// ≥1280px
return { defaultCollapsed: false, forceCollapse: false };
```

### 🎯 **優先度2: アーキテクチャ改善（中期）**

#### A. 命名の明確化

```typescript
export type ResponsiveFlags = {
  // 5段階詳細（変更なし）
  isXs: boolean;
  isSm: boolean;
  isMd: boolean;
  isLg: boolean;
  isXl: boolean;

  // 3段階実運用（明確な命名）
  isMobileDevice: boolean; // ≤767 (旧isMobile)
  isTabletOrLaptop: boolean; // 768-1279 (旧isTablet)
  isDesktopWide: boolean; // ≥1280 (旧isDesktop)

  // 互換性維持（@deprecated マーク）
  /** @deprecated 代わりに isMobileDevice を使用 */
  isMobile: boolean;
  /** @deprecated 768-1023pxのみ。768-1279pxは isTabletOrLaptop を使用 */
  isTablet: boolean;
  /** @deprecated 代わりに isDesktopWide を使用 */
  isDesktop: boolean;
};
```

#### B. 段階的な移行計画

1. 新しい命名を追加（互換性維持）
2. コンポーネントを順次移行
3. 旧命名を`@deprecated`マーク
4. 3ヶ月後に旧命名を削除

### 🎯 **優先度3: クリーンアップ（低優先）**

1. 非推奨定数の削除（`BREAKPOINTS`など）
2. ハードコードされた数値の置き換え
3. CSS変数の見直し

---

## 📋 チェックリスト

### 即座に実施

- [ ] `useResponsive.ts`の`makeFlags`を修正（isTabletにisLgを含める）
- [ ] `useSidebar.ts`の判定ロジックを修正
- [ ] 動作確認: 768px, 1024px, 1280pxで検証
- [ ] ユニットテストの追加

### 1週間以内

- [ ] 全コンポーネントでbreakpoint使用状況をレビュー
- [ ] ハードコードされた数値を洗い出し
- [ ] CSS変数の統一性を確認

### 1ヶ月以内

- [ ] 命名の改善提案をチームで議論
- [ ] 移行計画の策定
- [ ] ドキュメントの更新

---

## 🎓 ベストプラクティス

### ✅ 推奨

```typescript
// 統一フックを使用
const { flags } = useResponsive();

if (flags.isMobile) {
  return <MobileView />;
}
if (flags.isTablet || flags.isLaptop) {
  return <TabletView />;
}
return <DesktopView />;
```

### ❌ 非推奨

```typescript
// window.innerWidthを直接参照
if (window.innerWidth < 768) { ... }

// 数値をハードコード
const modalWidth = width < 1024 ? 640 : 720;

// 古い定数を使用
import { BREAKPOINTS } from './tokens';
```

---

## 📚 参考資料

- **Single Source of Truth**: `src/shared/constants/breakpoints.ts`
- **統一フック**: `src/shared/hooks/ui/useResponsive.ts`
- **Tailwind CSS**: https://tailwindcss.com/docs/responsive-design
- **FSD Architecture**: `docs/architecture/20251127_FSD_ARCHITECTURE_GUIDE.md`

---

## 🎯 結論

**根本原因**: `useResponsive`の`isTablet`が768-1023pxのみを対象とし、1024-1279pxが漏れている

**即座の対応**:

1. `makeFlags`で`isTablet`に`isLg`を含める
2. `useSidebar`で`isTablet || isLaptop`を明示的に判定

**長期的改善**:

- 命名を明確化（`isTabletOrLaptop`など）
- 段階的な移行計画の実施
- ドキュメントとテストの充実

これにより、サイドバーが1024-1279pxで正しく閉じた状態になります。
