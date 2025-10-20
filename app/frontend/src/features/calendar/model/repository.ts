import type { CalendarDayDTO } from "./types";

export interface ICalendarRepository {
  fetchMonth(params: { year: number; month: number }): Promise<CalendarDayDTO[]>;
}
