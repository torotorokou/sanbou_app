// /app/src/pages/types/index.ts

/**
 * pages/types モジュールのエクスポート
 * 
 * 🎯 目的：
 * - 型定義の一元的なエクスポート
 * - インポート文の簡潔化
 * - モジュール構造の明確化
 */

// ==============================
// 📋 レポートモード関連
// ==============================

export {
    REPORT_GENERATION_MODES,
    REPORT_MODE_CONFIG,
    API_ENDPOINTS,
    getReportModeInfo,
    getInteractiveReportKeys,
    getAutoReportKeys,
    getApiEndpoint,
    getApiEndpointByReportKey,
} from './reportMode';

export type {
    ReportGenerationMode,
    ReportKey,
    ReportModeInfo,
} from './reportMode';

// ==============================
// 🎮 インタラクティブモード関連
// ==============================

export {
    INTERACTIVE_STEPS,
    INTERACTION_TYPES,
} from './interactiveMode';

export type {
    InteractiveProcessState,
    InteractiveStep,
    InteractiveResult,
    InteractiveComponentProps,
    InteractiveComponentConfig,
    InteractionType,
    InteractionConfig,
    InteractiveStepConfig,
    InteractiveFlowConfig,
    InteractiveApiRequest,
    InteractiveApiResponse,
    SessionData,
    UserSelections,
    ProcessData,
    InputValue,
} from './interactiveMode';
