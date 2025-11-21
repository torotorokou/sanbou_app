import React from 'react';
import { DatePicker, Typography } from 'antd';
import type { Dayjs } from 'dayjs';
const { Title } = Typography;

type Props = {
    currentStart: Dayjs | null;
    currentEnd: Dayjs | null;
    previousStart: Dayjs | null;
    previousEnd: Dayjs | null;
    setCurrentStart: (d: Dayjs | null) => void;
    setCurrentEnd: (d: Dayjs | null) => void;
    setPreviousStart: (d: Dayjs | null) => void;
    setPreviousEnd: (d: Dayjs | null) => void;
};

const ComparisonConditionForm: React.FC<Props> = ({
    currentStart,
    currentEnd,
    previousStart,
    previousEnd,
    setCurrentStart,
    setCurrentEnd,
    setPreviousStart,
    setPreviousEnd,
}) => (
    <>
        <Title level={5} style={{ marginBottom: 12 }}>
            今期（分析対象期間）
        </Title>
        <div style={{ marginBottom: 8 }}>
            開始月:{' '}
            <DatePicker
                picker='month'
                value={currentStart}
                onChange={setCurrentStart}
                style={{ width: 120 }}
            />
            <span style={{ margin: '0 8px' }}>～</span>
            終了月:{' '}
            <DatePicker
                picker='month'
                value={currentEnd}
                onChange={setCurrentEnd}
                disabledDate={(current) =>
                    currentStart
                        ? current && current.isBefore(currentStart, 'month')
                        : false
                }
                style={{ width: 120 }}
            />
        </div>
        <Title level={5} style={{ margin: '24px 0 8px 0' }}>
            前期（比較期間）
        </Title>
        <div style={{ marginBottom: 8 }}>
            開始月:{' '}
            <DatePicker
                picker='month'
                value={previousStart}
                onChange={setPreviousStart}
                style={{ width: 120 }}
            />
            <span style={{ margin: '0 8px' }}>～</span>
            終了月:{' '}
            <DatePicker
                picker='month'
                value={previousEnd}
                onChange={setPreviousEnd}
                disabledDate={(current) =>
                    previousStart
                        ? current && current.isBefore(previousStart, 'month')
                        : false
                }
                style={{ width: 120 }}
            />
        </div>
    </>
);

export default ComparisonConditionForm;
