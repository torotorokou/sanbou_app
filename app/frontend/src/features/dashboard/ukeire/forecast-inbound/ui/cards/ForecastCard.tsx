/**
 * ForecastCard Component
 * 搬入量予測を表示するカード（簡略版）
 */

import React, { useState } from "react";
import { Card, Space, Typography, Tooltip, Row, Col, Tabs, Progress, Switch } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import { ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend, Area, AreaChart } from "recharts";
import { COLORS, FONT } from "@/features/dashboard/ukeire/domain/constants";
import { ChartFrame } from "@/features/dashboard/ukeire/shared/ui/ChartFrame";
import { SingleLineLegend } from "@/features/dashboard/ukeire/shared/ui/SingleLineLegend";
import { clamp } from "@/features/dashboard/ukeire/domain/valueObjects";
import { useInstallTabsFillCSS } from "@/features/dashboard/ukeire/shared/styles/useInstallTabsFillCSS";
import { WipNotice } from "@/features/wip-notice";
import dayjs from "dayjs";
import isoWeekPlugin from "dayjs/plugin/isoWeek";
// レスポンシブ判定は Page 側へ移譲したため、ここではフックを使わない

export type KPIBlockProps = {
  title: string;
  p50: number;
  p10: number;
  p90: number;
  target: number | null;
  // 実測値（任意）: 表示を "予測/実測" にする場合に使用
  actual?: number | null;
  // 将来的にはバックグラウンドから渡す想定。なければコンポーネント内で計算する
  isoWeek?: number;
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
  oddDayTicks: string[];
  /**
   * レイアウト判定は Page 側で行う（責務の分離）。
   * true = width >= 768px（デスクトップ/タブレットの広い表示）
   * undefined の場合は既存のデスクトップ挙動を維持する（保守性目的）。
   */
  isGeMd?: boolean;
  // 将来的にはバックグラウンドから取得する想定
  isoWeek?: number;
  /**
   * 未完成機能の警告バナーを表示するかどうか
   * true = 表示、false または undefined = 非表示
   */
  showWipNotice?: boolean;
};

