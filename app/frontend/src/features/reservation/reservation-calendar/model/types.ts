/**
 * ReservationCalendar - 型定義
 *
 * Model (型定義)
 * 規約: UI Componentのprops型をmodel層で一元管理
 */

import type { Dayjs } from "dayjs";
import type { ReservationForecastDaily } from "../../shared";

/**
 * ReservationHistoryCalendar コンポーネントのProps
 */
export interface ReservationHistoryCalendarProps {
  historyMonth: Dayjs;
  historyData: ReservationForecastDaily[];
  onChangeHistoryMonth: (month: Dayjs) => void;
  onDeleteDate?: (date: string) => Promise<void>;
  goToCurrentMonth?: () => void;
  isLoadingHistory?: boolean;
  isDeletingDate?: string | null;
}

/**
 * ReservationMonthlyStats コンポーネントのProps
 */
export interface ReservationMonthlyStatsProps {
  data: ReservationForecastDaily[];
  isLoading?: boolean;
}

/**
 * ReservationMonthlyChart コンポーネントのProps
 */
export interface ReservationMonthlyChartProps {
  data: ReservationForecastDaily[];
  isLoading?: boolean;
}
