/**
 * sales-pivot/infrastructure/salesPivot.repository.ts
 * Repository インターフェース + モック実装
 * 
 * 【概要】
 * データアクセス層のインターフェース定義とモック実装を提供
 * 
 * 【設計パターン】
 * - Repository パターン: ドメインロジックをデータアクセスから分離
 * - Dependency Inversion Principle (DIP): インターフェースに依存、実装に依存しない
 * 
 * 【将来計画】
 * 現在はモック実装のみだが、本番環境では以下の実装を追加予定:
 * - `HttpSalesPivotRepository`: FastAPI バックエンド（/api/sales/...）との通信
 * - coreApi (Axios instance) を使用したHTTP通信
 * - レスポンスキャッシュ、エラーハンドリング
 * 
 * 【使用方法】
 * ```typescript
 * import { salesPivotRepository } from './salesPivot.repository';
 * 
 * // シングルトンインスタンスを使用
 * const summary = await salesPivotRepository.fetchSummary(query);
 * ```
 */

import type {
  SummaryQuery,
  SummaryRow,
  PivotQuery,
  CursorPage,
  MetricEntry,
  DailySeriesQuery,
  DailyPoint,
  ExportQuery,
  SalesRep,
  UniverseEntry,
} from '../model/types';
import { sortMetrics, monthDays, monthsBetween, allDaysInRange } from '../model/metrics';

// ========================================
// Repository インターフェース
// ========================================

/**
 * 売上ピボット分析データアクセス用 Repository インターフェース
 * 
 * @description
 * DIP（依存性逆転の原則）に基づき、具体的な実装から独立したインターフェース
 * ViewModelは常にこのインターフェースを通してデータを取得する
 * 
 * 【実装クラス】
 * - MockSalesPivotRepository: モックデータを返すテスト用実装
 * - HttpSalesPivotRepository（未実装）: FastAPI バックエンドと通信する本番実装
 */
export interface SalesPivotRepository {
  /**
   * サマリデータ取得（営業ごとの TopN メトリクス）
   * 
   * @param query - サマリ取得クエリ（期間、モード、ソート条件等）
   * @returns 営業ごとのTopNメトリクス配列
   * 
   * @description
   * メイン画面のサマリテーブル表示用データを取得
   * 各営業担当者について、指定されたモード（顧客/品名/日付）で
   * TopN件のメトリクスを集計して返す
   */
  fetchSummary(query: SummaryQuery): Promise<SummaryRow[]>;

  /**
   * Pivot データ取得（固定軸 × 展開軸）
   * 
   * @param query - Pivot取得クエリ（固定軸、展開軸、ソート条件等）
   * @returns カーソルページネーション形式のメトリクス
   * 
   * @description
   * ドリルダウン用のPivotデータを取得
   * 例: 「顧客A」を固定して「品名別」に展開した内訳データ
   * カーソルベースページネーションに対応
   */
  fetchPivot(query: PivotQuery): Promise<CursorPage<MetricEntry>>;

  /**
   * 日次推移データ取得
   * 
   * @param query - 日次推移取得クエリ（期間、営業/顧客/品名の絞り込み）
   * @returns 日次データポイント配列
   * 
   * @description
   * 折れ線グラフ表示用の日次推移データを取得
   * 指定された期間内の各日の売上・数量・件数を返す
   */
  fetchDailySeries(query: DailySeriesQuery): Promise<DailyPoint[]>;

  /**
   * CSV エクスポート
   * 
   * @param query - エクスポートクエリ（出力条件、フォーマット設定等）
   * @returns CSV形式のBlob（ファイルダウンロード用）
   * 
   * @description
   * サマリデータをCSV形式でエクスポート
   * - モック実装: Blob を直接返却
   * - HTTP実装（予定）: サーバー側でCSV生成し、Blob or ダウンロードURL を返却
   */
  exportModeCube(query: ExportQuery): Promise<Blob>;

  /**
   * マスタデータ取得（営業担当者）
   * 
   * @returns 営業担当者マスタ配列
   */
  getSalesReps(): Promise<SalesRep[]>;

  /**
   * マスタデータ取得（顧客）
   * 
   * @returns 顧客マスタ配列
   */
  getCustomers(): Promise<UniverseEntry[]>;

