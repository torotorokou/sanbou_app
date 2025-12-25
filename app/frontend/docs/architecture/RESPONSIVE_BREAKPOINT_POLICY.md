# レスポンシブブレイクポイント運用ポリシー

**策定日**: 2024-12-22  
**最終更新**: 2025-12-22（Desktop定義変更）  
**適用範囲**: `app/frontend` 全体  
**目的**: ブレイクポイント判定を3段階に統一し、保守性と一貫性を確保

---

## 🎯 基本方針

### Single Source of Truth

**唯一の定義元**: `src/shared/constants/breakpoints.ts`

すべてのブレイクポイント境界値はこのファイルで定義され、他のファイルはこれを参照する。

---

## 📐 運用3段階の定義（2025-12-22更新）

### 境界値

```typescript
Mobile:  ≤ 767px    (0 〜 767)
Tablet:  768-1280px (768 〜 1280) ★1280を含む
Desktop: ≥ 1281px   (1281 〜 ∞)  ★1280は含まない
```

### ⚠️ 重要変更: Desktop定義の修正

**変更前**: Desktop = ≥1280px  
**変更後**: Desktop = ≥1281px

**理由**:

- **1280px幅はTabletに含める**（多くのノートPC標準解像度）
- Desktopは「十分に広い画面」のみを指す（フルHD以上）
- Tablet上限を1280pxとすることで、サイドバーのデフォルト閉じ動作が1280pxまで適用される

### Tablet の定義（更新）

**Tablet = 768-1280px**（★1280px を含む）

- タブレット端末だけでなく、小型〜中型ノートPC（1024-1280px）も含む
- 「Laptop」という運用判定は作らない（混乱の元）
- 1024-1280px が漏れることで発生するサイドバー不具合を根絶

### 視覚的な境界

```
画面幅:    0     640    768    1024    1280 1281    1920
          │      │      │       │       │   │       │
運用判定: ├─Mobile─────┼──Tablet────────┼──┼Desktop─→
          │   ≤767     │   768-1280    │1281～
          │             │      ★1280含む│
境界:                  768             1280│1281
                                           └─Desktop開始
```

---

## 🔧 技術実装

### 1. 定義箇所

**`src/shared/constants/breakpoints.ts`**:

```typescript
// 5段階詳細（Tailwind準拠）
export const bp = {
  xs: 0,
  sm: 640,
  md: 768, // Mobile/Tablet 境界
  lg: 1024, // 詳細判定用（運用では使わない）
  xl: 1280, // 参考値（Tablet上限）
} as const;

// 運用3段階の境界値（★2025-12-22更新）
export const BP = {
  mobileMax: bp.md - 1, // 767
  tabletMin: bp.md, // 768
  tabletMax: bp.xl, // 1280 ★追加: Tablet上限
  desktopMin: bp.xl + 1, // 1281 ★変更: 1280→1281
} as const;

// 運用判定関数
export const isMobile = (w: number) => w <= BP.mobileMax; // ≤767
export const isTablet = (w: number) => w >= BP.tabletMin && w <= BP.tabletMax; // 768-1280 ★変更
export const isDesktop = (w: number) => w >= BP.desktopMin; // ≥1281 ★変更
```

### 2. 統一Hook

**`src/shared/hooks/ui/useResponsive.ts`**:

```typescript
export type ResponsiveFlags = {
  // 運用3段階（主要な判定に使用）★2025-12-22境界値更新
  isMobile: boolean; // ≤767
  isTablet: boolean; // 768-1280（★1280を含む）
  isDesktop: boolean; // ≥1281（★1280は含まない）

  // 詳細5段階（特殊なUI調整のみ使用可）
  isXs: boolean; // <640
  isSm: boolean; // 640-767
  isMd: boolean; // 768-1023
  isLg: boolean; // 1024-1279
  isXl: boolean; // ≥1280

  // ユーティリティ
  tier: "mobile" | "tablet" | "desktop";
  isNarrow: boolean; // ≤1280（= isMobile || isTablet）★更新
};
```

