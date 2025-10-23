/**
 * 受入ダッシュボード - Public API
 * features/dashboard/ukeire のエントリーポイント
 * 
 * リファクタ後: 機能別ディレクトリから再エクスポート
 */

// ========== Domain ==========
export * from "./domain/types";
export * from "./domain/valueObjects";
export * from "./domain/constants";
export * from "./domain/repository";
export * from "./domain/services/calendarService";
export * from "./domain/services/targetService";

// ========== Shared ==========
export * from "./shared/ui/ChartFrame";
export * from "./shared/ui/SingleLineLegend";
export * from "./shared/styles/useInstallTabsFillCSS";
export * from "./shared/tokens";

// ========== Business Calendar ==========
export { decorateCalendarCells } from "./business-calendar/application/decorateCalendarCells";
export { useUkeireCalendarVM } from "./business-calendar/application/useUkeireCalendarVM";
export { CalendarRepositoryForUkeire } from "./business-calendar/infrastructure/calendar.http.repository";
export { MockCalendarRepositoryForUkeire } from "./business-calendar/infrastructure/calendar.mock.repository";
export { default as UkeireCalendarCard } from "./business-calendar/ui/CalendarCard";
export { default as CalendarCardUkeire } from "./business-calendar/ui/CalendarCard.Ukeire";
export { default as UkeireCalendar, UkeireCalendar as UkeireCalendarNamed } from "./business-calendar/ui/UkeireCalendar";

// ========== KPI Targets ==========
export * from "./kpi-targets/ui/TargetCard";
export * from "./kpi-targets/application/useTargetsVM";

// ========== Forecast Inbound ==========
export * from "./forecast-inbound/application/useUkeireForecastVM";
export * from "./forecast-inbound/ui/ForecastCard";
export { MockInboundForecastRepository } from "./forecast-inbound/infrastructure/mock.repository";
export { HttpInboundForecastRepository } from "./forecast-inbound/infrastructure/http.repository";

// ========== Inbound Monthly ==========
export * from "./inbound-monthly/ui/DailyActualsCard";
export * from "./inbound-monthly/ui/DailyCumulativeCard";
export * from "./inbound-monthly/ui/CombinedDailyCard";
export * from "./inbound-monthly/application/useInboundMonthlyVM";
