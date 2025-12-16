/**
 * Condition Panel Component
 * 
 * 条件指定パネル（期間選択 + 営業担当者フィルター）
 */

import React from 'react';
import { Card, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import type { SalesRep } from '../../shared/domain/types';
import { PeriodSelectorForm } from '../../period-selector';
import { SalesRepFilter } from '../../sales-rep-filter';

type Props = {
    // Period Selection
    currentStart: Dayjs | null;
    currentEnd: Dayjs | null;
    previousStart: Dayjs | null;
    previousEnd: Dayjs | null;
    setCurrentStart: (date: Dayjs | null) => void;
    setCurrentEnd: (date: Dayjs | null) => void;
    setPreviousStart: (date: Dayjs | null) => void;
    setPreviousEnd: (date: Dayjs | null) => void;
    
    // Sales Rep Filter
    salesReps: SalesRep[];
    selectedSalesRepIds: string[];
    setSelectedSalesRepIds: (ids: string[]) => void;
    analysisStarted: boolean;
    
    // Actions
    onReset: () => void;
};

/**
 * 分析条件指定パネル
 * 
 * 期間選択と営業担当者フィルターをまとめたカードコンポーネント
 */
const ConditionPanel: React.FC<Props> = ({
    currentStart,
    currentEnd,
    previousStart,
    previousEnd,
    setCurrentStart,
    setCurrentEnd,
    setPreviousStart,
    setPreviousEnd,
    salesReps,
    selectedSalesRepIds,
    setSelectedSalesRepIds,
    analysisStarted,
    onReset,
}) => (
    <Card
        title='条件指定'
        variant="borderless"
        style={{
            boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
            marginBottom: 16,
            borderRadius: 16,
        }}
        styles={{
            header: {
                background: '#f0f5ff',
                fontWeight: 600,
                borderTopLeftRadius: 16,
                borderTopRightRadius: 16,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: 'clamp(13px, 0.9vw, 16px)',
                padding: 'clamp(12px, 1vw, 16px) clamp(16px, 1.2vw, 24px)',
            },
            body: {
                fontSize: 'clamp(12px, 0.85vw, 14px)',
                padding: 'clamp(16px, 1.2vw, 24px)',
            },
        }}
        extra={
            <Button
                type='primary'
                danger
                onClick={onReset}
                size='middle'
                icon={<ReloadOutlined />}
                style={{ fontWeight: 600 }}
            >
                リセット
            </Button>
        }
    >
        <PeriodSelectorForm
            currentStart={currentStart}
            currentEnd={currentEnd}
            previousStart={previousStart}
            previousEnd={previousEnd}
            setCurrentStart={setCurrentStart}
            setCurrentEnd={setCurrentEnd}
            setPreviousStart={setPreviousStart}
            setPreviousEnd={setPreviousEnd}
        />
        
        <div style={{ marginTop: 'clamp(16px, 1.2vw, 24px)' }}>
            <div style={{ marginBottom: 8, fontWeight: 600, fontSize: 'clamp(12px, 0.85vw, 14px)' }}>
                営業担当者フィルター
            </div>
            <SalesRepFilter
                salesReps={salesReps}
                selectedSalesRepIds={selectedSalesRepIds}
                onChange={setSelectedSalesRepIds}
                disabled={!analysisStarted}
            />
        </div>
    </Card>
);

export default ConditionPanel;
