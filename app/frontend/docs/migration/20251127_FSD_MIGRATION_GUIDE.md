# FSD Refactoring - Migration Guide

**作成日**: 2025-11-20  
**対象**: 既存コードの移行ガイド

---

## 🎯 このガイドの目的

今回のリファクタリングにより、一部のimport文やAPI使用方法が変更されました。  
このガイドでは、既存コードを新しい構造に移行する方法を説明します。

---

## 📋 変更サマリー

| 変更内容    | Before                       | After                      |
| ----------- | ---------------------------- | -------------------------- |
| CSV検証関数 | `@shared`                    | `@features/csv-validation` |
| CsvKind型   | `@/shared`                   | `@features/database`       |
| Job Service | `@shared/infrastructure/job` | `@features/notification`   |

---

## 🔄 Import変更手順

### 1. CSV検証機能

#### useCsvFileValidator

**Before:**

```typescript
import { useCsvFileValidator } from "@shared";
```

**After:**

```typescript
import { useCsvFileValidator } from "@features/csv-validation";
```

**影響範囲:**

- `features/report/base/model/useReportBaseBusiness.ts` ✅ 修正済み

---

#### validateHeaders / parseHeader

**Before:**

```typescript
import { validateHeaders, parseHeader } from "@shared";
```

**After:**

```typescript
import { validateHeaders, parseHeader } from "@features/csv-validation";
```

**影響範囲:**

- `features/csv-validation/core/*` ✅ 修正済み
- `features/csv-validation/hooks/*` ✅ 修正済み

---

### 2. CsvKind型

**Before:**

```typescript
import type { CsvKind } from "@/shared";
```

**After:**

```typescript
import type { CsvKind } from "@features/database/shared/types/common";
// または短縮形
import type { CsvKind } from "@features/database";
```

**影響範囲:**

- `features/database/config/types.ts` ✅ 修正済み
- `features/database/upload-calendar/model/types.ts` ✅ 修正済み
- `features/database/shared/types/common.ts` ✅ 修正済み

---

### 3. Job Service

**Before:**

```typescript
import { pollJob, createAndPollJob } from "@shared/infrastructure/job";
// または
import { pollJob } from "@shared";
```

**After:**

```typescript
import { pollJob, createAndPollJob } from "@features/notification";
```

**使用例:**

```typescript
import { pollJob, JobStatus } from "@features/notification";

async function uploadAndWait(jobId: string) {
  try {
    const result = await pollJob<MyResult>(jobId, (progress, message) => {
      console.log(`進捗: ${progress}% - ${message}`);
    });
    return result;
  } catch (error) {
    // notifyApiError は pollJob 内部で自動的に呼ばれる
    throw error;
  }
}
```

---

## 🔍 自動検索・置換スクリプト

プロジェクト全体で一括置換する場合:

```bash
# CSV検証関連
find src -type f -name "*.ts" -o -name "*.tsx" | \
  xargs sed -i "s|from '@shared'|from '@features/csv-validation'|g" \
  -e "s|useCsvFileValidator|useCsvFileValidator|g"

# CsvKind型
find src -type f -name "*.ts" -o -name "*.tsx" | \
  xargs sed -i "s|from '@/shared';.*CsvKind|from '@features/database';|g"

# Job Service
find src -type f -name "*.ts" -o -name "*.tsx" | \
  xargs sed -i "s|from '@shared/infrastructure/job'|from '@features/notification'|g"
```

> ⚠️ **注意**: 実行前に必ずバックアップを取ってください

---

## 🧪 テストの更新

### モックの変更

**Before:**

```typescript
jest.mock("@shared", () => ({
  useCsvFileValidator: jest.fn(),
}));
```

**After:**

```typescript
jest.mock("@features/csv-validation", () => ({
  useCsvFileValidator: jest.fn(),
}));
```

---

## 📦 新しい公開API一覧

### features/csv-validation

```typescript
// 型定義
export type { CsvValidationStatus, LegacyReportStatus, ValidationResult };

// ユーティリティ
export {
  mapLegacyToCsvStatus,
  mapCsvToLegacyStatus,
  normalizeValidationStatus,
  toLegacyValidationStatus,
};

// UIコンポーネント
export { CsvValidationBadge, type CsvValidationBadgeProps };

// コア関数
export { parseHeader, validateHeaders, validateHeadersFromText };

// Hooks
export { useCsvFileValidator, type CsvFileValidatorOptions };
```

### features/database

```typescript
// CsvKind関連
export type { CsvKind };
export { CsvKindUtils, ALL_CSV_KINDS };

// 設定
export { DATASETS, DATASET_RULES };
export type { DatasetKey, CsvConfig };
```

### features/notification

```typescript
// Job Service
export { pollJob, createAndPollJob, type JobStatus, type JobStatusType };

// 通知機能
export { notifySuccess, notifyError, notifyApiError };
```

---

## 🐛 よくあるエラーと対処法

### Error: Module not found

```
Module '"@shared"' has no exported member 'useCsvFileValidator'
```

**原因**: importパスが古い

**対処法**:

```typescript
// ❌ 古い
import { useCsvFileValidator } from "@shared";

// ✅ 新しい
import { useCsvFileValidator } from "@features/csv-validation";
```

---

### Error: Cannot find module '@features/database/config/datasets'

**原因**: 循環参照を避けるため、一部ファイルが移動

**対処法**:

```typescript
// ❌ 循環参照を引き起こす
import { getRequiredHeaders } from "@features/database/config/datasets";
// csv-validation 内からの参照

// ✅ 正しい方法: database 内で使用
import { getRequiredHeaders } from "../config/datasets";
```

---

### Error: Circular dependency detected

**原因**: Feature間の相互依存

**対処法**:

1. 共通ロジックを `shared` に移動
2. Dependency Injection パターンを使用
3. 型定義のみを別ファイルに分離

```typescript
// ✅ Good: 型定義のみをimport
import type { SomeType } from "@features/other";

// ❌ Bad: 実装をimport
import { SomeFunction } from "@features/other";
```

---

## ✅ 移行チェックリスト

### ステップ1: Import文の確認

- [ ] `@shared` からのCSV検証関連importを検索
- [ ] `@/shared` からのCsvKind importを検索
- [ ] `@shared/infrastructure/job` からのimportを検索

### ステップ2: Import文の修正

- [ ] CSV検証 → `@features/csv-validation`
- [ ] CsvKind → `@features/database`
- [ ] Job Service → `@features/notification`

### ステップ3: ビルド確認

- [ ] `npm run build` を実行
- [ ] 型エラーがないことを確認
- [ ] 警告メッセージを確認

### ステップ4: テスト実行

- [ ] `npm run test` を実行
- [ ] すべてのテストが通ることを確認
- [ ] モックの更新が必要な箇所を修正

### ステップ5: 動作確認

- [ ] 開発サーバーを起動 (`npm run dev`)
- [ ] CSV検証機能が正常に動作することを確認
- [ ] データベース機能が正常に動作することを確認
- [ ] 通知機能が正常に動作することを確認

---

## 🔗 関連ドキュメント

- [FSD Architecture Guide](./FSD_ARCHITECTURE_GUIDE.md)
- [Feature-Sliced Design 公式](https://feature-sliced.design/)

---

## 💬 質問・サポート

移行中に問題が発生した場合:

1. このガイドの「よくあるエラー」セクションを確認
2. [FSD Architecture Guide](./FSD_ARCHITECTURE_GUIDE.md) を参照
3. チームに相談

---

**Last Updated**: 2025-11-20  
**Version**: 1.0.0
