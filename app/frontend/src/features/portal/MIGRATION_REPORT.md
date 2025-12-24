# PortalPage - Feature-Sliced Design 移行レポート

## 実施日
2025-12-24

## 概要
PortalPageのリファクタリング済みコードを、プロジェクトのフロントエンド規約に従って`features/portal`ディレクトリに移行しました。

## 移行内容

### 移行前の構造
```
pages/home/
├── PortalPage.tsx (230行)
├── PortalPage.css
├── components/ (4ファイル)
├── config/ (1ファイル)
├── constants/ (1ファイル)
├── hooks/ (1ファイル)
├── types/ (1ファイル)
└── utils/ (1ファイル)
```

### 移行後の構造（Feature-Sliced Design）
```
features/portal/
├── index.ts                      # 公開API
├── ui/                          # View層（4ファイル）
│   ├── PortalCard.tsx
│   ├── CardIcon.tsx
│   ├── CardContent.tsx
│   └── CardButton.tsx
├── model/                       # ViewModel層（3ファイル）
│   ├── types.ts
│   ├── usePortalCardStyles.ts
│   └── colorUtils.ts
├── domain/                      # Domain層（1ファイル）
│   └── constants.ts
└── infrastructure/              # Infrastructure層（1ファイル）
    └── portalMenus.tsx

pages/home/
└── PortalPage.tsx               # ページコンポーネント（統合のみ）
```

## レイヤー分離（VVMC パターン）

### ✅ View層（ui/）
**責務:** 完全に状態レスなViewコンポーネント

| コンポーネント | 役割 |
|--------------|------|
| `PortalCard.tsx` | カード統合コンポーネント |
| `CardIcon.tsx` | アイコン表示 |
| `CardContent.tsx` | コンテンツ（タイトル・説明）表示 |
| `CardButton.tsx` | アクションボタン表示 |

**特徴:**
- propsで値・コールバックを受け取る
- `useState`やAPI呼び出しは禁止
- 純粋な表示ロジックのみ

### ✅ ViewModel層（model/）
**責務:** 画面の状態管理、データ整形、計算ロジック

| ファイル | 役割 |
|---------|------|
| `usePortalCardStyles.ts` | スタイル計算ロジック（カスタムフック） |
| `colorUtils.ts` | 色計算ユーティリティ関数 |
| `types.ts` | 型定義（PortalCardProps, Notice） |

**特徴:**
- カスタムフック形式（`useXxxVM`）
- UIで扱いやすい形にデータを整形
- useMemoによるパフォーマンス最適化

### ✅ Domain層（domain/）
**責務:** ビジネスルール、ドメイン定数

| ファイル | 役割 |
|---------|------|
| `constants.ts` | カードサイズ、カラーパレット定数 |

**特徴:**
- 外部I/Oに依存しない純粋なドメイン知識
- ビジネスルールの表現

### ✅ Infrastructure層（infrastructure/）
**責務:** 設定データ、マスターデータの管理

| ファイル | 役割 |
|---------|------|
| `portalMenus.tsx` | メニュー定義データ |

**特徴:**
- 設定値の一元管理
- 将来的にAPIから取得する場合の拡張ポイント

## 公開API（index.ts）

```typescript
// UI Components
export { PortalCard } from './ui/PortalCard';
export { CardIcon } from './ui/CardIcon';
export { CardContent } from './ui/CardContent';
export { CardButton } from './ui/CardButton';

// Model (ViewModel & Hooks)
export { usePortalCardStyles } from './model/usePortalCardStyles';
export * from './model/colorUtils';
export type { PortalCardProps, Notice } from './model/types';

// Domain
export * from './domain/constants';

// Infrastructure
export { portalMenus } from './infrastructure/portalMenus';
```

## インポートパスの変更

### Before
```typescript
import { PortalCard } from './components/PortalCard';
import { portalMenus } from './config/portalMenus';
import { CARD_WIDTH, CARD_HEIGHT, BUTTON_WIDTH } from './constants/portalConstants';
import type { Notice } from './types/portalTypes';
```

