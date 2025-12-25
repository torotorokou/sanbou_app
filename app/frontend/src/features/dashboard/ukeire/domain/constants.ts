/**
 * 受入ダッシュボード - Constants
 * 色定数とフォント設定
 */

export const COLORS = {
  primary: "#1677ff",
  actual: "#52c41a",
  target: "#faad14",
  baseline: "#9e9e9e",
  danger: "#cf1322",
  warn: "#fa8c16",
  ok: "#389e0d",
  sunday: "#ff85c0",

  // 営業カレンダーと統一した色定義（CalendarCardと同じ値）
  business: "#52c41a", // 通常営業日（緑）
  holiday: "#ff85c0", // 予約営業日・日祝（ピンク）
  closed: "#cf1322", // 休業日（赤）
} as const;

export const FONT = {
  family: undefined as string | undefined,
  size: 14,
} as const;
