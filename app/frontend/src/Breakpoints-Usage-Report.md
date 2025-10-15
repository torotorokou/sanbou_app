# Breakpoints Usage Report

**Generated:** 2025-10-15  
**Scope:** `src/` directory (`.css`, `.less`, `.scss`, `.sass`, `.ts`, `.tsx`, `.jsx`)  
**Purpose:** レスポンシブデザインの実装状況を可視化し、統一化・保守性向上のための改善指針を示す

---

## 1. Summary（要約: 主要発見点）

1. **3段運用に収束済み**: `--lt-md` (≤767px), `--md-only` (768–1199px), `--ge-xl` (≥1200px) の3本のcustom mediaトークンが主要な運用パターンとして確立している
2. **ANT Design標準準拠**: ブレークポイントは `breakpoints.ts` で定義された `ANT = {xs:480, sm:576, md:768, lg:992, xl:1200, xxl:1600}` を基準としており、非標準の数値は最小限（1024pxが1箇所のみ）
3. **自動生成の仕組み完備**: `vite-plugin-custom-media.ts` により `breakpoints.ts` を単一の真実源（SSOT）としてcustom mediaが自動生成される優れた設計
4. **未使用トークン多数**: `--bp-sm`, `--bp-lg`, `--bp-xxl` など定義されているが使用されていないトークンが存在し、削減の余地あり
5. **TypeScriptとCSS両方で活用**: `useWindowSize`, `useBreakpoint` などのフックでJS側も同じ閾値を使用しており、一貫性が保たれている

---

## 2. Top Tokens（custom media）上位10

| Rank | Token | 使用頻度 | 説明 |
|------|-------|----------|------|
| 1 | `--lt-md` | 6回 | モバイル（≤767px）※最重要 |
| 2 | `--ge-xl` | 5回 | デスクトップ（≥1200px）※最重要 |
| 3 | `--md-only` | 4回 | タブレット（768–1199px）※最重要 |
| 4 | `--ge-md` | 0回 | 定義済み（768px以上）だが未使用 |
| 5 | `--lt-xl` | 0回 | 定義済み（≤1199px）だが未使用 |
| 6 | `--bp-sm` | 0回 | 定義済み（576px）だが未使用 |
| 7 | `--bp-md` | 0回 | 定義済み（768px）だが未使用 |
| 8 | `--bp-lg` | 0回 | 定義済み（992px）だが未使用 |
| 9 | `--bp-xl` | 0回 | 定義済み（1200px）だが未使用 |
| 10 | `--bp-xxl` | 0回 | 定義済み（1600px）だが未使用 |

**実質的な使用パターン**: **3本のトークン（--lt-md / --md-only / --ge-xl）のみ**が実運用されている

---

## 3. Top Numeric Widths（min/max-widthの数値）上位10

| Rank | 値 | 使用箇所数 | コンテキスト |
|------|------|------------|--------------|
| 1 | 767px | 4回 | `max-width` (--lt-mdの実体: 768-1) |
| 2 | 768px | 4回 | `min-width` (--md-only, --ge-md開始点) |
| 3 | 1199px | 3回 | `max-width` (--md-only, --lt-xl終端: 1200-1) |
| 4 | 1200px | 3回 | `min-width` (--ge-xl, --bp-xl) |
| 5 | 1600px | 1回 | `min-width` (--bp-xxl, 未使用) |
| 6 | 992px | 1回 | `min-width` (--bp-lg, 未使用) |
| 7 | 576px | 1回 | `min-width` (--bp-sm, 未使用) |
| 8 | 1024px | 1回 | `max-width` (PortalPage.cssで例外的使用) |
| 9 | 160px | 1回 | `min-width` (サイドバー最小幅: responsive.css) |
| 10 | 260px | 1回 | `max-width` (サイドバー最大幅: responsive.css) |

**注目点**: 
- 768px と 1200px が最重要な分岐点
- 1024px はANT標準外だが1箇所のみ（PortalPage）で使用され、統一の余地あり

---

