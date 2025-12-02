/**
 * API Endpoint Configuration
 * Single Source of Truth for all API endpoints
 * 
 * すべてのAPI呼び出しはこのファイルで定義されたエンドポイントを経由する
 * 
 * @module shared/config/apiEndpoints
 * @created 2024-12-02
 * @refactoring P0: API設定統合 (refactor/centralize-scattered-concerns)
 */

/**
 * Core API ベースパス（BFF統一）
 * すべてのAPI呼び出しは /core_api を経由してバックエンドにルーティングされる
 */
export const CORE_API_BASE = '/core_api';

/**
 * レポート系API
 * 各種帳簿・レポート生成に関するエンドポイント
 */
export const REPORT_ENDPOINTS = {
  /** レポートAPIベース */
  base: `${CORE_API_BASE}/reports`,
  
  // 工場日報系
  /** 工場日報 */
  factoryReport: `${CORE_API_BASE}/reports/factory_report`,
  /** 工場実績報告書（factory_reportと同じエンドポイントを使用） */
  factoryReport2: `${CORE_API_BASE}/reports/factory_report`,
  
  // 収支・管理表系
  /** 収支表 */
  balanceSheet: `${CORE_API_BASE}/reports/balance_sheet`,
  /** 平均単価表 */
  averageSheet: `${CORE_API_BASE}/reports/average_sheet`,
  /** 管理票 */
  managementSheet: `${CORE_API_BASE}/reports/management_sheet`,
  
  // インタラクティブ帳簿系
  /** ブロック単価インタラクティブ処理 */
  blockUnitPrice: `${CORE_API_BASE}/block_unit_price_interactive`,
  
  // 台帳系
  /** 台帳 */
  ledgerBook: `${CORE_API_BASE}/reports/ledger`,
} as const;

/**
 * ダッシュボード系API
 * 受入予測、実績データなどのダッシュボード表示用エンドポイント
 */
export const DASHBOARD_ENDPOINTS = {
  // 受入系
  /** 受入日次データ */
  inboundDaily: `${CORE_API_BASE}/inbound/daily`,
  /** 受入予測データ */
  inboundForecast: `${CORE_API_BASE}/inbound/forecast`,
  
  // カレンダー
  /** 営業カレンダー（月単位） */
  calendar: `${CORE_API_BASE}/calendar/month`,
} as const;

/**
 * データベース系API
 * CSVアップロード、履歴管理、プレビューなど
 */
export const DATABASE_ENDPOINTS = {
  /** CSVアップロード */
  upload: `${CORE_API_BASE}/csv/upload`,
  /** アップロード履歴 */
  history: `${CORE_API_BASE}/csv/history`,
  /** CSVプレビュー */
  preview: `${CORE_API_BASE}/csv/preview`,
} as const;

/**
 * RAG・AI系API
 * チャット、検索、マニュアル参照など
 */
export const RAG_ENDPOINTS = {
  /** RAGチャット */
  chat: `${CORE_API_BASE}/rag/chat`,
  /** RAG検索 */
  search: `${CORE_API_BASE}/rag/search`,
} as const;

/**
 * マニュアル系API
 * 将軍マニュアル検索、取込など
 */
export const MANUAL_ENDPOINTS = {
  /** 将軍マニュアル検索 */
  shogunSearch: `${CORE_API_BASE}/manual/shogun/search`,
  /** 将軍マニュアル取込 */
  shogunImport: `${CORE_API_BASE}/manual/shogun/import`,
} as const;

/**
 * 全エンドポイントの型安全な参照
 * 各ドメイン別にグルーピングされたエンドポイント集
 */
export const API_ENDPOINTS = {
  /** レポート系 */
  report: REPORT_ENDPOINTS,
  /** ダッシュボード系 */
  dashboard: DASHBOARD_ENDPOINTS,
  /** データベース系 */
  database: DATABASE_ENDPOINTS,
  /** RAG・AI系 */
  rag: RAG_ENDPOINTS,
  /** マニュアル系 */
  manual: MANUAL_ENDPOINTS,
} as const;

/**
 * レポートキーからエンドポイントを取得するヘルパー関数
 * 
 * @param reportKey - レポートキー（例: 'factory_report', 'balance_sheet'）
 * @returns エンドポイントURL
 * 
 * @example
 * ```typescript
 * const endpoint = getReportEndpoint('factory_report');
 * // => '/core_api/reports/factory_report'
 * ```
 */
export function getReportEndpoint(reportKey: string): string {
  const endpoints: Record<string, string> = {
    factory_report: REPORT_ENDPOINTS.factoryReport,
    factory_report2: REPORT_ENDPOINTS.factoryReport2,
    balance_sheet: REPORT_ENDPOINTS.balanceSheet,
    average_sheet: REPORT_ENDPOINTS.averageSheet,
    management_sheet: REPORT_ENDPOINTS.managementSheet,
    block_unit_price: REPORT_ENDPOINTS.blockUnitPrice,
    ledger_book: REPORT_ENDPOINTS.ledgerBook,
  };
  return endpoints[reportKey] || REPORT_ENDPOINTS.base;
}

/**
 * ダッシュボードキーからエンドポイントを取得するヘルパー関数
 * 
 * @param dashboardKey - ダッシュボードキー
 * @returns エンドポイントURL
 */
export function getDashboardEndpoint(dashboardKey: string): string {
  const endpoints: Record<string, string> = {
    inbound_daily: DASHBOARD_ENDPOINTS.inboundDaily,
    inbound_forecast: DASHBOARD_ENDPOINTS.inboundForecast,
    calendar: DASHBOARD_ENDPOINTS.calendar,
  };
  return endpoints[dashboardKey] || DASHBOARD_ENDPOINTS.inboundDaily;
}

/**
 * エンドポイント型定義
 * 型安全なエンドポイント参照のための型
 */
export type ReportEndpointKey = keyof typeof REPORT_ENDPOINTS;
export type DashboardEndpointKey = keyof typeof DASHBOARD_ENDPOINTS;
export type DatabaseEndpointKey = keyof typeof DATABASE_ENDPOINTS;
export type RagEndpointKey = keyof typeof RAG_ENDPOINTS;
export type ManualEndpointKey = keyof typeof MANUAL_ENDPOINTS;
