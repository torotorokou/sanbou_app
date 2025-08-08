// /app/src/pages/types/reportMode.ts

/**
 * 帳簿生成モードの型定義
 * 
 * 🎯 目的：
 * - 自動帳簿生成とインタラクティブ帳簿生成の明確な区別
 * - モードごとの処理フロー分岐をtype-safeに実現
 * - SOLID原則のOpen/Closed Principleに準拠
 */

// ==============================
// 📋 基本モード定義
// ==============================

/**
 * 帳簿生成のモード種類
 */
export const REPORT_GENERATION_MODES = {
    AUTO: 'auto',
    INTERACTIVE: 'interactive'
} as const;

export type ReportGenerationMode = typeof REPORT_GENERATION_MODES[keyof typeof REPORT_GENERATION_MODES];

// ==============================
// 🏭 帳簿モード設定マップ
// ==============================

/**
 * 各帳簿タイプのモード設定
 * - true: インタラクティブモード対応
 * - false: 自動モードのみ
 */
export const REPORT_MODE_CONFIG = {
    // 管理業務ページ
    factory_report: { mode: REPORT_GENERATION_MODES.AUTO },
    balance_sheet: { mode: REPORT_GENERATION_MODES.INTERACTIVE },
    average_sheet: { mode: REPORT_GENERATION_MODES.AUTO },
    block_unit_price: { mode: REPORT_GENERATION_MODES.INTERACTIVE },
    management_sheet: { mode: REPORT_GENERATION_MODES.AUTO },
    
    // 工場ページ
    // factory_report は管理業務と重複のため除外
    
    // 帳簿ページ  
    ledger_book: { mode: REPORT_GENERATION_MODES.AUTO },
} as const;

export type ReportKey = keyof typeof REPORT_MODE_CONFIG;

// ==============================
// 🔍 ユーティリティ型とヘルパー関数
// ==============================

/**
 * モード判定結果の型
 */
export interface ReportModeInfo {
    mode: ReportGenerationMode;
    isInteractive: boolean;
    isAuto: boolean;
}

/**
 * 指定された帳簿キーのモード情報を取得
 */
export const getReportModeInfo = (reportKey: ReportKey): ReportModeInfo => {
    const config = REPORT_MODE_CONFIG[reportKey];
    const mode = config.mode;
    
    return {
        mode,
        isInteractive: mode === REPORT_GENERATION_MODES.INTERACTIVE,
        isAuto: mode === REPORT_GENERATION_MODES.AUTO,
    };
};

/**
 * インタラクティブモード対応の帳簿キーをフィルタリング
 */
export const getInteractiveReportKeys = (): ReportKey[] => {
    return Object.keys(REPORT_MODE_CONFIG).filter(
        key => REPORT_MODE_CONFIG[key as ReportKey].mode === REPORT_GENERATION_MODES.INTERACTIVE
    ) as ReportKey[];
};

/**
 * 自動モードのみの帳簿キーをフィルタリング
 */
export const getAutoReportKeys = (): ReportKey[] => {
    return Object.keys(REPORT_MODE_CONFIG).filter(
        key => REPORT_MODE_CONFIG[key as ReportKey].mode === REPORT_GENERATION_MODES.AUTO
    ) as ReportKey[];
};

// ==============================
// 🚀 API エンドポイント設定
// ==============================

/**
 * モード別APIエンドポイント設定
 */
export const API_ENDPOINTS = {
    [REPORT_GENERATION_MODES.AUTO]: '/ledger_api/report/manage',
    [REPORT_GENERATION_MODES.INTERACTIVE]: '/ledger_api/report/interactive',
} as const;

/**
 * 指定されたモードのAPIエンドポイントを取得
 */
export const getApiEndpoint = (mode: ReportGenerationMode): string => {
    return API_ENDPOINTS[mode];
};

/**
 * 帳簿キーからAPIエンドポイントを取得
 */
export const getApiEndpointByReportKey = (reportKey: ReportKey): string => {
    const modeInfo = getReportModeInfo(reportKey);
    return getApiEndpoint(modeInfo.mode);
};
