# CSV検証共通機能

## 概要

`features/shared/csv-validation` は、データベース機能とレポート機能の両方で使用される共通のCSV検証ロジックを提供します。

## 機能

### 1. ヘッダー検証

CSVファイルのヘッダー（最初の5列）が期待される形式と一致するかを検証します。

```typescript
import { validateHeaders } from '@features/shared/csv-validation';

const status = await validateHeaders(file, ['列1', '列2', '列3', '列4', '列5']);
// 'valid' | 'invalid' | 'unknown'
```

### 2. CSV検証フック

React コンポーネントで使用できる検証フックを提供します。

```typescript
import { useCsvFileValidator } from '@features/shared/csv-validation';

const validator = useCsvFileValidator({
  getRequiredHeaders: (label) => {
    // ラベルごとに必須ヘッダーを返す
    return ['列1', '列2', '列3', '列4', '列5'];
  },
  onValidate: async (label, file, text) => {
    // カスタム検証ロジック（オプション）
    return true;
  },
});

// ファイルを検証
const status = await validator.validateFile('ファイル名', file);

// 検証結果を取得
const result = validator.getValidationResult('ファイル名');

// 検証結果をリセット
validator.resetValidation('ファイル名');
```

## 型定義

### ValidationStatus

```typescript
type ValidationStatus = 'valid' | 'invalid' | 'unknown';
```

- `valid`: 検証成功
- `invalid`: 検証失敗
- `unknown`: 未検証

### CsvValidationOptions

```typescript
interface CsvValidationOptions {
  requiredHeaders?: string[];
  customValidator?: (text: string) => Promise<boolean>;
}
```

## 使用例

### データベース機能での使用

```typescript
// features/database/dataset-validate/hooks/useValidateOnPick.ts
import { validateHeaders } from '@features/shared/csv-validation';

export function useValidateOnPick(getRequired) {
  return useCallback(async (typeKey, file) => {
    const req = getRequired(typeKey) ?? [];
    if (req.length === 0) return 'unknown';
    return await validateHeaders(file, req);
  }, [getRequired]);
}
```

### レポート機能での使用

```typescript
// features/report/base/model/useReportBaseBusiness.ts
import { useCsvFileValidator } from '@features/shared/csv-validation';

const csvValidation = useCsvFileValidator({
  getRequiredHeaders: (label) => {
    const entry = csvConfigs.find(c => c.config.label === label);
    return entry?.config.expectedHeaders;
  },
});

// ファイル検証
await csvValidation.validateFile(label, file);
```

## 検証ルール

1. **ヘッダー検証**: 最初の5列のヘッダーが必須ヘッダーと完全一致するか確認
2. **順序チェック**: ヘッダーの順序も検証対象
3. **空白処理**: ヘッダーの前後の空白はトリム処理される
4. **カスタム検証**: 必要に応じて追加の検証ロジックを実装可能

## 依存関係

- React (useState, useCallback)
- TypeScript

## メリット

1. **コードの重複削減**: 検証ロジックを一箇所に集約
2. **保守性向上**: 検証ルールの変更が一箇所で完結
3. **再利用性**: 任意の機能から使用可能
4. **型安全性**: TypeScriptによる型チェック
5. **テスタビリティ**: 独立したロジックとしてテスト可能

## 今後の拡張案

- [ ] バリデーションエラーの詳細メッセージ
- [ ] 行単位のバリデーション
- [ ] データ型検証（数値、日付など）
- [ ] 必須フィールドチェック
- [ ] カスタムルールの拡張API
