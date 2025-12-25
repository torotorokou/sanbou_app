/**
 * Period Selector Sub-Feature - Public API
 */

// Domain
export type {
  PeriodRange,
  ComparisonPeriods,
  MonthRange,
} from "./domain/types";

// Model
export { getMonthRange, isValidPeriodRange } from "./model/utils";
export { usePeriodSelector } from "./model/usePeriodSelector";
export type { PeriodSelectorViewModel } from "./model/usePeriodSelector";

// UI
export { PeriodSelectorForm } from "./ui";
