import React from 'react';
import { Select } from 'antd';
import type { SalesRep } from '../../shared/domain/types';

type Props = {
    salesReps: SalesRep[];
    selectedSalesRepIds: string[];
    onChange: (ids: string[]) => void;
    disabled?: boolean;
};

/**
 * Sales Rep Filter Component
 * 
 * 営業担当者フィルター
 */
const SalesRepFilter: React.FC<Props> = ({
    salesReps,
    selectedSalesRepIds,
    onChange,
    disabled = false,
}) => (
    <Select
        mode="multiple"
        placeholder="営業担当者で絞り込み（未選択時は全員）"
        value={selectedSalesRepIds}
        onChange={onChange}
        disabled={disabled}
        style={{ width: '100%' }}
        allowClear
        showSearch
        filterOption={(input, option) =>
            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
        }
        options={salesReps.map(rep => ({
            value: rep.salesRepId,
            label: rep.salesRepName,
        }))}
    />
);

export default SalesRepFilter;
