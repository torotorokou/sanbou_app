/**
 * Ukeire Calendar ViewModel Hook
 * API駆動のカレンダーデータ取得とUI Props生成
 */

import { useEffect, useState } from "react";
import type { MonthISO, CalendarPayload } from "@/shared/ui/calendar/types";
import type { ICalendarRepository } from "../domain/repository";
import dayjs from "dayjs";

export type UkeireCalendarVM = {
  month: MonthISO;
  setMonth: (m: MonthISO) => void;
  loading: boolean;
  error: string | null;
  payload: CalendarPayload;
  onDayClick?: (iso: string) => void;
};

export function useUkeireCalendarVM(
  repo: ICalendarRepository,
  initialMonth?: MonthISO
): UkeireCalendarVM {
  const [month, setMonth] = useState<MonthISO>(
    initialMonth ?? dayjs().format("YYYY-MM")
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState<CalendarPayload>({
    month,
    days: [],
  });

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);

    repo
      .fetchMonthCalendar(month)
      .then((p) => {
        if (alive) {
          setPayload(p);
        }
      })
      .catch((e) => {
        if (alive) {
          setError(e?.message ?? "Failed to load calendar");
        }
      })
      .finally(() => {
        if (alive) {
          setLoading(false);
        }
      });

    return () => {
      alive = false;
    };
  }, [repo, month]);

  return {
    month,
    setMonth,
    loading,
    error,
    payload,
  };
}
