// src/components/ui/ReportStepIndicator.tsx

import React, { useMemo } from 'react';
import { Steps } from 'antd';
import { useWindowSize } from '@/hooks/ui';

export type StepItem = {
    // ← ここでexportを明記
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
    const { isMobile, isTablet } = useWindowSize();

    // ポリシー: responsive.css に合わせて
    // - モバイル（<=767）: 縦・小・タイトルのみ
    // - タブレット（768–1279）: 横・小・タイトルのみ（コンパクト）
    // - デスクトップ（>=1280）: 横・通常・タイトル+説明
    const compactItems = useMemo(() => {
        return isMobile || isTablet
            ? items.map((it) => ({ title: it.title }))
            : items;
    }, [isMobile, isTablet, items]);

    const isVertical = isMobile;
    const stepSize = isMobile || isTablet ? 'small' : 'default';
    const showProgressDot = isMobile;

    return (
        <div
            style={{
                background: '#fff',
                borderRadius: 32,
                padding: isMobile || isTablet ? '8px 12px' : '16px 24px',
                boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
            }}
        >
            <Steps
                current={currentStep}
                direction={isVertical ? 'vertical' : 'horizontal'}
                size={stepSize as any}
                progressDot={showProgressDot}
                responsive
                items={compactItems}
            />
        </div>
    );
};

export default ReportStepIndicator;
