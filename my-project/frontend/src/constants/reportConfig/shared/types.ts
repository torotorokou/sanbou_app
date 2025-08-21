// /app/src/constants/reportConfig/shared/types.ts
import type React from 'react';
import type { CsvDefinition } from '../../CsvDefinition';

// ==============================
// 🎯 共通型定義
// ==============================

export type CsvConfig = CsvDefinition;

export type CsvConfigEntry = {
    config: CsvConfig;
    required: boolean;
};

export type CsvConfigGroup = CsvConfigEntry[];

export type ModalStepConfig = {
    label: string;
    content: React.ReactNode;
    showNext?: boolean;
    showClose?: boolean;
};

export type ReportConfig = {
    csvConfigs: CsvConfigGroup;
    steps: string[];
    previewImage: string;
    modalSteps: ModalStepConfig[];
};

// 帳票キー型（各ページ設定で拡張）
export type BaseReportKey = string;

// ページ設定インターフェース
export interface PageReportConfig<T extends BaseReportKey> {
    pageKey: string;
    reportKeys: Record<T, { readonly value: T; readonly label: string }>;
    csvConfigMap: Record<T, CsvConfigGroup>;
    modalStepsMap: Record<T, ModalStepConfig[]>;
    pdfGeneratorMap: Record<T, () => Promise<string>>;
    pdfPreviewMap: Record<T, string>;
}

// 帳簿期間タイプ（共通定義）
export type PeriodType = 'oneday' | 'oneweek' | 'onemonth';
