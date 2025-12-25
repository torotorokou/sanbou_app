# 設定ファイル構造ガイド

**作成日**: 2024-12-02  
**対象**: Feature内の設定ファイル（config/）の標準化

## 概要

このガイドは、各featureにおける設定ファイルの配置と命名規則を定義します。
統一された構造により、新規開発者のオンボーディングを容易にし、保守性を向上させます。

## 標準ディレクトリ構造

### Feature内の設定配置

```
features/[feature-name]/
  ├── config/
  │   ├── index.ts           # バレルエクスポート（公開API）
  │   ├── constants.ts       # 定数定義
  │   ├── types.ts           # 型定義
  │   └── selectors.ts       # 設定取得関数（オプション）
  ├── domain/
  ├── infrastructure/
  └── ui/
```

### 例: Database Feature

```typescript
// features/database/config/index.ts
export * from './datasets';
export * from './types';
export * from './selectors';

// features/database/config/datasets.ts
export const DATASETS = {
  receive: { key: 'receive', label: '受入データ' },
  shipment: { key: 'shipment', label: '出荷データ' },
} as const;

// features/database/config/types.ts
export type DatasetKey = keyof typeof DATASETS;
export interface DatasetConfig {
  key: string;
  label: string;
}

// features/database/config/selectors.ts
export const getDatasetByKey = (key: string) => { ... };
```

## ファイル別の責務

### 1. `index.ts` - バレルエクスポート

**目的**: config/ 内の全てのエクスポートを集約し、外部からの参照を簡潔にする

**ルール**:

- 必ず `export *` または `export { ... }` を使用
- 他のファイルをインポートしない（再エクスポートのみ）
- ドキュメントコメントを追加

```typescript
/**
 * Database Feature - Configuration
 * データセット定義と設定関数
 */

export * from "./datasets";
export * from "./types";
export * from "./selectors";
```

### 2. `constants.ts` - 定数定義

**目的**: feature固有の定数値を集約

**ルール**:

- `UPPER_SNAKE_CASE` で命名
- `as const` で型を固定
- JSDocコメントで説明を追加

```typescript
/**
 * データセット定義
 * CSVアップロード・データベース管理で使用
 */
export const DATASETS = {
  receive: {
    key: "receive",
    label: "受入データ",
    tableName: "receive_records",
  },
  shipment: {
    key: "shipment",
    label: "出荷データ",
    tableName: "shipment_records",
  },
} as const;

/**
 * アップロード設定
 */
export const UPLOAD_CONFIG = {
  maxFileSize: 10 * 1024 * 1024, // 10MB
  allowedExtensions: [".csv", ".xlsx"],
} as const;
```

### 3. `types.ts` - 型定義

**目的**: config関連の型を集約

**ルール**:

- インターフェース、型エイリアス、ユーティリティ型を定義
- constants.ts から型を派生させる場合は `typeof` を使用

```typescript
import { DATASETS } from "./constants";

/**
 * データセットキー型
 */
export type DatasetKey = keyof typeof DATASETS;

/**
 * データセット設定インターフェース
 */
export interface DatasetConfig {
  key: string;
  label: string;
  tableName: string;
}

/**
 * データセットマップ型
 */
export type DatasetMap = typeof DATASETS;
```

### 4. `selectors.ts` - 設定取得関数（オプション）

**目的**: 設定値を取得・加工する純粋関数を提供

**ルール**:

- 全て純粋関数（副作用なし）
- 引数の型は明示的に指定
- JSDocで使用例を記載

````typescript
import { DATASETS, type DatasetKey, type DatasetConfig } from ".";

/**
 * キーからデータセット設定を取得
 *
 * @example
 * ```typescript
 * const config = getDatasetByKey('receive');
 * console.log(config.label); // "受入データ"
 * ```
 */
export function getDatasetByKey(key: DatasetKey): DatasetConfig {
  return DATASETS[key];
}

/**
 * 全データセットの配列を取得
 */
export function getAllDatasets(): DatasetConfig[] {
  return Object.values(DATASETS);
}

/**
 * データセットキーの妥当性チェック
 */
export function isValidDatasetKey(key: string): key is DatasetKey {
  return key in DATASETS;
}
````

## アンチパターン

### ❌ 避けるべきパターン

#### 1. 設定とロジックの混在

```typescript
// ❌ BAD: 設定ファイルにビジネスロジックを含める
export const DATASETS = { ... };

export function processUpload(file: File) {
  // ビジネスロジックは domain/ または infrastructure/ に配置すべき
  return uploadToServer(file);
}
```

#### 2. API呼び出しを含む

```typescript
// ❌ BAD: 設定ファイルでAPI呼び出し
export async function getRemoteConfig() {
  const response = await fetch("/api/config");
  return response.json();
}
```

#### 3. 状態管理を含む

```typescript
// ❌ BAD: 設定ファイルで状態を持つ
let currentDataset = "receive";

export function setCurrentDataset(key: string) {
  currentDataset = key;
}
```

### ✅ 推奨パターン

#### 1. 純粋な設定のみ

```typescript
// ✅ GOOD: 設定は純粋なデータ
export const DATASETS = {
  receive: { key: "receive", label: "受入データ" },
  shipment: { key: "shipment", label: "出荷データ" },
} as const;
```

#### 2. ロジックは適切な層に配置

```typescript
// ✅ GOOD: ビジネスロジックは domain/services に配置
// features/database/domain/services/uploadService.ts
import { DATASETS } from "../../config";

export async function processUpload(datasetKey: DatasetKey, file: File) {
  const dataset = DATASETS[datasetKey];
  // ビジネスロジック
  return uploadToServer(dataset.tableName, file);
}
```

