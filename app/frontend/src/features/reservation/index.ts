/**
 * Public API for reservation features
 *
 * 規約: 予約管理関連機能のグループ
 * 明示的な Named Export を使用
 */

// Reservation Input (手入力フォーム)
export {
  ReservationInputForm,
  useReservationInputVM,
  type ReservationInputViewModel,
  type ReservationInputFormProps,
} from './reservation-input';

// Reservation Calendar (履歴カレンダー)
export {
  ReservationHistoryCalendar,
  ReservationMonthlyStats,
  ReservationMonthlyChart,
  useReservationCalendarVM,
  type ReservationCalendarViewModel,
  type ReservationHistoryCalendarProps,
  type ReservationMonthlyStatsProps,
  type ReservationMonthlyChartProps,
} from './reservation-calendar';

// Shared (Repository層)
export type {
  ReservationDailyRepository,
  ReservationForecastDaily,
  ReservationManualInput,
} from './shared';

export {
  ReservationDailyHttpRepository,
  reservationDailyRepository,
  ReservationDailyMockRepository,
  reservationDailyMockRepository,
} from './shared';