  /**
   * マスタデータ取得（品名）
   * 
   * @returns 品名マスタ配列
   */
  getItems(): Promise<UniverseEntry[]>;
}

// ========================================
// モック実装
// ========================================

/**
 * モックマスタデータ（営業担当者）
 * 
 * @description 開発・テスト用のサンプルデータ
 * 本番環境では FastAPI から取得
 */
const MOCK_REPS: SalesRep[] = [
  { id: 'rep_a', name: '営業A' },
  { id: 'rep_b', name: '営業B' },
  { id: 'rep_c', name: '営業C' },
  { id: 'rep_d', name: '営業D' },
];

/**
 * モックマスタデータ（顧客）
 * 
 * @description 開発・テスト用のサンプルデータ
 * 本番環境では FastAPI から取得
 */
const MOCK_CUSTOMERS: UniverseEntry[] = [
  { id: 'c_alpha', name: '顧客アルファ' },
  { id: 'c_bravo', name: '顧客ブラボー' },
  { id: 'c_charlie', name: '顧客チャーリー' },
  { id: 'c_delta', name: '顧客デルタ' },
  { id: 'c_echo', name: '顧客エコー' },
  { id: 'c_fox', name: '顧客フォックス' },
  { id: 'c_golf', name: '顧客ゴルフ' },
  { id: 'c_hotel', name: '顧客ホテル' },
  { id: 'c_india', name: '顧客インディア' },
  { id: 'c_juliet', name: '顧客ジュリエット' },
];

/**
 * モックマスタデータ（品名）
 * 
 * @description 開発・テスト用のサンプルデータ
 * 本番環境では FastAPI から取得
 */
const MOCK_ITEMS: UniverseEntry[] = [
  { id: 'i_a', name: '商品A' },
  { id: 'i_b', name: '商品B' },
  { id: 'i_c', name: '商品C' },
  { id: 'i_d', name: '商品D' },
  { id: 'i_e', name: '商品E' },
  { id: 'i_f', name: '商品F' },
  { id: 'i_g', name: '商品G' },
  { id: 'i_h', name: '商品H' },
  { id: 'i_i', name: '商品I' },
  { id: 'i_j', name: '商品J' },
  { id: 'i_k', name: '商品K' },
];

// ========================================
// モックデータ生成ユーティリティ
// ========================================

/**
 * 遅延処理（ネットワーク遅延のシミュレーション）
 * 
 * @param ms - 遅延時間（ミリ秒）
 * @returns Promise（指定時間後に resolve）
 */
const delay = (ms = 180) => new Promise((r) => setTimeout(r, ms));

/**
 * ランダムな整数を生成
 * 
 * @param min - 最小値（含む）
 * @param max - 最大値（含む）
 * @returns min以上max以下のランダムな整数
 */
const rndInt = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min;

/**
 * ランダムにメトリクスを生成（矛盾を極力避ける）
 * 
 * @param weight - 重み係数（営業担当者の実績傾向を反映、デフォルト1）
 * @returns 生成されたメトリクス（amount, qty, count, unit_price）
 * 
 * @description
 * リアリティのあるモックデータ生成のため、以下のロジックを実装:
 * - 約17%の確率で0実績（has = false）
 * - 数量(qty)と件数(count)に相関を持たせる（大量注文ほど件数も多い傾向）
 * - 単価(unit_price)と数量から売上(amount)を逆算し、ランダム性を加える
 * - 数量0の場合は単価もnull（計算不可）
 */
const makeMetric = (
  weight = 1
): Pick<MetricEntry, 'amount' | 'qty' | 'count' | 'unit_price'> => {
  // 約83%の確率で実績あり、17%で0実績
  const has = Math.random() < 0.83;
  
  // 数量（kg）: 0 ～ 140kg × weight
  const qty = has ? Math.max(0, Math.round(Math.random() * 140 * weight)) : 0;
  
  // 件数: qtyに相関（300～500kg あたり1件の割合）
  // qty>0なら最低1件は保証
  const count = qty > 0 ? Math.max(1, Math.round(qty / rndInt(300, 500))) : 0;
  
  // 単価（円/kg）: 120～520円
  const price = has ? rndInt(120, 520) : 0;
  
  // 売上金額: 数量 × 単価 × (0.7～1.3のランダム係数)
  // ランダム係数で取引ごとの価格変動を表現
  const amount = has ? Math.round(qty * price * (0.7 + Math.random() * 0.6)) : 0;
  
  // 実際の単価（逆算）: 売上 ÷ 数量（小数点2桁）
  const unit_price = qty > 0 ? Math.round((amount / qty) * 100) / 100 : null;
  
  return { amount, qty, count, unit_price };
};

