import type { ICalendarRepository } from "@/features/calendar/model/repository";
import type { CalendarDayDTO } from "@/features/calendar/model/types";
import { coreApi } from "@/shared/infrastructure/http";

type BackendCalendarDay = {
  ddate: string;
  y: number;
  m: number;
  iso_year: number;
  iso_week: number;
  iso_dow: number;
  is_holiday: boolean;
  is_second_sunday: boolean;
  is_company_closed: boolean;
  day_type: string;
  is_business: boolean;
};

export class CalendarRepositoryForUkeire implements ICalendarRepository {
  async fetchMonth({ year, month }: { year: number; month: number }): Promise<CalendarDayDTO[]> {
    // バックエンドAPIは /core_api/calendar/month?year=YYYY&month=MM の形式で配列を直接返す
    const data = await coreApi.get<BackendCalendarDay[]>(`/core_api/calendar/month?year=${year}&month=${month}`);
    return (data ?? []).map(mapBackendDayToCalendarDTO);
  }
}

function mapBackendDayToCalendarDTO(d: BackendCalendarDay): CalendarDayDTO {
  return {
    date: d.ddate,
    isHoliday: d.is_holiday || !d.is_business,
  };
}
