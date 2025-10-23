/**
 * CombinedDailyCard Component
 * 日次・累積をタブで切り替えるカード
 */

import React from "react";
import { Card, Tabs } from "antd";
import { DailyActualsCard, type DailyActualsCardProps } from "./DailyActualsCard";
import { DailyCumulativeCard, type DailyCumulativeCardProps } from "./DailyCumulativeCard";
import { useInstallTabsFillCSS } from "@/features/dashboard/ukeire/shared/styles/useInstallTabsFillCSS";
import tabsTight from "@/styles/tabsTight.module.css";

export type CombinedDailyCardProps = {
  dailyProps: DailyActualsCardProps;
  cumulativeProps: DailyCumulativeCardProps;
  style?: React.CSSProperties;
};

export const CombinedDailyCard: React.FC<CombinedDailyCardProps> = ({ dailyProps, cumulativeProps, style }) => {
  const tabsClass = useInstallTabsFillCSS();

  return (
    <Card
      bordered
      size="small"
      style={{ height: "100%", display: "flex", flexDirection: "column", ...(style || {}) }}
      bodyStyle={{ padding: 12, flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}
    >
      <Tabs
        size="small"
        className={`${tabsClass} ${tabsTight.root}`}
        tabBarStyle={{ padding: "4px 8px", minHeight: 26, height: 26, fontSize: 13, marginBottom: 0 }}
        style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}
        items={[
          {
            key: "daily",
            label: "日次",
            children: (
              <div style={{ height: "100%", minHeight: 0 }}>
                <DailyActualsCard {...dailyProps} variant="embed" />
              </div>
            ),
          },
          {
            key: "cumulative",
            label: "累積",
            children: (
              <div style={{ height: "100%", minHeight: 0 }}>
                <DailyCumulativeCard {...cumulativeProps} variant="embed" />
              </div>
            ),
          },
        ]}
      />
    </Card>
  );
};
