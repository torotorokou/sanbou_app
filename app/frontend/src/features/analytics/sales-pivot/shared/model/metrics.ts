/**
 * sales-pivot/model/metrics.ts
 * フォーマッタ・ソートロジック・集計ユーティリティ
 * 
 * 【概要】
 * 純粋関数で構成され、状態を持たないユーティリティモジュール
 * 
 * 【責務】
 * 1. 数値・通貨・日付のフォーマット
 * 2. メトリクスデータのソート処理
 * 3. 日付・期間に関する計算
 * 4. 軸（Mode）に関するヘルパー関数
 * 
 * 【設計原則】
 * - 全て純粋関数（同じ入力に対して常に同じ出力）
 * - 副作用なし（例外: sortMetrics は破壊的ソート）
 * - テスタブル（単体テストが容易）
 */

import { dayjs, formatCurrency } from '@shared/utils/dateUtils';
import type {
  Mode,
  SortKey,
  SortOrder,
  MetricEntry,
  UniverseEntry,
  YYYYMM,
  SummaryQuery,
} from './types';

// ========================================
// フォーマッタ関数群
// ========================================

/**
 * 通貨フォーマット
 * 
 * @deprecated 代わりに @shared/utils/dateUtils の formatCurrency を使用してください
 * 
 * @param n - 金額（数値）
 * @returns 日本円表記の文字列（例: "¥1,234,567"）
 */
export const fmtCurrency = formatCurrency;

/**
 * 数値フォーマット（3桁区切り）
 * 
 * @param n - 数値
 * @returns 3桁区切りの文字列（例: "1,234"）
 * 
 * @example
 * fmtNumber(1234)   // "1,234"
 * fmtNumber(500.5)  // "500.5"
 */
export const fmtNumber = (n: number): string => n.toLocaleString('ja-JP');

/**
 * 単価フォーマット（小数点2桁固定）
 * 
 * @param v - 単価（数値 or null）。nullの場合は計算不可を表す
 * @returns 単価文字列（例: "¥3,000.00"） or "—"（計算不可）
 * 
 * @description
 * 単価は「売上金額 ÷ 数量」で計算されるため、
 * 数量が0の場合はnullとなり、"—" で表示する
 * 
 * @example
 * fmtUnitPrice(3000.5)   // "¥3,000.50"
 * fmtUnitPrice(null)     // "—"
 * fmtUnitPrice(150.123)  // "¥150.12" (小数点2桁で四捨五入)
 */
