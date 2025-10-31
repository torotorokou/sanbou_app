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
export { MonthNavigator, type MonthNavigatorProps } from "./shared/ui/MonthNavigator";
export * from "./shared/styles/useInstallTabsFillCSS";
export * from "./shared/tokens";
export { useResponsiveLayout, type ResponsiveLayoutConfig, type LayoutMode } from "./shared/hooks/useResponsiveLayout";

// ========== Business Calendar ==========
export { decorateCalendarCells } from "./business-calendar/application/decorators";
export { useBusinessCalendarVM } from "./business-calendar/application/useBusinessCalendarVM";
export { CalendarRepositoryForUkeire } from "./business-calendar/infrastructure/calendar.repository";
export { MockCalendarRepositoryForUkeire } from "./business-calendar/infrastructure/calendar.mock.repository";
export { default as UkeireCalendarCard } from "./business-calendar/ui/cards/CalendarCard";
export { default as UkeireCalendar, UkeireCalendar as UkeireCalendarNamed } from "./business-calendar/ui/components/UkeireCalendar";

// ========== KPI Targets ==========
export { TargetCard, type TargetCardProps } from "./kpi-targets/ui/cards/TargetCard";
export { useTargetsVM } from "./kpi-targets/application/useTargetsVM";
export { useTargetMetrics } from "./kpi-targets/application/useTargetMetrics";

// ========== Forecast Inbound ==========
export type { IInboundForecastRepository } from "./forecast-inbound/ports/repository";
export { HttpInboundForecastRepository } from "./forecast-inbound/infrastructure/inboundForecast.repository";
export { MockInboundForecastRepository } from "./forecast-inbound/infrastructure/inboundForecast.mock.repository";
export { useInboundForecastVM, type InboundForecastViewModel } from "./forecast-inbound/application/useInboundForecastVM";
export { ForecastCard, type ForecastCardProps, type KPIBlockProps } from "./forecast-inbound/ui/cards/ForecastCard";

// ========== Inbound Monthly ==========
export { DailyActualsCard } from "./inbound-monthly/ui/cards/DailyActualsCard";
export { DailyCumulativeCard } from "./inbound-monthly/ui/cards/DailyCumulativeCard";
export { CombinedDailyCard, type CombinedDailyCardProps } from "./inbound-monthly/ui/cards/CombinedDailyCard";
export { useInboundMonthlyVM } from "./inbound-monthly/application/useInboundMonthlyVM";
