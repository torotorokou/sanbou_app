/**
 * 受入ダッシュボード - Value Objects
 * 日付操作・純粋関数群
 * 
 * @deprecated 日付関連の関数は @shared を使用してください
 * このファイルは後方互換性のために残されています
 */

import {
  toDate,
  toIsoDate,
  getMondayOfWeek,
  getCurrentMonth,
  getNextMonth,
  addDays,
  clamp,
  sum,
  monthNameJP,
  todayInMonth,
  dayjs,
  type IsoMonth,
  type IsoDate,
} from "@shared";

// ========================================
// Re-export from shared/utils/dateUtils
// ========================================

/**
 * @deprecated 代わりに @shared/utils/dateUtils の toDate を使用してください
 */
export { toDate };

/**
 * @deprecated 代わりに @shared/utils/dateUtils の toIsoDate を使用してください
 */
export const ymd = toIsoDate;

/**
 * @deprecated 代わりに @shared/utils/dateUtils の getMondayOfWeek を使用してください
 */
export { getMondayOfWeek as mondayOf };

/**
 * @deprecated 代わりに @shared/utils/dateUtils の getCurrentMonth を使用してください
 */
export { getCurrentMonth as curMonth };

/**
 * @deprecated 代わりに @shared/utils/dateUtils の getNextMonth を使用してください
 */
export { getNextMonth as nextMonth };

/**
 * @deprecated 代わりに @shared/utils/dateUtils の addDays を使用してください
 */
export { addDays };

/**
 * @deprecated 代わりに @shared/utils/dateUtils の sum を使用してください
 */
export { sum };

/**
 * @deprecated 代わりに @shared/utils/dateUtils の clamp を使用してください
 */
export { clamp };

/**
 * @deprecated 代わりに @shared/utils/dateUtils の monthNameJP を使用してください
 */
export { monthNameJP };

/**
 * @deprecated 代わりに @shared/utils/dateUtils の todayInMonth を使用してください
 */
export { todayInMonth };

/**
 * 実績カットオフ日を取得（昨日まで表示）
 * 
 * @param m - ISO月文字列
 * @returns ISO日付文字列
 */
export const getActualCutoffIso = (m: IsoMonth): IsoDate => {
  const now = dayjs();
  const monthStart = dayjs(m + "-01");
  if (monthStart.isSame(now, "month"))
    return now.subtract(1, "day").format("YYYY-MM-DD");
  if (monthStart.isBefore(now, "month"))
    return monthStart.endOf("month").format("YYYY-MM-DD");
  return monthStart.startOf("month").subtract(1, "day").format("YYYY-MM-DD");
};
