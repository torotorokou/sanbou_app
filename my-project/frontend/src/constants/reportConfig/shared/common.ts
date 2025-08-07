// /app/src/constants/reportConfig/shared/common.ts
import type { CsvConfigGroup, ModalStepConfig, ReportConfig } from './types';

// ==============================
// 🌐 共通定数・設定
// ==============================

/**
 * APIエンドポイント定数
 */
export const LEDGER_API_URL = '/ledger_api/report/manage';

/**
 * 共通ユーティリティ関数
 */
export const createReportConfig = <T extends string>(
    csvConfigMap: Record<T, CsvConfigGroup>,
    modalStepsMap: Record<T, ModalStepConfig[]>,
    pdfPreviewMap: Record<T, string>
): Record<T, ReportConfig> => {
    return Object.fromEntries(
        Object.keys(csvConfigMap).map((key) => [
            key,
            {
                csvConfigs: csvConfigMap[key as T],
                steps: modalStepsMap[key as T].map(
                    (step: ModalStepConfig) => step.label
                ),
                previewImage: pdfPreviewMap[key as T],
                modalSteps: modalStepsMap[key as T],
            },
        ])
    ) as Record<T, ReportConfig>;
};
