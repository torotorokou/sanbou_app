import React, { useEffect, useMemo, useState } from 'react';
import dayjs, { Dayjs } from 'dayjs';
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
 * 搬入量ダッシュボード（上段=2カラム：左2枚 / 右1枚）
 * - 右の「月見通し」は左列に「今日 / 今週 / 今月」の行ラベルを設置
 * - 月の着地（現行/AI）に細い達成率バーを追加
 * - 週別テーブルに「平日数 / 日・祝日数 / 休業日数」を追加
 * - コンパクト化＆余白対策を維持
 * ========================================================= */

const Colors = {
  actual: '#52c41a',
  forecast: '#1677ff',
  pace:    '#6c757d',
  target:  '#faad14',
  bad:     '#cf1322',
  warn:    '#fa8c16',
  good:    '#389e0d',
} as const;

const DENSE = {
  gutter: 12,
  cardPad: 10,
  headPad: '6px 10px',
  kpiMd: 22,
  kpiLg: 26,
  chartH: 240,
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

/* =========================
 * Repository（Mock）
 * ========================= */
interface ForecastRepository { fetchDailySeries: (month: YYYYMM) => Promise<DailyPoint[]>; }
const mockRepo: ForecastRepository = {
  async fetchDailySeries(month) {
    const days = Array.from({ length: 31 }, (_, i) => i + 1);
    return days.map((d) => {
      const date = `${month}-${String(d).padStart(2, '0')}`;
      const base = 100 + Math.sin((d / 31) * Math.PI * 2) * 20;
      const predicted = Math.max(40, Math.round(base + (Math.random() * 10 - 5)));
      const actual = d < 20 ? Math.max(35, Math.round(predicted * (0.9 + Math.random() * 0.2))) : undefined; // デモ：20日が“今日”
      const target = 110;
      const dow = new Date(date + 'T00:00:00').getDay();
      const isBusinessDay = dow !== 0; // 日曜休み
      return { date, predicted, actual, target, isBusinessDay };
    });
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

    // 週内の各日種別カウント
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
}> = ({ title, tooltip, extra, children, dense, className, style }) => {
  const headPad = dense ? '4px 8px' : DENSE.headPad;
  const bodyPad = dense ? 8 : DENSE.cardPad;
  return (
    <Card
      className={`no-overlap-card ${className ?? ''}`}
      style={{ marginBottom: DENSE.gutter, height: '100%', display: 'flex', flexDirection: 'column', ...style }}
    >
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
      <div className="section-body" style={{ padding: bodyPad, flex: 1, display: 'flex', flexDirection: 'column' }}>
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
}> = ({ label, sub, tone, value, rate }) => {
  const color = tone === 'pace' ? Colors.pace : Colors.forecast;
  return (
    <Card className="no-overlap-card" size="small" bordered bodyStyle={{ padding: 6 }}>
      <Space size={6} align="baseline" style={{ marginBottom: 1 }}>
        <Tag color={tone === 'pace' ? 'default' : 'blue'}>{label}</Tag>
        <TinyLabel>{sub}</TinyLabel>
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

const HeroKPICard: FC<{ monthTarget: number; mtdActual: number; mtdRate: number | null; paceBiz: number | null; }>
= ({ monthTarget, mtdActual, mtdRate, paceBiz }) => {
  const ringPercent = clamp(Math.round((mtdRate ?? 0) * 100), 0, 120);
  const ringColor = (mtdRate ?? 0) >= 1 ? Colors.good : (mtdRate ?? 0) >= 0.8 ? Colors.warn : Colors.bad;

  return (
    <Card className="no-overlap-card" style={{ marginBottom: DENSE.gutter }}>
      <div style={{ padding: DENSE.headPad, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography.Title level={5} style={{ margin: 0 }}>月目標〜平均ペース</Typography.Title>
        <TinyLabel>確定のみ・数字はタブラー体</TinyLabel>
      </div>

      <div className="kpi-grid" style={{ padding: DENSE.cardPad }}>
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
        <div className="kpi-cell">
          <span className="kpi-label">達成率（確定）</span>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Progress type="dashboard" percent={ringPercent} size={96} strokeColor={ringColor} format={() => `${ringPercent}%`} />
          </div>
        </div>
        <div className="kpi-cell">
          <span className="kpi-label">平日ペース（直近）</span>
          <span className="kpi-value kpi-num small" style={{ color: Colors.pace }}>
            {paceBiz != null ? `${Math.round(paceBiz)} t/日` : '—'}
          </span>
        </div>
      </div>
    </Card>
  );
};

/* 目標達成ペース：0.9xのコンパクト */
const ActionPaceCard: FC<{
  loading: boolean;
  remainingBizDays: number; remainingSunAndHoli: number; remainingHoliDays: number;
  remainingGoal: number; requiredPerBizDay: number | null;
}> = ({ loading, remainingBizDays, remainingSunAndHoli, remainingHoliDays, remainingGoal, requiredPerBizDay }) => {
  return (
    <SectionCard dense className="action-compact" title="目標達成ペース" tooltip="必要平均＝(月目標−MTD実績)/残営業日。">
      {!loading ? (
        <div className="action-grid">
          <Card className="no-overlap-card action-tile" bordered bodyStyle={{ padding: 8 }}>
            <TinyLabel>必要ペース（残平日数）</TinyLabel>
            <div className="action-val">{requiredPerBizDay != null ? `${requiredPerBizDay.toFixed(1)} t/日` : '—'}</div>
          </Card>
          <Card className="no-overlap-card action-tile" bordered bodyStyle={{ padding: 8 }}>
            <TinyLabel>残り目標数</TinyLabel><div className="action-val">{remainingGoal.toLocaleString()} t</div>
          </Card>
          <Card className="no-overlap-card action-tile" bordered bodyStyle={{ padding: 8 }}>
            <TinyLabel>残平日数</TinyLabel><div className="action-val">{remainingBizDays} 日</div>
          </Card>
          <Card className="no-overlap-card action-tile" bordered bodyStyle={{ padding: 8 }}>
            <TinyLabel>残日・祝日数</TinyLabel><div className="action-val">{remainingSunAndHoli} 日</div>
          </Card>
          <Card className="no-overlap-card action-tile" bordered bodyStyle={{ padding: 8 }}>
            <TinyLabel>残休業日数</TinyLabel><div className="action-val">{remainingHoliDays} 日</div>
          </Card>
        </div>
      ) : <Skeleton active paragraph={{ rows: 2 }} title={false} />}
    </SectionCard>
  );
};

/* =========================
 * メイン
 * ========================= */
const ExecutiveForecastDashboard: FC = () => {
  const [month, setMonth] = useState<YYYYMM>(currentMonth());
  const [daily, setDaily] = useState<DailyPoint[] | null>(null);

  const thisMonth = useMemo(() => currentMonth(), []);
  const nextMonthAllowed = useMemo(() => nextMonthStr(thisMonth), [thisMonth]);

  const clampMonth = (m: YYYYMM): YYYYMM => { if (m < thisMonth) return thisMonth; if (m > nextMonthAllowed) return nextMonthAllowed; return m; };
  const safeSetMonth = (m: YYYYMM) => setMonth(clampMonth(m));

  useEffect(() => {
    let mounted = true;
    setDaily(null);
    (async () => { const d = await mockRepo.fetchDailySeries(month); if (mounted) setDaily(d); })();
    return () => { mounted = false; };
  }, [month]);

  const weeks = useMemo(() => buildWeeks(month), [month]);
  const todayStr = useMemo(() => yyyymmddTodayFromMonth(month), [month]);
  const todayDate = useMemo(() => toDate(todayStr), [todayStr]);
  const currentWeek = useMemo(() => weeks.find(w => w.start <= todayDate && todayDate <= w.end) ?? weeks[0], [weeks, todayDate]);

  const [activeWeekKey, setActiveWeekKey] = useState<string>('');
  useEffect(() => { setActiveWeekKey(currentWeek?.key ?? weeks[0]?.key ?? 'W1'); }, [currentWeek, weeks]);

  const monthJP = useMemo(() => formatMonthJP(month), [month]);
  const { mActual, mTarget, landingAI, mtdRate } = useMemo(
    () => (daily ? computeMonthRates(daily, todayStr) : { mActual: 0, mTarget: 0, landingAI: 0, mtdRate: null }),
    [daily, todayStr]
  );

  const paceBiz = useMemo(() => (daily ? currentBusinessPace(daily, todayStr, 7) : null), [daily, todayStr]);
  const { landingPace, futureBiz, futureHoli } = useMemo(
    () => (daily ? landingByCurrentPace(daily, todayStr, paceBiz, 0) : { landingPace: 0, futureBiz: 0, futureHoli: 0 }),
    [daily, todayStr, paceBiz]
  );

  const remainingBizDays = useMemo(() => (daily ? daily.filter(d => d.date > todayStr && d.isBusinessDay !== false).length : 0), [daily, todayStr]);
  const remainingHoliDays = useMemo(() => (daily ? daily.filter(d => d.date > todayStr && d.isBusinessDay === false).length : 0), [daily, todayStr]);
  const remainingSunAndHoli = useMemo(() => (daily ? daily.filter(d => d.date > todayStr && (new Date(d.date + 'T00:00:00').getDay() === 0 || d.isBusinessDay === false)).length : 0), [daily, todayStr]);
  const remainingGoal = useMemo(() => Math.max(0, mTarget - mActual), [mTarget, mActual]);
  const requiredPerBizDay = useMemo(() => (remainingBizDays ? remainingGoal / remainingBizDays : null), [remainingGoal, remainingBizDays]);

  const { todayAI, weekAI, weekTarget } = useMemo(
    () => (daily ? buildShortAI(daily, currentWeek, todayStr) : { todayAI: null, weekAI: null, weekTarget: 0 }),
    [daily, currentWeek, todayStr]
  );

  const dayTarget = useMemo(() => { if (!daily) return 0; const r = daily.find(d => d.date === todayStr); return r?.target ?? 0; }, [daily, todayStr]);
  const todayCurrent = useMemo(() => {
    if (!daily) return null;
    const r = daily.find(d => d.date === todayStr);
    if (!r) return null;
    const isBiz = r.isBusinessDay !== false;
    if (!isBiz) return 0;
    return paceBiz ?? null;
  }, [daily, todayStr, paceBiz]);

  const weekCurrent = useMemo(() => {
    if (!daily || !currentWeek) return null;
    const keys = currentWeek.days.map(ymd);
    const ds = keys.map(k => daily.find(r => r.date === k)).filter(Boolean) as DailyPoint[];
    const past = ds.filter(r => r.date <= todayStr);
    const future = ds.filter(r => r.date > todayStr);
    const futureBizCount = future.filter(r => r.isBusinessDay !== false).length;
    const add = (paceBiz ?? 0) * futureBizCount;
    const cur = sum(past.map(r => r.actual ?? 0)) + (paceBiz == null ? 0 : add);
    return paceBiz == null ? null : cur;
  }, [daily, currentWeek, todayStr, paceBiz]);

  const dayRateAI = useMemo(() => (dayTarget ? (todayAI ?? 0) / dayTarget : null), [todayAI, dayTarget]);
  const dayRateCurrent = useMemo(() => (dayTarget ? (todayCurrent ?? 0) / dayTarget : null), [todayCurrent, dayTarget]);
  const dayDeltaPct = useMemo(() => (dayTarget ? ((todayAI ?? 0) - (todayCurrent ?? 0)) / dayTarget : null), [todayAI, todayCurrent, dayTarget]);

  const weekRateAI = useMemo(() => (weekTarget ? (weekAI ?? 0) / weekTarget : null), [weekAI, weekTarget]);
  const weekRateCurrent = useMemo(() => (weekTarget ? (weekCurrent ?? 0) / weekTarget : null), [weekCurrent, weekTarget]);
  const weekDeltaPct = useMemo(() => (weekTarget ? ((weekAI ?? 0) - (weekCurrent ?? 0)) / weekTarget : null), [weekAI, weekCurrent, weekTarget]);

  const weeklyAIMap = useMemo(() => {
    if (!daily) return {} as Record<string, { landing: number; target: number }>;
    const map: Record<string, { landing: number; target: number }> = {};
    weeks.forEach(w => {
      const keys = w.days.map(ymd);
      const ds = keys.map(k => daily.find(r => r.date === k)).filter(Boolean) as DailyPoint[];
      const past = ds.filter(r => r.date <= todayStr);
      const future = ds.filter(r => r.date > todayStr);
      const landing = sum(past.map(r => r.actual ?? 0)) + sum(future.map(r => r.predicted ?? 0));
      const target = sum(ds.map(r => r.target ?? 0));
      map[w.key] = { landing, target };
    });
    return map;
  }, [daily, weeks, todayStr]);

  const [adopted, setAdopted] = useState<AdoptedKind>('AI');

  const weeklyConfirmedRows = useMemo(() => (daily ? buildWeeklyConfirmed(daily, weeks, todayStr) : []), [daily, weeks, todayStr]);

  const weekRowsForTabs = useMemo(() => {
    if (!daily) return {} as Record<string, DailyPoint[]>;
    const map: Record<string, DailyPoint[]> = {};
    weeks.forEach(w => {
      const keys = w.days.map(ymd);
      map[w.key] = keys.map(k => daily.find(d => d.date === k)).filter(Boolean) as DailyPoint[];
    });
    return map;
  }, [daily, weeks]);

  const weekChartData = useMemo(() => {
    const rows = weekRowsForTabs[activeWeekKey] ?? [];
    return rows.map(r => ({ 日付: r.date.slice(5), 実績: r.actual ?? null, AI予測: r.predicted, 目標: r.target ?? null, isBiz: r.isBusinessDay !== false, yyyyMMdd: r.date }));
  }, [weekRowsForTabs, activeWeekKey]);

  const todayXLabel = useMemo(() => {
    const idx = weekChartData.findIndex(d => d.yyyyMMdd === todayStr);
    if (idx < 0) return undefined;
    const rec = weekChartData[idx] as Record<string, unknown>;
    return rec['日付'] as string | undefined;
  }, [weekChartData, todayStr]);

  const disabledMonthDate = (cur: Dayjs) => { if (!cur) return false; const ym = cur.format('YYYY-MM'); return ym < thisMonth || ym > nextMonthAllowed; };
  const canPrev = month > thisMonth;
  const canNext = month < nextMonthAllowed;

  const tabItems = useMemo(() => weeks.map(w => {
    const ai = weeklyAIMap[w.key];
    const label = (
      <Space size={6}>
        <span>{w.key}</span>
        {ai && <Badge count={`${Math.round(ai.landing).toLocaleString()}t`} style={{ backgroundColor: '#1677ff' }} />}
      </Space>
    );
    return { key: w.key, label };
  }), [weeks, weeklyAIMap]);

  const loading = daily == null;

  return (
    <div style={{ padding: 16 }}>
      {/* ヘッダー */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 8 }}>
        <Col aria-live="polite">
          <Typography.Title level={4} style={{ margin: 0 }}>
            搬入量ダッシュボード — {monthJP}
          </Typography.Title>
          <TinyLabel>左＝確定/行動指標　右＝見通し（現行 vs AI）　下＝根拠（週表・日別）</TinyLabel>
        </Col>
        <Col>
          <Space size={8}>
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

      {/* ====== 上段：CSS Grid（左2枚 / 右1枚） ====== */}
      <div className="top-grid">
        <div className="left-stack">
          <HeroKPICard monthTarget={mTarget} mtdActual={mActual} mtdRate={mtdRate} paceBiz={paceBiz} />
          <ActionPaceCard
            loading={loading}
            remainingBizDays={remainingBizDays}
            remainingSunAndHoli={remainingSunAndHoli}
            remainingHoliDays={remainingHoliDays}
            remainingGoal={remainingGoal}
            requiredPerBizDay={requiredPerBizDay}
          />
        </div>

        {/* 右列：月見通し（左列ラベル付きの行マトリクス） */}
        <SectionCard
          dense
          className="forecast-card forecast-compact"
          style={{ height: 'auto' }}  // ← 見通しカードだけ高さを自動に
          title="月見通し"
          tooltip="左列に 今日/今週/今月。右列で「現行 vs AI」を比較。今月には達成率バー。"
          extra={(
            <Space size={8}>
              <TinyLabel>採用値</TinyLabel>
              <Segmented<AdoptedKind>
                size="small"
                value={adopted}
                onChange={(v) => setAdopted(v as AdoptedKind)}
                options={[{ label: 'AI', value: 'AI' }, { label: '現行', value: '現行' }]}
              />
            </Space>
          )}
        >
          <div className="forecast-matrix">
            {/* 今日 */}
            <div className="fm-label">今日</div>
            <div className="fm-content">
              <div className="fm-row">
                <CompareCell compact title="現行" value={todayCurrent} rate={dayRateCurrent} tone="pace" />
                <CompareCell compact title="AI" value={todayAI ?? null} rate={dayRateAI} tone="ai" showDelta deltaPct={dayDeltaPct} />
              </div>
            </div>

            {/* 今週 */}
            <div className="fm-label">今週</div>
            <div className="fm-content">
              <div className="fm-row">
                <CompareCell compact title="現行" value={weekCurrent} rate={weekRateCurrent} tone="pace" />
                <CompareCell compact title="AI" value={weekAI ?? null} rate={weekRateAI} tone="ai" showDelta deltaPct={weekDeltaPct} />
              </div>
            </div>

            {/* 今月 */}
            <div className="fm-label">今月</div>
            <div className="fm-content">
              <div className="fm-row">
                <MonthLandingCard
                  label="現行ペース着地"
                  sub={`残：営業${futureBiz} / 休業${futureHoli}`}
                  tone="pace"
                  value={landingPace}
                  rate={mTarget ? landingPace / mTarget : null}
                />
                <MonthLandingCard
                  label="AI着地"
                  sub="日次予測積上げ"
                  tone="ai"
                  value={landingAI}
                  rate={mTarget ? landingAI / mTarget : null}
                />
              </div>
            </div>
          </div>
        </SectionCard>
      </div>

      {/* ===== 週別＋日別 ===== */}
      <Row gutter={[12, 12]}>
        <Col xs={24}>
          <SectionCard title="週別の状況（確定のみ）" tooltip="週ごとの目標合計・確定合計・達成率と、日種別カウントを表示。未来の見込みは表示しません。">
            {daily ? <WeeklyConfirmedTable rows={weeklyConfirmedRows} currentWeekKey={currentWeek?.key} />
                   : <Skeleton active paragraph={{ rows: 3 }} title={false} />}
          </SectionCard>
        </Col>

        <Col xs={24}>
          <SectionCard
            title="実績 vs 見込み（日別）"
            tooltip="凡例：実績=緑 / AI予測=青 / 目標=橙（折れ線）。縦帯=本日。タブ右のバッジは週AI着地。"
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
          /* ===== 上段：左右の高さを揃える ===== */
          .top-grid {
            display: grid;
            grid-template-columns: 0.42fr 0.58fr;
            gap: ${DENSE.gutter}px;
            align-items: stretch;
          }
          @media (max-width: 991px) {
            .top-grid { grid-template-columns: 1fr; }
          }
          .left-stack {
            display: flex;
            flex-direction: column;
            gap: ${DENSE.gutter}px;
            min-width: 0;
          }
          .forecast-card {
            min-width: 0;
            align-self: start; /* ← 右カードだけ行高のストレッチを無効化して内容高さに合わせる */
          }

          /* 重なり防止 */
          .no-overlap-card { position: relative; z-index: 1; overflow: visible; }
          .row-current-week td { background: #f0f5ff !important; }

          /* KPIカード：はみ出し防止 */
          .kpi-grid {
            display: grid;
            gap: ${DENSE.gutter}px;
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
          @media (min-width: 768px) {
            .kpi-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
          }
          .kpi-cell {
            height: 108px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 10px;
            border: 1px solid #f0f0f0;
            border-radius: 8px;
            background: #fff;
          }
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
          .kpi-value.kpi-num.small { font-size: ${DENSE.kpiMd}px; }
          .kpi-value .unit { font-size: 13px; }

          /* 目標達成ペース：2行グリッド（PCは3列×2行） + コンパクト */
          .action-grid {
            display: grid;
            grid-template-columns: repeat(1, minmax(0, 1fr));
            gap: ${DENSE.gutter}px;
          }
          @media (min-width: 576px) { .action-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
          @media (min-width: 992px) { .action-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } } /* 5枚→上3/下2 */

          .action-compact .action-grid { gap: ${Math.round(DENSE.gutter * 0.75)}px; }
          .action-compact .action-tile .action-val {
            font-size: 18px;   /* 20px -> 18px */
            font-feature-settings: 'tnum' 1;
            font-variant-numeric: tabular-nums;
          }
          .action-compact .ant-typography { line-height: 1.2; }
          .action-compact .ant-card-head { min-height: 0; }

          /* 見通しカード：行ラベル付きマトリクス（bodyはblockでOK） */
          .forecast-card .ant-card-body { display: block; }
          /* 見通しカードでは SectionCard の body 伸張を無効化（flex:1 を 0 に） */
          .forecast-card .section-body {
            flex: 0 0 auto;
          }
          /* 念のためカード自体の高さも自動に */
          .forecast-card { height: auto !important; }
          .forecast-matrix {
            display: grid;
            grid-template-columns: 84px 1fr;
            column-gap: 8px;
            row-gap: 6px;
            /* 余白伸張をやめ、内容高さのみ */
            flex: 0 0 auto;
            min-height: auto;
          }
          .fm-label {
            color: #8c8c8c;
            font-size: 12px;
            line-height: 28px;
            align-self: center;
            white-space: nowrap;
          }
          .fm-content { min-width: 0; }
          .fm-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
          }
          @media (max-width: 575px) {
            .forecast-matrix { grid-template-columns: 1fr; }
            .fm-row { grid-template-columns: 1fr; }
          }

          /* 見通しカードをさらに 0.9 倍程度に圧縮 */
          .forecast-compact .ant-tag { transform: scale(0.95); transform-origin: left center; }
          .forecast-compact .ant-badge { transform: scale(0.95); transform-origin: left center; }
          .forecast-compact .ant-card-small > .ant-card-body { padding: 6px; }
          .forecast-compact .ant-progress-line { margin-bottom: 4px; }
        `}
      </style>
    </div>
  );
};

export default ExecutiveForecastDashboard;
