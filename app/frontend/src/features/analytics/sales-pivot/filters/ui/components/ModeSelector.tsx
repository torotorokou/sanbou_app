import { Space, Segmented, Typography } from 'antd';
import type { Mode } from '../../../shared/model/types';

interface ModeSelectorProps {
  value: Mode;
  onChange: (value: Mode) => void;
}

export const ModeSelector: React.FC<ModeSelectorProps> = ({ value, onChange }) => {
  return (
    <Space direction="vertical" size={2}>
      <Typography.Text type="secondary">モード</Typography.Text>
      <Segmented
        options={[
          { label: '顧客', value: 'customer' },
          { label: '品名', value: 'item' },
          { label: '日付', value: 'date' },
        ]}
        value={value}
        onChange={(v) => onChange(v as Mode)}
      />
    </Space>
  );
};
