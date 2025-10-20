export type CalendarDayDTO = {
  date: string;          // 'YYYY-MM-DD'
  isHoliday?: boolean;
};

/**
 * CalendarCore 用の描画セル型（汎用）
 */
export interface CalendarCell {
  date: string; // ISO "YYYY-MM-DD"
  inMonth: boolean;
  /**
   * 任意の描画プロパティをここに追加可能
   * 各ドメイン（受入量など）はこの型を extends して利用
   */
  [key: string]: unknown;
}
