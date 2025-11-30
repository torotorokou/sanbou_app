/**
 * Report Feature - Public API
 * MVVM+SOLID アーキテクチャに準拠した barrel export
 */

// Domain Types
export type {
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
    SampleSectionProps,
} from '@features/report/shared/types/report.types';

export type {
    WorkerRow,
    ValuableRow,
    ShipmentRow,
} from '@features/report/shared/types/report-api.types';

// Domain Config (still in model/config for now - skip to avoid duplicates)
// export * from './model/config';  // CsvConfig, CsvConfigEntry already exported from report.types

// Ports
export type { IReportRepository } from '@features/report/upload/ports/repository';

// Application (ViewModels)
export { useReportActions } from '@features/report/actions/model/useReportActions';
export { useReportArtifact } from '@features/report/preview/model/useReportArtifact';
export { useReportBaseBusiness } from '@features/report/base/model/useReportBaseBusiness';

// Infrastructure
export {
    generateFactoryReport,
    generateBalanceSheet,
    generateAverageSheet,
    generateManagementSheet,
    generateReportWithFiles,
    type ReportArtifactResponse,
    type ReportGenerateRequest,
} from '@features/report/upload/infrastructure/report.repository';

// UI
export { default as ReportBase } from '@features/report/base/ui/ReportBase';
export { default as ReportHeader } from '@features/report/base/ui/ReportHeader';

// Selector
export {
    useReportManager,
    useReportLayoutStyles,
    ReportSelector,
    ReportStepIndicator,
} from '@features/report/selector';

// Modal
export {
    ReportStepperModal,
    type ReportStepperModalProps,
} from '@features/report/modal';

// Interactive
export {
    initializeBlockUnitPrice,
    startBlockUnitPrice,
    selectTransport,
    applyPrice,
    finalizePrice,
    BlockUnitPriceInteractiveModal,
    InteractiveReportModal,
    TransportSelectionList,
    TransportConfirmationTable,
    createInteractiveItemFromRow,
    buildSelectionPayload,
    type BlockUnitPriceInitialRequest,
    type BlockUnitPriceInitialResponse,
    type BlockUnitPriceStartRequest,
    type BlockUnitPriceStartResponse,
    type SelectTransportRequest,
    type SelectTransportResponse,
    type ApplyPriceRequest,
    type ApplyPriceResponse,
    type FinalizePriceRequest,
    type FinalizePriceResponse,
    type TransportCandidateRow,
    type TransportVendor,
    type InteractiveItem,
    type InitialApiResponse,
    type SessionData,
} from '@features/report/interactive';
