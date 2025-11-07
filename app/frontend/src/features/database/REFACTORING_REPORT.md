# Database Feature リファクタリング完了報告

## 実施日時
2025-11-07

## 目的
features/database を SOLID 原則に基づいた新しいモジュール構造に再配置し、
状態管理・検証・送信を typeKey ベースで統一。

## 新しいディレクトリ構造

```
src/features/database/
├── shared/
│   ├── csv/
│   │   ├── parseCsv.ts         # CSV解析ユーティリティ
│   │   └── detectEncoding.ts   # エンコーディング検出
│   ├── upload/
│   │   └── buildFormData.ts    # FormData構築
│   ├── types/
│   │   └── common.ts            # 共通型定義
│   ├── dataset/
│   │   └── dataset.ts           # データセット定義とヘルパー
│   ├── ui/
│   │   └── colors.ts            # UIカラー定数
│   ├── constants.ts
│   └── index.ts
├── dataset-import/
│   ├── ui/
│   │   ├── SimpleUploadPanel.tsx
│   │   ├── ValidationBadge.tsx
│   │   └── UploadInstructions.tsx
│   ├── hooks/
│   │   └── useDatasetImportVM.ts  # メインViewModel
│   ├── repository/
│   │   ├── DatasetImportRepository.ts
│   │   └── DatasetImportRepositoryImpl.ts
│   ├── api/
│   │   └── client.ts
│   ├── model/
│   │   ├── types.ts
│   │   └── constants.ts
│   └── index.ts
├── dataset-validate/
│   ├── core/
│   │   ├── csvHeaderValidator.ts  # ヘッダー検証
│   │   └── csvRowValidator.ts     # 行検証（将来用）
│   ├── adapters/
│   │   ├── shogun-flash.validator.ts
│   │   ├── shogun-final.validator.ts
│   │   └── manifest.validator.ts
│   ├── hooks/
│   │   └── useValidateOnPick.ts
│   ├── model/
│   │   ├── rules.ts
│   │   └── types.ts
│   └── index.ts
├── dataset-submit/
│   ├── hooks/
│   │   └── useSubmitVM.ts
│   ├── model/
│   │   └── types.ts
│   └── index.ts
├── dataset-preview/
│   ├── ui/
│   │   └── CsvPreviewCard.tsx
│   ├── model/
│   │   └── types.ts
│   └── index.ts
└── index.ts  # 統合エクスポート

## 主要な変更点

### 1. 責務の分離（SRP）
- **dataset-import**: ファイル選択・UI管理
- **dataset-validate**: CSV検証ロジック（純関数）
- **dataset-submit**: アップロード送信処理
- **dataset-preview**: プレビュー表示
- **shared**: 共通ユーティリティ・型定義

### 2. typeKey による状態管理
- すべての状態管理は `typeKey` (文字列ID) で行う
- `label` は UI 表示専用
- 検証・送信・保存はすべて `typeKey` ベース

### 3. SOLID 原則の適用
- **SRP**: 各モジュールが単一の責務を持つ
- **OCP**: 新しい検証ルールは `adapters/` に追加するだけ
- **DIP**: ViewModel は Repository インターフェースに依存

### 4. メインフック: useDatasetImportVM

```typescript
import { useDatasetImportVM } from '@features/database/dataset-import';
import { collectTypesForDataset } from '@features/database/shared';

const activeTypes = collectTypesForDataset('shogun_flash');
const {
  panelFiles,      // UI表示用データ
  canUpload,       // アップロード可否
  uploading,       // アップロード中フラグ
  onPickFile,      // ファイル選択ハンドラ
  onRemoveFile,    // ファイル削除ハンドラ
  doUpload,        // アップロード実行
} = useDatasetImportVM({ activeTypes });
```

## 互換性対応

旧実装との互換性を保つため、以下を `index.ts` でエクスポート:

```typescript
// 旧フック名でエクスポート
export { useDatasetImportVM as useDatabaseUploadVM } from './dataset-import';

// 旧UIコンポーネント
export { default as CsvUploadPanel } from './ui/cards/CsvUploadPanel';

// 旧hooks
export { useCsvUploadArea } from './model/useCsvUploadArea';
export { useCsvUploadHandler } from './model/useCsvUploadHandler';

// 旧型定義
export type { CsvFileType, CsvUploadCardEntry } from './domain/types';
```

## 使用例

### DatasetImportPage での使用

```tsx
import {
  UploadInstructions,
  SimpleUploadPanel,
  useDatasetImportVM,
  csvTypeColors,
} from '@features/database/dataset-import';
import { collectTypesForDataset } from '@features/database/shared';

const DatasetImportPage = () => {
  const [datasetKey, setDatasetKey] = useState('shogun_flash');
  const activeTypes = collectTypesForDataset(datasetKey);
  
  const {
    panelFiles,
    canUpload,
    uploading,
    onPickFile,
    onRemoveFile,
    doUpload,
  } = useDatasetImportVM({ activeTypes });

  return (
    <>
      <UploadInstructions />
      <SimpleUploadPanel
        items={panelFiles}
        onPickFile={onPickFile}
        onRemoveFile={onRemoveFile}
      />
      <Button 
        disabled={!canUpload || uploading}
        onClick={doUpload}
      >
        アップロード
      </Button>
    </>
  );
};
```

## 検証状況

### ✅ 成功項目
- `pnpm typecheck` で DatasetImportPage および新構造のモジュールがエラーなし
- 新しいディレクトリ構造の作成完了
- メインフック `useDatasetImportVM` の実装完了
- 検証ロジックの分離完了
- Repository パターンの実装完了

### ⚠️ 残課題
- **UploadPage.tsx**: 旧UIコンポーネントを使用しており型エラーあり
  - 対応策: DatasetImportPage への段階的移行を推奨
  - または: UploadPage を新構造に合わせて全面書き換え

- **report機能**: 旧 `CsvFileType` に依存
  - 現在は互換性エクスポートで対応
  - 今後: 新しい `PanelFileItem` への移行を検討

## 次のステップ

1. **UploadPage の対応**
   - オプション A: DatasetImportPage に統合
   - オプション B: 新構造に合わせて全面改修

2. **旧コード削除**
   - `features/database/ui/` (旧UIコンポーネント)
   - `features/database/model/` (旧hooks)
   - `features/database/domain/` (旧型定義)
   - `features/database/hooks/useDatabaseUploadVM.ts`

3. **テスト実行**
   - ブラウザでの動作確認
   - CSV選択→検証→アップロードの一連のフロー確認

4. **ドキュメント整備**
   - 各モジュールの README 追加
   - 使用例とベストプラクティスの記載

## まとめ

新しいモジュール構造により、以下を達成:
- ✅ 責務の明確な分離
- ✅ typeKey ベースの統一的な状態管理
- ✅ SOLID 原則の適用
- ✅ テスト容易性の向上
- ✅ 拡張性の確保

主要な `DatasetImportPage` は新構造で動作可能な状態です。
