import React from 'react';
import { DatePicker, Typography } from 'antd';
import type { Dayjs } from 'dayjs';
const { Title } = Typography;

type Props = {
    targetStart: Dayjs | null;
    targetEnd: Dayjs | null;
    compareStart: Dayjs | null;
    compareEnd: Dayjs | null;
    setTargetStart: (d: Dayjs | null) => void;
    setTargetEnd: (d: Dayjs | null) => void;
    setCompareStart: (d: Dayjs | null) => void;
    setCompareEnd: (d: Dayjs | null) => void;
};

const ComparisonConditionForm: React.FC<Props> = ({
    targetStart,
    targetEnd,
    compareStart,
    compareEnd,
    setTargetStart,
    setTargetEnd,
    setCompareStart,
    setCompareEnd,
}) => (
    <>
        <Title level={5} style={{ marginBottom: 12 }}>
            対象月グループ
        </Title>
        <div style={{ marginBottom: 8 }}>
            開始月:{' '}
            <DatePicker
                picker='month'
                value={targetStart}
                onChange={setTargetStart}
                style={{ width: 120 }}
            />
            <span style={{ margin: '0 8px' }}>～</span>
            終了月:{' '}
            <DatePicker
                picker='month'
                value={targetEnd}
                onChange={setTargetEnd}
                disabledDate={(current) =>
                    targetStart
                        ? current && current.isBefore(targetStart, 'month')
                        : false
                }
                style={{ width: 120 }}
            />
        </div>
        <Title level={5} style={{ margin: '24px 0 8px 0' }}>
            比較月グループ
        </Title>
        <div style={{ marginBottom: 8 }}>
            開始月:{' '}
            <DatePicker
                picker='month'
                value={compareStart}
                onChange={setCompareStart}
                style={{ width: 120 }}
            />
            <span style={{ margin: '0 8px' }}>～</span>
            終了月:{' '}
            <DatePicker
                picker='month'
                value={compareEnd}
                onChange={setCompareEnd}
                disabledDate={(current) =>
                    compareStart
                        ? current && current.isBefore(compareStart, 'month')
                        : false
                }
                style={{ width: 120 }}
            />
        </div>
    </>
);

export default ComparisonConditionForm;
