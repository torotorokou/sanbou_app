/**
 * Customer List Feature - Public API
 *
 * 顧客離脱分析フィーチャーのエクスポート
 * FSD + MVVM + Repository アーキテクチャに準拠
 *
 * アーキテクチャ構成:
 * - domain/: ビジネスエンティティ（純粋なドメインモデル）
 * - model/: 主ViewModel（Repositoryパターンでバックエンドと連携）
 * - ports/: Repository抽象インターフェース
 * - infrastructure/: Repository実装（HTTP経由）
 * - period-selector/: 期間選択サブフィーチャー
 * - customer-aggregation/: 顧客集約サブフィーチャー
 * - customer-comparison/: 顧客比較サブフィーチャー
 * - data-export/: CSV/Excelエクスポートサブフィーチャー
 * - ui/: 状態レスなViewコンポーネント
 */

// Domain Types
export type {
  CustomerData,
  LostCustomer,
  CustomerChurnAnalyzeParams,
  SalesRep,
} from "./shared/domain/types";

// Repository (Clean Architecture Ports & Adapters)
export type { CustomerChurnRepository } from "./shared/ports/customerChurnRepository";
export {
  customerChurnRepository,
  CustomerChurnHttpRepository,
} from "./shared/infrastructure/customerChurnRepository";

// Main ViewModel - 主要なエントリーポイント
export { useCustomerChurnViewModel } from "./shared/model/useCustomerChurnVM";
export type { CustomerChurnViewModel } from "./shared/model/useCustomerChurnVM";

// Sub-features - 個別に使用可能な機能モジュール
export * from "./period-selector";
export * from "./sales-rep-filter";
export * from "./condition-panel";
export * from "./action-buttons";
export * from "./result-panel";
export * from "./customer-aggregation";
export * from "./customer-comparison";
export * from "./data-export";

// Shared Components
export * from "./shared";
