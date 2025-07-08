// /components/Report/common/ReportSelector.tsx
import React from 'react';
import { Select } from 'antd';

type ReportSelectorProps = {
    reportKey: string;
    onChange: (key: string) => void;
};

const ReportSelector: React.FC<ReportSelectorProps> = ({
    reportKey,
    onChange,
}) => {
    return (
        <Select
            value={reportKey}
            onChange={onChange}
            options={[
                { value: 'factory', label: '工場日報' },
                { value: 'attendance', label: '搬出入収支表' },
                { value: 'abc', label: 'ABC集計表' },
                { value: 'block', label: 'ブロック単価表' },
                { value: 'management', label: '管理表' },
                // 他帳票追加可
            ]}
            size='large'
            style={{
                width: 240,
                fontWeight: 500,
                borderRadius: 12,
                boxShadow: '0 2px 6px rgba(0,0,0,0.06)',
            }}
        />
    );
};

export default ReportSelector;