export const fmtUnitPrice = (v: number | null): string =>
  v == null
    ? '—'
    : `¥${v.toLocaleString('ja-JP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

// ========================================
// メトリクス値抽出・ソート関連
// ========================================

/**
 * 数値型ソートキー
 * @description 'date' と 'name' を除いた、数値として扱えるソートキー
 */
type NumericSortKey = Exclude<SortKey, 'date' | 'name'>;

/**
 * メトリクスエントリから指定キーの値を取得
 * 
 * @param entry - メトリクスエントリ
 * @param key - 取得するメトリクスのキー（amount | qty | count | unit_price）
 * @returns 指定されたメトリクス値。存在しない場合はnull
 * 
 * @example
 * const entry = { id: 'c_alpha', name: '顧客A', amount: 1000, qty: 50, count: 5, unitPrice: 20 };
 * metricValue(entry, 'amount')  // 1000
 * metricValue(entry, 'qty')     // 50
 * metricValue(entry, 'unit_price') // 20
 */
export const metricValue = (entry: MetricEntry, key: NumericSortKey): number | null => {
  switch (key) {
    case 'amount':
      return entry.amount;
    case 'qty':
      return entry.qty;
    case 'count':
      return entry.count;
    case 'unit_price':
      return entry.unitPrice;
    default:
      return null;
  }
};

/**
 * メトリクス配列のソート（破壊的）
 * 
 * @param arr - ソート対象のメトリクス配列（この配列自体が変更される）
 * @param sortBy - ソートキー
 * @param order - ソート順（'asc' | 'desc'）
 * 
 * @description
 * メトリクス配列を指定されたキーと順序でソート（in-place）
 * 
 * 【ソートロジック】
 * 1. 主ソートキー（sortBy）で比較
 * 2. 同値の場合、タイブレイク（優先順: amount → qty → name）
 * 
 * 【特殊ケース】
 * - sortBy='date': dateKeyまたはnameを文字列として比較
 * - sortBy='name': 日本語ロケールでの辞書順比較
 * - sortBy='unit_price': nullは常に最後尾
 * 
 * @example
 * const metrics = [
 *   { id: '1', name: 'A', amount: 100, qty: 10, count: 1, unitPrice: 10 },
 *   { id: '2', name: 'B', amount: 200, qty: 20, count: 2, unitPrice: 10 },
 *   { id: '3', name: 'C', amount: 150, qty: 15, count: 1, unitPrice: 10 },
 * ];
 * sortMetrics(metrics, 'amount', 'desc');
 * // => [B(200), C(150), A(100)] の順にソート（破壊的）
 */
export const sortMetrics = (
  arr: MetricEntry[],
  sortBy: SortKey,
  order: SortOrder
): void => {
  const dir = order === 'asc' ? 1 : -1;
  
  arr.sort((a, b) => {
    // ========== 日付ソート ==========
    if (sortBy === 'date') {
      const av = a.dateKey ?? a.name;
      const bv = b.dateKey ?? b.name;
      if (av > bv) return 1 * dir;
      if (av < bv) return -1 * dir;
      
      // タイブレイク: 同じ日付なら amount → qty → name で比較
      if (a.amount !== b.amount) return (a.amount - b.amount) * dir;
      if (a.qty !== b.qty) return (a.qty - b.qty) * dir;
      return a.name.localeCompare(b.name, 'ja');
    }

    // ========== 名称ソート ==========
    if (sortBy === 'name') {
      const cmp = a.name.localeCompare(b.name, 'ja');
      if (cmp !== 0) return cmp * dir;
      
      // タイブレイク: 同名なら amount → qty で比較
      if (a.amount !== b.amount) return (a.amount - b.amount) * dir;
      if (a.qty !== b.qty) return (a.qty - b.qty) * dir;
      return 0;
    }

    // ========== 数値ソート（amount, qty, count, unit_price） ==========
    const av = metricValue(a, sortBy);
    const bv = metricValue(b, sortBy);
    
    // 両方nullの場合は名前で比較
    if (av == null && bv == null) return a.name.localeCompare(b.name, 'ja');
    
    // nullは常に後ろ（大きい値扱い）
    if (av == null) return 1;
    if (bv == null) return -1;
    
    // 数値比較
    if (av > bv) return 1 * dir;
    if (av < bv) return -1 * dir;
    
    // タイブレイク: 同値なら amount → qty → name で比較
    if (a.amount !== b.amount) return (a.amount - b.amount) * dir;
    if (a.qty !== b.qty) return (a.qty - b.qty) * dir;
    return a.name.localeCompare(b.name, 'ja');
  });
};

// ========================================
// 日付・期間計算ユーティリティ
// ========================================

/**
 * 指定月の日リストを生成（UniverseEntry形式）
 * 
 * @param m - 年月（YYYY-MM形式）
 * @returns その月の1日～月末までの日付エントリ配列
 * 
 * @description
 * 日付モードでの分析に使用。指定月の全日をUniverseEntry形式で返す
 * 
 * @example
 * monthDays('2025-11')
 * // => [
 * //   { id: 'd_2025-11-01', name: '2025-11-01', dateKey: '2025-11-01' },
 * //   { id: 'd_2025-11-02', name: '2025-11-02', dateKey: '2025-11-02' },
 * //   ...
 * //   { id: 'd_2025-11-30', name: '2025-11-30', dateKey: '2025-11-30' }
 * // ]
 */
export const monthDays = (m: YYYYMM): UniverseEntry[] => {
  const start = dayjs(m + '-01');
  const days = start.daysInMonth();
  const list: UniverseEntry[] = [];
  
  for (let d = 1; d <= days; d++) {
    const dateStr = start.date(d).format('YYYY-MM-DD');
    list.push({ 
      id: `d_${dateStr}`, 
      name: dateStr, 
      dateKey: dateStr 
    });
  }
  
  return list;
};

/**
 * 期間内の全月を列挙
 * 
 * @param from - 開始月（YYYY-MM形式）
 * @param to - 終了月（YYYY-MM形式、from以降である必要がある）
 * @returns 期間内の全月の配列（from月 ～ to月を含む）
 * 
 * @description
 * 月次の期間分析で使用。fromからtoまでの全ての月をYYYY-MM形式で返す
 * 
 * @example
 * monthsBetween('2025-01', '2025-03')
 * // => ['2025-01', '2025-02', '2025-03']
 * 
 * monthsBetween('2024-12', '2025-02')
 * // => ['2024-12', '2025-01', '2025-02']
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
 * 
 * @param range - 期間（from, to を含むオブジェクト）
 * @returns 期間内の全日のUniverseEntry配列
 * 
 * @description
 * monthsBetween と monthDays を組み合わせ、
 * 期間内の全ての日をフラットな配列として返す
 * 
 * @example
 * allDaysInRange({ from: '2025-01', to: '2025-02' })
 * // => [
 * //   { id: 'd_2025-01-01', name: '2025-01-01', dateKey: '2025-01-01' },
 * //   { id: 'd_2025-01-02', name: '2025-01-02', dateKey: '2025-01-02' },
 * //   ...
 * //   { id: 'd_2025-01-31', name: '2025-01-31', dateKey: '2025-01-31' },
 * //   { id: 'd_2025-02-01', name: '2025-02-01', dateKey: '2025-02-01' },
 * //   ...
 * //   { id: 'd_2025-02-28', name: '2025-02-28', dateKey: '2025-02-28' }
 * // ]
 */
export const allDaysInRange = (range: { from: YYYYMM; to: YYYYMM }): UniverseEntry[] =>
  monthsBetween(range.from, range.to).flatMap((m) => monthDays(m));

// ========================================
// 軸（Mode）関連ヘルパー
// ========================================

/**
 * 軸（Mode）から日本語ラベルを取得
 * 
 * @param ax - 分析モード（customer | item | date）
 * @returns 日本語のラベル文字列
 * 
 * @description
 * UI表示用に、内部のMode値を日本語表記に変換
 * 
 * @example
 * axisLabel('customer') // "顧客"
 * axisLabel('item')     // "品名"
 * axisLabel('date')     // "日付"
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
 * Modeから3軸の順序を取得（baseAx, axB, axC）
 * 
 * @param m - 基準となる分析モード
 * @returns 3軸のタプル [基準軸, 第2軸, 第3軸]
 * 
 * @description
 * ピボット分析では常に3軸（customer, item, date）を扱う。
 * 基準軸を指定すると、残りの2軸を決定された順序で返す。
 * CSV出力時の列順などに使用される。
 * 
 * @example
 * axesFromMode('customer') // ['customer', 'item', 'date']
 * axesFromMode('item')     // ['item', 'customer', 'date']
 * axesFromMode('date')     // ['date', 'customer', 'item']
 */
export const axesFromMode = (m: Mode): [Mode, Mode, Mode] => {
  if (m === 'customer') return ['customer', 'item', 'date'];
  if (m === 'item') return ['item', 'customer', 'date'];
  return ['date', 'customer', 'item'];
};

/**
 * 指定軸のマスタデータをQueryから取得（フィルタ・期間適用前の全件）
 * 
 * @param ax - 対象の軸（customer | item | date）
 * @param q - サマリクエリ（期間情報を含む）
 * @param customers - 顧客マスタ全件
 * @param items - 品名マスタ全件
 * @returns 指定軸のUniverseEntry配列
 * 
 * @description
 * 軸に応じたマスタデータを返す汎用関数
 * - customer軸: 顧客マスタ全件
 * - item軸: 品名マスタ全件
 * - date軸: クエリの期間に基づいた日付リスト
 * 
 * フィルタリング前の「全件」を返すため、
 * フィルタ選択肢の生成などに使用される
 * 
 * @example
 * // 顧客軸のマスタ取得
 * universeOf('customer', query, customers, items)
 * // => 全顧客のUniverseEntry配列
 * 
 * // 日付軸のマスタ取得（2025年11月）
 * universeOf('date', { month: '2025-11', ... }, customers, items)
 * // => 2025年11月1日～30日のUniverseEntry配列
 */
export const universeOf = (
  ax: Mode,
  q: SummaryQuery,
  customers: UniverseEntry[],
  items: UniverseEntry[]
): UniverseEntry[] => {
  // 顧客軸の場合
  if (ax === 'customer') {
    return customers.map((c) => ({ id: c.id, name: c.name }));
  }
  
  // 品名軸の場合
  if (ax === 'item') {
    return items.map((i) => ({ id: i.id, name: i.name }));
  }
  
  // 日付軸の場合：クエリの期間設定に基づいて日付リストを生成
  const days = q.monthRange 
    ? allDaysInRange(q.monthRange) 
    : monthDays(q.month!);
  
  return days.map((d) => ({ 
    id: d.id, 
    name: d.name, 
    dateKey: d.dateKey 
  }));
};
