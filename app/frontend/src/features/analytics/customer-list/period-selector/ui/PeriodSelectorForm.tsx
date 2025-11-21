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

/**
 * Period Selector Form Component
 * 
 * 今期・前期の期間選択フォーム
 */
const PeriodSelectorForm: React.FC<Props> = ({
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
            <div style={{ marginBottom: 8 }}>
                開始月：
                <DatePicker
                    picker='month'
                    value={currentStart}
                    onChange={setCurrentStart}
                    style={{ width: 120, marginLeft: 8 }}
                />
            </div>
            <div>
                終了月：
                <DatePicker
                    picker='month'
                    value={currentEnd}
                    onChange={setCurrentEnd}
                    disabledDate={(current) =>
                        currentStart
                            ? current && current.isBefore(currentStart, 'month')
                            : false
                    }
                    style={{ width: 120, marginLeft: 8 }}
                />
            </div>
        </div>
        <Title level={5} style={{ margin: '24px 0 8px 0' }}>
            前期（比較期間）
        </Title>
        <div style={{ marginBottom: 8 }}>
            <div style={{ marginBottom: 8 }}>
                開始月：
                <DatePicker
                    picker='month'
                    value={previousStart}
                    onChange={setPreviousStart}
                    disabled={!currentStart || !currentEnd}
                    disabledDate={(current) => {
                        if (!currentStart || !currentEnd) return false;
                        // 今期の範囲と重複する月を無効化
                        return current && (
                            !current.isBefore(currentStart, 'month') && 
                            !current.isAfter(currentEnd, 'month')
                        );
                    }}
                    style={{ width: 120, marginLeft: 8 }}
                    placeholder={!currentStart || !currentEnd ? '今期を先に選択' : undefined}
                />
            </div>
            <div>
                終了月：
                <DatePicker
                    picker='month'
                    value={previousEnd}
                    onChange={setPreviousEnd}
                    disabled={!previousStart || !currentStart || !currentEnd}
                    disabledDate={(current) => {
                        if (!currentStart || !currentEnd || !previousStart) return false;
                        // 前期開始月より前、または今期と重複する月を無効化
                        return current && (
                            current.isBefore(previousStart, 'month') ||
                            (!current.isBefore(currentStart, 'month') && 
                             !current.isAfter(currentEnd, 'month'))
                        );
                    }}
                    style={{ width: 120, marginLeft: 8 }}
                    placeholder={!previousStart ? '開始月を先に選択' : undefined}
                />
            </div>
        </div>
    </>
);

export default PeriodSelectorForm;
