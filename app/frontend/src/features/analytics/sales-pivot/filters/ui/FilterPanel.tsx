/**
 * filters/ui/FilterPanel.tsx
 * フィルタパネル統合UI
 */

import React from 'react';
import { Card, Row, Col, Divider, Space, Typography, Segmented, DatePicker, Select, Button, Radio } from 'antd';
import type { Dayjs } from 'dayjs';
import type { Mode, SortKey, SortOrder, ID, SalesRep, CategoryKind } from '../../shared/model/types';
import { axisLabel } from '../../shared/model/metrics';

interface FilterPanelProps {
  // Period
  periodMode: 'single' | 'range';
  month: Dayjs;
  range: [Dayjs, Dayjs] | null;
  onPeriodModeChange: (mode: 'single' | 'range') => void;
  onMonthChange: (month: Dayjs) => void;
  onRangeChange: (range: [Dayjs, Dayjs] | null) => void;

  // Category
  categoryKind: CategoryKind;
  onCategoryKindChange: (kind: CategoryKind) => void;

  // Mode & Controls
  mode: Mode;
  topN: 10 | 20 | 50 | 'all';
  sortBy: SortKey;
  order: SortOrder;
  onModeChange: (mode: Mode) => void;
  onTopNChange: (topN: 10 | 20 | 50 | 'all') => void;
  onSortByChange: (sortBy: SortKey) => void;
  onOrderChange: (order: SortOrder) => void;

  // Rep & Filter
  repIds: ID[];
  filterIds: ID[];
  reps: SalesRep[];
  repOptions: Array<{ label: string; value: ID }>;
  filterOptions: Array<{ label: string; value: ID }>;
  sortKeyOptions: Array<{ label: string; value: SortKey }>;
  onRepIdsChange: (ids: ID[]) => void;
  onFilterIdsChange: (ids: ID[]) => void;
}

/**
 * フィルタパネルコンポーネント
 */
