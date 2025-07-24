// /components/Report/common/ReportSelector.tsx
import React from 'react';
import { Select } from 'antd';

import { REPORT_OPTIONS } from '@/constants/reportConfig/managementReportConfig';
import type { ReportKey } from '@/constants/reportConfig/managementReportConfig';

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
            options={REPORT_OPTIONS}
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
