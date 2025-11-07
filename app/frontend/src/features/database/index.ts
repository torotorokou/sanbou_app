/**
 * Database Feature - Public API
 * リファクタリング後の新構造
 */

// Shared
export * from './shared';

// Dataset Import
export * from './dataset-import';

// Dataset Validate
export * from './dataset-validate';

// Dataset Submit
export * from './dataset-submit';

// Dataset Preview
export * from './dataset-preview';

// 旧互換性エクスポート（非推奨 - 段階的に削除予定）
export { useDatasetImportVM as useDatabaseVM } from './dataset-import';
export { useDatasetImportVM as useDatabaseUploadVM } from './dataset-import';
export { CsvPreviewCard } from './dataset-preview';
export { SimpleUploadPanel } from './dataset-import';
export { UploadInstructions } from './dataset-import';
export { ValidationBadge } from './dataset-import';
export { UPLOAD_CSV_DEFINITIONS, UPLOAD_CSV_TYPES, csvTypeColors } from './dataset-import/model/constants';

// 以下の旧実装は削除されました - 新しい実装を使用してください
// export { default as CsvUploadPanel } from './ui/cards/CsvUploadPanel'; // → SimpleUploadPanel を使用
// export { default as CsvUploadPanelComponent } from './ui/components/csv-upload/CsvUploadPanel'; // → SimpleUploadPanel を使用
// export { useCsvUploadArea } from './model/useCsvUploadArea'; // → useDatasetImportVM を使用
// export { useCsvUploadHandler } from './model/useCsvUploadHandler'; // → useDatasetImportVM または useSubmitVM を使用
// export { useCsvValidation } from './domain/services/csvValidationService'; // → useValidateOnPick を使用

// 旧型定義の互換性
export type { PanelFileItem, DatasetImportVMOptions as UseDatabaseUploadVMOptions } from './dataset-import/model/types';
export type { ValidationStatus, CsvDefinition, UploadResponseShape } from './shared/types/common';
export type { CsvPreviewData as CsvPreview } from './dataset-preview/model/types';
export type { DatasetKey } from './shared/dataset/dataset';

// CsvFileType は削除されました - PanelFileItem を使用するか、独自に定義してください
// export type { CsvFileType, CsvUploadCardEntry } from './domain/types';
