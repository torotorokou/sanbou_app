/**
 * sales-pivot/infrastructure/salesPivot.repository.ts
 * Repository インターフェース + モック実装
 * 
 * 将来的に HttpSalesPivotRepository を追加して /api/sales/... を叩く想定
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

/**
 * Repository インターフェース（DIP）
 * 
 * 将来的に FastAPI の /api/sales/... エンドポイントと連携する際は、
 * HttpSalesPivotRepository を実装して coreApi を使う
 */
export interface SalesPivotRepository {
  /**
   * サマリデータ取得（営業ごとの TopN メトリクス）
   */
  fetchSummary(query: SummaryQuery): Promise<SummaryRow[]>;

  /**
   * Pivot データ取得（固定軸 × 展開軸）
   */
  fetchPivot(query: PivotQuery): Promise<CursorPage<MetricEntry>>;

  /**
   * 日次推移データ取得
   */
  fetchDailySeries(query: DailySeriesQuery): Promise<DailyPoint[]>;

  /**
   * CSV エクスポート（Blob 返却 or ダウンロード）
   * ※モック実装では Blob 返却、HTTP 実装では URL 返却も可
   */
  exportModeCube(query: ExportQuery): Promise<Blob>;

  /**
   * マスタデータ取得（営業）
   */
  getSalesReps(): Promise<SalesRep[]>;

  /**
   * マスタデータ取得（顧客）
   */
  getCustomers(): Promise<UniverseEntry[]>;

  /**
   * マスタデータ取得（品名）
   */
  getItems(): Promise<UniverseEntry[]>;
}

/* ========================================
 * モック実装
 * ======================================== */

// モックマスタデータ
const MOCK_REPS: SalesRep[] = [
  { id: 'rep_a', name: '営業A' },
  { id: 'rep_b', name: '営業B' },
  { id: 'rep_c', name: '営業C' },
  { id: 'rep_d', name: '営業D' },
];

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

// ユーティリティ
const delay = (ms = 180) => new Promise((r) => setTimeout(r, ms));
const rndInt = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min;

/**
 * 乱数でメトリクスを生成（矛盾を極力避ける）
 */
const makeMetric = (
  weight = 1
): Pick<MetricEntry, 'amount' | 'qty' | 'count' | 'unit_price'> => {
  const has = Math.random() < 0.83; // 17%は0実績
  const qty = has ? Math.max(0, Math.round(Math.random() * 140 * weight)) : 0;
  // 台数はqtyにゆるく相関（qty>0なら最低1台）
  const count = qty > 0 ? Math.max(1, Math.round(qty / rndInt(300, 500))) : 0;
  const price = has ? rndInt(120, 520) : 0;
  const amount = has ? Math.round(qty * price * (0.7 + Math.random() * 0.6)) : 0;
  const unit_price = qty > 0 ? Math.round((amount / qty) * 100) / 100 : null;
  return { amount, qty, count, unit_price };
};

/**
 * カーソルベースページネーション
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

/**
 * モック Repository 実装
 */
export class MockSalesPivotRepository implements SalesPivotRepository {
  async getSalesReps(): Promise<SalesRep[]> {
    await delay(50);
    return [...MOCK_REPS];
  }

  async getCustomers(): Promise<UniverseEntry[]> {
    await delay(50);
    return [...MOCK_CUSTOMERS];
  }

  async getItems(): Promise<UniverseEntry[]> {
    await delay(50);
    return [...MOCK_ITEMS];
  }

  async fetchSummary(q: SummaryQuery): Promise<SummaryRow[]> {
    const reps = q.repIds.length
      ? MOCK_REPS.filter((r) => q.repIds.includes(r.id))
      : MOCK_REPS;

    const months = q.monthRange
      ? monthsBetween(q.monthRange.from, q.monthRange.to)
      : [q.month!];

    const universe: UniverseEntry[] =
      q.mode === 'customer'
        ? MOCK_CUSTOMERS
        : q.mode === 'item'
        ? MOCK_ITEMS
        : q.monthRange
        ? allDaysInRange(q.monthRange)
        : monthDays(q.month!);

    const filtered = q.filterIds.length
      ? universe.filter((u) => q.filterIds.includes(u.id))
      : universe;

    const rows: SummaryRow[] = reps.map((rep) => {
      const weight = 1 + ((rep.id.charCodeAt(rep.id.length - 1) % 3) * 0.2);
      const pool: MetricEntry[] = filtered.map((t) => {
        const m = makeMetric(weight);
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
        台数: 10,
        売単価: 2000,
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
