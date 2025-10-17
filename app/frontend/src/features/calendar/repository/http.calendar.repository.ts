import { coreApi } from '@/shared/infrastructure/http';
import type { ICalendarRepository } from '@/features/calendar/model/repository';
import type { MonthCalendarDTO, CalendarDayDTO } from '@/features/calendar/model/types';

export class HttpCalendarRepository implements ICalendarRepository {
  async fetchMonthCalendar(year: number, month: number): Promise<MonthCalendarDTO> {
    const url = `/core_api/calendar/month?year=${year}&month=${month}`;
    const rows = await coreApi.get<CalendarDayDTO[]>(url);
    const pad = (n: number) => String(n).padStart(2, '0');
    return { month: `${year}-${pad(month)}`, days: rows };
  }
}
