import {
    parseReceiveCSV,
    parseShipmentCSV,
    parseYardCSV,
} from '@/parsers/csvParsers';

import type { CsvType, CsvDefinition } from './csvTypes';
import { CSV_DEFINITIONS } from './csvTypes';

// ==============================
// 🤉 帳票定義（キー + ラベル）
// ==============================

export const REPORT_KEYS = {
    factory: { value: 'factory', label: '工場日報' },
    balance: { value: 'balance', label: '搬出入収支表' },
    abc: { value: 'abc', label: 'ABC集計表' },
    block: { value: 'block', label: 'ブロック単価表' },
    management: { value: 'management', label: '管理表' },
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
    factory: [
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: true },
    ],
    // 搬出入収支表
    balance: [
        { config: CSV_DEFINITIONS.receive, required: false },
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: true },
    ],
    // ABC集計表
    abc: [{ config: CSV_DEFINITIONS.receive, required: true }],
    // ブロック単価表
    block: [{ config: CSV_DEFINITIONS.shipment, required: true }],
    // 管理表
    management: [
        { config: CSV_DEFINITIONS.receive, required: true },
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: true },
    ],
};

// =====================================
// 🔁 ステップ構成（帳票ごとの進行表示）
// =====================================

export const stepConfigMap: Record<ReportKey, string[]> = {
    factory: ['CSV選択', 'PDF生成中', '完了'],
    balance: ['CSV読み込み', '帳票生成', '完了'],
    abc: ['準備中'],
    block: ['準備中'],
    management: ['準備中'],
};

// ===================================
// 📤 PDF出力関数（帳票ごとに切替）
// ===================================

export const pdfGeneratorMap: Record<ReportKey, () => Promise<string>> = {
    factory: async () => '/factory_report.pdf',
    balance: async () => '/balance_report.pdf',
    abc: async () => '/abc_report.pdf',
    block: async () => '/block_report.pdf',
    management: async () => '/management_report.pdf',
};

// ===================================
// 🔍 PDFプレビューURL（帳票別）
// ===================================

export const pdfPreviewMap: Record<ReportKey, string> = {
    factory: '/images/sampleViews/manage/factoryReport.png',
    balance: '/images/sampleViews/manage/balanceSheet.png',
    abc: '/images/sampleViews/manage/averageSheet.png',
    block: '/images/sampleViews/manage/blockunitPrice.png',
    management: '/images/sampleViews/manage/managementSheet.png',
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
            steps: stepConfigMap[key as ReportKey],
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
