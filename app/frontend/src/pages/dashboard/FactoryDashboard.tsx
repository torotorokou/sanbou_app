import React, { useEffect, useMemo, useState } from "react";
import dayjs, { Dayjs } from "dayjs";
import {
  Card,
  Row,
  Col,
  Typography,
  DatePicker,
  Calendar,
  Space,
  Tag,
  Progress,
  Tabs,
  Table,
  Skeleton,
  Empty,
  Badge,
  Tooltip,
  Statistic,
  Alert,
  Switch,
} from "antd";
import type { TableColumnsType } from "antd";
import {
  BarChart,
  ComposedChart,
  Bar,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RTooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  Legend,
  ReferenceArea,
  ReferenceLine,
  Cell,
  // AreaChart/Area removed (not used after calendar change)
} from "recharts";
import { InfoCircleOutlined, WarningOutlined } from "@ant-design/icons";

/* ===================================================================
 * 搬入量予測ダッシュボード（単一ファイル・自己完結モック）
 * 目的：アイデアを具体のUIに落とし込んだフルコード
 *
 * 依存：React / TypeScript / Ant Design v5 / Recharts / dayjs
 *
 * カード一覧
 *  1) 目標カード（「月」「週（第n営業週）」「日（平日/土/日祝）」）
 *  2) 目標VS現状実績カード（MTD・残必要量/必要ペース）
 *  3) 搬入量予測カード（当日/週/当月のP50とP帯）
 *  4) 営業カレンダーカード（営業/日祝/非営業のカウント）
 *
 * ※サーバAPI未確定のため、データはモックで生成。
 *   数式・処理はコメントに明記。わからない所はプレースホルダ。
 * =================================================================== */

/* =========================
 * 型
 * ========================= */
type IsoMonth = string; // "YYYY-MM"
type IsoDate = string;  // "YYYY-MM-DD"

type CalendarDay = {
  date: IsoDate;
  is_business_day: 0 | 1;
  is_holiday: 0 | 1;
  week_id: IsoDate; // 週の月曜
};

type HeaderDTO = {
  month: IsoMonth;
  business_days: { total: number; mon_sat: number; sun_holiday: number; non_business: number };
  rules: { week_def: string; week_to_month: string; alignment: string };
};

type TargetsDTO = {
  month: number;
  weeks: { bw_idx: number; week_target: number }[];
  day_weights: { weekday: number; sat: number; sun_hol: number };
};

type ProgressDTO = {
  mtd_actual: number;
  remaining_business_days: number;
};

type ForecastDTO = {
  today: { p50: number; p10: number; p90: number };
  week: { p50: number; p10: number; p90: number; target: number };
  month_landing: { p50: number; p10: number; p90: number };
};

type DailyCurveDTO = {
  date: IsoDate;
  from_7wk: number;         // 直近7週の同曜日平均×補正（A系）
  from_month_share: number; // 月トータル按分（B系）
  bookings: number;         // 予約台数（棒に重ねても良い）
  actual?: number;          // 実際の搬入量（モックで追加）
};

