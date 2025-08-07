// /app/src/constants/reportConfig/factoryReportConfigSet.tsx
import React from 'react';
import type { ReportConfigPackage, ReportType, ReportKey } from '../../types/reportConfig';
import type { CsvDefinition } from '../CsvDefinition';
import { CSV_DEFINITIONS } from '../CsvDefinition';

/**
 * 工場系帳票設定パッケージの例
 * 
 * 新しい帳票タイプが簡単に追加できることを実証
 */

const FACTORY_REPORT_KEYS = {
    production_report: { value: 'production_report', label: '生産実績報告書', type: 'auto' as ReportType },
    quality_report: { value: 'quality_report', label: '品質管理レポート', type: 'interactive' as ReportType },
    maintenance_report: { value: 'maintenance_report', label: '設備保守点検表', type: 'auto' as ReportType },
} as const;

const FACTORY_API_URL_MAP: Record<ReportKey, string> = {
    production_report: '/factory_api/production/report',
    quality_report: '/factory_api/quality/interactive',
    maintenance_report: '/factory_api/maintenance/report',
};

const FACTORY_CSV_CONFIG_MAP: Record<ReportKey, Array<{ config: CsvDefinition; required: boolean }>> = {
    production_report: [
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: false },
    ],
    quality_report: [
        { config: CSV_DEFINITIONS.receive, required: true },
    ],
    maintenance_report: [
        { config: CSV_DEFINITIONS.shipment, required: true },
        { config: CSV_DEFINITIONS.yard, required: true },
    ],
};

const FACTORY_AUTO_MODAL_STEPS = {
    production_report: [
        { label: '生産データ処理中', content: <div>生産実績を集計中です...</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>生産実績報告書が完成しました</div>, showNext: false, showClose: true },
    ],
    maintenance_report: [
        { label: '保守データ処理中', content: <div>保守点検データを処理中です...</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>保守点検表が完成しました</div>, showNext: false, showClose: true },
    ],
};

const FACTORY_INTERACTIVE_MODAL_STEPS = {
    quality_report: [
        {
            label: 'データ分析',
            content: null,
            showNext: true,
            showClose: false
        },
        {
            label: '品質基準設定',
            content: null,
            showNext: true,
            showClose: false,
            canProceed: () => {
                // 品質基準が設定されているかチェック
                return true; // 簡易版
            }
        },
        {
            label: 'レポート生成',
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

const FACTORY_PDF_GENERATOR_MAP: Record<ReportKey, () => Promise<string>> = {
    production_report: async () => '/factory_production_report.pdf',
    quality_report: async () => '/factory_quality_report.pdf',
    maintenance_report: async () => '/factory_maintenance_report.pdf',
};

const FACTORY_PDF_PREVIEW_MAP: Record<ReportKey, string> = {
    production_report: '/images/sampleViews/factory/productionReport.png',
    quality_report: '/images/sampleViews/factory/qualityReport.png',
    maintenance_report: '/images/sampleViews/factory/maintenanceReport.png',
};

// ヘルパー関数
const getReportType = (reportKey: ReportKey): ReportType => {
    return FACTORY_REPORT_KEYS[reportKey as keyof typeof FACTORY_REPORT_KEYS]?.type || 'auto';
};

const getReportKeysByType = (type: ReportType): ReportKey[] => {
    return Object.entries(FACTORY_REPORT_KEYS)
        .filter(([, config]) => config.type === type)
        .map(([key]) => key as ReportKey);
};

const getReportOptions = () => {
    return Object.values(FACTORY_REPORT_KEYS);
};

const getAllModalSteps = (reportKey: ReportKey) => {
    const reportType = getReportType(reportKey);
    if (reportType === 'auto') {
        return FACTORY_AUTO_MODAL_STEPS[reportKey as keyof typeof FACTORY_AUTO_MODAL_STEPS] || [];
    } else {
        return FACTORY_INTERACTIVE_MODAL_STEPS[reportKey as keyof typeof FACTORY_INTERACTIVE_MODAL_STEPS] || [];
    }
};

// 工場系帳票設定パッケージ
export const factoryReportConfigPackage: ReportConfigPackage = {
    name: 'factory',

    reportKeys: FACTORY_REPORT_KEYS,
    apiUrlMap: FACTORY_API_URL_MAP,
    csvConfigMap: FACTORY_CSV_CONFIG_MAP,
    autoModalStepsMap: FACTORY_AUTO_MODAL_STEPS,
    interactiveModalStepsMap: FACTORY_INTERACTIVE_MODAL_STEPS,
    pdfGeneratorMap: FACTORY_PDF_GENERATOR_MAP,
    pdfPreviewMap: FACTORY_PDF_PREVIEW_MAP,

    getReportType,
    getReportKeysByType,
    getReportOptions,
    getAllModalSteps,
};
