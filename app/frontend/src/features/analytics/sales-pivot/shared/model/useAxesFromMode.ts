/**
 * features/analytics/sales-pivot/shared/model/useAxesFromMode.ts
 * モードに応じた軸の取得（baseAx, axB, axC）
 */

import { useMemo } from 'react';
import type { Mode } from './types';
import { axesFromMode } from './metrics';

export function useAxesFromMode(mode: Mode) {
  const [baseAx, axB, axC] = useMemo(() => axesFromMode(mode), [mode]);
  return { baseAx, axB, axC };
}
