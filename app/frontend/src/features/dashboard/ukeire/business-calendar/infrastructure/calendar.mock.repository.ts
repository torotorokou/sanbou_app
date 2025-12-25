import type { ICalendarRepository } from '@/features/calendar/ports/repository';
import type { CalendarDayDTO } from '@/features/calendar/domain/types';

/**
 * Mock Calendar Repository
 * バックエンドAPI (/core_api/calendar/month) の返却データと同じ形式でモックデータを生成
 *
 * バックエンドが返すデータ:
 * - ddate, y, m, iso_year, iso_week, iso_dow
 * - is_holiday, is_second_sunday, is_company_closed
 * - day_type (NORMAL, RESERVATION, CLOSED), is_business
 */
export class MockCalendarRepositoryForUkeire implements ICalendarRepository {
  async fetchMonth({ year, month }: { year: number; month: number }): Promise<CalendarDayDTO[]> {
    const mm = String(month).padStart(2, '0');
    const daysInMonth = new Date(year, month, 0).getDate();
    const days: CalendarDayDTO[] = [];

    for (let day = 1; day <= daysInMonth; day++) {
      const dd = String(day).padStart(2, '0');
      const date = `${year}-${mm}-${dd}`;
      const currentDate = new Date(year, month - 1, day);
      const dayOfWeek = currentDate.getDay(); // 0=日, 6=土

      // バックエンドと同様にISO週番号とISO年を計算
      const isoWeek = getIsoWeekNumber(currentDate);
      const isoYear = getIsoYearNumber(currentDate);
      const isoDow = dayOfWeek === 0 ? 7 : dayOfWeek; // ISO曜日（1=月, 7=日）

      // モックデータ: 日曜日と特定の祝日をシミュレート
      const isSunday = dayOfWeek === 0;
      const isSecondSunday = isSunday && day >= 8 && day <= 14;

      // より現実的な祝日判定（実際の祝日に近いパターン）
      // 1/1, 2/11, 3/21, 4/29, 5/3-5, 7/15, 8/11, 9/15, 10/10, 11/3, 11/23, 12/23
      const isHoliday =
        (month === 1 && day === 1) ||
        (month === 2 && day === 11) ||
        (month === 3 && day === 21) ||
        (month === 4 && day === 29) ||
        (month === 5 && (day === 3 || day === 4 || day === 5)) ||
        (month === 7 && day === 15) ||
        (month === 8 && day === 11) ||
        (month === 9 && day === 15) ||
        (month === 10 && day === 10) ||
        (month === 11 && (day === 3 || day === 23)) ||
        (month === 12 && day === 23);

      // day_type の判定（バックエンドのロジックと同様）
      // NORMAL: 通常営業日
      // RESERVATION: 予約営業日（日曜・祝日）
      // CLOSED: 休業日（第2日曜日など）
      let dayType: 'NORMAL' | 'RESERVATION' | 'CLOSED' = 'NORMAL';
      if (isSecondSunday) {
        dayType = 'CLOSED';
      } else if (isSunday || isHoliday) {
        dayType = 'RESERVATION';
      }

      const isBusiness = dayType === 'NORMAL';

      days.push({
        ddate: date,
        y: year,
        m: month,
        iso_year: isoYear,
        iso_week: isoWeek,
        iso_dow: isoDow,
        is_holiday: isHoliday,
        is_second_sunday: isSecondSunday,
        is_company_closed: isSecondSunday,
        day_type: dayType,
        is_business: isBusiness,
        // 後方互換性のためのエイリアス
        date: date,
        isHoliday: isHoliday || !isBusiness,
      });
    }

    return days;
  }
}

/**
 * ISO週番号を計算（ISO 8601準拠）
 * バックエンドのPostgreSQL関数 EXTRACT(WEEK FROM date) と同じロジック
 */
function getIsoWeekNumber(date: Date): number {
  const target = new Date(date.valueOf());
  const dayNum = (date.getDay() + 6) % 7;
  target.setDate(target.getDate() - dayNum + 3);
  const firstThursday = target.valueOf();
  target.setMonth(0, 1);
  if (target.getDay() !== 4) {
    target.setMonth(0, 1 + ((4 - target.getDay() + 7) % 7));
  }
  return 1 + Math.ceil((firstThursday - target.valueOf()) / 604800000);
}

/**
 * ISO年を計算
 * バックエンドのPostgreSQL関数 EXTRACT(ISOYEAR FROM date) と同じロジック
 */
function getIsoYearNumber(date: Date): number {
  const year = date.getFullYear();
  const month = date.getMonth();
  const day = date.getDate();

  // 1月1-3日で前年の最終週に属する場合
  if (month === 0 && day <= 3) {
    const isoWeek = getIsoWeekNumber(date);
    if (isoWeek >= 52) {
      return year - 1;
    }
  }

  // 12月29-31日で翌年の第1週に属する場合
  if (month === 11 && day >= 29) {
    const isoWeek = getIsoWeekNumber(date);
    if (isoWeek === 1) {
      return year + 1;
    }
  }

  return year;
}
