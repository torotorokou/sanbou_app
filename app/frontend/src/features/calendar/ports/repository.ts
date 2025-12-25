import type { CalendarDayDTO } from '../domain/types';

export interface ICalendarRepository {
  fetchMonth(params: { year: number; month: number }): Promise<CalendarDayDTO[]>;
}
