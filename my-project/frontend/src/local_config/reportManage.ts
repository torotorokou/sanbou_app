// src/config/managementReportConfig.ts

import {
    REPORT_KEYS,
    type ReportKey,
} from '@/constants/reportConfig/managementReportConfig';
import {
    csvConfigMap,
    stepConfigMap,
    pdfGeneratorMap,
} from '@/constants/reportConfig/managementReportConfig';

type CsvConfig = {
    label: string;
    onParse: (text: string) => void;
};

type ReportConfig = {
    reportKey: ReportKey;
    label: string;
    csvConfigs: CsvConfig[];
    steps: string[];
    generatePdf: () => Promise<string>;
};

export const reportConfigMap: Record<ReportKey, ReportConfig> = Object.keys(
    REPORT_KEYS
).reduce((acc, key) => {
    const reportKey = key as ReportKey;

    // csvConfigMapから適切な形式に変換
    const csvConfigEntries = csvConfigMap[reportKey] || [];
    const csvConfigs: CsvConfig[] = csvConfigEntries.map((entry) => ({
        label: entry.config.label,
        onParse: entry.config.onParse,
    }));

    acc[reportKey] = {
        reportKey,
        label: REPORT_KEYS[reportKey].label,
        csvConfigs,
        steps: stepConfigMap[reportKey],
        generatePdf: pdfGeneratorMap[reportKey],
    };
    return acc;
}, {} as Record<ReportKey, ReportConfig>);

export const getReportConfig = (key: ReportKey): ReportConfig =>
    reportConfigMap[key];
