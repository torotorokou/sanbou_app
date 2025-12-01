import React, { useEffect, useMemo, useState } from 'react';
import dayjs, { type Dayjs } from 'dayjs';
import {
  App,
  Typography,
  Row,
  Col,
  Card,
  Space,
  Button,
  Segmented,
  Tag,
  Badge,
  Table,
  Input,
  Select,
  Tabs,
  Alert,
  Empty,
} from 'antd';
import { notifyInfo, notifySuccess } from '@features/notification';
import type { ColumnsType } from 'antd/es/table';

const { Title, Text } = Typography;

/* ========== Types ========== */
type GroupKey = 'shogun_flash' | 'shogun_final' | 'manifest';
type KindKey =
  | 'flash_ship' | 'flash_receive' | 'flash_yard'
  | 'final_ship' | 'final_receive' | 'final_yard'
  | 'mani_primary' | 'mani_secondary';
type Status = 'ok' | 'warn' | 'error';

type RecordRow = {
  id: string;
  date: string;
  group: GroupKey;
  kind: KindKey;
  slip_no?: string;
  customer?: string;
  weight_kg?: number;
  amount_yen?: number;
  source: 'CSV' | '手打ち' | '自動';
  uploader?: string;
  imported_at?: string;
  status: Status;
  filename?: string;
};

/* ========== Constants ========== */
const GROUP_LABEL: Record<GroupKey, string> = {
  shogun_flash: '将軍_速報版',
  shogun_final: '将軍_最終版',
  manifest: 'マニフェスト',
};

const KIND_LABEL: Record<KindKey, string> = {
  flash_ship: '（速報）出荷',
  flash_receive: '（速報）受入',
  flash_yard: '（速報）ヤード',
  final_ship: '（最終）出荷',
  final_receive: '（最終）受入',
  final_yard: '（最終）ヤード',
  mani_primary: '1次マニ',
  mani_secondary: '2次マニ',
};

const GROUP_COLOR: Record<GroupKey, string> = {
  shogun_flash: 'geekblue',
  shogun_final: 'green',
  manifest: 'purple',
};

const STATUS_TAG: Record<Status, { color: string; label: string }> = {
  ok: { color: 'default', label: 'OK' },
  warn: { color: 'gold', label: '警告' },
  error: { color: 'red', label: 'エラー' },
};

/* ========== LocalStorage Helper ========== */
const LS_KEY = 'record_manager_demo_rows_v1';

const loadRows = (): RecordRow[] => {
  try {
    const s = localStorage.getItem(LS_KEY);
    return s ? JSON.parse(s) : [];
  } catch {
    return [];
  }
};

const saveRows = (rows: RecordRow[]) => {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(rows));
  } catch { /* ignore */ }
};

/* ========== Sample Data Generator ========== */
const seedRandom = (seed: number) => {
  let x = Math.sin(seed) * 10000;
  return () => {
    x = Math.sin(x + seed) * 10000;
    return x - Math.floor(x);
  };
};

const generateSampleMonth = (month: Dayjs): RecordRow[] => {
  const start = month.startOf('month');
  const end = month.endOf('month');
  const rand = seedRandom(parseInt(month.format('YYYYMM'), 10));
  const rows: RecordRow[] = [];

  for (let d = start; d.isBefore(end) || d.isSame(end, 'day'); d = d.add(1, 'day')) {
    const isWeekend = [0, 6].includes(d.day());
    const base = isWeekend ? 0.2 : 0.75;

    const appearFlash = rand() < base ? 1 : 0;
    const appearFinal = rand() < base * 0.6 ? 1 : 0;
    const appearMani = rand() < base * 0.35 ? 1 : 0;

    const push = (group: GroupKey, kind: KindKey) => {
      const id = `${group}-${kind}-${d.format('YYYYMMDD')}-${Math.floor(rand() * 100000)}`;
      const weight = Math.floor(rand() * 12000) + 500;
      const amount = Math.floor(weight * (50 + rand() * 30));
      const cust = ['A社', 'B社', 'C社', 'D社', 'E社'][Math.floor(rand() * 5)];
      const status: Status = rand() < 0.08 ? 'error' : rand() < 0.15 ? 'warn' : 'ok';

      rows.push({
        id,
        date: d.format('YYYY-MM-DD'),
        group,
        kind,
        slip_no: group === 'manifest' ? undefined : `SL-${Math.floor(rand() * 900000 + 100000)}`,
        customer: cust,
        weight_kg: weight,
        amount_yen: amount,
        source: 'CSV',
        uploader: ['佐藤', '鈴木', '田中', '伊藤'][Math.floor(rand() * 4)],
        imported_at: d.add(rand() * 10, 'hour').toISOString(),
        status,
        filename: `${group}_${kind}_${d.format('YYYYMMDD')}.csv`,
      });
    };

    if (appearFlash) {
      if (rand() < 0.9) push('shogun_flash', 'flash_receive');
      if (rand() < 0.6) push('shogun_flash', 'flash_ship');
      if (rand() < 0.4) push('shogun_flash', 'flash_yard');
    }
    if (appearFinal) {
      if (rand() < 0.9) push('shogun_final', 'final_receive');
      if (rand() < 0.6) push('shogun_final', 'final_ship');
      if (rand() < 0.4) push('shogun_final', 'final_yard');
    }
    if (appearMani) {
      if (rand() < 0.7) push('manifest', 'mani_primary');
      if (rand() < 0.4) push('manifest', 'mani_secondary');
    }
  }
  return rows;
};

