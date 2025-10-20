/**
 * Ukeire Actuals ViewModel Hook
 * 実績データ取得と整形
 */

import { useEffect, useState } from "react";
import type { UkeireActualsRepository } from "../repository/UkeireActualsRepository";
import type { IsoMonth, DailyCurveDTO, CalendarDay } from "../../model/types";

export type UkeireActualsViewModel = {
  loading: boolean;
  error: Error | null;
  data: {
    days: DailyCurveDTO[];
    calendar: CalendarDay[];
  } | null;
};

export function useUkeireActualsVM(
  repository: UkeireActualsRepository,
  month: IsoMonth
): UkeireActualsViewModel {
  const [state, setState] = useState<UkeireActualsViewModel>({
    loading: true,
    error: null,
    data: null,
  });

  useEffect(() => {
    let alive = true;
    setState((s) => ({ ...s, loading: true, error: null }));

    repository
      .fetchDailyActuals(month)
      .then((data) => {
        if (alive) {
          setState({ loading: false, error: null, data });
        }
      })
      .catch((error) => {
        if (alive) {
          setState({ loading: false, error: error as Error, data: null });
        }
      });

    return () => {
      alive = false;
    };
  }, [repository, month]);

  return state;
}