### After
```typescript
import {
  PortalCard,
  portalMenus,
  CARD_WIDTH,
  CARD_HEIGHT,
  BUTTON_WIDTH,
} from '@features/portal';
import type { Notice } from '@features/portal';
```

**改善点:**
- 単一のエントリーポイントからインポート
- パスがシンプルで分かりやすい
- 内部構造の変更に強い

## 規約への準拠

### ✅ Feature-Sliced Design
- 機能ごとにフォルダを分割
- 各レイヤーの責務が明確
- 依存関係が一方向（pages → features）

### ✅ VVMC パターン
- View: 状態レス、表示のみ
- ViewModel: 状態管理・データ整形
- Model: ドメインロジック
- Controller: ページ統合

### ✅ 命名規則
- コンポーネント: `PascalCase`
- フック: `useCamelCase`
- ファイル名: コンポーネント名に一致

### ✅ Export/Import スタイル
- Named Export を使用
- 明示的な re-export
- 型は `import type` を使用

## 移行による利点

### 1. **明確な責務分離**
各レイヤーが明確な役割を持ち、コードの見通しが良い

### 2. **再利用性の向上**
`@features/portal`からインポートするだけで他のページからも利用可能

### 3. **テスタビリティの向上**
各レイヤーを独立してテスト可能

### 4. **保守性の向上**
- 変更箇所が明確
- 影響範囲が限定的
- ドキュメント化が容易

### 5. **規約への準拠**
プロジェクト全体の一貫性が保たれる

### 6. **拡張性の向上**
新機能追加時の拡張ポイントが明確

## ファイルマッピング

| 移行前 | 移行後 | 理由 |
|--------|--------|------|
| `pages/home/types/portalTypes.ts` | `features/portal/model/types.ts` | ViewModelで使用する型 |
| `pages/home/components/*.tsx` | `features/portal/ui/*.tsx` | 状態レスView |
| `pages/home/constants/portalConstants.ts` | `features/portal/domain/constants.ts` | ドメイン定数 |
| `pages/home/utils/colorUtils.ts` | `features/portal/model/colorUtils.ts` | ViewModel用ユーティリティ |
| `pages/home/hooks/usePortalCardStyles.ts` | `features/portal/model/usePortalCardStyles.ts` | ViewModel hooks |
| `pages/home/config/portalMenus.tsx` | `features/portal/infrastructure/portalMenus.tsx` | 設定データ |

## 検証結果

### ✅ TypeScriptエラー
- エラーなし
- 型チェック完全通過

### ✅ インポートパス
- すべてのインポートパスを修正済み
- `@features/portal`からの参照に統一

### ✅ ディレクトリ構造
```
features/portal/
├── index.ts
├── ui/ (4ファイル)
├── model/ (3ファイル)
├── domain/ (1ファイル)
├── infrastructure/ (1ファイル)
└── README.md
```

### ✅ 公開API
- featuresのindex.tsに追加
- 他のモジュールからアクセス可能

## 今後の展開

### すぐに可能な拡張
1. **新メニューの追加**: `infrastructure/portalMenus.tsx`に定義追加
2. **ViewModelの追加**: `model/`に新しいhooksを追加
3. **ドメインロジックの追加**: `domain/`に新しいサービスを追加

### 将来的な拡張
1. **Repository の追加**: APIが必要になれば`ports/`と`infrastructure/`に追加
2. **テストの追加**: 各レイヤーごとに単体テスト実装
3. **Storybook**: UIコンポーネントのドキュメント化

## まとめ

PortalPageのリファクタリング済みコードを、Feature-Sliced Designに従って正しく配置しました。

**成果:**
- ✅ レイヤー分離（VVMC）の完全実装
- ✅ Feature-Sliced Design への準拠
- ✅ 規約に従った命名・構造
- ✅ 公開APIの整備
- ✅ TypeScriptエラーゼロ

**効果:**
- 保守性 ⬆️ （責務が明確）
- 再利用性 ⬆️ （簡単にインポート可能）
- テスタビリティ ⬆️ （レイヤーごとにテスト可能）
- 拡張性 ⬆️ （拡張ポイントが明確）

この移行により、PortalPageは他のfeatureと同様の構造を持ち、プロジェクト全体の一貫性が保たれました。
