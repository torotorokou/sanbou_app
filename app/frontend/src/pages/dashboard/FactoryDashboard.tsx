import React, { useEffect, useMemo, useState } from 'react';
import dayjs, { Dayjs } from 'dayjs';
import type { FC } from 'react';
import {
  Card, Row, Col, Typography, DatePicker, Space, Button, Progress, Tag,
  Tooltip as AntTooltip, Skeleton, Tabs,
} from 'antd';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, ReferenceLine, Legend,
} from 'recharts';

/* =========================================================
 * 運用ダッシュボード（1ページ完結／未来フォーカス）
 * - ページ＝月。KPIは月基準固定。グラフのみ週タブで切替。
 * - 月ナビ：当月〜来月のみ（過去へは遡らない）。
 * - 左列：実績（確定）ドメイン ／ 右列：予測（見込み）ドメイン
 * - この1ファイルに domain/util/usecase/view を内包
 * ========================================================= */

/* =========================
 * 色（固定）
 * ========================= */
const Colors = {
  actual: '#52c41a',   // 実績
  forecast: '#1677ff', // 予測
  target:   '#faad14', // 目標
  capacity: '#cf1322', // 能力（未使用だが将来用に保持）
} as const;

/* =========================
 * 密度トークン（コンパクト表示）
 * ========================= */
const DENSE = {
  gutter: 12,
  cardPad: 10,
  headPad: '6px 10px',
  kpiLg: 32,
  kpiMd: 26,
  chartH: 220,
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
  capacity?: number;
  isBusinessDay?: boolean;
};

type Week = {
  key: string;            // "W1" など
  index: number;          // 0-based
  start: Date;            // 月曜
  end: Date;              // 土曜
  days: Date[];           // [Mon..Sat]
  label: string;          // "1週目（9/1–9/6）"
};

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
      const target = 110;
      const capacity = 130;
      const dow = new Date(date + 'T00:00:00').getDay(); // 0=Sun..6=Sat
      const isBusinessDay = dow !== 0; // デモ: 日曜休み
      return { date, predicted, actual, target, capacity, isBusinessDay };
    });
  },
};

/* =========================
 * Util（純関数）
 * ========================= */
const sum = (arr: number[]) => arr.reduce((a, b) => a + b, 0);
const avg = (arr: number[]) => (arr.length ? sum(arr) / arr.length : 0);
const toDate = (d: string) => new Date(d + 'T00:00:00');

function formatPct(v: number | null | undefined, digits = 0) {
  if (v == null) return '—';
  return `${(v * 100).toFixed(digits)}%`;
}
function ymd(d: Date): YYYYMMDD {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}
function formatDateJP(d: YYYYMMDD) {
  const dt = toDate(d);
  const youbi = ['日','月','火','水','木','金','土'][dt.getDay()];
  return `${dt.getFullYear()}年${dt.getMonth()+1}月${dt.getDate()}日(${youbi})`;
}
function formatMonthJP(month: YYYYMM) {
  const [y, m] = month.split('-').map(Number);
  return `${y}年${m}月`;
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
      const label = `${i}週目（${days[0].getMonth() + 1}/${days[0].getDate()}–${days[5].getMonth() + 1}/${days[5].getDate()}）`;
      weeks.push({ key: `W${i}`, index: i - 1, start, end, days, label });
      i++;
    }
    start = addDays(start, 7);
  }
  return weeks;
}

/* =========================
 * UseCase（計算ロジック）
 * ========================= */
