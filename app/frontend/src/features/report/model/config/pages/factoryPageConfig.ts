// features/report/model/config/pages/factoryPageConfig.ts
import React from "react";
import { Spin } from 'antd';
import { CSV_DEFINITIONS } from "@features/csv-schemas/domain/config/CsvDefinition";
import type {
  CsvConfigGroup,
  ModalStepConfig,
  PeriodType,
} from "@features/report/model/config/shared/types";
import { createReportConfig } from "@features/report/model/config/shared/common";

// ==============================
// 🏭 工場ページ専用設定
// ==============================

export const FACTORY_REPORT_KEYS = {
  factory_report2: {
    value: "factory_report2",
    label: "実績報告書",
    periodType: "oneday" as PeriodType,
  },

} as const;

export type FactoryReportKey = keyof typeof FACTORY_REPORT_KEYS;
export const FACTORY_REPORT_OPTIONS = Object.values(FACTORY_REPORT_KEYS);

// CSV設定
export const factoryCsvConfigMap: Record<FactoryReportKey, CsvConfigGroup> = {
  factory_report2: [
    { config: CSV_DEFINITIONS.shipment, required: true },
    { config: CSV_DEFINITIONS.yard, required: true },
  ],
};

// モーダルステップ設定
export const factoryModalStepsMap: Record<FactoryReportKey, ModalStepConfig[]> =
  {
    factory_report2: [
      {
        label: "帳簿作成中",
        content: React.createElement(
          "div",
          { style: { textAlign: 'center', padding: 24 } },
          React.createElement(Spin, { size: 'large' })
        ),
        showNext: false,
        showClose: false,
      },
      {
        label: "完了",
        content: React.createElement("div", {}, "完了しました"),
        showNext: false,
        showClose: true,
      },
    ],
  };

// PDFプレビュー設定
export const factoryPdfPreviewMap: Record<FactoryReportKey, string> = {
  factory_report2: "/images/sampleViews/manage/factoryReport2.png",
};

// 統合設定
export const factoryReportConfigMap = createReportConfig(
  factoryCsvConfigMap,
  factoryModalStepsMap,
  factoryPdfPreviewMap
);
