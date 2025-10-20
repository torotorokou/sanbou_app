/**
 * DailyActualsCard Component
 * 日次搬入量（実績）を表示するカード
 */

import React, { useState } from "react";
import { Card, Typography, Tooltip, Switch, Space } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend, Line, Cell } from "recharts";
import type { IsoDate } from "../../model/types";
import { COLORS, FONT } from "../../model/constants";
import { ChartFrame } from "../components/ChartFrame";
import { SingleLineLegend } from "../components/SingleLineLegend";
import { isSecondSunday } from "../../model/services/calendarService";

export type DailyActualsCardProps = {
  chartData: {
    label: string;
    actual?: number;
    dateFull: IsoDate;
    prevMonth: number | null;
    prevYear: number | null;
  }[];
  variant?: "standalone" | "embed";
};

export const DailyActualsCard: React.FC<DailyActualsCardProps> = ({ chartData, variant = "standalone" }) => {
  const [showPrevMonth, setShowPrevMonth] = useState(false);
  const [showPrevYear, setShowPrevYear] = useState(false);

  const colorForDate = (dateStr: string) => {
    if (isSecondSunday(dateStr)) return COLORS.danger;
    const d = dayjs(dateStr);
    if (d.day() === 0) return COLORS.sunday;
    return COLORS.ok;
  };

  const Inner = () => (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "space-between", padding: "0 0 4px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Typography.Title level={5} style={{ margin: 0, fontSize: 13 }}>
            日次搬入量（実績）
          </Typography.Title>
          <Tooltip title="実際に搬入された日次トン数（モック）。">
            <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
          </Tooltip>
        </div>
        <Space size="small">
          <span style={{ color: "#8c8c8c" }}>先月</span>
          <Switch size="small" checked={showPrevMonth} onChange={setShowPrevMonth} />
          <span style={{ color: "#8c8c8c" }}>前年</span>
          <Switch size="small" checked={showPrevYear} onChange={setShowPrevYear} />
        </Space>
      </div>

      <div style={{ flex: 1, minHeight: 0 }}>
        <ChartFrame style={{ flex: 1, minHeight: 0 }}>
          <BarChart data={chartData} margin={{ left: 0, right: 8, top: 6, bottom: 12 }}>
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
            <YAxis unit="t" fontSize={FONT.size} />
            <RTooltip
              contentStyle={{ fontSize: FONT.size }}
              formatter={(...args) => {
                const [v, name, payloadItem] = args as unknown as [unknown, unknown, { payload?: Record<string, unknown> }?];
                const map: Record<string, string> = { actual: "実績", prevMonth: "先月", prevYear: "前年" };
                const key = name == null ? "" : String(name);
                const label = key ? map[key] || key : "";
                const p = payloadItem && payloadItem.payload ? payloadItem.payload : null;
                let actualVal: number | null = null;
                if (p && typeof p === "object" && "actual" in p) {
                  const a = (p as Record<string, unknown>)["actual"];
                  if (typeof a === "number") actualVal = a;
                  else if (typeof a === "string" && !Number.isNaN(Number(a))) actualVal = Number(a);
                }
                if (v == null || v === "" || Number.isNaN(Number(v))) return ["—", label];
                const valNum = Number(v);
                if ((key === "prevMonth" || key === "prevYear") && actualVal != null && actualVal !== 0) {
                  const diffPct = ((valNum - actualVal) / actualVal) * 100;
                  const sign = diffPct >= 0 ? "+" : "-";
                  const absPct = Math.abs(diffPct).toFixed(1);
                  return [`${valNum}t (${sign}${absPct}%)`, label];
                }
                return [`${valNum}t`, label];
              }}
            />
            <Bar dataKey="actual">
              {chartData.map((entry, idx) => (
                <Cell key={`cell-${idx}`} fill={colorForDate(entry.dateFull)} />
              ))}
            </Bar>
            {showPrevMonth && <Line type="monotone" dataKey="prevMonth" stroke="#40a9ff" dot={false} strokeWidth={2} />}
            {showPrevYear && <Line type="monotone" dataKey="prevYear" stroke="#fa8c16" dot={false} strokeWidth={2} />}
            <Legend
              verticalAlign="bottom"
              content={(props: unknown) => (
                <SingleLineLegend
                  {...(props as Parameters<typeof SingleLineLegend>[0])}
                  extraStatic={[
                    { label: "営業", color: COLORS.ok },
                    { label: "日祝", color: COLORS.sunday },
                    { label: "休業", color: COLORS.danger },
                  ]}
                />
              )}
            />
          </BarChart>
        </ChartFrame>
      </div>
    </div>
  );

  if (variant === "embed") return <Inner />;
  return (
    <Card bordered size="small" bodyStyle={{ padding: 12, height: "100%", display: "flex", flexDirection: "column", minHeight: 0 }}>
      <Inner />
    </Card>
  );
};