/* ========== Calendar Cell Component ========== */
type DayCellProps = {
  date: Dayjs;
  month: Dayjs;
  counts: { total: number; byGroup: Partial<Record<GroupKey, number>>; hasError: boolean };
  onClick: (d: Dayjs) => void;
  selected: boolean;
  business: boolean;
};

const DayCell: React.FC<DayCellProps> = ({ date, month, counts, onClick, selected, business }) => {
  const inMonth = date.month() === month.month();
  const bg = !inMonth ? '#fafafa' : selected ? '#e6f4ff' : business ? '#fff' : '#f6ffed';
  const border = selected ? '1px solid #1677ff' : '1px solid #f0f0f0';
  const color = !inMonth ? '#bfbfbf' : 'inherit';

  return (
    <div
      onClick={() => onClick(date)}
      style={{
        cursor: 'pointer',
        padding: 8,
        height: 84,
        background: bg,
        border,
        borderRadius: 8,
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontWeight: 600, color }}>{date.date()}</span>
        {counts.total > 0 ? <Badge count={counts.total} size="small" /> : <span />}
      </div>

      <div style={{ display: 'flex', gap: 6 }}>
        {(['shogun_flash', 'shogun_final', 'manifest'] as GroupKey[]).map((g) => {
          const n = counts.byGroup[g] || 0;
          if (!n) return null;
          const colorMap: Record<GroupKey, string> = {
            shogun_flash: '#2f54eb',
            shogun_final: '#389e0d',
            manifest: '#722ed1',
          };
          return (
            <div
              key={g}
              title={`${GROUP_LABEL[g]}: ${n}件`}
              style={{ width: 10, height: 10, borderRadius: 10, background: colorMap[g] }}
            />
          );
        })}
        {counts.hasError && <Tag color="red" style={{ marginLeft: 'auto' }}>!</Tag>}
      </div>
    </div>
  );
};

