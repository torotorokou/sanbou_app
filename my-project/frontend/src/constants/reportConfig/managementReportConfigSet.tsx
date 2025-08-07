// /app/src/constants/reportConfig/managementReportConfigSet.tsx
import React from 'react';
import type { ReportConfigPackage, ReportType, ReportKey } from '../../types/reportConfig';
import type { CsvDefinition } from '../CsvDefinition';
import { CSV_DEFINITIONS } from '../CsvDefinition';

// ==============================
// 🤉 帳票定義（管理系帳票専用）
// ==============================

const MANAGEMENT_REPORT_KEYS = {
    factory_report: { value: 'factory_report', label: '工場日報', type: 'auto' as ReportType },
    balance_sheet: { value: 'balance_sheet', label: '工場搬出入収支表', type: 'auto' as ReportType },
    average_sheet: { value: 'average_sheet', label: '集計項目平均表', type: 'auto' as ReportType },
    block_unit_price: { value: 'block_unit_price', label: 'ブロック単価表', type: 'interactive' as ReportType },
    management_sheet: { value: 'management_sheet', label: '管理票', type: 'auto' as ReportType },
} as const;

// ==============================
// APIエンドポイント（管理系専用）
// ==============================
const REPORT_COMMON_API_URL = '/ledger_api/report/manage';
const REPORT_BLOCKUNIT_API_URL = '/ledger_api/block_unit_price_interactive/upload-and-start';

const MANAGEMENT_API_URL_MAP: Record<ReportKey, string> = {
    factory_report: REPORT_COMMON_API_URL,
    balance_sheet: REPORT_COMMON_API_URL,
    average_sheet: REPORT_COMMON_API_URL,
    block_unit_price: REPORT_BLOCKUNIT_API_URL,
    management_sheet: REPORT_COMMON_API_URL,
};

// =================================
// 📄 CSVファイル構成（管理系帳票専用）
// =================================

const MANAGEMENT_CSV_CONFIG_MAP: Record<ReportKey, Array<{ config: CsvDefinition; required: boolean }>> = {
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
// 🔁 ステップ構成＋モーダル内容（管理系専用）
// =====================================

// 自動処理用のステップ構成
const MANAGEMENT_AUTO_MODAL_STEPS = {
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
const MANAGEMENT_INTERACTIVE_MODAL_STEPS = {
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

// ===================================
// 📤 PDF出力関数（管理系専用）
// ===================================

const MANAGEMENT_PDF_GENERATOR_MAP: Record<ReportKey, () => Promise<string>> = {
    factory_report: async () => '/factory_report.pdf',
    balance_sheet: async () => '/balance_sheet.pdf',
    average_sheet: async () => '/average_sheet.pdf',
    block_unit_price: async () => '/block_unit_price.pdf',
    management_sheet: async () => '/management_sheet.pdf',
};

// ===================================
// 🔍 PDFプレビューURL（管理系専用）
// ===================================

const MANAGEMENT_PDF_PREVIEW_MAP: Record<ReportKey, string> = {
    factory_report: '/images/sampleViews/manage/factoryReport.png',
    balance_sheet: '/images/sampleViews/manage/balanceSheet.png',
    average_sheet: '/images/sampleViews/manage/averageSheet.png',
    block_unit_price: '/images/sampleViews/manage/blockunitPrice.png',
    management_sheet: '/images/sampleViews/manage/managementSheet.png',
};

// ==============================
// 🔧 ヘルパー関数実装
// ==============================

const getReportType = (reportKey: ReportKey): ReportType => {
    return MANAGEMENT_REPORT_KEYS[reportKey as keyof typeof MANAGEMENT_REPORT_KEYS]?.type || 'auto';
};

const getReportKeysByType = (type: ReportType): ReportKey[] => {
    return Object.entries(MANAGEMENT_REPORT_KEYS)
        .filter(([, config]) => config.type === type)
        .map(([key]) => key as ReportKey);
};

const getReportOptions = () => {
    return Object.values(MANAGEMENT_REPORT_KEYS);
};

const getAllModalSteps = (reportKey: ReportKey) => {
    const reportType = getReportType(reportKey);
    if (reportType === 'auto') {
        return MANAGEMENT_AUTO_MODAL_STEPS[reportKey as keyof typeof MANAGEMENT_AUTO_MODAL_STEPS] || [];
    } else {
        return MANAGEMENT_INTERACTIVE_MODAL_STEPS[reportKey as keyof typeof MANAGEMENT_INTERACTIVE_MODAL_STEPS] || [];
    }
};

// ==============================
// 📦 管理系帳票設定パッケージ
// ==============================

export const managementReportConfigPackage: ReportConfigPackage = {
    name: 'management',

    // 基本情報
    reportKeys: MANAGEMENT_REPORT_KEYS,

    // API設定
    apiUrlMap: MANAGEMENT_API_URL_MAP,

    // CSV設定
    csvConfigMap: MANAGEMENT_CSV_CONFIG_MAP,

    // ステップ設定
    autoModalStepsMap: MANAGEMENT_AUTO_MODAL_STEPS,
    interactiveModalStepsMap: MANAGEMENT_INTERACTIVE_MODAL_STEPS,

    // PDF関連
    pdfGeneratorMap: MANAGEMENT_PDF_GENERATOR_MAP,
    pdfPreviewMap: MANAGEMENT_PDF_PREVIEW_MAP,

    // ヘルパー関数
    getReportType,
    getReportKeysByType,
    getReportOptions,
    getAllModalSteps,
};

// ==============================
// 🔄 後方互換性エクスポート（段階的移行用）
// ==============================

// 既存コードとの互換性のため、古い名前でもエクスポート
export const {
    reportKeys: REPORT_KEYS,
    apiUrlMap: reportApiUrlMap,
    csvConfigMap,
    autoModalStepsMap,
    interactiveModalStepsMap,
    pdfGeneratorMap,
    pdfPreviewMap,
} = managementReportConfigPackage;

// 既存関数の互換性維持
export { getReportType, getReportKeysByType };
export type { ReportKey, ReportType } from '../../types/reportConfig';
