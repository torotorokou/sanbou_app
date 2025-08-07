// /app/src/constants/reportConfig/legacyReportConfigSet.tsx
import React from 'react';
import type { ReportConfigPackage, ReportType, ReportKey } from '../../types/reportConfig';
import type { CsvDefinition } from '../CsvDefinition';
import { CSV_DEFINITIONS } from '../CsvDefinition';

/**
 * 既存ReportFactory.tsx用の設定パッケージ
 * 
 * 既存のReportFactory.tsxページを新しい汎用システムに統合するための
 * 互換性設定パッケージ
 */

const LEGACY_REPORT_KEYS = {
    legacy_factory_report: {
        value: 'legacy_factory_report',
        label: '工場レポート（レガシー）',
        type: 'auto' as ReportType
    },
} as const;

const LEGACY_API_URL_MAP: Record<ReportKey, string> = {
    legacy_factory_report: '/legacy_api/factory_report',
};

const LEGACY_CSV_CONFIG_MAP: Record<ReportKey, Array<{ config: CsvDefinition; required: boolean }>> = {
    legacy_factory_report: [
        { config: CSV_DEFINITIONS.shipment, required: true },   // 出荷一覧
        { config: CSV_DEFINITIONS.yard, required: false },      // ヤード一覧
        { config: CSV_DEFINITIONS.receive, required: false },   // 受入一覧
    ],
};

const LEGACY_AUTO_MODAL_STEPS = {
    legacy_factory_report: [
        {
            label: 'データ選択',
            content: (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                    <p>帳簿を作成する準備が整いました。</p>
                </div>
            ),
            showNext: true,
            showClose: false
        },
        {
            label: 'PDF生成中',
            content: (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                    <div>帳簿をPDFに変換中です...</div>
                </div>
            ),
            showNext: false,
            showClose: false
        },
        {
            label: '完了',
            content: (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                    <div style={{ color: '#52c41a' }}>✅ PDF帳簿が作成されました。</div>
                </div>
            ),
            showNext: false,
            showClose: true
        },
    ],
};

const LEGACY_INTERACTIVE_MODAL_STEPS = {};

const LEGACY_PDF_GENERATOR_MAP: Record<ReportKey, () => Promise<string>> = {
    legacy_factory_report: async () => '/factory_report.pdf',
};

const LEGACY_PDF_PREVIEW_MAP: Record<ReportKey, string> = {
    legacy_factory_report: '/images/sampleViews/legacy/factoryReport.png',
};

// ヘルパー関数
const getReportType = (reportKey: ReportKey): ReportType => {
    return LEGACY_REPORT_KEYS[reportKey as keyof typeof LEGACY_REPORT_KEYS]?.type || 'auto';
};

const getReportKeysByType = (type: ReportType): ReportKey[] => {
    return Object.entries(LEGACY_REPORT_KEYS)
        .filter(([, config]) => config.type === type)
        .map(([key]) => key as ReportKey);
};

const getReportOptions = () => {
    return Object.values(LEGACY_REPORT_KEYS);
};

const getAllModalSteps = (reportKey: ReportKey) => {
    const reportType = getReportType(reportKey);
    if (reportType === 'auto') {
        return LEGACY_AUTO_MODAL_STEPS[reportKey as keyof typeof LEGACY_AUTO_MODAL_STEPS] || [];
    } else {
        return LEGACY_INTERACTIVE_MODAL_STEPS[reportKey as keyof typeof LEGACY_INTERACTIVE_MODAL_STEPS] || [];
    }
};

// レガシー設定パッケージ
export const legacyReportConfigPackage: ReportConfigPackage = {
    name: 'legacy',

    reportKeys: LEGACY_REPORT_KEYS,
    apiUrlMap: LEGACY_API_URL_MAP,
    csvConfigMap: LEGACY_CSV_CONFIG_MAP,
    autoModalStepsMap: LEGACY_AUTO_MODAL_STEPS,
    interactiveModalStepsMap: LEGACY_INTERACTIVE_MODAL_STEPS,
    pdfGeneratorMap: LEGACY_PDF_GENERATOR_MAP,
    pdfPreviewMap: LEGACY_PDF_PREVIEW_MAP,

    getReportType,
    getReportKeysByType,
    getReportOptions,
    getAllModalSteps,
};
