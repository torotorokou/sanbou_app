import React, { useEffect, useMemo, useState } from 'react';
import dayjs, { Dayjs } from 'dayjs';
import type { FC, ReactNode } from 'react';
import {
  Card, Row, Col, Typography, DatePicker, Space, Button, Progress, Tag,
  Tooltip as AntTooltip, Skeleton, Tabs, Table, Divider, Segmented, Badge
} from 'antd';
import type { TableColumnsType } from 'antd';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend, Line, ReferenceArea
} from 'recharts';
import { InfoCircleOutlined } from '@ant-design/icons';

/* =========================================================
 * 搬入量ダッシュボード（1ページ完結 / 未来フォーカス）
 * - ヒーロー：1枚カードに統合（目標 / MTD / 達成率リング / 平日ペース）
 * - 中段：月見通し（AI/現行の比較、短期AI：今日・今週）
 * - 行動帯：目標達成ペース（必要平均と現行差）
 * - 下段：週別の状況（確定のみ）＋ 日別グラフ（PCは横並び、SPは縦積み）
 * ========================================================= */

/* =========================
 * 色・トークン
 * ========================= */
const Colors = {
  actual: '#52c41a',   // 実績
  forecast: '#1677ff', // AI予測
  pace:    '#6c757d',  // 現行ペース
  target:  '#faad14',  // 目標
  bad:     '#cf1322',  // 警告
  warn:    '#fa8c16',  // 注意
  good:    '#389e0d',  // 達成
} as const;

const DENSE = {
  gutter: 12,
  cardPad: 10,
  headPad: '6px 10px',
  kpiMd: 26,
  kpiLg: 30,
  chartH: 240,
} as const;

/* =========================
 * 型
 * ========================= */
type YYYYMM = string;
type YYYYMMDD = string;

type DailyPoint = {
  date: YYYYMMDD;
  predicted: number;       // AI予測（日次）
  actual?: number;         // 実績（日次）
  target?: number;         // 目標（日次）
  isBusinessDay?: boolean; // true=営業 / false=休業
};

type Week = {
  key: string;     // "W1"
  index: number;   // 0-based
  start: Date;     // 月曜
  end: Date;       // 土曜
  days: Date[];    // [Mon..Sat]
  label: string;   // "1週目（9/2–9/7）"
};

type WeeklyConfirmedRow = {
  key: string;
  label: string;       // "W1（MM/DD–MM/DD）"
  targetSum: number;   // 週目標合計
  actualSum: number;   // 週実績（<= today）
  rateConfirmed: number | null; // 実績/目標
};

type AdoptedKind = 'AI' | '現行';

/* =========================
 * Repository（Mock）
 * ========================= */
interface ForecastRepository {
  fetchDailySeries: (month: YYYYMM) => Promise<DailyPoint[]>;
}

const mockRepo: ForecastRepository = {
  async fetchDailySeries(month) {
    const days = Array.from({ length: 31 }, (_, i) => i + 1);
    return days.map((d) => {
      const date = `${month}-${String(d).padStart(2, '0')}`;
      const base = 100 + Math.sin((d / 31) * Math.PI * 2) * 20;
      const predicted = Math.max(40, Math.round(base + (Math.random() * 10 - 5)));
      const actual = d < 20 ? Math.max(35, Math.round(predicted * (0.9 + Math.random() * 0.2))) : undefined; // デモ：20日が“今日”
      const target = 110; // デモ固定：日別目標
      const dow = new Date(date + 'T00:00:00').getDay(); // 0=Sun..6=Sat
      const isBusinessDay = dow !== 0; // デモ: 日曜休み
      return { date, predicted, actual, target, isBusinessDay };
    });
  },
};

/* =========================
 * Util（純関数）
 * ========================= */
const sum = (arr: number[]) => arr.reduce((a, b) => a + b, 0);
const avg = (arr: number[]) => (arr.length ? sum(arr) / arr.length : 0);
const toDate = (d: string) => new Date(d + 'T00:00:00');

