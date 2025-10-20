import type { ICalendarRepository } from "@/features/calendar/model/repository";
import type { CalendarDayDTO } from "@/features/calendar/model/types";

export class MockCalendarRepositoryForUkeire implements ICalendarRepository {
  async fetchMonth({ year, month }: { year: number; month: number }): Promise<CalendarDayDTO[]> {
    const mm = String(month).padStart(2, "0");
    return [
      { date: `${year}-${mm}-01` },
      { date: `${year}-${mm}-02`, isHoliday: true },
    ];
  }
}
