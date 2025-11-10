# csv-uploader (compat adapter)

旧 `CsvUploadPanelComponent` を互換提供するアダプタ。
内部で `SimpleUploadPanel` と `useDatasetImportVM` に委譲します。

- 目的: 呼び出し側の最小変更で復旧し、段階的に新実装へ移行する。
- 将来方針: 呼び出し箇所を直接 `SimpleUploadPanel` 利用に切替 → 本アダプタ削除。

## 参照元

コミット: `76ab662` (my-project/frontend/src/components/database/CsvUploadPanel.tsx)

## 使用方法

```tsx
import { CsvUploadPanelComponent } from "@/features/csv-uploader";

<CsvUploadPanelComponent
  datasetKey="your-dataset"
  activeTypes={["type1", "type2"]}
/>
```

## 移行計画

1. 既存の呼び出し箇所で動作確認
2. 段階的に `SimpleUploadPanel` + `useDatasetImportVM` への直接呼び出しに置き換え
3. すべての移行が完了したら、本アダプタを削除