const pctStr = (v: number | null | undefined, digits = 0) =>
  v == null ? '—' : `${(v * 100).toFixed(digits)}%`;

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

function ymd(d: Date): YYYYMMDD {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}
function formatMonthJP(month: YYYYMM) {
  const [y, m] = month.split('-').map(Number);
  return `${y}年${m}月`;
}
function formatRangeJP(a: Date, b: Date) {
  return `${a.getMonth() + 1}/${a.getDate()}–${b.getMonth() + 1}/${b.getDate()}`;
}
function currentMonth(): YYYYMM {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}
function nextMonthStr(month: YYYYMM): YYYYMM {
  const [y, m] = month.split('-').map(Number);
  const d = new Date(y, m - 1, 1);
  d.setMonth(d.getMonth() + 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}
function prevMonthStr(month: YYYYMM): YYYYMM {
  const [y, m] = month.split('-').map(Number);
  const d = new Date(y, m - 1, 1);
  d.setMonth(d.getMonth() - 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}
function yyyymmddTodayFromMonth(month: YYYYMM): YYYYMMDD {
  const now = new Date();
  const currentYM = currentMonth();
  if (month === currentYM) {
    return `${month}-${String(now.getDate()).padStart(2, '0')}`;
  }
  return `${month}-20`; // デモ仕様
}
function getIsoMonday(d: Date) {
  const day = d.getDay(); // 0=Sun..6=Sat
  const diff = (day === 0 ? -6 : 1 - day);
  const monday = new Date(d);
  monday.setDate(d.getDate() + diff);
  monday.setHours(0, 0, 0, 0);
  return monday;
}
function addDays(date: Date, n: number) {
  const dd = new Date(date);
  dd.setDate(date.getDate() + n);
  return dd;
}
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
 * UseCase（計算）
 * ========================= */
const monthTargetSum = (all: DailyPoint[]) => sum(all.map(r => r.target ?? 0));
const actualSumMonth = (all: DailyPoint[], today: YYYYMMDD) =>
  sum(all.filter(r => r.date <= today).map(r => r.actual ?? 0));
const actualSum = (rows: DailyPoint[]) => sum(rows.map(r => r.actual ?? 0));
const predictedSum = (rows: DailyPoint[]) => sum(rows.map(r => r.predicted ?? 0));

/** MTD達成率（確定）とAI月着地/達成見込み */
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

/** 現行ペース（直近営業n日平均） */
function currentBusinessPace(all: DailyPoint[], today: YYYYMMDD, n = 7) {
  const rows = all.filter(d => d.date < today && d.isBusinessDay !== false);
  const recent = rows.slice(-n);
  const vals = recent.map(d => d.actual ?? 0).filter(v => v != null);
  if (!vals.length) return null;
  return avg(vals);
}

/** 現行ペース着地（機械的） */
function landingByCurrentPace(all: DailyPoint[], today: YYYYMMDD, paceBiz: number | null, paceHoliday = 0) {
  const mActual = actualSumMonth(all, today);
  const future = all.filter(d => d.date > today);
  const biz = future.filter(d => d.isBusinessDay !== false).length;
  const holi = future.length - biz;
  const add = (paceBiz ?? 0) * biz + paceHoliday * holi;
  return { landingPace: mActual + add, futureBiz: biz, futureHoli: holi };
}

/** 週：確定のみ（目標・実績・率） */
function buildWeeklyConfirmed(rows: DailyPoint[], weeks: Week[], today: YYYYMMDD): WeeklyConfirmedRow[] {
  return weeks.map((w) => {
    const keys = w.days.map(ymd);
    const ds = keys.map(k => rows.find(r => r.date === k)).filter(Boolean) as DailyPoint[];
    const targetSum = sum(ds.map(r => r.target ?? 0));
    const actualSum = sum(ds.filter(r => r.date <= today).map(r => r.actual ?? 0));
    const rateConfirmed = targetSum ? actualSum / targetSum : null;
    return {
      key: w.key,
      label: `${w.key}（${formatRangeJP(w.start, w.end)}）`,
      targetSum, actualSum, rateConfirmed,
    };
  });
}

/** 今日AI・今週AI（着地） */
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

const SectionCard: FC<{ title: string; tooltip?: string; extra?: React.ReactNode; children: React.ReactNode }> = ({ title, tooltip, extra, children }) => (
  <Card style={{ marginBottom: DENSE.gutter }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: DENSE.headPad }}>
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
    <div style={{ padding: DENSE.cardPad }}>{children}</div>
  </Card>
);

/** ミニ達成バー（セル内） */
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
}> = ({ title, value, rate, tone, showDelta, deltaPct }) => {
  const color = tone === 'pace' ? Colors.pace : Colors.forecast;
  const rateP = rate == null ? '—' : pctStr(rate, 0);
  return (
    <Card size="small" bordered bodyStyle={{ padding: 8 }}>
      <Space size={6} align="baseline" style={{ marginBottom: 4 }}>
        <Tag color={tone === 'pace' ? 'default' : 'blue'}>{title}</Tag>
      </Space>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <div style={{ fontSize: 24, color, fontFeatureSettings: "'tnum' 1", fontVariantNumeric: 'tabular-nums' }}>
          {value != null ? `${Math.round(value).toLocaleString()} t` : '—'}
        </div>
        <TinyLabel>達成：{rateP}</TinyLabel>
        {showDelta && <SoftBadge value={deltaPct} />}
      </div>
      {rate != null && (
        <Progress
          percent={clamp(Math.round(rate * 100), 0, 200)}
          showInfo={false}
          strokeWidth={6}
          style={{ marginTop: 2 }}
        />
      )}
    </Card>
  );
};

