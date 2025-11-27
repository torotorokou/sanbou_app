import { useMemo } from "react";
import { useCalendarVM } from "@/features/calendar/application/useCalendarVM";
import { decorateCalendarCells } from "./decorators";
import type { ICalendarRepository } from "@/features/calendar/ports/repository";

type Params = { year: number; month: number; repository: ICalendarRepository };

/**
 * Business Calendar ViewModel
 * 汎用カレンダーに営業日ステータス装飾を追加
 */
export function useBusinessCalendarVM({ year, month, repository }: Params) {
  const base = useCalendarVM({ year, month, repository });
  const decorated = useMemo(() => decorateCalendarCells(base.grid), [base.grid]);
  return { ...base, grid: decorated };
}
