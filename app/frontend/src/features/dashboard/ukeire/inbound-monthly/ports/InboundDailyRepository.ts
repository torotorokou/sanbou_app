/**
 * InboundDailyRepository Port
 * 日次搬入量データ取得のインターフェース定義
 */

export type CumScope = "range" | "month" | "week" | "none";

export type InboundDailyRow = {
  ddate: string; // ISO date string "YYYY-MM-DD"
  iso_year: number;
  iso_week: number;
  iso_dow: number; // 1=Mon, 7=Sun
  is_business: boolean;
  segment: string | null;
  ton: number;
  cum_ton: number | null;
  prev_month_ton?: number | null; // 先月（4週前）の同曜日の搬入量
  prev_year_ton?: number | null; // 前年の同ISO週・同曜日の搬入量
  prev_month_cum_ton?: number | null; // 先月の累積搬入量
  prev_year_cum_ton?: number | null; // 前年の累積搬入量
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
