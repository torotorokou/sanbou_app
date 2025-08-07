// /app/src/constants/reportConfig/pages/factoryPageConfig.ts
import React from 'react';
import { CSV_DEFINITIONS } from '../../CsvDefinition';
import type { CsvConfigGroup, ModalStepConfig } from '../shared/types';
import { createReportConfig } from '../shared/common';

// ==============================
// 🏭 工場ページ専用設定
// ==============================

export const FACTORY_REPORT_KEYS = {
    factory_report: { value: 'factory_report', label: '工場日報' },
    block_unit_price: { value: 'block_unit_price', label: 'ブロック単価表' },
} as const;

export type FactoryReportKey = keyof typeof FACTORY_REPORT_KEYS;
export const FACTORY_REPORT_OPTIONS = Object.values(FACTORY_REPORT_KEYS);

// CSV設定
export const factoryCsvConfigMap: Record<FactoryReportKey, CsvConfigGroup> = {
    factory_report: [
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: true },
    ],
    block_unit_price: [{ config: CSV_DEFINITIONS.shipment, required: true }],
};

// モーダルステップ設定
export const factoryModalStepsMap: Record<FactoryReportKey, ModalStepConfig[]> =
    {
        factory_report: [
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
                content: React.createElement('div', {}, '完了しました'),
                showNext: false,
                showClose: true,
            },
        ],
        block_unit_price: [
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
                content: React.createElement('div', {}, '完了しました'),
                showNext: false,
                showClose: true,
            },
        ],
    };

// PDF生成設定
export const factoryPdfGeneratorMap: Record<
    FactoryReportKey,
    () => Promise<string>
> = {
    factory_report: async () => '/factory_report.pdf',
    block_unit_price: async () => '/block_unit_price.pdf',
};

// PDFプレビュー設定
export const factoryPdfPreviewMap: Record<FactoryReportKey, string> = {
    factory_report: '/images/sampleViews/manage/factoryReport.png',
    block_unit_price: '/images/sampleViews/manage/blockunitPrice.png',
};

// 統合設定
export const factoryReportConfigMap = createReportConfig(
    factoryCsvConfigMap,
    factoryModalStepsMap,
    factoryPdfGeneratorMap,
    factoryPdfPreviewMap
);
