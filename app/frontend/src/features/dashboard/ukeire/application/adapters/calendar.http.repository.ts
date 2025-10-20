import type { ICalendarRepository } from "@/features/calendar/model/repository";
import type { CalendarDayDTO } from "@/features/calendar/model/types";
import { coreApi } from "@/shared/infrastructure/http";

type UkeireDayDTO = {
  date: string;
  isHoliday?: boolean;
  [key: string]: unknown;
};

export class CalendarRepositoryForUkeire implements ICalendarRepository {
  async fetchMonth({ year, month }: { year: number; month: number }): Promise<CalendarDayDTO[]> {
    const data = await coreApi.get<{ days: UkeireDayDTO[] }>("/core_api/calendar/month", {
      params: { year, month },
    });
    return (data?.days ?? []).map(mapUkeireDayToCalendarDTO);
  }
}

function mapUkeireDayToCalendarDTO(d: UkeireDayDTO): CalendarDayDTO {
  return {
    date: d.date,
    isHoliday: !!d.isHoliday,
  };
}
