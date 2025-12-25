import { Row, Col, Space, Select, Button, Typography } from 'antd';
import type { Mode, ID, SalesRep } from '../../../shared/model/types';
import { axisLabel } from '../../../shared/model/metrics';

interface RepFilterSelectorProps {
  mode: Mode;
  repIds: ID[];
  filterIds: ID[];
  reps: SalesRep[];
  repOptions: Array<{ label: string; value: string }>;
  filterOptions: Array<{ label: string; value: string }>;
  onRepIdsChange: (value: ID[]) => void;
  onFilterIdsChange: (value: ID[]) => void;
}

export const RepFilterSelector: React.FC<RepFilterSelectorProps> = ({
  mode,
  repIds,
  filterIds,
  reps,
  repOptions,
  filterOptions,
  onRepIdsChange,
  onFilterIdsChange,
}) => {
  return (
    <Row gutter={[16, 16]}>
      {/* 営業選択 */}
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
              <Button
                size="small"
                onClick={() => onRepIdsChange([])}
                disabled={repIds.length === 0}
              >
                クリア
              </Button>
            </Space>
          </div>
        </Space>
      </Col>

      {/* 絞り込みフィルタ */}
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
  );
};
