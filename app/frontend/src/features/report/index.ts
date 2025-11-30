/**
 * Report Feature - Public API
 * MVVM+SOLID アーキテクチャに準拠した barrel export
 */

// Domain Types
export * from '@features/report/shared/types/report.types';
export * from '@features/report/shared/types/report-api.types';

// Domain Config (still in model/config for now - skip to avoid duplicates)
// export * from './model/config';  // CsvConfig, CsvConfigEntry already exported from report.types

// Ports
export type { IReportRepository } from '@features/report/upload/ports/repository';

// Application (ViewModels)
export { useReportActions } from '@features/report/actions/model/useReportActions';
export { useReportArtifact } from '@features/report/preview/model/useReportArtifact';
export { useReportBaseBusiness } from '@features/report/base/model/useReportBaseBusiness';

// Infrastructure
export * from '@features/report/upload/infrastructure/report.repository';

// UI
export { default as ReportBase } from '@features/report/base/ui/ReportBase';
export { default as ReportHeader } from '@features/report/base/ui/ReportHeader';

// Selector (新規追加)
export * from '@features/report/selector';

// Modal (新規追加)
export * from '@features/report/modal';

// Interactive (新規追加)
export * from '@features/report/interactive';
