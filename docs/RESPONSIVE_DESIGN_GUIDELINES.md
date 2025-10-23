# レスポンシブデザイン設計ガイドライン

このWebアプリケーションにおける、レスポンシブデザインの統一仕様です。

## 📊 ブレークポイント体系

### 1. Ant Design Grid のブレークポイント（実際の動作）

```typescript
// Ant Designが実際に使用するブレークポイント
{
  xs: 0,      // 0px以上
  sm: 576,    // 576px以上
  md: 768,    // 768px以上
  lg: 992,    // 992px以上  ⚠️ プロジェクトのbp.lgと異なる
  xl: 1200,   // 1200px以上
  xxl: 1600   // 1600px以上
}
```

### 2. プロジェクト定義のブレークポイント（breakpoints.ts）

```typescript
// /shared/constants/breakpoints.ts
export const bp = {
  xs: 0,
  sm: 640,   // 小型デバイス（Tailwind準拠）
  md: 768,   // タブレット開始
  lg: 1024,  // 大型タブレット/小型ノートPC
  xl: 1280,  // デスクトップ開始
}

// 実運用の3段階分類
export const BP = {
  mobileMax: 767,     // ≤767px
  tabletMin: 768,     // 768px
  desktopMin: 1200,   // ≥1200px  ⚠️ Ant xlに合わせた値
}
```

---

## 🎯 推奨設計パターン

### パターンA: 2段階レイアウト（モバイル / デスクトップ）

**使用ケース**: シンプルなコンテンツ、フォーム、詳細ページ

```tsx
<Row gutter={[16, 16]}>
  {/* モバイル: 全幅、デスクトップ: 半分 */}
  <Col xs={24} xl={12}>
    <Card>左側コンテンツ</Card>
  </Col>
  <Col xs={24} xl={12}>
    <Card>右側コンテンツ</Card>
  </Col>
</Row>
```

**ブレークポイント**:
- `xs={24}`: 0-1199px（モバイル・タブレット）→ 縦積み
- `xl={...}`: 1200px以上（デスクトップ）→ 横並び

**変数名**: `isMobile` / `isDesktop`（useResponsive）

---

### パターンB: 3段階レイアウト（モバイル / タブレット / デスクトップ）

**使用ケース**: ダッシュボード、カード一覧、グリッド表示

```tsx
<Row gutter={[12, 12]}>
  {items.map(item => (
    <Col xs={24} md={12} xl={8} key={item.id}>
      <Card>{item.content}</Card>
    </Col>
  ))}
</Row>
```

**ブレークポイント**:
- `xs={24}`: 0-767px（モバイル）→ 1列
- `md={12}`: 768-1199px（タブレット）→ 2列
- `xl={8}`: 1200px以上（デスクトップ）→ 3列

**変数名**: `isMobile` / `isTablet` / `isDesktop`

---

### パターンC: 細かい制御（4段階以上）

**使用ケース**: 複雑なダッシュボード、柔軟なレイアウト

```tsx
<Row gutter={[12, 12]}>
  <Col xs={24} sm={12} md={8} lg={6} xl={4}>
    <Card>リッチレイアウト</Card>
  </Col>
</Row>
```

**ブレークポイント**:
- `xs={24}`: 0-575px → 1列
- `sm={12}`: 576-767px → 2列
- `md={8}`: 768-991px → 3列
- `lg={6}`: 992-1199px → 4列
- `xl={4}`: 1200px以上 → 6列

**変数名**: `width`, `isSm`, `isMd`, `isLg`, `isXl`（useResponsive）

---

## 🔧 実装方法

### 1. Ant Design Grid使用時（推奨）

```tsx
import { Row, Col } from "antd";

// パターンA: 2段階（最もシンプル）
<Row gutter={[16, 16]}>
  <Col xs={24} xl={12}>コンテンツ</Col>
</Row>

// パターンB: 3段階（推奨）
<Row gutter={[12, 12]}>
  <Col xs={24} md={12} xl={8}>カード</Col>
</Row>
```

**コメント規約**:
```tsx
{/* モバイル（0-1199px）: 縦積み、デスクトップ（1200px+）: 3列 */}
<Row gutter={[12, 12]}>
  <Col xs={24} xl={8}>...</Col>
  <Col xs={24} xl={8}>...</Col>
  <Col xs={24} xl={8}>...</Col>
</Row>
```

---

### 2. useResponsive Hook使用時

```tsx
import { useResponsive } from "@/shared";

function MyComponent() {
  const { width, isNarrow, isXl } = useResponsive();
  
  // 条件分岐
  if (isNarrow) { // < 1024px
    return <MobileView />;
  }
  
  return <DesktopView />;
}
```

**利用可能なフラグ**:
```typescript
{
  width: number,        // 現在の幅
  isSm: boolean,        // 640-767px
  isMd: boolean,        // 768-1023px
  isLg: boolean,        // 1024-1279px
  isXl: boolean,        // 1280px以上
  isNarrow: boolean,    // < 1024px（モバイル+タブレット）
}
```

