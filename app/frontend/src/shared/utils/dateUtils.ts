/**
 * Date Utilities
 * 日付操作・フォーマットの統一ライブラリ
 *
 * @module shared/utils/dateUtils
 * @created 2024-12-02
 * @refactoring P1: 日付ユーティリティ統合 (refactor/centralize-scattered-concerns)
 *
 * 【設計方針】
 * - dayjs を内部実装として使用し、一貫したAPIを提供
 * - 全てのプラグインはこのファイルで一括初期化
 * - ISO 8601 形式を標準とする
 * - タイムゾーンは日本時間（JST）を前提
 */

import dayjs, { type Dayjs } from 'dayjs';
import isoWeek from 'dayjs/plugin/isoWeek';
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter';
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore';

// ========================================
// プラグインの一括初期化
// ========================================
dayjs.extend(isoWeek);
dayjs.extend(isSameOrAfter);
dayjs.extend(isSameOrBefore);

// ========================================
// 型定義
// ========================================

/** ISO 8601 形式の月: YYYY-MM */
export type IsoMonth = string;

/** ISO 8601 形式の日付: YYYY-MM-DD */
export type IsoDate = string;

/** ISO 8601 形式の日時: YYYY-MM-DDTHH:mm:ss.sssZ */
export type IsoDateTime = string;

// ========================================
// フォーマット定数
// ========================================

/**
 * 日付フォーマット定数
 * アプリケーション全体で使用する標準フォーマット
 */
export const DATE_FORMATS = {
  // ISO標準
  /** ISO日付: YYYY-MM-DD */
  isoDate: 'YYYY-MM-DD',
  /** ISO月: YYYY-MM */
  isoMonth: 'YYYY-MM',
  /** ISO日時: YYYY-MM-DDTHH:mm:ss */
  isoDateTime: 'YYYY-MM-DDTHH:mm:ss',

  // 日本語表示
  /** 日本語日付: YYYY年MM月DD日 */
  jpDate: 'YYYY年MM月DD日',
  /** 日本語月: YYYY年MM月 */
  jpMonth: 'YYYY年MM月',
  /** 短縮日付: MM/DD */
  jpShortDate: 'MM/DD',
  /** 日時: YYYY/MM/DD HH:mm */
  jpDateTime: 'YYYY/MM/DD HH:mm',
  /** 完全日時: YYYY/MM/DD HH:mm:ss */
  jpFullDateTime: 'YYYY/MM/DD HH:mm:ss',

  // API互換（コンパクト形式）
  /** コンパクト日付: YYYYMMDD */
  compactDate: 'YYYYMMDD',
  /** コンパクト月: YYYYMM */
  compactMonth: 'YYYYMM',
} as const;

// ========================================
// 基本変換
// ========================================

/**
 * 文字列→Date変換
 * ISO形式の日付文字列をDateオブジェクトに変換
 *
 * @param s - ISO日付文字列 (YYYY-MM-DD)
 * @returns Dateオブジェクト
 *
 * @example
 * ```typescript
 * const date = toDate('2024-12-02');
 * ```
 */
export const toDate = (s: string): Date => new Date(s + 'T00:00:00');

/**
 * Date→ISO日付文字列
 *
 * @param d - Dateオブジェクト
 * @returns ISO日付文字列 (YYYY-MM-DD)
 */
export const toIsoDate = (d: Date): IsoDate => dayjs(d).format(DATE_FORMATS.isoDate);

/**
 * Date→ISO月文字列
 *
 * @param d - Dateオブジェクト
 * @returns ISO月文字列 (YYYY-MM)
 */
export const toIsoMonth = (d: Date): IsoMonth => dayjs(d).format(DATE_FORMATS.isoMonth);

/**
 * Dayjs→ISO日付文字列
 *
 * @param d - Dayjsオブジェクト
 * @returns ISO日付文字列 (YYYY-MM-DD)
 */
export const dayjsToIsoDate = (d: Dayjs): IsoDate => d.format(DATE_FORMATS.isoDate);

/**
 * Dayjs→ISO月文字列
 *
 * @param d - Dayjsオブジェクト
 * @returns ISO月文字列 (YYYY-MM)
 */
export const dayjsToIsoMonth = (d: Dayjs): IsoMonth => d.format(DATE_FORMATS.isoMonth);

// ========================================
// フォーマット関数
// ========================================

