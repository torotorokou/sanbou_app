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

// 旧UIコンポーネント（report等で使用中 - 非推奨）
export { default as CsvUploadPanel } from './ui/cards/CsvUploadPanel';

// 旧model hooks（非推奨）
export { useCsvUploadArea } from './model/useCsvUploadArea';
export { useCsvUploadHandler } from './model/useCsvUploadHandler';

// 旧型定義の互換性
export type { PanelFileItem, DatasetImportVMOptions as UseDatabaseUploadVMOptions } from './dataset-import/model/types';
export type { ValidationStatus, CsvDefinition, UploadResponseShape } from './shared/types/common';
export type { CsvPreviewData as CsvPreview } from './dataset-preview/model/types';
export type { DatasetKey } from './shared/dataset/dataset';

// 旧domain types（report機能等で使用中 - 非推奨）
export type { CsvFileType, CsvUploadCardEntry } from './domain/types';