export const FilterPanel: React.FC<FilterPanelProps> = ({
  periodMode,
  month,
  range,
  onPeriodModeChange,
  onMonthChange,
  onRangeChange,
  categoryKind,
  onCategoryKindChange,
  mode,
  topN,
  sortBy,
  order,
  onModeChange,
  onTopNChange,
  onSortByChange,
  onOrderChange,
  repIds,
  filterIds,
  reps,
  repOptions,
  filterOptions,
  sortKeyOptions,
  onRepIdsChange,
  onFilterIdsChange,
}) => {
  return (
    <Card className="sales-tree-accent-card sales-tree-accent-primary" title={<div className="sales-tree-card-section-header">条件</div>}>
      <Row gutter={[16, 16]} align="middle">
        {/* 種別切り替え */}
        <Col xs={24} sm={8} md={4}>
          <Space direction="vertical" size={2}>
            <Typography.Text type="secondary">種別</Typography.Text>
            <Radio.Group
              value={categoryKind}
              onChange={(e) => onCategoryKindChange(e.target.value as CategoryKind)}
              buttonStyle="solid"
            >
              <Radio.Button value="waste">廃棄物</Radio.Button>
              <Radio.Button value="valuable">有価物</Radio.Button>
            </Radio.Group>
          </Space>
        </Col>

        {/* モード */}
        <Col xs={24} sm={8} md={4}>
          <Space direction="vertical" size={2}>
            <Typography.Text type="secondary">モード</Typography.Text>
            <Segmented
              options={[
                { label: '顧客', value: 'customer' },
                { label: '品名', value: 'item' },
                { label: '日付', value: 'date' },
              ]}
              value={mode}
              onChange={(v) => onModeChange(v as Mode)}
            />
          </Space>
        </Col>

        {/* TopN・ソート */}
        <Col xs={24} sm={16} md={16}>
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
                value={String(topN)}
                onChange={(v: string | number) =>
                  onTopNChange(v === 'all' ? 'all' : (Number(v) as 10 | 20 | 50))
                }
              />
              <Segmented
                options={sortKeyOptions}
                value={sortBy}
                onChange={(v) => onSortByChange(v as SortKey)}
              />
              <Segmented
                options={[
                  { label: '降順', value: 'desc' },
                  { label: '昇順', value: 'asc' },
                ]}
                value={order}
                onChange={(v) => onOrderChange(v as SortOrder)}
              />
            </Space>
          </Space>
        </Col>
      </Row>

      <Row gutter={[16, 16]} align="middle" style={{ marginTop: 8 }}>
        {/* 期間選択 */}
        <Col xs={24} lg={24}>
          <Space direction="vertical" size={2} style={{ width: '100%' }}>
            <Typography.Text type="secondary">対象（単月 / 期間）</Typography.Text>
            <Space wrap>
              <Segmented
                options={[
                  { label: '単月', value: 'single' },
                  { label: '期間', value: 'range' },
                ]}
                value={periodMode}
                onChange={(v: string | number) => onPeriodModeChange(v as 'single' | 'range')}
              />
              {periodMode === 'single' ? (
                <DatePicker
                  picker="month"
                  value={month}
                  onChange={(d: Dayjs | null) => d && onMonthChange(d.startOf('month'))}
                  allowClear={false}
                />
              ) : (
                <DatePicker.RangePicker
                  picker="month"
                  value={range}
                  onChange={(vals: [Dayjs | null, Dayjs | null] | null) => {
                    if (vals && vals[0] && vals[1])
                      onRangeChange([vals[0].startOf('month'), vals[1].startOf('month')]);
                  }}
                  allowEmpty={[false, false]}
                />
              )}
            </Space>
          </Space>
        </Col>
      </Row>

      <Divider style={{ margin: '16px 0' }} />

      {/* 旧レイアウトの残骸を削除するため、次のセクションを調整 */}
      <Row gutter={[16, 16]} style={{ display: 'none' }}>
        <Col xs={24} lg={11}>
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
                  value={mode}
                  onChange={(v) => onModeChange(v as Mode)}
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
                    value={String(topN)}
                    onChange={(v: string | number) =>
                      onTopNChange(v === 'all' ? 'all' : (Number(v) as 10 | 20 | 50))
                    }
                  />
                  <Segmented
                    options={sortKeyOptions}
                    value={sortBy}
                    onChange={(v) => onSortByChange(v as SortKey)}
                  />
                  <Segmented
                    options={[
                      { label: '降順', value: 'desc' },
                      { label: '昇順', value: 'asc' },
                    ]}
                    value={order}
                    onChange={(v) => onOrderChange(v as SortOrder)}
                  />
                </Space>
              </Space>
            </Col>
          </Row>
        </Col>
      </Row>

      <Divider style={{ margin: '16px 0' }} />

      {/* 営業・絞り込み */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={18}>
          <Space direction="vertical" size={2} style={{ width: '100%' }}>
            <Typography.Text type="secondary">営業</Typography.Text>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Select
                mode="multiple"
                allowClear
                placeholder="（未選択）"
                options={repOptions}
                value={repIds}
                onChange={onRepIdsChange}
                style={{ flex: 1 }}
              />
              <Space>
                <Button
                  size="small"
                  onClick={() => onRepIdsChange(reps.map((r) => r.id))}
                  disabled={repIds.length === reps.length}
                >
                  全営業を表示
                </Button>
                <Button size="small" onClick={() => onRepIdsChange([])} disabled={repIds.length === 0}>
                  クリア
                </Button>
              </Space>
            </div>
          </Space>
        </Col>
        <Col xs={24} md={6}>
          <Space direction="vertical" size={2} style={{ width: '100%' }}>
            <Typography.Text type="secondary">{axisLabel(mode)}で絞る</Typography.Text>
            <Select
              key={mode}
              mode="multiple"
              allowClear
              placeholder={`（未選択＝全${axisLabel(mode)}）`}
              options={filterOptions}
              value={filterIds}
              onChange={onFilterIdsChange}
              style={{ width: '100%' }}
            />
          </Space>
        </Col>
      </Row>

      {/* スタイル */}
      <style>{`
        .accent-card { border-left: 4px solid #23780410; overflow: hidden; }
        .accent-primary { border-left-color: #237804; }
        .card-section-header { 
          font-weight: 600; 
          padding: 6px 10px; 
          margin-bottom: 12px; 
          border-radius: 6px; 
          background: #f3fff4; 
          border: 1px solid #e6f7e6; 
        }
      `}</style>
    </Card>
  );
};