## 4. Non-ANT Numeric Widths（既定外の数値と出現数）

**ANT Design既定値**: 480, 576, 768, 992, 1200, 1600

| 値 | 出現数 | ファイル | 理由/用途 |
|----|--------|----------|-----------|
| **1024px** | 1回 | `pages/home/PortalPage.css` | `.portal-hero` の `max-width` – コンテナ幅制限 |
| **767px** | 4回 | `styles/custom-media.css` 他 | `md - 1` の計算値（`max-width` の慣習的な値） |
| **1199px** | 3回 | `styles/custom-media.css` 他 | `xl - 1` の計算値（`max-width` の慣習的な値） |
| **160px** | 1回 | `shared/theme/responsive.css` | サイドバー最小幅（レイアウト固有値） |
| **260px** | 1回 | `shared/theme/responsive.css` | サイドバー最大幅（レイアウト固有値） |

**評価**: 
- 767px/1199px: 標準的な「閾値-1」パターンで問題なし
- **1024px**: 唯一の逸脱候補。1200px（xl）への統一を検討すべき
- 160px/260px: レイアウト固有の値で問題なし

---

## 5. Per-Directory Overview

### 📁 `src/styles/`
- **custom-media.css**: 全custom mediaトークンの定義ファイル（自動生成）
- 使用状況: すべての定義が含まれているが、実際に参照されるのは `--lt-md`, `--md-only`, `--ge-xl` の3本のみ

### 📁 `src/shared/theme/`
- **responsive.css**: グローバルレスポンシブルール（最重要ファイル）
  ```css
  @media (--lt-md) {
    .ant-card { margin: 8px 0; border-radius: 8px; }
    .ant-layout-content { padding: 12px; }
  }
  @media (--md-only) {
    .ant-layout-sider { display: block !important; min-width: 160px; }
  }
  @media (--ge-xl) {
    .ant-card { margin: 16px 0; border-radius: 12px; }
  }
  ```
- **判定**: 3段運用の模範例。コメントで閾値を明記しており保守性高い

### 📁 `src/shared/constants/`
- **breakpoints.ts**: 単一の真実源（SSOT）
  - `ANT` オブジェクトでブレークポイントを定義
  - `isMobile`, `isTabletOrHalf`, `isDesktop` などの判定関数をエクスポート
- **使用パターン**: TypeScriptコード内で `ANT.md`, `ANT.xl` などを直接参照

### 📁 `src/shared/hooks/`
- **useBreakpoint.ts**, **useWindowSize.ts**: 画面幅判定フック
  - `breakpoints.ts` の関数を活用し、React内で一貫した判定を提供
  - 15箇所以上のコンポーネントで利用されている重要な抽象化

### 📁 `src/pages/dashboard/`
- **ManagementDashboard.css**: 3段運用のお手本
  ```css
  @media (--lt-md) { /* モバイル: 自動高さ */ }
  @media (--md-only) { /* タブレット: 柔軟レイアウト */ }
  @media (--ge-xl) { /* デスクトップ: グリッド2列 */ }
  ```
- **monthGrid.module.css**: メディアクエリなし（フレックスボックスで対応）

### 📁 `src/pages/home/`
- **PortalPage.css**: 
  - `max-width: 1024px;` — **唯一の逸脱値**
  - 推奨: `1200px` (xl) に変更し、ANT標準に準拠

### 📁 `src/pages/manual/`
- **shogunManual.module.css**:
  ```css
  @media (--ge-xl) {
    .headerSearchInput { background: var(--ant-color-bg-container); }
  }
  ```
- 使用頻度: 1箇所のみ（軽微な装飾）

### 📁 `src/app/layout/`
- **Sidebar.tsx**: TypeScript側で `ANT.xl`, `ANT.xxl` を参照
  - サイドバー幅を動的調整（xxl未満で0.9倍）
  - CSS側ではなくJSで制御する設計

---

## 6. Hotspots（置換・修正の優先候補）

### 🔥 優先度: 高

