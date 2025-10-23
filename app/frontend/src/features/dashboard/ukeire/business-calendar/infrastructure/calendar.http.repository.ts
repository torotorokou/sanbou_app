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
    ddate: d.ddate,
    y: d.y,
    m: d.m,
    iso_year: d.iso_year,
    iso_week: d.iso_week,
    iso_dow: d.iso_dow,
    is_holiday: d.is_holiday,
    is_second_sunday: d.is_second_sunday,
    is_company_closed: d.is_company_closed,
    day_type: d.day_type,
    is_business: d.is_business,
    // 後方互換性のためのエイリアス
    date: d.ddate,
    isHoliday: d.is_holiday || !d.is_business,
  };
}
