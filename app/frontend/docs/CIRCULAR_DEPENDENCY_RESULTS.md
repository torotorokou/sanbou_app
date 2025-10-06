# 🎯 循環依存チェック実行手順 & 結果の見方

## 📋 実行手順（ターミナル）

### ステップ1: フロントエンドディレクトリに移動
```bash
cd /home/koujiro/work_env/22.Work_React/sanbou_app/app/frontend
```

### ステップ2: 循環依存をチェック
```bash
npm run dep:circular
```

または、同じ結果を得る既存のコマンド:
```bash
npm run depcheck
```

### ステップ3: より詳細なグラフを表示（オプション）
```bash
npm run dep:graph
```

---

## 📊 現在の検出結果（2025-10-06）

```
✖ Found 13 circular dependencies!
```

### 🔴 検出された循環依存の内訳

#### 1. **database feature** (1件)
```
features/database/index.ts > features/database/ui/CsvUploadPanel.tsx
```
**問題**: 
- `index.ts` が `CsvUploadPanel.tsx` をエクスポート
- `CsvUploadPanel.tsx` が `index.ts` から型をインポート

**修正方法**:
```typescript
// ❌ 悪い例（循環）
import type { CsvFileType } from '@features/database';

// ✅ 良い例（直接インポート）
import type { CsvFileType } from '@features/database/model/database.types';
```

#### 2. **chat feature** (1件)
```
features/chat/index.ts > features/chat/api/chatService.ts
```
**問題**: バレルファイル経由のインポート

**修正方法**:
```typescript
// chatService.ts 内で index.ts を経由せず、直接インポート
import type { ChatMessage } from './model/chat.types';
```

#### 3. **report feature** (11件) 🚨
```
features/report/index.ts > [様々なファイル]
```
**問題の多くはバレルファイルパターン**:
1. `index.ts` → `useReportBaseBusiness.ts` → `index.ts`
2. `index.ts` → `ReportBase.tsx` → `index.ts`
3. `index.ts` → `ActionsSection.tsx` → `index.ts`
... など11件

---

## 📖 循環依存の見方（詳細解説）

### パターン1: 単純な相互依存
```
A.ts > B.ts > A.ts
```
**読み方**:
- A が B をインポート
- B が A をインポート（戻ってくる）
- これが「輪（cycle）」を作っている

**例**:
```
features/database/index.ts > features/database/ui/CsvUploadPanel.tsx
                          ↑___________________________________|
```

### パターン2: バレルファイル経由の循環
```
index.ts > Component.tsx > index.ts
```
**読み方**:
1. `index.ts` が `Component.tsx` を `export` している
2. `Component.tsx` が `index.ts` から型やユーティリティをインポート
3. 循環が発生

**これが最も多いパターン（report featureの11件）**

### パターン3: 多段階の循環
```
index.ts > A.tsx > B.ts > index.ts
```
**読み方**:
1. `index.ts` が `A.tsx` をエクスポート
2. `A.tsx` が `B.ts` をインポート
3. `B.ts` が `index.ts` から何かをインポート
4. 3段階で元に戻る

**例**:
```
features/report/index.ts > hooks/useReportBaseBusiness.ts > model/useReportArtifact.ts > index.ts
```

---

## 🔧 循環依存の修正方法（優先度順）

### 🥇 方法1: バレルファイルを経由しない（推奨）
**index.ts を経由せず、直接ファイルからインポート**

```typescript
// ❌ 悪い例（バレルファイル経由 = 循環の原因）
import { CsvFileType, useCsvUploadHandler } from '@features/database';

// ✅ 良い例（直接インポート）
import type { CsvFileType } from '@features/database/model/database.types';
import { useCsvUploadHandler } from '@features/database/hooks/useCsvUploadHandler';
```

**メリット**:
- 循環依存を根本的に解決
- バンドルサイズの削減
- ツリーシェイキングの改善

### 🥈 方法2: 型のみのインポートを使用
**`import type` を活用してランタイム依存を減らす**

```typescript
// ❌ 悪い例（値と型を混在）
import { CsvFileType, DEFAULT_CONFIG } from '@features/database';

// ✅ 良い例（型は分離）
import type { CsvFileType } from '@features/database';
import { DEFAULT_CONFIG } from '@features/database/config/constants';
```

### 🥉 方法3: 共通部分を抽出
**循環している部分を shared/ に移動**

```typescript
// 循環の原因となる型を shared/types/ に移動
// src/shared/types/database.ts
export type CsvFileType = 'worker' | 'valuable' | 'shipment';

// 各ファイルから参照
import type { CsvFileType } from '@shared/types/database';
```

---

## 🎯 具体的な修正例（report feature）

### 現状の問題コード
```typescript
// src/features/report/hooks/useReportBaseBusiness.ts
import { CsvConfig, ValidationResult } from '@features/report'; // ❌ 循環!
```

### 修正後のコード
```typescript
// src/features/report/hooks/useReportBaseBusiness.ts
import type { CsvConfig, ValidationResult } from '@features/report/model/report.types'; // ✅ 直接インポート
```

---

## 📈 循環依存がもたらす問題

### 1. **ビルドエラー**
- モジュールの初期化順序が不定になる
- `undefined is not a function` エラーの原因

### 2. **パフォーマンス劣化**
- 不要なコードが含まれる
- ツリーシェイキングが効かない

### 3. **メンテナンス性の低下**
- コードの理解が困難
- リファクタリングがしにくい

---

## ✅ チェックリスト（フォルダ移動後）

```bash
# 1. 循環依存をチェック
npm run dep:circular

# 2. TypeScriptエラーをチェック
npm run build

# 3. ESLintでコード品質をチェック
npm run lint

# 4. すべてクリアなら OK!
```

---

## 🚀 自動化（CI/CD統合）

Pull Request作成時に自動チェック:

```yaml
# .github/workflows/quality-check.yml
name: Code Quality
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - name: Check circular dependencies
        run: npm run dep:circular
      - name: Lint code
        run: npm run lint
      - name: Build
        run: npm run build
```

---

## 🎓 学習リソース

- [Circular Dependencies in JavaScript](https://blog.logrocket.com/circular-dependencies-javascript/)
- [FSD: Isolation Best Practices](https://feature-sliced.design/docs/reference/isolation/circular-dependencies)
- [madge Documentation](https://github.com/pahen/madge)

---

## 📝 まとめ

### 🔍 検出された問題
- **13件の循環依存**を検出
- 主な原因: バレルファイル（`index.ts`）経由のインポート
- 特に `features/report` が重症（11件）

### 🔧 修正の基本方針
1. **バレルファイルを経由しない**（直接インポート）
2. **`import type` を活用**（型のみのインポート）
3. **共通部分は `shared/` に抽出**

### 📋 次のステップ
```bash
# 1. 現状確認
npm run dep:circular

# 2. 修正作業（上記の方法を参考に）

# 3. 再チェック
npm run dep:circular

# 4. クリーンになるまで繰り返す
# 目標: ✔ No circular dependencies found!
```

---

**💡 ヒント**: 循環依存の修正は一度に全部やる必要はありません。重要度の高いものから順番に修正していきましょう！
