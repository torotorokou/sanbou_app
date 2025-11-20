/**
 * sales-pivot/ui/SalesPivotBoardPage.tsx
 * Sales Pivot Board ページコンポーネント（MVVM View層）
 * 
 * ViewModel Hook（useSalesPivotBoardViewModel）を呼び出し、
 * 返された state/handlers を使って UI を描画する
 * 
 * ビジネスロジックは持たず、イベントを ViewModel に委譲する
 */

import React, { type FC } from 'react';
import {
  App,
  Badge,
  Button,
  Card,
  Col,
  DatePicker,
  Divider,
  Drawer,
  Empty,
  Row,
  Segmented,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Tabs,
  Tooltip,
  Typography,
  Dropdown,
  Switch,
} from 'antd';
import type { TableColumnsType, TableProps, MenuProps } from 'antd';
import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  InfoCircleOutlined,
  SwapOutlined,
  ReloadOutlined,
  DownloadOutlined,
  DownOutlined,
} from '@ant-design/icons';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RTooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import type { Dayjs } from 'dayjs';
import { salesPivotRepository } from '../shared/api/salesPivot.repository';
import { useSalesPivotBoardViewModel } from '../model/useSalesPivotBoardViewModel';
import type { MetricEntry, SummaryRow, Mode, SortKey, SortOrder } from '../shared/model/types';
import { fmtCurrency, fmtNumber, fmtUnitPrice, axisLabel } from '../shared/model/metrics';

/**
 * ソートバッジコンポーネント
 */
interface SortBadgeProps {
  label: string;
  keyName: SortKey;
  order: SortOrder;
}

const SortBadge: FC<SortBadgeProps> = ({ label, keyName, order }) => (
  <Badge
    count={order === 'desc' ? <ArrowDownOutlined /> : <ArrowUpOutlined />}
    style={{ backgroundColor: '#237804' }}
  >
    <Tag style={{ marginRight: 8 }}>
      {label}: {keyName}
    </Tag>
  </Badge>
);

/**
 * ページ本体
 */
