import React, { useEffect, useMemo, useState } from 'react';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import type { FC } from 'react';
import {
  Card, Row, Col, Typography, DatePicker, Space, Button, Progress, Tag,
  Tooltip as AntTooltip, Skeleton, Tabs, Table, Segmented, Badge
} from 'antd';
import type { TableColumnsType } from 'antd';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend, Line, ReferenceArea
} from 'recharts';
import { InfoCircleOutlined } from '@ant-design/icons';

/* =========================================================
 * 搬入量ダッシュボード（上段=2×2：統一高さ / 下段=根拠）
 * - 比較トグル：今月 / 先月 / 前年同月（営業日補正で比較）
 * - カード責務の整理：HeroKPI（月目標&MTD）/ ActionPace（必要ペース）/
 *   今日・今週見込み（現行vsAI）/ 月着地（現行vsAI）
 * - 週別（確定のみ）/ 日別（週タブ）は据え置き＋比較系列の点線
 * ========================================================= */

const Colors = {
  actual: '#52c41a',
  forecast: '#1677ff',
  pace:    '#6c757d',
  target:  '#faad14',
  bad:     '#cf1322',
  warn:    '#fa8c16',
  good:    '#389e0d',
  baseline: '#9e9e9e', // 比較系列（先月/前年）
} as const;

const DENSE = {
  gutter: 12,
  cardPad: 10,
  headPad: '6px 10px',
  kpiMd: 22,
  kpiLg: 26,
  chartH: 240,
  cellMinH: 160,
} as const;

/* =========================
 * 型
 * ========================= */
type YYYYMM = string;
type YYYYMMDD = string;

type DailyPoint = {
  date: YYYYMMDD;
  predicted: number;
  actual?: number;
  target?: number;
  isBusinessDay?: boolean;
};
type Week = { key: string; index: number; start: Date; end: Date; days: Date[]; label: string; };
type WeeklyConfirmedRow = {
  key: string; label: string;
  targetSum: number; actualSum: number; rateConfirmed: number | null;
  bizDays: number; sunHoliDays: number; offDays: number;
};
type AdoptedKind = 'AI' | '現行';
type CompareBasis = 'now' | 'prevMonth' | 'prevYear';

type SeriesBundle = {
  base: DailyPoint[];
  prevMonth?: DailyPoint[];
  prevYear?: DailyPoint[];
}

/* =========================
 * Repository（Mock）
 * ========================= */
interface ForecastRepository {
  fetchSeriesBundle: (month: YYYYMM) => Promise<SeriesBundle>;
}

const mkMonthSeries = (month: YYYYMM, opts?: { noise?: number; shift?: number }) => {
  const days = Array.from({ length: 31 }, (_, i) => i + 1);
  return days.map((d) => {
    const date = `${month}-${String(d).padStart(2, '0')}`;
    const base = 100 + Math.sin((d / 31) * Math.PI * 2) * 20 + (opts?.shift ?? 0);
    const predicted = Math.max(40, Math.round(base + (Math.random() * (opts?.noise ?? 10) - (opts?.noise ?? 10)/2)));
    const todayDate = new Date();
    const currentYM = `${todayDate.getFullYear()}-${String(todayDate.getMonth() + 1).padStart(2, '0')}`;
    const isCurrentMonth = month === currentYM;
    // デモ：カレント月のみ20日を“今日”とみなす
    const actual = isCurrentMonth ? (d < 20 ? Math.max(35, Math.round(predicted * (0.9 + Math.random() * 0.2))) : undefined)
                                  : Math.max(35, Math.round(predicted * (0.9 + Math.random() * 0.2)));
    const target = 110 + (opts?.shift ?? 0) * 0.1;
    const dow = new Date(date + 'T00:00:00').getDay();
    const isBusinessDay = dow !== 0; // 日曜休み
    return { date, predicted, actual, target, isBusinessDay };
  });
};

const mockRepo: ForecastRepository = {
  async fetchSeriesBundle(month) {
    const base = mkMonthSeries(month, { noise: 10, shift: 0 });
    const prevM = prevMonthStr(month);
    const prevY = `${Number(month.slice(0, 4)) - 1}-${month.slice(5, 7)}`;
    const prevMonth = mkMonthSeries(prevM, { noise: 12, shift: -5 });
    const prevYear = mkMonthSeries(prevY, { noise: 12, shift: -8 });
    return { base, prevMonth, prevYear };
  },
};

/* =========================
 * Util
 * ========================= */