/**
 * 日本語日付フォーマット: YYYY年MM月DD日
 *
 * @param d - Date, Dayjs, または日付文字列
 * @returns 日本語形式の日付文字列
 *
 * @example
 * ```typescript
 * formatJpDate('2024-12-02'); // "2024年12月02日"
 * ```
 */
export const formatJpDate = (d: Date | Dayjs | string): string =>
  dayjs(d).format(DATE_FORMATS.jpDate);

/**
 * 日本語月フォーマット: YYYY年MM月
 *
 * @param d - Date, Dayjs, または日付文字列
 * @returns 日本語形式の月文字列
 */
export const formatJpMonth = (d: Date | Dayjs | string): string =>
  dayjs(d).format(DATE_FORMATS.jpMonth);

/**
 * 短縮日付フォーマット: MM/DD
 *
 * @param d - Date, Dayjs, または日付文字列
 * @returns 短縮形式の日付文字列
 */
export const formatShortDate = (d: Date | Dayjs | string): string =>
  dayjs(d).format(DATE_FORMATS.jpShortDate);

/**
 * 日時フォーマット: YYYY/MM/DD HH:mm
 *
 * @param d - Date, Dayjs, または日付文字列
 * @returns 日時文字列
 */
export const formatDateTime = (d: Date | Dayjs | string): string =>
  dayjs(d).format(DATE_FORMATS.jpDateTime);

/**
 * 完全日時フォーマット: YYYY/MM/DD HH:mm:ss
 *
 * @param d - Date, Dayjs, または日付文字列
 * @returns 完全な日時文字列
 */
export const formatFullDateTime = (d: Date | Dayjs | string): string =>
  dayjs(d).format(DATE_FORMATS.jpFullDateTime);

// ========================================
// 日付操作
// ========================================

/**
 * 指定日が属する週の月曜日（ISO週）を取得
 *
 * @param d - Date または Dayjs
 * @returns 週の月曜日のDateオブジェクト
 *
 * @example
 * ```typescript
 * const monday = getMondayOfWeek(new Date('2024-12-05')); // 2024-12-02
 * ```
 */
export const getMondayOfWeek = (d: Date | Dayjs): Date => {
  const dj = dayjs(d);
  return dj.startOf('isoWeek').toDate();
};

/**
 * 現在月を取得
 *
 * @returns 現在月のISO月文字列 (YYYY-MM)
 */
export const getCurrentMonth = (): IsoMonth => dayjs().format(DATE_FORMATS.isoMonth);

/**
 * 翌月を取得
 *
 * @param m - ISO月文字列 (YYYY-MM)
 * @returns 翌月のISO月文字列
 */
export const getNextMonth = (m: IsoMonth): IsoMonth =>
  dayjs(m + '-01')
    .add(1, 'month')
    .format(DATE_FORMATS.isoMonth);

/**
 * 前月を取得
 *
 * @param m - ISO月文字列 (YYYY-MM)
 * @returns 前月のISO月文字列
 */
export const getPreviousMonth = (m: IsoMonth): IsoMonth =>
  dayjs(m + '-01')
    .subtract(1, 'month')
    .format(DATE_FORMATS.isoMonth);

/**
 * n日後のDateを取得
 *
 * @param d - 基準日
 * @param n - 加算する日数
 * @returns n日後のDateオブジェクト
 */
export const addDays = (d: Date, n: number): Date => dayjs(d).add(n, 'day').toDate();

/**
 * n日前のDateを取得
 *
 * @param d - 基準日
 * @param n - 減算する日数
 * @returns n日前のDateオブジェクト
 */
export const subtractDays = (d: Date, n: number): Date => dayjs(d).subtract(n, 'day').toDate();

/**
 * 指定月における「今日」を取得
 * - 現在月なら今日
 * - 過去月なら20日（または月末）
 * - 未来月なら1日
 *
 * @param m - ISO月文字列 (YYYY-MM)
 * @returns ISO日付文字列 (YYYY-MM-DD)
 */
export const todayInMonth = (m: IsoMonth): IsoDate => {
  const nowM = getCurrentMonth();
  if (m === nowM) return dayjs().format(DATE_FORMATS.isoDate);

  const targetMonth = dayjs(m + '-01');
  const now = dayjs();

  if (targetMonth.isBefore(now, 'month')) {
    // 過去月: 20日または月末
    const last = targetMonth.endOf('month').date();
    const d = Math.min(20, last);
    return `${m}-${String(d).padStart(2, '0')}`;
  } else {
    // 未来月: 1日
    return `${m}-01`;
  }
};