/* ========== Main Component ========== */
const RecordManagerPage: React.FC = () => {
  const { modal } = App.useApp();

  const [month, setMonth] = useState(dayjs().startOf('month'));
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());
  const [groupFilter, setGroupFilter] = useState<GroupKey | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<Status | 'all'>('all');
  const [q, setQ] = useState('');

  const [rows, setRows] = useState<RecordRow[]>(() => {
    const existing = loadRows();
    if (existing.length > 0) return existing;
    const demo = generateSampleMonth(dayjs());
    saveRows(demo);
    return demo;
  });

  useEffect(() => {
    const ym = month.format('YYYY-MM');
    const has = rows.some((r) => r.date.startsWith(ym));
    if (!has) {
      const add = generateSampleMonth(month);
      setRows((prev) => {
        const next = [...prev, ...add];
        saveRows(next);
        return next;
      });
    }
  }, [month, rows]);

  const calendarCounts = useMemo(() => {
    const map: Record<
      string,
      { total: number; byGroup: Partial<Record<GroupKey, number>>; hasError: boolean }
    > = {};
    const ym = month.format('YYYY-MM');
    rows.forEach((r) => {
      if (!r.date.startsWith(ym)) return;
      const k = r.date;
      if (!map[k]) map[k] = { total: 0, byGroup: {}, hasError: false };
      map[k].total += 1;
      map[k].byGroup[r.group] = (map[k].byGroup[r.group] || 0) + 1;
      if (r.status === 'error') map[k].hasError = true;
    });
    return map;
  }, [rows, month]);

  const filteredRows = useMemo(() => {
    const target = selectedDate.format('YYYY-MM-DD');
    let list = rows.filter((r) => r.date === target);
    if (groupFilter !== 'all') list = list.filter((r) => r.group === groupFilter);
    if (statusFilter !== 'all') list = list.filter((r) => r.status === statusFilter);
    if (q.trim()) {
      const s = q.toLowerCase();
      list = list.filter(
        (r) =>
          (r.slip_no || '').toLowerCase().includes(s) ||
          (r.customer || '').toLowerCase().includes(s) ||
          (r.filename || '').toLowerCase().includes(s)
      );
    }
    const order: Record<Status, number> = { error: 0, warn: 1, ok: 2 };
    list.sort((a, b) => order[a.status] - order[b.status]);
    return list;
  }, [rows, selectedDate, groupFilter, statusFilter, q]);

  const [selectedRow, setSelectedRow] = useState<RecordRow | null>(null);

  useEffect(() => {
    setSelectedRow(null);
  }, [selectedDate.format('YYYY-MM-DD')]);

  const bulkDeleteDay = () => {
    const target = selectedDate.format('YYYY-MM-DD');
    const condition = (r: RecordRow) =>
      r.date === target && (groupFilter === 'all' || r.group === groupFilter);
    const count = rows.filter(condition).length;
    if (count === 0) {
      notifyInfo('情報', '削除対象がありません');
      return;
    }

    modal.confirm({
      title: '日全削除の確認',
      content: (
        <div>
          <p>対象日：{target}</p>
          <p>対象グループ：{groupFilter === 'all' ? 'すべて' : GROUP_LABEL[groupFilter]}</p>
          <p>削除件数：{count} 件</p>
          <Alert type="warning" showIcon message="この操作は取り消せません" />
        </div>
      ),
      okText: '削除する',
      okButtonProps: { danger: true },
      cancelText: 'キャンセル',
      onOk: () => {
        const next = rows.filter((r) => !condition(r));
        setRows(next);
        saveRows(next);
        setSelectedRow(null);
        notifySuccess('削除完了', `削除しました（${count}件）`);
      },
    });
  };

  const deleteRow = (row: RecordRow) => {
    modal.confirm({
      title: '行の削除',
      content: <Text>伝票/識別: {row.slip_no || row.id} を削除します。よろしいですか?</Text>,
      okText: '削除',
      okButtonProps: { danger: true },
      cancelText: 'キャンセル',
      onOk: () => {
        const next = rows.filter((r) => r.id !== row.id);
        setRows(next);
        saveRows(next);
        setSelectedRow(null);
        notifySuccess('削除完了', '削除しました');
      },
    });
  };

  const revalidate = () => {
    const targetIds = new Set(filteredRows.map((r) => r.id));
    const next = rows.map((r) => {
      if (!targetIds.has(r.id)) return r;
      return { ...r, status: (r.status === 'error' ? 'warn' : 'ok') as Status };
    });
    setRows(next);
    saveRows(next);
    notifySuccess('再検証完了', '再検証を実行しました');
  };

  const exportCsv = () => {
    const header = [
      'date',
      'group',
      'kind',
      'slip_no',
      'customer',
      'weight_kg',
      'amount_yen',
      'status',
      'source',
      'filename',
      'imported_at',
    ] as const;
    const lines = [
      header.join(','),
      ...filteredRows.map((r) => header.map((h) => String(r[h] ?? '')).join(',')),
    ];
    const blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `records_${selectedDate.format('YYYYMMDD')}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const daysGrid = useMemo(() => {
    const first = month.startOf('month').startOf('week');
    const cells: Dayjs[] = [];
    for (let i = 0; i < 42; i++) cells.push(first.add(i, 'day'));
    return cells;
  }, [month]);

  const isBusinessDay = (d: Dayjs) => ![0, 6].includes(d.day());

  const columns: ColumnsType<RecordRow> = [
    {
      title: '種別',
      dataIndex: 'group',
      width: 130,
      render: (v: GroupKey) => <Tag color={GROUP_COLOR[v]}>{GROUP_LABEL[v]}</Tag>,
    },
    { title: '区分', dataIndex: 'kind', width: 110, render: (v: KindKey) => KIND_LABEL[v] },
    { title: '伝票No', dataIndex: 'slip_no', width: 130, ellipsis: true },
    { title: '顧客', dataIndex: 'customer', width: 120, ellipsis: true },
    {
      title: '重量(kg)',
      dataIndex: 'weight_kg',
      width: 110,
      render: (v?: number) => v?.toLocaleString(),
    },
    {
      title: '金額(円)',
      dataIndex: 'amount_yen',
      width: 120,
      render: (v?: number) => v?.toLocaleString(),
    },
    {
      title: 'ステータス',
      dataIndex: 'status',
      width: 100,
      render: (s: Status) => <Tag color={STATUS_TAG[s].color}>{STATUS_TAG[s].label}</Tag>,
    },
    { title: 'ソース', dataIndex: 'source', width: 80 },
    { title: 'ファイル', dataIndex: 'filename', width: 200, ellipsis: true },
    {
      title: '取込時刻',
      dataIndex: 'imported_at',
      width: 170,
      render: (v?: string) => (v ? dayjs(v).format('MM/DD HH:mm') : '-'),
    },
    {
      title: '操作',
      key: 'op',
      fixed: 'right',
      width: 100,
      render: (_: unknown, r: RecordRow) => (
        <Button size="small" danger onClick={() => deleteRow(r)}>
          削除
        </Button>
      ),
    },
  ];

  const RightPanel = () => {
    if (!selectedRow) {
      const dayCount = filteredRows.length;
      const byGroup: Record<GroupKey, number> = {
        shogun_flash: 0,
        shogun_final: 0,
        manifest: 0,
      };
      filteredRows.forEach((r) => {
        byGroup[r.group] = (byGroup[r.group] || 0) + 1;
      });
      const errs = filteredRows.filter((r) => r.status === 'error').length;
      const warns = filteredRows.filter((r) => r.status === 'warn').length;

      return (
        <Card title="日サマリー">
          <Space direction="vertical">
            <Text>
              日付：<b>{selectedDate.format('YYYY-MM-DD')}</b>
            </Text>
            <Space wrap>
              <Tag color="blue">合計 {dayCount} 件</Tag>
              <Tag color={GROUP_COLOR.shogun_flash}>速報 {byGroup.shogun_flash || 0}</Tag>
              <Tag color={GROUP_COLOR.shogun_final}>最終 {byGroup.shogun_final || 0}</Tag>
              <Tag color={GROUP_COLOR.manifest}>マニ {byGroup.manifest || 0}</Tag>
              <Tag color="red">エラー {errs}</Tag>
              <Tag color="gold">警告 {warns}</Tag>
            </Space>
            <Alert type="info" showIcon message="行を選択すると詳細がここに表示されます。" />
          </Space>
        </Card>
      );
    }

    return (
      <Card
        title={
          <Space>
            <Text strong>詳細</Text>
            <Tag color={GROUP_COLOR[selectedRow.group]}>{GROUP_LABEL[selectedRow.group]}</Tag>
            <Text>{KIND_LABEL[selectedRow.kind]}</Text>
          </Space>
        }
        extra={
          <Button danger onClick={() => deleteRow(selectedRow)}>
            この行を削除
          </Button>
        }
      >
        <Tabs
          defaultActiveKey="preview"
          items={[
            {
              key: 'preview',
              label: 'プレビュー',
              children: (
                <Space direction="vertical">
                  <Text type="secondary">元CSV（サンプル表示）</Text>
                  <Card size="small" style={{ maxHeight: 220, overflow: 'auto' }}>
                    <pre
                      style={{
                        margin: 0,
                        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
                      }}
                    >
                      {`date,slip_no,customer,weight_kg,amount_yen
${selectedRow.date},${selectedRow.slip_no || '-'},${selectedRow.customer || '-'},${selectedRow.weight_kg || 0},${selectedRow.amount_yen || 0}
...（ここにCSVの先頭数行を表示する想定）`}
                    </pre>
                  </Card>
                </Space>
              ),
            },
            {
              key: 'consistency',
              label: '整合性',
              children: (
                <Space direction="vertical">
                  <Alert
                    type={
                      selectedRow.status === 'error'
                        ? 'error'
                        : selectedRow.status === 'warn'
                        ? 'warning'
                        : 'success'
                    }
                    showIcon
                    message={
                      selectedRow.status === 'ok'
                        ? '整合性チェックOK'
                        : selectedRow.status === 'warn'
                        ? '一部に警告があります'
                        : 'エラーが検出されました'
                    }
                    description="実運用では、速報↔最終の差分、予約表との突合、型/必須列の検証結果などを可視化します。"
                  />
                  <Text type="secondary">・ここに突合結果の詳細を並べます。</Text>
                </Space>
              ),
            },
            {
              key: 'history',
              label: '履歴',
              children: <Empty description="編集履歴（デモでは未実装）" />,
            },
            {
              key: 'source',
              label: 'ソース情報',
              children: (
                <Space direction="vertical">
                  <Text>ファイル名：{selectedRow.filename || '-'}</Text>
                  <Text>
                    取込時刻：
                    {selectedRow.imported_at
                      ? dayjs(selectedRow.imported_at).format('YYYY/MM/DD HH:mm:ss')
                      : '-'}
                  </Text>
                  <Text>アップローダ：{selectedRow.uploader || '-'}</Text>
                  <Text>ソース：{selectedRow.source}</Text>
                </Space>
              ),
            },
          ]}
        />
      </Card>
    );
  };

  return (
    <div style={{ height: 'calc(100dvh - (var(--page-padding, 0px) * 2))', minHeight: 680 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 12,
        }}
      >
        <Space>
          <Button onClick={() => setMonth((m) => m.subtract(1, 'month'))}>◀ 前月</Button>
          <Button
            onClick={() => {
              setMonth(dayjs().startOf('month'));
              setSelectedDate(dayjs());
            }}
          >
            今月
          </Button>
          <Button onClick={() => setMonth((m) => m.add(1, 'month'))}>次月 ▶</Button>
        </Space>
        <Title level={4} style={{ margin: 0 }}>
          {month.format('YYYY年 M月')}
        </Title>
        <Space>
          <Segmented<GroupKey | 'all'>
            options={[
              { label: 'すべて', value: 'all' },
              { label: '将軍_速報', value: 'shogun_flash' },
              { label: '将軍_最終', value: 'shogun_final' },
              { label: 'マニフェスト', value: 'manifest' },
            ]}
            value={groupFilter}
            onChange={(v) => setGroupFilter(v)}
          />
        </Space>
      </div>

      <Row gutter={16} style={{ height: 'calc(100% - 60px)' }}>
        <Col span={8} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Card size="small" title="月間カレンダー（クリックで絞込み）" style={{ flex: 1 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 8 }}>
              {['日', '月', '火', '水', '木', '金', '土'].map((d) => (
                <div
                  key={d}
                  style={{
                    textAlign: 'center',
                    fontWeight: 600,
                    color: '#8c8c8c',
                    marginBottom: 4,
                  }}
                >
                  {d}
                </div>
              ))}
              {daysGrid.map((d) => {
                const k = d.format('YYYY-MM-DD');
                const counts = calendarCounts[k] || { total: 0, byGroup: {}, hasError: false };
                return (
                  <DayCell
                    key={k}
                    date={d}
                    month={month}
                    counts={counts}
                    onClick={(dd) => setSelectedDate(dd)}
                    selected={selectedDate.isSame(d, 'day')}
                    business={isBusinessDay(d)}
                  />
                );
              })}
            </div>
          </Card>
        </Col>

        <Col span={9} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Card
            size="small"
            title={
              <Space>
                <Text strong>{selectedDate.format('YYYY-MM-DD')}</Text>
                <Tag color="blue">件数 {filteredRows.length}</Tag>
              </Space>
            }
            extra={
              <Space>
                <Input
                  placeholder="伝票No/顧客/ファイル名 検索"
                  allowClear
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  style={{ width: 240 }}
                />
                <Select<Status | 'all'>
                  value={statusFilter}
                  onChange={(v) => setStatusFilter(v)}
                  options={[
                    { value: 'all', label: '全ステータス' },
                    { value: 'ok', label: 'OK' },
                    { value: 'warn', label: '警告' },
                    { value: 'error', label: 'エラー' },
                  ]}
                  style={{ width: 130 }}
                />
                <Button onClick={revalidate}>再検証</Button>
                <Button onClick={exportCsv}>CSV出力</Button>
                <Button danger onClick={bulkDeleteDay}>
                  日全削除
                </Button>
              </Space>
            }
            style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
            styles={{ body: { padding: 0, flex: 1, overflow: 'hidden' } }}
          >
            <div style={{ padding: 12, height: '100%', overflow: 'auto' }}>
              <Table<RecordRow>
                size="small"
                columns={columns}
                dataSource={filteredRows}
                rowKey="id"
                pagination={{ pageSize: 10, size: 'small' }}
                scroll={{ x: 900 }}
                onRow={(r) => ({ onClick: () => setSelectedRow(r) })}
              />
            </div>
          </Card>
        </Col>

        <Col span={7} style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 16 }}>
          <RightPanel />
          <Card size="small" title="ヒント">
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              <li>左のカレンダーで日付を選ぶと中央の一覧が絞り込まれます。</li>
              <li>行をクリックすると右ペインに詳細が出ます。</li>
              <li>「日全削除」は現在のグループフィルタにだけ作用します。</li>
            </ul>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default RecordManagerPage;
