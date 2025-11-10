// features/report/model/index.ts
// Model層の公開API (Controller Hooks + Types)

// ========================================
// Controller Hooks (UIロジック・状態管理)
// ========================================
export { useReportActions } from '@features/report/report-actions/model/useReportActions';
export { useReportBaseBusiness } from '@features/report/report-base/model/useReportBaseBusiness';
export { useReportLayoutStyles } from '@features/report/report-select/model/useReportLayoutStyles';
export { useReportManager } from '@features/report/report-select/model/useReportManager';
export { useReportArtifact } from '@features/report/report-preview/model/useReportArtifact';

// ========================================
// Types (データ型定義)
// ========================================
export type * from '@features/report/types/report.types';
export type * from '@features/report/types/report-api.types';

// ========================================
// Config
// ========================================
// 設定はconfig/index.tsから直接インポートしてください
// 型の重複を避けるため、ここではエクスポートしません

