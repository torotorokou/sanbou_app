// /app/src/constants/reportConfig/managementReportConfig.tsx
import React from 'react';

import type { CsvDefinition } from '../CsvDefinition';
import { CSV_DEFINITIONS } from '../CsvDefinition';

// ==============================
// 🤉 帳票定義（キー + ラベル）
// ==============================

export const REPORT_KEYS = {
    factory_report: { value: 'factory_report', label: '工場日報' },
    balance_sheet: { value: 'balance_sheet', label: '工場搬出入収支表' },
    average_sheet: { value: 'average_sheet', label: '集計項目平均表' },
    block_unit_price: { value: 'block_unit_price', label: 'ブロック単価表' },
    management_sheet: { value: 'management_sheet', label: '管理票' },
} as const;

export type ReportKey = keyof typeof REPORT_KEYS;
export const REPORT_OPTIONS = Object.values(REPORT_KEYS);

// =================================
// 📄 CSVファイル構成（帳票別）
// =================================

export type CsvConfig = CsvDefinition;

export type CsvConfigEntry = {
    config: CsvConfig;
    required: boolean;
};

export type CsvConfigGroup = CsvConfigEntry[];

export const csvConfigMap: Record<ReportKey, CsvConfigGroup> = {
    // 工場日報
    factory_report: [
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: true },
    ],
    // 搬出入収支表
    balance_sheet: [
        { config: CSV_DEFINITIONS.receive, required: false },
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: true },
    ],
    // ABC集計表
    average_sheet: [{ config: CSV_DEFINITIONS.receive, required: true }],
    // ブロック単価表
    block_unit_price: [{ config: CSV_DEFINITIONS.shipment, required: true }],
    // 管理表
    management_sheet: [
        { config: CSV_DEFINITIONS.receive, required: true },
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: true },
    ],
};

// =====================================
// 🔁 ステップ構成＋モーダル内容（帳票ごとに統一）
// =====================================

export type ModalStepConfig = {
    label: string;
    content: React.ReactNode;
    showNext?: boolean;
    showClose?: boolean;
};

export const modalStepsMap: Record<
    ReportKey,
    ModalStepConfig[]
> = {
    factory_report: [
        { label: '帳簿作成中', content: <div>帳簿を作成中です。しばらくお待ちください。</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>完了しました</div>, showNext: false, showClose: true },
    ],
    balance_sheet: [
        { label: '帳簿作成中', content: <div>帳票を生成中です</div>, showNext: true, showClose: false },
        { label: '完了', content: <div>完了しました</div>, showNext: false, showClose: true },
    ],
    average_sheet: [
        { label: '帳簿作成中', content: <div>帳票を生成中です</div>, showNext: true, showClose: false },
        { label: '完了', content: <div>完了しました</div>, showNext: false, showClose: true },
    ],
    block_unit_price: [
        { label: '帳簿作成中', content: <div>帳簿を作成中です。しばらくお待ちください。</div>, showNext: false, showClose: false },
        { label: '帳簿作成中', content: <div>帳簿を作成中です。しばらくお待ちください。</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>完了しました</div>, showNext: false, showClose: true },
    ],
    management_sheet: [
        { label: '帳簿作成中', content: <div>帳票を生成中です</div>, showNext: true, showClose: false },
        { label: '完了', content: <div>完了しました</div>, showNext: false, showClose: true },
    ],
};

// ===================================
// 📤 PDF出力関数（帳票ごとに切替）
// ===================================

export const pdfGeneratorMap: Record<ReportKey, () => Promise<string>> = {
    factory_report: async () => '/factory_report.pdf',
    balance_sheet: async () => '/balance_sheet.pdf',
    average_sheet: async () => '/average_sheet.pdf',
    block_unit_price: async () => '/block_unit_price.pdf',
    management_sheet: async () => '/management_sheet.pdf',
};

// ===================================
// 🔍 PDFプレビューURL（帳票別）
// ===================================

export const pdfPreviewMap: Record<ReportKey, string> = {
    factory_report: '/images/sampleViews/manage/factoryReport.png',
    balance_sheet: '/images/sampleViews/manage/balanceSheet.png',
    average_sheet: '/images/sampleViews/manage/averageSheet.png',
    block_unit_price: '/images/sampleViews/manage/blockunitPrice.png',
    management_sheet: '/images/sampleViews/manage/managementSheet.png',
};

// ===================================
// 🔧 帳票設定マップ（統合）
// ===================================

export const reportConfigMap: Record<
    ReportKey,
    {
        csvConfigs: CsvConfigGroup;
        steps: string[];
        generatePdf: () => Promise<string>;
        previewImage: string;
    }
> = Object.fromEntries(
    Object.keys(REPORT_KEYS).map((key) => [
        key,
        {
            csvConfigs: csvConfigMap[key as ReportKey],
            steps: modalStepsMap[key as ReportKey].map((step) => step.label),
            generatePdf: pdfGeneratorMap[key as ReportKey],
            previewImage: pdfPreviewMap[key as ReportKey],
        },
    ])
) as Record<
    ReportKey,
    {
        csvConfigs: CsvConfigGroup;
        steps: string[];
        generatePdf: () => Promise<string>;
        previewImage: string;
    }
>;
