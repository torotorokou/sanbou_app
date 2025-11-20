/**
 * pages/analytics/SalesTreePage.tsx
 * 売上ツリー分析ページ
 * 
 * ページレベルの責務：
 * - ページレイアウト・構成
 * - 各機能sliceの統合
 * - ページタイトル・メタ情報
 * 
 * ビジネスロジックは features/analytics/sales-pivot の各sliceに分離済み
 * 
 * リファクタリング完了（2025-11-20）:
 * - 8つの機能slice化（header/filters/kpi/summary-table/pivot-drawer/export-menu/detail-chart/shared）
 * - 各sliceが独立したViewModel(Hooks)とUIを持つ
 * - 共通UIコンポーネント層（SortBadge/MiniBarChart/EmptyStateCard/styles）
 * - 暫定的に既存の統合ページを使用（完全分離は将来フェーズで実装）
 */

import React from 'react';
import { Space } from 'antd';

/**
 * レイアウトProps定義
 */
export interface SalesPivotLayoutProps {
  header: React.ReactNode;
  filters: React.ReactNode;
  kpi: React.ReactNode;
  summaryTable: React.ReactNode;
  pivotDrawer?: React.ReactNode;
  styles?: React.ReactNode;
}

/**
 * 売上ピボット分析ページレイアウト
 * 
 * 責務:
 * - ページ全体のレイアウト構成
 * - 各sliceコンポーネントの配置
 * - レスポンシブデザイン
 */
export const SalesPivotLayout: React.FC<SalesPivotLayoutProps> = ({
  header,
  filters,
  kpi,
  summaryTable,
  pivotDrawer,
  styles,
}) => {
  return (
    <>
      {styles}
      <Space direction="vertical" size="large" style={{ display: 'block' }}>
        {header}
        {filters}
        {kpi}
        {summaryTable}
        {pivotDrawer}
      </Space>
    </>
  );
};

// 既存の統合ページを使用（バックワード互換性維持）
export { default } from '@/features/analytics/sales-pivot';
