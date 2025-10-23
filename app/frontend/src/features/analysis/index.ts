/**
 * Analysis Feature - Public API
 * MVVM+SOLID アーキテクチャに準拠した barrel export
 */

// Domain
export type { CustomerData } from './domain/types';
export { allCustomerData } from './domain/types';

// Ports (placeholder)
export type { IAnalysisRepository } from './ports/repository';

// Application (ViewModel)
export { useCustomerComparison } from './application/useAnalysisVM';

// UI
export {
  ComparisonConditionForm,
  CustomerComparisonResultCard,
  AnalysisProcessingModal,
} from './ui';
