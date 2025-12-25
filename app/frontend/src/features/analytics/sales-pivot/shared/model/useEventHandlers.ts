/**
 * features/analytics/sales-pivot/shared/model/useEventHandlers.ts
 * シンプルなイベントハンドラー（モード切替）の管理
 */

import { useCallback } from "react";
import type { Mode, ID } from "./types";

interface EventHandlersParams {
  setMode: (mode: Mode) => void;
  setFilterIds: (ids: ID[]) => void;
}

export function useEventHandlers(params: EventHandlersParams) {
  const { setMode, setFilterIds } = params;

  // Mode switch
  const switchMode = useCallback(
    (m: Mode) => {
      setMode(m);
      setFilterIds([]);
    },
    [setMode, setFilterIds],
  );

  return {
    switchMode,
  };
}
