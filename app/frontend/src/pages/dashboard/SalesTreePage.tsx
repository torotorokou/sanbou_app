// src/pages/SalesPivotBoardPlusWithCharts.tsx
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import type { FC } from 'react';
import {
  App, Badge, Button, Card, Col, DatePicker, Divider, Drawer, Empty, Row,
  Segmented, Select, Space, Statistic, Table, Tag, Tabs, Tooltip, Typography
} from 'antd';
import type { TableColumnsType, TableProps } from 'antd';
import {
  ArrowDownOutlined, ArrowUpOutlined, InfoCircleOutlined, SwapOutlined, ReloadOutlined
} from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, ResponsiveContainer, LineChart, Line
} from 'recharts';

/* =========================================================================
 * Sales Pivot Board Plus + Charts (v3)
 * 変更点：
 *  - 顧客/品名/日付列のヘッダクリックで並び替え（name / date）
 *  - 売単価にもセル内ミニバーを追加
 *  - 詳細ドロワー内の表でもミニバー表示＆ヘッダ並び替え
 * ========================================================================= */

type YYYYMM = string;
type YYYYMMDD = string;

type Mode = 'customer' | 'item' | 'date';
type SortKey = 'amount' | 'qty' | 'unit_price' | 'date' | 'name';
type SortOrder = 'asc' | 'desc';
type ID = string;

interface SalesRep { id: ID; name: string; }

interface MetricEntry {
  id: ID;
  name: string;        // 顧客名 | 品名 | 日付(YYYY-MM-DD)
  amount: number;
  qty: number;
  unit_price: number | null;
  dateKey?: YYYYMMDD;  // dateモードのソート用
}

interface SummaryRow { repId: ID; repName: string; topN: MetricEntry[]; }

interface SummaryQuery {
  month: YYYYMM; mode: Mode; repIds: ID[]; filterIds: ID[];
  sortBy: SortKey; order: SortOrder; topN: 10 | 20 | 50 | 'all';
}

type CursorPage<T> = { rows: T[]; next_cursor: string | null };

/* =========================
 * Mock Data / Repository
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

const delay = (ms = 180) => new Promise((r) => setTimeout(r, ms));
const rndInt = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min;

const makeMetric = (weight = 1): Pick<MetricEntry, 'amount' | 'qty' | 'unit_price'> => {
  const has = Math.random() < 0.83; // 17%は0実績
  const qty = has ? Math.max(0, Math.round((Math.random() * 140) * weight)) : 0;
  const price = has ? rndInt(120, 520) : 0;
  const amount = has ? Math.round(qty * price * (0.7 + Math.random() * 0.6)) : 0;
  const unit_price = qty > 0 ? Math.round((amount / qty) * 100) / 100 : null;
  return { amount, qty, unit_price };
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
 * APIs (mock)
 * ========================= */