**重要**: `isTablet` は `isMd || isLg` として実装する

### 3. 使用例

#### ✅ 推奨される実装

```typescript
import { useResponsive } from '@/shared';

function MyComponent() {
  const { flags } = useResponsive();

  if (flags.isMobile) {
    return <MobileView />;
  }
  if (flags.isTablet) {
    return <TabletView />;  // 768-1279px（1024-1279を含む）
  }
  return <DesktopView />;
}
```

#### ✅ レイアウト分岐

```typescript
const padding = flags.isMobile ? 8 : flags.isTablet ? 16 : 24;

const columns = flags.isMobile ? 1 : flags.isTablet ? 2 : 3;
```

#### ✅ 詳細判定が必要な場合

```typescript
// 特殊なUI調整でのみ使用可
const fontSize = flags.isXs
  ? 12
  : flags.isSm
    ? 14
    : flags.isMd
      ? 14
      : flags.isLg
        ? 15
        : 16;

// ただし、基本は3段階で十分
const fontSize = flags.isMobile ? 14 : flags.isTablet ? 15 : 16;
```

---

## ❌ 禁止事項

### 1. window.innerWidth の直参照

```typescript
// ❌ 禁止
if (window.innerWidth < 768) { ... }

// ✅ 正解
const { flags } = useResponsive();
if (flags.isMobile) { ... }
```

### 2. 境界値のハードコード

```typescript
// ❌ 禁止
const isMobile = width <= 767;
const modalWidth = width < 1280 ? 640 : 720;

// ✅ 正解
import { BP } from "@/shared";
const isMobile = width <= BP.mobileMax;
const modalWidth = flags.isTablet ? 640 : 720;
```

### 3. Laptop を運用判定に使用

```typescript
// ❌ 禁止（4段階になり混乱の元）
if (flags.isMobile) { ... }
else if (flags.isTablet) { ... }
else if (flags.isLaptop) { ... }  // ← これは禁止
else if (flags.isDesktop) { ... }

// ✅ 正解（3段階統一）
if (flags.isMobile) { ... }
else if (flags.isTablet) { ... }  // 768-1279を含む
else { ... }  // Desktop
```

### 4. 独自の境界値定義

```typescript
// ❌ 禁止
const TABLET_MAX = 1199;  // 独自定義
if (width < TABLET_MAX) { ... }

// ✅ 正解
import { BP } from '@/shared';
if (width < BP.desktopMin) { ... }
```

---

## 🎨 デザイン指針

### Mobile（≤767px）

- **レイアウト**: 1カラム縦並び
- **ナビゲーション**: Drawer（ハンバーガーメニュー）
- **フォント**: 小さめ（14-16px）
- **間隔**: 狭い（8-12px）
- **タッチターゲット**: 44px以上

### Tablet（768-1280px）★更新

- **レイアウト**: 2カラムまたは可変
- **ナビゲーション**: サイドバー（デフォルトで閉じる）
- **フォント**: 標準（15-16px）
- **間隔**: 標準（12-16px）
- **対象デバイス**: iPad, 小型〜中型ノートPC（1024-1280px含む）, 狭いウィンドウ

**重要**: 1024-1280px もこのカテゴリに含まれる（★1280pxを含む）

### Desktop（≥1281px）★更新

- **レイアウト**: 3カラム、フル機能
- **ナビゲーション**: サイドバー（デフォルトで開く）
- **フォント**: 大きめ（16-18px）
- **間隔**: 広い（16-24px）
- **対象**: フルHD以上のデスクトップPC、大型モニター
- **注意**: 1280px は含まない（1281px から開始）

---

## 🔧 サイドバー挙動の定義

### 運用ルール

