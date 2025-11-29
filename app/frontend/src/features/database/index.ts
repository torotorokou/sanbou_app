/**
 * Database Feature - Public API
 * リファクタリング後の新構造
 */

// Config (新規追加 - 一元管理されたデータセット設定)
export * from './config';

// Shared (個別エクスポートで重複を回避)
export * from './shared/constants';
export * from './shared/types/common';
export * from './shared/csv/parseCsv';
export * from './shared/csv/detectEncoding';
export * from './shared/ui/colors';
export * from './shared/upload/buildFormData';
// dataset/dataset.ts は deprecated なので config を優先

// Dataset Import
export * from './dataset-import';

// Dataset Submit
export * from './dataset-submit';

// Dataset Preview
export * from './dataset-preview';

// 旧互換性エクスポート（非推奨 - 段階的に削除予定）
export { useDatasetImportVM as useDatabaseVM } from './dataset-import';
export { useDatasetImportVM as useDatabaseUploadVM } from './dataset-import';
export { CsvPreviewCard } from './dataset-preview';
export { SimpleUploadPanel } from './dataset-import';

/**
 * @deprecated config レジストリに移行済み。config/datasets.ts を使用してください。
 */
export { UPLOAD_CSV_DEFINITIONS, UPLOAD_CSV_TYPES, csvTypeColors } from './dataset-import/model/constants';

// 旧型定義の互換性
export type { PanelFileItem, DatasetImportVMOptions as UseDatabaseUploadVMOptions } from './dataset-import/model/types';
export type { ValidationStatus, CsvDefinition, UploadResponseShape } from './shared/types/common';
export type { CsvPreviewData as CsvPreview } from './dataset-preview/model/types';
// export type { CsvFileType, CsvUploadCardEntry } from './domain/types';