## Shared Config（共有設定）

アプリケーション全体で使用される設定は `app/frontend/src/shared/config/` に配置します。

### 現在のShared Config

```
shared/config/
  ├── index.ts             # バレルエクスポート
  ├── apiEndpoints.ts      # API エンドポイント定義（SSOT）
  └── README.md            # 設定ガイド
```

### Shared Configの使用例

```typescript
// features内から参照
import { REPORT_ENDPOINTS, DASHBOARD_ENDPOINTS } from "@shared/config";

// または
import { REPORT_ENDPOINTS, DASHBOARD_ENDPOINTS } from "@shared";
```

## 設定の優先順位

設定ファイルの配置場所は以下の優先順位で決定します：

1. **Feature固有** → `features/[feature]/config/`

   - 特定のfeatureでのみ使用される設定
   - 例: データセット定義、ページ設定

2. **複数Featureで共有** → `shared/config/`

   - 2つ以上のfeatureで使用される設定
   - 例: APIエンドポイント、共通定数

3. **環境依存** → `環境変数（.env）`
   - 実行環境によって変わる設定
   - 例: API URL、認証キー

## 移行ガイド

既存の設定ファイルを標準構造に移行する手順：

### Step 1: 現状確認

```bash
# 既存の設定ファイルを確認
find features/[feature-name] -name "config*" -o -name "constants*"
```

### Step 2: 構造の作成

```bash
# 標準ディレクトリ構造を作成
mkdir -p features/[feature-name]/config
touch features/[feature-name]/config/{index,constants,types,selectors}.ts
```

### Step 3: 定数の移動

既存の定数を `constants.ts` に移動し、`as const` を追加します。

### Step 4: 型の抽出

定数から型を派生させ、`types.ts` に配置します。

### Step 5: 関数の移動

設定取得関数があれば `selectors.ts` に移動します。

### Step 6: バレルエクスポート

`index.ts` で全てを再エクスポートします。

### Step 7: インポートの更新

既存コードのインポートパスを新しい構造に合わせて更新します。

```typescript
// Before
import { DATASETS } from "../constants/datasets";

// After
import { DATASETS } from "../config";
```

## ベストプラクティス

### 1. 設定は小さく保つ

設定ファイルは100行以内を目安にします。大きくなりすぎた場合は分割を検討してください。

### 2. 型安全性を最大化

`as const` を活用し、TypeScriptの型推論を最大限に利用します。

```typescript
// ✅ GOOD: as const で型を固定
export const DATASETS = {
  receive: { key: "receive", label: "受入データ" },
} as const;

// データセットキー型が自動的に 'receive' のリテラル型になる
type DatasetKey = keyof typeof DATASETS; // 'receive'
```

### 3. ドキュメントを充実させる

JSDocコメントで使用例や注意事項を記載します。

````typescript
/**
 * データセット定義
 *
 * CSVアップロード・データベース管理で使用されます。
 * 新しいデータセットを追加する場合は、以下も更新してください：
 * - backend/core_api/routers/csv.py
 * - docs/database/DATASETS.md
 *
 * @example
 * ```typescript
 * import { DATASETS } from '@features/database/config';
 * const label = DATASETS.receive.label;
 * ```
 */
export const DATASETS = { ... } as const;
````

### 4. マジックナンバーを避ける

数値リテラルは名前付き定数として定義します。

```typescript
// ❌ BAD
if (fileSize > 10485760) { ... }

// ✅ GOOD
export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
if (fileSize > MAX_FILE_SIZE) { ... }
```

## チェックリスト

新しい設定ファイルを作成する際のチェックリスト：

- [ ] `config/` ディレクトリを作成
- [ ] `constants.ts` に定数を定義（`as const` 使用）
- [ ] `types.ts` に型を定義
- [ ] 必要に応じて `selectors.ts` に取得関数を定義
- [ ] `index.ts` でバレルエクスポート
- [ ] JSDocコメントで使用例を記載
- [ ] README.md で設定の概要を説明（オプション）
- [ ] ESLintエラーがないことを確認
- [ ] TypeScriptエラーがないことを確認

## 参考資料

- [FSD Architecture Guide](./FSD_ARCHITECTURE.md)
- [Shared Config README](../../frontend/src/shared/config/README.md)
- [API Endpoints Integration](../../refactoring/20251202_STEP1_API_ENDPOINTS_INTEGRATION.md)

## FAQ

### Q: 設定とビジネスロジックの境界は？

A: 設定は「データ」、ビジネスロジックは「処理」です。設定ファイルには定数と型のみを配置し、処理は `domain/` または `infrastructure/` に配置してください。

### Q: 環境変数はどう扱う？

A: 環境変数は `.env` ファイルで管理し、`import.meta.env` 経由でアクセスします。設定ファイルでラップする場合は、シンプルな値の取得のみに留めてください。

```typescript
// ✅ GOOD: シンプルなラッパー
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// ❌ BAD: 複雑な初期化ロジック
export function initializeApiClient() {
  // 初期化ロジックは infrastructure/ に配置すべき
  return new ApiClient(API_BASE_URL);
}
```

### Q: 複数featureで共有する設定は？

A: 2つ以上のfeatureで使用される設定は `shared/config/` に移動してください。ただし、移動前に本当に共有が必要か検討してください。

### Q: レガシー設定ファイルはどうする？

A: 段階的に移行します。`@deprecated` コメントを追加し、新しい設定へのパスを示してください。

```typescript
/**
 * @deprecated 代わりに @shared/config から REPORT_ENDPOINTS を使用してください
 */
export const LEGACY_ENDPOINTS = { ... };
```
