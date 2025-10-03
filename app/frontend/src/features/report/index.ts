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

// Hooks (Step 3-2で追加) ✅
export { useReportManager } from './hooks/useReportManager';
export { useReportBaseBusiness } from './hooks/useReportBaseBusiness';
export { useReportActions } from './hooks/useReportActions';
export { useReportLayoutStyles } from './hooks/useReportLayoutStyles';

// ========================================
// UI Components (Step 3-3で追加) ✅
// ========================================

// Common UI Components
export { default as ReportHeader } from './ui/common/ReportHeader';
export { default as ReportSelector } from './ui/common/ReportSelector';
export { default as ReportStepIndicator } from './ui/common/ReportStepIndicator';
export { default as ReportStepperModal } from './ui/common/ReportStepperModal';
export { default as ReportManagePageLayout } from './ui/common/ReportManagePageLayout';
export { default as CsvUploadSection } from './ui/common/CsvUploadSection';
export { default as PreviewSection } from './ui/common/PreviewSection';
export { default as ActionsSection } from './ui/common/ActionsSection';
export { default as SampleSection } from './ui/common/SampleSection';
export { default as InteractiveReportModal } from './ui/common/InteractiveReportModal';

// Common UI Types
export type {
    CsvFileType,
    SampleSectionProps,
    CsvUploadSectionProps,
    ActionsSectionProps,
} from './ui/common/types';

// Common UI Utilities
export { downloadExcelFile } from './ui/common/downloadExcel';

// ========================================
// UI Components - Main (Step 3-4で追加) ✅
// ========================================

export { default as ReportBase } from './ui/ReportBase';

// ========================================
// 将来の公開API (Step 3-5以降)
// ========================================

// Interactive Components (Step 3-5で追加予定)
// export { BlockUnitPriceInteractive } from './ui/interactive/BlockUnitPriceInteractive';

// Viewer Components (Step 3-6で追加予定)
// export { PDFViewer } from './ui/viewer/PDFViewer';
// export { ReportSampleThumbnail } from './ui/viewer/ReportSampleThumbnail';


