/**
 * InboundDailyRepository Port
 * 日次搬入量データ取得のインターフェース定義
 */

export type CumScope = 'range' | 'month' | 'week' | 'none';

/**
 * 日次搬入量データ行
 * バックエンドのInboundDailyRowと完全一致
 */
export type InboundDailyRow = {
  ddate: string; // ISO date string "YYYY-MM-DD"
  iso_year: number; // ISO年
  iso_week: number; // ISO週番号
  iso_dow: number; // ISO曜日（1=月, 7=日）
  is_business: boolean; // 営業日フラグ
  segment: string | null; // セグメント（オプション）
  ton: number; // 日次搬入量トン数
  cum_ton: number | null; // 累積搬入量トン数（cum_scope指定時のみ）
  prev_month_ton: number | null; // 先月（4週前）の同曜日の搬入量
  prev_year_ton: number | null; // 前年の同ISO週・同曜日の搬入量
  prev_month_cum_ton: number | null; // 先月の累積搬入量
  prev_year_cum_ton: number | null; // 前年の累積搬入量
};

export type FetchDailyParams = {
  start: string; // YYYY-MM-DD
  end: string; // YYYY-MM-DD
  segment?: string | null;
  cum_scope?: CumScope;
};

/**
 * 日次搬入量データ取得のポート
 */
export interface InboundDailyRepository {
  /**
   * 日次搬入量データを取得（カレンダー連続・0埋め済み）
   * @param params 取得パラメータ
   * @returns 日次データ配列
   */
  fetchDaily(params: FetchDailyParams): Promise<InboundDailyRow[]>;
}