/**
 * カーソルベースページネーション
 * 
 * @param sorted - ソート済みの全データ配列
 * @param cursor - 現在のカーソル位置（文字列形式の数値、null/undefinedは先頭）
 * @param pageSize - 1ページあたりの件数
 * @returns ページネーション結果（rows: データ配列, next_cursor: 次ページのカーソル）
 * 
 * @description
 * オフセットベースではなくカーソルベースでページネーション
 * - cursor = "0": 0番目から取得
 * - cursor = "20": 20番目から取得
 * - next_cursor = null: 最終ページ到達
 */
function paginateWithCursor<T>(
  sorted: T[],
  cursor: string | null | undefined,
  pageSize: number
): CursorPage<T> {
  const start = cursor ? Number(cursor) : 0;
  const end = Math.min(start + pageSize, sorted.length);
  
  return {
    rows: sorted.slice(start, end),
    next_cursor: end < sorted.length ? String(end) : null,
  };
}

// ========================================
// モック Repository 実装クラス
// ========================================

/**
 * モック Repository 実装
 * 
 * @description
 * 開発・テスト環境で使用するRepository実装
 * ランダムデータを生成して返すため、バックエンドなしでUI開発が可能
 * 
 * 【特徴】
 * - ネットワーク遅延をシミュレート（delay関数）
 * - リアリティのあるランダムデータ生成
 * - 実際のAPI仕様を想定したレスポンス構造
 * 
 * 【注意】
 * - データは毎回ランダム生成されるため、リロードで変わる
 * - ページネーションは見た目上動作するが、実際のDBアクセスはしない
 * 
 * @implements {SalesPivotRepository}
 */
export class MockSalesPivotRepository implements SalesPivotRepository {
  /**
   * 営業マスタ取得
   * 
   * @returns 営業担当者マスタ配列
   */
  async getSalesReps(): Promise<SalesRep[]> {
    await delay(50);
    return [...MOCK_REPS];
  }

  /**
   * 顧客マスタ取得
   * 
   * @returns 顧客マスタ配列
   */
  async getCustomers(): Promise<UniverseEntry[]> {
    await delay(50);
    return [...MOCK_CUSTOMERS];
  }

  /**
   * 品名マスタ取得
   * 
   * @returns 品名マスタ配列
   */
  async getItems(): Promise<UniverseEntry[]> {
    await delay(50);
    return [...MOCK_ITEMS];
  }

