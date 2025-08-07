// /app/src/constants/reportConfig/factoryReportConfig.tsx
import React from 'react';

import type { CsvDefinition } from '../CsvDefinition';
import { CSV_DEFINITIONS } from '../CsvDefinition';

// ==============================
// 🏭 工場帳簿専用設定
// ==============================

// APIエンドポイント定数
export const FACTORY_REPORT_COMMON_API_URL = '/ledger_api/factory/report/manage';
export const FACTORY_REPORT_INTERACTIVE_API_URL = '/ledger_api/factory/interactive/upload-and-start';

// 工場帳簿定義
export const FACTORY_REPORT_KEYS = {
    // 実績系帳簿
    performance_report: { value: 'performance_report', label: '実績報告書', type: 'auto' },
    production_efficiency: { value: 'production_efficiency', label: '生産効率表', type: 'auto' },

    // 物流系帳簿
    transport_volume_report: { value: 'transport_volume_report', label: '搬入量表', type: 'auto' },
    inventory_summary: { value: 'inventory_summary', label: '在庫集計表', type: 'auto' },

    // 品質・監視系帳簿（インタラクティブ）
    quality_inspection_sheet: { value: 'quality_inspection_sheet', label: '品質検査表', type: 'interactive' },
    environmental_monitoring: { value: 'environmental_monitoring', label: '環境監視レポート', type: 'auto' },

    // 管理系帳簿（インタラクティブ）
    monthly_operation_report: { value: 'monthly_operation_report', label: '月次運営報告書', type: 'interactive' },
    cost_analysis_report: { value: 'cost_analysis_report', label: 'コスト分析表', type: 'interactive' },
} as const;

export type FactoryReportKey = keyof typeof FACTORY_REPORT_KEYS;
export type FactoryReportType = 'auto' | 'interactive';
export const FACTORY_REPORT_OPTIONS = Object.values(FACTORY_REPORT_KEYS);

// ヘルパー関数
export const getFactoryReportType = (reportKey: FactoryReportKey): FactoryReportType => {
    return FACTORY_REPORT_KEYS[reportKey].type;
};

export const getFactoryReportKeysByType = (type: FactoryReportType): FactoryReportKey[] => {
    return Object.entries(FACTORY_REPORT_KEYS)
        .filter(([, config]) => config.type === type)
        .map(([key]) => key as FactoryReportKey);
};

// APIエンドポイントマップ
export const factoryReportApiUrlMap: Record<FactoryReportKey, string> = {
    performance_report: FACTORY_REPORT_COMMON_API_URL,
    production_efficiency: FACTORY_REPORT_COMMON_API_URL,
    transport_volume_report: FACTORY_REPORT_COMMON_API_URL,
    inventory_summary: FACTORY_REPORT_COMMON_API_URL,
    environmental_monitoring: FACTORY_REPORT_COMMON_API_URL,

    // インタラクティブタイプ
    quality_inspection_sheet: FACTORY_REPORT_INTERACTIVE_API_URL,
    monthly_operation_report: FACTORY_REPORT_INTERACTIVE_API_URL,
    cost_analysis_report: FACTORY_REPORT_INTERACTIVE_API_URL,
};

// =================================
// 📄 工場帳簿用CSV設定
// =================================

export type FactoryCsvConfig = CsvDefinition;

export type FactoryCsvConfigEntry = {
    config: FactoryCsvConfig;
    required: boolean;
};

export type FactoryCsvConfigGroup = FactoryCsvConfigEntry[];

