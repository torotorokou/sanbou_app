// features/report/model/config/index.ts
// レポート設定の統合エクスポート

// ==============================
// 🎯 統合エクスポート・設定管理
// ==============================

// 共通型・ユーティリティ
export * from "./shared/types";
export * from "./shared/common";

// 主要な型のre-export
export type { ModalStepConfig, CsvConfigGroup } from "./shared/types";

// 新しい関数のre-export
export {
  getApiEndpoint,
  isInteractiveReport,
  REPORT_API_ENDPOINTS,
  INTERACTIVE_REPORTS,
} from "./shared/common";

// ページ別設定
export * from "./pages/managePageConfig";
export * from "./pages/factoryPageConfig";
export * from "./pages/ledgerPageConfig";

// ==============================
// 🌐 統合設定（後方互換性のため）
// ==============================

import {
  MANAGE_REPORT_KEYS,
  type ManageReportKey,
  manageReportConfigMap,
  manageModalStepsMap,
} from "./pages/managePageConfig";
import {
  FACTORY_REPORT_KEYS,
  type FactoryReportKey,
  factoryReportConfigMap,
  factoryModalStepsMap,
} from "./pages/factoryPageConfig";
import {
  LEDGER_REPORT_KEYS,
  type LedgerReportKey,
  ledgerReportConfigMap,
  ledgerModalStepsMap,
} from "./pages/ledgerPageConfig";

// 全帳票キーの統合（既存コードとの互換性のため）
export const REPORT_KEYS = {
  ...MANAGE_REPORT_KEYS,
  ...FACTORY_REPORT_KEYS,
  ...LEDGER_REPORT_KEYS,
} as const;

export type ReportKey = ManageReportKey | FactoryReportKey | LedgerReportKey;
export const REPORT_OPTIONS = Object.values(REPORT_KEYS);

// ページグループ設定
export const PAGE_REPORT_GROUPS = {
  manage: Object.values(MANAGE_REPORT_KEYS),
  factory: Object.values(FACTORY_REPORT_KEYS),
  ledger: Object.values(LEDGER_REPORT_KEYS),
  all: Object.values(REPORT_KEYS),
} as const;

export type PageGroupKey = keyof typeof PAGE_REPORT_GROUPS;

// 統合設定マップ（既存コードとの互換性のため）
export const reportConfigMap = {
  ...manageReportConfigMap,
  ...factoryReportConfigMap,
  ...ledgerReportConfigMap,
};

export const modalStepsMap = {
  ...manageModalStepsMap,
  ...factoryModalStepsMap,
  ...ledgerModalStepsMap,
};

// PDF関連の統合マップ
import {
  managePdfPreviewMap,
  manageCsvConfigMap,
} from "./pages/managePageConfig";
import {
  factoryPdfPreviewMap,
  factoryCsvConfigMap,
} from "./pages/factoryPageConfig";
import {
  ledgerPdfPreviewMap,
  ledgerCsvConfigMap,
} from "./pages/ledgerPageConfig";

export const pdfPreviewMap = {
  ...managePdfPreviewMap,
  ...factoryPdfPreviewMap,
  ...ledgerPdfPreviewMap,
};

export const csvConfigMap = {
  ...manageCsvConfigMap,
  ...factoryCsvConfigMap,
  ...ledgerCsvConfigMap,
};

// ==============================
// 🔍 ページ別設定取得ヘルパー
// ==============================

/**
 * ページキーに基づいて適切な設定を取得
 */
export const getPageConfig = (pageKey: PageGroupKey) => {
  switch (pageKey) {
    case "manage":
      return {
        reportKeys: MANAGE_REPORT_KEYS,
        reportOptions: Object.values(MANAGE_REPORT_KEYS),
        configMap: manageReportConfigMap,
        modalSteps: manageModalStepsMap,
      };
    case "factory":
      return {
        reportKeys: FACTORY_REPORT_KEYS,
        reportOptions: Object.values(FACTORY_REPORT_KEYS),
        configMap: factoryReportConfigMap,
        modalSteps: factoryModalStepsMap,
      };
    case "ledger":
      return {
        reportKeys: LEDGER_REPORT_KEYS,
        reportOptions: Object.values(LEDGER_REPORT_KEYS),
        configMap: ledgerReportConfigMap,
        modalSteps: ledgerModalStepsMap,
      };
    case "all":
      return {
        reportKeys: REPORT_KEYS,
        reportOptions: REPORT_OPTIONS,
        configMap: reportConfigMap,
        modalSteps: modalStepsMap,
      };
    default:
      throw new Error(`Unknown page key: ${pageKey}`);
  }
};