  /**
   * サマリデータ取得
   * 
   * @param q - サマリ取得クエリ
   * @returns 営業ごとのTopNメトリクス配列
   * 
   * @description
   * 以下の処理フローでモックデータを生成:
   * 1. 対象営業を絞り込み（repIds が空なら全営業）
   * 2. 期間から対象月を算出
   * 3. モードに応じたユニバース（全件リスト）を生成
   * 4. filterIds でフィルタリング
   * 5. 各営業 × 各エンティティでランダムメトリクス生成
   * 6. ソート・TopN抽出
   */
  async fetchSummary(q: SummaryQuery): Promise<SummaryRow[]> {
    // 1. 対象営業を絞り込み
    const reps = q.repIds.length
      ? MOCK_REPS.filter((r) => q.repIds.includes(r.id))
      : MOCK_REPS;

    // 2. 期間から対象月を算出
    const months = q.monthRange
      ? monthsBetween(q.monthRange.from, q.monthRange.to)
      : [q.month!];

    // 3. モードに応じたユニバース（全件リスト）を生成
    const universe: UniverseEntry[] =
      q.mode === 'customer'
        ? MOCK_CUSTOMERS
        : q.mode === 'item'
        ? MOCK_ITEMS
        : q.monthRange
        ? allDaysInRange(q.monthRange)
        : monthDays(q.month!);

    // 4. filterIds でフィルタリング（空なら全件）
    const filtered = q.filterIds.length
      ? universe.filter((u) => q.filterIds.includes(u.id))
      : universe;

    // 5. 各営業ごとにメトリクスを生成
    const rows: SummaryRow[] = reps.map((rep) => {
      // 営業ごとの重み係数（実績傾向の個人差をシミュレート）
      const weight = 1 + ((rep.id.charCodeAt(rep.id.length - 1) % 3) * 0.2);
      
      // 各エンティティについてメトリクス生成
      const pool: MetricEntry[] = filtered.map((t) => {
        const m = makeMetric(weight);
        
        // 期間が複数月の場合は月数分を乗算（単純化）
        const mult = q.mode === 'date' ? 1 : months.length;
        const amount = Math.round(m.amount * mult);
        const qty = Math.round(m.qty * mult);
        const count = Math.round(m.count * mult);
        
        return {
          id: t.id,
          name: t.name,
          amount,
          qty,
          count,
          unit_price: qty > 0 ? Math.round((amount / qty) * 100) / 100 : null,
          dateKey: t.dateKey,
        };
      });
      
      // 6. ソート
      sortMetrics(pool, q.sortBy, q.order);
      const top = q.topN === 'all' ? pool : pool.slice(0, q.topN);
      return { repId: rep.id, repName: rep.name, topN: top };
    });

    await delay();
    return rows;
  }

  async fetchPivot(params: PivotQuery): Promise<CursorPage<MetricEntry>> {
    const months = params.monthRange
      ? monthsBetween(params.monthRange.from, params.monthRange.to)
      : [params.month!];

    const universe: UniverseEntry[] =
      params.targetAxis === 'customer'
        ? MOCK_CUSTOMERS
        : params.targetAxis === 'item'
        ? MOCK_ITEMS
        : params.monthRange
        ? allDaysInRange(params.monthRange)
        : monthDays(params.month!);

    const rows: MetricEntry[] = universe.map((t) => {
      const repWeight =
        (params.repIds.length ? params.repIds : MOCK_REPS.map((r) => r.id)).reduce(
          (acc, id) => acc + (1 + ((id.charCodeAt(id.length - 1) % 3) * 0.1)),
          0
        ) / Math.max(1, params.repIds.length || MOCK_REPS.length);
      const baseWeight = 1 + ((params.baseId.charCodeAt(params.baseId.length - 1) % 5) * 0.08);
      const m = makeMetric(0.9 * repWeight * baseWeight);
      const mult = params.targetAxis === 'date' ? 1 : months.length;
      const amount = Math.round(m.amount * mult);
      const qty = Math.round(m.qty * mult);
      const count = Math.round(m.count * mult);
      return {
        id: t.id,
        name: t.name,
        amount,
        qty,
        count,
        unit_price: qty > 0 ? Math.round((amount / qty) * 100) / 100 : null,
        dateKey: t.dateKey,
      };
    });

    sortMetrics(rows, params.sortBy, params.order);

    if (params.topN === 'all') {
      const page = paginateWithCursor(rows, params.cursor, 30);
      await delay();
      return page;
    } else {
      await delay();
      return { rows: rows.slice(0, params.topN), next_cursor: null };
    }
  }

  async fetchDailySeries(params: DailySeriesQuery): Promise<DailyPoint[]> {
    const days = params.monthRange
      ? allDaysInRange(params.monthRange)
      : monthDays(params.month!);
    const series = days.map((d) => {
      const m = makeMetric(1);
      return {
        date: d.name,
        amount: m.amount,
        qty: m.qty,
        count: m.count,
        unit_price: m.qty > 0 ? Math.round((m.amount / m.qty) * 100) / 100 : null,
      };
    });
    await delay(120);
    return series;
  }

  async exportModeCube(query: ExportQuery): Promise<Blob> {
    // CSV 生成ロジック（簡易実装）
    // 本来は query.options に基づいて動的に列を組み立てる
    const rows: Array<Record<string, string | number>> = [];
    for (const repId of query.targetRepIds) {
      const rep = MOCK_REPS.find((r) => r.id === repId);
      if (!rep) continue;
      // ダミー行を追加（実運用では集計ロジックを呼ぶ）
      rows.push({
        営業: rep.name,
        売上: 1000000,
        数量: 500,
        件数: 10,
        単価: 2000,
      });
    }

    const headers = Object.keys(rows[0] ?? {});
    const csv = [
      headers.join(','),
      ...rows.map((r) => headers.map((h) => r[h] ?? '').join(',')),
    ].join('\r\n');

    const blob = new Blob(['\uFEFF', csv], { type: 'text/csv;charset=utf-8;' });
    await delay(200);
    return blob;
  }
}