function computeLandingForWeek(rows: DailyPoint[], today: YYYYMMDD) {
  const past = rows.filter(r => r.date < today);
  const future = rows.filter(r => r.date >= today);
  return sum(past.map(r => r.actual ?? 0)) + sum(future.map(r => r.predicted ?? 0));
}
function computeLandingForMonth(all: DailyPoint[], today: YYYYMMDD) {
  const past = all.filter(r => r.date < today);
  const future = all.filter(r => r.date >= today);
  return sum(past.map(r => r.actual ?? 0)) + sum(future.map(r => r.predicted ?? 0));
}
function computeWeekRates(rows: DailyPoint[], today: YYYYMMDD) {
  const past = rows.filter(r => r.date < today);
  const future = rows.filter(r => r.date >= today);
  const wtdNum = sum(past.map(r => r.actual ?? 0));
  const wtdDen = sum(past.map(r => r.target ?? 0));
  const weekRateConfirmed = wtdDen ? wtdNum / wtdDen : null;

  const weekNumProj = wtdNum + sum(future.map(r => r.predicted ?? 0));
  const weekDen = sum(rows.map(r => r.target ?? 0));
  const weekRateProjected = weekDen ? weekNumProj / weekDen : null;

  return { weekRateConfirmed, weekRateProjected };
}
function computeMonthRates(all: DailyPoint[], today: YYYYMMDD) {
  const past = all.filter(r => r.date < today);
  const future = all.filter(r => r.date >= today);
  const mtdNum = sum(past.map(r => r.actual ?? 0));
  const mtdDen = sum(past.map(r => r.target ?? 0));
  const mtdRate = mtdDen ? mtdNum / mtdDen : null;

  const monthNumProj = mtdNum + sum(future.map(r => r.predicted ?? 0));
  const monthDen = sum(all.map(r => r.target ?? 0));
  const monthRateProj = monthDen ? monthNumProj / monthDen : null;

  return { mtdRate, monthRateProj };
}
function computeRunRateMonth(all: DailyPoint[], today: YYYYMMDD) {
  const inPast = all.filter(d => d.date < today);
  const inFuture = all.filter(d => d.date >= today);

  const goal = sum(all.map(d => d.target ?? 0));
  const actualCum = sum(inPast.map(d => d.actual ?? 0));
  const remainingGoal = Math.max(0, goal - actualCum);

  const remainingBizDays = inFuture.filter(d => d.isBusinessDay !== false).length;
  const requiredPerDay = remainingBizDays ? remainingGoal / remainingBizDays : null;

  const recent = inPast.filter(d => d.isBusinessDay !== false).slice(-7);
  const currentPace = recent.length
    ? avg(recent.map(d => d.actual ?? 0))
    : (inFuture.length ? avg(inFuture.map(d => d.predicted ?? 0)) : null);

  const upliftPct = (requiredPerDay != null && currentPace && currentPace > 0)
    ? (requiredPerDay / currentPace) - 1
    : null;

  return { requiredPerDay, currentPace, upliftPct, remainingBizDays, remainingGoal };
}

/* 実績KPI用：累計（<= 今日で集計） */
function actualSumWeek(rows: DailyPoint[], today: YYYYMMDD) {
  return sum(rows.filter(r => r.date <= today).map(r => r.actual ?? 0));
}
function actualSumMonth(all: DailyPoint[], today: YYYYMMDD) {
  return sum(all.filter(r => r.date <= today).map(r => r.actual ?? 0));
}

/* =========================
 * 小さな表示部品
 * ========================= */
const TinyLabel: FC<{ children: React.ReactNode }> = ({ children }) => (
  <span style={{ color: '#8c8c8c', fontSize: 13 }}>{children}</span>
);

const SoftBadge: FC<{ value: number | null | undefined }> = ({ value }) => {
  if (value == null) return <span style={{ color: '#8c8c8c' }}>—</span>;
  const tone = value >= 0 ? '#0958d9' : '#cf1322';
  const bg = value >= 0 ? '#f0f5ff' : '#fff1f0';
  const arrow = value >= 0 ? '▲' : '▼';
  return (
    <span style={{ display: 'inline-block', padding: '0 8px', lineHeight: '22px', borderRadius: 6, background: bg, color: tone }}>
      {arrow} {formatPct(Math.abs(value), 1)}
    </span>
  );
};

