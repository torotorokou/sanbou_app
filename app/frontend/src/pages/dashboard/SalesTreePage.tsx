// src/pages/SalesPivotBoardPlusWithCharts.tsx
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import type { FC } from 'react';
import {
  App, Badge, Button, Card, Col, DatePicker, Divider, Drawer, Empty, Row,
  Segmented, Select, Space, Statistic, Table, Tag, Tabs, Tooltip, Typography, Dropdown, Switch
} from 'antd';
import type { TableColumnsType, TableProps, MenuProps } from 'antd';
import {
  ArrowDownOutlined, ArrowUpOutlined, InfoCircleOutlined, SwapOutlined, ReloadOutlined, DownloadOutlined, DownOutlined
} from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, ResponsiveContainer, LineChart, Line
} from 'recharts';

/* =========================
 * Domain Types
 * ========================= */
type YYYYMM = string;
type YYYYMMDD = string;

type Mode = 'customer' | 'item' | 'date';
type SortKey = 'amount' | 'qty' | 'count' | 'unit_price' | 'date' | 'name';
type SortOrder = 'asc' | 'desc';
type ID = string;

interface SalesRep { id: ID; name: string; }

interface MetricEntry {
  id: ID;
  name: string;        // 顧客名 | 品名 | 日付(YYYY-MM-DD)
  amount: number;      // 売上
  qty: number;         // 数量(kg)
  count: number;       // 台数
  unit_price: number | null; // 売単価 = 金額/数量（数量=0はnull）
  dateKey?: YYYYMMDD;  // dateモードのソート用
}

interface SummaryRow { repId: ID; repName: string; topN: MetricEntry[]; }

interface SummaryQuery {
  month?: YYYYMM;                // 単月
  monthRange?: { from: YYYYMM; to: YYYYMM }; // 期間
  mode: Mode; repIds: ID[]; filterIds: ID[];
  sortBy: SortKey; order: SortOrder; topN: 10 | 20 | 50 | 'all';
}

type CursorPage<T> = { rows: T[]; next_cursor: string | null };

/* =========================
 * Export options (simple)
 * ========================= */
type SplitBy = 'none' | 'rep';

type ExportOptions = {
  excludeZero: boolean;  // 0実績を除外（Excel負荷対策）
  splitBy: SplitBy;      // 分割出力
  addAxisB: boolean;     // 残りモード1（実名）を列に追加
  addAxisC: boolean;     // 残りモード2（実名）を列に追加
};

const DEFAULT_EXPORT_OPTIONS: ExportOptions = {
  excludeZero: true,     // 既定ON（Excel負荷対策）
  splitBy: 'none',
  addAxisB: false,
  addAxisC: false,
};

/* =========================
 * Mock Masters
 * ========================= */
const REPS: SalesRep[] = [
  { id: 'rep_a', name: '営業A' },
  { id: 'rep_b', name: '営業B' },
  { id: 'rep_c', name: '営業C' },
  { id: 'rep_d', name: '営業D' },
];

