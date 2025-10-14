import React, { useEffect, useMemo, useRef, useState } from "react";
import CalendarGrid from "./components/calendar/CalendarGrid";
import dayjs from "dayjs";
import tabsTight from "@/styles/tabsTight.module.css";
import {
  Card,
  Row,
  Col,
  Typography,
  DatePicker,
  Space,
  Progress,
  Tabs,
  Skeleton,
  Badge,
  Tooltip,
  Statistic,
  Switch,
} from "antd";
import {
  BarChart,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RTooltip,
  ResponsiveContainer,
  Line,
  AreaChart,
  Area,
  Legend,
  ReferenceLine,
  Cell,
} from "recharts";
import { InfoCircleOutlined } from "@ant-design/icons";

/* ===================================================================
 * 搬入量予測ダッシュボード（1ページ=1画面、縦スクロールなし）
 * Tabs の高さ問題は CSS 側で強制的に 100% に
 * グラフは ChartFrame が親の実寸高さを測って渡す
 * =================================================================== */

/* =============== Tabs 高さ fix =============== */
const TABS_FILL_CLASS = "tabs-fill-100";
function useInstallTabsFillCSS() {
  useEffect(() => {
    const css = `
.${TABS_FILL_CLASS} { height:100%; display:flex; flex-direction:column; min-height:0; }
.${TABS_FILL_CLASS} .ant-tabs-content-holder,
.${TABS_FILL_CLASS} .ant-tabs-content {
  height:100%;
  display:flex;
  flex-direction:column;
  min-height:0;
}
.${TABS_FILL_CLASS} .ant-tabs-tabpane { height:100%; min-height:0; }
.${TABS_FILL_CLASS} .ant-tabs-tabpane.ant-tabs-tabpane-active { display:flex; flex-direction:column; }
.${TABS_FILL_CLASS} .ant-tabs-tabpane:not(.ant-tabs-tabpane-active),
.${TABS_FILL_CLASS} .ant-tabs-tabpane[aria-hidden="true"] { display:none !important; }
`;
    const el = document.createElement("style");
    el.setAttribute("data-tabs-fill", "true");
    el.textContent = css;
    document.head.appendChild(el);
    return () => { document.head.removeChild(el); };
  }, []);
}

/* =========================
 * 型
 * ========================= */
type IsoMonth = string; // "YYYY-MM"
type IsoDate = string; // "YYYY-MM-DD"

type CalendarDay = {
  date: IsoDate;
  is_business_day: 0 | 1;
  is_holiday: 0 | 1;
  week_id: IsoDate; // 週の月曜
};

type HeaderDTO = {
  month: IsoMonth;
  business_days: {
    total: number;
    mon_sat: number;
    sun_holiday: number;
    non_business: number;
  };
  rules: { week_def: string; week_to_month: string; alignment: string };
};

type TargetsDTO = {
  month: number;
  weeks: { bw_idx: number; week_target: number }[];
  day_weights: { weekday: number; sat: number; sun_hol: number };
};

type ProgressDTO = { mtd_actual: number; remaining_business_days: number };

type ForecastDTO = {
  today: { p50: number; p10: number; p90: number };
  week: { p50: number; p10: number; p90: number; target: number };
  month_landing: { p50: number; p10: number; p90: number };
};

type DailyCurveDTO = {
  date: IsoDate;
  from_7wk: number;
  from_month_share: number;
  bookings: number;
  actual?: number;
};

type WeekRowDTO = {
  week_id: IsoDate;
  week_start: IsoDate;
  week_end: IsoDate;
  business_week_index_in_month: number;
  ton_in_month: number;
  in_month_business_days: number;
  portion_in_month: number;
  targets: { week: number };
  comparisons: {
    vs_prev_week: { delta_ton: number | null; delta_pct: number | null; align_note: string };
    vs_prev_month_same_idx: { delta_ton: number | null; delta_pct: number | null; align_note: string };
    vs_prev_year_same_idx: { delta_ton: number | null; delta_pct: number | null; align_note: string };
  };
};

type HistoryDTO = {
  m_vs_prev_month: { delta_ton: number; delta_pct: number; align_note: string };
  m_vs_prev_year: { delta_ton: number; delta_pct: number };
  m_vs_3yr_avg: { delta_ton: number; delta_pct: number };
};

type MonthPayloadDTO = {
  header: HeaderDTO;
  targets: TargetsDTO;
  calendar: { days: CalendarDay[] };
  progress: ProgressDTO;
  forecast: ForecastDTO;
  daily_curve: DailyCurveDTO[];
  weeks: WeekRowDTO[];
  history: HistoryDTO;
  prev_month_daily?: Record<IsoDate, number>;
  prev_year_daily?: Record<IsoDate, number>;
};

/* =========================
 * 色・定数
 * ========================= */
const C = {
  primary: "#1677ff",
  actual: "#52c41a",
  target: "#faad14",
  baseline: "#9e9e9e",
  danger: "#cf1322",
  warn: "#fa8c16",
  ok: "#389e0d",
};

const FONT = { family: undefined as string | undefined, size: 14 }; // サイズを12から14に変更

// カスタム凡例: 1行表示に固定し、dataKey==="actual"(または表示名が「実績」)の項目は非表示にする
/* eslint-disable @typescript-eslint/no-explicit-any */
type LegendPropsLike = Record<string, any> & { payload?: readonly any[] };
const SingleLineLegend: React.FC<LegendPropsLike> = (props) => {
  const payload = props.payload;
  if (!payload || !Array.isArray(payload)) return null;

  const map: Record<string, string> = {
    prevMonth: "先月",
    prevYear: "前年",
    prevMonthCumulative: "先月累積",
    prevYearCumulative: "前年累積",
    actual: "実績",
    actualCumulative: "実績累積",
    cumActual: "実績累積",
  cumDaily: "バック予測累積",
  dailyForward: "フロント予測",
  daily: "バック予測",
  };

  const normalizeLabel = (p: unknown) => {
    const obj = p as Record<string, unknown> | undefined;
    const rawKey = obj && (obj.dataKey ?? obj.value ?? obj.payloadKey ?? "");
    const key = String(rawKey ?? "");
    if (key === "先月" || key === "前年" || key === "実績" || key === "先月累積" || key === "前年累積" || key === "実績累積") return key;
    return map[key] ?? key;
  };

  const items = payload.filter((p) => {
    const obj = p as Record<string, unknown> | undefined;
    const raw = obj && (obj.dataKey ?? obj.value ?? "");
    const name = String(raw ?? "");
    if (name === "actual" || name === "実績" || name === "actualCumulative" || name === "実績累積") return false;
    return true;
  }) as unknown[];

  if (items.length === 0) return null;

  return (
    <div style={{ display: "flex", gap: 12, alignItems: "center", justifyContent: "center", whiteSpace: "nowrap", overflowX: "auto", padding: "4px 0" }}>
      {items.map((p, i) => {
        const label = normalizeLabel(p);
        if (label === "実績") return null;
        const obj = p as Record<string, unknown> | undefined;
        const color = (obj && (obj.color ?? (obj.payload && (obj.payload as Record<string, any>).color))) || "#ccc";
        return (
          <div key={i} style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <div style={{ width: 14, height: 14, borderRadius: 3, background: String(color) }} /> {/* サイズを12から14に変更 */}
            <div style={{ color: "#595959", fontSize: FONT.size }}>{label}</div> {/* フォントサイズを変更 */}
          </div>
        );
      })}
    </div>
  );
};
/* eslint-enable @typescript-eslint/no-explicit-any */

