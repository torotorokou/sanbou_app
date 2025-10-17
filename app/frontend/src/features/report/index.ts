// features/report/index.ts
// Report機能の公開API (MVC構造)

// ========================================
// API Layer (HTTP通信)
// ========================================
export * from './api';

// ========================================
// Model Layer (型定義・データ構造)
// ========================================
export type {
    // report.types.ts から
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
    // report-api.types.ts から
    WorkerRow,
    ValuableRow,
    ShipmentRow,
} from './model/report-api.types';

// ========================================
// Config (設定・定数)
// ========================================
export {
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
} from './model/config';

export type {
    ReportConfig,
    ModalStepConfig,
    CsvConfigGroup,
} from './model/config/shared/types';

export type {
    ReportKey,
    PageGroupKey,
} from './model/config';

// ========================================
// Controller Layer (Hooks - UIロジック・状態管理)
// ========================================
export { useReportManager } from './model/useReportManager';
export { useReportBaseBusiness } from './model/useReportBaseBusiness';
export { useReportActions } from './model/useReportActions';
export { useReportLayoutStyles } from './model/useReportLayoutStyles';
export { useReportArtifact } from './model/useReportArtifact';

// ========================================
// View Layer (UIコンポーネント)
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

// Main Component
export { default as ReportBase } from './ui/ReportBase';

// Interactive Components
export { default as BlockUnitPriceInteractive } from './ui/interactive/BlockUnitPriceInteractive';
export { default as BlockUnitPriceInteractiveModal } from './ui/interactive/BlockUnitPriceInteractiveModal';
export type { InitialApiResponse, SessionData } from './ui/interactive/BlockUnitPriceInteractiveModal';
export type { TransportCandidateRow } from './ui/interactive/types';
export { normalizeRow, isRecord } from './ui/interactive/transportNormalization';

// Viewer Components
export { default as PDFViewer } from './ui/viewer/PDFViewer';
export { default as ReportSampleThumbnail } from './ui/viewer/ReportSampleThumbnail';


