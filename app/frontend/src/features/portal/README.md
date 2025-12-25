# Portal Feature - Feature-Sliced Design への移行

## 概要

PortalPageのリファクタリング後のコードを、Feature-Sliced Design（FSD）に従って`features/portal`ディレクトリに移行しました。

## ディレクトリ構造

### 移行前（pages/home）

```
pages/home/
├── PortalPage.tsx
├── PortalPage.css
├── components/          # UIコンポーネント
├── config/              # 設定
├── constants/           # 定数
├── hooks/               # カスタムフック
├── types/               # 型定義
└── utils/               # ユーティリティ
```

### 移行後（features/portal）

```
features/portal/
├── index.ts                      # Public API
├── ui/                          # View層（状態レス）
│   ├── PortalCard.tsx
│   ├── CardIcon.tsx
│   ├── CardContent.tsx
│   └── CardButton.tsx
├── model/                       # ViewModel層
│   ├── types.ts                 # 型定義
│   ├── usePortalCardStyles.ts   # スタイル計算ViewModel
│   └── colorUtils.ts            # 色計算ユーティリティ
├── domain/                      # Domain層
│   └── constants.ts             # ドメイン定数（サイズ、パレット）
└── infrastructure/              # Infrastructure層
    └── portalMenus.tsx          # メニュー定義（設定データ）

pages/home/
└── PortalPage.tsx               # ページコンポーネント（統合）
```

## レイヤー分離（VVMC パターン）

### View（V） - `ui/`

完全に状態レスなViewコンポーネント

- `PortalCard.tsx` - カード統合コンポーネント
- `CardIcon.tsx` - アイコン表示
- `CardContent.tsx` - コンテンツ表示
- `CardButton.tsx` - ボタン表示

**特徴:**

- propsで値・コールバックを受け取る
- `useState`やAPI呼び出しは禁止
- 表示ロジックに専念

### ViewModel（VM） - `model/`

画面の状態・イベント管理、データ整形

- `usePortalCardStyles.ts` - スタイル計算ロジック
- `colorUtils.ts` - 色計算ユーティリティ
- `types.ts` - ViewModel用の型定義

**特徴:**

- カスタムフック（`useXxxVM`形式）
- UIで扱いやすい形にデータを整形
- 軽いビジネスロジックを含む

### Model（M） - `domain/` & `infrastructure/`

ドメインロジックとデータアクセス

#### domain/

- `constants.ts` - カードサイズ、カラーパレット等の定数
- ドメインオブジェクト、値オブジェクト（今後追加可能）

#### infrastructure/

- `portalMenus.tsx` - メニュー定義データ
- 設定・マスターデータの管理

**特徴:**

- 外部I/O（HTTP・localStorage等）に依存しない純粋なドメインロジック
- ビジネスルールを表現

### Controller（C） - `pages/`

ルーティングと画面構成

- `PortalPage.tsx` - ページの骨組み、ViewModelの統合

**特徴:**

- URLとコンポーネントの結びつけ
- どのViewModelを使うかの選択
- ビジネスロジックは持たない

## インポート構造

### 公開API（index.ts）

```typescript
// UI Components
export { PortalCard } from "./ui/PortalCard";
export { CardIcon } from "./ui/CardIcon";
export { CardContent } from "./ui/CardContent";
export { CardButton } from "./ui/CardButton";

// Model (ViewModel & Hooks)
export { usePortalCardStyles } from "./model/usePortalCardStyles";
export * from "./model/colorUtils";
export type { PortalCardProps, Notice } from "./model/types";

// Domain
export * from "./domain/constants";

// Infrastructure
export { portalMenus } from "./infrastructure/portalMenus";
```

### ページからの利用

```typescript
// PortalPage.tsx
import {
  PortalCard,
  portalMenus,
  CARD_WIDTH,
  CARD_HEIGHT,
  BUTTON_WIDTH,
} from "@features/portal";
import type { Notice } from "@features/portal";
```

## 移行による利点

### 1. **明確な責務分離**

各レイヤーが明確な役割を持つ

- UI: 表示のみ
- Model: 状態管理・データ整形
- Domain: ビジネスルール
- Infrastructure: データ取得・設定

### 2. **依存関係の整理**

```
pages → features (外部から内部への単方向依存)
  features/portal/
    ui → model → domain ← infrastructure
```

### 3. **再利用性の向上**

- `@features/portal`からインポートするだけで利用可能
- 他のページやfeatureからも簡単に参照

### 4. **テスタビリティの向上**

- 各レイヤーを独立してテスト可能
- モックの注入が容易

### 5. **規約への準拠**

- Feature-Sliced Design のベストプラクティスに従う
- プロジェクト全体の一貫性が保たれる

## ファイルマッピング

| 移行前                         | 移行後                           | 理由                      |
| ------------------------------ | -------------------------------- | ------------------------- |
| `types/portalTypes.ts`         | `model/types.ts`                 | ViewModelで使用する型     |
| `components/*.tsx`             | `ui/*.tsx`                       | 状態レスView              |
| `constants/portalConstants.ts` | `domain/constants.ts`            | ドメイン定数              |
| `utils/colorUtils.ts`          | `model/colorUtils.ts`            | ViewModel用ユーティリティ |
| `hooks/usePortalCardStyles.ts` | `model/usePortalCardStyles.ts`   | ViewModel hooks           |
| `config/portalMenus.tsx`       | `infrastructure/portalMenus.tsx` | 設定データ                |

## 使用例

```typescript
// 他のページから利用する場合
import { PortalCard, portalMenus } from '@features/portal';

function MyCustomPage() {
  return (
    <div>
      {portalMenus.map(menu => (
        <PortalCard key={menu.link} {...menu} />
      ))}
    </div>
  );
}
```

## 今後の拡張

Feature-Sliced Design により、以下の拡張が容易に：

1. **新機能の追加**: `infrastructure/portalMenus.tsx`に定義を追加
2. **ViewModelの追加**: `model/`に新しいhooksを追加
3. **ドメインロジックの追加**: `domain/`に新しいサービスを追加
4. **Repository の追加**: 将来的にAPIが必要になれば`ports/`と`infrastructure/`を追加

## 参考資料

- [Feature-Sliced Design 公式](https://feature-sliced.design/)
- プロジェクト規約: `/docs/conventions/frontend/20251127_webapp_development_conventions_frontend.md`
