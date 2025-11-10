// features/report/model/index.ts
// Model層の公開API (Controller Hooks + Types)

// ========================================
// Controller Hooks (UIロジック・状態管理)
// ========================================
export { useReportActions } from '@features/report-actions/model/useReportActions';
export { useReportBaseBusiness } from '@features/report-extras/model/useReportBaseBusiness';
export { useReportLayoutStyles } from '@features/report-select/model/useReportLayoutStyles';
export { useReportManager } from '@features/report-select/model/useReportManager';
export { useReportArtifact } from '@features/report-preview/model/useReportArtifact';

// ========================================
// Types (データ型定義)
// ========================================
export type * from '@features/report-extras/types/report.types';
export type * from '@features/report-extras/types/report-api.types';

// ========================================
// Config
// ========================================
// 設定はconfig/index.tsから直接インポートしてください
// 型の重複を避けるため、ここではエクスポートしません

