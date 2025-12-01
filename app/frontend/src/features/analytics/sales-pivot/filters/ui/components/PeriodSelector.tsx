import { Space, Segmented, DatePicker, Typography } from 'antd';
import type { Dayjs } from 'dayjs';
import locale from 'antd/es/date-picker/locale/ja_JP';
import 'dayjs/locale/ja';
import styles from './PeriodSelector.module.css';

interface PeriodSelectorProps {
  granularity: 'month' | 'date';
  periodMode: 'single' | 'range';
  month: Dayjs | null;
  range: [Dayjs, Dayjs] | null;
  singleDate: Dayjs | null;
  dateRange: [Dayjs, Dayjs] | null;
  onGranularityChange: (value: 'month' | 'date') => void;
  onPeriodModeChange: (value: 'single' | 'range') => void;
  onMonthChange: (value: Dayjs) => void;
  onRangeChange: (value: [Dayjs, Dayjs]) => void;
  onSingleDateChange: (value: Dayjs) => void;
  onDateRangeChange: (value: [Dayjs, Dayjs] | null) => void;
}

export const PeriodSelector: React.FC<PeriodSelectorProps> = ({
  granularity,
  periodMode,
  month,
  range,
  singleDate,
  dateRange,
  onGranularityChange,
  onPeriodModeChange,
  onMonthChange,
  onRangeChange,
  onSingleDateChange,
  onDateRangeChange,
}) => {
  return (
    <Space direction="vertical" size={2} style={{ width: '100%' }}>
      <Typography.Text type="secondary">対象（月次 / 日次）</Typography.Text>
      <Space wrap>
        {/* 粒度選択 */}
        <Segmented
          options={[
            { label: '月次', value: 'month' },
            { label: '日次', value: 'date' },
          ]}
          value={granularity}
          onChange={(v: string | number) => onGranularityChange(v as 'month' | 'date')}
        />
        {/* 単一/期間選択 */}
        <Segmented
          options={[
            { label: '単一', value: 'single' },
            { label: '期間', value: 'range' },
          ]}
          value={periodMode}
          onChange={(v: string | number) => onPeriodModeChange(v as 'single' | 'range')}
        />
        {/* 日付/月の選択 */}
        {granularity === 'month' ? (
          periodMode === 'single' ? (
            <DatePicker
              picker="month"
              value={month}
              onChange={(d: Dayjs | null) => d && onMonthChange(d.startOf('month'))}
              allowClear={false}
              placeholder="対象月"
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
              placeholder={['開始月', '終了月']}
            />
          )
        ) : (
          periodMode === 'single' ? (
            <DatePicker
              value={singleDate}
              onChange={(d: Dayjs | null) => d && onSingleDateChange(d)}
              allowClear={false}
              placeholder="対象日"
              locale={locale}
              className={styles.datePicker}
            />
          ) : (
            <DatePicker.RangePicker
              value={dateRange}
              onChange={(vals: [Dayjs | null, Dayjs | null] | null) => {
                if (vals && vals[0] && vals[1]) {
                  onDateRangeChange([vals[0], vals[1]]);
                } else {
                  onDateRangeChange(null);
                }
              }}
              placeholder={['開始日', '終了日']}
              locale={locale}
              className={styles.datePicker}
            />
          )
        )}
      </Space>
    </Space>
  );
};
