/**
 * Shared Module - Public API
 *
 * customer-list内で共有される汎用コンポーネント、型定義、ViewModel
 */

// Types
export type { CustomerData } from "./domain/types";

// Main ViewModel
export { useCustomerChurnViewModel } from "./model/useCustomerChurnVM";
export type { CustomerChurnViewModel } from "./model/useCustomerChurnVM";

// UI Components
export * from "./ui";
