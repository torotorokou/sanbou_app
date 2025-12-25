/**
 * Customer Comparison Sub-Feature - Public API
 */

// Domain
export type { CustomerComparisonResult } from './domain/types';

// Model
export { getExclusiveCustomers, getCommonCustomers } from './model/comparison';
export { useCustomerComparison } from './model/useCustomerComparison';

// UI
export { CustomerComparisonResultCard } from './ui';