export const factoryCsvConfigMap: Record<FactoryReportKey, FactoryCsvConfigGroup> = {
    // 実績報告書 - 実績データ + 生産ログ
    performance_report: [
        { config: CSV_DEFINITIONS.performance_data, required: true },
        { config: CSV_DEFINITIONS.production_log, required: true },
        { config: CSV_DEFINITIONS.shipment, required: false },
    ],

    // 生産効率表 - 生産ログ + 実績データ
    production_efficiency: [
        { config: CSV_DEFINITIONS.production_log, required: true },
        { config: CSV_DEFINITIONS.performance_data, required: false },
    ],

    // 搬入量表 - 搬入量データ + 出荷データ
    transport_volume_report: [
        { config: CSV_DEFINITIONS.transport_volume, required: true },
        { config: CSV_DEFINITIONS.shipment, required: true },
    ],

    // 在庫集計表 - 在庫データ
    inventory_summary: [
        { config: CSV_DEFINITIONS.inventory_data, required: true },
        { config: CSV_DEFINITIONS.receive, required: false },
    ],

    // 品質検査表 - 品質検査データ + 生産ログ
    quality_inspection_sheet: [
        { config: CSV_DEFINITIONS.quality_check, required: true },
        { config: CSV_DEFINITIONS.production_log, required: true },
    ],

    // 環境監視レポート - 環境監視データ
    environmental_monitoring: [
        { config: CSV_DEFINITIONS.environmental_data, required: true },
    ],

    // 月次運営報告書 - 運営ログ + 実績データ + コストデータ
    monthly_operation_report: [
        { config: CSV_DEFINITIONS.operation_log, required: true },
        { config: CSV_DEFINITIONS.performance_data, required: true },
        { config: CSV_DEFINITIONS.cost_data, required: true },
    ],

    // コスト分析表 - コストデータ + 出荷データ
    cost_analysis_report: [
        { config: CSV_DEFINITIONS.cost_data, required: true },
        { config: CSV_DEFINITIONS.shipment, required: true },
    ],
};

// =====================================
// 🔁 工場帳簿用ステップ構成
// =====================================

export type FactoryModalStepConfig = {
    label: string;
    content: React.ReactNode;
    showNext?: boolean;
    showPrev?: boolean;
    showClose?: boolean;
    canProceed?: () => boolean;
};

// 自動処理用ステップ
export const factoryAutoModalStepsMap: Record<string, FactoryModalStepConfig[]> = {
    performance_report: [
        { label: '実績データ処理中', content: <div>実績報告書を作成中です...</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>実績報告書が完成しました！</div>, showNext: false, showClose: true },
    ],
    production_efficiency: [
        { label: '生産効率分析中', content: <div>生産効率表を作成中です...</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>生産効率表が完成しました！</div>, showNext: false, showClose: true },
    ],
    transport_volume_report: [
        { label: '搬入量集計中', content: <div>搬入量表を作成中です...</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>搬入量表が完成しました！</div>, showNext: false, showClose: true },
    ],
    inventory_summary: [
        { label: '在庫集計中', content: <div>在庫集計表を作成中です...</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>在庫集計表が完成しました！</div>, showNext: false, showClose: true },
    ],
    environmental_monitoring: [
        { label: '環境データ分析中', content: <div>環境監視レポートを作成中です...</div>, showNext: false, showClose: false },
        { label: '完了', content: <div>環境監視レポートが完成しました！</div>, showNext: false, showClose: true },
    ],
};

// インタラクティブ処理用ステップ
export const factoryInteractiveModalStepsMap: Record<string, FactoryModalStepConfig[]> = {
    quality_inspection_sheet: [
        { label: 'データ処理', content: null, showNext: true, showClose: false },
        { label: '品質基準設定', content: null, showNext: true, showClose: false },
        { label: '検査項目選択', content: null, showNext: true, showPrev: true, showClose: false },
        { label: '帳簿生成', content: null, showNext: false, showClose: false },
        { label: '完了', content: null, showNext: false, showClose: true },
    ],
    monthly_operation_report: [
        { label: 'データ処理', content: null, showNext: true, showClose: false },
        { label: '集計期間設定', content: null, showNext: true, showClose: false },
        { label: 'レポート項目選択', content: null, showNext: true, showPrev: true, showClose: false },
        { label: '帳簿生成', content: null, showNext: false, showClose: false },
        { label: '完了', content: null, showNext: false, showClose: true },
    ],
    cost_analysis_report: [
        { label: 'データ処理', content: null, showNext: true, showClose: false },
        { label: 'コスト分類設定', content: null, showNext: true, showClose: false },
        { label: '分析範囲選択', content: null, showNext: true, showPrev: true, showClose: false },
        { label: '帳簿生成', content: null, showNext: false, showClose: false },
        { label: '完了', content: null, showNext: false, showClose: true },
    ],
};

