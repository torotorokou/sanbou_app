// features/report/index.ts
// Report機能の公開API

// ========================================
// Model (型定義)
// ========================================
export type {
    // reportBase.ts から
    CsvConfig,
    CsvConfigEntry,
    CsvFiles,
    ValidationResult,
    StepProps,
    FileProps,
    PreviewProps,
    ModalProps,
    FinalizedProps,
    LoadingProps,
    ReportBaseProps,
    UploadFileConfig,
    MakeUploadPropsFn,
} from './model/report.types';

export type {
    // report.ts から
    WorkerRow,
    ValuableRow,
    ShipmentRow,
} from './model/report-api.types';

// ========================================
// Config (設定)
// ========================================
export {
    // reportConfig から
    reportConfigMap,
    manageReportConfigMap,
    factoryReportConfigMap,
    ledgerReportConfigMap,
    modalStepsMap,
    pdfPreviewMap,
    csvConfigMap,
    getPageConfig,
    getApiEndpoint,
    isInteractiveReport,
    REPORT_API_ENDPOINTS,
    INTERACTIVE_REPORTS,
    REPORT_KEYS,
    REPORT_OPTIONS,
    PAGE_REPORT_GROUPS,
    MANAGE_REPORT_KEYS,
    FACTORY_REPORT_KEYS,
    LEDGER_REPORT_KEYS,
} from './config/reportConfig';

export type {
    // reportConfig/shared/types.ts から
    ReportConfig,
    ModalStepConfig,
    CsvConfigGroup,
} from './config/reportConfig/shared/types';

export type {
    // reportConfig/index.ts から
    ReportKey,
    PageGroupKey,
} from './config/reportConfig';

// ========================================
// 将来の公開API (Phase 4 Step 3-2以降)
// ========================================

// Hooks (Step 3-2で追加予定)
// export { useReportManager } from './hooks/useReportManager';
// export { useReportGeneration } from './hooks/useReportGeneration';
// export { useReportPreview } from './hooks/useReportPreview';

// UI Components (Step 3-3以降で追加予定)
// export { ReportBase } from './ui/ReportBase';
// export { ReportHeader } from './ui/common/ReportHeader';
// export { ReportSelector } from './ui/common/ReportSelector';
// export { CsvUploadSection } from './ui/common/CsvUploadSection';
// export { PreviewSection } from './ui/common/PreviewSection';
// export { ActionsSection } from './ui/common/ActionsSection';
