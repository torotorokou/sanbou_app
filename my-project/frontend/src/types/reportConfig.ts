// /app/src/types/reportConfig.ts
import type React from 'react';
import type { CsvDefinition } from '../constants/CsvDefinition';

// ==============================
// 🔧 汎用的な帳票設定の型定義
// ==============================

export type ReportType = 'auto' | 'interactive';

export type ReportKey = string;

export type ReportDefinition = {
    value: ReportKey;
    label: string;
    type: ReportType;
};

export type CsvConfigEntry = {
    config: CsvDefinition;
    required: boolean;
};

export type CsvConfigGroup = CsvConfigEntry[];

export type ModalStepConfig = {
    label: string;
    content: React.ReactNode;
    showNext?: boolean;
    showPrev?: boolean;
    showClose?: boolean;
    canProceed?: () => boolean;
};

// ==============================
// 🏗️ 汎用的な帳票設定インターフェース
// ==============================

export interface ReportConfigSet {
    // 基本情報
    reportKeys: Record<string, ReportDefinition>;

    // API設定
    apiUrlMap: Record<ReportKey, string>;

    // CSV設定
    csvConfigMap: Record<ReportKey, CsvConfigGroup>;

    // ステップ設定
    autoModalStepsMap: Record<ReportKey, ModalStepConfig[]>;
    interactiveModalStepsMap: Record<ReportKey, ModalStepConfig[]>;

    // PDF関連
    pdfGeneratorMap: Record<ReportKey, () => Promise<string>>;
    pdfPreviewMap: Record<ReportKey, string>;
}

// ==============================
// 🔧 ヘルパー関数の型定義
// ==============================

export interface ReportConfigHelpers {
    getReportType: (reportKey: ReportKey) => ReportType;
    getReportKeysByType: (type: ReportType) => ReportKey[];
    getReportOptions: () => ReportDefinition[];
    getAllModalSteps: (reportKey: ReportKey) => ModalStepConfig[];
}

// ==============================
// 📋 完全な帳票設定パッケージ
// ==============================

export interface ReportConfigPackage
    extends ReportConfigSet,
        ReportConfigHelpers {
    name: string; // 設定セットの名前（例：'management', 'factory', 'customer'）
}
