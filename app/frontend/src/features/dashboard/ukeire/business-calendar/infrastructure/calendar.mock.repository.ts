import type { ICalendarRepository } from "@/features/calendar/ports/repository";
import type { CalendarDayDTO } from "@/features/calendar/domain/types";

export class MockCalendarRepositoryForUkeire implements ICalendarRepository {
  async fetchMonth({ year, month }: { year: number; month: number }): Promise<CalendarDayDTO[]> {
    const mm = String(month).padStart(2, "0");
    const daysInMonth = new Date(year, month, 0).getDate();
    const days: CalendarDayDTO[] = [];
    
    for (let day = 1; day <= daysInMonth; day++) {
      const dd = String(day).padStart(2, "0");
      const date = `${year}-${mm}-${dd}`;
      const dayOfWeek = new Date(year, month - 1, day).getDay(); // 0=日, 6=土
      
      // モックデータ: 日曜日と特定の祝日をシミュレート
      const isSunday = dayOfWeek === 0;
      const isSecondSunday = isSunday && day >= 8 && day <= 14;
      const isHoliday = day === 13; // 仮の祝日
      
      let dayType = "NORMAL";
      if (isSecondSunday) {
        dayType = "CLOSED";
      } else if (isSunday || isHoliday) {
        dayType = "RESERVATION";
      }
      
      days.push({
        ddate: date,
        y: year,
        m: month,
        iso_year: year,
        iso_week: Math.ceil(day / 7),
        iso_dow: dayOfWeek === 0 ? 7 : dayOfWeek,
        is_holiday: isHoliday,
        is_second_sunday: isSecondSunday,
        is_company_closed: isSecondSunday,
        day_type: dayType,
        is_business: dayType === "NORMAL",
        date: date,
        isHoliday: isHoliday || isSunday,
      });
    }
    
    return days;
  }
}
