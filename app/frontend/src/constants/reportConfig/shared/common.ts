// /app/src/constants/reportConfig/shared/common.ts
import React from 'react';
import type { CsvConfigGroup, ModalStepConfig, ReportConfig } from './types';

// ==============================
// 🌐 共通定数・設定
// ==============================

/**
 * APIエンドポイント定数
 */
export const LEDGER_API_URL = '/ledger_api/report/manage';
export const LEDGER_REPORT_URL = '/ledger_api/reports';
/**
 * 帳簿タイプ別APIエンドポイント設定
 */
export const REPORT_API_ENDPOINTS = {
    // 工場日報系
    factory_report: `${LEDGER_REPORT_URL}/factory_report`,

    // 収支・管理表系
    balance_sheet: `${LEDGER_REPORT_URL}/balance_sheet`,
    average_sheet: `${LEDGER_REPORT_URL}/average_sheet`,
    management_sheet: `${LEDGER_REPORT_URL}/management_sheet`,

    // インタラクティブ帳簿系
    // バックエンドの実装: app.include_router(block_unit_price_router, prefix="/ledger_api/block_unit_price_interactive")
    block_unit_price: `/ledger_api/block_unit_price_interactive/initial`,

    // 台帳系（将来追加用）
    ledger_book: `${LEDGER_REPORT_URL}/ledger`,
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

// 共通のシンプルなモーダルステップ（作成中 -> 完了）
export const SIMPLE_CREATE_AND_DONE_STEPS: ModalStepConfig[] = [
    {
        label: "帳簿作成中",
        content: React.createElement(
            "div",
            {},
            "帳簿を作成中です。しばらくお待ちください。"
        ),
        showNext: false,
        showClose: false,
    },
    {
        label: "完了",
        content: React.createElement("div", {}, "完了しました"),
        showNext: false,
        showClose: true,
    },
];

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