const CUSTOMERS: Array<{ id: ID; name: string }> = [
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

const ITEMS: Array<{ id: ID; name: string }> = [
  { id: 'i_a', name: '商品A' }, { id: 'i_b', name: '商品B' }, { id: 'i_c', name: '商品C' },
  { id: 'i_d', name: '商品D' }, { id: 'i_e', name: '商品E' }, { id: 'i_f', name: '商品F' },
  { id: 'i_g', name: '商品G' }, { id: 'i_h', name: '商品H' }, { id: 'i_i', name: '商品I' },
  { id: 'i_j', name: '商品J' }, { id: 'i_k', name: '商品K' },
];

/* =========================
 * Utils
 * ========================= */
const delay = (ms = 180) => new Promise((r) => setTimeout(r, ms));
const rndInt = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min;

// 乱数でメトリクスを生成（矛盾を極力避ける）
const makeMetric = (weight = 1): Pick<MetricEntry, 'amount' | 'qty' | 'count' | 'unit_price'> => {
  const has = Math.random() < 0.83; // 17%は0実績
  const qty = has ? Math.max(0, Math.round((Math.random() * 140) * weight)) : 0;
  // 台数はqtyにゆるく相関（qty>0なら最低1台）
  const count = qty > 0 ? Math.max(1, Math.round(qty / rndInt(300, 500))) : 0;
  const price = has ? rndInt(120, 520) : 0;
  const amount = has ? Math.round(qty * price * (0.7 + Math.random() * 0.6)) : 0;
  const unit_price = qty > 0 ? Math.round((amount / qty) * 100) / 100 : null;
  return { amount, qty, count, unit_price };
};

const monthDays = (m: YYYYMM) => {
  const start = dayjs(m + '-01');
  const days = start.daysInMonth();
  const list: { id: ID; name: string; dateKey: YYYYMMDD }[] = [];
  for (let d = 1; d <= days; d++) {
    const s = start.date(d).format('YYYY-MM-DD');
    list.push({ id: `d_${s}`, name: s, dateKey: s });
  }
  return list;
};

const monthsBetween = (from: YYYYMM, to: YYYYMM): YYYYMM[] => {
  const res: YYYYMM[] = [];
  let cur = dayjs(from + '-01');
  const end = dayjs(to + '-01');
  while (cur.isSame(end) || cur.isBefore(end)) {
    res.push(cur.format('YYYY-MM'));
    cur = cur.add(1, 'month');
  }
  return res;
};

const allDaysInRange = (range: { from: YYYYMM; to: YYYYMM }) =>
  monthsBetween(range.from, range.to).flatMap(m => monthDays(m));

const sortMetrics = (arr: MetricEntry[], sortBy: SortKey, order: SortOrder) => {
  const dir = order === 'asc' ? 1 : -1;
  arr.sort((a, b) => {
    if (sortBy === 'date') {
      const av = a.dateKey ?? a.name; const bv = b.dateKey ?? b.name;
      if (av > bv) return 1 * dir;
      if (av < bv) return -1 * dir;
      if (a.amount !== b.amount) return (a.amount - b.amount) * dir;
      if (a.qty !== b.qty) return (a.qty - b.qty) * dir;
      return a.name.localeCompare(b.name, 'ja');
    }
    if (sortBy === 'name') {
      const cmp = a.name.localeCompare(b.name, 'ja');
      if (cmp !== 0) return cmp * dir;
      if (a.amount !== b.amount) return (a.amount - b.amount) * dir;
      if (a.qty !== b.qty) return (a.qty - b.qty) * dir;
      return 0;
    }
    const av = (a as any)[sortBy]; const bv = (b as any)[sortBy];
    if (av == null && bv == null) return a.name.localeCompare(b.name, 'ja');
    if (av == null) return 1;
    if (bv == null) return -1;
    if (av > bv) return 1 * dir;
    if (av < bv) return -1 * dir;
    if (a.amount !== b.amount) return (a.amount - b.amount) * dir;
    if (a.qty !== b.qty) return (a.qty - b.qty) * dir;
    return a.name.localeCompare(b.name, 'ja');
  });
};

/* =========================
 * Mock APIs
 * ========================= */
async function fetchSummary(q: SummaryQuery): Promise<SummaryRow[]> {
  const reps = q.repIds.length ? REPS.filter(r => q.repIds.includes(r.id)) : REPS;

  const months = q.monthRange ? monthsBetween(q.monthRange.from, q.monthRange.to) : [q.month!];

  const universe =
    q.mode === 'customer' ? CUSTOMERS :
    q.mode === 'item' ? ITEMS :
    q.monthRange ? allDaysInRange(q.monthRange) : monthDays(q.month!);

  const filtered = q.filterIds.length ? (universe as any[]).filter(u => q.filterIds.includes(u.id)) : universe;

  const rows: SummaryRow[] = reps.map(rep => {
    const weight = 1 + (rep.id.charCodeAt(rep.id.length - 1) % 3) * 0.2;
    const pool: MetricEntry[] = (filtered as any[]).map((t: any) => {
      const m = makeMetric(weight);
      const mult = q.mode === 'date' ? 1 : months.length;
      const amount = Math.round(m.amount * mult);
      const qty = Math.round(m.qty * mult);
      const count = Math.round(m.count * mult);
      return {
        id: t.id, name: t.name, amount, qty, count,
        unit_price: qty > 0 ? Math.round((amount / qty) * 100) / 100 : null,
        dateKey: t.dateKey
      };
    });
    sortMetrics(pool, q.sortBy, q.order);
    const top = q.topN === 'all' ? pool : pool.slice(0, q.topN);
    return { repId: rep.id, repName: rep.name, topN: top };
  });

  await delay();
  return rows;
}

function paginateWithCursor<T>(sorted: T[], cursor: string | null | undefined, pageSize: number): CursorPage<T> {
  const start = cursor ? Number(cursor) : 0;
  const end = Math.min(start + pageSize, sorted.length);
  return { rows: sorted.slice(start, end), next_cursor: end < sorted.length ? String(end) : null };
}

async function fetchPivot(params: {
  month?: YYYYMM; monthRange?: { from: YYYYMM; to: YYYYMM };
  baseAxis: Mode; baseId: ID; repIds: ID[];
  targetAxis: Mode; sortBy: SortKey; order: SortOrder; topN: 10 | 20 | 50 | 'all'; cursor?: string | null;
}): Promise<CursorPage<MetricEntry>> {
  const months = params.monthRange ? monthsBetween(params.monthRange.from, params.monthRange.to) : [params.month!];
  const universe =
    params.targetAxis === 'customer' ? CUSTOMERS :
    params.targetAxis === 'item' ? ITEMS :
    params.monthRange ? allDaysInRange(params.monthRange) : monthDays(params.month!);

  const rows: MetricEntry[] = (universe as any[]).map((t: any) => {
    const repWeight =
      (params.repIds.length ? params.repIds : REPS.map(r => r.id))
        .reduce((acc, id) => acc + (1 + (id.charCodeAt(id.length - 1) % 3) * 0.1), 0) / Math.max(1, (params.repIds.length || REPS.length));
    const baseWeight = 1 + (params.baseId.charCodeAt(params.baseId.length - 1) % 5) * 0.08;
    const m = makeMetric(0.9 * repWeight * baseWeight);
    const mult = params.targetAxis === 'date' ? 1 : months.length;
    const amount = Math.round(m.amount * mult);
    const qty = Math.round(m.qty * mult);
    const count = Math.round(m.count * mult);
    return {
      id: t.id, name: t.name, amount, qty, count,
      unit_price: qty > 0 ? Math.round((amount / qty) * 100) / 100 : null, dateKey: t.dateKey
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

async function fetchDailySeries(params: {
  month?: YYYYMM; monthRange?: { from: YYYYMM; to: YYYYMM };
  repId?: ID; customerId?: ID; itemId?: ID;
}): Promise<Array<{ date: YYYYMMDD; amount: number; qty: number; count: number; unit_price: number | null }>> {
  const days = params.monthRange ? allDaysInRange(params.monthRange) : monthDays(params.month!);
  const series = days.map(d => {
    const m = makeMetric(1);
    return {
      date: d.name, amount: m.amount, qty: m.qty, count: m.count,
      unit_price: m.qty > 0 ? Math.round((m.amount / m.qty) * 100) / 100 : null
    };
  });
  await delay(120);
  return series;
}

/* =========================
 * Formatters / Small UI
 * ========================= */
const fmtCurrency = (n: number) => `¥${n.toLocaleString('ja-JP')}`;
const fmtNumber = (n: number) => n.toLocaleString('ja-JP');
const fmtUnitPrice = (v: number | null) => (v == null ? '—' : `¥${v.toLocaleString('ja-JP', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`);

const SortBadge: FC<{ label: string; keyName: SortKey; order: SortOrder }> = ({ label, keyName, order }) => (
  <Badge count={order === 'desc' ? <ArrowDownOutlined /> : <ArrowUpOutlined />} style={{ backgroundColor: '#237804' }}>
    <Tag style={{ marginRight: 8 }}>{label}: {keyName}</Tag>
  </Badge>
);

/* =========================
 * CSV Builder
 * ========================= */
function toCsv(rows: Array<Record<string, any>>, bomUtf8 = true): Blob {
  const headers = Object.keys(rows[0] ?? {});
  const escape = (v: any) => {
    if (v == null) return '';
    let s = String(v).replace(/"/g, '""');
    // Excelの数式インジェクション最低限対策
    if (/^[=+\-@]/.test(s)) s = "'" + s;
    if (/[",\r\n]/.test(s)) return `"${s}"`;
    return s;
  };
  const csv = [headers.join(','), ...rows.map(r => headers.map(h => escape(r[h])).join(','))].join('\r\n');
  const blob = new Blob([bomUtf8 ? '\uFEFF' : '', csv], { type: 'text/csv;charset=utf-8;' });
  return blob;
}
function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

/* =========================
 * CSV Export helpers
 * ========================= */
type Axis = Mode;

const axisLabel = (ax: Axis) => ax === 'customer' ? '顧客' : ax === 'item' ? '品名' : '日付';

const universeOf = (ax: Axis, q: SummaryQuery) => {
  if (ax === 'customer') return CUSTOMERS.map(c => ({ id: c.id, name: c.name }));
  if (ax === 'item')     return ITEMS.map(i => ({ id: i.id, name: i.name }));
  const days = q.monthRange ? allDaysInRange(q.monthRange) : monthDays(q.month!);
  return days.map(d => ({ id: d.id, name: d.name, dateKey: d.dateKey }));
};

const axesFromMode = (m: Mode): [Axis, Axis, Axis] => {
  if (m === 'customer') return ['customer', 'item', 'date'];
  if (m === 'item')     return ['item', 'customer', 'date'];
  return ['date', 'customer', 'item'];
};

/* =========================
 * Component
 * ========================= */
const SalesPivotBoardPlusWithCharts: FC = () => {
  const { message } = App.useApp?.() ?? { message: { success: () => {}, warning: () => {}, error: () => {} } as any };

  // Period
  const [periodMode, setPeriodMode] = useState<'single' | 'range'>('single');
  const [month, setMonth] = useState<Dayjs>(dayjs().startOf('month'));
  const [range, setRange] = useState<[Dayjs, Dayjs] | null>(null);

  // Controls
  const [mode, setMode] = useState<Mode>('customer');
  const [topN, setTopN] = useState<10 | 20 | 50 | 'all'>('all');
  const [sortBy, setSortBy] = useState<SortKey>('amount');
  const [order, setOrder] = useState<SortOrder>('desc');
  const [repIds, setRepIds] = useState<ID[]>([]);
  const [filterIds, setFilterIds] = useState<ID[]>([]);

  // Export options (persist)
  const [exportOptions, setExportOptions] = useState<ExportOptions>(() => {
    try {
      const raw = localStorage.getItem('exportOptions_v1');
      return raw ? JSON.parse(raw) as ExportOptions : DEFAULT_EXPORT_OPTIONS;
    } catch {
      return DEFAULT_EXPORT_OPTIONS;
    }
  });
  useEffect(() => {
    localStorage.setItem('exportOptions_v1', JSON.stringify(exportOptions));
  }, [exportOptions]);

  // （残り2軸の個別選択は今回の方針で廃止）

  // Data
  const [summary, setSummary] = useState<SummaryRow[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // Drawer (pivot)
  type DrawerState =
    | { open: false }
    | {
        open: true;
        baseAxis: Mode; baseId: ID; baseName: string;
        month?: YYYYMM; monthRange?: { from: YYYYMM; to: YYYYMM };
        repIds: ID[];
        targets: { axis: Mode; label: string }[]; activeAxis: Mode;
        sortBy: SortKey; order: SortOrder; topN: 10 | 20 | 50 | 'all';
      };
  const [drawer, setDrawer] = useState<DrawerState>({ open: false });

  const [pivotData, setPivotData] = useState<Record<Mode, MetricEntry[]>>({ customer: [], item: [], date: [] });
  const [pivotCursor, setPivotCursor] = useState<Record<Mode, string | null>>({ customer: null, item: null, date: null });
  const [pivotLoading, setPivotLoading] = useState<boolean>(false);

  const [repSeriesCache, setRepSeriesCache] = useState<Record<ID, Array<{ date: YYYYMMDD; amount: number; qty: number; count: number; unit_price: number | null }>>>({});

  // Query materialize
  const query: SummaryQuery = useMemo(() => {
    const base = { mode, repIds, filterIds, sortBy, order, topN };
    if (periodMode === 'single') return { ...base, month: month.format('YYYY-MM') };
    if (range) return { ...base, monthRange: { from: range[0].format('YYYY-MM'), to: range[1].format('YYYY-MM') } };
    return { ...base, month: month.format('YYYY-MM') };
  }, [periodMode, month, range, mode, repIds, filterIds, sortBy, order, topN]);

  // Load
  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await fetchSummary(query);
      setSummary(rows);
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => { reload(); }, [reload]);

  // Select options
  const repOptions = useMemo(() => REPS.map(r => ({ label: r.name, value: r.id })), []);
  const filterOptions = useMemo(() => {
    if (mode === 'customer') return CUSTOMERS.map(c => ({ label: c.name, value: c.id }));
    if (mode === 'item') return ITEMS.map(i => ({ label: i.name, value: i.id }));
    if (query.monthRange) return allDaysInRange(query.monthRange).map(d => ({ label: d.name, value: d.id }));
    return monthDays(query.month!).map(d => ({ label: d.name, value: d.id }));
  }, [mode, query]);

  // ====== 残り2軸の候補リスト ======
  const [baseAx, axB, axC] = useMemo(() => axesFromMode(mode), [mode]);

  // axisB/axisC option lists are not used for export selection in this simplified approach

  // Header totals
  const headerTotals = useMemo(() => {
    const flat = summary.flatMap(r => r.topN);
    const amount = flat.reduce((s, x) => s + x.amount, 0);
    const qty = flat.reduce((s, x) => s + x.qty, 0);
    const count = flat.reduce((s, x) => s + x.count, 0);
    const unit = qty > 0 ? Math.round((amount / qty) * 100) / 100 : null;
    return { amount, qty, count, unit };
  }, [summary]);

  // 選択営業名（KPIタイトル表示用）
  const selectedRepLabel = useMemo(() => {
    if (repIds.length === 0) return '未選択';
    const names = REPS.filter(r => repIds.includes(r.id)).map(r => r.name);
    return names.length <= 3 ? names.join('・') : `${names.slice(0, 3).join('・')} ほか${names.length - 3}名`;
  }, [repIds]);

  // ============ CSV Export ============
  const periodLabel = useMemo(() => {
    return periodMode === 'single'
      ? month.format('YYYYMM')
      : `${(range?.[0] ?? dayjs()).format('YYYYMM')}-${(range?.[1] ?? dayjs()).format('YYYYMM')}`;
  }, [periodMode, month, range]);

  // exportModeCube: 新方針に合わせた集約ロジック
  const exportModeCube = async (options: ExportOptions, targetRepIds: ID[]) => {
    const q = query;

    // ベース軸：画面のフィルタを尊重
    const baseUniverseFull = universeOf(baseAx, q);
    const baseUniverse =
      filterIds.length ? baseUniverseFull.filter(x => filterIds.includes(x.id)) : baseUniverseFull;

    // 残り2軸の全件（今回の方針では値選択なし）
    const bUniverse = universeOf(axB, q);
    const cUniverse = universeOf(axC, q);

    // 動的ヘッダ
    const headers = [
      '営業',
      axisLabel(baseAx),
      ...(options.addAxisB ? [axisLabel(axB)] : []),
      ...(options.addAxisC ? [axisLabel(axC)] : []),
      '売上', '数量（kg）', '台数（台）', '売単価'
    ];

    const fileStem = `csv_${axisLabel(baseAx)}${options.addAxisB ? `_${axisLabel(axB)}` : ''}${options.addAxisC ? `_${axisLabel(axC)}` : ''}_${periodLabel}`;

    const buildRowsFor = async (repId: ID) => {
      const repName = REPS.find(r => r.id === repId)?.name ?? repId;
      const rows: Array<Record<string, any>> = [];

      const pushRow = (baseName: string, bName?: string, cName?: string, amount = 0, qty = 0, count = 0) => {
        const unit = qty > 0 ? Math.round((amount / qty) * 100) / 100 : null;
        if (options.excludeZero && amount === 0 && qty === 0 && count === 0) return;

        const row: Record<string, any> = { 営業: repName, [axisLabel(baseAx)]: baseName };
        if (options.addAxisB) row[axisLabel(axB)] = bName ?? '';
        if (options.addAxisC) row[axisLabel(axC)] = cName ?? '';
        row['売上'] = amount;
        row['数量（kg）'] = qty;
        row['台数（台）'] = count;
        row['売単価'] = unit ?? '';
        rows.push(row);
      };

      // 集約ヘルパ（ダミー集計：実運用ではAPIに置換）
      const addMetric = (acc: { a: number; q: number; c: number }, w = 1) => {
        const m = makeMetric(w);
        acc.a += m.amount;
        acc.q += m.qty;
        acc.c += m.count;
      };

      for (const base of baseUniverse) {
        if (options.addAxisB && options.addAxisC) {
          // ベース × B × C（明細）
          for (const b of bUniverse) {
            for (const c of cUniverse) {
              const acc = { a: 0, q: 0, c: 0 };
              addMetric(acc, 1); // ※ここは本来は（repId, base.id, b.id, c.id, 期間）で集計
              pushRow(base.name, b.name, c.name, acc.a, acc.q, acc.c);
            }
          }
        } else if (options.addAxisB && !options.addAxisC) {
          // ベース × B（Cを合算）
          for (const b of bUniverse) {
            const acc = { a: 0, q: 0, c: 0 };
            for (const _c of cUniverse) addMetric(acc, 1);
            pushRow(base.name, b.name, undefined, acc.a, acc.q, acc.c);
          }
        } else if (!options.addAxisB && options.addAxisC) {
          // ベース × C（Bを合算）
          for (const c of cUniverse) {
            const acc = { a: 0, q: 0, c: 0 };
            for (const _b of bUniverse) addMetric(acc, 1);
            pushRow(base.name, undefined, c.name, acc.a, acc.q, acc.c);
          }
        } else {
          // ベースのみ（BとCを合算）
          const acc = { a: 0, q: 0, c: 0 };
          for (const _b of bUniverse) for (const _c of cUniverse) addMetric(acc, 1);
          pushRow(base.name, undefined, undefined, acc.a, acc.q, acc.c);
        }
      }

      return rows;
    };

    if (options.splitBy === 'rep') {
      for (const repId of targetRepIds) {
        const rows = await buildRowsFor(repId);
        if (rows.length) downloadBlob(toCsv(rows), `${fileStem}_${repId}.csv`);
      }
    } else {
      let all: Record<string, any>[] = [];
      for (const repId of targetRepIds) all = all.concat(await buildRowsFor(repId));
      if (all.length) downloadBlob(toCsv(all), `${fileStem}.csv`);
    }
  };

  // exportCustomerItem は今回の方針で不要のため削除

  // handleExport: modeCube のみ呼び出す
  const handleExport = async () => {
    if (repIds.length === 0) return;
    try {
      await exportModeCube(exportOptions, repIds);
      message?.success?.('CSVを出力しました。');
    } catch (e) {
      console.error(e);
      message?.error?.('CSV出力でエラーが発生しました。');
    }
  };

  // Table (parent)
  const parentCols: TableColumnsType<SummaryRow> = useMemo(() => ([
    { title: '営業', dataIndex: 'repName', key: 'repName', width: 160, fixed: 'left' },
    {
      title: `${mode === 'customer' ? '顧客' : mode === 'item' ? '品名' : '日付'} Top${topN === 'all' ? 'All' : topN}`,
      key: 'summary',
      render: (_, row) => {
        const totalAmount = row.topN.reduce((s, x) => s + x.amount, 0);
        const totalQty = row.topN.reduce((s, x) => s + x.qty, 0);
        const totalCount = row.topN.reduce((s, x) => s + x.count, 0);
        const unit = totalQty > 0 ? Math.round((totalAmount / totalQty) * 100) / 100 : null;
        return (
          <Space wrap size="small" className="summary-tags">
            <Tag color="#237804">合計 売上 {fmtCurrency(totalAmount)}</Tag>
            <Tag color="green">数量 {fmtNumber(totalQty)} kg</Tag>
            <Tag color="blue">台数 {fmtNumber(totalCount)} 台</Tag>
            <Tag color="gold">単価 {fmtUnitPrice(unit)}</Tag>
          </Space>
        );
      }
    }
  ]), [mode, topN]);

  /* ========== Expanded child (営業ごとのTopN) ========== */
  const renderChildTable = (row: SummaryRow) => {
    const data = row.topN;
    const maxAmount = Math.max(1, ...data.map(x => x.amount));
    const maxQty = Math.max(1, ...data.map(x => x.qty));
    const maxCount = Math.max(1, ...data.map(x => x.count));
    const unitCandidates = data.map(x => x.unit_price ?? 0);
    const maxUnit = Math.max(1, ...unitCandidates);
    const nameTitle = mode === 'customer' ? '顧客' : mode === 'item' ? '品名' : '日付';

    const childCols: TableColumnsType<MetricEntry> = [
      { title: nameTitle, dataIndex: 'name', key: 'name', width: 220, sorter: true },
      {
        title: '売上', dataIndex: 'amount', key: 'amount', align: 'right', width: 180, sorter: true,
        render: (v: number) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ minWidth: 80, textAlign: 'right' }}>{fmtCurrency(v)}</span>
            <div className="mini-bar-bg">
              <div className="mini-bar mini-bar-blue" style={{ width: `${Math.round((v / maxAmount) * 100)}%` }} />
            </div>
          </div>
        )
      },
      {
        title: '数量（kg）', dataIndex: 'qty', key: 'qty', align: 'right', width: 160, sorter: true,
        render: (v: number) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ minWidth: 64, textAlign: 'right' }}>{fmtNumber(v)}</span>
            <div className="mini-bar-bg">
              <div className="mini-bar mini-bar-green" style={{ width: `${Math.round((v / maxQty) * 100)}%` }} />
            </div>
          </div>
        )
      },
      {
        title: '台数（台）', dataIndex: 'count', key: 'count', align: 'right', width: 120, sorter: true,
        render: (v: number) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ minWidth: 48, textAlign: 'right' }}>{fmtNumber(v)} 台</span>
            <div className="mini-bar-bg">
              <div className="mini-bar mini-bar-blue" style={{ width: `${Math.round((v / maxCount) * 100)}%` }} />
            </div>
          </div>
        )
      },
      {
        title: (<Space><span>売単価</span><Tooltip title="単価＝Σ金額 / Σ数量（数量=0は未定義）"><InfoCircleOutlined /></Tooltip></Space>),
        dataIndex: 'unit_price', key: 'unit_price', align: 'right', width: 170, sorter: true,
        render: (v: number | null) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
            <span style={{ minWidth: 64, textAlign: 'right' }}>{fmtUnitPrice(v)}</span>
            <div className="mini-bar-bg">
              <div className="mini-bar mini-bar-gold" style={{ width: `${v ? Math.round((v / maxUnit) * 100) : 0}%` }} />
            </div>
          </div>
        )
      },
      {
        title: '操作', key: 'ops', fixed: 'right', width: 120,
        render: (_, rec) => (<Button size="small" icon={<SwapOutlined />} onClick={() => openPivot(rec)}>詳細</Button>)
      }
    ];

    const onChildChange: TableProps<MetricEntry>['onChange'] = (_p, _f, sorter) => {
      const s = Array.isArray(sorter) ? sorter[0] : sorter;
      if (s && 'field' in s && s.field) {
        const f = String(s.field);
        let key: SortKey = sortBy;
        if (f === 'name') key = (mode === 'date') ? 'date' : 'name';
        else if ((['amount','qty','count','unit_price'] as string[]).includes(f)) key = f as SortKey;
        const ord: SortOrder = s.order === 'ascend' ? 'asc' : 'desc';
        setSortBy(key); setOrder(ord);
      }
    };

    // グラフ用（TopN棒）
    const chartBarData = data.map(d => ({
      name: d.name, 売上: d.amount, 数量: d.qty, 台数: d.count, 売単価: d.unit_price ?? 0
    }));
    const repId = row.repId;
    const series = repSeriesCache[repId];
    const handleLoadSeries = async () => {
      if (repSeriesCache[repId]) return;
      const s = await fetchDailySeries(query.month ? { month: query.month, repId } : { monthRange: query.monthRange!, repId });
      setRepSeriesCache(prev => ({ ...prev, [repId]: s }));
    };

    return (
      <Card className="accent-card accent-secondary" size="small" style={{ marginTop: 8 }}>
        <Tabs
          tabBarExtraContent={
            <Space wrap>
              <SortBadge label="並び替え" keyName={sortBy} order={order} />
              <Tag>Top{topN === 'all' ? 'All' : topN}</Tag>
            </Space>
          }
          items={[
            {
              key: 'table', label: '表',
              children: (
                <Table<MetricEntry>
                  rowKey="id"
                  size="small"
                  columns={childCols}
                  dataSource={data}
                  pagination={false}
                  onChange={onChildChange}
                  scroll={{ x: 1200 }}
                  rowClassName={(_, idx) => (idx % 2 === 0 ? 'zebra-even' : 'zebra-odd')}
                />
              )
            },
            {
              key: 'chart', label: 'グラフ',
              children: (
                <Row gutter={[16, 16]}>
                  <Col xs={24} md={14}>
                    <div className="card-subtitle">TopN（売上・数量・台数・売単価）</div>
                    <div style={{ width: '100%', height: 320 }}>
                      <ResponsiveContainer>
                        <BarChart data={chartBarData} margin={{ top: 8, right: 8, left: 8, bottom: 24 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" hide={chartBarData.length > 12} />
                          <YAxis />
                          <RTooltip />
                          <Bar dataKey="売上" />
                          <Bar dataKey="数量" />
                          <Bar dataKey="台数" />
                          <Bar dataKey="売単価" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </Col>
                  <Col xs={24} md={10}>
                    <Space align="baseline" style={{ justifyContent: 'space-between', width: '100%' }}>
                      <div className="card-subtitle">
                        {query.month ? `${query.month} 日次推移` : `${query.monthRange!.from}〜${query.monthRange!.to} 日次推移`}（営業：{row.repName}）
                      </div>
                      {!series && (<Button size="small" onClick={handleLoadSeries} icon={<ReloadOutlined />}>日次を取得</Button>)}
                    </Space>
                    <div style={{ width: '100%', height: 320 }}>
                      <ResponsiveContainer>
                        <LineChart data={series ?? []} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" hide />
                          <YAxis />
                          <RTooltip
                            formatter={(v: number | string, name: string) =>
                              name === 'amount' ? fmtCurrency(Number(v))
                              : name === 'qty' ? `${fmtNumber(Number(v))} kg`
                              : name === 'count' ? `${fmtNumber(Number(v))} 台`
                              : fmtUnitPrice(Number(v))}
                            labelFormatter={(l) => l}
                          />
                          <Line type="monotone" dataKey="amount" name="売上" />
                          <Line type="monotone" dataKey="qty" name="数量" />
                          <Line type="monotone" dataKey="count" name="台数" />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </Col>
                </Row>
              )
            }
          ]}
        />
      </Card>
    );
  };

  /* ========== Drawer (Pivot) ========== */
  const openPivot = (rec: MetricEntry) => {
    const others = (['customer', 'item', 'date'] as Mode[]).filter(ax => ax !== mode);
    const targets = others.map(ax => ({ axis: ax, label: ax === 'customer' ? '顧客' : ax === 'item' ? '品名' : '日付' })) as { axis: Mode; label: string }[];

    const base = {
      open: true, baseAxis: mode, baseId: rec.id, baseName: rec.name,
      repIds, targets, activeAxis: targets[0].axis, sortBy, order, topN
    } as any;

    if (query.monthRange) setDrawer({ ...base, monthRange: query.monthRange });
    else setDrawer({ ...base, month: query.month });
    setPivotData({ customer: [], item: [], date: [] });
    setPivotCursor({ customer: null, item: null, date: null });
  };

  const loadPivot = useCallback(async (axis: Mode, reset = false) => {
    if (!drawer.open) return;
    const targetAxis = axis;
    if (targetAxis === drawer.baseAxis) return;
    setPivotLoading(true);
    try {
      const page = await fetchPivot({
        month: (drawer as any).month,
        monthRange: (drawer as any).monthRange,
        baseAxis: drawer.baseAxis, baseId: drawer.baseId, repIds: drawer.repIds,
        targetAxis: targetAxis as Mode, sortBy: drawer.sortBy, order: drawer.order, topN: drawer.topN,
        cursor: reset ? null : pivotCursor[targetAxis]
      });
      setPivotData(prev => ({ ...prev, [targetAxis]: reset ? page.rows : prev[targetAxis].concat(page.rows) }));
      setPivotCursor(prev => ({ ...prev, [targetAxis]: page.next_cursor }));
    } finally { setPivotLoading(false); }
  }, [drawer, pivotCursor]);

  const isDrawerOpen = (d: DrawerState): d is Extract<DrawerState, { open: true }> => d.open;
  useEffect(() => {
    if (!isDrawerOpen(drawer)) return;
    loadPivot(drawer.activeAxis, true);
  }, [drawer.open, isDrawerOpen(drawer) ? drawer.activeAxis : null, isDrawerOpen(drawer) ? drawer.sortBy : null, isDrawerOpen(drawer) ? drawer.order : null, isDrawerOpen(drawer) ? drawer.topN : null]);

  const onPivotTableChange: TableProps<MetricEntry>['onChange'] = (_p, _f, sorter) => {
    const s = Array.isArray(sorter) ? sorter[0] : sorter;
    if (s && 'field' in s && s.field && drawer.open) {
      const f = String(s.field);
      let nextKey: SortKey = drawer.sortBy;
      if (f === 'name') nextKey = (drawer.activeAxis === 'date') ? 'date' : 'name';
      else if ((['amount','qty','count','unit_price'] as string[]).includes(f)) nextKey = f as SortKey;
      const nextOrder: SortOrder = s.order === 'ascend' ? 'asc' : 'desc';
      setDrawer(prev => prev.open ? { ...prev, sortBy: nextKey, order: nextOrder } : prev);
    }
  };

  // Sort options
  const sortKeyOptions = useMemo(() => {
    return [
      { label: mode === 'date' ? '日付' : '名称', value: mode === 'date' ? 'date' : 'name' },
      { label: '売上', value: 'amount' },
      { label: '数量', value: 'qty' },
      { label: '台数', value: 'count' },
      { label: '売単価', value: 'unit_price' },
    ];
  }, [mode]);

  // Mode switch（残り軸の選択は廃止のためフィルタだけリセット）
  const switchMode = (m: Mode) => { setMode(m); setFilterIds([]); };

  /* =========================
   * Export Dropdown (UI)
   * ========================= */
  const exportMenu: MenuProps['items'] = [
    { key: 'title', label: <b>出力条件</b> },
    { type: 'divider' as const },

    // 追加カラム：残りモード1（実名）
    {
      key: 'addB',
      label: (
        <div onClick={e => e.stopPropagation()}>
          <Space>
            <Switch
              size="small"
              checked={exportOptions.addAxisB}
              onChange={(v) => setExportOptions(prev => ({ ...prev, addAxisB: v }))}
            />
            <span>追加カラム：{axisLabel(axB)}</span>
          </Space>
        </div>
      ),
    },

    // 追加カラム：残りモード2（実名）
    {
      key: 'addC',
      label: (
        <div onClick={e => e.stopPropagation()}>
          <Space>
            <Switch
              size="small"
              checked={exportOptions.addAxisC}
              onChange={(v) => setExportOptions(prev => ({ ...prev, addAxisC: v }))}
            />
            <span>追加カラム：{axisLabel(axC)}</span>
          </Space>
        </div>
      ),
    },

    { type: 'divider' as const },

    // 0実績除外（Excel負荷対策）
    {
      key: 'opt-zero',
      label: (
        <Space onClick={e => e.stopPropagation()}>
          <Switch
            size="small"
            checked={exportOptions.excludeZero}
            onChange={(checked) => setExportOptions(prev => ({ ...prev, excludeZero: checked }))}
          />
          <span>0実績を除外する（Excel負荷対策）</span>
        </Space>
      ),
    },

    // 分割出力（任意・既存そのまま継続）
    {
      key: 'opt-split',
      label: (
        <Space onClick={e => e.stopPropagation()}>
          <Select
            size="small"
            value={exportOptions.splitBy}
            onChange={(v: SplitBy) => setExportOptions(prev => ({ ...prev, splitBy: v }))}
            options={[
              { label: '分割しない', value: 'none' },
              { label: '営業ごとに分割', value: 'rep' },
            ]}
            style={{ width: 180 }}
          />
          <span>（Excel負荷対策）</span>
        </Space>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ display: 'block' }}>
      {/* スタイル */}
      <style>{`
        .app-header { position: relative; padding: 12px 0 4px; }
        .app-title { text-align: center; font-weight: 700; letter-spacing: 0.02em; margin: 0; }
        .app-title-accent { display: inline-flex; align-items: center; gap: 10px; padding-left: 8px; color: #000; font-weight: 700; line-height: 1.2; font-size: 1.05em; }
        .app-title-accent::before { content: ""; display: inline-block; width: 6px; height: 22px; background: #237804; border-radius: 3px; }
        .app-header-actions { position: absolute; right: 0; top: 8px; display: flex; gap: 8px; }
        .accent-card { border-left: 4px solid #23780410; overflow: hidden; }
        .accent-primary { border-left-color: #237804; }
        .accent-secondary { border-left-color: #52c41a; }
        .accent-gold { border-left-color: #faad14; }
        .card-section-header { font-weight: 600; padding: 6px 10px; margin-bottom: 12px; border-radius: 6px; background: #f3fff4; border: 1px solid #e6f7e6; }
        .card-subtitle { color: rgba(0,0,0,0.55); margin-bottom: 6px; font-size: 12px; }
        .mini-bar-bg { flex: 1; height: 6px; background: #f6f7fb; border-radius: 4px; overflow: hidden; }
        .mini-bar { height: 100%; }
        .mini-bar-blue { background: #237804; }
        .mini-bar-green { background: #52c41a; }
        .mini-bar-gold { background: #faad14; }
        .zebra-even { background: #ffffff; }
        .zebra-odd { background: #fbfcfe; }
        .ant-table-tbody > tr:hover > td { background: #f6fff4 !important; }
        .ant-table-header { box-shadow: inset 0 -1px 0 #f0f0f0; }
      `}</style>

      <style>{`
        .summary-tags { font-size: 14px; }
        .summary-tags .ant-tag { font-size: 14px; padding: 0 10px; }
      `}</style>

      {/* ヘッダ（CSV：Dropdown.Buttonでワンクリック＋実名選択） */}
      <div className="app-header">
        <Typography.Title level={3} className="app-title">
          <span className="app-title-accent">売上ツリー</span>
        </Typography.Title>
        <div className="app-header-actions">
          {repIds.length === 0 ? (
            <Tooltip title="営業が未選択のためCSV出力できません">
              <Button icon={<DownloadOutlined />} type="default" disabled>
                CSV出力
              </Button>
            </Tooltip>
          ) : (
            <Tooltip
              title={`出力：選択営業 × ${axisLabel(baseAx)}${exportOptions.addAxisB ? ` × ${axisLabel(axB)}` : ''}${exportOptions.addAxisC ? ` × ${axisLabel(axC)}` : ''}（期間：${
                periodMode === 'single'
                  ? month.format('YYYY-MM')
                  : `${(range?.[0] ?? dayjs()).format('YYYY-MM')}〜${(range?.[1] ?? dayjs()).format('YYYY-MM')}`
              }、0実績は${exportOptions.excludeZero ? '除外' : '含む'}、${exportOptions.splitBy === 'rep' ? '営業別分割' : '単一ファイル'}）`}
            >
              <Dropdown.Button
                type="default"
                icon={<DownloadOutlined />}
                overlayStyle={{ width: 380 }}
                menu={{ items: exportMenu }}
                onClick={handleExport}
                placement="bottomRight"
                trigger={['click']}
                buttonsRender={([left, right]) => [
                  left,
                  React.cloneElement(right as any, { icon: <DownOutlined /> })
                ]}
              >
                CSV出力
              </Dropdown.Button>
            </Tooltip>
          )}
        </div>
      </div>

      {/* フィルタ＆コントロール */}
      <Card className="accent-card accent-primary" title={<div className="card-section-header">条件</div>}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={10}>
            <Space direction="vertical" size={2} style={{ width: '100%' }}>
              <Typography.Text type="secondary">対象（単月 / 期間）</Typography.Text>
              <Space wrap>
                <Segmented
                  options={[{ label: '単月', value: 'single' }, { label: '期間', value: 'range' }]}
                  value={periodMode}
                  onChange={(v: string | number) => setPeriodMode(v as 'single' | 'range')}
                />
                {periodMode === 'single' ? (
                  <DatePicker picker="month" value={month} onChange={(d) => d && setMonth(d.startOf('month'))} allowClear={false} />
                ) : (
                  <DatePicker.RangePicker
                    picker="month"
                    value={range ?? [dayjs().startOf('month'), dayjs().startOf('month')]}
                    onChange={(vals) => {
                      if (vals && vals[0] && vals[1]) setRange([vals[0].startOf('month'), vals[1].startOf('month')]);
                    }}
                    allowEmpty={[false, false]}
                  />
                )}
              </Space>
            </Space>
          </Col>

          <Col xs={24} lg={14}>
            <Row gutter={[16, 16]}>
              <Col xs={24} md={8}>
                <Space direction="vertical" size={2}>
                  <Typography.Text type="secondary">モード</Typography.Text>
                  <Segmented options={[{ label: '顧客', value: 'customer' }, { label: '品名', value: 'item' }, { label: '日付', value: 'date' }]}
                    value={mode} onChange={(v) => switchMode(v as Mode)} />
                </Space>
              </Col>
              <Col xs={24} md={16}>
                <Space direction="vertical" size={2} style={{ width: '100%' }}>
                  <Typography.Text type="secondary">Top & 並び替え</Typography.Text>
                  <Space wrap>
                    <Segmented options={[{ label: '10', value: '10' }, { label: '20', value: '20' }, { label: '50', value: '50' }, { label: 'All', value: 'all' }]} value={String(topN)}
                      onChange={(v: string | number) => setTopN(v === 'all' ? 'all' : (Number(v) as 10 | 20 | 50))} />
                    <Segmented options={sortKeyOptions} value={sortBy} onChange={(v) => setSortBy(v as SortKey)} />
                    <Segmented options={[{ label: '降順', value: 'desc' }, { label: '昇順', value: 'asc' }]} value={order} onChange={(v) => setOrder(v as SortOrder)} />
                  </Space>
                </Space>
              </Col>
            </Row>
          </Col>
        </Row>

        <Divider style={{ margin: '16px 0' }} />

        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Space direction="vertical" size={2} style={{ width: '100%' }}>
              <Typography.Text type="secondary">営業</Typography.Text>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <Select mode="multiple" allowClear placeholder="（未選択）"
                  options={repOptions} value={repIds} onChange={setRepIds} style={{ flex: 1 }} />
                <Space>
                  <Button size="small" onClick={() => setRepIds(REPS.map(r => r.id))} disabled={repIds.length === REPS.length}>全営業を表示</Button>
                  <Button size="small" onClick={() => setRepIds([])} disabled={repIds.length === 0}>クリア</Button>
                </Space>
              </div>
            </Space>
          </Col>
          <Col xs={24} md={12}>
            <Space direction="vertical" size={2} style={{ width: '100%' }}>
              <Typography.Text type="secondary">{mode === 'customer' ? '顧客で絞る' : mode === 'item' ? '品名で絞る' : '日付で絞る'}</Typography.Text>
              <Select mode="multiple" allowClear placeholder={`（未選択＝全${mode === 'customer' ? '顧客' : mode === 'item' ? '品名' : '日付'}）`}
                options={filterOptions} value={filterIds} onChange={setFilterIds} style={{ width: '100%' }} />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* KPI（営業名をタイトルに反映） */}
      {repIds.length > 0 ? (
        <Card
          className="accent-card accent-gold"
          title={
            <div className="card-section-header">
              KPI（営業：
              <Tooltip
                title={
                  repIds.length
                    ? REPS.filter(r => repIds.includes(r.id)).map(r => r.name).join('・')
                    : '未選択'
                }
              >
                <span>{selectedRepLabel}</span>
              </Tooltip>
              ）
            </div>
          }
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} md={6}><Statistic title="（表示対象）合計 売上" value={headerTotals.amount} formatter={(v) => fmtCurrency(Number(v))} /></Col>
            <Col xs={24} md={6}><Statistic title="（表示対象）合計 数量" value={headerTotals.qty} formatter={(v) => `${fmtNumber(Number(v))} kg`} /></Col>
            <Col xs={24} md={6}><Statistic title="（表示対象）合計 台数" value={headerTotals.count} formatter={(v) => `${fmtNumber(Number(v))} 台`} /></Col>
            <Col xs={24} md={6}><Statistic title="（表示対象）加重平均 単価" valueRender={() => <span>{fmtUnitPrice(headerTotals.unit)}</span>} /></Col>
          </Row>
        </Card>
      ) : (
        <Card className="accent-card accent-gold">
          <div style={{ padding: 12 }}>
            <Typography.Text type="secondary">営業が未選択のため、KPIは表示されません。左上の「営業」から選択してください。</Typography.Text>
          </div>
        </Card>
      )}

      {/* メインテーブル */}
      {repIds.length > 0 ? (
        <Card className="accent-card accent-primary" title={<div className="card-section-header">一覧</div>}>
          <Table<SummaryRow>
            rowKey={(r) => r.repId}
            columns={parentCols}
            dataSource={summary}
            loading={loading}
            pagination={false}
            expandable={{ expandedRowRender: (record) => renderChildTable(record), rowExpandable: () => true }}
            scroll={{ x: 1220 }}
            rowClassName={(_, idx) => (idx % 2 === 0 ? 'zebra-even' : 'zebra-odd')}
          />
        </Card>
      ) : (
        <Card className="accent-card accent-primary">
          <div style={{ padding: 12 }}>
            <Typography.Text type="secondary">営業が未選択のため、一覧は表示されません。左上の「営業」から選択してください。</Typography.Text>
          </div>
        </Card>
      )}

      {/* Drawer: Pivot（CSVボタンなし） */}
      <Drawer
        title={
          drawer.open
            ? `詳細：${drawer.baseAxis === 'customer' ? '顧客' : drawer.baseAxis === 'item' ? '品名' : '日付'}「${drawer.baseName}」`
            : ''
        }
        open={drawer.open}
        onClose={() => setDrawer({ open: false })}
        width={1000}
      >
        {drawer.open ? (
          <Card className="accent-card accent-secondary" title={<div className="card-section-header">ピボット</div>}>
            <Row gutter={[16, 16]} align="middle" style={{ marginBottom: 8 }}>
              <Col flex="auto">
                <Space wrap>
                  <Tag color="#237804">ベース：{drawer.baseAxis === 'customer' ? '顧客' : drawer.baseAxis === 'item' ? '品名' : '日付'}</Tag>
                  <Tag>{drawer.baseName}</Tag>
                  <SortBadge label="並び替え" keyName={drawer.sortBy} order={drawer.order} />
                  <Tag>Top{drawer.topN === 'all' ? 'All' : drawer.topN}</Tag>
                </Space>
              </Col>
            </Row>

            <Tabs
              activeKey={drawer.activeAxis}
              onChange={(active) => setDrawer(prev => prev.open ? { ...prev, activeAxis: active as Mode } : prev)}
              tabBarExtraContent={
                <Space wrap>
                  <Segmented options={[{ label: '10', value: '10' }, { label: '20', value: '20' }, { label: '50', value: '50' }, { label: 'All', value: 'all' }]} value={String(drawer.open ? drawer.topN : 10)}
                    onChange={(v: string | number) => drawer.open && setDrawer(prev => prev.open ? { ...prev, topN: (v === 'all' ? 'all' : (Number(v) as 10 | 20 | 50)) } : prev)} />
                  <Segmented
                    options={[
                      { label: '売上', value: 'amount' },
                      { label: '数量', value: 'qty' },
                      { label: '台数', value: 'count' },
                      { label: '売単価', value: 'unit_price' },
                      { label: drawer.open && drawer.activeAxis === 'date' ? '日付' : '名称', value: drawer.open && drawer.activeAxis === 'date' ? 'date' : 'name' }
                    ]}
                    value={drawer.open ? drawer.sortBy : 'amount'}
                    onChange={(v) => drawer.open && setDrawer(prev => prev.open ? { ...prev, sortBy: v as SortKey } : prev)}
                  />
                  <Segmented options={[{ label: '降順', value: 'desc' }, { label: '昇順', value: 'asc' }]}
                    value={drawer.open ? drawer.order : 'desc'}
                    onChange={(v) => drawer.open && setDrawer(prev => prev.open ? { ...prev, order: v as SortOrder } : prev)} />
                </Space>
              }
              items={drawer.targets.map(t => {
                const rows = pivotData[t.axis];
                const maxA = Math.max(1, ...rows.map(x => x.amount));
                const maxQ = Math.max(1, ...rows.map(x => x.qty));
                const maxC = Math.max(1, ...rows.map(x => x.count));
                const maxU = Math.max(1, ...rows.map(x => x.unit_price ?? 0));

                const cols: TableColumnsType<MetricEntry> = [
                  { title: t.axis === 'customer' ? '顧客' : t.axis === 'item' ? '品名' : '日付',
                    dataIndex: 'name', key: 'name', width: 220, sorter: true },
                  { title: '売上', dataIndex: 'amount', key: 'amount', align: 'right', width: 170, sorter: true,
                    render: (v: number) => (
                      <div style={{ display:'flex', alignItems:'center', gap:8, justifyContent:'flex-end' }}>
                        <span style={{ minWidth: 72, textAlign:'right' }}>{fmtCurrency(v)}</span>
                        <div className="mini-bar-bg"><div className="mini-bar mini-bar-blue" style={{ width:`${Math.round((v / maxA) * 100)}%` }} /></div>
                      </div>
                    ) },
                  { title: '数量', dataIndex: 'qty', key: 'qty', align: 'right', width: 150, sorter: true,
                    render: (v: number) => (
                      <div style={{ display:'flex', alignItems:'center', gap:8, justifyContent:'flex-end' }}>
                        <span style={{ minWidth: 60, textAlign:'right' }}>{fmtNumber(v)}</span>
                        <div className="mini-bar-bg"><div className="mini-bar mini-bar-green" style={{ width:`${Math.round((v / maxQ) * 100)}%` }} /></div>
                      </div>
                    ) },
                  { title: '台数（台）', dataIndex: 'count', key: 'count', align: 'right', width: 120, sorter: true,
                    render: (v: number) => (
                      <div style={{ display:'flex', alignItems:'center', gap:8, justifyContent:'flex-end' }}>
                        <span style={{ minWidth: 48, textAlign:'right' }}>{fmtNumber(v)} 台</span>
                        <div className="mini-bar-bg"><div className="mini-bar mini-bar-blue" style={{ width:`${Math.round((v / maxC) * 100)}%` }} /></div>
                      </div>
                    ) },
                  { title: (<Space><span>売単価</span><Tooltip title="単価＝Σ金額 / Σ数量（数量=0は未定義）"><InfoCircleOutlined /></Tooltip></Space>),
                    dataIndex: 'unit_price', key: 'unit_price', align: 'right', width: 170, sorter: true,
                    render: (v: number | null) => (
                      <div style={{ display:'flex', alignItems:'center', gap:8, justifyContent:'flex-end' }}>
                        <span style={{ minWidth: 64, textAlign:'right' }}>{fmtUnitPrice(v)}</span>
                        <div className="mini-bar-bg"><div className="mini-bar mini-bar-gold" style={{ width:`${v ? Math.round((v / maxU) * 100) : 0}%` }} /></div>
                      </div>
                    ) },
                ];

                return {
                  key: t.axis,
                  label: t.label,
                  children: (
                    <>
                      <Table<MetricEntry>
                        rowKey="id"
                        size="small"
                        columns={cols}
                        dataSource={rows}
                        loading={pivotLoading}
                        pagination={false}
                        onChange={onPivotTableChange}
                        locale={{ emptyText: pivotLoading ? '読込中...' : <Empty description="該当なし" /> }}
                        scroll={{ x: 980 }}
                        rowClassName={(_, idx) => (idx % 2 === 0 ? 'zebra-even' : 'zebra-odd')}
                      />
                      <Space style={{ marginTop: 8 }}>
                        <Button icon={<ReloadOutlined />} onClick={() => loadPivot(t.axis, true)}>再読込</Button>
                        {drawer.topN === 'all' && pivotCursor[t.axis] && (
                          <Button type="primary" onClick={() => loadPivot(t.axis, false)} loading={pivotLoading}>さらに読み込む</Button>
                        )}
                        {drawer.topN === 'all' && !pivotCursor[t.axis] && (
                          <Typography.Text type="secondary">すべて読み込み済み</Typography.Text>
                        )}
                      </Space>
                    </>
                  )
                };
              })}
            />
          </Card>
        ) : null}
      </Drawer>
    </Space>
  );
};

export default SalesPivotBoardPlusWithCharts;
