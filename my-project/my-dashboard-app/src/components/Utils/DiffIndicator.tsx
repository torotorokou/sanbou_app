// src/components/Utils/DiffIndicator.tsx
import React from 'react';
import { RiseOutlined, FallOutlined } from '@ant-design/icons';

interface DiffIndicatorProps {
    diff: number;
    unit?: string;
}

const DiffIndicator: React.FC<DiffIndicatorProps> = ({ diff, unit = '' }) => {
    if (diff > 0) {
        return (
            <span style={{ color: '#3f8600', fontSize: '0.85rem' }}>
                <RiseOutlined /> 前日比 +{diff}
                {unit}
            </span>
        );
    } else if (diff < 0) {
        return (
            <span style={{ color: '#cf1322', fontSize: '0.85rem' }}>
                <FallOutlined /> 前日比 {diff}
                {unit}
            </span>
        );
    } else {
        return (
            <span style={{ color: '#8c8c8c', fontSize: '0.85rem' }}>
                変化なし
            </span>
        );
    }
};

export default DiffIndicator;
