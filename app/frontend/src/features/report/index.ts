/**
 * Report Feature - Public API
 * MVVM+SOLID アーキテクチャに準拠した barrel export
 */

// Domain Types
export * from './domain/types/report.types';
export * from './domain/types/report-api.types';

// Domain Config (still in model/config for now - skip to avoid duplicates)
// export * from './model/config';  // CsvConfig, CsvConfigEntry already exported from report.types

// Ports
export type { IReportRepository } from './ports/repository';

// Application (ViewModels)
export * from './application/useReportManager';
export * from './application/useReportActions';
export { useReportArtifact } from './application/useReportArtifact';  // Named export only, avoid type conflict
export * from './application/useReportBaseBusiness';
export * from './application/useReportLayoutStyles';

// Infrastructure
export * from './infrastructure/report.repository';

// UI
export { default as ReportBase } from './ui/cards/ReportBase';
export { default as ReportHeader } from './ui/components/common/ReportHeader';