/* 週別状況テーブル（確定のみ） */
const WeeklyConfirmedTable: FC<{
  rows: WeeklyConfirmedRow[];
  currentWeekKey?: string;
}> = ({ rows, currentWeekKey }) => {
  const cols: TableColumnsType<WeeklyConfirmedRow> = [
    { title: '週', dataIndex: 'label', key: 'label', width: 180,
      render: (v: string, r) => (
        <span>
          {r.key === currentWeekKey && <Tag color="blue" style={{ marginRight: 6 }}>今</Tag>}
          {v}
        </span>
      )
    },
    {
      title: '目標合計(t)',
      dataIndex: 'targetSum',
      key: 'targetSum',
      align: 'right',
      render: (v: number) => v.toLocaleString(),
      width: 140,
    },
    {
      title: '確定合計(t)',
      dataIndex: 'actualSum',
      key: 'actualSum',
      align: 'right',
      render: (v: number) => v.toLocaleString(),
      width: 140,
    },
    {
      title: '達成率',
      dataIndex: 'rateConfirmed',
      key: 'rateConfirmed',
      align: 'right',
      render: (v: number | null) => <MiniRateBar rate={v} />,
      width: 180,
    },
  ];
  return (
    <Table
      size="small"
      bordered
      pagination={false}
      dataSource={rows}
      columns={cols}
      rowClassName={(rec) => rec.key === currentWeekKey ? 'row-current-week' : ''}
      scroll={{ x: 680 }}
      style={{ width: '100%' }}
    />
  );
};

