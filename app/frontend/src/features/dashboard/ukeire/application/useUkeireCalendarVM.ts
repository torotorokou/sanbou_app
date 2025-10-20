import { useMemo } from "react";
import { useCalendarVM } from "@/features/calendar/controller/useCalendarVM";
import { decorateCalendarCells } from "./decorateCalendarCells";
import type { ICalendarRepository } from "@/features/calendar/model/repository";

type Params = { year: number; month: number; repository: ICalendarRepository };

export function useUkeireCalendarVM({ year, month, repository }: Params) {
  const base = useCalendarVM({ year, month, repository });
  const decorated = useMemo(() => decorateCalendarCells(base.grid), [base.grid]);
  return { ...base, grid: decorated };
}
