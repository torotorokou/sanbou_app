// src/pages/SalesPivotBoardPlus.tsx
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

/* =========================================================================
 * Sales Pivot Board Plus（顧客 / 品名 / 日付 ＋ 相互ピボット ＋ TopN=All/ページング）
 * - モード：customer | item | date
 * - 親＝営業行、子＝選択モードのTopN（売上・数量・売単価）
 * - 詳細ドロワー：ベース以外の2軸にピボット（TopN 10/20/50/All、並び替え可、Allはカーソルページング）
 * - 単価＝Σ金額 / Σ数量（数量=0は null → 表示は "—"）
 * - すべてモックAPI内で擬似集計・並び替え・TopN・カーソルを実装
 * ========================================================================= */

/* =========================
 * Domain Types
 * ========================= */
type YYYYMM = string;
type YYYYMMDD = string;

type Mode = 'customer' | 'item' | 'date';
type SortKey = 'amount' | 'qty' | 'unit_price';
type SortOrder = 'asc' | 'desc';
type ID = string;

interface SalesRep { id: ID; name: string; }

interface MetricEntry {
  id: ID;           // customerId | itemId | dateId
  name: string;     // 顧客名 | 品名 | 日付(YYYY-MM-DD)
  amount: number;
  qty: number;
  unit_price: number | null;
}

interface SummaryRow {
  repId: ID;
  repName: string;
  topN: MetricEntry[];
}

interface SummaryQuery {
  month: YYYYMM;
  mode: Mode;
  repIds: ID[];   // 未指定=全営業
  filterIds: ID[]; // customerIds | itemIds | dateIds（任意）
  sortBy: SortKey;
  order: SortOrder;
  topN: 10 | 20 | 50 | 'all';
  cursor?: string | null; // 親表では使わない（子=TopNのみ）
}

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