/* セクションカード（小型ヘッダ＋ボディ余白縮小） */
const SectionCard: FC<{ title: string; tooltip?: string; extra?: React.ReactNode; children: React.ReactNode }> = ({ title, tooltip, extra, children }) => (
  <Card style={{ marginBottom: DENSE.gutter }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: DENSE.headPad }}>
      <Typography.Title level={5} style={{ margin: 0 }}>{title}</Typography.Title>
      <Space size={8}>
        {extra}
        {tooltip && (
          <AntTooltip title={tooltip}>
            <span style={{ color: '#8c8c8c' }}>?</span>
          </AntTooltip>
        )}
      </Space>
    </div>
    <div style={{ padding: DENSE.cardPad }}>{children}</div>
  </Card>
);

/* ミニKPI（ラベル左／値右） */
const KPI: FC<{ label: string; value: React.ReactNode; hint?: string }> = ({ label, value, hint }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
    <TinyLabel>
      {label}
      {hint ? <AntTooltip title={hint}><span style={{ marginLeft: 4, color: '#8c8c8c' }}>?</span></AntTooltip> : null}
    </TinyLabel>
    <div style={{ fontSize: DENSE.kpiMd, fontFeatureSettings: "'tnum' 1", fontVariantNumeric: 'tabular-nums' }}>{value}</div>
  </div>
);

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

  /* ===== 週（現在週を既定。タブはグラフだけ切替） ===== */
  const weeks = useMemo(() => buildWeeks(month), [month]);
  const todayStr = useMemo(() => yyyymmddTodayFromMonth(month), [month]);
  const todayDate = useMemo(() => toDate(todayStr), [todayStr]);
  const currentWeek = useMemo(
    () => weeks.find(w => w.start <= todayDate && todayDate <= w.end) ?? weeks[0],
    [weeks, todayDate]
  );
  const [activeWeekKey, setActiveWeekKey] = useState<string>('');
  useEffect(() => {
    setActiveWeekKey(currentWeek?.key ?? weeks[0]?.key ?? 'W1');
  }, [currentWeek, weeks]);

  /* ===== 行抽出 ===== */
  const todayRow = useMemo(() => daily?.find(r => r.date === todayStr), [daily, todayStr]);
  const weekRows_current = useMemo(() => {
    if (!daily || !currentWeek) return [] as DailyPoint[];
    const keys = currentWeek.days.map(ymd);
    return keys.map(k => daily.find(d => d.date === k)).filter(Boolean) as DailyPoint[];
  }, [daily, currentWeek]);

  /* ===== KPI計算 ===== */
  const monthTargetTotal = useMemo(() => daily ? sum(daily.map(d => d.target ?? 0)) : 0, [daily]);

  // 予測量（今日・週着地・月着地）
  const todayForecast = useMemo(() => todayRow?.predicted ?? null, [todayRow]);
  const weekLanding_current = useMemo(() => computeLandingForWeek(weekRows_current, todayStr), [weekRows_current, todayStr]);
  const monthLanding = useMemo(() => (daily ? computeLandingForMonth(daily, todayStr) : 0), [daily, todayStr]);

  // 実績KPI（今日/週累計/月累計）
  const todayActual = useMemo(() => todayRow?.actual ?? null, [todayRow]);
  const weekActualCum = useMemo(() => actualSumWeek(weekRows_current, todayStr), [weekRows_current, todayStr]);
  const monthActualCum = useMemo(() => (daily ? actualSumMonth(daily, todayStr) : 0), [daily, todayStr]);

  // 達成率（確定・見込み）
  const weekRates_current = useMemo(() => computeWeekRates(weekRows_current, todayStr), [weekRows_current, todayStr]);
  const monthRates = useMemo(() => (daily ? computeMonthRates(daily, todayStr) : { mtdRate: null, monthRateProj: null }), [daily, todayStr]);

  // 必要ペース（今月）
  const runRate = useMemo(
    () => (daily ? computeRunRateMonth(daily, todayStr) : {
      requiredPerDay: null, currentPace: null, upliftPct: null, remainingBizDays: 0, remainingGoal: 0,
    }),
    [daily, todayStr]
  );

  /* ===== グラフ（週タブ：グラフのみ切替） ===== */
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
      予測: r.predicted,
      実績: r.actual ?? null,
      目標: r.target ?? null,
    }));
  }, [weekRowsForTabs, activeWeekKey]);

  /* ===== 月ナビ制御 ===== */
  const canPrev = month > thisMonth;
  const canNext = month < nextMonthAllowed;
  const disabledMonthDate = (cur: Dayjs) => {
    if (!cur) return false;
    const ym = cur.format('YYYY-MM');
    return ym < thisMonth || ym > nextMonthAllowed;
  };

  /* ===== 乖離（予測-目標）/目標 の% ===== */
  const todayTarget = todayRow?.target ?? null;
  const weekTarget_current = useMemo(() => sum(weekRows_current.map(r => r.target ?? 0)), [weekRows_current]);
  const monthTarget = monthTargetTotal;

  const diffPctToday = useMemo(() => {
    if (todayTarget == null || todayTarget === 0 || todayForecast == null) return null;
    return (todayForecast - todayTarget) / todayTarget;
  }, [todayTarget, todayForecast]);

  const diffPctWeek = useMemo(() => {
    if (!weekTarget_current) return null;
    return (weekLanding_current - weekTarget_current) / weekTarget_current;
  }, [weekLanding_current, weekTarget_current]);

  const diffPctMonth = useMemo(() => {
    if (!monthTarget) return null;
    return (monthLanding - monthTarget) / monthTarget;
  }, [monthLanding, monthTarget]);

  /* ===== 表示用：月（日本語） ===== */
  const monthJP = useMemo(() => formatMonthJP(month), [month]);

  return (
    <div style={{ padding: 16 }}>
      {/* ヘッダー */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 8 }}>
        <Col aria-live="polite" aria-label={`${monthJP}を表示中`}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            搬入量（運用）ダッシュボード — {monthJP}
          </Typography.Title>
          <div style={{ marginTop: 4 }}>
            <TinyLabel>現在週：</TinyLabel>
            {currentWeek ? <Tag color="blue">{currentWeek.key}</Tag> : <Tag>—</Tag>}
            <AntTooltip title="週は月曜〜土曜。KPIは月基準のまま、グラフのみ週切替。">
              <span style={{ color: '#8c8c8c', marginLeft: 6 }}>?</span>
            </AntTooltip>
          </div>
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

      {/* 上段：サマリー帯（6指標以内） */}
      <SectionCard title={`サマリー（${monthJP}）`} tooltip="一目で状況判断：目標/達成率/着地/乖離/必要ペース/現行ペース">
        <Row gutter={[DENSE.gutter, DENSE.gutter]}>
          <Col xs={12} md={8} lg={4}>
            <KPI label="月目標" value={<>{monthTarget.toLocaleString()} <span style={{fontSize:14}}>t</span></>} />
          </Col>
          <Col xs={12} md={8} lg={4}>
            <KPI label="MTD達成率" value={formatPct(monthRates.mtdRate, 0)} />
          </Col>
          <Col xs={12} md={8} lg={4}>
            <KPI label="月着地" value={<>{monthLanding.toLocaleString()} <span style={{fontSize:14}}>t</span></>} />
          </Col>
          <Col xs={12} md={8} lg={4}>
            <KPI label="月乖離" value={<SoftBadge value={diffPctMonth} />} hint="(着地−目標)/目標" />
          </Col>
          <Col xs={12} md={8} lg={4}>
            <KPI label="必要平均" value={runRate.requiredPerDay != null ? `${runRate.requiredPerDay.toFixed(1)} t/日` : '—'} />
          </Col>
          <Col xs={12} md={8} lg={4}>
            <KPI label="現行ペース" value={runRate.currentPace != null ? `${runRate.currentPace.toFixed(1)} t/日` : '—'} />
          </Col>
        </Row>
      </SectionCard>

      {/* 中段：左右2カード（実績／予測） */}
      <Row gutter={[DENSE.gutter, DENSE.gutter]}>
        {/* 実績（確定） */}
        <Col xs={24} md={12}>
          <SectionCard title="実績ドメイン（確定）">
            {daily ? (
              <Row gutter={[DENSE.gutter, 8]}>
                <Col xs={12}><KPI label="今日実績" value={<>{todayActual ?? '—'} <span style={{fontSize:14}}>t</span></>} /></Col>
                <Col xs={12}><KPI label="週累計" value={<>{weekActualCum} <span style={{fontSize:14}}>t</span></>} /></Col>
                <Col xs={12}><KPI label="MTD累計" value={<>{monthActualCum} <span style={{fontSize:14}}>t</span></>} /></Col>
                <Col xs={12}><KPI label="WTD達成率" value={formatPct(weekRates_current.weekRateConfirmed, 0)} /></Col>
                <Col xs={12}><KPI label="MTD達成率" value={formatPct(monthRates.mtdRate, 0)} /></Col>
                <Col xs={24}>
                  <div style={{ marginTop: 4 }}>
                    <Progress percent={Math.round((monthRates.mtdRate ?? 0) * 100)} showInfo={false} strokeWidth={6} />
                  </div>
                </Col>
              </Row>
            ) : <Skeleton active paragraph={{rows:2}} title={false} />}
          </SectionCard>
        </Col>

        {/* 予測（見込み） */}
        <Col xs={24} md={12}>
          <SectionCard title="予測ドメイン（見込み）">
            {daily ? (
              <Row gutter={[DENSE.gutter, 8]}>
                <Col xs={12}><KPI label="今日予測" value={<>{todayForecast ?? 0} <span style={{fontSize:14}}>t</span></>} /></Col>
                <Col xs={12}><KPI label="週着地" value={<>{weekLanding_current} <span style={{fontSize:14}}>t</span></>} /></Col>
                <Col xs={12}><KPI label="月着地" value={<>{monthLanding} <span style={{fontSize:14}}>t</span></>} /></Col>
                <Col xs={12}><KPI label="WTD見込み" value={formatPct(weekRates_current.weekRateProjected, 0)} /></Col>
                <Col xs={12}><KPI label="月見込み" value={formatPct(monthRates.monthRateProj, 0)} /></Col>
                <Col xs={12}>
                  <div style={{ display:'flex', justifyContent:'flex-end', marginTop: 4 }}>
                    <SoftBadge value={diffPctWeek} />
                  </div>
                </Col>
                <Col xs={24}>
                  <div style={{ display:'flex', justifyContent:'flex-end' }}>
                    <TinyLabel>{formatDateJP(todayStr)} ／ 今日乖離：<SoftBadge value={diffPctToday} /></TinyLabel>
                  </div>
                </Col>
              </Row>
            ) : <Skeleton active paragraph={{rows:2}} title={false} />}
          </SectionCard>
        </Col>
      </Row>

      {/* 下段：週タブ付きグラフ（高さを抑える） */}
      <SectionCard
        title="実績 vs 予測（日別）"
        tooltip="グラフのみ週タブで切替。色：実績=緑／予測=青／目標=橙。"
        extra={<Tag color="geekblue">{monthJP}</Tag>}
      >
        <Tabs
          activeKey={activeWeekKey}
          onChange={setActiveWeekKey}
          items={weeks.map(w => ({ key: w.key, label: w.key }))}
          style={{ marginBottom: 8 }}
          size="small"
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
                <ReferenceLine
                  y={weekChartData.length ? (weekChartData[0]?.目標 ?? undefined) : undefined}
                  stroke={Colors.target}
                  strokeDasharray="4 4"
                  ifOverflow="extendDomain"
                />
                <Bar dataKey="予測" fill={Colors.forecast} />
                <Bar dataKey="実績" fill={Colors.actual} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </SectionCard>
    </div>
  );
};

export default ExecutiveForecastDashboard;
