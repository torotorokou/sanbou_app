/**
 * Calendar Feature Barrel Export
 * 外部から利用可能な最小限のAPI（汎用のみ）
 */

// Types
export type { CalendarDayDTO, CalendarCell } from "./model/types";

// Repository
export type { ICalendarRepository } from "./model/repository";

// Controller
export { useCalendarVM } from "./controller/useCalendarVM";

// UI
export { default as CalendarCore } from "./ui/CalendarCore";

// Hooks
export { useContainerSize } from "./hooks/useContainerSize";
