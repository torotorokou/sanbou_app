/**
 * ForecastCard Component
 * 搬入量予測を表示するカード（簡略版）
 */

import React, { useState } from "react";
import { Card, Space, Typography, Tooltip, Row, Col, Tabs, Progress, Switch } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import { ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend, Area, AreaChart, ReferenceLine } from "recharts";
import { COLORS, FONT } from "@/features/dashboard/ukeire/domain/constants";
import { ChartFrame } from "@/features/dashboard/ukeire/shared/ui/ChartFrame";
import { SingleLineLegend } from "@/features/dashboard/ukeire/shared/ui/SingleLineLegend";
import { clamp } from "@/features/dashboard/ukeire/domain/valueObjects";
import { useInstallTabsFillCSS } from "@/features/dashboard/ukeire/shared/styles/useInstallTabsFillCSS";

export type KPIBlockProps = {
  title: string;
  p50: number;
  p10: number;
  p90: number;
  target: number | null;
};

export type ForecastCardProps = {
  kpis: KPIBlockProps[];
  chartData: {
    label: string;
    daily: number;
    dailyForward?: number;
    actual?: number;
  }[];
  cumData: {
    label: string;
    cumDaily: number;
    cumActual: number;
  }[];
  monthTarget: number;
  daysInMonth: number;
  oddDayTicks: string[];
  forecastP50: number;
};

const KPIBlock: React.FC<KPIBlockProps> = ({ title, p50, p10, p90, target }) => {
  const ratio = target ? p50 / target : null;
  const pct = ratio != null ? Math.round(ratio * 100) : null;
  const pctColor = ratio == null ? "#8c8c8c" : ratio >= 1 ? COLORS.ok : ratio >= 0.9 ? COLORS.warn : COLORS.danger;

  return (
    <Card size="small" bodyStyle={{ padding: 12, height: "100%", display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ height: "100%", display: "grid", gridTemplateColumns: "auto 1fr auto", alignItems: "center", gap: 8 }}>
        <div style={{ textAlign: "left", paddingLeft: 4 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#2b2b2b" }}>{title}</div>
        </div>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 18, fontWeight: 900, color: COLORS.primary }}>
              {p50.toLocaleString()}
              <span style={{ fontSize: 13, fontWeight: 700 }}>t</span>
            </div>
            <div style={{ fontSize: 11, color: "#8c8c8c" }}>
              レンジ: {p10}–{p90}
              <span style={{ fontSize: 10 }}>t</span>
            </div>
          </div>
        </div>
        <div style={{ width: 92, display: "flex", flexDirection: "column", alignItems: "center" }}>
          {pct != null ? (
            <>
              <Progress percent={clamp(pct, 0, 200)} showInfo={false} strokeColor={pctColor} strokeWidth={8} />
              <div style={{ textAlign: "center", marginTop: 4, color: pctColor, fontWeight: 700, fontSize: 12 }}>
                {pct}%
              </div>
            </>
          ) : (
            <div style={{ color: "#8c8c8c", textAlign: "center", fontSize: 12 }}>目標不明</div>
          )}
        </div>
      </div>
    </Card>
  );
};

