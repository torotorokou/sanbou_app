import type { ICalendarRepository } from '@/features/calendar/model/repository';
import type { MonthCalendarDTO, CalendarDayDTO } from '@/features/calendar/model/types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export class HttpCalendarRepository implements ICalendarRepository {
  async fetchMonthCalendar(year: number, month: number): Promise<MonthCalendarDTO> {
    const url = `${BASE_URL}/calendar/month?year=${year}&month=${month}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Calendar API ${res.status}`);
    const rows = (await res.json()) as CalendarDayDTO[];
    const pad = (n: number) => String(n).padStart(2, '0');
    return { month: `${year}-${pad(month)}`, days: rows };
  }
}
