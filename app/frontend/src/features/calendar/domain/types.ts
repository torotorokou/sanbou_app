export type CalendarDayDTO = {
  ddate: string;         // 'YYYY-MM-DD'
  y: number;             // 年
  m: number;             // 月
  iso_year: number;      // ISO年
  iso_week: number;      // ISO週番号
  iso_dow: number;       // ISO曜日（1=月, 7=日）
  is_holiday: boolean;   // 祝日フラグ
  is_second_sunday: boolean; // 第2日曜日フラグ
  is_company_closed: boolean; // 会社休業日フラグ
  day_type: string;      // 日タイプ（NORMAL, RESERVATION, CLOSED）
  is_business: boolean;  // 営業日フラグ
  date?: string;         // 後方互換性のためのエイリアス
  isHoliday?: boolean;   // 後方互換性のためのエイリアス
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