---

### 3. カスタムスタイル使用時

```tsx
import { bp } from "@/shared/constants/breakpoints";

const styles = {
  container: {
    padding: "16px",
    [`@media (min-width: ${bp.xl}px)`]: {
      padding: "24px",
    },
  },
};
```

---

## 📏 具体的なpx値とユースケース

### デバイス分類と設計指針

| デバイス分類 | 幅の範囲 | Ant Grid | 設計方針 |
|------------|---------|----------|---------|
| **📱 スマートフォン** | 0-767px | `xs={24}` | 縦積み、フルワイド |
| **📱 大型スマホ** | 576-767px | `sm={...}` | 必要に応じて2列 |
| **📱 タブレット縦** | 768-991px | `md={12}` | 2列レイアウト |
| **💻 タブレット横** | 992-1199px | ~~`lg={...}`~~ 使用注意 | mdかxlを使用 |
| **💻 ノートPC** | 1200-1599px | `xl={8}` | 3列レイアウト |
| **🖥️ デスクトップ** | 1600px以上 | `xxl={6}` | 4列以上 |

---

## ⚠️ 重要な注意事項

### 1. Ant Design `lg` の罠

```typescript
// ❌ 間違い: プロジェクトのbp.lg (1024px) と誤解
<Col xs={24} lg={8}>  // 実際は992pxで切り替わる！

// ✅ 正しい: xl を使用（1200px）
<Col xs={24} xl={8}>  // 意図通り1200pxで切り替わる
```

**理由**: 
- Ant Design `lg` = **992px**
- プロジェクト `bp.lg` = **1024px**
- **32pxのズレ**が発生！

**推奨**: `lg`は極力使わず、`md`（768px）か`xl`（1200px）を使用

---

### 2. useResponsive と Ant Grid の違い

```tsx
// useResponsive の isLg
const { isLg } = useResponsive(); 
// → 1024-1279px を判定（プロジェクト定義）

// Ant Grid の lg
<Col lg={8}>
// → 992px以上で適用（Ant Design定義）
```

**使い分け**:
- **Ant Grid**: レイアウト制御（推奨）
- **useResponsive**: 条件分岐・動的制御

---

## 📋 各ページタイプ別の推奨パターン

### ダッシュボード系（複数カード）

```tsx
// 受入ダッシュボード例
<Row gutter={[12, 12]}>
  <Col xs={24} xl={7}>Target Card</Col>
  <Col xs={24} xl={12}>Daily Chart</Col>
  <Col xs={24} xl={5}>Calendar</Col>
</Row>
```

- **0-1199px**: 縦積み（モバイル・タブレット）
- **1200px+**: 7-12-5列配分

---

### 一覧・グリッド系（繰り返し）

```tsx
// カード一覧
<Row gutter={[12, 12]}>
  {items.map(item => (
    <Col xs={24} md={12} xl={8}>
      <ItemCard {...item} />
    </Col>
  ))}
</Row>
```

- **0-767px**: 1列
- **768-1199px**: 2列
- **1200px+**: 3列

---

### フォーム・詳細系（2分割）

```tsx
// サイドバー + メインコンテンツ
<Row gutter={16}>
  <Col xs={24} xl={6}>
    <Sidebar />
  </Col>
  <Col xs={24} xl={18}>
    <MainContent />
  </Col>
</Row>
```

- **0-1199px**: 縦積み
- **1200px+**: 6:18分割

---

## 🎨 実際のコード例（ベストプラクティス）

### Example 1: シンプルなダッシュボード

```tsx
/**
 * シンプルダッシュボード
 * レスポンシブ: モバイル（縦積み）/ デスクトップ（3列）
 * - xs (0-1199px): 全幅縦積み
 * - xl (1200px+): 3列レイアウト
 */
function SimpleDashboard() {
  return (
    <div style={{ padding: 12 }}>
      <Row gutter={[12, 12]}>
        <Col xs={24} xl={8}>
          <MetricCard title="売上" value="¥1,000,000" />
        </Col>
        <Col xs={24} xl={8}>
          <MetricCard title="受注" value="50件" />
        </Col>
        <Col xs={24} xl={8}>
          <MetricCard title="在庫" value="200個" />
        </Col>
      </Row>
    </div>
  );
}
```

---

### Example 2: 3段階レスポンシブ

```tsx
/**
 * プロダクト一覧
 * レスポンシブ: モバイル（1列）/ タブレット（2列）/ デスクトップ（3列）
 * - xs (0-767px): 1列
 * - md (768-1199px): 2列  
 * - xl (1200px+): 3列
 */
function ProductGrid({ products }) {
  return (
    <Row gutter={[16, 16]}>
      {products.map(product => (
        <Col xs={24} md={12} xl={8} key={product.id}>
          <ProductCard {...product} />
        </Col>
      ))}
    </Row>
  );
}
```