export const SalesPivotBoardPage: FC = () => {
  const appContext = App.useApp?.();
  const message = appContext?.message;

  // ========== ViewModel ==========
  const vm = useSalesPivotBoardViewModel(salesPivotRepository);

  // ========== CSV Export Dropdown Menu ==========
  const exportMenu: MenuProps['items'] = [
    { key: 'title', label: <b>出力条件</b> },
    { type: 'divider' as const },

    // 追加カラム：残りモード1（実名）
    {
      key: 'addB',
      label: (
        <div onClick={(e) => e.stopPropagation()}>
          <Space>
            <Switch
              size="small"
              checked={vm.exportOptions.addAxisB}
              onChange={(v) => vm.setExportOptions((prev) => ({ ...prev, addAxisB: v }))}
            />
            <span>追加カラム：{axisLabel(vm.axB)}</span>
          </Space>
        </div>
      ),
    },

    // 追加カラム：残りモード2（実名）
    {
      key: 'addC',
      label: (
        <div onClick={(e) => e.stopPropagation()}>
          <Space>
            <Switch
              size="small"
              checked={vm.exportOptions.addAxisC}
              onChange={(v) => vm.setExportOptions((prev) => ({ ...prev, addAxisC: v }))}
            />
            <span>追加カラム：{axisLabel(vm.axC)}</span>
          </Space>
        </div>
      ),
    },

    { type: 'divider' as const },

    // 0実績除外（Excel負荷対策）
    {
      key: 'opt-zero',
      label: (
        <Space onClick={(e) => e.stopPropagation()}>
          <Switch
            size="small"
            checked={vm.exportOptions.excludeZero}
            onChange={(checked) => vm.setExportOptions((prev) => ({ ...prev, excludeZero: checked }))}
          />
          <span>0実績を除外する（Excel負荷対策）</span>
        </Space>
      ),
    },

    // 分割出力（任意・既存そのまま継続）
    {
      key: 'opt-split',
      label: (
        <Space onClick={(e) => e.stopPropagation()}>
          <Select
            size="small"
            value={vm.exportOptions.splitBy}
            onChange={(v: 'none' | 'rep') => vm.setExportOptions((prev) => ({ ...prev, splitBy: v }))}
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

  // ========== Parent Table Columns ==========
  const parentCols: TableColumnsType<SummaryRow> = [
    { title: '営業', dataIndex: 'repName', key: 'repName', width: 160, fixed: 'left' },
    {
      title: `${axisLabel(vm.mode)} Top${vm.topN === 'all' ? 'All' : vm.topN}`,
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
      },
    },
  ];

  // ========== Child Table Renderer（営業ごとのTopN） ==========
  const renderChildTable = (row: SummaryRow) => {
    const data = row.topN;
    const maxAmount = Math.max(1, ...data.map((x) => x.amount));
    const maxQty = Math.max(1, ...data.map((x) => x.qty));
    const maxCount = Math.max(1, ...data.map((x) => x.count));
    const unitCandidates = data.map((x) => x.unit_price ?? 0);
    const maxUnit = Math.max(1, ...unitCandidates);
    const nameTitle = axisLabel(vm.mode);

    const childCols: TableColumnsType<MetricEntry> = [
      { title: nameTitle, dataIndex: 'name', key: 'name', width: 220, sorter: true },
      {
        title: '売上',
        dataIndex: 'amount',
        key: 'amount',
        align: 'right',
        width: 180,
        sorter: true,
        render: (v: number) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ minWidth: 80, textAlign: 'right' }}>{fmtCurrency(v)}</span>
            <div className="mini-bar-bg">
              <div
                className="mini-bar mini-bar-blue"
                style={{ width: `${Math.round((v / maxAmount) * 100)}%` }}
              />
            </div>
          </div>
        ),
      },
      {
        title: '数量（kg）',
        dataIndex: 'qty',
        key: 'qty',
        align: 'right',
        width: 160,
        sorter: true,
        render: (v: number) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ minWidth: 64, textAlign: 'right' }}>{fmtNumber(v)}</span>
            <div className="mini-bar-bg">
              <div
                className="mini-bar mini-bar-green"
                style={{ width: `${Math.round((v / maxQty) * 100)}%` }}
              />
            </div>
          </div>
        ),
      },
      {
        title: '台数（台）',
        dataIndex: 'count',
        key: 'count',
        align: 'right',
        width: 120,
        sorter: true,
        render: (v: number) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ minWidth: 48, textAlign: 'right' }}>{fmtNumber(v)} 台</span>
            <div className="mini-bar-bg">
              <div
                className="mini-bar mini-bar-blue"
                style={{ width: `${Math.round((v / maxCount) * 100)}%` }}
              />
            </div>
          </div>
        ),
      },
      {
        title: (
          <Space>
            <span>売単価</span>
            <Tooltip title="単価＝Σ金額 / Σ数量（数量=0は未定義）">
              <InfoCircleOutlined />
            </Tooltip>
          </Space>
        ),
        dataIndex: 'unit_price',
        key: 'unit_price',
        align: 'right',
        width: 170,
        sorter: true,
        render: (v: number | null) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
            <span style={{ minWidth: 64, textAlign: 'right' }}>{fmtUnitPrice(v)}</span>
            <div className="mini-bar-bg">
              <div
                className="mini-bar mini-bar-gold"
                style={{ width: `${v ? Math.round((v / maxUnit) * 100) : 0}%` }}
              />
            </div>
          </div>
        ),
      },
      {
        title: '操作',
        key: 'ops',
        fixed: 'right',
        width: 120,
        render: (_, rec) => (
          <Button size="small" icon={<SwapOutlined />} onClick={() => vm.openPivot(rec)}>
            詳細
          </Button>
        ),
      },
    ];

    const onChildChange: TableProps<MetricEntry>['onChange'] = (_p, _f, sorter) => {
      const s = Array.isArray(sorter) ? sorter[0] : sorter;
      if (s && 'field' in s && s.field) {
        const f = String(s.field);
        let key: SortKey = vm.sortBy;
        if (f === 'name') key = vm.mode === 'date' ? 'date' : 'name';
        else if ((['amount', 'qty', 'count', 'unit_price'] as string[]).includes(f))
          key = f as SortKey;
        const ord: SortOrder = s.order === 'ascend' ? 'asc' : 'desc';
        vm.setSortBy(key);
        vm.setOrder(ord);
      }
    };

    // グラフ用（TopN棒）
    const chartBarData = data.map((d) => ({
      name: d.name,
      売上: d.amount,
      数量: d.qty,
      台数: d.count,
      売単価: d.unit_price ?? 0,
    }));
    const repId = row.repId;
    const series = vm.repSeriesCache[repId];
    const handleLoadSeries = async () => {
      if (vm.repSeriesCache[repId]) return;
      await vm.loadDailySeries(repId);
    };

    return (
      <Card className="accent-card accent-secondary" size="small" style={{ marginTop: 8 }}>
        <Tabs
          tabBarExtraContent={
            <Space wrap>
              <SortBadge label="並び替え" keyName={vm.sortBy} order={vm.order} />
              <Tag>Top{vm.topN === 'all' ? 'All' : vm.topN}</Tag>
            </Space>
          }
          items={[
            {
              key: 'table',
              label: '表',
              children: (
                <Table<MetricEntry>
                  rowKey="id"
                  size="small"
                  columns={childCols}
                  dataSource={data}
                  pagination={false}
                  onChange={onChildChange}
                  scroll={{ x: 1280 }}
                  rowClassName={(_, idx) => (idx % 2 === 0 ? 'zebra-even' : 'zebra-odd')}
                />
              ),
            },
            {
              key: 'chart',
              label: 'グラフ',
              children: (
                <Row gutter={[16, 16]}>
                  {/* モバイル（全幅）、デスクトップ（14/24列） */}
                  <Col xs={24} xl={14}>
                    <div className="card-subtitle">TopN（売上・数量・台数・売単価）</div>
                    <div style={{ width: '100%', height: 320 }}>
                      <ResponsiveContainer>
                        <BarChart
                          data={chartBarData}
                          margin={{ top: 8, right: 8, left: 8, bottom: 24 }}
                        >
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
                  {/* モバイル（全幅）、デスクトップ（10/24列） */}
                  <Col xs={24} xl={10}>
                    <Space
                      align="baseline"
                      style={{ justifyContent: 'space-between', width: '100%' }}
                    >
                      <div className="card-subtitle">
                        {vm.query.month
                          ? `${vm.query.month} 日次推移`
                          : `${vm.query.monthRange!.from}〜${vm.query.monthRange!.to} 日次推移`}
                        （営業：{row.repName}）
                      </div>
                      {!series && (
                        <Button size="small" onClick={handleLoadSeries} icon={<ReloadOutlined />}>
                          日次を取得
                        </Button>
                      )}
                    </Space>
                    <div style={{ width: '100%', height: 320 }}>
                      <ResponsiveContainer>
                        <LineChart
                          data={series ?? []}
                          margin={{ top: 8, right: 8, left: 8, bottom: 8 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" hide />
                          <YAxis />
                          <RTooltip
                            formatter={(v: number | string, name: string) =>
                              name === 'amount'
                                ? fmtCurrency(Number(v))
                                : name === 'qty'
                                ? `${fmtNumber(Number(v))} kg`
                                : name === 'count'
                                ? `${fmtNumber(Number(v))} 台`
                                : fmtUnitPrice(Number(v))
                            }
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
              ),
            },
          ]}
        />
      </Card>
    );
  };

  // ========== Pivot Drawer Table Handler ==========
  const onPivotTableChange: TableProps<MetricEntry>['onChange'] = (_p, _f, sorter) => {
    const s = Array.isArray(sorter) ? sorter[0] : sorter;
    if (s && 'field' in s && s.field && vm.drawer.open) {
      const f = String(s.field);
      let nextKey: SortKey = vm.drawer.sortBy;
      if (f === 'name') nextKey = vm.drawer.activeAxis === 'date' ? 'date' : 'name';
      else if ((['amount', 'qty', 'count', 'unit_price'] as string[]).includes(f))
        nextKey = f as SortKey;
      const nextOrder: SortOrder = s.order === 'ascend' ? 'asc' : 'desc';
      vm.setDrawerSortBy(nextKey);
      vm.setDrawerOrder(nextOrder);
    }
  };

  // ========== Render ==========
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
        .summary-tags { font-size: 14px; }
        .summary-tags .ant-tag { font-size: 14px; padding: 0 10px; }
      `}</style>

      {/* ヘッダ（CSV：Dropdown.Buttonでワンクリック＋実名選択） */}
      <div className="app-header">
        <Typography.Title level={3} className="app-title">
          <span className="app-title-accent">売上ツリー</span>
        </Typography.Title>
        <div className="app-header-actions">
          {vm.repIds.length === 0 ? (
            <Tooltip title="営業が未選択のためCSV出力できません">
              <Button icon={<DownloadOutlined />} type="default" disabled>
                CSV出力
              </Button>
            </Tooltip>
          ) : (
            <Tooltip
              title={`出力：選択営業 × ${axisLabel(vm.baseAx)}${vm.exportOptions.addAxisB ? ` × ${axisLabel(vm.axB)}` : ''}${vm.exportOptions.addAxisC ? ` × ${axisLabel(vm.axC)}` : ''}（期間：${vm.periodLabel}、0実績は${vm.exportOptions.excludeZero ? '除外' : '含む'}、${vm.exportOptions.splitBy === 'rep' ? '営業別分割' : '単一ファイル'}）`}
            >
              <Dropdown.Button
                type="default"
                icon={<DownloadOutlined />}
                overlayStyle={{ width: 380 }}
                menu={{ items: exportMenu }}
                onClick={() => {
                  void vm.handleExport().then(() => {
                    message?.success?.('CSVを出力しました。');
                  }).catch((e) => {
                    console.error(e);
                    message?.error?.('CSV出力でエラーが発生しました。');
                  });
                }}
                placement="bottomRight"
                trigger={['click']}
                buttonsRender={([left, right]) => [
                  left,
                  React.isValidElement(right)
                    ? React.cloneElement(right, { icon: <DownOutlined /> })
                    : right,
                ]}
              >
                CSV出力
              </Dropdown.Button>
            </Tooltip>
          )}
        </div>
      </div>

      {/* フィルタ＆コントロール */}
      <Card
        className="accent-card accent-primary"
        title={<div className="card-section-header">条件</div>}
      >
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={10}>
            <Space direction="vertical" size={2} style={{ width: '100%' }}>
              <Typography.Text type="secondary">対象（単月 / 期間）</Typography.Text>
              <Space wrap>
                <Segmented
                  options={[
                    { label: '単月', value: 'single' },
                    { label: '期間', value: 'range' },
                  ]}
                  value={vm.periodMode}
                  onChange={(v: string | number) => vm.setPeriodMode(v as 'single' | 'range')}
                />
                {vm.periodMode === 'single' ? (
                  <DatePicker
                    picker="month"
                    value={vm.month}
                    onChange={(d: Dayjs | null) => d && vm.setMonth(d.startOf('month'))}
                    allowClear={false}
                  />
                ) : (
                  <DatePicker.RangePicker
                    picker="month"
                    value={vm.range}
                    onChange={(vals: [Dayjs | null, Dayjs | null] | null) => {
                      if (vals && vals[0] && vals[1])
                        vm.setRange([vals[0].startOf('month'), vals[1].startOf('month')]);
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
                  <Segmented
                    options={[
                      { label: '顧客', value: 'customer' },
                      { label: '品名', value: 'item' },
                      { label: '日付', value: 'date' },
                    ]}
                    value={vm.mode}
                    onChange={(v) => vm.switchMode(v as Mode)}
                  />
                </Space>
              </Col>
              <Col xs={24} md={16}>
                <Space direction="vertical" size={2} style={{ width: '100%' }}>
                  <Typography.Text type="secondary">Top & 並び替え</Typography.Text>
                  <Space wrap>
                    <Segmented
                      options={[
                        { label: '10', value: '10' },
                        { label: '20', value: '20' },
                        { label: '50', value: '50' },
                        { label: 'All', value: 'all' },
                      ]}
                      value={String(vm.topN)}
                      onChange={(v: string | number) =>
                        vm.setTopN(v === 'all' ? 'all' : (Number(v) as 10 | 20 | 50))
                      }
                    />
                    <Segmented
                      options={vm.sortKeyOptions}
                      value={vm.sortBy}
                      onChange={(v) => vm.setSortBy(v as SortKey)}
                    />
                    <Segmented
                      options={[
                        { label: '降順', value: 'desc' },
                        { label: '昇順', value: 'asc' },
                      ]}
                      value={vm.order}
                      onChange={(v) => vm.setOrder(v as SortOrder)}
                    />
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
                <Select
                  mode="multiple"
                  allowClear
                  placeholder="（未選択）"
                  options={vm.repOptions}
                  value={vm.repIds}
                  onChange={vm.setRepIds}
                  style={{ flex: 1 }}
                />
                <Space>
                  <Button
                    size="small"
                    onClick={() => vm.setRepIds(vm.reps.map((r) => r.id))}
                    disabled={vm.repIds.length === vm.reps.length}
                  >
                    全営業を表示
                  </Button>
                  <Button
                    size="small"
                    onClick={() => vm.setRepIds([])}
                    disabled={vm.repIds.length === 0}
                  >
                    クリア
                  </Button>
                </Space>
              </div>
            </Space>
          </Col>
          <Col xs={24} md={12}>
            <Space direction="vertical" size={2} style={{ width: '100%' }}>
              <Typography.Text type="secondary">
                {axisLabel(vm.mode)}で絞る
              </Typography.Text>
              <Select
                mode="multiple"
                allowClear
                placeholder={`（未選択＝全${axisLabel(vm.mode)}）`}
                options={vm.filterOptions}
                value={vm.filterIds}
                onChange={vm.setFilterIds}
                style={{ width: '100%' }}
              />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* KPI（営業名をタイトルに反映） */}
      {vm.repIds.length > 0 ? (
        <Card
          className="accent-card accent-gold"
          title={
            <div className="card-section-header">
              KPI（営業：
              <Tooltip
                title={
                  vm.repIds.length
                    ? vm.reps
                        .filter((r) => vm.repIds.includes(r.id))
                        .map((r) => r.name)
                        .join('・')
                    : '未選択'
                }
              >
                <span>{vm.selectedRepLabel}</span>
              </Tooltip>
              ）
            </div>
          }
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} md={6}>
              <Statistic
                title="（表示対象）合計 売上"
                value={vm.headerTotals.amount}
                formatter={(v) => fmtCurrency(Number(v))}
              />
            </Col>
            <Col xs={24} md={6}>
              <Statistic
                title="（表示対象）合計 数量"
                value={vm.headerTotals.qty}
                formatter={(v) => `${fmtNumber(Number(v))} kg`}
              />
            </Col>
            <Col xs={24} md={6}>
              <Statistic
                title="（表示対象）合計 台数"
                value={vm.headerTotals.count}
                formatter={(v) => `${fmtNumber(Number(v))} 台`}
              />
            </Col>
            <Col xs={24} md={6}>
              <Statistic
                title="（表示対象）加重平均 単価"
                valueRender={() => <span>{fmtUnitPrice(vm.headerTotals.unit)}</span>}
              />
            </Col>
          </Row>
        </Card>
      ) : (
        <Card className="accent-card accent-gold">
          <div style={{ padding: 12 }}>
            <Typography.Text type="secondary">
              営業が未選択のため、KPIは表示されません。左上の「営業」から選択してください。
            </Typography.Text>
          </div>
        </Card>
      )}

      {/* メインテーブル */}
      {vm.repIds.length > 0 ? (
        <Card
          className="accent-card accent-primary"
          title={<div className="card-section-header">一覧</div>}
        >
          <Table<SummaryRow>
            rowKey={(r) => r.repId}
            columns={parentCols}
            dataSource={vm.summary}
            loading={vm.loading}
            pagination={false}
            expandable={{
              expandedRowRender: (record) => renderChildTable(record),
              rowExpandable: () => true,
            }}
            scroll={{ x: 1220 }}
            rowClassName={(_, idx) => (idx % 2 === 0 ? 'zebra-even' : 'zebra-odd')}
          />
        </Card>
      ) : (
        <Card className="accent-card accent-primary">
          <div style={{ padding: 12 }}>
            <Typography.Text type="secondary">
              営業が未選択のため、一覧は表示されません。左上の「営業」から選択してください。
            </Typography.Text>
          </div>
        </Card>
      )}

      {/* Drawer: Pivot（CSVボタンなし） */}
      <Drawer
        title={
          vm.drawer.open
            ? `詳細：${axisLabel(vm.drawer.baseAxis)}「${vm.drawer.baseName}」`
            : ''
        }
        open={vm.drawer.open}
        onClose={vm.closeDrawer}
        width={1000}
      >
        {vm.drawer.open ? (
          <Card
            className="accent-card accent-secondary"
            title={<div className="card-section-header">ピボット</div>}
          >
            <Row gutter={[16, 16]} align="middle" style={{ marginBottom: 8 }}>
              <Col flex="auto">
                <Space wrap>
                  <Tag color="#237804">ベース：{axisLabel(vm.drawer.baseAxis)}</Tag>
                  <Tag>{vm.drawer.baseName}</Tag>
                  <SortBadge label="並び替え" keyName={vm.drawer.sortBy} order={vm.drawer.order} />
                  <Tag>Top{vm.drawer.topN === 'all' ? 'All' : vm.drawer.topN}</Tag>
                </Space>
              </Col>
            </Row>

            <Tabs
              activeKey={vm.drawer.activeAxis}
              onChange={(active) => vm.setDrawerActiveAxis(active as Mode)}
              tabBarExtraContent={
                <Space wrap>
                  <Segmented
                    options={[
                      { label: '10', value: '10' },
                      { label: '20', value: '20' },
                      { label: '50', value: '50' },
                      { label: 'All', value: 'all' },
                    ]}
                    value={String(vm.drawer.topN)}
                    onChange={(v: string | number) =>
                      vm.setDrawerTopN(v === 'all' ? 'all' : (Number(v) as 10 | 20 | 50))
                    }
                  />
                  <Segmented
                    options={[
                      { label: '売上', value: 'amount' },
                      { label: '数量', value: 'qty' },
                      { label: '台数', value: 'count' },
                      { label: '売単価', value: 'unit_price' },
                      {
                        label: vm.drawer.activeAxis === 'date' ? '日付' : '名称',
                        value: vm.drawer.activeAxis === 'date' ? 'date' : 'name',
                      },
                    ]}
                    value={vm.drawer.sortBy}
                    onChange={(v) => vm.setDrawerSortBy(v as SortKey)}
                  />
                  <Segmented
                    options={[
                      { label: '降順', value: 'desc' },
                      { label: '昇順', value: 'asc' },
                    ]}
                    value={vm.drawer.order}
                    onChange={(v) => vm.setDrawerOrder(v as SortOrder)}
                  />
                </Space>
              }
              items={vm.drawer.targets.map((t) => {
                const rows = vm.pivotData[t.axis];
                const maxA = Math.max(1, ...rows.map((x) => x.amount));
                const maxQ = Math.max(1, ...rows.map((x) => x.qty));
                const maxC = Math.max(1, ...rows.map((x) => x.count));
                const maxU = Math.max(1, ...rows.map((x) => x.unit_price ?? 0));

                const cols: TableColumnsType<MetricEntry> = [
                  {
                    title: axisLabel(t.axis),
                    dataIndex: 'name',
                    key: 'name',
                    width: 220,
                    sorter: true,
                  },
                  {
                    title: '売上',
                    dataIndex: 'amount',
                    key: 'amount',
                    align: 'right',
                    width: 170,
                    sorter: true,
                    render: (v: number) => (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
                        <span style={{ minWidth: 72, textAlign: 'right' }}>{fmtCurrency(v)}</span>
                        <div className="mini-bar-bg">
                          <div
                            className="mini-bar mini-bar-blue"
                            style={{ width: `${Math.round((v / maxA) * 100)}%` }}
                          />
                        </div>
                      </div>
                    ),
                  },
                  {
                    title: '数量',
                    dataIndex: 'qty',
                    key: 'qty',
                    align: 'right',
                    width: 150,
                    sorter: true,
                    render: (v: number) => (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
                        <span style={{ minWidth: 60, textAlign: 'right' }}>{fmtNumber(v)}</span>
                        <div className="mini-bar-bg">
                          <div
                            className="mini-bar mini-bar-green"
                            style={{ width: `${Math.round((v / maxQ) * 100)}%` }}
                          />
                        </div>
                      </div>
                    ),
                  },
                  {
                    title: '台数（台）',
                    dataIndex: 'count',
                    key: 'count',
                    align: 'right',
                    width: 120,
                    sorter: true,
                    render: (v: number) => (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
                        <span style={{ minWidth: 48, textAlign: 'right' }}>{fmtNumber(v)} 台</span>
                        <div className="mini-bar-bg">
                          <div
                            className="mini-bar mini-bar-blue"
                            style={{ width: `${Math.round((v / maxC) * 100)}%` }}
                          />
                        </div>
                      </div>
                    ),
                  },
                  {
                    title: (
                      <Space>
                        <span>売単価</span>
                        <Tooltip title="単価＝Σ金額 / Σ数量（数量=0は未定義）">
                          <InfoCircleOutlined />
                        </Tooltip>
                      </Space>
                    ),
                    dataIndex: 'unit_price',
                    key: 'unit_price',
                    align: 'right',
                    width: 170,
                    sorter: true,
                    render: (v: number | null) => (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
                        <span style={{ minWidth: 64, textAlign: 'right' }}>{fmtUnitPrice(v)}</span>
                        <div className="mini-bar-bg">
                          <div
                            className="mini-bar mini-bar-gold"
                            style={{ width: `${v ? Math.round((v / maxU) * 100) : 0}%` }}
                          />
                        </div>
                      </div>
                    ),
                  },
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
                        loading={vm.pivotLoading}
                        pagination={false}
                        onChange={onPivotTableChange}
                        locale={{
                          emptyText: vm.pivotLoading ? '読込中...' : <Empty description="該当なし" />,
                        }}
                        scroll={{ x: 980 }}
                        rowClassName={(_, idx) => (idx % 2 === 0 ? 'zebra-even' : 'zebra-odd')}
                      />
                      <Space style={{ marginTop: 8 }}>
                        <Button
                          icon={<ReloadOutlined />}
                          onClick={() => vm.loadPivot(t.axis, true)}
                        >
                          再読込
                        </Button>
                        {vm.drawer.open && vm.drawer.topN === 'all' && vm.pivotCursor[t.axis] && (
                          <Button
                            type="primary"
                            onClick={() => vm.loadPivot(t.axis, false)}
                            loading={vm.pivotLoading}
                          >
                            さらに読み込む
                          </Button>
                        )}
                        {vm.drawer.open && vm.drawer.topN === 'all' && !vm.pivotCursor[t.axis] && (
                          <Typography.Text type="secondary">すべて読み込み済み</Typography.Text>
                        )}
                      </Space>
                    </>
                  ),
                };
              })}
            />
          </Card>
        ) : null}
      </Drawer>
    </Space>
  );
};

export default SalesPivotBoardPage;