// 統合ステップマップ
export const factoryModalStepsMap: Record<FactoryReportKey, FactoryModalStepConfig[]> = {
    ...factoryAutoModalStepsMap,
    ...factoryInteractiveModalStepsMap,
} as Record<FactoryReportKey, FactoryModalStepConfig[]>;

// ===================================
// 📤 工場帳簿用PDF生成
// ===================================

export const factoryPdfGeneratorMap: Record<FactoryReportKey, () => Promise<string>> = {
    performance_report: async () => '/factory/performance_report.pdf',
    production_efficiency: async () => '/factory/production_efficiency.pdf',
    transport_volume_report: async () => '/factory/transport_volume_report.pdf',
    inventory_summary: async () => '/factory/inventory_summary.pdf',
    quality_inspection_sheet: async () => '/factory/quality_inspection_sheet.pdf',
    environmental_monitoring: async () => '/factory/environmental_monitoring.pdf',
    monthly_operation_report: async () => '/factory/monthly_operation_report.pdf',
    cost_analysis_report: async () => '/factory/cost_analysis_report.pdf',
};

// ===================================
// 🔍 工場帳簿用PDFプレビュー
// ===================================

export const factoryPdfPreviewMap: Record<FactoryReportKey, string> = {
    performance_report: '/images/sampleViews/factory/performanceReport.png',
    production_efficiency: '/images/sampleViews/factory/productionEfficiency.png',
    transport_volume_report: '/images/sampleViews/factory/transportVolumeReport.png',
    inventory_summary: '/images/sampleViews/factory/inventorySummary.png',
    quality_inspection_sheet: '/images/sampleViews/factory/qualityInspectionSheet.png',
    environmental_monitoring: '/images/sampleViews/factory/environmentalMonitoring.png',
    monthly_operation_report: '/images/sampleViews/factory/monthlyOperationReport.png',
    cost_analysis_report: '/images/sampleViews/factory/costAnalysisReport.png',
};

// ===================================
// 🔧 工場帳簿設定マップ（統合）
// ===================================

export const factoryReportConfigMap: Record<
    FactoryReportKey,
    {
        csvConfigs: FactoryCsvConfigGroup;
        steps: string[];
        generatePdf: () => Promise<string>;
        previewImage: string;
        type: FactoryReportType;
    }
> = Object.fromEntries(
    Object.keys(FACTORY_REPORT_KEYS).map((key) => {
        const reportKey = key as FactoryReportKey;
        const reportConfig = FACTORY_REPORT_KEYS[reportKey];
        const steps = reportConfig.type === 'auto'
            ? factoryAutoModalStepsMap[reportKey]?.map(step => step.label) || []
            : factoryInteractiveModalStepsMap[reportKey]?.map(step => step.label) || [];

        return [
            key,
            {
                csvConfigs: factoryCsvConfigMap[reportKey],
                steps,
                generatePdf: factoryPdfGeneratorMap[reportKey],
                previewImage: factoryPdfPreviewMap[reportKey],
                type: reportConfig.type,
            },
        ];
    })
) as Record<
    FactoryReportKey,
    {
        csvConfigs: FactoryCsvConfigGroup;
        steps: string[];
        generatePdf: () => Promise<string>;
        previewImage: string;
        type: FactoryReportType;
    }
>;
