import React, { useMemo } from 'react';
import { Steps } from 'antd';
import { useDeviceType } from '@/hooks/useResponsive';

export type StepItem = {
    title: string;
    description?: string;
};

type ReportStepIndicatorProps = {
    currentStep: number;
    items: StepItem[];
};

const ReportStepIndicator: React.FC<ReportStepIndicatorProps> = ({
    currentStep,
    items,
}) => {
    const { isMobileOrTablet } = useDeviceType();

    const compactItems = useMemo(
        () =>
            isMobileOrTablet
                ? items.map((it) => ({ title: it.title }))
                : items,
        [isMobileOrTablet, items]
    );

    return (
        <div
            style={{
                background: '#fff',
                borderRadius: 32,
                padding: isMobileOrTablet ? '8px 12px' : '16px 24px',
                boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
            }}
        >
            <Steps
                current={currentStep}
                direction={isMobileOrTablet ? 'vertical' : 'horizontal'}
                size={isMobileOrTablet ? 'small' : 'default'}
                progressDot={isMobileOrTablet}
                responsive
                items={compactItems}
            />
        </div>
    );
};

export default ReportStepIndicator;
