/**
 * UIカラー定数とユーティリティ
 * 
 * @deprecated 色定義は config/datasets.ts に移行済みです。
 * 新規コードでは config/selectors.getCsvColor() を使用してください。
 */

import { DATASETS } from '../../config';

/**
 * UIカラー（CSV種別ごと）
 * @deprecated config/selectors.getCsvColor() を使用してください
 */
export const CSV_TYPE_COLORS: Record<string, string> = (() => {
  const result: Record<string, string> = {};
  for (const dataset of Object.values(DATASETS)) {
    for (const csv of dataset.csv) {
      if (csv.color) {
        result[csv.typeKey] = csv.color;
      }
    }
  }
  return result;
})();

/**
 * デフォルトのカラー
 */
export const DEFAULT_CSV_COLOR = '#777777';

/**
 * 背景色に対して読みやすい文字色を返す
 */
export function readableTextColor(bg: string): string {
  try {
    const c = bg.replace('#', '');
    const r = parseInt(c.substring(0, 2), 16);
    const g = parseInt(c.substring(2, 4), 16);
    const b = parseInt(c.substring(4, 6), 16);
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.6 ? '#111827' : '#ffffff';
  } catch {
    return '#ffffff';
  }
}