// ========================================
// 比較・検証
// ========================================

/**
 * 日付が同じかチェック
 *
 * @param a - 比較元の日付
 * @param b - 比較先の日付
 * @returns 同じ日付ならtrue
 */
export const isSameDate = (a: Date | Dayjs | string, b: Date | Dayjs | string): boolean =>
  dayjs(a).isSame(dayjs(b), 'day');

/**
 * 日付が範囲内かチェック
 *
 * @param date - チェック対象の日付
 * @param start - 範囲の開始日
 * @param end - 範囲の終了日
 * @returns 範囲内ならtrue
 */
export const isInRange = (
  date: Date | Dayjs | string,
  start: Date | Dayjs | string,
  end: Date | Dayjs | string
): boolean => {
  const d = dayjs(date);
  return d.isSameOrAfter(dayjs(start), 'day') && d.isSameOrBefore(dayjs(end), 'day');
};

/**
 * 有効な日付文字列かチェック
 *
 * @param s - チェック対象の文字列
 * @returns 有効な日付ならtrue
 */
export const isValidDate = (s: string): boolean => dayjs(s).isValid();

/**
 * 月範囲を計算する
 *
 * @param start - 開始月
 * @param end - 終了月
 * @returns YYYY-MM形式の月の配列（最大24ヶ月）
 *
 * @example
 * ```typescript
 * getMonthRange(dayjs('2024-01'), dayjs('2024-03'));
 * // ['2024-01', '2024-02', '2024-03']
 * ```
 */
export function getMonthRange(start: Dayjs | null, end: Dayjs | null): IsoMonth[] {
  if (!start || !end) return [];

  const range: string[] = [];
  let current = start.startOf('month');

  while (current.isBefore(end.endOf('month')) || current.isSame(end, 'month')) {
    range.push(current.format(DATE_FORMATS.isoMonth));
    current = current.add(1, 'month');
    if (range.length > 24) break; // 安全弁: 最大24ヶ月
  }

  return range;
}

/**
 * 期間範囲が有効かチェックする
 *
 * @param start - 開始月
 * @param end - 終了月
 * @returns 有効な範囲ならtrue
 */
export function isValidPeriodRange(start: Dayjs | null, end: Dayjs | null): boolean {
  if (!start || !end) return false;
  return start.isSameOrBefore(end, 'month');
}

// ========================================
// 数値フォーマット（日付関連）
// ========================================

/**
 * 通貨フォーマット
 *
 * @param n - 金額（数値）
 * @returns 日本円表記の文字列
 *
 * @example
 * ```typescript
 * formatCurrency(1234567); // "¥1,234,567"
 * ```
 */
export const formatCurrency = (n: number): string => `¥${n.toLocaleString('ja-JP')}`;

/**
 * パーセントフォーマット
 *
 * @param n - パーセント値
 * @param decimals - 小数点以下の桁数（デフォルト: 1）
 * @returns パーセント表記の文字列
 *
 * @example
 * ```typescript
 * formatPercent(45.678, 1); // "45.7%"
 * ```
 */
export const formatPercent = (n: number, decimals = 1): string => `${n.toFixed(decimals)}%`;

/**
 * 数値を範囲内にクランプ
 *
 * @param v - 値
 * @param lo - 最小値
 * @param hi - 最大値
 * @returns クランプされた値
 */
export const clamp = (v: number, lo: number, hi: number): number => Math.max(lo, Math.min(hi, v));

/**
 * 配列の合計
 *
 * @param a - 数値配列
 * @returns 合計値
 */
export const sum = (a: number[]): number => a.reduce((p, c) => p + c, 0);

/**
 * ISO月形式を「YYYY年MM月」に変換
 *
 * @param m - ISO月文字列 (YYYY-MM)
 * @returns 日本語形式の月文字列
 *
 * @example
 * ```typescript
 * monthNameJP('2024-12'); // "2024年12月"
 * ```
 */
export const monthNameJP = (m: IsoMonth): string => {
  const [y, mm] = m.split('-').map(Number);
  return `${y}年${mm}月`;
};

// ========================================
// Re-export dayjs for advanced usage
// ========================================

/**
 * dayjs のエクスポート
 * 高度な用途のために dayjs を直接使用できるようにする
 *
 * 注意: 通常の日付操作にはこのモジュールの関数を使用してください
 */
export { dayjs };
export type { Dayjs };
