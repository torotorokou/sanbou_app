/**
 * Customer List Feature - Public API
 * 
 * 顧客離脱分析フィーチャーのエクスポート
 * FSD + MVVM + Repository アーキテクチャに準拠
 * 
 * アーキテクチャ構成:
 * - domain/: ビジネスエンティティ（純粋なドメインモデル）
 * - model/: 主ViewModel（4つのサブフィーチャーを統合）
 * - period-selector/: 期間選択サブフィーチャー
 * - customer-aggregation/: 顧客集約サブフィーチャー
 * - customer-comparison/: 顧客比較サブフィーチャー
 * - data-export/: CSV/Excelエクスポートサブフィーチャー
 * - ui/: 状態レスなViewコンポーネント
 */

// Domain Types
export type { CustomerData } from './domain/types';

// Main ViewModel - 主要なエントリーポイント
export { useCustomerChurnViewModel } from './model/useCustomerChurnViewModel';
export type { CustomerChurnViewModel } from './model/useCustomerChurnViewModel';

// Sub-features - 個別に使用可能な機能モジュール
export * from './period-selector';
export * from './customer-aggregation';
export * from './customer-comparison';
export * from './data-export';

// Shared Components
export * from './shared';

