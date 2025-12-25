// src/components/ui/ReportStepIndicator.tsx

import React, { useMemo } from 'react';
import { Steps } from 'antd';
import { useResponsive } from '@/shared';

export type StepItem = {
  // ← ここでexportを明記
  title: string;
  description?: string;
};

type ReportStepIndicatorProps = {
  currentStep: number;
  items: StepItem[];
};

const ReportStepIndicator: React.FC<ReportStepIndicatorProps> = ({ currentStep, items }) => {
  const { isMobile, isTablet } = useResponsive();

  // ポリシー: custom-media.css に合わせて（Lean-3 ブレークポイント）
  // - モバイル（≤767）: 上位と同じ横・通常サイズ（縦に伸ばさない）
  // - タブレット（768–1279）: 横・小・タイトルのみ（コンパクト）
  // - デスクトップ（≥1281）: 横・通常・タイトル+説明
  const compactItems = useMemo(() => {
    return isTablet ? items.map((it) => ({ title: it.title })) : items;
  }, [isTablet, items]);

  // 縦表示はタブレット/モバイルともに無効化（常に横向きを維持）
  const isVertical = false;
  // サイズはタブレットのみ 'small'、それ以外は 'default'
  const stepSize: 'small' | 'default' = isTablet ? 'small' : 'default';
  // プログレスドットはモバイルでの省スペース表示を行わない（以前は isMobile）
  const showProgressDot = false;

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
        size={stepSize}
        progressDot={showProgressDot}
        responsive
        items={compactItems}
      />
    </div>
  );
};

export default ReportStepIndicator;
