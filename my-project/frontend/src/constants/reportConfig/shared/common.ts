// /app/src/constants/reportConfig/shared/common.ts
import type { CsvConfigGroup, ModalStepConfig, ReportConfig } from './types';

// ==============================
// 🌐 共通定数・設定
// ==============================

/**
 * APIエンドポイント定数
 */
export const LEDGER_API_URL = '/ledger_api/report/manage';

/**
 * 帳簿タイプ別APIエンドポイント設定
 */
export const REPORT_API_ENDPOINTS = {
    // 工場日報系
    factory_report: LEDGER_API_URL,

    // 収支・管理表系
    balance_sheet: '/api/report/balance',
    average_sheet: '/api/report/average',
    management_sheet: '/api/report/management',

    // インタラクティブ帳簿系
    block_unit_price: '/ledger_api/report/block_unit_price',

    // 台帳系（将来追加用）
    ledger_book: '/api/report/ledger',
} as const;

/**
 * 帳簿タイプからAPIエンドポイントを取得
 */
export const getApiEndpoint = (reportKey: string): string => {
    return (
        REPORT_API_ENDPOINTS[reportKey as keyof typeof REPORT_API_ENDPOINTS] ||
        LEDGER_API_URL
    );
};

/**
 * インタラクティブ帳簿の設定
 */
export const INTERACTIVE_REPORTS = {
    block_unit_price: {
        modalComponent: 'BlockUnitPriceInteractiveModal',
        multiStep: true,
        requiresUserInput: true,
    },
    // 将来的な追加用
    custom_pricing: {
        modalComponent: 'CustomPricingModal',
        multiStep: true,
        requiresUserInput: true,
    },
} as const;

/**
 * 帳簿がインタラクティブタイプかチェック
 */
export const isInteractiveReport = (reportKey: string): boolean => {
    return reportKey in INTERACTIVE_REPORTS;
};

/**
 * 共通ユーティリティ関数
 */
export const createReportConfig = <T extends string>(
    csvConfigMap: Record<T, CsvConfigGroup>,
    modalStepsMap: Record<T, ModalStepConfig[]>,
    pdfPreviewMap: Record<T, string>
): Record<T, ReportConfig> => {
    return Object.fromEntries(
        Object.keys(csvConfigMap).map((key) => [
            key,
            {
                csvConfigs: csvConfigMap[key as T],
                steps: modalStepsMap[key as T].map(
                    (step: ModalStepConfig) => step.label
                ),
                previewImage: pdfPreviewMap[key as T],
                modalSteps: modalStepsMap[key as T],
            },
        ])
    ) as Record<T, ReportConfig>;
};