/**
 * デフォルトリポジトリインスタンス（モック）
 * 将来的に環境変数などで HTTP 実装に切り替え可能
 */
export const salesPivotRepository: SalesPivotRepository = new MockSalesPivotRepository();


/* ========================================
 * HTTP実装（実API連携）
 * ======================================== */

import { coreApi } from '@/shared';

/**
 * HTTP Repository 実装
 * バックエンド /core_api/analytics/sales-tree/* と連携
 */
export class HttpSalesPivotRepository implements SalesPivotRepository {
  async getSalesReps(): Promise<SalesRep[]> {
    // 実データから営業マスタを取得
    interface ApiRep {
      rep_id: number;
      rep_name: string;
    }
    const reps = await coreApi.get<ApiRep[]>('/core_api/analytics/sales-tree/masters/reps');
    return reps.map(r => ({
      id: String(r.rep_id),
      name: r.rep_name
    }));
  }

  async getCustomers(): Promise<UniverseEntry[]> {
    // 実データから顧客マスタを取得
    interface ApiCustomer {
      customer_id: string;
      customer_name: string;
    }
    const customers = await coreApi.get<ApiCustomer[]>('/core_api/analytics/sales-tree/masters/customers');
    return customers.map(c => ({
      id: c.customer_id,
      name: c.customer_name
    }));
  }

  async getItems(): Promise<UniverseEntry[]> {
    // 実データから品目マスタを取得
    interface ApiItem {
      item_id: number;
      item_name: string;
    }
    const items = await coreApi.get<ApiItem[]>('/core_api/analytics/sales-tree/masters/items');
    return items.map(i => ({
      id: String(i.item_id),
      name: i.item_name
    }));
  }

  async fetchSummary(q: SummaryQuery): Promise<SummaryRow[]> {
    // QueryをAPIリクエスト形式に変換
    // month: "2025-10" -> date_from: "2025-10-01", date_to: "2025-10-31"
    // monthRange: {from: "2025-10", to: "2025-12"} -> date_from: "2025-10-01", date_to: "2025-12-31"
    let date_from: string;
    let date_to: string;
    
    if (q.monthRange) {
      date_from = `${q.monthRange.from}-01`;
      date_to = this._getMonthEndDate(q.monthRange.to);
    } else if (q.month) {
      date_from = `${q.month}-01`;
      date_to = this._getMonthEndDate(q.month);
    } else {
      // フォールバック（通常はここには来ない）
      const now = new Date();
      const yyyymm = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
      date_from = `${yyyymm}-01`;
      date_to = this._getMonthEndDate(yyyymm);
    }

    const req = {
      date_from,
      date_to,
      mode: q.mode,
      rep_ids: q.repIds.map(id => parseInt(id, 10)),
      filter_ids: q.filterIds,
      top_n: q.topN === 'all' ? 0 : q.topN,
      sort_by: q.sortBy,
      order: q.order,
    };

    interface ApiSummaryRow {
      rep_id: number;
      rep_name: string;
      metrics: Array<{
        id: string;
        name: string;
        amount: number;
        qty: number;
        slip_count: number;
        unit_price: number | null;
        date_key?: string | null;
      }>;
    }

    const res = await coreApi.post<ApiSummaryRow[]>('/core_api/analytics/sales-tree/summary', req);
    
    // snake_case → camelCase 変換
    return res.map(row => ({
      repId: String(row.rep_id),
      repName: row.rep_name,
      topN: row.metrics.map(m => ({
        id: m.id,
        name: m.name,
        amount: m.amount,
        qty: m.qty,
        count: m.slip_count,
        unit_price: m.unit_price,
        dateKey: m.date_key ?? undefined,
      })),
    }));
  }

