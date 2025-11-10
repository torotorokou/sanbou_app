// features/report/model/config/pages/managePageConfig.ts
import React from "react";
import { Spin } from 'antd';
import { CSV_DEFINITIONS } from "@features/csv-schemas/domain/config/CsvDefinition";
import type { CsvConfigGroup, ModalStepConfig, PeriodType } from "@features/report/model/config/shared/types";
import { createReportConfig, SIMPLE_CREATE_AND_DONE_STEPS } from "@features/report/model/config/shared/common";

// ==============================
// 📄 管理業務ページ専用設定
// ==============================

export const MANAGE_REPORT_KEYS = {
  factory_report: {
    value: "factory_report",
    label: "工場日報",
    periodType: "oneday" as PeriodType,
  },
  balance_sheet: {
    value: "balance_sheet",
    label: "工場搬出入収支表",
    periodType: "oneday" as PeriodType,
  },
  average_sheet: {
    value: "average_sheet",
    label: "集計項目平均表",
    periodType: "oneday" as PeriodType,
  },
  block_unit_price: {
    value: "block_unit_price",
    label: "ブロック単価表",
    periodType: "oneday" as PeriodType,
  },
  management_sheet: {
    value: "management_sheet",
    label: "管理票",
    periodType: "oneday" as PeriodType,
  },
} as const;

export type ManageReportKey = keyof typeof MANAGE_REPORT_KEYS;
export const MANAGE_REPORT_OPTIONS = Object.values(MANAGE_REPORT_KEYS);

// ...common steps are imported from shared/common.ts

// CSV設定
export const manageCsvConfigMap: Record<ManageReportKey, CsvConfigGroup> = {
  factory_report: [
    { config: CSV_DEFINITIONS.shipment, required: true },
    { config: CSV_DEFINITIONS.yard, required: true },
  ],
  balance_sheet: [
    { config: CSV_DEFINITIONS.receive, required: false },
    { config: CSV_DEFINITIONS.shipment, required: true },
    { config: CSV_DEFINITIONS.yard, required: true },
  ],
  average_sheet: [{ config: CSV_DEFINITIONS.receive, required: true }],
  block_unit_price: [{ config: CSV_DEFINITIONS.shipment, required: true }],
  management_sheet: [
    { config: CSV_DEFINITIONS.receive, required: true },
    { config: CSV_DEFINITIONS.shipment, required: true },
    { config: CSV_DEFINITIONS.yard, required: true },
  ],
};

// モーダルステップ設定
export const manageModalStepsMap: Record<ManageReportKey, ModalStepConfig[]> = {
  // factory_report と balance_sheet は同じステップなので共通定義を使う
  factory_report: [...SIMPLE_CREATE_AND_DONE_STEPS],
  balance_sheet: [...SIMPLE_CREATE_AND_DONE_STEPS],
  average_sheet: [...SIMPLE_CREATE_AND_DONE_STEPS],
  block_unit_price: [
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
  management_sheet:[...SIMPLE_CREATE_AND_DONE_STEPS],
};

// PDFプレビュー設定
export const managePdfPreviewMap: Record<ManageReportKey, string> = {
  factory_report: "/images/sampleViews/manage/factoryReport.png",
  balance_sheet: "/images/sampleViews/manage/balanceSheet.png",
  average_sheet: "/images/sampleViews/manage/averageSheet.png",
  block_unit_price: "/images/sampleViews/manage/blockunitPrice.png",
  management_sheet: "/images/sampleViews/manage/managementSheet.png",
};

// 統合設定
export const manageReportConfigMap = createReportConfig(
  manageCsvConfigMap,
  manageModalStepsMap,
  managePdfPreviewMap
);