/** ヒーローKPIを1枚に統合 */
const HeroKPICard: FC<{
  monthTarget: number;
  mtdActual: number;
  mtdRate: number | null;
  paceBiz: number | null;
}> = ({ monthTarget, mtdActual, mtdRate, paceBiz }) => {
  const ringPercent = clamp(Math.round((mtdRate ?? 0) * 100), 0, 120);
  const ringColor = (mtdRate ?? 0) >= 1 ? Colors.good : (mtdRate ?? 0) >= 0.8 ? Colors.warn : Colors.bad;

  return (
    <Card style={{ marginBottom: DENSE.gutter }}>
      <div style={{ padding: DENSE.headPad, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography.Title level={5} style={{ margin: 0 }}>月目標〜平均ペース</Typography.Title>
        <TinyLabel>確定のみ・数字はタブラー体</TinyLabel>
      </div>

      <div className="kpi-grid" style={{ padding: DENSE.cardPad }}>
        {/* 月目標 */}
        <div className="kpi-cell">
          <span className="kpi-label">月目標</span>
          <span className="kpi-value" style={{ color: Colors.target }}>
            {Math.round(monthTarget).toLocaleString()} <span style={{ fontSize: 14 }}>t</span>
          </span>
        </div>

        {/* MTD実績 */}
        <div className="kpi-cell">
          <span className="kpi-label">MTD実績</span>
          <span className="kpi-value" style={{ color: Colors.actual }}>
            {Math.round(mtdActual).toLocaleString()} <span style={{ fontSize: 14 }}>t</span>
          </span>
        </div>

        {/* 達成率リング */}
        <div className="kpi-cell">
          <span className="kpi-label">達成率（確定）</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Progress type="dashboard" percent={ringPercent} size={72} strokeColor={ringColor} format={() => `${ringPercent}%`} />
            <TinyLabel>0 / 100 / 120%</TinyLabel>
          </div>
        </div>

        {/* 平日ペース */}
        <div className="kpi-cell">
          <span className="kpi-label">平日ペース（直近）</span>
          <span className="kpi-value" style={{ color: Colors.pace }}>
            {paceBiz != null ? `${Math.round(paceBiz)} t/日` : '—'}
          </span>
        </div>
      </div>
    </Card>
  );
};

/* =========================
 * メイン
 * ========================= */
const ExecutiveForecastDashboard: FC = () => {
  /* ===== 月（当月〜来月のみ） ===== */
  const [month, setMonth] = useState<YYYYMM>(currentMonth());
  const [daily, setDaily] = useState<DailyPoint[] | null>(null);

  const thisMonth = useMemo(() => currentMonth(), []);
  const nextMonthAllowed = useMemo(() => nextMonthStr(thisMonth), [thisMonth]);

  const clampMonth = (m: YYYYMM): YYYYMM => {
    if (m < thisMonth) return thisMonth;
    if (m > nextMonthAllowed) return nextMonthAllowed;
    return m;
  };
  const safeSetMonth = (m: YYYYMM) => setMonth(clampMonth(m));

  /* ===== データ取得 ===== */
  useEffect(() => {
    let mounted = true;
    setDaily(null);
    (async () => {
      const d = await mockRepo.fetchDailySeries(month);
      if (mounted) setDaily(d);
    })();
    return () => { mounted = false; };
  }, [month]);

  /* ===== 週関連 ===== */
  const weeks = useMemo(() => buildWeeks(month), [month]);
  const todayStr = useMemo(() => yyyymmddTodayFromMonth(month), [month]);
  const todayDate = useMemo(() => toDate(todayStr), [todayStr]);
  const currentWeek = useMemo(
    () => weeks.find(w => w.start <= todayDate && todayDate <= w.end) ?? weeks[0],
    [weeks, todayDate]
  );

  const [activeWeekKey, setActiveWeekKey] = useState<string>(''); // グラフ用
  useEffect(() => {
    setActiveWeekKey(currentWeek?.key ?? weeks[0]?.key ?? 'W1');
  }, [currentWeek, weeks]);

  /* ===== KPI・見通し計算 ===== */
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

  const monthDiffAI = useMemo(() => (mTarget ? (landingAI - mTarget) / mTarget : null), [landingAI, mTarget]);
  const monthDiffPace = useMemo(() => (mTarget ? (landingPace - mTarget) / mTarget : null), [landingPace, mTarget]);

  const remainingBizDays = useMemo(() => (daily ? daily.filter(d => d.date > todayStr && d.isBusinessDay !== false).length : 0), [daily, todayStr]);
  const remainingHoliDays = useMemo(() => (daily ? daily.filter(d => d.date > todayStr && d.isBusinessDay === false).length : 0), [daily, todayStr]);
  // 日曜＋祝日の合計（個別内訳は非表示）
  const remainingSunAndHoli = useMemo(() => (
    daily ? daily.filter(d => d.date > todayStr && (new Date(d.date + 'T00:00:00').getDay() === 0 || d.isBusinessDay === false)).length : 0
  ), [daily, todayStr]);
  const remainingGoal = useMemo(() => Math.max(0, mTarget - mActual), [mTarget, mActual]);
  const requiredPerBizDay = useMemo(() => (remainingBizDays ? remainingGoal / remainingBizDays : null), [remainingGoal, remainingBizDays]);
  

  // 短期AI（今日・今週）
  const { todayAI, weekAI, weekTarget } = useMemo(
    () => (daily ? buildShortAI(daily, currentWeek, todayStr) : { todayAI: null, weekAI: null, weekTarget: 0 }),
    [daily, currentWeek, todayStr]
  );

  // ==== 今日/今週：現行ペース側の見込みと比較用KPI ====
  // 今日ターゲット
  const dayTarget = useMemo(() => {
    if (!daily) return 0;
    const r = daily.find(d => d.date === todayStr);
    return r?.target ?? 0;
  }, [daily, todayStr]);

  // 今日（現行）＝ 営業日なら paceBiz、休業日なら 0
  const todayCurrent = useMemo(() => {
    if (!daily) return null;
    const r = daily.find(d => d.date === todayStr);
    if (!r) return null;
    const isBiz = r.isBusinessDay !== false;
    if (!isBiz) return 0;
    return paceBiz ?? null;
  }, [daily, todayStr, paceBiz]);

  // 今週（現行）＝ 週の確定合計 + paceBiz×残営業
  const weekCurrent = useMemo(() => {
    if (!daily || !currentWeek) return null;
    const keys = currentWeek.days.map(ymd);
    const ds = keys.map(k => daily.find(r => r.date === k)).filter(Boolean) as DailyPoint[];
    const past = ds.filter(r => r.date <= todayStr);
    const future = ds.filter(r => r.date > todayStr);
    const futureBiz = future.filter(r => r.isBusinessDay !== false).length;
    const add = (paceBiz ?? 0) * futureBiz; // 休業日は0
    const cur = sum(past.map(r => r.actual ?? 0)) + (paceBiz == null ? 0 : add);
    return paceBiz == null ? null : cur;
  }, [daily, currentWeek, todayStr, paceBiz]);

  // 達成率・Δ
  const dayRateAI = useMemo(() => (dayTarget ? (todayAI ?? 0) / dayTarget : null), [todayAI, dayTarget]);
  const dayRateCurrent = useMemo(() => (dayTarget ? (todayCurrent ?? 0) / dayTarget : null), [todayCurrent, dayTarget]);
  const dayDeltaPct = useMemo(() => (dayTarget ? ((todayAI ?? 0) - (todayCurrent ?? 0)) / dayTarget : null), [todayAI, todayCurrent, dayTarget]);

  const weekRateAI = useMemo(() => (weekTarget ? (weekAI ?? 0) / weekTarget : null), [weekAI, weekTarget]);
  const weekRateCurrent = useMemo(() => (weekTarget ? (weekCurrent ?? 0) / weekTarget : null), [weekCurrent, weekTarget]);
  const weekDeltaPct = useMemo(() => (weekTarget ? ((weekAI ?? 0) - (weekCurrent ?? 0)) / weekTarget : null), [weekAI, weekCurrent, weekTarget]);

  // 週タブ用：各週のAI着地（バッジ表示に使う）
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

  // 採用値（現行 or AI）
  const [adopted, setAdopted] = useState<AdoptedKind>('AI');

  /* ===== 週別状況（確定のみ） ===== */
  const weeklyConfirmedRows = useMemo(
    () => (daily ? buildWeeklyConfirmed(daily, weeks, todayStr) : []),
    [daily, weeks, todayStr]
  );

  /* ===== グラフデータ ===== */
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
    return rows.map(r => ({
      日付: r.date.slice(5),
      実績: r.actual ?? null,
      AI予測: r.predicted,
      目標: r.target ?? null,
      isBiz: r.isBusinessDay !== false,
      yyyyMMdd: r.date,
    }));
  }, [weekRowsForTabs, activeWeekKey]);

  // 本日の x 軸ラベル（例: "09-20"）
  const todayXLabel = useMemo(() => {
    const idx = weekChartData.findIndex(d => d.yyyyMMdd === todayStr);
    if (idx < 0) return undefined;
    const rec = weekChartData[idx] as Record<string, unknown>;
    return rec['日付'] as string | undefined;
  }, [weekChartData, todayStr]);

  /* ===== 月ナビ制御 ===== */
  const disabledMonthDate = (cur: Dayjs) => {
    if (!cur) return false;
    const ym = cur.format('YYYY-MM');
    return ym < thisMonth || ym > nextMonthAllowed;
  };
  const canPrev = month > thisMonth;
  const canNext = month < nextMonthAllowed;

  /* ===== タブアイテム（週AIバッジ付き） ===== */
  const tabItems = useMemo(() => {
    return weeks.map(w => {
      const ai = weeklyAIMap[w.key];
      const label = (
        <Space size={6}>
          <span>{w.key}</span>
          {ai && (
            <Badge count={`${Math.round(ai.landing).toLocaleString()}t`} style={{ backgroundColor: '#1677ff' }} />
          )}
        </Space>
      );
      return { key: w.key, label };
    });
  }, [weeks, weeklyAIMap]);

  return (
    <div style={{ padding: 16 }}>
      {/* ヘッダー */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 8 }}>
        <Col aria-live="polite">
          <Typography.Title level={4} style={{ margin: 0 }}>
            搬入量ダッシュボード — {monthJP}
          </Typography.Title>
          <TinyLabel>上：確定 / 中：見通し（現行 vs AI） / 下：根拠（週表・日別グラフ）</TinyLabel>
        </Col>
        <Col>
          <Space size={8}>
            <Button size="small" disabled={!canPrev} onClick={() => safeSetMonth(prevMonthStr(month))}>← 前月</Button>
            <Space size={4}>
              <TinyLabel>対象月</TinyLabel>
              <DatePicker
                picker="month"
                value={dayjs(month, 'YYYY-MM')}
                onChange={(_, s) => typeof s === 'string' && safeSetMonth(s as YYYYMM)}
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

      {/* ===== ヒーロー帯（統合カード） ===== */}
      <HeroKPICard
        monthTarget={mTarget}
        mtdActual={mActual}
        mtdRate={mtdRate}
        paceBiz={paceBiz}
      />

      {/* ===== 目標達成ペース（行動指標） ===== */}
      <SectionCard
        title="目標達成ペース"
        tooltip="必要平均＝(月目標−MTD実績)/残営業日。"
      >
        {daily ? (
          <Row gutter={[DENSE.gutter, DENSE.gutter]} style={{ flexWrap: 'nowrap', overflowX: 'auto' }}>
            <Col flex="1" style={{ minWidth: 160 }}><Card bordered bodyStyle={{ padding: 10 }}><TinyLabel>残平日数</TinyLabel><div style={{ fontSize: 20 }}>{remainingBizDays} 日</div></Card></Col>
            <Col flex="1" style={{ minWidth: 200 }}><Card bordered bodyStyle={{ padding: 10 }}><TinyLabel>残日・祝日数</TinyLabel><div style={{ fontSize: 20 }}>{remainingSunAndHoli} 日</div></Card></Col>
            <Col flex="1" style={{ minWidth: 160 }}><Card bordered bodyStyle={{ padding: 10 }}><TinyLabel>残休業日数</TinyLabel><div style={{ fontSize: 20 }}>{remainingHoliDays} 日</div></Card></Col>
            <Col flex="1" style={{ minWidth: 200 }}><Card bordered bodyStyle={{ padding: 10 }}><TinyLabel>残り目標数</TinyLabel><div style={{ fontSize: 20 }}>{remainingGoal.toLocaleString()} t</div></Card></Col>
            <Col flex="1" style={{ minWidth: 200 }}><Card bordered bodyStyle={{ padding: 10 }}><TinyLabel>必要ペース（残平日数）</TinyLabel><div style={{ fontSize: 20 }}>{requiredPerBizDay != null ? `${requiredPerBizDay.toFixed(1)} t/日` : '—'}</div></Card></Col>
          </Row>
        ) : <Skeleton active paragraph={{ rows: 2 }} title={false} />}
      </SectionCard>

      {/* ===== 月見通し（短期AI：今日・今週 をサブヘッダー帯で集約） ===== */}
      <SectionCard
        title="月見通し"
        tooltip="左=現行ペース着地（機械的） / 右=AI着地（日次予測の積上げ）。上部に短期AI：今日/今週。"
        extra={(
          <Space size={8}>
            <TinyLabel>採用値</TinyLabel>
            <Segmented<AdoptedKind>
              size="small"
              value={adopted}
              onChange={(v) => setAdopted(v as AdoptedKind)}
              options={[
                { label: 'AI', value: 'AI' },
                { label: '現行', value: '現行' },
              ]}
            />
          </Space>
        )}
      >
        {/* === 短期比較：2×2（上=今日 / 下=今週 × 左=現行 / 右=AI） === */}
        <Row gutter={[8, 8]} style={{ marginBottom: 8 }}>
          {/* 今日（現行） */}
          <Col xs={24} md={12}>
            <CompareCell
              title="今日（現行）"
              value={todayCurrent}
              rate={dayRateCurrent}
              tone="pace"
              showDelta={false}
            />
          </Col>
          {/* 今日（AI） */}
          <Col xs={24} md={12}>
            <CompareCell
              title="今日（AI）"
              value={todayAI ?? null}
              rate={dayRateAI}
              tone="ai"
              showDelta
              deltaPct={dayDeltaPct}
            />
          </Col>

          {/* 今週（現行） */}
          <Col xs={24} md={12}>
            <CompareCell
              title="今週（現行）"
              value={weekCurrent}
              rate={weekRateCurrent}
              tone="pace"
              showDelta={false}
            />
          </Col>
          {/* 今週（AI） */}
          <Col xs={24} md={12}>
            <CompareCell
              title="今週（AI）"
              value={weekAI ?? null}
              rate={weekRateAI}
              tone="ai"
              showDelta
              deltaPct={weekDeltaPct}
            />
          </Col>
        </Row>

        {/* 本体：現行ペース vs AI（同一フォーマット） */}
        <Row gutter={[8, 8]}>
          <Col xs={24} md={12}>
            <Card size="small" bordered bodyStyle={{ padding: 10 }}>
              <Space size={6} align="baseline" style={{ marginBottom: 4 }}>
                <Tag color="default">現行ペース</Tag>
                <TinyLabel>残：営業{futureBiz} / 休業{futureHoli}</TinyLabel>
              </Space>
              <Card bordered={false} bodyStyle={{ padding: 8 }}>
                <div style={{ fontSize: 22, color: Colors.pace, fontFeatureSettings: "'tnum' 1", fontVariantNumeric: 'tabular-nums' }}>
                  着地（機械的）：{Math.round(landingPace).toLocaleString()} t
                </div>
              </Card>
              <Row gutter={[8, 8]} style={{ marginTop: 6 }}>
                <Col span={12}><Card bordered={false} bodyStyle={{ padding: 8 }}><TinyLabel>達成見込み</TinyLabel><div>{mTarget ? pctStr(landingPace / mTarget, 0) : '—'}</div></Card></Col>
                <Col span={12}><Card bordered={false} bodyStyle={{ padding: 8 }}><TinyLabel>月乖離</TinyLabel><div><SoftBadge value={monthDiffPace} /></div></Card></Col>
              </Row>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card size="small" bordered bodyStyle={{ padding: 10 }}>
              <Space size={6} align="baseline" style={{ marginBottom: 4 }}>
                <Tag color="blue">AI予測</Tag>
                <TinyLabel>日次予測積上げ</TinyLabel>
              </Space>
              <Card bordered={false} bodyStyle={{ padding: 8 }}>
                <div style={{ fontSize: 22, color: Colors.forecast, fontFeatureSettings: "'tnum' 1", fontVariantNumeric: 'tabular-nums' }}>
                  着地（AI）：{Math.round(landingAI).toLocaleString()} t
                </div>
              </Card>
              <Row gutter={[8, 8]} style={{ marginTop: 6 }}>
                <Col span={12}><Card bordered={false} bodyStyle={{ padding: 8 }}><TinyLabel>達成見込み</TinyLabel><div>{mTarget ? pctStr(landingAI / mTarget, 0) : '—'}</div></Card></Col>
                <Col span={12}><Card bordered={false} bodyStyle={{ padding: 8 }}><TinyLabel>月乖離</TinyLabel><div><SoftBadge value={monthDiffAI} /></div></Card></Col>
              </Row>
            </Card>
          </Col>
        </Row>

        {/* 代替：差分の明示（KPI+Δ） */}
        <Divider style={{ margin: '8px 0' }} />
      </SectionCard>

      

      {/* ===== 週別＋日別（PCは横並び / SPは縦積み） ===== */}
      <Row gutter={[12, 12]}>
        <Col xs={24} lg={24}>
          <SectionCard
            title="週別の状況（確定のみ）"
            tooltip="週ごとの目標合計・確定合計・達成率。未来の見込みはここでは表示しません。"
          >
            {daily
              ? <WeeklyConfirmedTable rows={weeklyConfirmedRows} currentWeekKey={currentWeek?.key} />
              : <Skeleton active paragraph={{ rows: 3 }} title={false} />}
          </SectionCard>
  </Col>

  <Col xs={24} lg={24}>
          <SectionCard
            title="実績 vs 見込み（日別）"
            tooltip="凡例：実績=緑 / AI予測=青 / 目標=橙（折れ線）。縦帯=本日。タブ右のバッジは週AI着地。"
            extra={<Tag color="geekblue">{monthJP}</Tag>}
          >
            <Tabs
              activeKey={activeWeekKey}
              onChange={setActiveWeekKey}
              items={tabItems}
              size="small"
              style={{ marginBottom: 8 }}
            />
            <Card bordered bodyStyle={{ padding: DENSE.cardPad }}>
              <div style={{ height: DENSE.chartH }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={weekChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="日付" />
                    <YAxis unit="t" />
                    <Tooltip formatter={(v: number, name) => [v + 't', name]} />
                    <Legend />
                    {todayXLabel !== undefined && (
                      <ReferenceArea
                        x1={todayXLabel}
                        x2={todayXLabel}
                        strokeOpacity={0}
                        fill="#e6f4ff"
                        fillOpacity={0.6}
                      />
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

      {/* スタイル（現在週ハイライト & KPIグリッド） */}
      <style>
        {`
          .row-current-week td { background: #f0f5ff !important; }

          .kpi-grid {
            display: grid;
            gap: ${DENSE.gutter}px;
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
          @media (min-width: 768px) {
            .kpi-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
          }
          .kpi-cell {
            height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 10px;
            border: 1px solid #f0f0f0;
            border-radius: 8px;
            background: #fff;
          }
          .kpi-label { color: #8c8c8c; font-size: 13px; }
          .kpi-value {
            font-size: ${DENSE.kpiLg}px;
            font-feature-settings: 'tnum' 1;
            font-variant-numeric: tabular-nums;
            line-height: 1.2;
          }
        `}
      </style>
    </div>
  );
};

export default ExecutiveForecastDashboard;
