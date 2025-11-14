/**
 * DailyActualsCard Component
 * 日次搬入量（実績）を表示するカード
 */

import React, { useState } from "react";
import { Card, Typography, Tooltip, Switch, Space } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend, Line, Cell } from "recharts";
import type { IsoDate } from "@/features/dashboard/ukeire/domain/types";
import { COLORS, FONT } from "@/features/dashboard/ukeire/domain/constants";
import { ChartFrame } from "@/features/dashboard/ukeire/shared/ui/ChartFrame";
import { SingleLineLegend } from "@/features/dashboard/ukeire/shared/ui/SingleLineLegend";
import { isSecondSunday } from "@/features/dashboard/ukeire/domain/services/calendarService";

export type DailyActualsCardProps = {
  chartData: {
    label: string;
    actual?: number;
    dateFull: IsoDate;
    prevMonth: number | null;
    prevYear: number | null;
    /** 営業カレンダーから取得した日付ステータス（business: 営業日, holiday: 日祝・予約営業日, closed: 休業日） */
    status?: "business" | "holiday" | "closed";
  }[];
  variant?: "standalone" | "embed";
};

export const DailyActualsCard: React.FC<DailyActualsCardProps> = ({ chartData, variant = "standalone" }) => {
  const [showPrevMonth, setShowPrevMonth] = useState(false);
  const [showPrevYear, setShowPrevYear] = useState(false);

  /**
   * 営業カレンダーのステータスから色を取得
   * フォールバック: ステータスがない場合は第2日曜・日曜で判定（後方互換性）
   */
  const colorForDate = (dateStr: string, status?: "business" | "holiday" | "closed") => {
    // 営業カレンダーのステータスがある場合は優先的に使用
    if (status === "business") return COLORS.business;
    if (status === "holiday") return COLORS.holiday;
    if (status === "closed") return COLORS.closed;
    
    // フォールバック: 旧ロジック（後方互換性のため残す）
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
                <Cell key={`cell-${idx}`} fill={colorForDate(entry.dateFull, entry.status)} />
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
                    { label: "通常営業日", color: COLORS.business },
                    { label: "予約営業日", color: COLORS.holiday },
                    { label: "休業日", color: COLORS.closed },
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
    <Card variant="outlined" size="small" styles={{ body: { padding: 12, height: "100%", display: "flex", flexDirection: "column", minHeight: 0 } }}>
      <Inner />
    </Card>
  );
};