export const ForecastCard: React.FC<ForecastCardProps> = ({ kpis, chartData, cumData, monthTarget, daysInMonth, oddDayTicks, forecastP50 }) => {
  const tabsClass = useInstallTabsFillCSS();
  const [showActual, setShowActual] = useState(true);
  const [showForward, setShowForward] = useState(true);
  const [showReverse, setShowReverse] = useState(true);
  const [showCumReverse, setShowCumReverse] = useState(true);
  const [showCumActual, setShowCumActual] = useState(true);

  return (
    <Card
      bordered
      style={{ height: "100%", display: "flex", flexDirection: "column" }}
      bodyStyle={{ padding: 12, display: "flex", flexDirection: "column", gap: 8, flex: 1, minHeight: 0 }}
    >
      <Space align="baseline" style={{ justifyContent: "space-between", width: "100%" }}>
        <Typography.Title level={5} style={{ margin: 0 }}>
          搬入量予測（P50 / P10–P90）
        </Typography.Title>
        <Tooltip title="P帯はモデル残差から推定（本番）。ここではデモ値。">
          <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
        </Tooltip>
      </Space>

      <div style={{ flex: 1, minHeight: 0 }}>
        <Row gutter={[8, 8]} style={{ height: "100%" }}>
          {/* KPI Blocks: モバイル（全幅）、デスクトップ（8/24列） */}
          <Col xs={24} xl={8} style={{ height: "100%" }}>
            <div style={{ height: "100%", display: "grid", gridTemplateRows: "1fr 1fr 1fr", gap: 6 }}>
              {kpis.map((kpi, i) => (
                <KPIBlock key={i} {...kpi} />
              ))}
            </div>
          </Col>

          {/* Chart Tabs: モバイル（全幅）、デスクトップ（16/24列） */}
          <Col xs={24} xl={16} style={{ height: "100%", display: "flex", flexDirection: "column", minHeight: 0 }}>
            <Tabs
              size="small"
              className={tabsClass}
              tabBarStyle={{ padding: "0 8px", minHeight: 28, height: 28, fontSize: 13 }}
              style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}
              items={[
                {
                  key: "reverse",
                  label: "日次",
                  children: (
                    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
                      <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, padding: "4px 0" }}>
                        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                          <Switch size="small" checked={showActual} onChange={setShowActual} />
                          <span style={{ fontSize: 12 }}>実績</span>
                        </div>
                        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                          <Switch size="small" checked={showForward} onChange={setShowForward} />
                          <span style={{ fontSize: 12 }}>フロント予測</span>
                        </div>
                        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                          <Switch size="small" checked={showReverse} onChange={setShowReverse} />
                          <span style={{ fontSize: 12 }}>バック予測</span>
                        </div>
                      </div>
                      <div style={{ flex: 1, minHeight: 0 }}>
                        <ChartFrame style={{ flex: 1, minHeight: 0 }}>
                          <ComposedChart
                            data={chartData}
                            barCategoryGap="0%"
                            barGap={0}
                            margin={{ left: 0, right: 8, top: 6, bottom: 12 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="label" ticks={oddDayTicks} fontSize={FONT.size} />
                            <YAxis yAxisId="left" unit="t" fontSize={FONT.size} />
                            <RTooltip
                              contentStyle={{ fontSize: FONT.size }}
                              formatter={(v: unknown, name: unknown) => {
                                const key = name == null ? "" : String(name);
                                const map: Record<string, string> = { actual: "実績", dailyForward: "フロント予測", daily: "バック予測" };
                                const display = map[key] ?? (key === "label" || key === "undefined" || key === "" ? "" : key);
                                const vs = String(v ?? "");
                                return display ? [`${vs}t`, display] : [`${vs}t`, ""];
                              }}
                            />
                            {showActual && <Bar dataKey="actual" name="実績" yAxisId="left" fill={COLORS.ok} stackId="a" barSize={18} maxBarSize={32} />}
                            {showForward && <Bar dataKey="dailyForward" name="フロント予測" yAxisId="left" fill={"#40a9ff"} stackId="a" barSize={18} maxBarSize={32} />}
                            {showReverse && <Area type="monotone" dataKey="daily" name="バック予測" yAxisId="left" stroke={"#fa8c16"} fill={"#fa8c16"} fillOpacity={0.12} dot={{ r: 2 }} />}
                            <Legend content={(props: unknown) => <SingleLineLegend {...(props as Parameters<typeof SingleLineLegend>[0])} />} verticalAlign="bottom" />
                          </ComposedChart>
                        </ChartFrame>
                      </div>
                    </div>
                  ),
                },
                {
                  key: "cumulative",
                  label: "累積",
                  children: (
                    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
                      <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, padding: "4px 0" }}>
                        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                          <Switch size="small" checked={showCumReverse} onChange={setShowCumReverse} />
                          <span style={{ fontSize: 12 }}>バック予測累積</span>
                        </div>
                        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                          <Switch size="small" checked={showCumActual} onChange={setShowCumActual} />
                          <span style={{ fontSize: 12 }}>実績累積</span>
                        </div>
                      </div>
                      <div style={{ flex: 1, minHeight: 0 }}>
                        <ChartFrame style={{ flex: 1, minHeight: 0 }}>
                          <AreaChart data={cumData} margin={{ left: 0, right: 8, top: 6, bottom: 12 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="label" ticks={oddDayTicks} fontSize={FONT.size} />
                            <YAxis unit="t" domain={[0, "auto"]} fontSize={FONT.size} />
                            <RTooltip
                              contentStyle={{ fontSize: FONT.size }}
                              formatter={(v: unknown, name: unknown) => {
                                const map: Record<string, string> = { cumDaily: "バック予測累積", cumActual: "実績累積" };
                                const key = name == null ? "" : String(name);
                                const vs = String(v ?? "");
                                return [`${vs}t`, map[key] ?? key];
                              }}
                            />
                            {showCumReverse && (
                              <Area
                                type="monotone"
                                dataKey="cumDaily"
                                name="バック予測累積"
                                stroke={"#fa8c16"}
                                fill={"#fa8c16"}
                                fillOpacity={0.2}
                                isAnimationActive={false}
                              />
                            )}
                            {showCumActual && (
                              <Area
                                type="monotone"
                                dataKey="cumActual"
                                name="実績累積"
                                stroke={COLORS.ok}
                                fill={COLORS.ok}
                                fillOpacity={0.2}
                                isAnimationActive={false}
                              />
                            )}
                            <Legend verticalAlign="bottom" height={16} />
                            {Array.from({ length: Math.ceil(daysInMonth / 7) }, (_, i) => {
                              const end = Math.min((i + 1) * 7, daysInMonth);
                              const cumTarget = Math.round((monthTarget / Math.ceil(daysInMonth / 7)) * (i + 1));
                              return (
                                <ReferenceLine
                                  key={`week-${i}`}
                                  x={String(end).padStart(2, "0")}
                                  stroke={COLORS.target}
                                  strokeDasharray="5 5"
                                  strokeWidth={2}
                                  label={({ viewBox }) => {
                                    const vb = viewBox as { x?: number; y?: number; width?: number } | null | undefined;
                                    const vx = vb && vb.x != null ? vb.x + (vb.width ?? 0) / 2 : undefined;
                                    const vy = vb && vb.y != null ? vb.y + 16 : undefined;
                                    return (
                                      <g>
                                        <rect
                                          x={(vx ?? 0) - 40}
                                          y={(vy ?? 0) - 18}
                                          width={80}
                                          height={18}
                                          rx={6}
                                          ry={6}
                                          fill="rgba(255,255,255,0.85)"
                                          stroke="rgba(0,0,0,0.06)"
                                        />
                                        <text
                                          x={vx}
                                          y={vy}
                                          textAnchor="middle"
                                          fill={COLORS.target}
                                          fontSize={12}
                                          fontWeight={700}
                                        >
                                          {`W${i + 1}: ${cumTarget}t`}
                                        </text>
                                      </g>
                                    );
                                  }}
                                />
                              );
                            })}
                            <ReferenceLine
                              y={forecastP50}
                              stroke={COLORS.primary}
                              strokeDasharray="3 3"
                              strokeWidth={2}
                              label={{
                                value: `月末予測: ${forecastP50}t`,
                                position: "right",
                                fill: COLORS.primary,
                                fontSize: 12,
                              }}
                            />
                          </AreaChart>
                        </ChartFrame>
                      </div>
                    </div>
                  ),
                },
              ]}
            />
          </Col>
        </Row>
      </div>
    </Card>
  );
};
