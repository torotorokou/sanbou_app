import React from 'react';
import { Steps } from 'antd';

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
}) => (
    <div
        style={{
            background: '#fff',
            borderRadius: 32,
            padding: '16px 24px',
            boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
        }}
    >
        <Steps current={currentStep} responsive={false} items={items} />
    </div>
);

export default ReportStepIndicator;
