import { Space, Segmented, Typography } from 'antd';
import type { SortKey, SortOrder } from '../../../shared/model/types';

type TopN = 10 | 20 | 50 | 'all';

interface TopNSortControlsProps {
  topN: TopN;
  sortBy: SortKey;
  order: SortOrder;
  sortKeyOptions: Array<{ label: string; value: string }>;
  onTopNChange: (value: TopN) => void;
  onSortByChange: (value: SortKey) => void;
  onOrderChange: (value: SortOrder) => void;
}

export const TopNSortControls: React.FC<TopNSortControlsProps> = ({
  topN,
  sortBy,
  order,
  sortKeyOptions,
  onTopNChange,
  onSortByChange,
  onOrderChange,
}) => {
  return (
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
  );
};
