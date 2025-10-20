/**
 * Ukeire History ViewModel Hook
 * 過去データ取得と整形
 */

import { useEffect, useState } from "react";
import type { UkeireHistoryRepository } from "../repository/UkeireHistoryRepository";
import type { IsoMonth, IsoDate } from "../../model/types";

export type UkeireHistoryViewModel = {
  loading: boolean;
  error: Error | null;
  data: {
    prev_month_daily: Record<IsoDate, number>;
    prev_year_daily: Record<IsoDate, number>;
  } | null;
};

export function useUkeireHistoryVM(
  repository: UkeireHistoryRepository,
  month: IsoMonth
): UkeireHistoryViewModel {
  const [state, setState] = useState<UkeireHistoryViewModel>({
    loading: true,
    error: null,
    data: null,
  });

  useEffect(() => {
    let alive = true;
    setState((s) => ({ ...s, loading: true, error: null }));

    repository
      .fetchHistoricalData(month)
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