const sum = (arr: number[]) => arr.reduce((a, b) => a + b, 0);
const avg = (arr: number[]) => (arr.length ? sum(arr) / arr.length : 0);
const toDate = (d: string) => new Date(d + 'T00:00:00');
const pctStr = (v: number | null | undefined, digits = 0) => (v == null ? '—' : `${(v * 100).toFixed(digits)}%`);
const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
function ymd(d: Date): YYYYMMDD { const y = d.getFullYear(); const m = String(d.getMonth() + 1).padStart(2, '0'); const day = String(d.getDate()).padStart(2, '0'); return `${y}-${m}-${day}`; }
function formatMonthJP(month: YYYYMM) { const [y, m] = month.split('-').map(Number); return `${y}年${m}月`; }
function formatRangeJP(a: Date, b: Date) { return `${a.getMonth() + 1}/${a.getDate()}–${b.getMonth() + 1}/${b.getDate()}`; }
function currentMonth(): YYYYMM { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`; }
function nextMonthStr(month: YYYYMM): YYYYMM { const [y, m] = month.split('-').map(Number); const d = new Date(y, m - 1, 1); d.setMonth(d.getMonth() + 1); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`; }
function prevMonthStr(month: YYYYMM): YYYYMM { const [y, m] = month.split('-').map(Number); const d = new Date(y, m - 1, 1); d.setMonth(d.getMonth() - 1); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`; }
function yyyymmddTodayFromMonth(month: YYYYMM): YYYYMMDD { const now = new Date(); const currentYM = currentMonth(); if (month === currentYM) return `${month}-${String(now.getDate()).padStart(2, '0')}`; return `${month}-20`; }
function getIsoMonday(d: Date) { const day = d.getDay(); const diff = (day === 0 ? -6 : 1 - day); const monday = new Date(d); monday.setDate(d.getDate() + diff); monday.setHours(0, 0, 0, 0); return monday; }
function addDays(date: Date, n: number) { const dd = new Date(date); dd.setDate(date.getDate() + n); return dd; }
function buildWeeks(month: YYYYMM): Week[] {
  const [y, m] = month.split('-').map(Number);
  const first = new Date(y, m - 1, 1);
  const last = new Date(y, m, 0);
  const firstMonday = getIsoMonday(first);
  const weeks: Week[] = [];
  let start = new Date(firstMonday);
  let i = 1;
  while (start <= last) {
    const days = Array.from({ length: 6 }, (_, k) => addDays(start, k)); // Mon..Sat
    const end = days[5];
    const inMonth = days.some(d => d.getMonth() === (m - 1));
    if (inMonth) {
      const label = `${i}週目（${formatRangeJP(days[0], days[5])}）`;
      weeks.push({ key: `W${i}`, index: i - 1, start, end, days, label });
      i++;
    }
    start = addDays(start, 7);
  }
  return weeks;
}

/* =========================
 * UseCase
 * ========================= */
const monthTargetSum = (all: DailyPoint[]) => sum(all.map(r => r.target ?? 0));
const actualSumMonth = (all: DailyPoint[], today: YYYYMMDD) => sum(all.filter(r => r.date <= today).map(r => r.actual ?? 0));
const bizDayCountTo = (all: DailyPoint[], today: YYYYMMDD) => all.filter(d => d.date <= today && d.isBusinessDay !== false).length;
const monthBizDays = (all: DailyPoint[]) => all.filter(d => d.isBusinessDay !== false).length;

function computeMonthRates(all: DailyPoint[], today: YYYYMMDD) {
  const mActual = actualSumMonth(all, today);
  const mDenMTD = sum(all.filter(r => r.date <= today).map(r => r.target ?? 0));
  const mtdRate = mDenMTD ? mActual / mDenMTD : null;
  const futurePred = sum(all.filter(r => r.date > today).map(r => r.predicted ?? 0));
  const landingAI = mActual + futurePred;
  const mTarget = monthTargetSum(all);
  const monthRateProj = mTarget ? landingAI / mTarget : null;
  return { mActual, mTarget, landingAI, mtdRate, monthRateProj };
}

function currentBusinessPace(all: DailyPoint[], today: YYYYMMDD, n = 7) {
  const rows = all.filter(d => d.date < today && d.isBusinessDay !== false);
  const recent = rows.slice(-n);
  const vals = recent.map(d => d.actual ?? 0).filter(v => v != null);
  if (!vals.length) return null;
  return avg(vals);
}

function landingByCurrentPace(all: DailyPoint[], today: YYYYMMDD, paceBiz: number | null, paceHoliday = 0) {
  const mActual = actualSumMonth(all, today);
  const future = all.filter(d => d.date > today);
  const biz = future.filter(d => d.isBusinessDay !== false).length;
  const holi = future.length - biz;
  const add = (paceBiz ?? 0) * biz + paceHoliday * holi;
  return { landingPace: mActual + add, futureBiz: biz, futureHoli: holi };
}

function buildWeeklyConfirmed(rows: DailyPoint[], weeks: Week[], today: YYYYMMDD): WeeklyConfirmedRow[] {
  return weeks.map((w) => {
    const keys = w.days.map(ymd);
    const ds = keys.map(k => rows.find(r => r.date === k)).filter(Boolean) as DailyPoint[];
    const targetSum = sum(ds.map(r => r.target ?? 0));
    const actualSum = sum(ds.filter(r => r.date <= today).map(r => r.actual ?? 0));
    const rateConfirmed = targetSum ? actualSum / targetSum : null;

    const bizDays      = ds.filter(r => r.isBusinessDay !== false).length;
    const sunHoliDays  = ds.filter(r => {
      const dow = new Date(r.date + 'T00:00:00').getDay();
      return dow === 0 || r.isBusinessDay === false;
    }).length;
    const offDays      = ds.filter(r => r.isBusinessDay === false).length;

    return { key: w.key, label: `${w.key}（${formatRangeJP(w.start, w.end)}）`, targetSum, actualSum, rateConfirmed, bizDays, sunHoliDays, offDays };
  });
}

function buildShortAI(all: DailyPoint[], curWeek: Week | undefined, today: YYYYMMDD) {
  const todayAI = all.find(r => r.date === today)?.predicted ?? null;
  let weekAI: number | null = null;
  let weekTarget = 0;
  if (curWeek) {
    const keys = curWeek.days.map(ymd);
    const ds = keys.map(k => all.find(r => r.date === k)).filter(Boolean) as DailyPoint[];
    const past = ds.filter(r => r.date <= today);
    const future = ds.filter(r => r.date > today);
    weekAI = sum(past.map(r => r.actual ?? 0)) + sum(future.map(r => r.predicted ?? 0));
    weekTarget = sum(ds.map(r => r.target ?? 0));
  }
  return { todayAI, weekAI, weekTarget };
}

/** 営業日補正を伴う比較（MoM/YoY）。
 *  normalized = (実績/営業日数) 比で評価。戻り値は {deltaPct, baselineValue} */
function normalizedDelta(
  baseSeries: DailyPoint[],
  baselineSeries: DailyPoint[] | undefined,
  today: YYYYMMDD,
  valueCurrent: number | null
): { deltaPct: number | null, baselineValue: number | null } {
  if (!baselineSeries || valueCurrent == null) return { deltaPct: null, baselineValue: null };
  const curDays = bizDayCountTo(baseSeries, today) || 1;
  const baseDay = ymd(addDays(toDate(today), - (curDays - 1)));
  // baseline 側は「同数の営業日」を目安に同月内の先頭から該当営業日数分を集計
  const bsBiz = baselineSeries.filter(d => d.isBusinessDay !== false);
  const cutoff = bsBiz.slice(0, curDays).map(d => d.date);
  const baselineActual = sum(baselineSeries.filter(d => cutoff.includes(d.date)).map(d => d.actual ?? d.predicted ?? 0));
  const normCur = valueCurrent / curDays;
  const normBase = baselineActual / curDays;
  if (!normBase) return { deltaPct: null, baselineValue: baselineActual };
  return { deltaPct: (normCur - normBase) / normBase, baselineValue: baselineActual };
}

/* =========================
 * ビジュアル部品
 * ========================= */
const TinyLabel: FC<{ children: React.ReactNode }> = ({ children }) => (
  <span style={{ color: '#8c8c8c', fontSize: 13 }}>{children}</span>
);

const SoftBadge: FC<{ value: number | null | undefined }> = ({ value }) => {
  if (value == null) return <span style={{ color: '#8c8c8c' }}>—</span>;
  const tone = value >= 0 ? '#0958d9' : Colors.bad;
  const bg = value >= 0 ? '#f0f5ff' : '#fff1f0';
  const arrow = value >= 0 ? '▲' : '▼';
  return (
    <span style={{ display: 'inline-block', padding: '0 8px', lineHeight: '22px', borderRadius: 6, background: bg, color: tone }}>
      {arrow} {pctStr(Math.abs(value), 1)}
    </span>
  );
};

/** 共通セクションカード（dense: 余白圧縮） */
const SectionCard: FC<{
  title: string;
  tooltip?: string;
  extra?: React.ReactNode;
  children: React.ReactNode;
  dense?: boolean;
  className?: string;
  style?: React.CSSProperties;
  minBodyHeight?: number;
}> = ({ title, tooltip, extra, children, dense, className, style, minBodyHeight }) => {
  const headPad = dense ? '4px 8px' : DENSE.headPad;
  const bodyPad = dense ? 8 : DENSE.cardPad;
  return (
    <Card className={`no-overlap-card ${className ?? ''}`} style={{ marginBottom: DENSE.gutter, height: '100%', display: 'flex', flexDirection: 'column', ...style }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: headPad }}>
        <Typography.Title level={5} style={{ margin: 0 }}>{title}</Typography.Title>
        <Space size={8}>
          {extra}
          {tooltip && (
            <AntTooltip title={tooltip}>
              <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
            </AntTooltip>
          )}
        </Space>
      </div>
      <div className="section-body" style={{ padding: bodyPad, flex: 1, display: 'flex', flexDirection: 'column', minHeight: minBodyHeight ?? DENSE.cellMinH }}>
        {children}
      </div>
    </Card>
  );
};

const MiniRateBar: FC<{ rate: number | null }> = ({ rate }) => {
  if (rate == null) return <>—</>;
  const p = clamp(Math.round(rate * 100), 0, 200);
  const color = p >= 100 ? Colors.good : p >= 80 ? Colors.warn : Colors.bad;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 8, background: '#f0f0f0', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: `${Math.min(p, 100)}%`, height: '100%', background: color }} />
      </div>
      <span style={{ width: 48, textAlign: 'right' }}>{p}%</span>
    </div>
  );
};

// 小さめの数値タイル
const StatTile: FC<{ label: string; value: number | null | undefined; unit?: string; color?: string; sub?: string; }> = ({ label, value, unit = 't', color, sub }) => (
  <Card className="no-overlap-card" bordered size="small" bodyStyle={{ padding: 8 }}>
    <TinyLabel>{label}{sub ? `（${sub}）` : ''}</TinyLabel>
    <div style={{ fontSize: 20, color: color ?? 'inherit', fontFeatureSettings: "'tnum' 1", fontVariantNumeric: 'tabular-nums' }}>
      {value != null ? `${Math.round(value).toLocaleString()} ${unit}` : '—'}
    </div>
  </Card>
);

// ヘッダー用ピル
const StatPill: FC<{ label: string; value: number; unit?: string; aria?: string; }> = ({ label, value, unit = '日', aria }) => (
  <span
    aria-label={aria ?? `${label} ${value}${unit}`}
    style={{
      display: 'inline-flex', alignItems: 'baseline', gap: 6,
      padding: '2px 8px', borderRadius: 999, background: '#f5f5f5', border: '1px solid #e8e8e8'
    }}
  >
    <span style={{ color: '#8c8c8c', fontSize: 12 }}>{label}</span>
    <span style={{ fontSize: 14, fontFeatureSettings: "'tnum' 1", fontVariantNumeric: 'tabular-nums' }}>
      {value.toLocaleString()}<span style={{ fontSize: 11, marginLeft: 2 }}>{unit}</span>
    </span>
  </span>
);

// ==== 比較セル（現行/AI 共通） ====
const CompareCell: FC<{
  title: string;
  value: number | null;
  rate: number | null;
  tone: 'pace' | 'ai';
  showDelta?: boolean;
  deltaPct?: number | null;
  compact?: boolean;
}> = ({ title, value, rate, tone, showDelta, deltaPct, compact }) => {
  const color = tone === 'pace' ? Colors.pace : Colors.forecast;
  const rateP = rate == null ? '—' : pctStr(rate, 0);
  const fz = compact ? 18 : 22;
  const stroke = compact ? 4 : 6;
  return (
    <Card className="no-overlap-card" size="small" bordered bodyStyle={{ padding: compact ? 5 : 8 }}>
      <Space size={6} align="baseline" style={{ marginBottom: compact ? 1 : 4 }}>
        <Tag color={tone === 'pace' ? 'default' : 'blue'}>{title}</Tag>
      </Space>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: compact ? 1 : 4 }}>
        <div style={{ fontSize: fz, color, fontFeatureSettings: "'tnum' 1", fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap' }}>
          {value != null ? `${Math.round(value).toLocaleString()} t` : '—'}
        </div>
        <TinyLabel>達成：{rateP}</TinyLabel>
        {showDelta && <SoftBadge value={deltaPct} />}
      </div>
      {rate != null && (
        <Progress percent={clamp(Math.round(rate * 100), 0, 200)} showInfo={false} strokeWidth={stroke} style={{ marginTop: 0 }} />
      )}
    </Card>
  );
};

/** 今月着地カード（達成率バー付き） */
const MonthLandingCard: FC<{
  label: string;
  sub: string;
  tone: 'pace' | 'ai';
  value: number;
  rate: number | null;  // value / mTarget
  deltaPct?: number | null;
}> = ({ label, sub, tone, value, rate, deltaPct }) => {
  const color = tone === 'pace' ? Colors.pace : Colors.forecast;
  return (
    <Card className="no-overlap-card" size="small" bordered bodyStyle={{ padding: 6 }}>
      <Space size={6} align="baseline" style={{ marginBottom: 1 }}>
        <Tag color={tone === 'pace' ? 'default' : 'blue'}>{label}</Tag>
        <TinyLabel>{sub}</TinyLabel>
        {deltaPct != null && <SoftBadge value={deltaPct} />}
      </Space>
      <div style={{ fontSize: 18, color, fontFeatureSettings: "'tnum' 1", fontVariantNumeric: 'tabular-nums' }}>
        {`${Math.round(value).toLocaleString()} t`}
      </div>
      <div style={{ marginTop: 4 }}>
        <Progress
          percent={rate == null ? 0 : clamp(Math.round(rate * 100), 0, 200)}
          showInfo={false}
          strokeWidth={5}
        />
      </div>
    </Card>
  );
};

const WeeklyConfirmedTable: FC<{ rows: WeeklyConfirmedRow[]; currentWeekKey?: string; }> = ({ rows, currentWeekKey }) => {
  const cols: TableColumnsType<WeeklyConfirmedRow> = [
    { title: '週', dataIndex: 'label', key: 'label', width: 180,
      render: (v: string, r) => (<span>{r.key === currentWeekKey && <Tag color="blue" style={{ marginRight: 6 }}>今</Tag>}{v}</span>) },
    { title: '平日数', dataIndex: 'bizDays', key: 'bizDays', align: 'right', width: 90 },
    { title: '日・祝日数', dataIndex: 'sunHoliDays', key: 'sunHoliDays', align: 'right', width: 110 },
    { title: '休業日数', dataIndex: 'offDays', key: 'offDays', align: 'right', width: 100 },
    { title: '目標合計(t)', dataIndex: 'targetSum', key: 'targetSum', align: 'right', render: (v: number) => v.toLocaleString(), width: 120 },
    { title: '確定合計(t)', dataIndex: 'actualSum', key: 'actualSum', align: 'right', render: (v: number) => v.toLocaleString(), width: 120 },
    { title: '達成率', dataIndex: 'rateConfirmed', key: 'rateConfirmed', align: 'right', render: (v: number | null) => <MiniRateBar rate={v} />, width: 160 },
  ];
  return (
    <Table size="small" bordered pagination={false} dataSource={rows} columns={cols}
      rowClassName={(rec) => rec.key === currentWeekKey ? 'row-current-week' : ''} scroll={{ x: 920 }} style={{ width: '100%' }} />
  );
};

const HeroKPICard: FC<{ monthTarget: number; mtdActual: number; mtdRate: number | null; }>
= ({ monthTarget, mtdActual, mtdRate }) => {
  const ringPercent = clamp(Math.round((mtdRate ?? 0) * 100), 0, 120);
  const ringColor = (mtdRate ?? 0) >= 1 ? Colors.good : (mtdRate ?? 0) >= 0.8 ? Colors.warn : Colors.bad;

  return (
    <SectionCard dense title="月目標 vs MTD実績" tooltip="月目標＝当月目標合計、MTD＝本日までの確定合計。" minBodyHeight={DENSE.cellMinH}>
      <div className="kpi-grid" style={{ padding: 0 }}>
        <div className="kpi-cell">
          <span className="kpi-label">月目標</span>
          <span className="kpi-value kpi-num" style={{ color: Colors.target }}>
            {Math.round(monthTarget).toLocaleString()} <span className="unit">t</span>
          </span>
        </div>
        <div className="kpi-cell">
          <span className="kpi-label">MTD実績</span>
          <span className="kpi-value kpi-num" style={{ color: Colors.actual }}>
            {Math.round(mtdActual).toLocaleString()} <span className="unit">t</span>
          </span>
        </div>
        <div className="kpi-cell ring">
          <span className="kpi-label">達成率（確定）</span>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Progress type="dashboard" percent={ringPercent} size={96} strokeColor={ringColor} format={() => `${ringPercent}%`} />
          </div>
        </div>
      </div>
    </SectionCard>
  );
};

/* === 今日/今週 見込み（現行 vs AI） === */
const TodayWeekCompareCard: FC<{
  todayCurrent: number | null;
  todayAI: number | null;
  dayTargetPlan: number | null;
  weekCurrent: number | null;
  weekAI: number | null;
  weekTarget: number;
  dayDeltaPct?: number | null;
  weekDeltaPct?: number | null;
}> = ({ todayCurrent, todayAI, dayTargetPlan, weekCurrent, weekAI, weekTarget, dayDeltaPct, weekDeltaPct }) => {
  const dayRateAI = useMemo(() => (dayTargetPlan ? (todayAI ?? 0) / dayTargetPlan : null), [todayAI, dayTargetPlan]);
  const dayRateCurrent = useMemo(() => (dayTargetPlan ? (todayCurrent ?? 0) / dayTargetPlan : null), [todayCurrent, dayTargetPlan]);
  const weekRateAI = useMemo(() => (weekTarget ? (weekAI ?? 0) / weekTarget : null), [weekAI, weekTarget]);
  const weekRateCurrent = useMemo(() => (weekTarget ? (weekCurrent ?? 0) / weekTarget : null), [weekCurrent, weekTarget]);

  return (
    <SectionCard dense title="今日・今週の見込み（現行 vs AI）" tooltip="現行＝直近平日ペースに基づく見込み、AI＝モデル予測の積上げ。">
      <div className="matrix-two">
        <div className="m-label">今日</div>
        <div className="m-row">
          <CompareCell compact title="現行" value={todayCurrent} rate={dayRateCurrent} tone="pace" />
          <CompareCell compact title="AI" value={todayAI ?? null} rate={dayRateAI} tone="ai" showDelta deltaPct={dayDeltaPct} />
        </div>

        <div className="m-label">今週</div>
        <div className="m-row">
          <CompareCell compact title="現行" value={weekCurrent} rate={weekRateCurrent} tone="pace" />
          <CompareCell compact title="AI" value={weekAI ?? null} rate={weekRateAI} tone="ai" showDelta deltaPct={weekDeltaPct} />
        </div>
      </div>
    </SectionCard>
  );
};

/* === 実績カード（月/週/日） === */
const ActualsCard: FC<{
  monthActualMTD: number;
  weekActualToDate: number;
  dayActual: number | null;
  mtdRate: number | null;
}> = ({ monthActualMTD, weekActualToDate, dayActual, mtdRate }) => {
  const ringPercent = clamp(Math.round((mtdRate ?? 0) * 100), 0, 120);
  const ringColor = (mtdRate ?? 0) >= 1 ? Colors.good : (mtdRate ?? 0) >= 0.8 ? Colors.warn : Colors.bad;

  return (
    <SectionCard
      dense
      title="実績（確定）"
      tooltip="月＝MTD、週＝当週の本日まで、日＝本日確定。"
      extra={<TinyLabel>MTD達成率</TinyLabel>}
    >
      <div className="actuals-grid">
        <Card className="no-overlap-card" bordered size="small" bodyStyle={{ padding: 8 }}>
          <TinyLabel>月実績（MTD）</TinyLabel>
          <div style={{ fontSize: 20, color: Colors.actual, fontFeatureSettings: "'tnum' 1", fontVariantNumeric: 'tabular-nums' }}>
            {monthActualMTD.toLocaleString()} t
          </div>
          <div style={{ marginTop: 6 }}>
            <Progress type="line" percent={ringPercent} strokeColor={ringColor} showInfo />
          </div>
        </Card>
        <StatTile label="週実績" value={weekActualToDate} color={Colors.actual} sub="今日まで" />
        <StatTile label="日実績" value={dayActual ?? null} color={Colors.actual} sub="本日" />
      </div>
    </SectionCard>
  );
};

/* === 目標達成ペース：必要ペース/残り目標 === */
const ActionPaceCard: FC<{
  loading: boolean;
  remainingGoal: number; requiredPerBizDay: number | null;
  paceBiz: number | null;
}> = ({ loading, remainingGoal, requiredPerBizDay, paceBiz }) => {
  return (
    <SectionCard dense className="action-compact" title="目標達成ペース" tooltip="必要平均＝(月目標−MTD実績)/残営業日。" minBodyHeight={DENSE.cellMinH}>
      {!loading ? (
        <div className="action-grid two-cols">
          <Card className="no-overlap-card action-tile" bordered bodyStyle={{ padding: 8 }}>
            <TinyLabel>必要ペース（残平日）</TinyLabel>
            <div className="action-val">{requiredPerBizDay != null ? `${requiredPerBizDay.toFixed(1)} t/日` : '—'}</div>
            <TinyLabel style={{ marginTop: 4 }}>直近平日ペース：{paceBiz != null ? `${Math.round(paceBiz)} t/日` : '—'}</TinyLabel>
          </Card>
          <Card className="no-overlap-card action-tile" bordered bodyStyle={{ padding: 8 }}>
            <TinyLabel>残り目標数</TinyLabel><div className="action-val">{remainingGoal.toLocaleString()} t</div>
          </Card>
        </div>
      ) : <Skeleton active paragraph={{ rows: 2 }} title={false} />}
    </SectionCard>
  );
};

/* === 月着地（現行 vs AI） === */
const MonthLandingCompareCard: FC<{
  landingPace: number; landingAI: number; mTarget: number;
  subLeft: string; compareDeltaPace?: number | null; compareDeltaAI?: number | null;
}> = ({ landingPace, landingAI, mTarget, subLeft, compareDeltaPace, compareDeltaAI }) => {
  return (
    <SectionCard dense title="月着地（現行ペース vs AI）" tooltip="現行＝直近平日ペース×残営業日で積上げ、AI＝日次予測の積上げ。">
      <div className="m-row">
        <MonthLandingCard
          label="現行ペース着地"
          sub={subLeft}
          tone="pace"
          value={landingPace}
          rate={mTarget ? landingPace / mTarget : null}
          deltaPct={compareDeltaPace}
        />
        <MonthLandingCard
          label="AI着地"
          sub="日次予測積上げ"
          tone="ai"
          value={landingAI}
          rate={mTarget ? landingAI / mTarget : null}
          deltaPct={compareDeltaAI}
        />
      </div>
    </SectionCard>
  );
};

/* =========================
 * メイン
 * ========================= */
const ExecutiveForecastDashboard: FC = () => {
  const [month, setMonth] = useState<YYYYMM>(currentMonth());
  const [series, setSeries] = useState<SeriesBundle | null>(null);
  const [compareBasis, setCompareBasis] = useState<CompareBasis>('now');

  const thisMonth = useMemo(() => currentMonth(), []);
  const nextMonthAllowed = useMemo(() => nextMonthStr(thisMonth), [thisMonth]);

  const clampMonth = (m: YYYYMM): YYYYMM => { if (m < thisMonth) return thisMonth; if (m > nextMonthAllowed) return nextMonthAllowed; return m; };
  const safeSetMonth = (m: YYYYMM) => setMonth(clampMonth(m));

  useEffect(() => {
    let mounted = true;
    setSeries(null);
    (async () => {
      const d = await mockRepo.fetchSeriesBundle(month);
      if (mounted) setSeries(d);
    })();
    return () => { mounted = false; };
  }, [month]);

  const weeks = useMemo(() => buildWeeks(month), [month]);
  const todayStr = useMemo(() => yyyymmddTodayFromMonth(month), [month]);
  const todayDate = useMemo(() => toDate(todayStr), [todayStr]);
  const currentWeek = useMemo(() => weeks.find(w => w.start <= todayDate && todayDate <= w.end) ?? weeks[0], [weeks, todayDate]);

  const [activeWeekKey, setActiveWeekKey] = useState<string>('');
  useEffect(() => { setActiveWeekKey(currentWeek?.key ?? weeks[0]?.key ?? 'W1'); }, [currentWeek, weeks]);

  const monthJP = useMemo(() => formatMonthJP(month), [month]);

  const base = series?.base ?? [];
  const baselineSeries = useMemo(() => {
    if (!series) return undefined;
    if (compareBasis === 'prevMonth') return series.prevMonth;
    if (compareBasis === 'prevYear') return series.prevYear;
    return undefined;
  }, [series, compareBasis]);

  const { mActual, mTarget, landingAI, mtdRate } = useMemo(
    () => (base.length ? computeMonthRates(base, todayStr) : { mActual: 0, mTarget: 0, landingAI: 0, mtdRate: null }),
    [base, todayStr]
  );

  const paceBiz = useMemo(() => (base.length ? currentBusinessPace(base, todayStr, 7) : null), [base, todayStr]);
  const { landingPace, futureBiz, futureHoli } = useMemo(
    () => (base.length ? landingByCurrentPace(base, todayStr, paceBiz, 0) : { landingPace: 0, futureBiz: 0, futureHoli: 0 }),
    [base, todayStr, paceBiz]
  );

  const remainingBizDays = useMemo(() => (base.length ? base.filter(d => d.date > todayStr && d.isBusinessDay !== false).length : 0), [base, todayStr]);
  const remainingHoliDays = useMemo(() => (base.length ? base.filter(d => d.date > todayStr && d.isBusinessDay === false).length : 0), [base, todayStr]);
  const remainingSunAndHoli = useMemo(() => (base.length ? base.filter(d => d.date > todayStr && (new Date(d.date + 'T00:00:00').getDay() === 0 || d.isBusinessDay === false)).length : 0), [base, todayStr]);
  const remainingGoal = useMemo(() => Math.max(0, mTarget - mActual), [mTarget, mActual]);
  const requiredPerBizDay = useMemo(() => (remainingBizDays ? remainingGoal / remainingBizDays : null), [remainingGoal, remainingBizDays]);

  const { todayAI, weekAI, weekTarget } = useMemo(
    () => (base.length ? buildShortAI(base, currentWeek, todayStr) : { todayAI: null, weekAI: null, weekTarget: 0 }),
    [base, currentWeek, todayStr]
  );

  // === 目標・実績 ===
  const monthTarget = useMemo(() => (base.length ? monthTargetSum(base) : 0), [base]);
  const weekTargetPlan = useMemo(() => {
    if (!base.length || !currentWeek) return 0;
    const keys = currentWeek.days.map(ymd);
    const ds = keys.map(k => base.find(r => r.date === k)).filter(Boolean) as DailyPoint[];
    return sum(ds.map(r => r.target ?? 0));
  }, [base, currentWeek]);
  const dayTargetPlan = useMemo(() => {
    if (!base.length) return null;
    const r = base.find(d => d.date === todayStr);
    if (!r) return null;
    return r.isBusinessDay === false ? null : (r.target ?? null);
  }, [base, todayStr]);

  const monthActualMTD = useMemo(() => (base.length ? actualSumMonth(base, todayStr) : 0), [base, todayStr]);
  const weekActualToDate = useMemo(() => {
    if (!base.length || !currentWeek) return 0;
    const keys = currentWeek.days.map(ymd);
    const ds = keys.map(k => base.find(r => r.date === k)).filter(Boolean) as DailyPoint[];
    return sum(ds.filter(r => r.date <= todayStr).map(r => r.actual ?? 0));
  }, [base, currentWeek, todayStr]);
  const dayActual = useMemo(() => {
    if (!base.length) return null;
    const r = base.find(d => d.date === todayStr);
    return r?.actual ?? null;
  }, [base, todayStr]);

  const todayCurrent = useMemo(() => {
    if (!base.length) return null;
    const r = base.find(d => d.date === todayStr);
    if (!r) return null;
    const isBiz = r.isBusinessDay !== false;
    if (!isBiz) return 0;
    return paceBiz ?? null;
  }, [base, todayStr, paceBiz]);

  const weekCurrent = useMemo(() => {
    if (!base.length || !currentWeek) return null;
    const keys = currentWeek.days.map(ymd);
    const ds = keys.map(k => base.find(r => r.date === k)).filter(Boolean) as DailyPoint[];
    const past = ds.filter(r => r.date <= todayStr);
    const future = ds.filter(r => r.date > todayStr);
    const futureBizCount = future.filter(r => r.isBusinessDay !== false).length;
    const add = (paceBiz ?? 0) * futureBizCount;
    const cur = sum(past.map(r => r.actual ?? 0)) + (paceBiz == null ? 0 : add);
    return paceBiz == null ? null : cur;
  }, [base, currentWeek, todayStr, paceBiz]);

  // === 比較デルタ（営業日補正） ===
  const compareForDay = useMemo(() => normalizedDelta(base, baselineSeries, todayStr, (todayAI ?? null) ?? null), [base, baselineSeries, todayStr, todayAI]);
  const compareForWeek = useMemo(() => normalizedDelta(base, baselineSeries, todayStr, (weekAI ?? null) ?? null), [base, baselineSeries, todayStr, weekAI]);

  const compareForLandingPace = useMemo(() => {
    if (!baselineSeries) return { deltaPct: null };
    const curDays = monthBizDays(base) || 1;
    const baseBiz = baselineSeries.filter(d => d.isBusinessDay !== false).slice(0, curDays);
    const baseLanding = sum(baseBiz.map(d => d.actual ?? d.predicted ?? 0));
    if (!baseLanding) return { deltaPct: null };
    return { deltaPct: (landingPace - baseLanding) / baseLanding };
  }, [baselineSeries, base, landingPace]);

  const compareForLandingAI = useMemo(() => {
    if (!baselineSeries) return { deltaPct: null };
    const curDays = monthBizDays(base) || 1;
    const baseBiz = baselineSeries.filter(d => d.isBusinessDay !== false).slice(0, curDays);
    const baseLanding = sum(baseBiz.map(d => d.actual ?? d.predicted ?? 0));
    if (!baseLanding) return { deltaPct: null };
    return { deltaPct: (landingAI - baseLanding) / baseLanding };
  }, [baselineSeries, base, landingAI]);

  // === 週別テーブル/チャート ===
  const weeklyConfirmedRows = useMemo(() => (base.length ? buildWeeklyConfirmed(base, weeks, todayStr) : []), [base, weeks, todayStr]);

  const weekRowsForTabs = useMemo(() => {
    if (!base.length) return {} as Record<string, DailyPoint[]>;
    const map: Record<string, DailyPoint[]> = {};
    weeks.forEach(w => {
      const keys = w.days.map(ymd);
      map[w.key] = keys.map(k => base.find(d => d.date === k)).filter(Boolean) as DailyPoint[];
    });
    return map;
  }, [base, weeks]);

  const baselineWeekRowsForTabs = useMemo(() => {
    if (!baselineSeries) return {} as Record<string, DailyPoint[]>;
    const map: Record<string, DailyPoint[]> = {};
    weeks.forEach(w => {
      const keys = w.days.map(ymd);
      map[w.key] = keys.map(k => baselineSeries.find(d => d.date.endsWith(k.slice(5)))).filter(Boolean) as DailyPoint[];
    });
    return map;
  }, [baselineSeries, weeks]);

  const weekChartData = useMemo(() => {
    const rows = weekRowsForTabs[activeWeekKey] ?? [];
    const bRows = baselineWeekRowsForTabs[activeWeekKey] ?? [];
    return rows.map((r, i) => {
      const b = bRows[i];
      return {
        日付: r.date.slice(5),
        実績: r.actual ?? null,
        AI予測: r.predicted,
        目標: r.target ?? null,
        比較基準: b ? (b.actual ?? b.predicted ?? null) : null,
        isBiz: r.isBusinessDay !== false,
        yyyyMMdd: r.date
      };
    });
  }, [weekRowsForTabs, baselineWeekRowsForTabs, activeWeekKey]);

  const tabItems = useMemo(() => {
    if (!base.length) return [];
    const map: Record<string, { landing: number; target: number }> = {};
    weeks.forEach(w => {
      const keys = w.days.map(ymd);
      const ds = keys.map(k => base.find(r => r.date === k)).filter(Boolean) as DailyPoint[];
      const past = ds.filter(r => r.date <= todayStr);
      const future = ds.filter(r => r.date > todayStr);
      const landing = sum(past.map(r => r.actual ?? 0)) + sum(future.map(r => r.predicted ?? 0));
      const target = sum(ds.map(r => r.target ?? 0));
      map[w.key] = { landing, target };
    });
    return weeks.map(w => {
      const ai = map[w.key];
      const label = (
        <Space size={6}>
          <span>{w.key}</span>
          {ai && <Badge count={`${Math.round(ai.landing).toLocaleString()}t`} style={{ backgroundColor: '#1677ff' }} />}
        </Space>
      );
      return { key: w.key, label };
    });
  }, [weeks, base, todayStr]);

  const todayXLabel = useMemo(() => {
    const idx = weekChartData.findIndex(d => d.yyyyMMdd === todayStr);
    if (idx < 0) return undefined;
    const rec = weekChartData[idx] as Record<string, unknown>;
    return rec['日付'] as string | undefined;
  }, [weekChartData, todayStr]);

  const disabledMonthDate = (cur: Dayjs) => { if (!cur) return false; const ym = cur.format('YYYY-MM'); return ym < thisMonth || ym > nextMonthAllowed; };
  const canPrev = month > thisMonth;
  const canNext = month < nextMonthAllowed;

  const loading = series == null;

  return (
    <div style={{ padding: 16 }}>
      {/* ヘッダー */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 8 }}>
        <Col aria-live="polite">
          <Typography.Title level={4} style={{ margin: 0 }}>
            搬入量ダッシュボード — {monthJP}
          </Typography.Title>
          <TinyLabel>上段＝意思決定（2×2） / 下段＝根拠（週・日別）。比較：営業日補正MoM/YoY。</TinyLabel>
        </Col>
        <Col>
          <Space size={8} wrap>
            <Segmented<CompareBasis>
              value={compareBasis}
              onChange={(v) => setCompareBasis(v as CompareBasis)}
              options={[
                { label: '今月', value: 'now' },
                { label: '先月比', value: 'prevMonth' },
                { label: '前年同月比', value: 'prevYear' },
              ]}
            />
            <Button size="small" disabled={!canPrev} onClick={() => safeSetMonth(prevMonthStr(month))}>← 前月</Button>
            <Space size={4}>
              <TinyLabel>対象月</TinyLabel>
              <DatePicker
                picker="month"
                value={dayjs(month, 'YYYY-MM')}
                onChange={(_, s) => typeof s === 'string' && setMonth(clampMonth(s as YYYYMM))}
                disabledDate={disabledMonthDate}
                style={{ width: 140 }}
                aria-label="対象月を選択"
                size="small"
              />
            </Space>
            <Button size="small" disabled={!canNext} onClick={() => safeSetMonth(nextMonthStr(month))}>次月 →</Button>
          </Space>
        </Col>
      </Row>

      {/* ====== 上段：2×2 グリッド ====== */}
      <div className="top-grid-2x2">
        <div className="cell">
          <HeroKPICard monthTarget={mTarget} mtdActual={mActual} mtdRate={mtdRate} />
        </div>

        <div className="cell">
          <TodayWeekCompareCard
            todayCurrent={todayCurrent}
            todayAI={todayAI}
            dayTargetPlan={dayTargetPlan}
            weekCurrent={weekCurrent}
            weekAI={weekAI}
            weekTarget={weekTarget}
            dayDeltaPct={compareBasis === 'now' ? null : compareForDay.deltaPct}
            weekDeltaPct={compareBasis === 'now' ? null : compareForWeek.deltaPct}
          />
        </div>

        <div className="cell">
          <ActionPaceCard
            loading={loading}
            remainingGoal={remainingGoal}
            requiredPerBizDay={requiredPerBizDay}
            paceBiz={paceBiz}
          />
        </div>

        <div className="cell">
          <MonthLandingCompareCard
            landingPace={landingPace}
            landingAI={landingAI}
            mTarget={mTarget}
            subLeft={`残：営業${futureBiz} / 休業${futureHoli}`}
            compareDeltaPace={compareBasis === 'now' ? null : compareForLandingPace.deltaPct}
            compareDeltaAI={compareBasis === 'now' ? null : compareForLandingAI.deltaPct}
          />
        </div>
      </div>

      {/* ===== 残日ピル ===== */}
      <Row style={{ marginBottom: 8 }}>
        <Col span={24}>
          <SectionCard
            dense
            title="カレンダー残日サマリー"
            tooltip="当月の本日以降の残日内訳（自動算出）。"
            extra={
              <div className="card-header-stats">
                <StatPill label="残平日数" value={remainingBizDays} />
                <StatPill label="残日・祝日数" value={remainingSunAndHoli} />
                <StatPill label="残休業日数" value={remainingHoliDays} />
              </div>
            }
          >
            <TinyLabel>※ ヘッダー右のピルに内訳を表示しています。</TinyLabel>
          </SectionCard>
        </Col>
      </Row>

      {/* ===== 週別＋日別 ===== */}
      <Row gutter={[12, 12]}>
        <Col xs={24}>
          <SectionCard title="週別の状況（確定のみ）" tooltip="週ごとの目標合計・確定合計・達成率と、日種別カウントを表示。未来の見込みは表示しません。">
            {base.length ? <WeeklyConfirmedTable rows={weeklyConfirmedRows} currentWeekKey={currentWeek?.key} />
                         : <Skeleton active paragraph={{ rows: 3 }} title={false} />}
          </SectionCard>
        </Col>

        <Col xs={24}>
          <SectionCard
            title="実績 vs 見込み（日別）"
            tooltip="凡例：実績=緑 / AI予測=青 / 目標=橙（折れ線） / 比較（先月/前年）=灰（点線）。縦帯=本日。"
            extra={<Tag color="geekblue">{monthJP}</Tag>}
          >
            <Tabs activeKey={activeWeekKey} onChange={setActiveWeekKey} items={tabItems} size="small" style={{ marginBottom: 8 }} />
            <Card className="no-overlap-card" bordered bodyStyle={{ padding: DENSE.cardPad }}>
              <div style={{ height: DENSE.chartH }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={weekChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="日付" />
                    <YAxis unit="t" />
                    <Tooltip formatter={(v: number, name) => [v + 't', name]} />
                    <Legend />
                    {todayXLabel !== undefined && (
                      <ReferenceArea x1={todayXLabel} x2={todayXLabel} strokeOpacity={0} fill="#e6f4ff" fillOpacity={0.6} />
                    )}
                    <Line type="monotone" dataKey="目標" stroke={Colors.target} dot={false} strokeWidth={2} />
                    {compareBasis !== 'now' && (
                      <Line type="monotone" dataKey="比較基準" stroke={Colors.baseline} dot={false} strokeDasharray="4 4" />
                    )}
                    <Bar dataKey="AI予測" fill={Colors.forecast} />
                    <Bar dataKey="実績" fill={Colors.actual} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </SectionCard>
        </Col>
      </Row>

      {/* スタイル */}
      <style>
        {`
          /* ===== 上段：2×2 固定グリッド ===== */
          .top-grid-2x2 {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            grid-auto-rows: 1fr;
            gap: ${DENSE.gutter}px;
            align-items: stretch;
          }
          .top-grid-2x2 .cell { min-width: 0; }
          @media (max-width: 991px) {
            .top-grid-2x2 { grid-template-columns: 1fr; }
          }

          /* 共通 */
          .no-overlap-card { position: relative; z-index: 1; overflow: visible; }
          .row-current-week td { background: #f0f5ff !important; }
          .section-body { min-height: ${DENSE.cellMinH}px; }

          /* KPIカード：コンパクト */
          .kpi-grid {
            display: grid;
            gap: ${DENSE.gutter}px;
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }
          .kpi-cell {
            min-height: 108px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 10px;
            border: 1px solid #f0f0f0;
            border-radius: 8px;
            background: #fff;
          }
          .kpi-cell.ring { align-items: center; }
          .kpi-label { color: #8c8c8c; font-size: 13px; }
          .kpi-value.kpi-num {
            font-size: ${DENSE.kpiLg}px;
            font-feature-settings: 'tnum' 1;
            font-variant-numeric: tabular-nums;
            line-height: 1.15;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .kpi-value .unit { font-size: 13px; }

          /* 2列行マトリクス */
          .matrix-two {
            display: grid;
            grid-template-columns: 84px 1fr;
            column-gap: 8px;
            row-gap: 6px;
          }
          .m-label { color: #8c8c8c; font-size: 12px; line-height: 28px; align-self: center; white-space: nowrap; }
          .m-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
          }
          @media (max-width: 575px) {
            .matrix-two { grid-template-columns: 1fr; }
            .m-row { grid-template-columns: 1fr; }
          }

          /* 実績カードの内部グリッド */
          .actuals-grid {
            display: grid;
            gap: ${DENSE.gutter}px;
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }
          @media (max-width: 575px) { .actuals-grid { grid-template-columns: 1fr; } }

          /* 目標達成ペース：2タイル */
          .action-grid.two-cols {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: ${DENSE.gutter}px;
          }
          @media (max-width: 575px) { .action-grid.two-cols { grid-template-columns: 1fr; } }
          .action-compact .action-grid { gap: ${Math.round(DENSE.gutter * 0.75)}px; }
          .action-compact .action-tile .action-val {
            font-size: 18px;
            font-feature-settings: 'tnum' 1;
            font-variant-numeric: tabular-nums;
          }

          /* ヘッダー内ピル */
          .card-header-stats {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            justify-content: flex-end;
          }
          @media (max-width: 575px) {
            .card-header-stats { justify-content: flex-start; }
          }
        `}
      </style>
    </div>
  );
};

export default ExecutiveForecastDashboard;
