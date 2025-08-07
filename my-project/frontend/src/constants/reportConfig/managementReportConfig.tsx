// /app/src/constants/reportConfig/managementReportConfig.tsx
import React from 'react';

import type { CsvDefinition } from '../CsvDefinition';
import { CSV_DEFINITIONS } from '../CsvDefinition';

// ==============================
// 🤉 帳票定義（キー + ラベル）
// ==============================

// ==============================
// APIエンドポイント定数（帳簿作成など）
// ==============================
export const REPORT_COMMON_API_URL = '/ledger_api/report/manage';
export const REPORT_BLOCKUNIT_API_URL = '/ledger_api/block_unit_price_interactive/upload-and-start';
// ==============================
// APIエンドポイント定数（帳簿作成など）
// ==============================
export const reportApiUrlMap: Record<ReportKey, string> = {
    factory_report: REPORT_COMMON_API_URL,
    balance_sheet: REPORT_COMMON_API_URL,
    average_sheet: REPORT_COMMON_API_URL,
    block_unit_price: REPORT_BLOCKUNIT_API_URL,
    management_sheet: REPORT_COMMON_API_URL,
};



export const REPORT_KEYS = {
    factory_report: { value: 'factory_report', label: '工場日報', type: 'auto' },
    balance_sheet: { value: 'balance_sheet', label: '工場搬出入収支表', type: 'auto' },
    average_sheet: { value: 'average_sheet', label: '集計項目平均表', type: 'auto' },
    block_unit_price: { value: 'block_unit_price', label: 'ブロック単価表', type: 'interactive' },
    management_sheet: { value: 'management_sheet', label: '管理票', type: 'auto' },
} as const;

export type ReportKey = keyof typeof REPORT_KEYS;
export type ReportType = 'auto' | 'interactive';
export const REPORT_OPTIONS = Object.values(REPORT_KEYS);

// レポートタイプを取得するヘルパー関数
export const getReportType = (reportKey: ReportKey): ReportType => {
    return REPORT_KEYS[reportKey].type;
};

// レポートタイプ別にキーを取得するヘルパー関数
export const getReportKeysByType = (type: ReportType): ReportKey[] => {
    return Object.entries(REPORT_KEYS)
        .filter(([, config]) => config.type === type)
        .map(([key]) => key as ReportKey);
};

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
    showPrev?: boolean; // 戻るボタンの表示制御
    showClose?: boolean;
    canProceed?: () => boolean; // 進むボタンの制御関数
};

// 自動処理用のステップ構成
export const autoModalStepsMap: Record<string, ModalStepConfig[]> = {
    factory_report: [
        { label: '帳簿作成中', content: <div>帳簿を作成中です。しばらくお待ちください。</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>完了しました</div>, showNext: false, showClose: true },
    ],
    balance_sheet: [
        { label: '帳簿作成中', content: <div>帳票を生成中です</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>完了しました</div>, showNext: false, showClose: true },
    ],
    average_sheet: [
        { label: '帳簿作成中', content: <div>帳票を生成中です</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>完了しました</div>, showNext: false, showClose: true },
    ],
    management_sheet: [
        { label: '帳簿作成中', content: <div>帳票を生成中です</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>完了しました</div>, showNext: false, showClose: true },
    ],
};

// インタラクティブ処理用のステップ構成
export const interactiveModalStepsMap: Record<string, ModalStepConfig[]> = {
    block_unit_price: [
        {
            label: 'データ処理',
            content: null,
            showNext: true,
            showClose: false
        },
        {
            label: '運搬業者選択',
            content: null,
            showNext: true,
            showClose: false,
            // カスタム検証関数（進むボタンの制御）
            canProceed: () => {
                // window.blockUnitPriceWorkflowValidationが存在し、全選択完了している場合のみtrue
                const win = window as typeof window & {
                    blockUnitPriceWorkflowValidation?: {
                        canProceed: boolean;
                        currentStep: number;
                        isAllSelected: boolean;
                    }
                };
                const validation = win.blockUnitPriceWorkflowValidation;
                return validation?.canProceed === true && validation?.isAllSelected === true;
            }
        },
        {
            label: '選択内容確認',
            content: null,
            showNext: true,
            showPrev: true, // 戻るボタンを表示
            showClose: false
        },
        {
            label: '計算実行',
            content: null,
            showNext: false,
            showClose: false
        },
        {
            label: '完了',
            content: null,
            showNext: false,
            showClose: true
        },
    ],
};

// 後方互換性のための統合マップ（廃止予定）
export const modalStepsMap: Record<ReportKey, ModalStepConfig[]> = {
    ...autoModalStepsMap,
    ...interactiveModalStepsMap,
} as Record<ReportKey, ModalStepConfig[]>;

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
        type: ReportType;
    }
> = Object.fromEntries(
    Object.keys(REPORT_KEYS).map((key) => {
        const reportKey = key as ReportKey;
        const reportConfig = REPORT_KEYS[reportKey];
        const steps = reportConfig.type === 'auto'
            ? autoModalStepsMap[reportKey]?.map(step => step.label) || []
            : interactiveModalStepsMap[reportKey]?.map(step => step.label) || [];

        return [
            key,
            {
                csvConfigs: csvConfigMap[reportKey],
                steps,
                generatePdf: pdfGeneratorMap[reportKey],
                previewImage: pdfPreviewMap[reportKey],
                type: reportConfig.type,
            },
        ];
    })
) as Record<
    ReportKey,
    {
        csvConfigs: CsvConfigGroup;
        steps: string[];
        generatePdf: () => Promise<string>;
        previewImage: string;
        type: ReportType;
    }
>;

