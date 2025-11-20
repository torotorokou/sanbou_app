/**
 * sales-pivot/model/types.ts
 * 売上ピボット分析のドメイン型・Query型・DTO型
 * 
 * 将来的に FastAPI の Pydantic / DB の集計ビューと対応させる想定
 */

export type YYYYMM = string;
export type YYYYMMDD = string;
export type ID = string;

/**
 * 分析モード（集約軸）
 * - customer: 顧客別
 * - item: 品名別
 * - date: 日付別
 */
export type Mode = 'customer' | 'item' | 'date';

/**
 * ソートキー
 */
export type SortKey = 'amount' | 'qty' | 'count' | 'unit_price' | 'date' | 'name';

/**
 * ソート順
 */
export type SortOrder = 'asc' | 'desc';

/**
 * 売上担当（営業）
 */
export interface SalesRep {
  id: ID;
  name: string;
}

/**
 * マスタエントリ（顧客 / 品名 / 日付）
 */
export interface UniverseEntry {
  id: ID;
  name: string;
  dateKey?: YYYYMMDD; // date モードのソート用
}

/**
 * メトリクスエントリ（集計結果）
 */
export interface MetricEntry {
  id: ID;
  name: string;         // 顧客名 | 品名 | 日付(YYYY-MM-DD)
  amount: number;       // 売上
  qty: number;          // 数量(kg)
  count: number;        // 台数
  unit_price: number | null; // 売単価 = Σ金額 / Σ数量（数量=0はnull）
  dateKey?: YYYYMMDD;   // dateモードのソート用
}

/**
 * サマリ行（営業ごとの TopN メトリクス）
 */
export interface SummaryRow {
  repId: ID;
  repName: string;
  topN: MetricEntry[];
}

/**
 * サマリ取得用クエリ（FastAPI / DB 集計ビューに渡す想定）
 */
export interface SummaryQuery {
  month?: YYYYMM;                            // 単月（例: "2025-11"）
  monthRange?: { from: YYYYMM; to: YYYYMM }; // 期間（例: { from: "2025-01", to: "2025-03" }）
  mode: Mode;                                 // 集約軸
  repIds: ID[];                               // 対象営業ID（空 = 全営業）
  filterIds: ID[];                            // フィルタID（空 = 全件）
  sortBy: SortKey;                            // ソートキー
  order: SortOrder;                           // ソート順
  topN: 10 | 20 | 50 | 'all';                 // 取得件数
}

/**
 * Pivot取得用クエリ（詳細ドリルダウン用）
 */
export interface PivotQuery {
  month?: YYYYMM;
  monthRange?: { from: YYYYMM; to: YYYYMM };
  baseAxis: Mode;       // 固定軸（例: customer）
  baseId: ID;           // 固定値（例: 'c_alpha'）
  repIds: ID[];         // 対象営業ID
  targetAxis: Mode;     // 展開軸（例: item）
  sortBy: SortKey;
  order: SortOrder;
  topN: 10 | 20 | 50 | 'all';
  cursor?: string | null; // ページネーション用カーソル
}

/**
 * カーソルベースページネーション結果
 */
export interface CursorPage<T> {
  rows: T[];
  next_cursor: string | null;
}

/**
 * 日次推移取得用クエリ
 */
export interface DailySeriesQuery {
  month?: YYYYMM;
  monthRange?: { from: YYYYMM; to: YYYYMM };
  repId?: ID;
  customerId?: ID;
  itemId?: ID;
}

/**
 * 日次推移データポイント
 */
export interface DailyPoint {
  date: YYYYMMDD;
  amount: number;
  qty: number;
  count: number;
  unit_price: number | null;
}

/**
 * CSV エクスポートオプション
 */
export interface ExportOptions {
  excludeZero: boolean;  // 0実績を除外（Excel負荷対策）
  splitBy: 'none' | 'rep'; // 分割出力（営業ごと / 単一ファイル）
  addAxisB: boolean;     // 残りモード1を列に追加
  addAxisC: boolean;     // 残りモード2を列に追加
}

export const DEFAULT_EXPORT_OPTIONS: ExportOptions = {
  excludeZero: true,
  splitBy: 'none',
  addAxisB: false,
  addAxisC: false,
};

/**
 * CSV エクスポート用クエリ
 */
export interface ExportQuery extends SummaryQuery {
  options: ExportOptions;
  targetRepIds: ID[];
}

/**
 * Drawer状態（閉じている or 開いている）
 */
export type DrawerState =
  | { open: false }
  | {
      open: true;
      baseAxis: Mode;
      baseId: ID;
      baseName: string;
      month?: YYYYMM;
      monthRange?: { from: YYYYMM; to: YYYYMM };
      repIds: ID[];
      targets: { axis: Mode; label: string }[];
      activeAxis: Mode;
      sortBy: SortKey;
      order: SortOrder;
      topN: 10 | 20 | 50 | 'all';
    };