```typescript
Mobile (≤767):
  - drawerMode: true  // Drawerとして表示
  - forceCollapse: true  // 強制的に閉じる
  - defaultCollapsed: true

Tablet (768-1279):
  - drawerMode: false  // サイドバー固定
  - forceCollapse: false  // ユーザーが開閉可能
  - defaultCollapsed: true  // デフォルトは閉じる

Desktop (≥1280):
  - drawerMode: false
  - forceCollapse: false
  - defaultCollapsed: false  // デフォルトは開く
```

### 実装（useSidebar.ts）

```typescript
const { isMobile, isTablet, isDesktop } = useResponsive();

if (isMobile) {
  return {
    width: 280,
    collapsedWidth: 0,
    breakpoint: "xs",
    defaultCollapsed: true,
    forceCollapse: true,
    drawerMode: true,
  };
}

if (isTablet) {
  // 768-1279px（1024-1279を含む）
  return {
    width: 230,
    collapsedWidth: 60,
    breakpoint: "md",
    defaultCollapsed: true,
    forceCollapse: false,
    drawerMode: false,
  };
}

// Desktop (≥1281px) ★更新
return {
  width: 250,
  collapsedWidth: 80,
  breakpoint: "xl",
  defaultCollapsed: false,
  forceCollapse: false,
  drawerMode: false,
};
```

---

## 📋 例外ルール

### 許容される例外

1. **shared 層の内部実装**

   - `useResponsive.ts` 内の `window.innerWidth` 参照
   - `breakpoints.ts` 内の数値定義

2. **テスト・デバッグツール**

   - `responsiveTest.ts` などのデバッグ用ツール

3. **CSS変数**

   ```css
   --breakpoint-mobile: 767px;
   --breakpoint-tablet-max: 1280px; /* ★更新 */
   --breakpoint-desktop: 1281px; /* ★更新 */
   ```

   → breakpoints.ts から生成されている場合は許容

4. **コメント内の説明**
   ```typescript
   // Mobile (≤767px) の場合
   // Tablet (768-1280px) の場合 ★更新
   // Desktop (≥1281px) の場合 ★更新
   ```
   → 説明用の数値は削除不要

### 例外申請プロセス

どうしても例外が必要な場合：

1. docs/audits/RESPONSIVE_EXCEPTIONS.md に記録
2. 理由を明記
3. 代替案がないことを証明
4. レビューで承認を得る

**原則**: 例外はゼロを目指す

---

## 🧪 テスト方針（2025-12-22更新）

### 境界値テスト

以下の境界値で動作確認を実施：

- **767px**: Mobile の最大幅
- **768px**: Tablet の最小幅
- **1280px**: Tablet の最大幅（★更新：Tabletに含まれる）
- **1281px**: Desktop の最小幅（★更新：Desktopの開始点）

### 確認項目

1. **サイドバーの挙動**

   - 767px: Drawer、閉じる
   - 768px: 固定サイドバー、閉じる
   - 1280px: 固定サイドバー、閉じる（★更新：Tablet扱い）
   - 1281px: 固定サイドバー、開く（★更新：Desktop開始）

2. **ページレイアウト**

   - 各ページが3段階で正しく分岐
   - 1024-1280px で期待通りの表示（★更新：1280px含む）

3. **レスポンシブフラグ**

   ```typescript
   // 767px
   expect(flags.isMobile).toBe(true);
   expect(flags.isTablet).toBe(false);

   // 768px
   expect(flags.isMobile).toBe(false);
   expect(flags.isTablet).toBe(true);

   // 1280px ★更新：Tablet扱い
   expect(flags.isTablet).toBe(true);
   expect(flags.isDesktop).toBe(false);

   // 1281px ★更新：Desktop開始
   expect(flags.isTablet).toBe(false);
   expect(flags.isDesktop).toBe(true);
   ```

---

## 📚 移行ガイド

### 既存コードの修正手順

#### Step 1: 4段階 → 3段階

