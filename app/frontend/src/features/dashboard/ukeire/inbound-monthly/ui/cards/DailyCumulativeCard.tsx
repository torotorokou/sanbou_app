/**
 * DailyCumulativeCard Component
 * 日次累積搬入量を表示するカード
 */

import React, { useState } from "react";
import { Card, Typography, Space, Switch } from "antd";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend, Line } from "recharts";
import { COLORS, FONT } from "@/features/dashboard/ukeire/domain/constants";
import { ChartFrame } from "@/features/dashboard/ukeire/shared/ui/ChartFrame";
import { SingleLineLegend } from "@/features/dashboard/ukeire/shared/ui/SingleLineLegend";

export type DailyCumulativeCardProps = {
  cumData: {
    label: string;
    yyyyMMdd: string;
    actualCumulative: number;
    prevMonthCumulative: number;
    prevYearCumulative: number;
  }[];
  variant?: "standalone" | "embed";
};

export const DailyCumulativeCard: React.FC<DailyCumulativeCardProps> = ({ cumData, variant = "standalone" }) => {
  const [showPrevMonth, setShowPrevMonth] = useState(false);
  const [showPrevYear, setShowPrevYear] = useState(false);

  const tooltipFormatter = (...args: unknown[]) => {
    const [v, name, payloadItem] = args as [unknown, unknown, { payload?: Record<string, unknown> }?];
    const map: Record<string, string> = {
      actualCumulative: "累積実績",
      prevMonthCumulative: "先月累積",
      prevYearCumulative: "前年累積",
    };
    const key = name == null ? "" : String(name);
    const label = key ? map[key] || key : "";
    const payload = payloadItem && payloadItem.payload ? payloadItem.payload : null;
    let actualCum: number | null = null;
    if (payload && typeof payload === "object" && "actualCumulative" in payload) {
      const a = (payload as Record<string, unknown>)["actualCumulative"];
      if (typeof a === "number") actualCum = a;
      else if (typeof a === "string" && !Number.isNaN(Number(a))) actualCum = Number(a);
    }
    if (v == null || v === "" || Number.isNaN(Number(v))) return ["—", label];
    const valNum = Number(v);
    if ((key === "prevMonthCumulative" || key === "prevYearCumulative") && actualCum != null && actualCum !== 0) {
      const diffPct = ((valNum - actualCum) / actualCum) * 100;
      const sign = diffPct >= 0 ? "+" : "-";
      const absPct = Math.abs(diffPct).toFixed(1);
      return [`${valNum}t (${sign}${absPct}%)`, label];
    }
    return [`${valNum}t`, label];
  };

  const Inner = () => (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      <Space align="baseline" style={{ justifyContent: "space-between", width: "100%", paddingBottom: 4 }}>
        <Typography.Title level={5} style={{ margin: 0, fontSize: 13 }}>
          日次累積搬入量（累積）
        </Typography.Title>
        <Space size="small">
          <span style={{ color: "#8c8c8c" }}>先月累積</span>
          <Switch size="small" checked={showPrevMonth} onChange={setShowPrevMonth} />
          <span style={{ color: "#8c8c8c" }}>前年累積</span>
          <Switch size="small" checked={showPrevYear} onChange={setShowPrevYear} />
        </Space>
      </Space>

      <div style={{ flex: 1, minHeight: 0 }}>
        <ChartFrame style={{ flex: 1, minHeight: 0 }}>
          <AreaChart data={cumData} margin={{ left: 0, right: 8, top: 6, bottom: 12 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="label"
              interval={0}
              tickFormatter={(v) => {
                const n = Number(String(v));
                if (Number.isNaN(n)) return String(v);
                return n % 2 === 1 ? String(v) : "";
              }}
              fontSize={FONT.size}
            />
            <YAxis unit="t" domain={[0, "auto"]} fontSize={FONT.size} />
            <RTooltip contentStyle={{ fontSize: FONT.size }} formatter={tooltipFormatter} />
            <Area type="monotone" dataKey="actualCumulative" stroke={COLORS.actual} fill={COLORS.actual} fillOpacity={0.2} />
            {showPrevMonth && (
              <Line type="monotone" dataKey="prevMonthCumulative" name="先月累積" stroke="#40a9ff" dot={false} strokeWidth={2} />
            )}
            {showPrevYear && (
              <Line type="monotone" dataKey="prevYearCumulative" name="前年累積" stroke="#fa8c16" dot={false} strokeWidth={2} />
            )}
            <Legend content={(props: unknown) => <SingleLineLegend {...(props as Parameters<typeof SingleLineLegend>[0])} />} verticalAlign="bottom" />
          </AreaChart>
        </ChartFrame>
      </div>
    </div>
  );

  if (variant === "embed") return <Inner />;
  return (
    <Card bordered bodyStyle={{ padding: 12, height: "100%", display: "flex", flexDirection: "column", minHeight: 0 }}>
      <Inner />
    </Card>
  );
};