const KPIBlock: React.FC<KPIBlockProps> = ({ title, p50, p10, p90, target, actual, isoWeek }) => {
  // 新仕様: 可能であれば予測(p50)/実測(actual)を達成率として表示する
  const ratio = typeof actual === "number" && actual > 0 ? p50 / actual : (target ? p50 / target : null);
  const pct = ratio != null ? Math.round(ratio * 100) : null;
  const pctColor = ratio == null ? "#8c8c8c" : ratio >= 1 ? COLORS.ok : ratio >= 0.9 ? COLORS.warn : COLORS.danger;

  return (
    <Card size="small" styles={{ body: { padding: 12, height: "100%", display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } }}>
      <div style={{ height: "100%", display: "grid", gridTemplateColumns: "auto 1fr auto", alignItems: "center", gap: 8 }}>
        <div style={{ textAlign: "left", paddingLeft: 4 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#2b2b2b" }}>
            {(() => {
              const isThisWeek = title != null && String(title).startsWith("今週");
              if (isThisWeek && typeof isoWeek === "number") {
                const w = String(isoWeek).padStart(2, "0");
                return <>{title} <span style={{ color: "#8c8c8c", fontWeight: 700 }}>(W{w})</span></>;
              }
              return <>{title}</>;
            })()}
          </div>
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
              <Progress 
                type="line" 
                percent={clamp(pct, 0, 200)} 
                showInfo={false} 
                strokeColor={pctColor} 
                size={["100%", 8]}
                style={{ width: "100%" }}
              />
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

// Mobile専用の横長KPIブロック（1行で全情報を表示）
type MobileKPIBlockProps = KPIBlockProps & { achievementPct?: number };
const MobileKPIBlock: React.FC<MobileKPIBlockProps> = ({ title, p50, p10, p90, target, achievementPct, isoWeek }) => {
  const ratio = target ? p50 / target : null;
  const pctByTarget = ratio != null ? Math.round(ratio * 100) : null;
  // achievementPct が渡されたら優先して表示（モバイル用）。なければ目标ベースのpctを表示
  const displayPct = typeof achievementPct === "number" ? achievementPct : pctByTarget;
  const pctColor = displayPct == null ? "#8c8c8c" : displayPct >= 100 ? COLORS.ok : displayPct >= 90 ? COLORS.warn : COLORS.danger;

  return (
    <Card size="small" styles={{ body: { padding: "6px 10px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 6 } }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: "#2b2b2b", whiteSpace: "nowrap" }}>
        {(() => {
          const isThisWeek = title != null && String(title).startsWith("今週");
          if (isThisWeek && typeof isoWeek === "number") {
            const w = String(isoWeek).padStart(2, "0");
            return <>{title} <span style={{ color: "#8c8c8c", fontWeight: 700 }}>(W{w})</span></>;
          }
          return <>{title}</>;
        })()}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, flex: 1, justifyContent: "center" }}>
        <div style={{ fontSize: 15, fontWeight: 900, color: COLORS.primary }}>
          {p50.toLocaleString()}
          <span style={{ fontSize: 10, fontWeight: 700 }}>t</span>
        </div>
        <div style={{ fontSize: 9, color: "#8c8c8c", whiteSpace: "nowrap" }}>
          ({p10}–{p90}t)
        </div>
      </div>
      <div style={{ minWidth: 112, display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
        {displayPct != null ? (
          <>
            <div style={{ textAlign: "center", color: pctColor, fontWeight: 700, fontSize: 11 }}>{displayPct}%</div>
            <div style={{ width: 96, marginTop: 6 }}>
              <Progress 
                type="line" 
                percent={clamp(displayPct, 0, 200)} 
                showInfo={false} 
                strokeColor={pctColor} 
                size={["100%", 6]}
                style={{ width: "100%" }}
              />
            </div>
          </>
        ) : (
          <div style={{ color: "#8c8c8c", fontSize: 9 }}>―</div>
        )}
      </div>
    </Card>
  );
};

// カスタムツールチップ: 累積グラフ用に実績と予測の差分（%）を表示する
const CumTooltip: React.FC<{ active?: boolean; payload?: unknown; label?: string }> = ({ active, payload, label }) => {
  if (!active) return null;
  if (!payload || !Array.isArray(payload)) return null;
  const arr = payload as Array<Record<string, unknown>>;
  const findByKey = (k: string) => arr.find((p) => p && typeof p === "object" && (p as Record<string, unknown>)["dataKey"] === k) as Record<string, unknown> | undefined;
  const cumDailyObj = findByKey("cumDaily");
  const cumActualObj = findByKey("cumActual");
  const parseVal = (o?: Record<string, unknown>) => {
    if (!o) return null as number | null;
    const v = o["value"];
    if (typeof v === "number") return v;
    if (typeof v === "string" && v.trim() !== "") {
      const n = Number(v);
      return Number.isFinite(n) ? n : null;
    }
    return null;
  };
  const cumDaily = parseVal(cumDailyObj);
  const cumActual = parseVal(cumActualObj);

  // 新仕様: ((予測 - 実績) / 実績) * 100 を表示。実績が 0 または null の場合は表示しない。
  const diffPct = cumActual != null && cumActual !== 0 && cumDaily != null ? Math.round(((cumDaily - cumActual) / cumActual) * 100) : null;

  return (
    <div style={{ background: "rgba(255,255,255,0.98)", padding: 8, borderRadius: 6, boxShadow: "0 1px 4px rgba(0,0,0,0.12)", fontSize: 12 }}>
      <div style={{ color: "#8c8c8c", marginBottom: 6 }}>{label}</div>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
        <div style={{ color: "#fa8c16" }}>予測累積</div>
        <div style={{ fontWeight: 700 }}>{cumDaily != null ? `${cumDaily}t` : "―"}</div>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginTop: 6 }}>
        <div style={{ color: COLORS.ok }}>実績累積</div>
        <div style={{ fontWeight: 700 }}>{cumActual != null ? `${cumActual}t` : "―"}</div>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginTop: 6 }}>
        <div style={{ color: "#595959" }}>誤差</div>
        <div style={{ fontWeight: 700, color: diffPct == null ? "#8c8c8c" : diffPct >= 0 ? COLORS.danger : COLORS.ok }}>
          {diffPct == null ? "―" : `${diffPct > 0 ? "+" : ""}${diffPct}%`}
        </div>
      </div>
    </div>
  );
};

export const ForecastCard: React.FC<ForecastCardProps> = ({ kpis, chartData, cumData, oddDayTicks, isGeMd, isoWeek, showWipNotice = false }) => {
  const tabsClass = useInstallTabsFillCSS();
  const [showActual, setShowActual] = useState(true);
  const [showForward, setShowForward] = useState(true);
  const [showReverse, setShowReverse] = useState(true);
  const [showCumReverse, setShowCumReverse] = useState(true);
  const [showCumActual, setShowCumActual] = useState(true);

  // Mobile モードでは padding を小さく
  const cardPadding = isGeMd ? 12 : 8;
  const cardGap = isGeMd ? 8 : 6;

  // isoWeek: propsがあれば優先、なければ今日から計算（将来的にはバックエンドから渡す想定）
  dayjs.extend(isoWeekPlugin);
  const isoWeekToShow: number = typeof isoWeek === "number" ? isoWeek : dayjs().isoWeek();

  // --- Mobile 向け: 当日/今週合計/今月末 の達成率を算出 ---
  // 前提（仮定）:
  // - 日目標は `monthTarget / daysInMonth` として推定
  // - 当日は chartData の最終要素の actual を優先、なければ dailyForward/ daily を使用
  // - 今週合計は chartData の末尾7要素の合計を使用
  // 実測値ベースでの達成率（予測 / 実測）を各カードに渡すための準備
  const latestPoint = chartData && chartData.length ? chartData[chartData.length - 1] : null;
  const todayActual = latestPoint
    ? (typeof latestPoint.actual === "number"
        ? latestPoint.actual
        : (typeof latestPoint.dailyForward === "number" ? latestPoint.dailyForward : (typeof latestPoint.daily === "number" ? latestPoint.daily : null)))
    : null;
  const weekSum = chartData && chartData.length ? chartData.slice(-7).reduce((s, d) => s + (typeof d.actual === "number" ? d.actual : (typeof d.daily === "number" ? d.daily : (typeof d.dailyForward === "number" ? d.dailyForward : 0))), 0) : 0;
  const cumActualLast = cumData && cumData.length ? cumData[cumData.length - 1].cumActual : null;
  const actualsForKpis: Array<number | null> = [todayActual, weekSum || null, cumActualLast];

  return (
    <Card
      variant="outlined"
      style={{ height: "100%", display: "flex", flexDirection: "column" }}
      styles={{ body: { padding: cardPadding, display: "flex", flexDirection: "column", gap: cardGap, flex: 1, minHeight: 0 } }}
    >
      {/* 未完成機能の警告バナー */}
      <WipNotice show={showWipNotice} />

      <Space align="baseline" style={{ justifyContent: "space-between", width: "100%" }}>
        <Typography.Title level={5} style={{ margin: 0 }}>
          搬入量予測（P50 / P10–P90）
        </Typography.Title>
        <Tooltip title="P帯はモデル残差から推定（本番）。ここではデモ値。">
          <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
        </Tooltip>
      </Space>

      <div style={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
        {isGeMd ? (
          // Desktop/Laptop: KPI左、グラフ右
          <Row gutter={[8, 8]} style={{ height: "100%" }}>
            <Col span={8} style={{ height: "100%" }}>
              <div style={{ height: "100%", display: "grid", gridTemplateRows: "1fr 1fr 1fr", gap: 6 }}>
                {kpis.map((kpi, i) => {
                  const actual = actualsForKpis[i] ?? undefined;
                  return <KPIBlock key={i} {...kpi} actual={actual} isoWeek={isoWeekToShow} />;
                })}
              </div>
            </Col>
            <Col span={16} style={{ height: "100%", display: "flex", flexDirection: "column", minHeight: 0 }}>
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
                            <RTooltip content={<CumTooltip />} />
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
                            {/* 週ごとの参考線と月末予測の水平ラインは非表示に変更 */}
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
        ) : (
          // Mobile: KPI上段3行、グラフ下段全幅（コンパクト表示）
          // KPI を小さく詰めてグラフにより多く縦スペースを割り当てる（カード内に収める）
          <div style={{ display: "flex", flexDirection: "column", height: "100%", gap: 4 }}>
            {/* KPI: 縦積み3行（横長ブロック） - 各KPIは固定高さで詰める */}
            <div style={{ display: "flex", flexDirection: "column", gap: 3, flex: "0 0 auto" }}>
              {kpis.map((kpi, i) => {
                const actual = actualsForKpis[i] ?? undefined;
                const achievementPct = typeof actual === "number" && actual > 0 ? Math.round((kpi.p50 / actual) * 100) : undefined;
                // 各KPIブロックを固定高さのラッパーで包んで縦を小さく保つ
                return (
                  <div key={i} style={{ height: 56, minHeight: 56, maxHeight: 56, overflow: "hidden" }}>
                    <MobileKPIBlock {...kpi} actual={actual} achievementPct={achievementPct} isoWeek={isoWeekToShow} />
                  </div>
                );
              })}
            </div>
            {/* グラフ: KPIより大きめの縦幅を確保（カード内で収まるようflexで割り当て） */}
            <div style={{ flex: 2, minHeight: 0 }}>
              <Tabs
                size="small"
                className={tabsClass}
                tabBarStyle={{ padding: "0 8px", minHeight: 28, height: 28, fontSize: 13 }}
                style={{ height: "100%", display: "flex", flexDirection: "column" }}
                items={[
                  {
                    key: "reverse",
                    label: "日次",
                    children: (
                      <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
                        <div style={{ display: "flex", justifyContent: "flex-end", gap: 6, padding: "2px 0", flexWrap: "wrap" }}>
                          <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                            <Switch size="small" checked={showActual} onChange={setShowActual} />
                            <span style={{ fontSize: 11 }}>実績</span>
                          </div>
                          <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                            <Switch size="small" checked={showForward} onChange={setShowForward} />
                            <span style={{ fontSize: 11 }}>フロント</span>
                          </div>
                          <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                            <Switch size="small" checked={showReverse} onChange={setShowReverse} />
                            <span style={{ fontSize: 11 }}>バック</span>
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
                        <div style={{ display: "flex", justifyContent: "flex-end", gap: 6, padding: "2px 0", flexWrap: "wrap" }}>
                          <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                            <Switch size="small" checked={showCumReverse} onChange={setShowCumReverse} />
                            <span style={{ fontSize: 11 }}>バック累積</span>
                          </div>
                          <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                            <Switch size="small" checked={showCumActual} onChange={setShowCumActual} />
                            <span style={{ fontSize: 11 }}>実績累積</span>
                          </div>
                        </div>
                        <div style={{ flex: 1, minHeight: 0 }}>
                          <ChartFrame style={{ flex: 1, minHeight: 0 }}>
                            <AreaChart data={cumData} margin={{ left: 0, right: 8, top: 6, bottom: 12 }}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="label" ticks={oddDayTicks} fontSize={FONT.size} />
                              <YAxis unit="t" domain={[0, "auto"]} fontSize={FONT.size} />
                              <RTooltip content={<CumTooltip />} />
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
                              {/* 週ごとの参考線と月末予測の水平ラインは非表示に変更 */}
                            </AreaChart>
                          </ChartFrame>
                        </div>
                      </div>
                    ),
                  },
                ]}
              />
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
