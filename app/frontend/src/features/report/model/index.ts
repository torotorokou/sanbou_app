// features/report/model/index.ts
// Model層の公開API (Controller Hooks + Types)

// ========================================
// Controller Hooks (UIロジック・状態管理)
// ========================================
export { useReportActions } from '../application/useReportActions';
export { useReportBaseBusiness } from '../application/useReportBaseBusiness';
export { useReportLayoutStyles } from '../application/useReportLayoutStyles';
export { useReportManager } from '../application/useReportManager';
export { useReportArtifact } from '../application/useReportArtifact';

// ========================================
// Types (データ型定義)
// ========================================
export type * from '../domain/types/report.types';
export type * from '../domain/types/report-api.types';

// ========================================
// Config
// ========================================
// 設定はconfig/index.tsから直接インポートしてください
// 型の重複を避けるため、ここではエクスポートしません