  async fetchPivot(params: PivotQuery): Promise<CursorPage<MetricEntry>> {
    // PivotQueryをAPIリクエスト形式に変換
    let date_from: string;
    let date_to: string;
    
    if (params.monthRange) {
      date_from = `${params.monthRange.from}-01`;
      date_to = this._getMonthEndDate(params.monthRange.to);
    } else if (params.month) {
      date_from = `${params.month}-01`;
      date_to = this._getMonthEndDate(params.month);
    } else {
      throw new Error('month or monthRange is required');
    }

    const req = {
      date_from,
      date_to,
      base_axis: params.baseAxis,
      base_id: params.baseId,
      rep_ids: params.repIds.map(id => parseInt(id, 10)),
      target_axis: params.targetAxis,
      top_n: params.topN === 'all' ? 0 : params.topN,
      sort_by: params.sortBy,
      order: params.order,
      cursor: params.cursor,
    };

    interface ApiCursorPage {
      rows: Array<{
        id: string;
        name: string;
        amount: number;
        qty: number;
        slip_count: number;
        unit_price: number | null;
        date_key?: string | null;
      }>;
      next_cursor: string | null;
    }

    const res = await coreApi.post<ApiCursorPage>('/core_api/analytics/sales-tree/pivot', req);
    
    return {
      rows: res.rows.map(m => ({
        id: m.id,
        name: m.name,
        amount: m.amount,
        qty: m.qty,
        count: m.slip_count,
        unit_price: m.unit_price,
        dateKey: m.date_key ?? undefined,
      })),
      next_cursor: res.next_cursor,
    };
  }

  async fetchDailySeries(params: DailySeriesQuery): Promise<DailyPoint[]> {
    let date_from: string;
    let date_to: string;
    
    if (params.monthRange) {
      date_from = `${params.monthRange.from}-01`;
      date_to = this._getMonthEndDate(params.monthRange.to);
    } else if (params.month) {
      date_from = `${params.month}-01`;
      date_to = this._getMonthEndDate(params.month);
    } else {
      throw new Error('month or monthRange is required');
    }

    const req = {
      date_from,
      date_to,
      rep_id: params.repId ? parseInt(params.repId, 10) : undefined,
      customer_id: params.customerId,
      item_id: params.itemId ? parseInt(params.itemId, 10) : undefined,
    };

    interface ApiDailyPoint {
      date: string;
      amount: number;
      qty: number;
      slip_count: number;
      unit_price: number | null;
    }

    const res = await coreApi.post<ApiDailyPoint[]>('/core_api/analytics/sales-tree/daily-series', req);
    
    return res.map(p => ({
      date: p.date,
      amount: p.amount,
      qty: p.qty,
      count: p.slip_count,
      unit_price: p.unit_price,
    }));
  }

  async exportModeCube(query: ExportQuery): Promise<Blob> {
    // ExportQueryをAPIリクエスト形式に変換
    let date_from: string;
    let date_to: string;
    
    if (query.monthRange) {
      date_from = `${query.monthRange.from}-01`;
      date_to = this._getMonthEndDate(query.monthRange.to);
    } else if (query.month) {
      date_from = `${query.month}-01`;
      date_to = this._getMonthEndDate(query.month);
    } else {
      throw new Error('month or monthRange is required for CSV export');
    }

    const req = {
      date_from,
      date_to,
      mode: query.mode,
      rep_ids: query.targetRepIds.map(id => parseInt(id, 10)),
      filter_ids: query.filterIds,
      sort_by: query.sortBy,
      order: query.order,
    };

    // CSV Export APIを呼び出し (Blob返却)
    const blob = await coreApi.post<Blob>(
      '/core_api/analytics/sales-tree/export',
      req,
      {
        headers: { 'Content-Type': 'application/json' },
        responseType: 'blob',
      }
    );

    return blob;
  }

  /**
   * YYYY-MM から月末日を取得 (YYYY-MM-DD形式)
   */
  private _getMonthEndDate(yyyymm: string): string {
    const [year, month] = yyyymm.split('-').map(Number);
    const nextMonth = new Date(year, month, 1);
    const lastDay = new Date(nextMonth.getTime() - 86400000);
    const dd = String(lastDay.getDate()).padStart(2, '0');
    return `${yyyymm}-${dd}`;
  }
}
