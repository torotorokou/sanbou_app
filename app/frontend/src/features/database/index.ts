/**
 * Database Feature - Public API
 * MVVM+SOLID アーキテクチャに準拠した barrel export
 */

// Domain
export type { CsvFileType, CsvUploadCardEntry } from './domain/types';
export * from './domain/config/CsvDefinition';
export * from './domain/config/uploadCsvConfig';

// Ports
export type { IDatabaseRepository } from './ports/repository';

// Application
export * from './application/useDatabaseVM';

// UI Components
export { default as CsvPreviewCard } from './ui/cards/CsvPreviewCard';
export { default as CsvUploadPanel } from './ui/cards/CsvUploadPanel';
export { UploadInstructions } from './ui/components/UploadInstructions';
export { ValidationBadge } from './ui/ValidationBadge';
export { SimpleUploadPanel } from './ui/SimpleUploadPanel';

// Hooks
export { useDatabaseUploadVM } from './hooks/useDatabaseUploadVM';
export type { UseDatabaseUploadVMOptions } from './hooks/useDatabaseUploadVM';

// Model (型とConstants)
export type { PanelFileItem, ValidationStatus, CsvPreview, UploadResponseShape } from './model/types';
export * from './model/constants';
export * from './model/dataset';
// sampleCsvModelは直接import推奨（名前衝突のため）
