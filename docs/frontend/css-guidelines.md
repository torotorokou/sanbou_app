# CSS ガイドライン

このドキュメントは、本プロジェクトにおける CSS の設計・運用指針を定義します。

## 1. CSS アーキテクチャ

### 1.1 ディレクトリ構成

```
src/
├── app/
│   └── styles/           # グローバルスタイル（単一エントリポイント）
│       ├── index.css     # メインエントリポイント
│       ├── custom-media.css  # @custom-media ルール (自動生成)
│       ├── reset.css     # ブラウザリセット/正規化
│       ├── tokens.css    # デザイントークン (CSS変数)
│       ├── theme.css     # テーマカラー・ブランドカラー
│       ├── antd-overrides.css  # Ant Design グローバルオーバーライド
│       ├── utilities.css # ユーティリティクラス
│       └── globals.css   # その他グローバルスタイル
├── pages/
│   └── [page-name]/
│       └── PageName.module.css   # ページ固有スタイル
└── features/
    └── [feature-name]/
        └── ui/
            └── Component.module.css  # コンポーネント固有スタイル
```

### 1.2 インポート順序

`src/app/styles/index.css` でのインポート順序は以下の通りです：

```css
@import './custom-media.css';    /* 1. カスタムメディアクエリ定義 */
@import './reset.css';           /* 2. ブラウザリセット */
@import './tokens.css';          /* 3. デザイントークン */
@import './theme.css';           /* 4. テーマカラー */
@import './antd-overrides.css';  /* 5. Ant Design オーバーライド */
@import './utilities.css';       /* 6. ユーティリティクラス */
@import './globals.css';         /* 7. その他グローバルスタイル */
```

## 2. CSS Modules

### 2.1 命名規則

- ファイル名: `ComponentName.module.css`
- クラス名: camelCase を使用
  - 良い例: `.pageContainer`, `.headerTitle`, `.primaryButton`
  - 悪い例: `.page-container`, `.header_title`

### 2.2 使用方法

```tsx
// インポート
import styles from './ComponentName.module.css';

// 使用
<div className={styles.container}>
  <h1 className={styles.title}>タイトル</h1>
</div>

// 複数クラスの適用
<div className={`${styles.container} ${isActive ? styles.active : ''}`}>
```

### 2.3 Ant Design との共存

Ant Design コンポーネントのスタイルをオーバーライドする場合は `:global()` を使用します：

```css
/* ComponentName.module.css */
.customCard :global(.ant-card-body) {
  padding: 16px;
}

.customTabs :global(.ant-tabs-nav) {
  margin-bottom: 0;
}
```

## 3. カスタムメディアクエリ

### 3.1 定義

`vite-plugin-custom-media.ts` により `src/shared/constants/breakpoints.ts` から自動生成されます。

利用可能なメディアクエリ：

| メディアクエリ | 説明 |
|---------------|------|
| `--lt-md` | モバイル (≤767px) |
| `--ge-md` | タブレット以上 (≥768px) |
| `--ge-lg` | デスクトップ以上 (≥1024px) |
| `--ge-xl` | 大画面デスクトップ (≥1280px) |
| `--md-only` | タブレットのみ (768-1023px) |
| `--lg-only` | デスクトップのみ (1024-1279px) |

### 3.2 使用方法

```css
/* module.css ファイル内 */
@import '@app/styles/custom-media.css';

.container {
  padding: 16px;
}

@media (--lt-md) {
  .container {
    padding: 8px;
  }
}

@media (--ge-xl) {
  .container {
    max-width: 1280px;
    margin: 0 auto;
  }
}
```

## 4. デザイントークン

### 4.1 CSS 変数

`src/app/styles/tokens.css` でデザイントークンを定義します：

```css
:root {
  /* Colors */
  --color-primary: #1677ff;
  --color-success: #52c41a;
  --color-warning: #faad14;
  --color-error: #ff4d4f;

  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;

  /* Typography */
  --font-size-sm: 12px;
  --font-size-base: 14px;
  --font-size-lg: 16px;
}
```

## 5. ベストプラクティス

### 5.1 DO（推奨）

- ✅ コンポーネント固有のスタイルは `*.module.css` を使用
- ✅ グローバルスタイルは `src/app/styles/` 配下に配置
- ✅ カスタムメディアクエリを使用してレスポンシブ対応
- ✅ CSS 変数（デザイントークン）を活用
- ✅ Ant Design のオーバーライドは `:global()` を使用
- ✅ クラス名は camelCase で記述

### 5.2 DON'T（非推奨）

- ❌ `*.css` (非module) ファイルをコンポーネントに追加しない
- ❌ インラインスタイルの多用（動的な値以外）
- ❌ `!important` の乱用
- ❌ ハードコードされた色やサイズの使用
- ❌ グローバルセレクター（タグセレクター）の使用

## 6. 移行ガイド

### 6.1 非module CSS から module.css への変換

1. ファイル名を `Component.css` → `Component.module.css` に変更
2. クラス名を kebab-case → camelCase に変換
   ```css
   /* Before */
   .my-container { }
   
   /* After */
   .myContainer { }
   ```
3. TSX ファイルのインポートを更新
   ```tsx
   // Before
   import './Component.css';
   <div className="my-container">
   
   // After
   import styles from './Component.module.css';
   <div className={styles.myContainer}>
   ```
4. Ant Design セレクターは `:global()` でラップ
   ```css
   .myComponent :global(.ant-btn) { }
   ```

## 7. main.tsx の CSS インポート

`src/main.tsx` では以下の2つのCSSのみをインポートします：

```tsx
import 'antd/dist/reset.css';
import '@app/styles/index.css';
```

これにより、すべてのグローバルスタイルが `index.css` を通じて統一的に管理されます。

---

最終更新: 2025年1月