/* =========================
 * ChartFrame: 親の実寸高さ(px)を測って ResponsiveContainer に渡す
 * ========================= */
const ChartFrame: React.FC<React.PropsWithChildren<{ style?: React.CSSProperties }>> = ({
  style,
  children,
}) => {
  const ref = useRef<HTMLDivElement | null>(null);
  const [h, setH] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let disposed = false;
    const setFromRect = () => {
      const r = el.getBoundingClientRect();
      const hh = Math.max(0, Math.floor(r.height));
      setH(prev => Math.abs(prev - hh) > 1 ? hh : prev);
    };
    const ro = new ResizeObserver(() => requestAnimationFrame(() => !disposed && setFromRect()));
    ro.observe(el);
    let tries = 0;
    const kick = () => { if (disposed) return; setFromRect(); if (h === 0 && tries++ < 20) requestAnimationFrame(kick); };
    kick();
    window.addEventListener("resize", setFromRect);
    return () => { disposed = true; ro.disconnect(); window.removeEventListener("resize", setFromRect); };
  }, [h]);

  return (
    <div ref={ref} style={{ height: "100%", width: "100%", minHeight: 0, ...style }}>
      {h > 0 ? (
        <ResponsiveContainer width="100%" height={h}>
          {children as unknown as React.ReactElement}
        </ResponsiveContainer>
      ) : (
        <ResponsiveContainer width="100%" aspect={3}>
          {children as unknown as React.ReactElement}
        </ResponsiveContainer>
      )}
    </div>
  );
};

/* =========================
 * ユーティリティ
 * ========================= */
