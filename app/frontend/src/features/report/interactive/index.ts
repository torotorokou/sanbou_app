/**
 * Report Interactive Module
 * インタラクティブレポート生成（ブロック単価など）
 */

// Infrastructure - API
export {
    initializeBlockUnitPrice,
    startBlockUnitPrice,
    selectTransport,
    applyPrice,
    finalizePrice,
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
} from './infrastructure';

// UI Components
export { default as BlockUnitPriceInteractiveModal } from './ui/BlockUnitPriceInteractiveModal';
export { default as InteractiveReportModal } from './ui/InteractiveReportModal';
export { TransportSelectionList } from './ui/TransportSelectionList';
export { TransportConfirmationTable } from './ui/TransportConfirmationTable';

// Business Logic & Helpers
export { createInteractiveItemFromRow, buildSelectionPayload } from './model/blockUnitPriceHelpers';

// Re-export types from shared (for convenience)
export type {
    TransportCandidateRow,
    TransportVendor,
    InteractiveItem,
    InitialApiResponse,
    SessionData,
} from '../shared/types/interactive.types';
