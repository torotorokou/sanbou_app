/**
 * Calendar Feature Barrel Export
 * 外部から利用可能な最小限のAPI
 */

// Types
export type { MonthISO, DateISO, CalendarCell } from "./model/types";

// Repository
export type { ICalendarRepository } from "./model/repository";
export { HttpCalendarRepository } from "./repository/http.calendar.repository";

// Utils
export { buildCalendarCells } from "./utils/buildCalendarCells";

// Controller
export { useCalendarVM } from "./controller/useCalendarVM";

// UI
export { default as CalendarCore } from "./ui/CalendarCore";
export type { CalendarCoreProps } from "./ui/CalendarCore";

// Hooks
export { useContainerSize } from "./hooks/useContainerSize";
