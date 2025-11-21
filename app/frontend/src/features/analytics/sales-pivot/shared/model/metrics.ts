/**
 * sales-pivot/model/metrics.ts
 * フォーマッタ・ソートロジック・集計ユーティリティ
 * 
 * 純粋関数で構成され、状態を持たない
 */

import dayjs from 'dayjs';
import type {
  Mode,
  SortKey,
  SortOrder,
  MetricEntry,
  UniverseEntry,
  YYYYMM,
  SummaryQuery,
} from './types';

/**
 * フォーマッタ
 */
export const fmtCurrency = (n: number): string => `¥${n.toLocaleString('ja-JP')}`;

export const fmtNumber = (n: number): string => n.toLocaleString('ja-JP');

export const fmtUnitPrice = (v: number | null): string =>
  v == null
    ? '—'
    : `¥${v.toLocaleString('ja-JP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

/**
 * メトリクスから指定キーの値を取得
 */
type NumericSortKey = Exclude<SortKey, 'date' | 'name'>;

export const metricValue = (entry: MetricEntry, key: NumericSortKey): number | null => {
  switch (key) {
    case 'amount':
      return entry.amount;
    case 'qty':
      return entry.qty;
    case 'count':
      return entry.count;
    case 'unit_price':
      return entry.unit_price;
    default:
      return null;
  }
};

/**
 * メトリクス配列のソート（破壊的）
 */
export const sortMetrics = (
  arr: MetricEntry[],
  sortBy: SortKey,
  order: SortOrder
): void => {
  const dir = order === 'asc' ? 1 : -1;
  arr.sort((a, b) => {
    // date ソート
    if (sortBy === 'date') {
      const av = a.dateKey ?? a.name;
      const bv = b.dateKey ?? b.name;
      if (av > bv) return 1 * dir;
      if (av < bv) return -1 * dir;
      // 同値なら amount → qty でタイブレイク
      if (a.amount !== b.amount) return (a.amount - b.amount) * dir;
      if (a.qty !== b.qty) return (a.qty - b.qty) * dir;
      return a.name.localeCompare(b.name, 'ja');
    }

    // name ソート
    if (sortBy === 'name') {
      const cmp = a.name.localeCompare(b.name, 'ja');
      if (cmp !== 0) return cmp * dir;
      if (a.amount !== b.amount) return (a.amount - b.amount) * dir;
      if (a.qty !== b.qty) return (a.qty - b.qty) * dir;
      return 0;
    }

    // 数値ソート
    const av = metricValue(a, sortBy);
    const bv = metricValue(b, sortBy);
    if (av == null && bv == null) return a.name.localeCompare(b.name, 'ja');
    if (av == null) return 1;
    if (bv == null) return -1;
    if (av > bv) return 1 * dir;
    if (av < bv) return -1 * dir;
    // 同値なら amount → qty でタイブレイク
    if (a.amount !== b.amount) return (a.amount - b.amount) * dir;
    if (a.qty !== b.qty) return (a.qty - b.qty) * dir;
    return a.name.localeCompare(b.name, 'ja');
  });
};

/**
 * 月の日リストを生成（UniverseEntry形式）
 */
export const monthDays = (m: YYYYMM): UniverseEntry[] => {
  const start = dayjs(m + '-01');
  const days = start.daysInMonth();
  const list: UniverseEntry[] = [];
  for (let d = 1; d <= days; d++) {
    const s = start.date(d).format('YYYY-MM-DD');
    list.push({ id: `d_${s}`, name: s, dateKey: s });
  }
  return list;
};

/**
 * 期間内の全月を列挙
 */
export const monthsBetween = (from: YYYYMM, to: YYYYMM): YYYYMM[] => {
  const res: YYYYMM[] = [];
  let cur = dayjs(from + '-01');
  const end = dayjs(to + '-01');
  while (cur.isSame(end) || cur.isBefore(end)) {
    res.push(cur.format('YYYY-MM'));
    cur = cur.add(1, 'month');
  }
  return res;
};

/**
 * 期間内の全日リストを生成
 */
export const allDaysInRange = (range: { from: YYYYMM; to: YYYYMM }): UniverseEntry[] =>
  monthsBetween(range.from, range.to).flatMap((m) => monthDays(m));

/**
 * 軸（Mode）から日本語ラベルを取得
 */
export const axisLabel = (ax: Mode): string => {
  switch (ax) {
    case 'customer':
      return '顧客';
    case 'item':
      return '品名';
    case 'date':
      return '日付';
    default:
      return ax;
  }
};

/**
 * Mode から 3軸の順序を取得（baseAx, axB, axC）
 */
export const axesFromMode = (m: Mode): [Mode, Mode, Mode] => {
  if (m === 'customer') return ['customer', 'item', 'date'];
  if (m === 'item') return ['item', 'customer', 'date'];
  return ['date', 'customer', 'item'];
};

/**
 * 指定軸のマスタを Query から取得（フィルタ・期間適用前の全件）
 */
export const universeOf = (
  ax: Mode,
  q: SummaryQuery,
  customers: UniverseEntry[],
  items: UniverseEntry[]
): UniverseEntry[] => {
  if (ax === 'customer') return customers.map((c) => ({ id: c.id, name: c.name }));
  if (ax === 'item') return items.map((i) => ({ id: i.id, name: i.name }));
  const days = q.monthRange ? allDaysInRange(q.monthRange) : monthDays(q.month!);
  return days.map((d) => ({ id: d.id, name: d.name, dateKey: d.dateKey }));
};