const sortMetrics = (arr: MetricEntry[], sortBy: SortKey, order: SortOrder) => {
  const dir = order === 'asc' ? 1 : -1;
  arr.sort((a, b) => {
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

const monthDays = (m: YYYYMM) => {
  const start = dayjs(m + '-01');
  const days = start.daysInMonth();
  const list: { id: ID; name: string }[] = [];
  for (let d = 1; d <= days; d++) {
    const s = start.date(d).format('YYYY-MM-DD');
    list.push({ id: `d_${s}`, name: s });
  }
  return list;
};

/** Summary（営業ごとのTopN、モード=顧客/品名/日付） */
async function fetchSummary(q: SummaryQuery): Promise<SummaryRow[]> {
  const reps = q.repIds.length ? REPS.filter(r => q.repIds.includes(r.id)) : REPS;
  const universe =
    q.mode === 'customer' ? CUSTOMERS :
    q.mode === 'item' ? ITEMS :
    monthDays(q.month);

  const filtered = q.filterIds.length ? universe.filter(u => q.filterIds.includes(u.id)) : universe;

  const rows: SummaryRow[] = reps.map(rep => {
    const weight = 1 + (rep.id.charCodeAt(rep.id.length - 1) % 3) * 0.2;
    const pool: MetricEntry[] = filtered.map(t => {
      const m = makeMetric(weight);
      return { id: t.id, name: t.name, amount: m.amount, qty: m.qty, unit_price: m.unit_price };
    });
    sortMetrics(pool, q.sortBy, q.order);
    const top = q.topN === 'all' ? pool : pool.slice(0, q.topN);
    return { repId: rep.id, repName: rep.name, topN: top };
  });

  await delay();
  return rows;
}

/** 相互ピボット 詳細（base→target） with TopN=All cursor paging */
type CursorPage<T> = { rows: T[]; next_cursor: string | null };

function paginateWithCursor<T>(sorted: T[], cursor: string | null | undefined, pageSize: number): CursorPage<T> {
  const start = cursor ? Number(cursor) : 0;
  const end = Math.min(start + pageSize, sorted.length);
  return {
    rows: sorted.slice(start, end),
    next_cursor: end < sorted.length ? String(end) : null
  };
}

async function fetchPivot(params: {
  month: YYYYMM;
  baseAxis: Mode;            // 'customer' | 'item' | 'date'
  baseId: ID;                // 顧客ID or 品目ID or 日付ID
  repIds: ID[];
  targetAxis: Exclude<Mode, typeof params['baseAxis']>; // 残りの2軸のいずれか
  sortBy: SortKey;
  order: SortOrder;
  topN: 10 | 20 | 50 | 'all';
  cursor?: string | null;
}): Promise<CursorPage<MetricEntry>> {
  // ターゲット宇宙
  const universe =
    params.targetAxis === 'customer' ? CUSTOMERS :
    params.targetAxis === 'item' ? ITEMS :
    monthDays(params.month);

  // 疑似集計（base×target×rep のΣ）
  const rows: MetricEntry[] = universe.map(t => {
    // baseとrepにより重みを少し変える（擬似的な癖）
    const repWeight =
      (params.repIds.length ? params.repIds : REPS.map(r => r.id))
        .reduce((acc, id) => acc + (1 + (id.charCodeAt(id.length - 1) % 3) * 0.1), 0) / Math.max(1, (params.repIds.length || REPS.length));

    const baseWeight =
      1 + (params.baseId.charCodeAt(params.baseId.length - 1) % 5) * 0.08;

    const m = makeMetric(0.9 * repWeight * baseWeight);
    return { id: t.id, name: t.name, amount: m.amount, qty: m.qty, unit_price: m.unit_price };
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

/* =========================
 * Formatters / Small UI
 * ========================= */
const fmtCurrency = (n: number) => `¥${n.toLocaleString('ja-JP')}`;
const fmtNumber = (n: number) => n.toLocaleString('ja-JP');
const fmtUnitPrice = (v: number | null) =>
  v == null ? '—' : `¥${v.toLocaleString('ja-JP', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;

const SortBadge: FC<{ label: string; keyName: SortKey; order: SortOrder }> = ({ label, keyName, order }) => (
  <Badge count={order === 'desc' ? <ArrowDownOutlined /> : <ArrowUpOutlined />} style={{ backgroundColor: '#1677ff' }}>
    <Tag style={{ marginRight: 8 }}>{label}: {keyName}</Tag>
  </Badge>
);

/* =========================
 * Component
 * ========================= */
const SalesPivotBoardPlus: FC = () => {
  const { message } = App.useApp?.() ?? { message: { info: console.log } as any };

  // Controls
  const [month, setMonth] = useState<Dayjs>(dayjs().startOf('month'));
  const [mode, setMode] = useState<Mode>('customer');
  const [topN, setTopN] = useState<10 | 20 | 50 | 'all'>(10);
  const [sortBy, setSortBy] = useState<SortKey>('amount');
  const [order, setOrder] = useState<SortOrder>('desc');
  const [repIds, setRepIds] = useState<ID[]>([]);
  const [filterIds, setFilterIds] = useState<ID[]>([]); // モードに応じた事前絞込

  // Data
  const [summary, setSummary] = useState<SummaryRow[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // Drawer (pivot)
  type DrawerState =
    | { open: false }
    | {
        open: true;
        baseAxis: Mode;
        baseId: ID;
        baseName: string;
        month: YYYYMM;
        repIds: ID[];
        // 2つのターゲット軸に切替
        targets: { axis: Mode; label: string }[]; // 2つ
        activeAxis: Mode; // 今表示しているターゲット軸
        sortBy: SortKey;
        order: SortOrder;
        topN: 10 | 20 | 50 | 'all';
      };

  const [drawer, setDrawer] = useState<DrawerState>({ open: false });

  // Drawer data per axis
  const [pivotData, setPivotData] = useState<Record<Mode, MetricEntry[]>>({ customer: [], item: [], date: [] });
  const [pivotCursor, setPivotCursor] = useState<Record<Mode, string | null>>({ customer: null, item: null, date: null });
  const [pivotLoading, setPivotLoading] = useState<boolean>(false);

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

  // Parent columns
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

  // Child columns (row.expand)
  const childCols: TableColumnsType<MetricEntry> = useMemo(() => ([
    { title: mode === 'customer' ? '顧客' : mode === 'item' ? '品名' : '日付', dataIndex: 'name', key: 'name', width: 220 },
    { title: '売上', dataIndex: 'amount', key: 'amount', align: 'right', width: 140, render: (v: number) => fmtCurrency(v), sorter: true },
    { title: '数量', dataIndex: 'qty', key: 'qty', align: 'right', width: 120, render: (v: number) => fmtNumber(v), sorter: true },
    {
      title: (
        <Space>
          <span>売単価</span>
          <Tooltip title="単価＝Σ金額 / Σ数量（数量=0は未定義）"><InfoCircleOutlined /></Tooltip>
        </Space>
      ),
      dataIndex: 'unit_price', key: 'unit_price', align: 'right', width: 120, render: (v: number | null) => fmtUnitPrice(v), sorter: true
    },
    {
      title: '操作', key: 'ops', fixed: 'right', width: 110,
      render: (_, rec) => (
        <Button size="small" icon={<SwapOutlined />} onClick={() => openPivot(rec)}>
          詳細
        </Button>
      )
    }
  ]), [mode]);

  const onChildChange: TableProps<MetricEntry>['onChange'] = (_p, _f, sorter) => {
    const sArr = Array.isArray(sorter) ? sorter : [sorter];
    const s = sArr[0];
    if (s && 'field' in s && s.field) {
      const f = String(s.field);
      const key: SortKey = (['amount', 'qty', 'unit_price'] as SortKey[]).includes(f as any) ? (f as SortKey) : 'amount';
      const ord: SortOrder = s.order === 'ascend' ? 'asc' : 'desc';
      setSortBy(key);
      setOrder(ord);
    }
  };

  const renderChildTable = (row: SummaryRow) => (
    <Card size="small" style={{ marginTop: 8 }}>
      <Space style={{ marginBottom: 8 }} wrap>
        <SortBadge label={mode === 'customer' ? '顧客' : mode === 'item' ? '品名' : '日付'} keyName={sortBy} order={order} />
        <Tag>Top{topN === 'all' ? 'All' : topN}（{row.repName}）</Tag>
      </Space>
      <Table<MetricEntry>
        rowKey="id"
        size="small"
        columns={childCols}
        dataSource={row.topN}
        pagination={false}
        onChange={onChildChange}
        scroll={{ x: 720 }}
      />
    </Card>
  );

  // Open Drawer (Pivot)
  const openPivot = (rec: MetricEntry) => {
    // ベース＝現在のモード、ターゲット＝残り2軸
    const candidates: Mode[] = ['customer', 'item', 'date'];
    const others = candidates.filter(ax => ax !== mode);
    const targets = others.map(ax => ({ axis: ax, label: ax === 'customer' ? '顧客' : ax === 'item' ? '品名' : '日付' })) as { axis: Mode; label: string }[];

    setDrawer({
      open: true,
      baseAxis: mode,
      baseId: rec.id,
      baseName: rec.name,
      month: monthStr,
      repIds,
      targets,
      activeAxis: targets[0].axis,
      sortBy,
      order,
      topN
    });
    // 初期ロード
    setPivotData({ customer: [], item: [], date: [] });
    setPivotCursor({ customer: null, item: null, date: null });
  };

  // Drawer data loader
  const loadPivot = useCallback(async (axis: Mode, reset = false) => {
    if (!drawer.open) return;
    const targetAxis = axis;
    if (targetAxis === drawer.baseAxis) return; // 同軸にはピボットしない

    setPivotLoading(true);
    try {
      const page = await fetchPivot({
        month: drawer.month,
        baseAxis: drawer.baseAxis,
        baseId: drawer.baseId,
        repIds: drawer.repIds,
        targetAxis: targetAxis as any,
        sortBy: drawer.sortBy,
        order: drawer.order,
        topN: drawer.topN,
        cursor: reset ? null : pivotCursor[targetAxis]
      });
      setPivotData(prev => ({ ...prev, [targetAxis]: reset ? page.rows : prev[targetAxis].concat(page.rows) }));
      setPivotCursor(prev => ({ ...prev, [targetAxis]: page.next_cursor }));
    } finally {
      setPivotLoading(false);
    }
  }, [drawer, pivotCursor]);

  useEffect(() => {
    if (!drawer.open) return;
    // アクティブ軸の初回ロード（または設定変更時リロードは別で）
    loadPivot(drawer.activeAxis, true);
  }, [drawer.open, drawer.activeAxis, drawer.sortBy, drawer.order, drawer.topN]); // eslint-disable-line

  const pivotCols = useMemo<TableColumnsType<MetricEntry>>(() => ([
    { title: drawer.open && drawer.activeAxis === 'customer' ? '顧客' : drawer.open && drawer.activeAxis === 'item' ? '品名' : '日付',
      dataIndex: 'name', key: 'name', width: 220 },
    { title: '売上', dataIndex: 'amount', key: 'amount', align: 'right', width: 140, render: (v: number) => fmtCurrency(v) },
    { title: '数量', dataIndex: 'qty', key: 'qty', align: 'right', width: 120, render: (v: number) => fmtNumber(v) },
    {
      title: (<Space><span>売単価</span><Tooltip title="単価＝Σ金額 / Σ数量（数量=0は未定義）"><InfoCircleOutlined /></Tooltip></Space>),
      dataIndex: 'unit_price', key: 'unit_price', align: 'right', width: 120, render: (v: number | null) => fmtUnitPrice(v),
    },
  ]), [drawer.open, drawer.activeAxis]);

  // Drawer controls handlers
  const onDrawerTopNChange = (v: 10 | 20 | 50 | 'all') => {
    if (!drawer.open) return;
    setDrawer({ ...drawer, topN: v });
    // reset load
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

  // Switch global mode resets mode-specific filters
  const switchMode = (m: Mode) => {
    setMode(m);
    setFilterIds([]);
  };

  return (
    <Space direction="vertical" size="large" style={{ display: 'block' }}>
      <Typography.Title level={3} style={{ marginBottom: 0 }}>
        売上ツリー（顧客 / 品名 / 日付）
        <Typography.Text type="secondary" style={{ marginLeft: 8, fontSize: 14 }}>
          Sales Pivot Board Plus
        </Typography.Text>
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        月を選び、<b>顧客</b> / <b>品名</b> / <b>日付</b> モードで「営業ごとのTopN」を確認。［詳細］でベース以外の2軸にピボットできます。
        単価は <b>Σ金額 / Σ数量</b>（数量=0は「—」）。TopNは 10 / 20 / 50 / All を選択可（Allはページング）。
      </Typography.Paragraph>

      <Card>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={8}>
            <Space direction="vertical" size={2}>
              <Typography.Text type="secondary">対象月</Typography.Text>
              <DatePicker picker="month" value={month} onChange={(d) => d && setMonth(d.startOf('month'))} allowClear={false} />
            </Space>
          </Col>

          <Col xs={24} md={16}>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={8}>
                <Space direction="vertical" size={2}>
                  <Typography.Text type="secondary">モード</Typography.Text>
                  <Segmented
                    options={[
                      { label: '顧客', value: 'customer' },
                      { label: '品名', value: 'item' },
                      { label: '日付', value: 'date' },
                    ]}
                    value={mode}
                    onChange={(v) => switchMode(v as Mode)}
                  />
                </Space>
              </Col>
              <Col xs={12} sm={6} md={4}>
                <Space direction="vertical" size={2}>
                  <Typography.Text type="secondary">TopN</Typography.Text>
                  <Segmented
                    options={[10, 20, 50, { label: 'All', value: 'all' }]}
                    value={topN}
                    onChange={(v) => setTopN(v as any)}
                  />
                </Space>
              </Col>
              <Col xs={12} sm={12} md={12}>
                <Row gutter={[16, 16]}>
                  <Col xs={12}>
                    <Space direction="vertical" size={2}>
                      <Typography.Text type="secondary">並び替え</Typography.Text>
                      <Segmented
                        options={[
                          { label: '売上', value: 'amount' },
                          { label: '数量', value: 'qty' },
                          { label: '売単価', value: 'unit_price' },
                        ]}
                        value={sortBy}
                        onChange={(v) => setSortBy(v as SortKey)}
                      />
                    </Space>
                  </Col>
                  <Col xs={12}>
                    <Space direction="vertical" size={2}>
                      <Typography.Text type="secondary">降順/昇順</Typography.Text>
                      <Segmented
                        options={[{ label: '降順', value: 'desc' }, { label: '昇順', value: 'asc' }]}
                        value={order}
                        onChange={(v) => setOrder(v as SortOrder)}
                      />
                    </Space>
                  </Col>
                </Row>
              </Col>
            </Row>
          </Col>
        </Row>

        <Divider style={{ margin: '16px 0' }} />

        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Space direction="vertical" size={2} style={{ width: '100%' }}>
              <Typography.Text type="secondary">営業</Typography.Text>
              <Select
                mode="multiple"
                allowClear
                placeholder="（未選択＝全営業）"
                options={repOptions}
                value={repIds}
                  onChange={setRepIds}
                  style={{ width: '100%' }}
              />
            </Space>
          </Col>
          <Col xs={24} md={12}>
            <Space direction="vertical" size={2} style={{ width: '100%' }}>
              <Typography.Text type="secondary">
                {mode === 'customer' ? '顧客で絞る' : mode === 'item' ? '品名で絞る' : '日付で絞る'}
              </Typography.Text>
              <Select
                mode="multiple"
                allowClear
                placeholder={`（未選択＝全${mode === 'customer' ? '顧客' : mode === 'item' ? '品名' : '日付'}）`}
                options={filterOptions}
                value={filterIds}
                    onChange={setFilterIds}
                    style={{ width: '80%' }}
              />
            </Space>
          </Col>
        </Row>

        <Divider />

        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Statistic title="（表示対象）合計 売上" value={headerTotals.amount} formatter={(v) => fmtCurrency(Number(v))} />
          </Col>
          <Col xs={24} md={8}>
            <Statistic title="（表示対象）合計 数量" value={headerTotals.qty} formatter={(v) => fmtNumber(Number(v))} />
          </Col>
          <Col xs={24} md={8}>
            <Statistic title="（表示対象）加重平均 単価" valueRender={() => <span>{fmtUnitPrice(headerTotals.unit)}</span>} />
          </Col>
        </Row>

        <Table<SummaryRow>
          rowKey={(r) => r.repId}
          columns={parentCols}
          dataSource={summary}
          loading={loading}
          pagination={false}
          expandable={{
            expandedRowRender: (record) => renderChildTable(record),
            rowExpandable: () => true
          }}
          scroll={{ x: 900 }}
          style={{ marginTop: 16 }}
        />
      </Card>

      {/* Drawer: Pivot */}
      <Drawer
        title={
          drawer.open
            ? `詳細：${drawer.baseAxis === 'customer' ? '顧客' : drawer.baseAxis === 'item' ? '品名' : '日付'}「${drawer.baseName}」`
            : ''
        }
        open={drawer.open}
        onClose={() => setDrawer({ open: false })}
        width={880}
      >
        {drawer.open ? (
          <Card>
            <Row gutter={[16, 16]}>
              <Col xs={24} md={14}>
                <Space wrap>
                  <Tag color="blue">
                    ベース：{drawer.baseAxis === 'customer' ? '顧客' : drawer.baseAxis === 'item' ? '品名' : '日付'}
                  </Tag>
                  <Tag>{drawer.baseName}</Tag>
                  <SortBadge label="並び替え" keyName={drawer.sortBy} order={drawer.order} />
                  <Tag>Top{drawer.topN === 'all' ? 'All' : drawer.topN}</Tag>
                </Space>
              </Col>
              <Col xs={24} md={10}>
                <Row gutter={[8, 8]}>
                  <Col span={8}>
                    <Segmented
                      options={[10, 20, 50, { label: 'All', value: 'all' }]}
                      value={drawer.topN}
                      onChange={(v) => onDrawerTopNChange(v as any)}
                    />
                  </Col>
                  <Col span={8}>
                    <Segmented
                      options={[
                        { label: '売上', value: 'amount' },
                        { label: '数量', value: 'qty' },
                        { label: '売単価', value: 'unit_price' },
                      ]}
                      value={drawer.sortBy}
                      onChange={(v) => onDrawerSortKeyChange(v as SortKey)}
                    />
                  </Col>
                  <Col span={8}>
                    <Segmented
                      options={[{ label: '降順', value: 'desc' }, { label: '昇順', value: 'asc' }]}
                      value={drawer.order}
                      onChange={(v) => onDrawerOrderChange(v as SortOrder)}
                    />
                  </Col>
                </Row>
              </Col>
            </Row>

            <Divider />

            {/* Pivot target tabs (2 axes) */}
            <Tabs
              activeKey={drawer.activeAxis}
              onChange={(active) => setDrawer(prev => prev.open ? { ...prev, activeAxis: active as Mode } : prev)}
              items={drawer.targets.map(t => ({
                key: t.axis,
                label: t.label,
                children: (
                  <React.Fragment>
                    <Table<MetricEntry>
                      rowKey="id"
                      size="small"
                      columns={pivotCols}
                      dataSource={pivotData[t.axis]}
                      loading={pivotLoading}
                      pagination={false}
                      locale={{ emptyText: pivotLoading ? '読込中...' : <Empty description="該当なし" /> }}
                      scroll={{ x: 720 }}
                    />
                    <Space style={{ marginTop: 8 }}>
                      <Button
                        icon={<ReloadOutlined />}
                        onClick={() => loadPivot(t.axis, true)}
                      >
                        再読込
                      </Button>
                      {drawer.topN === 'all' && pivotCursor[t.axis] && (
                        <Button
                          type="primary"
                          onClick={() => loadPivot(t.axis, false)}
                          loading={pivotLoading}
                        >
                          さらに読み込む
                        </Button>
                      )}
                      {drawer.topN === 'all' && !pivotCursor[t.axis] && (
                        <Typography.Text type="secondary">すべて読み込み済み</Typography.Text>
                      )}
                    </Space>
                  </React.Fragment>
                )
              }))}
            />
          </Card>
        ) : null}
      </Drawer>
    </Space>
  );
};

export default SalesPivotBoardPlus;