#### 1. `src/pages/home/PortalPage.css` (L9)
**現状**:
```css
.portal-hero {
  max-width: 1024px;
}
```
**推奨置換**:
```css
.portal-hero {
  max-width: 1200px; /* ANT.xl に統一 */
}
```
**理由**: 唯一のANT標準外数値。1200pxに統一してデスクトップ閾値と揃える

---

### 🔥 優先度: 中

#### 2. `src/styles/custom-media.css` 全体
**現状**: 全トークンが定義されているが、使用されていないものが多い
```css
@custom-media --bp-sm (min-width: 576px);   /* 未使用 */
@custom-media --bp-md (min-width: 768px);   /* 未使用 */
@custom-media --bp-lg (min-width: 992px);   /* 未使用 */
@custom-media --bp-xl (min-width: 1200px);  /* 未使用 */
@custom-media --bp-xxl (min-width: 1600px); /* 未使用 */
@custom-media --ge-md (min-width: 768px);   /* 未使用 */
@custom-media --lt-xl (max-width: 1199px);  /* 未使用 */
```
**推奨**: 
- **保持すべき3本**: `--lt-md`, `--md-only`, `--ge-xl`
- **削除候補**: `--bp-*` 系統（今後使う予定がなければ）
- **保留**: `--ge-md`, `--lt-xl`（将来の拡張用として残してもOK）

**アクション**: プラグイン `vite-plugin-custom-media.ts` の生成ロジックを調整し、必要最小限のトークンのみ出力するよう変更

---

#### 3. `src/plugins/vite-plugin-custom-media.ts` (L38-54)
**現状**: すべてのブレークポイントをループで出力
```typescript
for (const [k, v] of Object.entries(ANT)) {
  if (k === "xs") continue;
  lines.push(`@custom-media --bp-${k} (min-width: ${v}px);`);
}
```
**推奨**: 使用する3本のみに絞るか、コメントで「未使用」を明示
```typescript
// 実運用トークン（3本のみ）
lines.push(`@custom-media --lt-md (max-width: ${mdMax}px);`);
lines.push(`@custom-media --md-only (min-width: ${md}px) and (max-width: ${xlMax}px);`);
lines.push(`@custom-media --ge-xl (min-width: ${xl}px);`);

// 補助トークン（将来の拡張用）
lines.push(`/* 以下は予備定義（現在未使用） */`);
lines.push(`@custom-media --ge-md (min-width: ${md}px);`);
lines.push(`@custom-media --lt-xl (max-width: ${xlMax}px);`);
```

---

### 🔥 優先度: 低

#### 4. `src/shared/theme/responsive.css` (L36-37)
**現状**: サイドバーの `min-width: 160px; max-width: 260px;`
**評価**: レイアウト固有の値で問題なし（変更不要）

#### 5. `src/index.css` / `src/shared/styles/base.css`
**現状**: `max-width: 100%`, `min-width: 0` など汎用的な値のみ
**評価**: ブレークポイントとは無関係の汎用スタイル（変更不要）

---

## 7. Recommendations（アクションプラン）

### ✅ 即座に実施すべき対応

1. **1024px を 1200px に統一**
   - ファイル: `src/pages/home/PortalPage.css`
   - 変更: `max-width: 1024px;` → `max-width: 1200px;`
   - 効果: ANT標準との完全準拠、デスクトップ閾値の統一

2. **custom media の生成を3本に絞る（オプション）**
   - ファイル: `src/plugins/vite-plugin-custom-media.ts`
   - 変更: 未使用の `--bp-*` 系統を出力しないようにする
   - 効果: 生成CSSファイルの簡素化、保守性向上

### 🔄 中期的な改善案