const toDate = (s: string) => new Date(s + "T00:00:00");
const ymd = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate()
  ).padStart(2, "0")}`;
const mondayOf = (d: Date) => {
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  const m = new Date(d);
  m.setDate(d.getDate() + diff);
  m.setHours(0, 0, 0, 0);
  return m;
};
const addDays = (d: Date, n: number) => { const x = new Date(d); x.setDate(d.getDate() + n); return x; };
const sum = (a: number[]) => a.reduce((p, c) => p + c, 0);
const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
const monthNameJP = (m: IsoMonth) => { const [y, mm] = m.split("-").map(Number); return `${y}年${mm}月`; };
const curMonth = (): IsoMonth => dayjs().format("YYYY-MM");
const nextMonth = (m: IsoMonth): IsoMonth => dayjs(m + "-01").add(1, "month").format("YYYY-MM");

/* =========================
 * モック生成
 * ========================= */
async function fetchMonthPayloadMock(month: IsoMonth): Promise<MonthPayloadDTO> {
  const first = dayjs(month + "-01");
  const last = first.endOf("month");
  const days: CalendarDay[] = [];
  let d = first;
  while (d.isBefore(last) || d.isSame(last, "day")) {
    const date = d.format("YYYY-MM-DD");
    const dow = d.day();
    const is_business_day = dow === 0 ? 0 : 1;
    const is_holiday = dow === 0 ? 1 : 0;
    days.push({ date, is_business_day, is_holiday, week_id: ymd(mondayOf(d.toDate())) });
    d = d.add(1, "day");
  }

  const wWeekday = 1.0, wSat = 1.1, wSunHol = 0.6;
  const weightOf = (date: string) => {
    const dow = toDate(date).getDay();
    if (dow === 6) return wSat;
    if (dow === 0) return 0;
    return wWeekday;
  };
  const dayWeightForBShare = (date: string) => {
    const dow = toDate(date).getDay();
    if (dow === 6) return wSat;
    if (dow === 0) return wSunHol;
    return wWeekday;
  };

  const bizWeights = days.map((x) => (x.is_business_day ? weightOf(x.date) : 0));
  const monthTarget = Math.round(sum(bizWeights) * 110);

  const weekMap = new Map<string, { start: IsoDate; end: IsoDate; tonInMonth: number; inMonthBiz: number; fullBiz: number }>();
  let calStart = mondayOf(first.toDate());
  while (calStart <= last.toDate()) {
    const wEnd = addDays(calStart, 6);
    const wid = ymd(calStart);
    let fullBiz = 0;
    for (let k = 0; k < 7; k++) {
      const dd = addDays(calStart, k);
      if (dd.getDay() !== 0) fullBiz++;
    }
    weekMap.set(wid, { start: ymd(calStart), end: ymd(wEnd), tonInMonth: 0, inMonthBiz: 0, fullBiz });
    calStart = addDays(calStart, 7);
  }

  const lastDay = last.date();
  const syntheticDailyTon: Record<IsoDate, number> = {};
  days.forEach((x, i) => {
    const base = 100 + Math.sin(((i + 1) / lastDay) * Math.PI * 2) * 20;
    const dow = toDate(x.date).getDay();
    const adj = dow === 6 ? 10 : 0;
    const noise = (Math.random() - 0.5) * 12;
    const ton = x.is_business_day ? Math.max(35, Math.round(base + adj + noise)) : 0;
    syntheticDailyTon[x.date] = ton;
  });

  for (const c of days) {
    const w = weekMap.get(c.week_id);
    if (!w) continue;
    if (c.is_business_day) {
      w.tonInMonth += syntheticDailyTon[c.date];
      w.inMonthBiz += 1;
    }
  }

  const weekEntries = [...weekMap.entries()].sort((a, b) => a[0] < b[0] ? -1 : 1);
  let idx = 0;
  const weekRows: WeekRowDTO[] = [];
  for (const [, v] of weekEntries) {
    if (v.inMonthBiz > 0) {
      idx += 1;
      weekRows.push({
        week_id: v.start, week_start: v.start, week_end: v.end,
        business_week_index_in_month: idx,
        ton_in_month: Math.round(v.tonInMonth),
        in_month_business_days: v.inMonthBiz,
        portion_in_month: v.fullBiz ? v.inMonthBiz / v.fullBiz : 0,
        targets: { week: 0 },
        comparisons: {
          vs_prev_week: { delta_ton: null, delta_pct: null, align_note: "prev business week" },
          vs_prev_month_same_idx: { delta_ton: null, delta_pct: null, align_note: "same idx" },
          vs_prev_year_same_idx: { delta_ton: null, delta_pct: null, align_note: "same idx" },
        },
      });
    }
  }
  const totalBizDays = sum(weekRows.map((w) => w.in_month_business_days));
  weekRows.forEach((w) => {
    w.targets.week = totalBizDays ? Math.round(monthTarget * (w.in_month_business_days / totalBizDays)) : 0;
  });

  const today = todayInMonth(month);
  const mtdActual = sum(days.filter((x) => x.date <= today).map((x) => syntheticDailyTon[x.date]));
  const remainingBiz = days.filter((x) => x.date > today && x.is_business_day).length;

  const futureTon = sum(days.filter((x) => x.date > today).map((x) => syntheticDailyTon[x.date]));
  const monthP50 = mtdActual + futureTon;
  const pBand = Math.max(80, Math.round(monthP50 * 0.06));
  const forecast: ForecastDTO = {
    today: { p50: syntheticDailyTon[today] ?? 0, p10: Math.max(0, (syntheticDailyTon[today] ?? 0) - 15), p90: (syntheticDailyTon[today] ?? 0) + 15 },
    week: { p50: Math.round(sum(days.filter((x) => toDate(x.date) >= mondayOf(toDate(today)) && toDate(x.date) <= addDays(mondayOf(toDate(today)), 6)).map((x) => syntheticDailyTon[x.date]))), p10: 0, p90: 0, target: 0 },
    month_landing: { p50: monthP50, p10: Math.max(0, monthP50 - pBand), p90: monthP50 + pBand },
  };

  const daily_curve: DailyCurveDTO[] = days.map((x, i) => {
    const dow = toDate(x.date).getDay();
    const backIdx = Math.max(0, i - 7);
    const near = days.slice(backIdx, i).filter((d) => toDate(d.date).getDay() === dow);
    const avg = near.length ? Math.round(sum(near.map((d) => syntheticDailyTon[d.date])) / near.length) : syntheticDailyTon[x.date];
    const wAll = sum(days.map((d) => toDate(d.date).getDay() === 0 ? 0 : dayWeightForBShare(d.date)));
    const wMe = toDate(x.date).getDay() === 0 ? 0 : dayWeightForBShare(x.date);
    const fromMonthShare = wAll ? Math.round(monthTarget * (wMe / wAll)) : 0;
    const bookings = Math.max(0, Math.round(Math.random() * 6 - (toDate(x.date).getDay() === 0 ? 6 : 0)));
    return { date: x.date, from_7wk: avg, from_month_share: fromMonthShare, bookings, actual: syntheticDailyTon[x.date] };
  });

  // 先月・前年ダミー
  const prevMonthDays: Record<IsoDate, number> = {};
  const prevYearDays: Record<IsoDate, number> = {};
  const pmFirst = dayjs(month + "-01").subtract(1, "month");
  const pmLast = pmFirst.endOf("month");
  let pd = pmFirst;
  while (pd.isBefore(pmLast) || pd.isSame(pmLast, "day")) {
    const k = pd.format("YYYY-MM-DD");
    const corresponding = dayjs(k).add(1, "month").format("YYYY-MM-DD");
    const base = daily_curve.find((r) => r.date === corresponding)?.actual ?? 80;
    prevMonthDays[k] = Math.max(0, Math.round(base * 0.98));
    pd = pd.add(1, "day");
  }
  const pyFirst = dayjs(month + "-01").subtract(1, "year");
  const pyLast = pyFirst.endOf("month");
  let yd = pyFirst;
  while (yd.isBefore(pyLast) || yd.isSame(pyLast, "day")) {
    const k = yd.format("YYYY-MM-DD");
    const corresponding = dayjs(k).add(1, "year").format("YYYY-MM-DD");
    const base = daily_curve.find((r) => r.date === corresponding)?.actual ?? 80;
    prevYearDays[k] = Math.max(0, Math.round(base * 0.95));
    yd = yd.add(1, "day");
  }

  const targets: TargetsDTO = {
    month: monthTarget,
    weeks: weekRows.map((w) => ({ bw_idx: w.business_week_index_in_month, week_target: w.targets.week })),
    day_weights: { weekday: wWeekday, sat: wSat, sun_hol: wSunHol },
  };

  const header: HeaderDTO = {
    month,
    business_days: {
      total: days.filter((x) => x.is_business_day).length,
      mon_sat: days.filter((x) => x.is_business_day && toDate(x.date).getDay() <= 6 && toDate(x.date).getDay() !== 0).length,
      sun_holiday: days.filter((x) => x.is_business_day && toDate(x.date).getDay() === 0).length,
      non_business: days.filter((x) => !x.is_business_day).length,
    },
    rules: { week_def: "ISO Monday-based", week_to_month: "partial-weeks included by day", alignment: "business-day" },
  };

  const progress: ProgressDTO = { mtd_actual: mtdActual, remaining_business_days: remainingBiz };

  return {
    header,
    targets,
    calendar: { days },
    progress,
    forecast,
    daily_curve,
    weeks: weekRows,
    history: {
      m_vs_prev_month: { delta_ton: 0, delta_pct: 0, align_note: "mock" },
      m_vs_prev_year: { delta_ton: 0, delta_pct: 0 },
      m_vs_3yr_avg: { delta_ton: 0, delta_pct: 0 },
    },
    prev_month_daily: prevMonthDays,
    prev_year_daily: prevYearDays,
  };
}

/* =========================
 * 表示補助
 * ========================= */
const todayInMonth = (m: IsoMonth): IsoDate => {
  const nowM = curMonth();
  if (m === nowM) return dayjs().format("YYYY-MM-DD");
  const last = dayjs(m + "-01").endOf("month").date();
  const d = Math.min(20, last);
  return `${m}-${String(d).padStart(2, "0")}`;
};

/* =========================
 * 目標カード（シンプル版：CSS だけで高さ配分）
 * ========================= */
const TargetCard: React.FC<{
  targets: TargetsDTO;
  calendarDays: CalendarDay[];
  progress?: ProgressDTO;
  daily_curve?: DailyCurveDTO[];
  style?: React.CSSProperties;
}> = ({ targets, calendarDays, progress, daily_curve, style }) => {
  const dayWeight = targets.day_weights;
  const weekdayCount = calendarDays.filter(
    (d) => d.is_business_day && toDate(d.date).getDay() >= 1 && toDate(d.date).getDay() <= 5
  ).length;
  const satCount = calendarDays.filter((d) => d.is_business_day && toDate(d.date).getDay() === 6).length;
  const sunHolCount = calendarDays.filter((d) => d.is_business_day && toDate(d.date).getDay() === 0).length;

  const businessDayCount = weekdayCount + satCount;
  const businessWeight = dayWeight.weekday + dayWeight.sat;

  const totalW = businessDayCount * businessWeight + sunHolCount * dayWeight.sun_hol || 1;
  const oneBusinessDay = Math.round((targets.month * (businessWeight / totalW)) || 0);

  // 今週の目標・実績
  const todayStr = dayjs().format("YYYY-MM-DD");
  const dayEntry = calendarDays.find((d) => d.date === todayStr) || calendarDays[0];
  const todayWeekId = dayEntry.week_id;
  const weekIds = Array.from(new Set(calendarDays.map((d) => d.week_id))).sort();
  let idx = 0;
  let currentIdx = 1;
  for (const wid of weekIds) {
    const inMonthBiz = calendarDays.filter((d) => d.week_id === wid && d.is_business_day).length;
    if (inMonthBiz > 0) idx += 1;
    if (wid === todayWeekId) { currentIdx = idx; break; }
  }
  const curWeek = targets.weeks.find((w) => w.bw_idx === currentIdx) ?? targets.weeks[targets.weeks.length - 1];
  const weekTarget = curWeek ? curWeek.week_target : 0;
  const thisWeekActual = daily_curve
    ? sum(
        daily_curve
          .filter((d) => {
            const wstart = mondayOf(toDate(todayStr));
            return toDate(d.date) >= wstart && toDate(d.date) <= addDays(wstart, 6);
          })
          .map((d) => d.actual ?? 0)
      )
    : 0;

  const todayActual = daily_curve ? daily_curve.find((d) => d.date === todayStr)?.actual ?? 0 : 0;

  const rowsData = [
    { key: "month", label: "1ヶ月", target: targets.month, actual: progress ? progress.mtd_actual : 0 },
    { key: "week", label: "今週", target: weekTarget, actual: thisWeekActual },
    { key: "day", label: "1日", target: oneBusinessDay, actual: todayActual },
  ];

  return (
    <Card
      bordered
      style={{ height: "100%", display: "flex", flexDirection: "column", ...style }}
      bodyStyle={{ padding: 12, display: "flex", flexDirection: "column", gap: 8, flex: 1, minHeight: 0 }}
    >
      <Space align="baseline" style={{ justifyContent: "space-between", width: "100%" }}>
        <Typography.Title level={5} style={{ margin: 0 }}>目標カード</Typography.Title>
        <Tooltip title="週目標は当月の営業日配分で按分。日目標は平日/土/日祝の重みで配分。">
          <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
        </Tooltip>
      </Space>

      <div
        style={{
          border: "1px solid #f0f0f0",
          borderRadius: 8,
          background: "#fff",
          padding: 8,
          display: "grid",
          gridTemplateColumns: "auto auto auto 1fr",
          gridTemplateRows: `repeat(${1 + rowsData.length}, minmax(44px, 1fr))`, // ← これで高さ自動配分
          columnGap: 12,
          rowGap: 6,
          alignItems: "center",
          boxSizing: "border-box",
          flex: 1,
          minHeight: 0,
          overflow: "hidden",
        }}
      >
  {/* ヘッダ行（列ラベル） */}
  <div style={{ color: "#8c8c8c", fontSize: 14 }} />
  <div style={{ color: "#8c8c8c", fontSize: 16, fontWeight: 700 }}>目標</div>
  <div style={{ color: "#8c8c8c", fontSize: 16, fontWeight: 700 }}>実績</div>
  <div style={{ color: "#8c8c8c", fontSize: 16, fontWeight: 700 }}>達成率</div>

        {/* データ行 */}
        {rowsData.map((r) => {
          const ratioRaw = r.target ? r.actual / r.target : 0;
          const pct = r.target ? Math.round(ratioRaw * 100) : 0;
          const barPct = clamp(pct, 0, 100);
          const pctColor = ratioRaw >= 1 ? C.ok : ratioRaw >= 0.9 ? C.warn : C.danger;

          return (
            <React.Fragment key={r.key}>
              <div style={{ color: "#595959", fontSize: 12, fontWeight: 800, lineHeight: 1 }}>{r.label}</div>
              <div>
                <Statistic value={typeof r.target === "number" ? r.target : 0} suffix="t"
                  valueStyle={{ color: C.primary, fontSize: 18, fontWeight: 800, lineHeight: 1 }}
                  style={{ lineHeight: 1 }} />
              </div>
              <div>
                <Statistic value={typeof r.actual === "number" ? r.actual : 0} suffix="t"
                  valueStyle={{ color: "#222", fontSize: 18, fontWeight: 800, lineHeight: 1 }}
                  style={{ lineHeight: 1 }} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4, minHeight: 0, overflow: "hidden" }}>
                <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "baseline" }}>
                  <Statistic value={pct} suffix="%"
                    valueStyle={{ color: pctColor, fontSize: 12, fontWeight: 700, lineHeight: 1 }}
                    style={{ lineHeight: 1 }} />
                </div>
                <Progress percent={barPct} showInfo={false} strokeColor={pctColor} strokeWidth={8} style={{ margin: 0 }} />
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </Card>
  );
};

/* =========================
 * 日次（実績）
 * ========================= */
const DailyActualsCard: React.FC<{
  rows: DailyCurveDTO[];
  prevMonthDaily?: Record<IsoDate, number>;
  prevYearDaily?: Record<IsoDate, number>;
  variant?: "standalone" | "embed";
}> = ({ rows, prevMonthDaily, prevYearDaily, variant = "standalone" }) => {
  const [showPrevMonth, setShowPrevMonth] = useState(false);
  const [showPrevYear, setShowPrevYear] = useState(false);

  const chartData = rows.map((r) => {
    const prevMonthKey = dayjs(r.date).subtract(1, "month").format("YYYY-MM-DD");
    const prevYearKey = dayjs(r.date).subtract(1, "year").format("YYYY-MM-DD");
    return {
      label: dayjs(r.date).format("DD"),
      actual: typeof r.actual === "number" ? r.actual : undefined,
      dateFull: r.date,
      prevMonth: prevMonthDaily ? prevMonthDaily[prevMonthKey] ?? null : null,
      prevYear: prevYearDaily ? prevYearDaily[prevYearKey] ?? null : null,
    };
  });
  const colorForDate = (dateStr: string) => {
    const d = dayjs(dateStr);
    const dow = d.day();
    const isSecondSunday = (() => {
      if (dow !== 0) return false;
      let count = 0;
      let cur = d.startOf("month");
      while (cur.isBefore(d) || cur.isSame(d, "day")) {
        if (cur.day() === 0) count += 1;
        cur = cur.add(1, "day");
      }
      return count === 2;
    })();
    if (isSecondSunday) return C.danger;
    if (dow === 0) return "#ff85c0";
    return C.ok;
  };

  const Inner = () => (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "space-between", padding: "0 0 4px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Typography.Title level={5} style={{ margin: 0, fontSize: 13 }}>日次搬入量（実績）</Typography.Title>
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
                const [v, name, payloadItem] = (args as unknown) as [
                  unknown,
                  unknown,
                  { payload?: Record<string, unknown> }?
                ];
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
                const valNum = Number(v as unknown as number);
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
              {chartData.map((entry, idx) => (<Cell key={`cell-${idx}`} fill={colorForDate(entry.dateFull)} />))}
            </Bar>
            {showPrevMonth && (<Line type="monotone" dataKey="prevMonth" stroke="#40a9ff" dot={false} strokeWidth={2} />)}
            {showPrevYear && (<Line type="monotone" dataKey="prevYear" stroke="#fa8c16" dot={false} strokeWidth={2} />)}
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <Legend content={(props: any) => <SingleLineLegend {...(props as any)} />} verticalAlign="bottom" />
          </BarChart>
        </ChartFrame>
      </div>

      <div style={{ paddingTop: 2, display: "flex", gap: 10, justifyContent: "center", alignItems: "center", flexWrap: "wrap", fontSize: 14 }}>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <div style={{ width: 14, height: 14, borderRadius: 3, background: C.ok }} />
          <div style={{ color: "#595959" }}>営業</div>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <div style={{ width: 14, height: 14, borderRadius: 3, background: "#ff85c0" }} />
          <div style={{ color: "#595959" }}>日祝</div>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <div style={{ width: 14, height: 14, borderRadius: 3, background: C.danger }} />
          <div style={{ color: "#595959" }}>休業</div>
        </div>
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

/* =========================
 * 日次（累積）
 * ========================= */
const DailyCumulativeCard: React.FC<{
  rows: DailyCurveDTO[];
  prevMonthDaily?: Record<IsoDate, number>;
  prevYearDaily?: Record<IsoDate, number>;
  variant?: "standalone" | "embed";
}> = ({ rows, prevMonthDaily, prevYearDaily, variant = "standalone" }) => {
  const [showPrevMonth, setShowPrevMonth] = useState(false);
  const [showPrevYear, setShowPrevYear] = useState(false);

  let running = 0, accPM = 0, accPY = 0;
  const cumData = rows.map((r) => {
    if (typeof r.actual === "number") running += r.actual;
    const yyyy = r.date;
    const pmKey = dayjs(yyyy).subtract(1, "month").format("YYYY-MM-DD");
    const pyKey = dayjs(yyyy).subtract(1, "year").format("YYYY-MM-DD");
    const pmVal = prevMonthDaily ? prevMonthDaily[pmKey] ?? 0 : 0;
    const pyVal = prevYearDaily ? prevYearDaily[pyKey] ?? 0 : 0;
    accPM += pmVal; accPY += pyVal;
    return { label: dayjs(r.date).format("DD"), yyyyMMdd: r.date, actualCumulative: running, prevMonthCumulative: accPM, prevYearCumulative: accPY };
  });

  const tooltipFormatter = (...args: unknown[]) => {
    const [v, name, payloadItem] = (args as unknown) as [unknown, unknown, { payload?: Record<string, unknown> }?];
    const map: Record<string, string> = { actualCumulative: "累積実績", prevMonthCumulative: "先月累積", prevYearCumulative: "前年累積" };
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
    const valNum = Number(v as unknown as number);
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
        <Typography.Title level={5} style={{ margin: 0, fontSize: 13 }}>日次累積搬入量（累積）</Typography.Title>
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
            <Area type="monotone" dataKey="actualCumulative" stroke={C.actual} fill={C.actual} fillOpacity={0.2} />
            {showPrevMonth && (<Line type="monotone" dataKey="prevMonthCumulative" name="先月累積" stroke="#40a9ff" dot={false} strokeWidth={2} />)}
            {showPrevYear && (<Line type="monotone" dataKey="prevYearCumulative" name="前年累積" stroke="#fa8c16" dot={false} strokeWidth={2} />)}
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <Legend content={(props: any) => <SingleLineLegend {...(props as any)} />} verticalAlign="bottom" />
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

/* =========================
 * 上段：日次/累積タブ
 * ========================= */
const CombinedDailyCard: React.FC<{
  rows: DailyCurveDTO[];
  prevMonthDaily?: Record<IsoDate, number>;
  prevYearDaily?: Record<IsoDate, number>;
  style?: React.CSSProperties;
}> = ({ rows, prevMonthDaily, prevYearDaily, style }) => {
  useInstallTabsFillCSS();
  return (
    <Card bordered size="small" style={{ height: "100%", display: "flex", flexDirection: "column", ...(style || {}) }}
      bodyStyle={{ padding: 12, flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
      <Tabs
        size="small"
        className={`${TABS_FILL_CLASS} ${tabsTight.root}`}
        tabBarStyle={{ padding: "4px 8px", minHeight: 26, height: 26, fontSize: 13, marginBottom: 0 }}
        style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}
        items={[
          {
            key: "daily",
            label: "日次",
            children: (
              <div style={{ height: "100%", minHeight: 0 }}>
                <DailyActualsCard variant="embed" rows={rows} prevMonthDaily={prevMonthDaily} prevYearDaily={prevYearDaily} />
              </div>
            ),
          },
          {
            key: "cumulative",
            label: "累積",
            children: (
              <div style={{ height: "100%", minHeight: 0 }}>
                <DailyCumulativeCard variant="embed" rows={rows} prevMonthDaily={prevMonthDaily} prevYearDaily={prevYearDaily} />
              </div>
            ),
          },
        ]}
      />
    </Card>
  );
};

/* =========================
 * 営業カレンダー
 * ========================= */
const CalendarCard: React.FC<{ days: CalendarDay[]; month?: IsoMonth; style?: React.CSSProperties; }> = ({ days, month = curMonth(), style }) => {
  const dayMap = useMemo(() => { const m = new Map<string, CalendarDay>(); days.forEach((d) => m.set(d.date, d)); return m; }, [days]);

  const dayCounts = useMemo(() => {
    let weekday = 0, sunday = 0, secondSunday = 0;
    let weekdayRem = 0, sundayRem = 0, secondSundayRem = 0;
    const todayStr = dayjs().format("YYYY-MM-DD");
    days.forEach((d) => {
      const dt = dayjs(d.date);
      const dow = dt.day();
      const isSecond = (() => {
        if (dow !== 0) return false;
        let count = 0; let cur = dt.startOf("month");
        while (cur.isBefore(dt) || cur.isSame(dt, "day")) { if (cur.day() === 0) count += 1; cur = cur.add(1, "day"); }
        return count === 2;
      })();
      if (isSecond) { secondSunday += 1; if (d.date >= todayStr) secondSundayRem += 1; }
      else if (dow === 0) { sunday += 1; if (d.date >= todayStr) sundayRem += 1; }
      else { weekday += 1; if (d.date >= todayStr) weekdayRem += 1; }
    });
    return { weekday, sunday, secondSunday, weekdayRem, sundayRem, secondSundayRem };
  }, [days]);

  // 行高はシンプルに利用可能高さを週数で割る（多少余白引き）
  const containerRef = useRef<HTMLDivElement | null>(null);
  const headerRef = useRef<HTMLDivElement | null>(null);
  const legendRef = useRef<HTMLDivElement | null>(null);
  const [rowHeight, setRowHeight] = useState<number>(28);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    let disposed = false;
    const recompute = () => {
      if (disposed) return;
      const rect = el.getBoundingClientRect();
      const totalH = Math.max(0, Math.floor(rect.height));
      const headerH = headerRef.current ? Math.ceil(headerRef.current.getBoundingClientRect().height) : 0;
      const legendH = legendRef.current ? Math.ceil(legendRef.current.getBoundingClientRect().height) : 0;
      const first = dayjs(month + "-01");
      const startDow = first.day();
      const daysInMonth = first.daysInMonth();
      const weeks = Math.max(1, Math.ceil((startDow + daysInMonth) / 7));
      const bodyExtra = 24;
      const avail = Math.max(0, totalH - headerH - legendH - bodyExtra);
      const rh = weeks > 0 ? Math.max(18, Math.floor(avail / weeks)) : 28;
      setRowHeight((prev) => (Math.abs(prev - rh) > 1 ? rh : prev));
    };
    const ro = new ResizeObserver(() => requestAnimationFrame(recompute));
    ro.observe(el);
    if (headerRef.current) ro.observe(headerRef.current);
    if (legendRef.current) ro.observe(legendRef.current);
    window.addEventListener("resize", recompute);
    recompute();
    return () => { disposed = true; ro.disconnect(); window.removeEventListener("resize", recompute); };
  }, [month, days]);

  return (
    <Card bordered size="small" style={{ height: "100%", display: "flex", flexDirection: "column", ...(style || {}) }}
      bodyStyle={{ display: "flex", flexDirection: "column", padding: 12, gap: 8, flex: 1, minHeight: 0 }}>
      <div ref={headerRef} style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 8 }}>
        <Typography.Title level={5} style={{ margin: 0, fontSize: 16 }}>営業カレンダー</Typography.Title>
        <Tooltip title="最終判定は is_business_day。祝日や独自休業はサーバで上書き。">
          <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
        </Tooltip>
      </div>
      <div ref={legendRef}
        style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", justifyContent: "center", fontSize: 14 }}> {/* フォントサイズを14に変更 */}
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <div style={{ width: 12, height: 12, borderRadius: 3, background: C.ok }} /> {/* サイズを12に変更 */}
          <div style={{ color: "#595959", fontWeight: 700 }}>
            {dayCounts.weekday}
            <span style={{ color: "#8c8c8c", fontWeight: 400, marginLeft: 6 }}>({dayCounts.weekdayRem})</span>
          </div>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <div style={{ width: 12, height: 12, borderRadius: 3, background: "#ff85c0" }} /> {/* サイズを12に変更 */}
          <div style={{ color: "#595959", fontWeight: 700 }}>
            {dayCounts.sunday}
            <span style={{ color: "#8c8c8c", fontWeight: 400, marginLeft: 6 }}>({dayCounts.sundayRem})</span>
          </div>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <div style={{ width: 12, height: 12, borderRadius: 3, background: C.danger }} /> {/* サイズを12に変更 */}
          <div style={{ color: "#595959", fontWeight: 700 }}>
            {dayCounts.secondSunday}
            <span style={{ color: "#8c8c8c", fontWeight: 400, marginLeft: 6 }}>({dayCounts.secondSundayRem})</span>
          </div>
        </div>
      </div>

      <div ref={containerRef} style={{ flex: 1, minHeight: 0 }}>
        <CalendarGrid
          month={month}
          rowHeight={rowHeight}
          renderCell={(value, inMonth) => {
            const key = value.format("YYYY-MM-DD");
            const info = dayMap.get(key);
            if (!info) return null;
            const dow = value.day();
            const isHoliday = info.is_holiday === 1;

            const isSecondSunday = (() => {
              if (dow !== 0) return false;
              let cnt = 0; let d = value.startOf("month");
              while (d.isBefore(value) || d.isSame(value, "day")) { if (d.day() === 0) cnt += 1; d = d.add(1, "day"); }
              return cnt === 2;
            })();

            let bg = C.ok, fg = "#fff";
            if (isSecondSunday) bg = C.danger;
            else if (dow === 0 || isHoliday) bg = "#ff85c0";

            const isToday = key === dayjs().format("YYYY-MM-DD");
            if (isToday) { bg = "#fadb14"; fg = "#000"; }

            const dayNum = value.date();
            if (!inMonth) return <div style={{ color: "#bfbfbf", fontSize: 11 }}>{dayNum}</div>;
            return (
              <div style={{ width: 22, height: 22, borderRadius: 6, background: bg, color: fg, fontSize: 12, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center" }}>
                {dayNum}
              </div>
            );
          }}
        />
      </div>
    </Card>
  );
};

/* =========================
 * 予測カード
 * ========================= */
const ForecastCard: React.FC<{ forecast: ForecastDTO; monthTarget: number; rows?: DailyCurveDTO[]; }> = ({ forecast, monthTarget, rows }) => {
  useInstallTabsFillCSS();

  const rowsData = rows && rows.length ? rows : [];
  const month = rowsData.length ? dayjs(rowsData[0].date).format("YYYY-MM") : curMonth();
  const daysInMonth = rowsData.length ? rowsData.length : dayjs(month + "-01").daysInMonth();
  const base = monthTarget && daysInMonth ? monthTarget / daysInMonth : 0;
  const chartData: { label: string; daily: number; cumulative: number; dailyForward?: number; actual?: number; }[] = [];
  let running = 0;
  const todayDate = dayjs();
  let forwardStartDay = todayDate.format("YYYY-MM") === month ? todayDate.date() : 1;
  const forwardEndDay = Math.min(daysInMonth, forwardStartDay + 6);

  if (rowsData.length) {
    for (let idx = 0; idx < rowsData.length; idx++) {
      const r = rowsData[idx];
      const i = idx + 1;
      const factor = 0.9 + 0.2 * (0.5 + Math.sin((i / daysInMonth) * Math.PI * 2) / 2);
      const daily = Math.round(base * factor);
      running += daily;
      const dailyForward = i >= forwardStartDay && i <= forwardEndDay ? Math.round(base * (0.9 + 0.2 * (0.5 + Math.sin((i / daysInMonth) * Math.PI * 2) / 2))) : 0;
      const actualDay = typeof r.actual === "number" ? r.actual : undefined;
      chartData.push({ label: String(i).padStart(2, "0"), daily, cumulative: running, dailyForward, actual: actualDay });
    }
  } else {
    for (let i = 1; i <= daysInMonth; i++) {
      const factor = 0.9 + 0.2 * (0.5 + Math.sin((i / daysInMonth) * Math.PI * 2) / 2);
      const daily = Math.round(base * factor);
      running += daily;
      const dailyForward = i >= forwardStartDay && i <= forwardEndDay ? Math.round(base * (0.9 + 0.2 * (0.5 + Math.sin((i / daysInMonth) * Math.PI * 2) / 2))) : 0;
      const actualDay = i < forwardStartDay ? Math.round(Math.round(base * (0.9 + 0.2 * (0.5 + Math.sin((i / daysInMonth) * Math.PI * 2) / 2))) * (0.95 + Math.random() * 0.1)) : 0;
      chartData.push({ label: String(i).padStart(2, "0"), daily, cumulative: running, dailyForward, actual: actualDay });
    }
  }

  const [showActual, setShowActual] = useState(true);
  const [showForward, setShowForward] = useState(true);
  const [showReverse, setShowReverse] = useState(true);
  const [showCumReverse, setShowCumReverse] = useState(true);
  const [showCumActual, setShowCumActual] = useState(true);

  type KPIProps = { title: string; p50: number; p10: number; p90: number; target?: number | null; };
  const KPIBlock: React.FC<KPIProps> = ({ title, p50, p10, p90, target = null }) => {
    const ratio = target ? p50 / target : null;
    const pct = ratio != null ? Math.round(ratio * 100) : null;
    const pctColor = ratio == null ? "#8c8c8c" : ratio >= 1 ? C.ok : ratio >= 0.9 ? C.warn : C.danger;
    return (
      <Card size="small" bodyStyle={{ padding: 12, height: "100%", display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
        <div style={{ height: "100%", display: "grid", gridTemplateColumns: "auto 1fr auto", alignItems: "center", gap: 8 }}>
          <div style={{ textAlign: "left", paddingLeft: 4 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#2b2b2b" }}>{title}</div>
          </div>
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
            <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 18, fontWeight: 900, color: C.primary }}>{p50.toLocaleString()}<span style={{ fontSize: 13, fontWeight: 700 }}>t</span></div>
                <div style={{ fontSize: 11, color: "#8c8c8c" }}>レンジ: {p10}–{p90}<span style={{ fontSize: 10 }}>t</span></div>
            </div>
          </div>
          <div style={{ width: 92, display: "flex", flexDirection: "column", alignItems: "center" }}>
            {pct != null ? (
              <>
                <Progress percent={clamp(pct, 0, 200)} showInfo={false} strokeColor={pctColor} strokeWidth={8} />
                <div style={{ textAlign: "center", marginTop: 4, color: pctColor, fontWeight: 700, fontSize: 12 }}>{pct}%</div>
              </>
            ) : (
              <div style={{ color: "#8c8c8c", textAlign: "center", fontSize: 12 }}>目標不明</div>
            )}
          </div>
        </div>
      </Card>
    );
  };

  const cumDailyData = React.useMemo(() => {
    let runReverse = 0; let runActual = 0;
    return chartData.map((d) => { runReverse += Number(d.daily || 0); if (typeof d.actual === "number") runActual += Number(d.actual); return { ...d, cumDaily: runReverse, cumActual: runActual }; });
  }, [chartData]);

  const oddDayTicks = Array.from({ length: daysInMonth }, (_, i) => String(i + 1).padStart(2, "0")).filter((s) => Number(s) % 2 === 1);

  return (
    <Card bordered style={{ height: "100%", display: "flex", flexDirection: "column" }}
      bodyStyle={{ padding: 12, display: "flex", flexDirection: "column", gap: 8, flex: 1, minHeight: 0 }}>
      <Space align="baseline" style={{ justifyContent: "space-between", width: "100%" }}>
        <Typography.Title level={5} style={{ margin: 0 }}>搬入量予測（P50 / P10–P90）</Typography.Title>
        <Tooltip title="P帯はモデル残差から推定（本番）。ここではデモ値。">
          <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
        </Tooltip>
      </Space>

      <div style={{ flex: 1, minHeight: 0 }}>
        <Row gutter={[8, 8]} style={{ height: "100%" }}>
          <Col xs={24} lg={8} style={{ height: "100%" }}>
            <div style={{ height: "100%", display: "grid", gridTemplateRows: "1fr 1fr 1fr", gap: 6 }}>
              <KPIBlock title="当日" p50={forecast.today.p50} p10={forecast.today.p10} p90={forecast.today.p90}
                target={monthTarget && rows?.length ? Math.round(monthTarget / rows.length) : null} />
              <KPIBlock title="今週合計" p50={forecast.week.p50} p10={forecast.week.p10} p90={forecast.week.p90}
                target={monthTarget && rows?.length ? Math.round((monthTarget / rows.length) * 7) : null} />
              <KPIBlock title="今月末" p50={forecast.month_landing.p50} p10={forecast.month_landing.p10} p90={forecast.month_landing.p90}
                target={monthTarget} />
            </div>
          </Col>

          <Col xs={24} lg={16} style={{ height: "100%", display: "flex", flexDirection: "column", minHeight: 0 }}>
            <Tabs size="small" className={TABS_FILL_CLASS} tabBarStyle={{ padding: "0 8px", minHeight: 28, height: 28, fontSize: 13 }}
              style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}
              items={[
                {
                  key: "reverse",
                  label: "日次",
                  children: (
                    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
                      <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, padding: "4px 0" }}>
                        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                          <Switch size="small" checked={showActual} onChange={setShowActual} /><span style={{ fontSize: 12 }}>実績</span>
                        </div>
                        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                          <Switch size="small" checked={showForward} onChange={setShowForward} /><span style={{ fontSize: 12 }}>フロント予測</span>
                        </div>
                        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                          <Switch size="small" checked={showReverse} onChange={setShowReverse} /><span style={{ fontSize: 12 }}>バック予測</span>
                        </div>
                      </div>
                      <div style={{ flex: 1, minHeight: 0 }}>
                        <ChartFrame style={{ flex: 1, minHeight: 0 }}>
                          <ComposedChart data={chartData} barCategoryGap="0%" barGap={0} margin={{ left: 0, right: 8, top: 6, bottom: 12 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="label" ticks={oddDayTicks} fontSize={12} />
                            <YAxis yAxisId="left" unit="t" fontSize={12} />
                            <RTooltip contentStyle={{ fontSize: 12 }}
                              formatter={(v: unknown, name: unknown) => {
                                const key = name == null ? "" : String(name);
                                const map: Record<string, string> = { actual: "実績", dailyForward: "フロント予測", daily: "バック予測" };
                                const display = map[key] ?? (key === "label" || key === "undefined" || key === "" ? "" : key);
                                const vs = String(v ?? "");
                                return display ? [`${vs}t`, display] : [`${vs}t`, ""];
                              }}
                            />
                            {showActual && (<Bar dataKey="actual" name="実績" yAxisId="left" fill={C.ok} stackId="a" barSize={18} maxBarSize={32} />)}
                            {showForward && (<Bar dataKey="dailyForward" name="フロント予測" yAxisId="left" fill={"#40a9ff"} stackId="a" barSize={18} maxBarSize={32} />)}
                            {showReverse && (<Area type="monotone" dataKey="daily" name="バック予測" yAxisId="left" stroke={"#fa8c16"} fill={"#fa8c16"} fillOpacity={0.12} dot={{ r: 2 }} />)}
                            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                            <Legend content={(props: any) => <SingleLineLegend {...(props as any)} />} verticalAlign="bottom" />
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
                          <Switch size="small" checked={showCumReverse} onChange={setShowCumReverse} /><span style={{ fontSize: 12 }}>バック予測累積</span>
                        </div>
                        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                          <Switch size="small" checked={showCumActual} onChange={setShowCumActual} /><span style={{ fontSize: 12 }}>実績累積</span>
                        </div>
                      </div>
                      <div style={{ flex: 1, minHeight: 0 }}>
                        <ChartFrame style={{ flex: 1, minHeight: 0 }}>
                          <AreaChart data={cumDailyData} margin={{ left: 0, right: 8, top: 6, bottom: 12 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="label" ticks={oddDayTicks} fontSize={12} />
                            <YAxis unit="t" domain={[0, "auto"]} fontSize={12} />
                            <RTooltip contentStyle={{ fontSize: 12 }}
                              formatter={(v: unknown, name: unknown) => {
                                const map: Record<string, string> = { cumDaily: "バック予測累積", cumActual: "実績累積" };
                                const key = name == null ? "" : String(name);
                                const vs = String(v ?? "");
                                return [`${vs}t`, map[key] ?? key];
                              }}
                            />
                            {showCumReverse && (<Area type="monotone" dataKey="cumDaily" name="バック予測累積" stroke={"#fa8c16"} fill={"#fa8c16"} fillOpacity={0.2} isAnimationActive={false} />)}
                            {showCumActual && (<Area type="monotone" dataKey="cumActual" name="実績累積" stroke={C.ok} fill={C.ok} fillOpacity={0.2} isAnimationActive={false} />)}
                            <Legend verticalAlign="bottom" height={16} />
                            {Array.from({ length: Math.ceil(daysInMonth / 7) }, (_, i) => {
                              const end = Math.min((i + 1) * 7, daysInMonth);
                              const cumTarget = Math.round((monthTarget / Math.ceil(daysInMonth / 7)) * (i + 1));
                              return (
                                <ReferenceLine key={`week-${i}`} x={String(end).padStart(2, "0")} stroke={C.target} strokeDasharray="5 5" strokeWidth={2}
                                  label={({ viewBox }) => {
                                    const vb = viewBox as { x?: number; y?: number; width?: number } | null | undefined;
                                    const vx = vb && vb.x != null ? vb.x + (vb.width ?? 0) / 2 : undefined;
                                    const vy = vb && vb.y != null ? vb.y + 16 : undefined;
                                    return (
                                      <g>
                                        <rect x={(vx ?? 0) - 40} y={(vy ?? 0) - 18} width={80} height={18} rx={6} ry={6} fill="rgba(255,255,255,0.85)" stroke="rgba(0,0,0,0.06)" />
                                        <text x={vx} y={vy} textAnchor="middle" fill={C.target} fontSize={12} fontWeight={700}>
                                          {`W${i + 1}: ${cumTarget}t`}
                                        </text>
                                      </g>
                                    );
                                  }}
                                />
                              );
                            })}
                            <ReferenceLine y={forecast.month_landing.p50} stroke={C.primary} strokeDasharray="3 3" strokeWidth={2}
                              label={{ value: `月末予測: ${forecast.month_landing.p50}t`, position: "right", fill: C.primary, fontSize: 12 }} />
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

/* =========================
 * ページ本体（1ページ=1画面）
 * ========================= */
const InboundForecastDashboardFull: React.FC = () => {
  const [month, setMonth] = useState<IsoMonth>(curMonth());
  const [data, setData] = useState<MonthPayloadDTO | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fetchMonthPayloadMock(month)
      .then((p) => { if (alive) setData(p); })
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [month]);

  if (loading || !data) {
    return (
      <div style={{ minHeight: "100dvh", overflow: "hidden", padding: 0, boxSizing: "border-box", display: "flex", flexDirection: "column", scrollbarGutter: "stable" }}>
        <div style={{ padding: 12, boxSizing: "border-box", flex: 1, minHeight: 0, overflowY: "auto", scrollbarGutter: "stable" }}>
          <Row gutter={[12, 12]} style={{ height: "100%", alignItems: "stretch" }}>
            <Col span={24}><Skeleton active paragraph={{ rows: 6 }} /></Col>
            <Col span={24}><Skeleton active paragraph={{ rows: 6 }} /></Col>
            <Col span={24}><Skeleton active paragraph={{ rows: 6 }} /></Col>
          </Row>
        </div>
      </div>
    );
  }

  // 実績は昨日まで
  const getActualCutoffIso = (m: IsoMonth) => {
    const now = dayjs();
    const monthStart = dayjs(m + "-01");
    if (monthStart.isSame(now, "month")) return now.subtract(1, "day").format("YYYY-MM-DD");
    if (monthStart.isBefore(now, "month")) return monthStart.endOf("month").format("YYYY-MM-DD");
    return monthStart.startOf("month").subtract(1, "day").format("YYYY-MM-DD");
  };
  const actualCutoff = getActualCutoffIso(month);
  const maskedRows: DailyCurveDTO[] = data.daily_curve.map((r) => ({ ...r, actual: r.date <= actualCutoff ? r.actual : undefined }));
  const mtdMasked = sum(maskedRows.map((r) => r.actual ?? 0));
  const remainingBizMasked = data.calendar.days.filter((d) => d.date > actualCutoff && d.is_business_day).length;
  const displayedProgress: ProgressDTO = { mtd_actual: mtdMasked, remaining_business_days: remainingBizMasked };
  const monthJP = monthNameJP(month);

  return (
    <div style={{ minHeight: "100dvh", overflow: "hidden", display: "flex", flexDirection: "column", padding: 0, boxSizing: "border-box", scrollbarGutter: "stable" }}>
      <div style={{ padding: 12, boxSizing: "border-box", flex: 1, minHeight: 0, display: "grid", gridTemplateRows: "auto 1fr 1.2fr", rowGap: 8, overflowY: "auto", scrollbarGutter: "stable" }}>
        {/* ヘッダー */}
        <div>
          <Row justify="space-between" align="middle">
            <Col>
              <Typography.Title level={4} style={{ margin: 0 }}>
                搬入量ダッシュボード — {monthJP}
              </Typography.Title>
            </Col>
            <Col>
              <Space size={8} wrap>
                <DatePicker
                  picker="month"
                  value={dayjs(month, "YYYY-MM")}
                  onChange={(_, s) => typeof s === "string" && setMonth(s)}
                  disabledDate={(d) => {
                    if (!d) return false;
                    const ym = d.format("YYYY-MM");
                    const min = curMonth();
                    const max = nextMonth(curMonth());
                    return ym < min || ym > max;
                  }}
                  style={{ width: 140 }}
                  size="small"
                />
                <Badge count={todayInMonth(month)} style={{ backgroundColor: C.primary }} />
              </Space>
            </Col>
          </Row>
        </div>

        {/* 上段：3カード */}
        <div style={{ minHeight: 0 }}>
          <Row gutter={[12, 12]} style={{ height: "100%", alignItems: "stretch" }}>
            <Col xs={24} lg={7} style={{ height: "100%" }}>
              <TargetCard targets={data.targets} calendarDays={data.calendar.days} progress={displayedProgress} daily_curve={maskedRows} />
            </Col>
            <Col xs={24} lg={12} style={{ height: "100%" }}>
              <CombinedDailyCard rows={maskedRows} prevMonthDaily={data.prev_month_daily} prevYearDaily={data.prev_year_daily} />
            </Col>
            <Col xs={24} lg={5} style={{ height: "100%" }}>
              <CalendarCard days={data.calendar.days} month={month} />
            </Col>
          </Row>
        </div>

        {/* 下段：予測 */}
        <div style={{ minHeight: 0 }}>
          <Row gutter={[8, 8]} style={{ height: "100%" }}>
            <Col xs={24} style={{ height: "100%" }}>
              <ForecastCard forecast={data.forecast} monthTarget={data.targets.month} rows={maskedRows} />
            </Col>
          </Row>
        </div>
      </div>
    </div>
  );
};

export default InboundForecastDashboardFull;