async function fetchSummary(q: SummaryQuery): Promise<SummaryRow[]> {
  const reps = q.repIds.length ? REPS.filter(r => q.repIds.includes(r.id)) : REPS;
  const universe = q.mode === 'customer' ? CUSTOMERS : q.mode === 'item' ? ITEMS : monthDays(q.month);
  const filtered = q.filterIds.length ? (universe as any[]).filter(u => q.filterIds.includes(u.id)) : universe;

  const rows: SummaryRow[] = reps.map(rep => {
    const weight = 1 + (rep.id.charCodeAt(rep.id.length - 1) % 3) * 0.2;
    const pool: MetricEntry[] = (filtered as any[]).map((t: any) => {
      const m = makeMetric(weight);
      return { id: t.id, name: t.name, amount: m.amount, qty: m.qty, unit_price: m.unit_price, dateKey: t.dateKey };
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
  month: YYYYMM; baseAxis: Mode; baseId: ID; repIds: ID[];
  targetAxis: Mode; sortBy: SortKey; order: SortOrder; topN: 10 | 20 | 50 | 'all'; cursor?: string | null;
}): Promise<CursorPage<MetricEntry>> {
  const universe = params.targetAxis === 'customer' ? CUSTOMERS : params.targetAxis === 'item' ? ITEMS : monthDays(params.month);

  const rows: MetricEntry[] = (universe as any[]).map((t: any) => {
    const repWeight =
      (params.repIds.length ? params.repIds : REPS.map(r => r.id))
        .reduce((acc, id) => acc + (1 + (id.charCodeAt(id.length - 1) % 3) * 0.1), 0) / Math.max(1, (params.repIds.length || REPS.length));
    const baseWeight = 1 + (params.baseId.charCodeAt(params.baseId.length - 1) % 5) * 0.08;
    const m = makeMetric(0.9 * repWeight * baseWeight);
    return { id: t.id, name: t.name, amount: m.amount, qty: m.qty, unit_price: m.unit_price, dateKey: t.dateKey };
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
  month: YYYYMM; repId?: ID; customerId?: ID; itemId?: ID;
}): Promise<Array<{ date: YYYYMMDD; amount: number; qty: number; unit_price: number | null }>> {
  const days = monthDays(params.month);
  const series = days.map(d => {
    const m = makeMetric(1);
    return { date: d.name, amount: m.amount, qty: m.qty, unit_price: m.qty > 0 ? Math.round((m.amount / m.qty) * 100) / 100 : null };
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
  <Badge count={order === 'desc' ? <ArrowDownOutlined /> : <ArrowUpOutlined />} style={{ backgroundColor: '#1677ff' }}>
    <Tag style={{ marginRight: 8 }}>{label}: {keyName}</Tag>
  </Badge>
);

/* =========================
 * Component
 * ========================= */
const SalesPivotBoardPlusWithCharts: FC = () => {
  App.useApp?.(); // (optional)
  const [month, setMonth] = useState<Dayjs>(dayjs().startOf('month'));
  const [mode, setMode] = useState<Mode>('customer');
  const [topN, setTopN] = useState<10 | 20 | 50 | 'all'>(10);
  const [sortBy, setSortBy] = useState<SortKey>('amount');
  const [order, setOrder] = useState<SortOrder>('desc');
  const [repIds, setRepIds] = useState<ID[]>([]);
  const [filterIds, setFilterIds] = useState<ID[]>([]);

  const [summary, setSummary] = useState<SummaryRow[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  type DrawerState =
    | { open: false }
    | {
        open: true;
        baseAxis: Mode; baseId: ID; baseName: string;
        month: YYYYMM; repIds: ID[];
        targets: { axis: Mode; label: string }[]; activeAxis: Mode;
        sortBy: SortKey; order: SortOrder; topN: 10 | 20 | 50 | 'all';
      };
  const [drawer, setDrawer] = useState<DrawerState>({ open: false });

  const [pivotData, setPivotData] = useState<Record<Mode, MetricEntry[]>>({ customer: [], item: [], date: [] });
  const [pivotCursor, setPivotCursor] = useState<Record<Mode, string | null>>({ customer: null, item: null, date: null });
  const [pivotLoading, setPivotLoading] = useState<boolean>(false);

  const [repSeriesCache, setRepSeriesCache] = useState<Record<ID, Array<{ date: YYYYMMDD; amount: number; qty: number; unit_price: number | null }>>>({});

  const monthStr: YYYYMM = useMemo(() => month.format('YYYY-MM'), [month]);

  const query: SummaryQuery = useMemo(() => ({
    month: monthStr, mode, repIds, filterIds, sortBy, order, topN
  }), [monthStr, mode, repIds, filterIds, sortBy, order, topN]);

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

  const repOptions = useMemo(() => REPS.map(r => ({ label: r.name, value: r.id })), []);
  const filterOptions = useMemo(() => {
    if (mode === 'customer') return CUSTOMERS.map(c => ({ label: c.name, value: c.id }));
    if (mode === 'item') return ITEMS.map(i => ({ label: i.name, value: i.id }));
    return monthDays(monthStr).map(d => ({ label: d.name, value: d.id }));
  }, [mode, monthStr]);

  // Header totals
  const headerTotals = useMemo(() => {
    const flat = summary.flatMap(r => r.topN);
    const amount = flat.reduce((s, x) => s + x.amount, 0);
    const qty = flat.reduce((s, x) => s + x.qty, 0);
    const unit = qty > 0 ? Math.round((amount / qty) * 100) / 100 : null;
    return { amount, qty, unit };
  }, [summary]);

  const parentCols: TableColumnsType<SummaryRow> = useMemo(() => ([
    { title: '営業', dataIndex: 'repName', key: 'repName', width: 160, fixed: 'left' },
    {
      title: `${mode === 'customer' ? '顧客' : mode === 'item' ? '品名' : '日付'} Top${topN === 'all' ? 'All' : topN}`,
      key: 'summary',
      render: (_, row) => {
        const totalAmount = row.topN.reduce((s, x) => s + x.amount, 0);
        const totalQty = row.topN.reduce((s, x) => s + x.qty, 0);
        const unit = totalQty > 0 ? Math.round((totalAmount / totalQty) * 100) / 100 : null;
        return (
          <Space wrap size="small">
            <Tag color="processing">合計 売上 {fmtCurrency(totalAmount)}</Tag>
            <Tag>数量 {fmtNumber(totalQty)}</Tag>
            <Tag>単価 {fmtUnitPrice(unit)}</Tag>
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
    const unitCandidates = data.map(x => x.unit_price ?? 0);
    const maxUnit = Math.max(1, ...unitCandidates);

    const nameTitle = mode === 'customer' ? '顧客' : mode === 'item' ? '品名' : '日付';

    const childCols: TableColumnsType<MetricEntry> = [
      {
        title: nameTitle, dataIndex: 'name', key: 'name', width: 220,
        sorter: true, // ヘッダクリック対応（name or date）
      },
      {
        title: '売上', dataIndex: 'amount', key: 'amount', align: 'right', width: 180, sorter: true,
        render: (v: number) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ minWidth: 80, textAlign: 'right' }}>{fmtCurrency(v)}</span>
            <div style={{ flex: 1, height: 6, background: '#f0f2f5', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ width: `${Math.round((v / maxAmount) * 100)}%`, height: '100%', background: '#1677ff' }} />
            </div>
          </div>
        )
      },
      {
        title: '数量', dataIndex: 'qty', key: 'qty', align: 'right', width: 160, sorter: true,
        render: (v: number) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ minWidth: 64, textAlign: 'right' }}>{fmtNumber(v)}</span>
            <div style={{ flex: 1, height: 6, background: '#f0f2f5', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ width: `${Math.round((v / maxQty) * 100)}%`, height: '100%', background: '#52c41a' }} />
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
            <div style={{ width: 90, height: 6, background: '#f0f2f5', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ width: `${v ? Math.round((v / maxUnit) * 100) : 0}%`, height: '100%', background: '#faad14' }} />
            </div>
          </div>
        )
      },
      { title: '操作', key: 'ops', fixed: 'right', width: 110,
        render: (_, rec) => (<Button size="small" icon={<SwapOutlined />} onClick={() => openPivot(rec)}>詳細</Button>) }
    ];

    const onChildChange: TableProps<MetricEntry>['onChange'] = (_p, _f, sorter) => {
      const s = Array.isArray(sorter) ? sorter[0] : sorter;
      if (s && 'field' in s && s.field) {
        const f = String(s.field);
        let key: SortKey = sortBy;
        if (f === 'name') key = (mode === 'date') ? 'date' : 'name';
        else if ((['amount','qty','unit_price'] as string[]).includes(f)) key = f as SortKey;
        const ord: SortOrder = s.order === 'ascend' ? 'asc' : 'desc';
        setSortBy(key); setOrder(ord);
      }
    };

    // グラフ用
    const chartBarData = data.map(d => ({ name: d.name, 売上: d.amount, 数量: d.qty, 売単価: d.unit_price ?? 0 }));
    const repId = row.repId;
    const series = repSeriesCache[repId];
    const handleLoadSeries = async () => {
      if (repSeriesCache[repId]) return;
      const s = await fetchDailySeries({ month: monthStr, repId });
      setRepSeriesCache(prev => ({ ...prev, [repId]: s }));
    };

    return (
      <Card size="small" style={{ marginTop: 8 }}>
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
                  rowKey="id" size="small" columns={childCols} dataSource={data}
                  pagination={false} onChange={onChildChange} scroll={{ x: 980 }}
                />
              )
            },
            {
              key: 'chart', label: 'グラフ',
              children: (
                <Row gutter={[16, 16]}>
                  <Col xs={24} md={12}>
                    <Typography.Text type="secondary">TopN（売上・数量・売単価）</Typography.Text>
                    <div style={{ width: '100%', height: 280 }}>
                      <ResponsiveContainer>
                        <BarChart data={chartBarData} margin={{ top: 8, right: 8, left: 8, bottom: 24 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" hide={chartBarData.length > 12} />
                          <YAxis />
                          <RTooltip />
                          <Bar dataKey="売上" />
                          <Bar dataKey="数量" />
                          <Bar dataKey="売単価" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </Col>
                  <Col xs={24} md={12}>
                    <Space align="baseline" style={{ justifyContent: 'space-between', width: '100%' }}>
                      <Typography.Text type="secondary">当月日次推移（営業：{row.repName}）</Typography.Text>
                      {!series && (<Button size="small" onClick={handleLoadSeries} icon={<ReloadOutlined />}>日次を取得</Button>)}
                    </Space>
                    <div style={{ width: '100%', height: 280 }}>
                      <ResponsiveContainer>
                        <LineChart data={series ?? []} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" hide />
                          <YAxis />
                          <RTooltip formatter={(v: any, n: any) => n === 'amount' ? fmtCurrency(Number(v)) : fmtNumber(Number(v))} labelFormatter={(l) => l} />
                          <Line type="monotone" dataKey="amount" />
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
    setDrawer({
      open: true, baseAxis: mode, baseId: rec.id, baseName: rec.name, month: monthStr, repIds,
      targets, activeAxis: targets[0].axis, sortBy, order, topN
    });
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
        month: drawer.month, baseAxis: drawer.baseAxis, baseId: drawer.baseId, repIds: drawer.repIds,
        targetAxis: targetAxis as Mode, sortBy: drawer.sortBy, order: drawer.order, topN: drawer.topN,
        cursor: reset ? null : pivotCursor[targetAxis]
      });
      setPivotData(prev => ({ ...prev, [targetAxis]: reset ? page.rows : prev[targetAxis].concat(page.rows) }));
      setPivotCursor(prev => ({ ...prev, [targetAxis]: page.next_cursor }));
    } finally { setPivotLoading(false); }
  }, [drawer, pivotCursor]);

  useEffect(() => {
    if (!drawer.open) return;
    loadPivot(drawer.activeAxis, true);
  }, [drawer.open, drawer.activeAxis, drawer.sortBy, drawer.order, drawer.topN]); // eslint-disable-line

  // Drawer テーブルの列ヘッダソート → ドロワー状態に反映
  const onPivotTableChange: TableProps<MetricEntry>['onChange'] = (_p, _f, sorter) => {
    const s = Array.isArray(sorter) ? sorter[0] : sorter;
    if (s && 'field' in s && s.field) {
      const f = String(s.field);
      let nextKey: SortKey = drawer.sortBy;
      if (f === 'name') nextKey = (drawer.activeAxis === 'date') ? 'date' : 'name';
      else if ((['amount','qty','unit_price'] as string[]).includes(f)) nextKey = f as SortKey;
      const nextOrder: SortOrder = s.order === 'ascend' ? 'asc' : 'desc';
      setDrawer(prev => prev.open ? { ...prev, sortBy: nextKey, order: nextOrder } : prev);
    }
  };

  // 上部コントロール
  const sortKeyOptions = useMemo(() => {
    const base = [
      { label: '売上', value: 'amount' },
      { label: '数量', value: 'qty' },
      { label: '売単価', value: 'unit_price' },
    ];
    // 顧客・品名のときは「名称」、日付モードでは「日付」
    base.push({ label: mode === 'date' ? '日付' : '名称', value: mode === 'date' ? 'date' : 'name' });
    return base;
  }, [mode]);

  const drawerTabBarExtra = (
    <Space wrap>
      <Segmented
        options={[10, 20, 50, { label: 'All', value: 'all' }]}
        value={drawer.open ? drawer.topN : 10}
        onChange={(v) => drawer.open && onDrawerTopNChange(v as any)}
      />
      <Segmented
        options={[
          { label: '売上', value: 'amount' },
          { label: '数量', value: 'qty' },
          { label: '売単価', value: 'unit_price' },
          { label: drawer.open && drawer.activeAxis === 'date' ? '日付' : '名称', value: drawer.open && drawer.activeAxis === 'date' ? 'date' : 'name' }
        ]}
        value={drawer.open ? drawer.sortBy : 'amount'}
        onChange={(v) => drawer.open && onDrawerSortKeyChange(v as SortKey)}
      />
      <Segmented
        options={[{ label: '降順', value: 'desc' }, { label: '昇順', value: 'asc' }]}
        value={drawer.open ? drawer.order : 'desc'}
        onChange={(v) => drawer.open && onDrawerOrderChange(v as SortOrder)}
      />
    </Space>
  );

  // Drawer controls handlers
  const onDrawerTopNChange = (v: 10 | 20 | 50 | 'all') => {
    if (!drawer.open) return;
    setDrawer({ ...drawer, topN: v });
    setPivotData({ customer: [], item: [], date: [] });
    setPivotCursor({ customer: null, item: null, date: null });
  };
  const onDrawerSortKeyChange = (v: SortKey) => {
    if (!drawer.open) return;
    setDrawer({ ...drawer, sortBy: v });
    setPivotData({ customer: [], item: [], date: [] });
    setPivotCursor({ customer: null, item: null, date: null });
  };
  const onDrawerOrderChange = (v: SortOrder) => {
    if (!drawer.open) return;
    setDrawer({ ...drawer, order: v });
    setPivotData({ customer: [], item: [], date: [] });
    setPivotCursor({ customer: null, item: null, date: null });
  };

  const switchMode = (m: Mode) => { setMode(m); setFilterIds([]); };

  return (
    <Space direction="vertical" size="large" style={{ display: 'block' }}>
      <Typography.Title level={3} style={{ marginBottom: 0 }}>
        売上ツリー（顧客 / 品名 / 日付）
        <Typography.Text type="secondary" style={{ marginLeft: 8, fontSize: 14 }}>Sales Pivot Board Plus + Charts</Typography.Text>
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        月を選び、<b>顧客</b> / <b>品名</b> / <b>日付</b> モードで「営業ごとのTopN」を確認。行を展開して「表｜グラフ」を切替、［詳細］でベース以外の2軸にピボットできます。
        単価は <b>Σ金額 / Σ数量</b>（数量=0は「—」）。TopNは 10 / 20 / 50 / All（Allはページング）。
      </Typography.Paragraph>

      <Card>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={8}>
            <Space direction="vertical" size={2}>
              <Typography.Text type="secondary">対象月</Typography.Text>
              <DatePicker picker="month" value={month} onChange={(d) => d && setMonth(d.startOf('month'))} allowClear={false} />
            </Space>
          </Col>

          <Col xs={24} lg={16}>
            <Row gutter={[16, 16]}>
              <Col xs={24} md={8}>
                <Space direction="vertical" size={2}>
                  <Typography.Text type="secondary">モード</Typography.Text>
                  <Segmented options={[{ label: '顧客', value: 'customer' }, { label: '品名', value: 'item' }, { label: '日付', value: 'date' }]}
                    value={mode} onChange={(v) => switchMode(v as Mode)} />
                </Space>
              </Col>

              {/* TopN / Sort をwrapで横並び。狭幅時は自動改行 */}
              <Col xs={24} md={16}>
                <Space direction="vertical" size={2} style={{ width: '100%' }}>
                  <Typography.Text type="secondary">Top & 並び替え</Typography.Text>
                  <Space wrap>
                    <Segmented options={[10, 20, 50, { label: 'All', value: 'all' }]} value={topN} onChange={(v) => setTopN(v as any)} />
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
              <Select mode="multiple" allowClear placeholder="（未選択＝全営業）"
                options={repOptions} value={repIds} onChange={setRepIds} style={{ width: '100%' }} />
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

        <Divider />

        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}><Statistic title="（表示対象）合計 売上" value={headerTotals.amount} formatter={(v) => fmtCurrency(Number(v))} /></Col>
          <Col xs={24} md={8}><Statistic title="（表示対象）合計 数量" value={headerTotals.qty} formatter={(v) => fmtNumber(Number(v))} /></Col>
          <Col xs={24} md={8}><Statistic title="（表示対象）加重平均 単価" valueRender={() => <span>{fmtUnitPrice(headerTotals.unit)}</span>} /></Col>
        </Row>

        <Table<SummaryRow>
          rowKey={(r) => r.repId} columns={parentCols} dataSource={summary}
          loading={loading} pagination={false}
          expandable={{ expandedRowRender: (record) => renderChildTable(record), rowExpandable: () => true }}
          scroll={{ x: 1000 }} style={{ marginTop: 16 }}
        />
      </Card>

      {/* Drawer: Pivot */}
      <Drawer
        title={drawer.open ? `詳細：${drawer.baseAxis === 'customer' ? '顧客' : drawer.baseAxis === 'item' ? '品名' : '日付'}「${drawer.baseName}」` : ''}
        open={drawer.open} onClose={() => setDrawer({ open: false })} width={980}
      >
        {drawer.open ? (
          <Card>
            <Row gutter={[16, 16]} align="middle">
              <Col flex="auto">
                <Space wrap>
                  <Tag color="blue">ベース：{drawer.baseAxis === 'customer' ? '顧客' : drawer.baseAxis === 'item' ? '品名' : '日付'}</Tag>
                  <Tag>{drawer.baseName}</Tag>
                </Space>
              </Col>
              <Col>
                <Space wrap>
                  <SortBadge label="並び替え" keyName={drawer.sortBy} order={drawer.order} />
                  <Tag>Top{drawer.topN === 'all' ? 'All' : drawer.topN}</Tag>
                </Space>
              </Col>
            </Row>

            <Divider />

            {/* Tabs の右側に操作を集約：被り解消 */}
            <Tabs
              activeKey={drawer.activeAxis}
              onChange={(active) => setDrawer(prev => prev.open ? { ...prev, activeAxis: active as Mode } : prev)}
              tabBarExtraContent={drawerTabBarExtra}
              items={drawer.targets.map(t => {
                const rows = pivotData[t.axis];
                const maxA = Math.max(1, ...rows.map(x => x.amount));
                const maxQ = Math.max(1, ...rows.map(x => x.qty));
                const maxU = Math.max(1, ...rows.map(x => x.unit_price ?? 0));

                // 各タブ（axis）ごとに列を生成：ミニバー＆ヘッダソート
                const cols: TableColumnsType<MetricEntry> = [
                  { title: t.axis === 'customer' ? '顧客' : t.axis === 'item' ? '品名' : '日付',
                    dataIndex: 'name', key: 'name', width: 220, sorter: true },
                  { title: '売上', dataIndex: 'amount', key: 'amount', align: 'right', width: 170, sorter: true,
                    render: (v: number) => (
                      <div style={{ display:'flex', alignItems:'center', gap:8, justifyContent:'flex-end' }}>
                        <span style={{ minWidth: 72, textAlign:'right' }}>{fmtCurrency(v)}</span>
                        <div style={{ width:90, height:6, background:'#f0f2f5', borderRadius:4, overflow:'hidden' }}>
                          <div style={{ width:`${Math.round((v / maxA) * 100)}%`, height:'100%', background:'#1677ff' }} />
                        </div>
                      </div>
                    ) },
                  { title: '数量', dataIndex: 'qty', key: 'qty', align: 'right', width: 150, sorter: true,
                    render: (v: number) => (
                      <div style={{ display:'flex', alignItems:'center', gap:8, justifyContent:'flex-end' }}>
                        <span style={{ minWidth: 60, textAlign:'right' }}>{fmtNumber(v)}</span>
                        <div style={{ width:90, height:6, background:'#f0f2f5', borderRadius:4, overflow:'hidden' }}>
                          <div style={{ width:`${Math.round((v / maxQ) * 100)}%`, height:'100%', background:'#52c41a' }} />
                        </div>
                      </div>
                    ) },
                  { title: (<Space><span>売単価</span><Tooltip title="単価＝Σ金額 / Σ数量（数量=0は未定義）"><InfoCircleOutlined /></Tooltip></Space>),
                    dataIndex: 'unit_price', key: 'unit_price', align: 'right', width: 170, sorter: true,
                    render: (v: number | null) => (
                      <div style={{ display:'flex', alignItems:'center', gap:8, justifyContent:'flex-end' }}>
                        <span style={{ minWidth: 64, textAlign:'right' }}>{fmtUnitPrice(v)}</span>
                        <div style={{ width:90, height:6, background:'#f0f2f5', borderRadius:4, overflow:'hidden' }}>
                          <div style={{ width:`${v ? Math.round((v / maxU) * 100) : 0}%`, height:'100%', background:'#faad14' }} />
                        </div>
                      </div>
                    ) },
                ];

                return {
                  key: t.axis,
                  label: t.label,
                  children: (
                    <>
                      <Table<MetricEntry>
                        rowKey="id" size="small" columns={cols} dataSource={rows}
                        loading={pivotLoading} pagination={false} onChange={onPivotTableChange}
                        locale={{ emptyText: pivotLoading ? '読込中...' : <Empty description="該当なし" /> }}
                        scroll={{ x: 900 }}
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