3. **3段運用の公式化とドキュメント化**
   - ファイル: `docs/RESPONSIVE_GUIDE.md` または `README.md`
   - 内容: 以下のルールを明文化
     ```markdown
     ## レスポンシブブレークポイント運用方針
     
     当プロジェクトでは **3段階のブレークポイント** を標準とします。
     
     | 名称 | custom media | 閾値 | 対象デバイス |
     |------|--------------|------|--------------|
     | モバイル | `@media (--lt-md)` | ≤767px | スマートフォン |
     | タブレット | `@media (--md-only)` | 768–1199px | タブレット、小型PC |
     | デスクトップ | `@media (--ge-xl)` | ≥1200px | デスクトップPC |
     
     ### 具体的な置換表
     - `(max-width: 767px)` → `@media (--lt-md)`
     - `(min-width: 768px) and (max-width: 1199px)` → `@media (--md-only)`
     - `(min-width: 1200px)` → `@media (--ge-xl)`
     ```

4. **未使用トークンの削除判断**
   - `--bp-sm`, `--bp-lg`, `--bp-xxl` など: AntD標準に沿った名前だが、実際には使われていない
   - **保持の理由がなければ削除**: CSSサイズ削減、混乱防止
   - **保持する場合**: コメントで「将来の拡張用、現在未使用」と明記

5. **TypeScript側とCSS側の統一確認**
   - 現状: `breakpoints.ts` を単一の真実源として両方が参照しており、統一済み
   - 継続監視: `vite-plugin-custom-media` の動作確認を定期的に実施

### ⚠️ 注意: やってはいけないこと

- **❌ `--md-only` の削除**: タブレット対応で実際に使用されている（4箇所）
- **❌ 数値の直書きへの戻し**: custom media の抽象化により保守性が向上しているため、数値直書きに戻すのは逆行
- **❌ AntD Grid の `sm`, `lg`, `xxl` の強制使用**: 現在のプロジェクトでは使われておらず、無理に導入する必要なし

---

## 8. Appendix（補足情報）

### スキャン対象統計
- **対象ファイル数**: 472ファイル（.ts, .tsx, .jsx, .css等）
- **メディアクエリ使用ファイル**: 8ファイル
  - CSSファイル: 6個
  - TypeScriptファイル: 15個以上（`breakpoints.ts`を直接import）
- **スキップした長大ファイル**: なし（すべて4000行以内）

### 主要ファイルリスト
1. `src/styles/custom-media.css` — 自動生成（SSOT）
2. `src/shared/constants/breakpoints.ts` — 定義元
3. `src/shared/theme/responsive.css` — グローバルルール
4. `src/pages/dashboard/ManagementDashboard.css` — 3段運用の模範例
5. `src/plugins/vite-plugin-custom-media.ts` — 生成プラグイン

### 定義済みトークン一覧（custom-media.css）
```css
@custom-media --bp-sm (min-width: 576px);
@custom-media --bp-md (min-width: 768px);
@custom-media --bp-lg (min-width: 992px);
@custom-media --bp-xl (min-width: 1200px);
@custom-media --bp-xxl (min-width: 1600px);
@custom-media --lt-md (max-width: 767px);           /* 使用中 */
@custom-media --md-only (min-width: 768px) and (max-width: 1199px); /* 使用中 */
@custom-media --ge-xl (min-width: 1200px);          /* 使用中 */
@custom-media --ge-md (min-width: 768px);
@custom-media --lt-xl (max-width: 1199px);
```

### 判定関数（breakpoints.ts）
```typescript
export const isMobile = (w: number) => w < ANT.md;           // ～767
export const isTabletOrHalf = (w: number) => w >= ANT.md && w < ANT.xl; // 768–1199
export const isDesktop = (w: number) => w >= ANT.xl;        // 1200+
```

---

## 結論

当プロジェクトのレスポンシブ実装は**高い一貫性と保守性**を備えています。

**強み**:
- 単一の真実源（`breakpoints.ts`）による管理
- 自動生成による同期保証
- 実質3段運用への収束（シンプルで理解しやすい）

**改善余地**:
- 1箇所の逸脱値（1024px）の統一
- 未使用トークンの整理
- 運用方針の明文化

上記のアクションプランに従い、小さな改善を重ねることで、さらに堅牢なレスポンシブ設計を実現できます。

---

**Report End** — Questions? → `src/shared/constants/breakpoints.ts` を確認
