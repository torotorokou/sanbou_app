/**
 * Mock Calendar Repository
 * 新しい ICalendarRepository インターフェース用のモックデータ生成
 */

import type { ICalendarRepository } from '@/features/calendar/model/repository';
import type { MonthCalendarDTO, CalendarDayDTO } from '@/features/calendar/model/types';
import dayjs from 'dayjs';

export class MockCalendarRepository implements ICalendarRepository {
  async fetchMonthCalendar(year: number, month: number): Promise<MonthCalendarDTO> {
    // 実際のAPIコールをシミュレート（300ms遅延）
    await new Promise((resolve) => setTimeout(resolve, 300));

    const pad = (n: number) => String(n).padStart(2, '0');
    const monthStr = `${year}-${pad(month)}`;
    const first = dayjs(`${monthStr}-01`);
    const daysInMonth = first.daysInMonth();
    
    const days: CalendarDayDTO[] = Array.from({ length: daysInMonth }, (_, i) => {
      const d = first.add(i, 'day');
      const dow = d.day();
      const dateStr = d.format('YYYY-MM-DD');
      
      // ISO曜日 (月=1, 日=7)
      const isoDow = dow === 0 ? 7 : dow;
      
      // デフォルト値
      let isHoliday = false;
      let isSecondSunday = false;
      let isCompanyClosed = false;
      let dayType: 'NORMAL' | 'RESERVATION' | 'CLOSED' = 'NORMAL';
      let isBusiness = true;

      // 日曜日は基本的に祝日扱い
      if (dow === 0) {
        isHoliday = true;
        isBusiness = false;
      }

      // 第2日曜日は休業日
      const nthSunday = getNthSundayIndex(d);
      if (dow === 0 && nthSunday === 2) {
        isSecondSunday = true;
        isCompanyClosed = true;
        dayType = 'CLOSED';
        isBusiness = false;
      }

      // 土曜日は営業
      if (dow === 6) {
        isBusiness = true;
      }

      // モック祝日（例：10/13がスポーツの日の場合）
      if (month === 10 && i === 12) {
        isHoliday = true;
        isBusiness = false;
      }

      // ISO週番号の計算（簡易版）
      const isoWeek = Math.ceil(d.date() / 7);

      return {
        ddate: dateStr,
        y: year,
        m: month,
        iso_year: year,
        iso_week: isoWeek,
        iso_dow: isoDow,
        is_holiday: isHoliday,
        is_second_sunday: isSecondSunday,
        is_company_closed: isCompanyClosed,
        day_type: dayType,
        is_business: isBusiness,
      };
    });

    return {
      month: monthStr,
      days,
    };
  }
}

/**
 * 月内で何番目の日曜日かを返す（1-indexed）
 */
function getNthSundayIndex(d: dayjs.Dayjs): number {
  if (d.day() !== 0) return 0;
  
  let count = 0;
  let cur = d.startOf('month');
  
  while (cur.isBefore(d) || cur.isSame(d, 'day')) {
    if (cur.day() === 0) count++;
    cur = cur.add(1, 'day');
  }
  
  return count;
}
