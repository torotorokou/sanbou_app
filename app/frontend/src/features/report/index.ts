/**
 * Report Feature - Public API
 * MVVM+SOLID アーキテクチャに準拠した barrel export
 */

// Domain Types
export * from '@features/report/report-extras/types/report.types';
export * from '@features/report/report-extras/types/report-api.types';

// Domain Config (still in model/config for now - skip to avoid duplicates)
// export * from './model/config';  // CsvConfig, CsvConfigEntry already exported from report.types

// Ports
export type { IReportRepository } from '@features/report/report-upload/ports/repository';

// Application (ViewModels)
export * from '@features/report/report-select/model/useReportManager';
export * from '@features/report/report-actions/model/useReportActions';
export { useReportArtifact } from '@features/report/report-preview/model/useReportArtifact';  // Named export only, avoid type conflict
export * from '@features/report/report-extras/model/useReportBaseBusiness';
export * from '@features/report/report-select/model/useReportLayoutStyles';

// Infrastructure
export * from '@features/report/report-upload/api/report.repository';

// UI
export { default as ReportBase } from '@features/report/report-extras/ui/ReportBase';
export { default as ReportHeader } from '@features/report/report-extras/ui/ReportHeader';
