// src/components/ui/ReportStepIndicator.tsx

import React, { useMemo } from "react";
import { Steps } from "antd";
import { useResponsive } from "@/shared";
import styles from "./ReportStepIndicator.module.css";

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
  const { isMobile, isTablet } = useResponsive();

  // ポリシー: custom-media.css に合わせて（Lean-3 ブレークポイント）
  // - モバイル（≤767）: 横・small・タイトルのみ（最小化）
  // - タブレット（768–1279）: 横・小・タイトルのみ（コンパクト）
  // - デスクトップ（≥1281）: 横・通常・タイトル+説明
  const compactItems = useMemo(() => {
    return isMobile || isTablet
      ? items.map((it) => ({ title: it.title }))
      : items;
  }, [isMobile, isTablet, items]);

  // サイズはモバイル・タブレットともに 'small'
  const stepSize: "small" | "default" =
    isMobile || isTablet ? "small" : "default";

  return (
    <div
      className={isMobile ? styles.mobileSteps : undefined}
      style={{
        background: "#fff",
        borderRadius: isMobile ? 16 : 32,
        padding: isMobile ? "4px 8px" : isTablet ? "8px 12px" : "16px 24px",
        boxShadow: "0 2px 6px rgba(0,0,0,0.04)",
        overflowX: isMobile ? "auto" : "hidden",
        overflowY: "hidden",
        WebkitOverflowScrolling: "touch",
      }}
    >
      <Steps
        current={currentStep}
        direction="horizontal"
        size={stepSize}
        progressDot={false}
        responsive={false}
        items={compactItems}
        style={{
          display: "flex",
          flexDirection: "row",
          flexWrap: "nowrap",
          whiteSpace: "nowrap",
          minWidth: isMobile ? "max-content" : "auto",
        }}
      />
    </div>
  );
};

export default ReportStepIndicator;