type WeekRowDTO = {
  week_id: IsoDate;
  week_start: IsoDate;
  week_end: IsoDate;
  business_week_index_in_month: number;
  ton_in_month: number;                 // 部分週＝当月に属する営業日の合計
  in_month_business_days: number;
  portion_in_month: number;             // 週営業日中、当月に属した割合
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

/* =========================
 * ユーティリティ
 * ========================= */
const toDate = (s: string) => new Date(s + "T00:00:00");
const ymd = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate()
  ).padStart(2, "0")}`;
const mondayOf = (d: Date) => {
  const day = d.getDay(); // 0 Sun..6 Sat
  const diff = day === 0 ? -6 : 1 - day;
  const m = new Date(d);
  m.setDate(d.getDate() + diff);
  m.setHours(0, 0, 0, 0);
  return m;
};
const addDays = (d: Date, n: number) => {
  const x = new Date(d);
  x.setDate(d.getDate() + n);
  return x;
};
const sum = (a: number[]) => a.reduce((p, c) => p + c, 0);
const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
const pctStr = (v: number | null, d = 1) => (v == null || Number.isNaN(v) ? "—" : `${(v * 100).toFixed(d)}%`);
const monthNameJP = (m: IsoMonth) => {
  const [y, mm] = m.split("-").map(Number);
  return `${y}年${mm}月`;
};
const curMonth = (): IsoMonth => dayjs().format("YYYY-MM");
const prevMonth = (m: IsoMonth): IsoMonth => dayjs(m + "-01").subtract(1, "month").format("YYYY-MM");
const nextMonth = (m: IsoMonth): IsoMonth => dayjs(m + "-01").add(1, "month").format("YYYY-MM");

/* =========================
 * モック生成（サーバAPI未確定のため）
 * - 日曜は非営業（祝日は未実装）※本番では is_holiday で上書き可
 * - 月目標=営業日重み×110t
 * - 週目標=当月営業日配分で按分
 * - P帯=±（残差）で簡易生成（本番はモデル残差から）
 * ========================= */
async function fetchMonthPayloadMock(month: IsoMonth): Promise<MonthPayloadDTO> {
  const first = dayjs(month + "-01");
  const last = first.endOf("month");
  const days: CalendarDay[] = [];
  let d = first;
  while (d.isBefore(last) || d.isSame(last, "day")) {
    const date = d.format("YYYY-MM-DD");
    const dow = d.day();
    const is_business_day = dow === 0 ? 0 : 1; // Sun休
    const is_holiday = dow === 0 ? 1 : 0;      // デモ：日曜=祝日扱い
    days.push({ date, is_business_day, is_holiday, week_id: ymd(mondayOf(d.toDate())) });
    d = d.add(1, "day");
  }

  // 重み（平日=1.0, 土=1.1, 日祝=0.6）— 実績から最適化予定、今は固定
  const wWeekday = 1.0, wSat = 1.1, wSunHol = 0.6;
  const weightOf = (date: string) => {
    const dow = toDate(date).getDay();
    if (dow === 6) return wSat;
    if (dow === 0) return 0; // 非営業日は0（ここでは日曜非営業）
    return wWeekday;
  };
  const dayWeightForBShare = (date: string) => {
    const dow = toDate(date).getDay();
    if (dow === 6) return wSat;
    if (dow === 0) return wSunHol; // 営業としないが「日目標」記載用の重みは残す時に使用可
    return wWeekday;
  };

  // 月目標（営業日重み合計 × 110t）
  const bizWeights = days.map((x) => (x.is_business_day ? weightOf(x.date) : 0));
  const monthTarget = Math.round(sum(bizWeights) * 110);

  // 週（部分週＝当月の営業日のみ合算）
  const weekMap = new Map<
    string,
    { start: IsoDate; end: IsoDate; tonInMonth: number; inMonthBiz: number; fullBiz: number }
  >();
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

  // 日量（モック）：営業日は 100±(sin)±ノイズ、土や季節で微調整
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

  // 週へ集計（当月営業日のみ）
  for (const c of days) {
    const w = weekMap.get(c.week_id);
    if (!w) continue;
    if (c.is_business_day) {
      w.tonInMonth += syntheticDailyTon[c.date];
      w.inMonthBiz += 1;
    }
  }

  // 第n営業週（当月営業日>0の週のみ）
  const weekEntries = [...weekMap.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1));
  let idx = 0;
  const weekRows: WeekRowDTO[] = [];
  for (const [wid, v] of weekEntries) {
    if (v.inMonthBiz > 0) {
      idx += 1;
      weekRows.push({
        week_id: wid,
        week_start: v.start,
        week_end: v.end,
        business_week_index_in_month: idx,
        ton_in_month: Math.round(v.tonInMonth),
        in_month_business_days: v.inMonthBiz,
        portion_in_month: v.fullBiz ? v.inMonthBiz / v.fullBiz : 0,
        targets: { week: 0 }, // 下で按分
        comparisons: {
          vs_prev_week: { delta_ton: null, delta_pct: null, align_note: "prev business week" },
          vs_prev_month_same_idx: { delta_ton: null, delta_pct: null, align_note: "same idx" },
          vs_prev_year_same_idx: { delta_ton: null, delta_pct: null, align_note: "same idx" },
        },
      });
    }
  }

  // 週目標按分：月目標 ×（当月週の営業日重み/当月全営業日重み）
  const totalBizDays = sum(weekRows.map((w) => w.in_month_business_days));
  weekRows.forEach((w) => {
    w.targets.week = totalBizDays ? Math.round(monthTarget * (w.in_month_business_days / totalBizDays)) : 0;
  });

  // 現月内 前営業週比較
  const mapCur: Record<number, number> = {};
  weekRows.forEach((w) => (mapCur[w.business_week_index_in_month] = w.ton_in_month));
  weekRows.forEach((w) => {
    const prevIdx = w.business_week_index_in_month - 1;
    if (prevIdx >= 1 && mapCur[prevIdx] != null) {
      const base = mapCur[prevIdx];
      const dton = w.ton_in_month - base;
      w.comparisons.vs_prev_week.delta_ton = dton;
      w.comparisons.vs_prev_week.delta_pct = base ? dton / base : null;
    }
  });

  // 先月/前年/3年平均（簡易モック：±ランダム）
  const randNear = (a: number, r: number) => Math.round(a * (1 + (Math.random() - 0.5) * r));
  const monthActual = sum(days.map((d) => syntheticDailyTon[d.date]));
  const prevMonthVal = randNear(monthActual, 0.15);
  const prevYearVal = randNear(monthActual, 0.25);
  const avg3yVal = Math.round((monthActual + randNear(monthActual, 0.3) + randNear(monthActual, 0.3)) / 3);

  const history: HistoryDTO = {
    m_vs_prev_month: {
      delta_ton: monthActual - prevMonthVal,
      delta_pct: prevMonthVal ? (monthActual - prevMonthVal) / prevMonthVal : 0,
      align_note: "business-day aligned (mock)",
    },
    m_vs_prev_year: {
      delta_ton: monthActual - prevYearVal,
      delta_pct: prevYearVal ? (monthActual - prevYearVal) / prevYearVal : 0,
    },
    m_vs_3yr_avg: {
      delta_ton: monthActual - avg3yVal,
      delta_pct: avg3yVal ? (monthActual - avg3yVal) / avg3yVal : 0,
    },
  };

  // 目標vs現状
  const today = todayInMonth(month);
  const mtdActual = sum(days.filter((x) => x.date <= today).map((x) => syntheticDailyTon[x.date]));
  const remainingBiz = days.filter((x) => x.date > today && x.is_business_day).length;

  // 予測（P帯簡易）
  const futureTon = sum(days.filter((x) => x.date > today).map((x) => syntheticDailyTon[x.date]));
  const monthP50 = mtdActual + futureTon;
  const pBand = Math.max(80, Math.round(monthP50 * 0.06)); // ±6%帯（デモ）
  const forecast: ForecastDTO = {
    today: { p50: syntheticDailyTon[today] ?? 0, p10: Math.max(0, (syntheticDailyTon[today] ?? 0) - 15), p90: (syntheticDailyTon[today] ?? 0) + 15 },
    week: {
      p50: Math.round(sum(days.filter((x) => toDate(x.date) >= mondayOf(toDate(today)) && toDate(x.date) <= addDays(mondayOf(toDate(today)), 6)).map((x) => syntheticDailyTon[x.date]))),
      p10: 0, p90: 0, target: 0, // 週のP帯は省略（本番で追加）
    },
    month_landing: { p50: monthP50, p10: Math.max(0, monthP50 - pBand), p90: monthP50 + pBand },
  };

  // 1日予測A/B
  const daily_curve: DailyCurveDTO[] = days.map((x, i) => {
    const dow = toDate(x.date).getDay();
    // A: 直近7週（同曜日）平均 — モックでは「近傍日の平均」で近似
    const backIdx = Math.max(0, i - 7);
    const near = days.slice(backIdx, i).filter((d) => toDate(d.date).getDay() === dow);
    const avg = near.length ? Math.round(sum(near.map((d) => syntheticDailyTon[d.date])) / near.length) : syntheticDailyTon[x.date];
    // B: 月トータル按分
    const wAll = sum(days.map((d) => (toDate(d.date).getDay() === 0 ? 0 : dayWeightForBShare(d.date))));
    const wMe = toDate(x.date).getDay() === 0 ? 0 : dayWeightForBShare(x.date);
    const fromMonthShare = wAll ? Math.round((monthTarget * (wMe / wAll))) : 0; // 日目標のイメージ
    const bookings = Math.max(0, Math.round((Math.random() * 6) - (toDate(x.date).getDay() === 0 ? 6 : 0))); // 非営業日は0に寄せる
    return { date: x.date, from_7wk: avg, from_month_share: fromMonthShare, bookings, actual: syntheticDailyTon[x.date] };
  });

  // 先月・前年のダミーデータ（単純に現在のデータにスケールやランダム差を加える）
  const prevMonthDays: Record<IsoDate, number> = {};
  const prevYearDays: Record<IsoDate, number> = {};
  // 先月の日付リストを作る
  const pmFirst = dayjs(month + "-01").subtract(1, "month");
  const pmLast = pmFirst.endOf("month");
  let pd = pmFirst;
  while (pd.isBefore(pmLast) || pd.isSame(pmLast, "day")) {
    const k = pd.format("YYYY-MM-DD");
    const corresponding = dayjs(k).add(1, "month").format("YYYY-MM-DD");
    const base = syntheticDailyTon[corresponding] ?? 80;
    prevMonthDays[k] = Math.max(0, Math.round(base * (0.9 + Math.random() * 0.2)));
    pd = pd.add(1, "day");
  }
  // 前年同月
  const pyFirst = dayjs(month + "-01").subtract(1, "year");
  const pyLast = pyFirst.endOf("month");
  let yd = pyFirst;
  while (yd.isBefore(pyLast) || yd.isSame(pyLast, "day")) {
    const k = yd.format("YYYY-MM-DD");
    const corresponding = dayjs(k).add(1, "year").format("YYYY-MM-DD");
    const base = syntheticDailyTon[corresponding] ?? 80;
    prevYearDays[k] = Math.max(0, Math.round(base * (0.85 + Math.random() * 0.3)));
    yd = yd.add(1, "day");
  }

  // 週目標をtargetsに反映
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
      sun_holiday: days.filter((x) => x.is_business_day && toDate(x.date).getDay() === 0).length, // デモ：0
      non_business: days.filter((x) => !x.is_business_day).length,
    },
    rules: {
      week_def: "ISO Monday-based",
      week_to_month: "partial-weeks included by day",
      alignment: "business-day",
    },
  };

  const progress: ProgressDTO = {
    mtd_actual: mtdActual,
    remaining_business_days: remainingBiz,
  };

  return {
    header,
    targets,
    calendar: { days },
    progress,
    forecast,
    daily_curve,
    weeks: weekRows,
    history: history,
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

const PctBadge: React.FC<{ v: number | null }> = ({ v }) => {
  if (v == null || Number.isNaN(v)) return <span style={{ color: "#8c8c8c" }}>—</span>;
  const up = v >= 0;
  const bg = up ? "#f0f5ff" : "#fff1f0";
  const fg = up ? "#0958d9" : C.danger;
  const arrow = up ? "▲" : "▼";
  return (
    <span style={{ background: bg, color: fg, padding: "0 8px", lineHeight: "22px", borderRadius: 6 }}>
      {arrow} {(Math.abs(v) * 100).toFixed(1)}%
    </span>
  );
};

const Pill: React.FC<{ label: string; value: string | number; unit?: string }> = ({ label, value, unit }) => (
  <span style={{ display: "inline-flex", gap: 6, padding: "2px 8px", borderRadius: 999, background: "#f5f5f5", border: "1px solid #e8e8e8" }}>
    <span style={{ color: "#8c8c8c", fontSize: 12 }}>{label}</span>
    <span style={{ fontVariantNumeric: "tabular-nums" }}>
      {typeof value === "number" ? value.toLocaleString() : value}{unit ? <span style={{ fontSize: 11, marginLeft: 2 }}>{unit}</span> : null}
    </span>
  </span>
);

/* =========================
 * カード1：目標カード
 * ========================= */
const TargetCard: React.FC<{ targets: TargetsDTO; calendarDays: CalendarDay[]; progress?: ProgressDTO; daily_curve?: DailyCurveDTO[] }> = ({ targets, calendarDays, progress, daily_curve }) => {
  // 日目標のサンプル（営業日（平日+土曜）/日祝 の重み）
  const dayWeight = targets.day_weights;
  const weekdayCount = calendarDays.filter((d) => d.is_business_day && toDate(d.date).getDay() >= 1 && toDate(d.date).getDay() <= 5).length;
  const satCount = calendarDays.filter((d) => d.is_business_day && toDate(d.date).getDay() === 6).length;
  const sunHolCount = calendarDays.filter((d) => d.is_business_day && toDate(d.date).getDay() === 0).length; // デモでは0

  // 営業日として平日と土曜をまとめる
  const businessDayCount = weekdayCount + satCount;
  const businessWeight = dayWeight.weekday + dayWeight.sat;

  const totalW = businessDayCount * businessWeight + sunHolCount * dayWeight.sun_hol || 1;
  const oneBusinessDay = Math.round((targets.month * (businessWeight / totalW)) || 0);
  const oneSunHol = Math.round((targets.month * (dayWeight.sun_hol / totalW)) || 0);

  // weekData removed: week chart replaced by per-week cards

  return (
  <Card bordered bodyStyle={{ padding: 8 }}>
      <Space align="baseline" style={{ justifyContent: "space-between", width: "100%" }}>
        <Typography.Title level={5} style={{ margin: 0 }}>目標カード</Typography.Title>
        <Tooltip title="週目標は当月の営業日配分で按分。日目標は平日/土/日祝の重みで配分。">
          <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
        </Tooltip>
      </Space>
      <Row gutter={[12, 12]} style={{ marginTop: 8 }}>
        <Col xs={24} lg={24}>
          {/* 3x3 grid: columns = 目標 / 実績 / 達成率バー、 rows = 1ヶ月 / 1週間 / 1日 */}
          {(() => {
            const todayStr = dayjs().format('YYYY-MM-DD');
            const dayEntry = calendarDays.find((d) => d.date === todayStr) || calendarDays[0];
            const todayWeekId = dayEntry.week_id;
            const weekIds = Array.from(new Set(calendarDays.map((d) => d.week_id))).sort();
            let idx = 0;
            let currentIdx = 1;
            for (const wid of weekIds) {
              const inMonthBiz = calendarDays.filter((d) => d.week_id === wid && d.is_business_day).length;
              if (inMonthBiz > 0) {
                idx += 1;
              }
              if (wid === todayWeekId) {
                currentIdx = idx;
                break;
              }
            }
            const curWeek = targets.weeks.find((w) => w.bw_idx === currentIdx) ?? targets.weeks[targets.weeks.length - 1];
            const weekTarget = curWeek ? curWeek.week_target : 0;
            const thisWeekActual = daily_curve ? sum(daily_curve.filter((d) => {
              const wstart = mondayOf(toDate(todayStr));
              return toDate(d.date) >= wstart && toDate(d.date) <= addDays(wstart, 6);
            }).map((d) => d.actual ?? 0)) : 0;

            const todayActual = daily_curve ? (daily_curve.find((d) => d.date === todayStr)?.actual ?? 0) : 0;

            const rowsData = [
              { key: 'month', label: '1ヶ月', target: targets.month, actual: progress ? progress.mtd_actual : 0 },
              { key: 'week', label: '今週', target: weekTarget, actual: thisWeekActual },
              { key: 'day', label: '1日', target: oneBusinessDay, actual: todayActual },
            ];

            return (
              <div style={{ padding: 8, border: '1px solid #f0f0f0', borderRadius: 8, background: '#fff' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 2fr', columnGap: 14, rowGap: 8, alignItems: 'center' }}>
                  {/* header row */}
                  <div style={{ color: '#8c8c8c', fontSize: 14 }} />
                  <div style={{ color: '#8c8c8c', fontSize: 14, fontWeight: 700 }}>目標</div>
                  <div style={{ color: '#8c8c8c', fontSize: 14, fontWeight: 700 }}>実績</div>
                  <div style={{ color: '#8c8c8c', fontSize: 14, fontWeight: 700 }}>達成率</div>

                  {rowsData.map((r) => {
                    const ratioRaw = r.target ? r.actual / r.target : 0;
                    const pct = r.target ? Math.round(ratioRaw * 100) : 0; // can be >100
                    const barPct = clamp(pct, 0, 100);
                    const pctColor = ratioRaw >= 1 ? C.ok : ratioRaw >= 0.9 ? C.warn : C.danger;

                    return (
                      <React.Fragment key={r.key}>
                        {/* row label */}
                        <div style={{ color: '#595959', fontSize: 14, fontWeight: 800 }}>{r.label}</div>
                        {/* target */}
                        <div>
                          <Statistic value={typeof r.target === 'number' ? r.target : 0} suffix="t" valueStyle={{ color: C.primary, fontSize: 22, fontWeight: 800 }} />
                        </div>
                        {/* actual */}
                        <div>
                          <Statistic value={typeof r.actual === 'number' ? r.actual : 0} suffix="t" valueStyle={{ color: '#222', fontSize: 22, fontWeight: 800 }} />
                        </div>
                        {/* progress (percent + horizontal bar) */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'baseline' }}>
                            <Statistic value={pct} suffix="%" valueStyle={{ color: pctColor, fontSize: 16, fontWeight: 700 }} />
                          </div>
                          <Progress percent={barPct} showInfo={false} strokeColor={pctColor} strokeWidth={8} />
                        </div>
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>
            );
          })()}
        </Col>
      </Row>
    </Card>
  );
};

/* =========================
 * カード：日次累積搬入量（トップレベルコンポーネント）
 * ========================= */
const DailyCumulativeCard: React.FC<{ rows: DailyCurveDTO[]; prevMonthDaily?: Record<IsoDate, number>; prevYearDaily?: Record<IsoDate, number> }> = ({ rows, prevMonthDaily, prevYearDaily }) => {
  const [showPrevMonth, setShowPrevMonth] = useState(false);
  const [showPrevYear, setShowPrevYear] = useState(false);

  // 当月実績の累積を作成しつつ、先月・前年の累積値を埋め込む
  let running = 0;
  let accPM = 0;
  let accPY = 0;
  const cumData = rows.map((r) => {
    running += r.actual ?? 0;
    const yyyy = r.date;
    const pmKey = dayjs(yyyy).subtract(1, 'month').format('YYYY-MM-DD');
    const pyKey = dayjs(yyyy).subtract(1, 'year').format('YYYY-MM-DD');
    const pmVal = prevMonthDaily ? (prevMonthDaily[pmKey] ?? 0) : 0;
    const pyVal = prevYearDaily ? (prevYearDaily[pyKey] ?? 0) : 0;
    accPM += pmVal;
    accPY += pyVal;
    return {
      label: dayjs(r.date).format('DD'),
      yyyyMMdd: r.date,
      actualCumulative: running,
      prevMonthCumulative: accPM,
      prevYearCumulative: accPY,
    } as { label: string; yyyyMMdd: string; actualCumulative: number; prevMonthCumulative: number; prevYearCumulative: number };
  });

  const tooltipFormatter = (...args: unknown[]) => {
    const [v, name, payloadItem] = (args as unknown) as [unknown, unknown, { payload?: Record<string, unknown> }?];
  const map: Record<string, string> = { actualCumulative: '累積実績', prevMonthCumulative: '先月累積', prevYearCumulative: '前年累積' };
    const key = name == null ? '' : String(name);
    const label = key ? (map[key] || key) : '';

    const payload = payloadItem && payloadItem.payload ? payloadItem.payload : null;
    let actualCum: number | null = null;
    if (payload && typeof payload === 'object' && 'actualCumulative' in payload) {
      const a = (payload as Record<string, unknown>)['actualCumulative'];
      if (typeof a === 'number') actualCum = a;
      else if (typeof a === 'string' && !Number.isNaN(Number(a))) actualCum = Number(a);
    }

    if (v == null || v === "" || Number.isNaN(Number(v))) return ['—', label];
    const valNum = Number(v as unknown as number);

    if ((key === 'prevMonthCumulative' || key === 'prevYearCumulative') && actualCum != null && actualCum !== 0) {
      const diffPct = ((valNum - actualCum) / actualCum) * 100;
      const sign = diffPct >= 0 ? '+' : '-';
      const absPct = Math.abs(diffPct).toFixed(1);
      return [`${valNum}t (${sign}${absPct}%)`, label];
    }
    return [`${valNum}t`, label];
  };

  return (
    <Card bordered>
      <Space align="baseline" style={{ justifyContent: 'space-between', width: '100%' }}>
        <Typography.Title level={5} style={{ margin: 0 }}>日次累積搬入量（累積）</Typography.Title>
        <Space size="small">
          <span style={{ color: '#8c8c8c' }}>先月累積</span>
          <Switch size="small" checked={showPrevMonth} onChange={setShowPrevMonth} />
          <span style={{ color: '#8c8c8c' }}>前年累積</span>
          <Switch size="small" checked={showPrevYear} onChange={setShowPrevYear} />
        </Space>
      </Space>
  <div style={{ height: 180, marginTop: 4 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={cumData}>
            <CartesianGrid strokeDasharray="3 3" />
            {/* x軸は奇数日のみ表示 */}
            <XAxis dataKey="label" interval={0} tickFormatter={(v) => {
              // v は '01','02' のような文字列
              const n = Number(String(v));
              if (Number.isNaN(n)) return String(v);
              return n % 2 === 1 ? String(v) : '';
            }} />
            <YAxis unit="t" domain={[0, 'auto']} />
            <RTooltip formatter={tooltipFormatter} />
            <Area type="monotone" dataKey="actualCumulative" stroke={C.actual} fill={C.actual} fillOpacity={0.24} />
            {showPrevMonth && <Line type="monotone" dataKey="prevMonthCumulative" name="prevMonthCumulative" stroke="#40a9ff" dot={false} strokeWidth={3} />}
            {showPrevYear && <Line type="monotone" dataKey="prevYearCumulative" name="prevYearCumulative" stroke="#fa8c16" dot={false} strokeWidth={3} />}
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div style={{ marginTop: 8, display: 'flex', gap: 16, justifyContent: 'center', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div style={{ width: 36, height: 6, background: C.actual, borderRadius: 3 }} />
          <div style={{ color: '#595959' }}>累積実績</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div style={{ width: 36, height: 6, background: '#40a9ff', borderRadius: 3 }} />
          <div style={{ color: '#595959' }}>先月累積</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div style={{ width: 36, height: 6, background: '#fa8c16', borderRadius: 3 }} />
          <div style={{ color: '#595959' }}>前年累積</div>
        </div>
      </div>
    </Card>
  );
};

/* =========================
 * CombinedDailyCard
 * - Segmented で '日次' / '累積' を切り替え
 * - 内部で既存の DailyActualsCard / DailyCumulativeCard のロジックを利用
 * ========================= */
const CombinedDailyCard: React.FC<{ rows: DailyCurveDTO[]; prevMonthDaily?: Record<IsoDate, number>; prevYearDaily?: Record<IsoDate, number> }> = ({ rows, prevMonthDaily, prevYearDaily }) => {
  const items = [
    { key: 'daily', label: '日次', children: <DailyActualsCard rows={rows} prevMonthDaily={prevMonthDaily} prevYearDaily={prevYearDaily} /> },
    { key: 'cumulative', label: '累積', children: <DailyCumulativeCard rows={rows} prevMonthDaily={prevMonthDaily} prevYearDaily={prevYearDaily} /> },
  ];

  return (
    <Card bordered size="small" bodyStyle={{ padding: 8 }}>
      {/* Make the tab header more compact (vertical size ~0.6x): use small size and custom tabBarStyle */}
      <Tabs
        items={items}
        size="small"
        tabBarStyle={{ padding: '4px 8px', minHeight: 26, height: 26, fontSize: 13 }}
      />
    </Card>
  );
};

/* GoalVsActualCard removed per request */

/* =========================
 * カード：日次搬入量（実績）
 * ========================= */
const DailyActualsCard: React.FC<{ rows: DailyCurveDTO[]; prevMonthDaily?: Record<IsoDate, number>; prevYearDaily?: Record<IsoDate, number> }> = ({ rows, prevMonthDaily, prevYearDaily }) => {
  const [showPrevMonth, setShowPrevMonth] = useState(false);
  const [showPrevYear, setShowPrevYear] = useState(false);
  const chartData = rows.map((r) => {
    const prevMonthKey = dayjs(r.date).subtract(1, 'month').format('YYYY-MM-DD');
    const prevYearKey = dayjs(r.date).subtract(1, 'year').format('YYYY-MM-DD');
    return {
      label: dayjs(r.date).format('DD'),
      actual: r.actual ?? 0,
      dateFull: r.date,
      prevMonth: prevMonthDaily ? prevMonthDaily[prevMonthKey] ?? null : null,
      prevYear: prevYearDaily ? prevYearDaily[prevYearKey] ?? null : null,
    };
  });
  const colorForDate = (dateStr: string) => {
    const d = dayjs(dateStr);
    const dow = d.day();
    // detect second Sunday in month
    const isSecondSunday = (() => {
      if (dow !== 0) return false;
      let count = 0;
      let cur = d.startOf('month');
      while (cur.isBefore(d) || cur.isSame(d, 'day')) {
        if (cur.day() === 0) count += 1;
        cur = cur.add(1, 'day');
      }
      return count === 2;
    })();
    if (isSecondSunday) return C.danger; // non-business
    if (dow === 0) return '#ff85c0'; // sunday/holiday
    return C.ok; // business day
  };
  return (
    <Card bordered size="small" bodyStyle={{ padding: 8 }}>
      <Space align="baseline" size="small" style={{ justifyContent: 'space-between', width: '100%', gap: 8 }}>
        <Typography.Title level={5} style={{ margin: 0, fontSize: 14 }}>日次搬入量（実績）</Typography.Title>
        <Tooltip title="実際に搬入された日次トン数（モック）。">
          <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
        </Tooltip>
        <Space size="small">
          <span style={{ color: '#8c8c8c' }}>先月</span>
          <Switch size="small" checked={showPrevMonth} onChange={setShowPrevMonth} />
          <span style={{ color: '#8c8c8c' }}>前年</span>
          <Switch size="small" checked={showPrevYear} onChange={setShowPrevYear} />
        </Space>
      </Space>
      <div style={{ height: 150, marginTop: 4 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
              {/* x軸は奇数日のみ表示 */}
              <XAxis dataKey="label" interval={0} tickFormatter={(v) => {
                const n = Number(String(v));
                if (Number.isNaN(n)) return String(v);
                return n % 2 === 1 ? String(v) : '';
              }} />
            <YAxis unit="t" />
            <RTooltip formatter={(...args) => {
              // args may contain more items; cast via unknown first to satisfy strict typing
              const [v, name, payloadItem] = (args as unknown) as [unknown, unknown, { payload?: Record<string, unknown> }?];
              const map: Record<string, string> = { actual: '実績', prevMonth: '先月', prevYear: '前年' };
              const key = name == null ? '' : String(name);
              const label = key ? (map[key] || key) : '';

              const payload = payloadItem && payloadItem.payload ? payloadItem.payload : null;
              let actualVal: number | null = null;
              if (payload && typeof payload === 'object' && 'actual' in payload) {
                const a = (payload as Record<string, unknown>)['actual'];
                if (typeof a === 'number') actualVal = a;
                else if (typeof a === 'string' && !Number.isNaN(Number(a))) actualVal = Number(a);
              }

              if (v == null || v === "" || Number.isNaN(Number(v))) {
                return ['—', label];
              }

              const valNum = Number(v as unknown as number);

              if ((key === 'prevMonth' || key === 'prevYear') && actualVal != null && actualVal !== 0) {
                const diffPct = ((valNum - actualVal) / actualVal) * 100;
                const sign = diffPct >= 0 ? '+' : '-';
                const absPct = Math.abs(diffPct).toFixed(1);
                return [`${valNum}t (${sign}${absPct}%)`, label];
              }

              return [`${valNum}t`, label];
            }} />
                <Bar dataKey="actual">
                  {chartData.map((entry, idx) => (
                    <Cell key={`cell-${idx}`} fill={colorForDate(entry.dateFull)} />
                  ))}
                </Bar>
                {showPrevMonth && <Line type="monotone" dataKey="prevMonth" stroke="#40a9ff" dot={false} strokeWidth={3} />}
                {showPrevYear && <Line type="monotone" dataKey="prevYear" stroke="#fa8c16" dot={false} strokeWidth={3} />}
          </BarChart>
        </ResponsiveContainer>
      </div>
  {/* 凡例 */}
  <div style={{ marginTop: 6, display: 'flex', gap: 12, justifyContent: 'center', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div style={{ width: 14, height: 14, borderRadius: 3, background: C.ok }} />
          <div style={{ color: '#595959' }}>営業</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div style={{ width: 14, height: 14, borderRadius: 3, background: '#ff85c0' }} />
          <div style={{ color: '#595959' }}>予約</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div style={{ width: 14, height: 14, borderRadius: 3, background: C.danger }} />
          <div style={{ color: '#595959' }}>休業</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div style={{ width: 36, height: 6, background: '#40a9ff', borderRadius: 3 }} />
          <div style={{ color: '#595959' }}>先月日</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div style={{ width: 36, height: 6, background: '#fa8c16', borderRadius: 3 }} />
          <div style={{ color: '#595959' }}>前年比</div>
        </div>
      </div>
    </Card>
  );
};

/* =========================
 * カード3：搬入量予測カード（当日/週/当月）
 * ========================= */
const ForecastCard: React.FC<{ forecast: ForecastDTO; monthTarget: number; rows?: DailyCurveDTO[] }> = ({ forecast, monthTarget, rows }) => {
  // Use provided rows (daily_curve) when available so actual values are unified
  const rowsData = rows && rows.length ? rows : [];
  const month = rowsData.length ? dayjs(rowsData[0].date).format('YYYY-MM') : curMonth();
  const daysInMonth = rowsData.length ? rowsData.length : dayjs(month + '-01').daysInMonth();
  const base = monthTarget && daysInMonth ? monthTarget / daysInMonth : 0;
  const chartData = [] as { label: string; daily: number; cumulative: number; dailyForward?: number; actual?: number }[];
  let running = 0;
  // determine forward window start (today if same month else month start)
  const todayDate = dayjs();
  const monthStart = dayjs(month + '-01');
  let forwardStartDay = 1;
  if (todayDate.format('YYYY-MM') === month) forwardStartDay = todayDate.date();
  // else keep as 1 (start of month)
  const forwardEndDay = Math.min(daysInMonth, forwardStartDay + 6);

  if (rowsData.length) {
    // build chartData from rowsData, using generated daily for reverse prediction
    for (let idx = 0; idx < rowsData.length; idx++) {
      const r = rowsData[idx];
      const i = idx + 1;
      const factor = 0.9 + 0.2 * (0.5 + Math.sin((i / daysInMonth) * Math.PI * 2) / 2);
      const daily = Math.round(base * factor);
      running += daily;
      const dailyForward = i >= forwardStartDay && i <= forwardEndDay ? Math.round(base * (0.9 + 0.2 * (0.5 + Math.sin((i / daysInMonth) * Math.PI * 2) / 2))) : 0;
      const actualDay = r.actual ?? 0;
      chartData.push({ label: String(i).padStart(2, '0'), daily, cumulative: running, dailyForward, actual: actualDay });
    }
  } else {
    for (let i = 1; i <= daysInMonth; i++) {
      const factor = 0.9 + 0.2 * (0.5 + Math.sin((i / daysInMonth) * Math.PI * 2) / 2);
      const daily = Math.round(base * factor);
      running += daily;
      const dailyForward = i >= forwardStartDay && i <= forwardEndDay ? Math.round(base * (0.9 + 0.2 * (0.5 + Math.sin((i / daysInMonth) * Math.PI * 2) / 2))) : 0;
      const actualDay = i < forwardStartDay ? Math.round(Math.round(base * (0.9 + 0.2 * (0.5 + Math.sin((i / daysInMonth) * Math.PI * 2) / 2))) * (0.95 + Math.random() * 0.1)) : 0;
      chartData.push({ label: String(i).padStart(2, '0'), daily, cumulative: running, dailyForward, actual: actualDay });
    }
  }  // approximate targets for day/week (simple split)
  const dayTarget = monthTarget && daysInMonth ? Math.round(monthTarget / daysInMonth) : 0;
  const weekTarget = dayTarget * 7;
  const [showActual, setShowActual] = useState(true);
  const [showForward, setShowForward] = useState(true);
  const [showReverse, setShowReverse] = useState(true);
  const [showCumReverse, setShowCumReverse] = useState(true);
  const [showCumActual, setShowCumActual] = useState(true);

  // Build cumulative series based on the 'daily' (逆行) series and 'actual' explicitly
  const cumDailyData = (() => {
    let runReverse = 0;
    let runActual = 0;
    return chartData.map((d) => {
      runReverse += Number(d.daily || 0);
      runActual += Number(d.actual || 0);
      return { ...d, cumDaily: runReverse, cumActual: runActual };
    });
  })();

  // Compute week end cumulative forecasts (simple: divide monthTarget by weeks and cumulate)
  const weeksInMonth = Math.ceil(daysInMonth / 7);
  const weekTargetAvg = monthTarget / weeksInMonth;
  const weekEndForecasts = [] as { day: number; cumTarget: number }[];
  for (let w = 1; w <= weeksInMonth; w++) {
    const endDay = Math.min(w * 7, daysInMonth);
    weekEndForecasts.push({ day: endDay, cumTarget: Math.round(weekTargetAvg * w) });
  }
  // Month end forecast from forecast.month_landing.p50
  const monthEndForecast = forecast.month_landing.p50;

  return (
    <Card bordered>
      <Space align="baseline" style={{ justifyContent: "space-between", width: "100%" }}>
        <Typography.Title level={5} style={{ margin: 0 }}>搬入量予測（P50 / P10–P90）</Typography.Title>
        <Tooltip title="P帯はモデル残差から推定（本番）。ここではデモ値。">
          <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
        </Tooltip>
      </Space>

      <div style={{ marginTop: 8 }}>
        <Row gutter={[12, 12]}>
          {/* Left: stacked 3 rows */}
          <Col xs={24} lg={8}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {/* 当日 */}
              {(() => {
                const ratio = dayTarget ? forecast.today.p50 / dayTarget : null;
                const pct = ratio != null ? Math.round(ratio * 100) : null;
                const pctColor = ratio == null ? '#8c8c8c' : ratio >= 1 ? C.ok : ratio >= 0.9 ? C.warn : C.danger;
                return (
                  <Card size="small">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ flex: 1 }}>
                        <Tag color="blue">当日</Tag>
                        <div style={{ color: '#8c8c8c', fontSize: 12 }}>レンジ: {forecast.today.p10}–{forecast.today.p90}</div>
                      </div>
                      <div style={{ width: 120, textAlign: 'right' }}>
                        <div style={{ color: C.primary, fontSize: 20, fontWeight: 800 }}>{forecast.today.p50.toLocaleString()}<span style={{ fontSize: 12 }}>t</span></div>
                      </div>
                      <div style={{ width: 110 }}>
                        {pct != null ? (
                          <div>
                            <Progress percent={clamp(pct, 0, 200)} showInfo={false} strokeColor={pctColor} strokeWidth={8} />
                            <div style={{ textAlign: 'center', marginTop: 4, color: pctColor, fontWeight: 700 }}>{pct}%</div>
                          </div>
                        ) : (
                          <div style={{ color: '#8c8c8c', textAlign: 'center' }}>目標不明</div>
                        )}
                      </div>
                    </div>
                  </Card>
                );
              })()}

              {/* 今週合計 */}
              {(() => {
                const ratio = weekTarget ? forecast.week.p50 / weekTarget : null;
                const pct = ratio != null ? Math.round(ratio * 100) : null;
                const pctColor = ratio == null ? '#8c8c8c' : ratio >= 1 ? C.ok : ratio >= 0.9 ? C.warn : C.danger;
                return (
                  <Card size="small">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ flex: 1 }}>
                        <Tag color="blue">今週合計</Tag>
                        <div style={{ color: '#8c8c8c', fontSize: 12 }}>(週のP帯は簡易表示)</div>
                      </div>
                      <div style={{ width: 120, textAlign: 'right' }}>
                        <div style={{ color: C.primary, fontSize: 20, fontWeight: 800 }}>{forecast.week.p50.toLocaleString()}<span style={{ fontSize: 12 }}>t</span></div>
                      </div>
                      <div style={{ width: 110 }}>
                        {pct != null ? (
                          <div>
                            <Progress percent={clamp(pct, 0, 200)} showInfo={false} strokeColor={pctColor} strokeWidth={8} />
                            <div style={{ textAlign: 'center', marginTop: 4, color: pctColor, fontWeight: 700 }}>{pct}%</div>
                          </div>
                        ) : (
                          <div style={{ color: '#8c8c8c', textAlign: 'center' }}>目標不明</div>
                        )}
                      </div>
                    </div>
                  </Card>
                );
              })()}

              {/* 今月末 */}
              {(() => {
                const ratio = monthTarget ? forecast.month_landing.p50 / monthTarget : null;
                const pct = ratio != null ? Math.round(ratio * 100) : null;
                const pctColor = ratio == null ? '#8c8c8c' : ratio >= 1 ? C.ok : ratio >= 0.9 ? C.warn : C.danger;
                return (
                  <Card size="small">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ flex: 1 }}>
                        <Tag color="blue">今月末</Tag>
                        <div style={{ color: '#8c8c8c', fontSize: 12 }}>目標: {monthTarget.toLocaleString()} t</div>
                      </div>
                      <div style={{ width: 120, textAlign: 'right' }}>
                        <div style={{ color: C.primary, fontSize: 20, fontWeight: 800 }}>{forecast.month_landing.p50.toLocaleString()}<span style={{ fontSize: 12 }}>t</span></div>
                      </div>
                      <div style={{ width: 110 }}>
                        {pct != null ? (
                          <div>
                            <Progress percent={clamp(pct, 0, 200)} showInfo={false} strokeColor={pctColor} strokeWidth={8} />
                            <div style={{ textAlign: 'center', marginTop: 4, color: pctColor, fontWeight: 700 }}>{pct}%</div>
                          </div>
                        ) : (
                          <div style={{ color: '#8c8c8c', textAlign: 'center' }}>目標不明</div>
                        )}
                      </div>
                    </div>
                  </Card>
                );
              })()}
            </div>
          </Col>

          {/* Right: tabbed charts (daily / cumulative) */}
          <Col xs={24} lg={16}>
            <Tabs
              size="small"
              tabBarStyle={{ padding: '4px 8px', minHeight: 28, height: 28, fontSize: 13 }}
              items={[
                {
                  key: 'reverse',
                  label: '日次',
                  children: (
                    <div style={{ height: 200 }}>
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginBottom: 8 }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <Switch size="small" checked={showActual} onChange={(checked) => setShowActual(checked)} />
                          <span style={{ fontSize: 12 }}>実績</span>
                        </div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <Switch size="small" checked={showForward} onChange={(checked) => setShowForward(checked)} />
                          <span style={{ fontSize: 12 }}>順行（7日）</span>
                        </div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <Switch size="small" checked={showReverse} onChange={(checked) => setShowReverse(checked)} />
                          <span style={{ fontSize: 12 }}>逆行（今月）</span>
                        </div>
                      </div>
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="label" interval={Math.max(0, Math.floor(daysInMonth / 10))} />
                          <YAxis yAxisId="left" unit="t" />
                          <RTooltip formatter={(v: any, name: any) => {
                            // Map common dataKey/names to friendly Japanese labels and avoid showing 'label' or 'undefined'
                            const key = name == null ? '' : String(name);
                            const map: Record<string, string> = {
                              actual: '実績',
                              dailyForward: '順行(P50)',
                              daily: '逆行(P50)',
                              cumulative: '累積',
                            };
                            const display = map[key] ?? (key === 'label' || key === 'undefined' || key === '' ? '' : key);
                            // If display is empty, only show the value without a trailing label
                            return display ? [`${v}t`, display] : [`${v}t`, ''];
                          }} />
                          {showActual && <Bar dataKey="actual" name="実績" yAxisId="left" fill={C.ok} barSize={8} />}
                          {showForward && <Bar dataKey="dailyForward" name="順行(P50)" yAxisId="left" fill={'#40a9ff'} barSize={8} />}
                          {showReverse && (
                            <Area
                              type="monotone"
                              dataKey="daily"
                              name="逆行(P50)"
                              yAxisId="left"
                              stroke={'#fa8c16'}
                              fill={'#fa8c16'}
                              fillOpacity={0.12}
                              dot={{ r: 3 }}
                            />
                          )}
                          {/* 'daily' series removed per request: only actual and forward remain */}
                          <Legend verticalAlign="top" height={24} formatter={(value: any) => {
                            if (value == null) return '';
                            const s = String(value);
                            if (s === 'label' || s === 'undefined') return '';
                            return s;
                          }} />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                  ),
                },
                {
                  key: 'cumulative',
                  label: '累積',
                  children: (
                    <div style={{ height: 200 }}>
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginBottom: 8 }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <Switch size="small" checked={showCumReverse} onChange={(checked) => setShowCumReverse(checked)} />
                          <span style={{ fontSize: 12 }}>逆行累積</span>
                        </div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <Switch size="small" checked={showCumActual} onChange={(checked) => setShowCumActual(checked)} />
                          <span style={{ fontSize: 12 }}>実績累積</span>
                        </div>
                      </div>
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={cumDailyData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="label" interval={Math.max(0, Math.floor(daysInMonth / 10))} />
                          <YAxis unit="t" domain={[0, 'auto']} />
                          <RTooltip formatter={(v: any, name: any) => {
                            const key = name == null ? '' : String(name);
                            const map: Record<string, string> = {
                              cumDaily: '逆行累積',
                              cumActual: '実績累積',
                            };
                            const display = map[key] ?? key;
                            return [`${v}t`, display];
                          }} />
                          {showCumReverse && <Area type="monotone" dataKey="cumDaily" name="逆行累積" stroke={'#fa8c16'} fill={'#fa8c16'} fillOpacity={0.2} />}
                          {showCumActual && <Area type="monotone" dataKey="cumActual" name="実績累積" stroke={C.ok} fill={C.ok} fillOpacity={0.2} />}
                          {/* Week end forecast lines */}
                          {weekEndForecasts.map((wf, idx) => (
                            <ReferenceLine
                              key={`week-${idx}`}
                              x={String(wf.day).padStart(2, '0')}
                              stroke={C.target}
                              strokeDasharray="5 5"
                              strokeWidth={2}
                              label={{ value: `週末予測: ${wf.cumTarget}t`, position: 'top', fill: C.target, fontSize: 10 }}
                            />
                          ))}
                          {/* Month end forecast line */}
                          <ReferenceLine
                            y={monthEndForecast}
                            stroke={C.primary}
                            strokeDasharray="3 3"
                            strokeWidth={2}
                            label={{ value: `月末予測: ${monthEndForecast}t`, position: 'right', fill: C.primary, fontSize: 11 }}
                          />
                          <Legend verticalAlign="top" height={24} formatter={(value: any) => {
                            if (value == null) return '';
                            const s = String(value);
                            if (s === 'label' || s === 'undefined') return '';
                            return s;
                          }} />
                        </AreaChart>
                      </ResponsiveContainer>
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
 * カード6：営業カレンダー（カウント）
 * ========================= */
const CalendarCard: React.FC<{ days: CalendarDay[]; month?: IsoMonth }> = ({ days, month = curMonth() }) => {
  // CalendarCard コンポーネントの先頭あたりに追加
  const fixedValue = useMemo(() => dayjs(month + '-01'), [month]);

  // 処理用に Map を構築
  const dayMap = useMemo(() => {
    const m = new Map<string, CalendarDay>();
    days.forEach((d) => m.set(d.date, d));
    return m;
  }, [days]);

  // 各種日数を集計：平日(Mon–Sat)、通常日曜、非営業（第2日曜）
  const dayCounts = useMemo(() => {
    let weekday = 0;
    let sunday = 0;
    let secondSunday = 0;
    let weekdayRem = 0;
    let sundayRem = 0;
    let secondSundayRem = 0;
    const todayStr = dayjs().format('YYYY-MM-DD');
    days.forEach((d) => {
      const dt = dayjs(d.date);
      const dow = dt.day();
      // 第2日曜の判定
      const isSecond = (() => {
        if (dow !== 0) return false;
        let count = 0;
        let cur = dt.startOf('month');
        while (cur.isBefore(dt) || cur.isSame(dt, 'day')) {
          if (cur.day() === 0) count += 1;
          cur = cur.add(1, 'day');
        }
        return count === 2;
      })();

      if (isSecond) {
        secondSunday += 1;
        if (d.date >= todayStr) secondSundayRem += 1;
      } else if (dow === 0) {
        sunday += 1;
        if (d.date >= todayStr) sundayRem += 1;
      } else {
        weekday += 1; // Mon–Sat (excluding Sundays)
        if (d.date >= todayStr) weekdayRem += 1;
      }
    });
    return { weekday, sunday, secondSunday, weekdayRem, sundayRem, secondSundayRem };
  }, [days]);

  const dateCellRender = (value: Dayjs): React.ReactNode => {
    const key = value.format('YYYY-MM-DD');
    const info = dayMap.get(key);
    if (!info) return null;

    const dow = value.day(); // 0 Sun .. 6 Sat
  const isHoliday = info.is_holiday === 1;

    // 判定：当月の第2日曜日を検出
    const isSecondSunday = (() => {
      if (dow !== 0) return false;
      let count = 0;
      let d = value.startOf('month');
      while (d.isBefore(value) || d.isSame(value, 'day')) {
        if (d.day() === 0) count += 1;
        d = d.add(1, 'day');
      }
      return count === 2;
    })();

    // カラー選定：第2日曜のみを非営業（濃赤）、通常の日曜/祝日はピンク、それ以外は緑
    let color = C.ok; // default green
    if (isSecondSunday) {
      color = C.danger; // 濃い赤 for second Sunday (non-business)
    } else if (dow === 0 || isHoliday) {
      color = '#ff85c0'; // pink for ordinary Sunday/holiday
    } else {
      color = C.ok; // green for Mon-Sat
    }

    // 当日を強調表示（黄色）
    const todayKey = dayjs().format('YYYY-MM-DD');
    const isToday = key === todayKey;
    let textColor = '#fff';
    if (isToday) {
      color = '#fadb14'; // Ant Design yellow-4
      textColor = '#000';
    }

    // Compact badge with day number
  const inMonth = value.format('YYYY-MM') === month;
    const dayNum = value.date();
    if (!inMonth) {
      // render muted small number for other-month dates
      return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', paddingTop: 6 }}>
          <div style={{ width: 20, height: 20, borderRadius: 4, color: '#bfbfbf', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11 }}>{dayNum}</div>
        </div>
      );
    }

    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', paddingTop: 6 }}>
        <div style={{ width: 22, height: 22, borderRadius: 6, background: color, display: 'flex', alignItems: 'center', justifyContent: 'center', color: textColor, fontSize: 12, fontWeight: 600 }}>{dayNum}</div>
      </div>
    );
  };

  const header = (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100%', gap: 6, alignItems: 'center' }}>
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}>
          <Typography.Title level={5} style={{ margin: 0, fontSize: 20 }}>営業カレンダー</Typography.Title>
          <Tooltip title="最終判定は is_business_day。祝日や独自休業はサーバで上書き。">
            <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
          </Tooltip>
        </div>
      </div>
      {/* 2行目：日数と残り日数のみ表示（文言は非表示） */}
      <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap', justifyContent: 'center' }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: 12 }}>
          <div style={{ width: 12, height: 12, borderRadius: 3, background: C.ok }} />
          <div style={{ color: '#595959', fontWeight: 700, fontSize: 12 }}>{dayCounts.weekday}<span style={{ color: '#8c8c8c', fontWeight: 400, fontSize: 11, marginLeft: 6 }}>({dayCounts.weekdayRem})</span></div>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: 12 }}>
          <div style={{ width: 12, height: 12, borderRadius: 3, background: '#ff85c0' }} />
          <div style={{ color: '#595959', fontWeight: 700, fontSize: 12 }}>{dayCounts.sunday}<span style={{ color: '#8c8c8c', fontWeight: 400, fontSize: 11, marginLeft: 6 }}>({dayCounts.sundayRem})</span></div>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: 12 }}>
          <div style={{ width: 12, height: 12, borderRadius: 3, background: C.danger }} />
          <div style={{ color: '#595959', fontWeight: 700, fontSize: 12 }}>{dayCounts.secondSunday}<span style={{ color: '#8c8c8c', fontWeight: 400, fontSize: 11, marginLeft: 6 }}>({dayCounts.secondSundayRem})</span></div>
        </div>
      </div>
    </div>
  );

  return (
    <Card bordered size="small">
      {header}
      <div style={{ marginTop: 8 }}>
        {/* カレンダーは表示中の月に固定 */}
          <Calendar
            key={month}                              // 月が変わった時だけ内部状態をリセット
            fullscreen={false}
            mode="month"                             // 常に月表示
            value={fixedValue}                       // 表示月を固定
            validRange={[fixedValue.startOf('month'), fixedValue.endOf('month')]} // 範囲外の移動を禁止
            disabledDate={(cur) => !!cur && cur.format('YYYY-MM') !== month}      // 当月以外は選択不可（見た目も無効）
            headerRender={() => null}                // ヘッダー操作を無効化
            onPanelChange={() => { /* 移動させない */ }}
            onChange={() => { /* 変更させない */ }}
            onSelect={() => { /* クリック選択も無視 */ }}
            // セル内クリックによるデフォルト動作を完全に抑止
            dateFullCellRender={(value) => (
              <div
                onMouseDown={(e) => e.preventDefault()}
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
                style={{ cursor: 'default' }}
              >
                {dateCellRender(value)}
              </div>
            )}
          />
      </div>
    </Card>
  );
};

/* =========================
 * ページ本体
 * ========================= */
const InboundForecastDashboardFull: React.FC = () => {
  const [month, setMonth] = useState<IsoMonth>(curMonth());
  const [data, setData] = useState<MonthPayloadDTO | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fetchMonthPayloadMock(month).then((p) => {
      if (alive) setData(p);
    }).finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [month]);

  const disabledMonth = (d: Dayjs) => {
    if (!d) return false;
    const ym = d.format("YYYY-MM");
    const min = curMonth();
    const max = nextMonth(curMonth()); // 当月〜翌月まで
    return ym < min || ym > max;
  };

  if (loading || !data) {
    return (
      <div style={{ padding: 16 }}>
        <Row gutter={[12, 12]}>
          <Col span={24}><Skeleton active paragraph={{ rows: 6 }} /></Col>
          <Col span={24}><Skeleton active paragraph={{ rows: 6 }} /></Col>
          <Col span={24}><Skeleton active paragraph={{ rows: 6 }} /></Col>
        </Row>
      </div>
    );
  }

  const monthJP = monthNameJP(month);

  return (
    <div style={{ padding: 16 }}>
      {/* ヘッダー */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 8 }}>
        <Col>
          <Typography.Title level={4} style={{ margin: 0 }}>
            搬入量ダッシュボード — {monthJP}
          </Typography.Title>
          <div style={{ color: "#8c8c8c" }}>月ページ固定 / 週は部分週（日で帰属） / 営業日アライメントで比較</div>
        </Col>
        <Col>
          <Space size={8} wrap>
            <DatePicker
              picker="month"
              value={dayjs(month, "YYYY-MM")}
              onChange={(_, s) => typeof s === "string" && setMonth(s)}
              disabledDate={disabledMonth}
              style={{ width: 140 }}
              size="small"
            />
            <Badge count={todayInMonth(month)} style={{ backgroundColor: C.primary }} />
          </Space>
        </Col>
      </Row>

      {/* 1段目：目標カード、日次・累積カード、営業カレンダーを1行に並べる */}
      <Row gutter={[12, 12]}>
        <Col xs={24} lg={7}>
          <TargetCard targets={data.targets} calendarDays={data.calendar.days} progress={data.progress} daily_curve={data.daily_curve} />
        </Col>
        <Col xs={24} lg={12}>
          <CombinedDailyCard rows={data.daily_curve} prevMonthDaily={data.prev_month_daily} prevYearDaily={data.prev_year_daily} />
        </Col>
        <Col xs={24} lg={5}>
          <CalendarCard days={data.calendar.days} month={month} />
        </Col>
      </Row>

      <Row gutter={[12, 12]} style={{ marginTop: 8 }}>
        <Col xs={24}>
          <ForecastCard forecast={data.forecast} monthTarget={data.targets.month} rows={data.daily_curve} />
        </Col>
      </Row>
    </div>
  );
};

export default InboundForecastDashboardFull;

