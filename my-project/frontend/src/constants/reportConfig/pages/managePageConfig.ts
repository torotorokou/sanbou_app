// /app/src/constants/reportConfig/pages/managePageConfig.ts
import React from 'react';
import { CSV_DEFINITIONS } from '../../CsvDefinition';
import BlockUnitPriceInteractive from '../../../components/Report/individual_process/BlockUnitPriceInteractive';
import type { CsvConfigGroup, ModalStepConfig } from '../shared/types';
import { createReportConfig } from '../shared/common';

// ==============================
// 📄 管理業務ページ専用設定
// ==============================

export const MANAGE_REPORT_KEYS = {
    factory_report: { value: 'factory_report', label: '工場日報' },
    balance_sheet: { value: 'balance_sheet', label: '工場搬出入収支表' },
    average_sheet: { value: 'average_sheet', label: '集計項目平均表' },
    block_unit_price: { value: 'block_unit_price', label: 'ブロック単価表' },
    management_sheet: { value: 'management_sheet', label: '管理票' },
} as const;

export type ManageReportKey = keyof typeof MANAGE_REPORT_KEYS;
export const MANAGE_REPORT_OPTIONS = Object.values(MANAGE_REPORT_KEYS);

// CSV設定
export const manageCsvConfigMap: Record<ManageReportKey, CsvConfigGroup> = {
    factory_report: [
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: true },
    ],
    balance_sheet: [
        { config: CSV_DEFINITIONS.receive, required: false },
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: true },
    ],
    average_sheet: [{ config: CSV_DEFINITIONS.receive, required: true }],
    block_unit_price: [{ config: CSV_DEFINITIONS.shipment, required: true }],
    management_sheet: [
        { config: CSV_DEFINITIONS.receive, required: true },
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: true },
    ],
};

// モーダルステップ設定
export const manageModalStepsMap: Record<ManageReportKey, ModalStepConfig[]> = {
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
    balance_sheet: [
        {
            label: '帳簿作成中',
            content: React.createElement('div', {}, '帳票を生成中です'),
            showNext: false,
            showClose: false,
        },
        {
            label: '運搬業者選択',
            content: React.createElement(BlockUnitPriceInteractive),
            showNext: true,
            showClose: false,
        },
        {
            label: '完了',
            content: React.createElement('div', {}, '完了しました'),
            showNext: false,
            showClose: true,
        },
    ],
    average_sheet: [
        {
            label: '帳簿作成中',
            content: React.createElement('div', {}, '帳票を生成中です'),
            showNext: true,
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
    management_sheet: [
        {
            label: '帳簿作成中',
            content: React.createElement('div', {}, '帳票を生成中です'),
            showNext: true,
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
export const managePdfGeneratorMap: Record<
    ManageReportKey,
    () => Promise<string>
> = {
    factory_report: async () => '/factory_report.pdf',
    balance_sheet: async () => '/balance_sheet.pdf',
    average_sheet: async () => '/average_sheet.pdf',
    block_unit_price: async () => '/block_unit_price.pdf',
    management_sheet: async () => '/management_sheet.pdf',
};

// PDFプレビュー設定
export const managePdfPreviewMap: Record<ManageReportKey, string> = {
    factory_report: '/images/sampleViews/manage/factoryReport.png',
    balance_sheet: '/images/sampleViews/manage/balanceSheet.png',
    average_sheet: '/images/sampleViews/manage/averageSheet.png',
    block_unit_price: '/images/sampleViews/manage/blockunitPrice.png',
    management_sheet: '/images/sampleViews/manage/managementSheet.png',
};

// 統合設定
export const manageReportConfigMap = createReportConfig(
    manageCsvConfigMap,
    manageModalStepsMap,
    managePdfGeneratorMap,
    managePdfPreviewMap
);
