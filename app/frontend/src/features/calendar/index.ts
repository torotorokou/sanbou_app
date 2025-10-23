/**
 * Calendar Feature Barrel Export
 * 外部から利用可能な最小限のAPI（汎用のみ）
 */

// Domain Types
export type { CalendarDayDTO, CalendarCell } from "./domain/types";

// Ports
export type { ICalendarRepository } from "./ports/repository";

// Application
export { useCalendarVM } from "./application/useCalendarVM";

// UI
export { default as CalendarCard } from "./ui/cards/CalendarCard";
export { default as CalendarCore } from "./ui/components/CalendarCore";

// Hooks (汎用)
export { useContainerSize } from "./hooks/useContainerSize";
