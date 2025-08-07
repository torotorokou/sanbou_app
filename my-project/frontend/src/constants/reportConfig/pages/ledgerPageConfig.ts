// /app/src/constants/reportConfig/pages/ledgerPageConfig.ts
import React from 'react';
import { CSV_DEFINITIONS } from '../../CsvDefinition';
import type { CsvConfigGroup, ModalStepConfig } from '../shared/types';
import { createReportConfig } from '../shared/common';

// ==============================
// 📖 帳簿ページ専用設定
// ==============================

export const LEDGER_REPORT_KEYS = {
    ledger_book: { value: 'ledger_book', label: '帳簿' },
} as const;

export type LedgerReportKey = keyof typeof LEDGER_REPORT_KEYS;
export const LEDGER_REPORT_OPTIONS = Object.values(LEDGER_REPORT_KEYS);

// CSV設定
export const ledgerCsvConfigMap: Record<LedgerReportKey, CsvConfigGroup> = {
    ledger_book: [
        { config: CSV_DEFINITIONS.receive, required: true },
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: true },
    ],
};

// モーダルステップ設定
export const ledgerModalStepsMap: Record<LedgerReportKey, ModalStepConfig[]> = {
    ledger_book: [
        {
            label: '帳簿作成中',
            content: React.createElement(
                'div',
                {},
                '帳簿を作成中です。しばらくお待ちください。'
            ),
            showNext: false,
            showClose: false,
        },
        {
            label: '完了',
            content: React.createElement('div', {}, '帳簿が作成されました'),
            showNext: false,
            showClose: true,
        },
    ],
};

// PDF生成設定
export const ledgerPdfGeneratorMap: Record<
    LedgerReportKey,
    () => Promise<string>
> = {
    ledger_book: async () => '/ledger_book.pdf',
};

// PDFプレビュー設定
export const ledgerPdfPreviewMap: Record<LedgerReportKey, string> = {
    ledger_book: '/images/sampleViews/manage/ledgerBook.png',
};

// 統合設定
export const ledgerReportConfigMap = createReportConfig(
    ledgerCsvConfigMap,
    ledgerModalStepsMap,
    ledgerPdfGeneratorMap,
    ledgerPdfPreviewMap
);
