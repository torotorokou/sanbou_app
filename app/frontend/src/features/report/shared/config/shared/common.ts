// /app/src/constants/reportConfig/shared/common.ts
import React from 'react';
import { Spin } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import type { CsvConfigGroup, ModalStepConfig, ReportConfig } from './types';
import { REPORT_ENDPOINTS, getReportEndpoint } from '@shared';

// ==============================
// 🌐 共通定数・設定
// ==============================

/**
 * APIエンドポイント定数
 * BFF統一: すべて /core_api 経由でアクセス
 *
 * @deprecated 代わりに @shared/config/apiEndpoints から直接インポートしてください
 */
export const CORE_API_URL = REPORT_ENDPOINTS.base;
export const LEDGER_REPORT_URL = REPORT_ENDPOINTS.base;

/**
 * 帳簿タイプ別APIエンドポイント設定
 * すべて core_api(BFF) 経由でアクセス
 *
 * @deprecated 代わりに @shared/config/apiEndpoints の REPORT_ENDPOINTS を使用してください
 */
export const REPORT_API_ENDPOINTS = {
  // 工場日報系
  factory_report: REPORT_ENDPOINTS.factoryReport,
  // 互換キー（工場実績報告書）→ 同じエンドポイントを使用
  factory_report2: REPORT_ENDPOINTS.factoryReport2,

  // 収支・管理表系
  balance_sheet: REPORT_ENDPOINTS.balanceSheet,
  average_sheet: REPORT_ENDPOINTS.averageSheet,
  management_sheet: REPORT_ENDPOINTS.managementSheet,

  // インタラクティブ帳簿系
  block_unit_price: REPORT_ENDPOINTS.blockUnitPrice,

  // 台帳系（将来追加用）
  ledger_book: REPORT_ENDPOINTS.ledgerBook,
} as const;

/**
 * 帳簿タイプからAPIエンドポイントを取得
 *
 * @deprecated 代わりに @shared/config/apiEndpoints の getReportEndpoint を使用してください
 */
export const getApiEndpoint = getReportEndpoint;

/**
 * インタラクティブ帳簿の設定
 */
export const INTERACTIVE_REPORTS = {
  block_unit_price: {
    modalComponent: 'BlockUnitPriceInteractiveModal',
    multiStep: true,
    requiresUserInput: true,
  },
  // 将来的な追加用
  custom_pricing: {
    modalComponent: 'CustomPricingModal',
    multiStep: true,
    requiresUserInput: true,
  },
} as const;

// 共通のシンプルなモーダルステップ（作成中 -> 完了）
export const SIMPLE_CREATE_AND_DONE_STEPS: ModalStepConfig[] = [
  {
    label: '帳簿作成中',
    content: React.createElement(
      'div',
      { style: { textAlign: 'center', padding: 24 } },
      React.createElement(Spin, { size: 'large' })
    ),
    showNext: false,
    showClose: false,
  },
  {
    label: '完了',
    content: React.createElement(
      'div',
      { style: { textAlign: 'center', padding: 40 } },
      React.createElement(CheckCircleOutlined, {
        style: { fontSize: 48, color: '#52c41a' },
      }),
      React.createElement('h3', { style: { marginTop: 16 } }, '完了しました！'),
      React.createElement('p', {}, '帳簿が正常に生成されました。')
    ),
    showNext: false,
    showClose: true,
  },
];

/**
 * 帳簿がインタラクティブタイプかチェック
 */
export const isInteractiveReport = (reportKey: string): boolean => {
  return reportKey in INTERACTIVE_REPORTS;
};

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
        steps: modalStepsMap[key as T].map((step: ModalStepConfig) => step.label),
        previewImage: pdfPreviewMap[key as T],
        modalSteps: modalStepsMap[key as T],
      },
    ])
  ) as Record<T, ReportConfig>;
};