```typescript
// 修正前
if (flags.isMobile) return mobile;
if (flags.isTablet) return tablet;
if (flags.isLaptop) return laptop;
return desktop;

// 修正後
if (flags.isMobile) return mobile;
if (flags.isTablet) return tablet; // 768-1279を含む
return desktop;
```

#### Step 2: 直参照 → Hook使用

```typescript
// 修正前
const width = window.innerWidth;
if (width < 768) { ... }

// 修正後
const { flags } = useResponsive();
if (flags.isMobile) { ... }
```

#### Step 3: ハードコード → 定数参照

```typescript
// 修正前
const modalWidth = width < 1280 ? 640 : 720;

// 修正後
import { BP } from "@/shared";
const modalWidth = width < BP.desktopMin ? 640 : 720;

// さらに良い
const modalWidth = flags.isTablet ? 640 : 720;
```

---

## 🎓 ベストプラクティス

### 1. シンプルな分岐

```typescript
// ✅ Good: 明確な3段階
const layout = flags.isMobile ? "stack" : flags.isTablet ? "grid-2" : "grid-3";
```

### 2. 早期リターン

```typescript
// ✅ Good: 読みやすい
if (flags.isMobile) {
  return <MobileView />;
}
if (flags.isTablet) {
  return <TabletView />;
}
return <DesktopView />;
```

### 3. オブジェクトマップ

```typescript
// ✅ Good: 拡張しやすい
const styles = {
  mobile: { padding: 8, fontSize: 14 },
  tablet: { padding: 16, fontSize: 15 },
  desktop: { padding: 24, fontSize: 16 },
};

const tier = flags.isMobile ? 'mobile'
           : flags.isTablet ? 'tablet'
           : 'desktop';

return <div style={styles[tier]} />;
```

### 4. useMemo での最適化

```typescript
// ✅ Good: 再計算を防ぐ
const gridColumns = useMemo(() => {
  if (flags.isMobile) return 1;
  if (flags.isTablet) return 2;
  return 3;
}, [flags.isMobile, flags.isTablet]);
```

---

## 🔄 保守手順

### 新しいページを追加する場合

1. `useResponsive()` をインポート
2. `flags.isMobile` / `flags.isTablet` / `flags.isDesktop` で分岐
3. `isLaptop` は使用しない
4. 境界値をハードコードしない

### 既存ページを修正する場合

1. docs/audits/RESPONSIVE_AUDIT.md で現状確認
2. 4段階判定を3段階に統一
3. 直参照を削除
4. ハードコードを定数参照に置き換え
5. テスト実施

### レビューチェックリスト

- [ ] `window.innerWidth` の直参照がない
- [ ] 境界値のハードコードがない
- [ ] `isLaptop` を運用判定に使用していない
- [ ] 3段階（mobile/tablet/desktop）で分岐している
- [ ] breakpoints.ts を参照している

---

## 📖 関連ドキュメント

- **監査レポート**: `docs/audits/RESPONSIVE_AUDIT.md`
- **ページマトリクス**: `docs/audits/RESPONSIVE_PAGE_MATRIX.md`
- **実装ガイド**: `docs/architecture/20250911_RESPONSIVE_GUIDE.md`
- **FSD規約**: `docs/architecture/20251127_FSD_ARCHITECTURE_GUIDE.md`

---

## ✅ Definition of Done

このポリシーが完全に適用された状態:

1. ✅ 運用判定は3段階のみ（Mobile/Tablet/Desktop）
2. ✅ `window.innerWidth` の直参照が0件（shared除く）
3. ✅ 境界値ハードコードが0件（定義元除く）
4. ✅ サイドバーが全ブレイクポイントで安定動作
5. ✅ pages/ 全体が同じ3段階で統一
6. ✅ 767/768/1279/1280 で挙動が揺れない
7. ✅ `isLaptop` の運用判定使用が0件

---

**最終更新**: 2024-12-22  
**次回レビュー**: リファクタリング完了後
