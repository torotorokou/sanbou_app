// features/report/model/index.ts
// Model層の公開API

// ========================================
// Hooks
// ========================================
export { useReportActions } from './useReportActions';
export { useReportBaseBusiness } from './useReportBaseBusiness';
export { useReportLayoutStyles } from './useReportLayoutStyles';
export { useReportManager } from './useReportManager';
export { useExcelGeneration } from './useExcelGeneration';
export { useReportArtifact } from './useReportArtifact';

// ========================================
// Deprecated (非推奨)
// ========================================
// 以下は後方互換性のために保持されていますが、使用しないでください
export { useZipFileGeneration } from './useZipFileGeneration';
export { useZipProcessing } from './useZipProcessing';

// ========================================
// Types
// ========================================
export type * from './report.types';
export type * from './report-api.types';

// ========================================
// Config
// ========================================
// 設定はconfig/index.tsから直接インポートしてください
// 型の重複を避けるため、ここではエクスポートしません

