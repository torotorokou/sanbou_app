import { useEffect, useMemo, useState } from "react";
import type { ICalendarRepository } from "@/features/calendar/ports/repository";
import type { CalendarDayDTO } from "@/features/calendar/domain/types";

type Params = { repository: ICalendarRepository; year: number; month: number };

export function useCalendarVM({ repository, year, month }: Params) {
  const [data, setData] = useState<CalendarDayDTO[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        setLoading(true);
        setError(undefined);
        const days = await repository.fetchMonth({ year, month });
        if (!cancel) setData(days);
      } catch (e: unknown) {
        if (!cancel) setError(e instanceof Error ? e.message : "unknown error");
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => {
      cancel = true;
    };
  }, [repository, year, month]);

  // 7x6 グリッド（前月・翌月含む）に整形（簡易版）
  const grid = useMemo(() => buildGrid(year, month, data), [year, month, data]);
  return { grid, loading, error };
}

function buildGrid(year: number, month: number, days: CalendarDayDTO[]) {
  const map = new Map(days.map((d) => [d.date, d]));
  const first = new Date(year, month - 1, 1);
  const last = new Date(year, month, 0);
  const start = startOfIsoWeek(first);
  const cells: Array<CalendarDayDTO & { inMonth: boolean }> = [];
  for (let i = 0; i < 42; i++) {
    const cur = new Date(start);
    cur.setDate(start.getDate() + i);
    // Use local date components to build YYYY-MM-DD key.
    // toISOString() uses UTC and can produce the previous day when the
    // runtime is in a positive offset timezone (e.g. Asia/Tokyo), which
    // causes a 1-day shift when matching server-provided date strings.
    const pad = (n: number) => String(n).padStart(2, "0");
    const key = `${cur.getFullYear()}-${pad(cur.getMonth() + 1)}-${pad(cur.getDate())}`;
    const inMonth = cur >= first && cur <= last;
    const existing = map.get(key);

    // バックエンドからデータがあればそれを優先使用
    // バックエンドにはiso_year, iso_week, iso_dowなど全て含まれている
    const base: CalendarDayDTO = existing ?? {
      ddate: key,
      y: cur.getFullYear(),
      m: cur.getMonth() + 1,
      iso_year: cur.getFullYear(), // フォールバック用の簡易値
      iso_week: 1, // フォールバック用の簡易値
      iso_dow: ((cur.getDay() + 6) % 7) + 1,
      is_holiday: false,
      is_second_sunday: false,
      is_company_closed: false,
      day_type: "NORMAL",
      is_business: true,
      date: key,
      isHoliday: false,
    };
    cells.push({ ...base, inMonth });
  }
  const rows: (typeof cells)[] = [];
  for (let r = 0; r < 6; r++) rows.push(cells.slice(r * 7, r * 7 + 7));
  return rows;
}
function startOfIsoWeek(d: Date) {
  const wd = isoDay(d);
  const out = new Date(d);
  out.setDate(d.getDate() - (wd - 1));
  out.setHours(0, 0, 0, 0);
  return out;
}
function isoDay(d: Date) {
  const wd = d.getDay();
  return wd === 0 ? 7 : wd;
}