---

### Example 3: Hook併用パターン

```tsx
/**
 * 条件分岐が必要な複雑なレイアウト
 */
function ComplexLayout() {
  const { isNarrow, isXl } = useResponsive();
  
  return (
    <div>
      {/* モバイル・タブレット専用ヘッダー */}
      {isNarrow && <MobileHeader />}
      
      {/* レイアウト */}
      <Row gutter={isXl ? 24 : 12}>
        <Col xs={24} xl={16}>
          <MainContent />
        </Col>
        <Col xs={24} xl={8}>
          {isNarrow ? <MobileSidebar /> : <DesktopSidebar />}
        </Col>
      </Row>
    </div>
  );
}
```

---

## 📝 コーディング規約

### 1. ブレークポイントの書き方

```tsx
// ✅ Good: 小さい順に記述
<Col xs={24} md={12} xl={8}>

// ❌ Bad: 順序がバラバラ
<Col xl={8} xs={24} md={12}>
```

---

### 2. コメントの書き方

```tsx
// ✅ Good: レスポンシブ仕様をコメント
{/* モバイル（0-1199px）: 縦積み、デスクトップ（1200px+）: 2列 */}
<Row gutter={[16, 16]}>
  <Col xs={24} xl={12}>...</Col>
</Row>

// ❌ Bad: コメントなし
<Row gutter={[16, 16]}>
  <Col xs={24} xl={12}>...</Col>
</Row>
```

---

### 3. gutter（余白）の使い分け

```tsx
// デスクトップ: 広めの余白
gutter={[24, 24]}  // 1200px以上

// モバイル/タブレット: 狭めの余白
gutter={[12, 12]}  // 1199px以下

// 動的に切り替え
<Row gutter={isXl ? [24, 24] : [12, 12]}>
```

---

## 🚀 クイックリファレンス

### よく使うパターン

```tsx
// パターン1: 2段階（最頻出）
<Col xs={24} xl={12}>

// パターン2: 3段階（推奨）
<Col xs={24} md={12} xl={8}>

// パターン3: サイドバー分割
<Col xs={24} xl={6}>  // サイド
<Col xs={24} xl={18}> // メイン

// パターン4: 不均等3列
<Col xs={24} xl={7}>  // 左
<Col xs={24} xl={12}> // 中央
<Col xs={24} xl={5}>  // 右
```

---

## 🔍 デバッグ・確認方法

### 1. 現在のブレークポイント確認

```tsx
import { useResponsive } from "@/shared";

function DebugComponent() {
  const { width, isSm, isMd, isLg, isXl, isNarrow } = useResponsive();
  
  return (
    <div style={{ position: 'fixed', top: 0, right: 0, background: 'yellow', padding: 8 }}>
      <div>Width: {width}px</div>
      <div>isSm: {String(isSm)}</div>
      <div>isMd: {String(isMd)}</div>
      <div>isLg: {String(isLg)}</div>
      <div>isXl: {String(isXl)}</div>
      <div>isNarrow: {String(isNarrow)}</div>
    </div>
  );
}
```

---

### 2. Chrome DevTools での確認

1. F12でDevToolsを開く
2. Device Toolbar（Ctrl+Shift+M）を開く
3. 以下の幅で確認:
   - 375px（モバイル）
   - 768px（タブレット）
   - 1200px（デスクトップ）
   - 1600px（大型デスクトップ）

---

## 📚 参考資料

- **Ant Design Grid**: https://ant.design/components/grid
- **Bootstrap Breakpoints**: https://getbootstrap.com/docs/4.0/layout/overview/
- **Tailwind Breakpoints**: https://tailwindcss.com/docs/responsive-design
- **プロジェクトbreakpoints.ts**: `/app/frontend/src/shared/constants/breakpoints.ts`

---

## 📌 まとめ

### 設計時に決めること

1. **何段階のレイアウトが必要か？**
   - 2段階: モバイル/デスクトップ → `xs={24}` + `xl={...}`
   - 3段階: モバイル/タブレット/デスクトップ → `xs={24}` + `md={...}` + `xl={...}`

2. **切り替えポイントはどこか？**
   - **768px（タブレット境界）**: `md`を使用
   - **1200px（デスクトップ境界）**: `xl`を使用
   - ~~992px: `lg`は使用しない（混乱のため）~~

3. **変数名は何を使うか？**
   - `isNarrow`: < 1024px（モバイル+タブレット）
   - `isXl`: ≥ 1280px（デスクトップ）
   - `isMobile`: ≤ 767px（スマホのみ）

### 迷ったら

**👉 `xs={24}` + `xl={8}` を使う（3列レイアウト）**

これが最も汎用的で、このプロジェクトの標準パターンです。
