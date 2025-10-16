import type { MonthCalendarDTO } from './types';

export interface ICalendarRepository {
  fetchMonthCalendar(year: number, month: number): Promise<MonthCalendarDTO>;
}
