/**
 * 受入ダッシュボード - Mock Repository
 * モックデータ生成によるRepository実装
 */

import dayjs from "dayjs";
import type { IInboundForecastRepository } from "../../domain/repository";
import type {
  IsoMonth,
  IsoDate,
  MonthPayloadDTO,
  CalendarDay,
  TargetsDTO,
  HeaderDTO,
  ProgressDTO,
  ForecastDTO,
  DailyCurveDTO,
  WeekRowDTO,
} from "../../domain/types";
import {
  toDate,
  ymd,
  mondayOf,
  addDays,
  sum,
  todayInMonth,
} from "../../domain/valueObjects";

export class MockInboundForecastRepository
  implements IInboundForecastRepository
{
  async fetchMonthPayload(month: IsoMonth): Promise<MonthPayloadDTO> {
    // モック遅延
    await new Promise((resolve) => setTimeout(resolve, 300));

    const first = dayjs(month + "-01");
    const last = first.endOf("month");
    const days: CalendarDay[] = [];
    let d = first;

    while (d.isBefore(last) || d.isSame(last, "day")) {
      const date = d.format("YYYY-MM-DD");
      const dow = d.day();
      const is_business_day = dow === 0 ? 0 : 1;
      const is_holiday = dow === 0 ? 1 : 0;
      days.push({
        date,
        is_business_day,
        is_holiday,
        week_id: ymd(mondayOf(d.toDate())),
      });
      d = d.add(1, "day");
    }

    const wWeekday = 1.0,
      wSat = 1.1,
      wSunHol = 0.6;
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

    const bizWeights = days.map((x) =>
      x.is_business_day ? weightOf(x.date) : 0,
    );
    const monthTarget = Math.round(sum(bizWeights) * 110);

    const weekMap = new Map<
      string,
      {
        start: IsoDate;
        end: IsoDate;
        tonInMonth: number;
        inMonthBiz: number;
        fullBiz: number;
      }
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
      weekMap.set(wid, {
        start: ymd(calStart),
        end: ymd(wEnd),
        tonInMonth: 0,
        inMonthBiz: 0,
        fullBiz,
      });
      calStart = addDays(calStart, 7);
    }

    const lastDay = last.date();
    const syntheticDailyTon: Record<IsoDate, number> = {};
    days.forEach((x, i) => {
      const base = 100 + Math.sin(((i + 1) / lastDay) * Math.PI * 2) * 20;
      const dow = toDate(x.date).getDay();
      const adj = dow === 6 ? 10 : 0;
      const noise = (Math.random() - 0.5) * 12;
      const ton = x.is_business_day
        ? Math.max(35, Math.round(base + adj + noise))
        : 0;
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

    const weekEntries = [...weekMap.entries()].sort((a, b) =>
      a[0] < b[0] ? -1 : 1,
    );
    let idx = 0;
    const weekRows: WeekRowDTO[] = [];
    for (const [, v] of weekEntries) {
      if (v.inMonthBiz > 0) {
        idx += 1;
        weekRows.push({
          week_id: v.start,
          week_start: v.start,
          week_end: v.end,
          business_week_index_in_month: idx,
          ton_in_month: Math.round(v.tonInMonth),
          in_month_business_days: v.inMonthBiz,
          portion_in_month: v.fullBiz ? v.inMonthBiz / v.fullBiz : 0,
          targets: { week: 0 },
          comparisons: {
            vs_prev_week: {
              delta_ton: null,
              delta_pct: null,
              align_note: "prev business week",
            },
            vs_prev_month_same_idx: {
              delta_ton: null,
              delta_pct: null,
              align_note: "same idx",
            },
            vs_prev_year_same_idx: {
              delta_ton: null,
              delta_pct: null,
              align_note: "same idx",
            },
          },
        });
      }
    }
    const totalBizDays = sum(weekRows.map((w) => w.in_month_business_days));
    weekRows.forEach((w) => {
      w.targets.week = totalBizDays
        ? Math.round(monthTarget * (w.in_month_business_days / totalBizDays))
        : 0;
    });

    const today = todayInMonth(month);
    const mtdActual = sum(
      days.filter((x) => x.date <= today).map((x) => syntheticDailyTon[x.date]),
    );
    const remainingBiz = days.filter(
      (x) => x.date > today && x.is_business_day,
    ).length;

    const futureTon = sum(
      days.filter((x) => x.date > today).map((x) => syntheticDailyTon[x.date]),
    );
    const monthP50 = mtdActual + futureTon;
    const pBand = Math.max(80, Math.round(monthP50 * 0.06));
    const forecast: ForecastDTO = {
      today: {
        p50: syntheticDailyTon[today] ?? 0,
        p10: Math.max(0, (syntheticDailyTon[today] ?? 0) - 15),
        p90: (syntheticDailyTon[today] ?? 0) + 15,
      },
      week: {
        p50: Math.round(
          sum(
            days
              .filter(
                (x) =>
                  toDate(x.date) >= mondayOf(toDate(today)) &&
                  toDate(x.date) <= addDays(mondayOf(toDate(today)), 6),
              )
              .map((x) => syntheticDailyTon[x.date]),
          ),
        ),
        p10: 0,
        p90: 0,
        target: 0,
      },
      month_landing: {
        p50: monthP50,
        p10: Math.max(0, monthP50 - pBand),
        p90: monthP50 + pBand,
      },
    };

    const daily_curve: DailyCurveDTO[] = days.map((x, i) => {
      const dow = toDate(x.date).getDay();
      const backIdx = Math.max(0, i - 7);
      const near = days
        .slice(backIdx, i)
        .filter((d) => toDate(d.date).getDay() === dow);
      const avg = near.length
        ? Math.round(
            sum(near.map((d) => syntheticDailyTon[d.date])) / near.length,
          )
        : syntheticDailyTon[x.date];
      const wAll = sum(
        days.map((d) =>
          toDate(d.date).getDay() === 0 ? 0 : dayWeightForBShare(d.date),
        ),
      );
      const wMe =
        toDate(x.date).getDay() === 0 ? 0 : dayWeightForBShare(x.date);
      const fromMonthShare = wAll ? Math.round(monthTarget * (wMe / wAll)) : 0;
      const bookings = Math.max(
        0,
        Math.round(Math.random() * 6 - (toDate(x.date).getDay() === 0 ? 6 : 0)),
      );
      return {
        date: x.date,
        from_7wk: avg,
        from_month_share: fromMonthShare,
        bookings,
        actual: syntheticDailyTon[x.date],
      };
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
      const base =
        daily_curve.find((r) => r.date === corresponding)?.actual ?? 80;
      prevMonthDays[k] = Math.max(0, Math.round(base * 0.98));
      pd = pd.add(1, "day");
    }
    const pyFirst = dayjs(month + "-01").subtract(1, "year");
    const pyLast = pyFirst.endOf("month");
    let yd = pyFirst;
    while (yd.isBefore(pyLast) || yd.isSame(pyLast, "day")) {
      const k = yd.format("YYYY-MM-DD");
      const corresponding = dayjs(k).add(1, "year").format("YYYY-MM-DD");
      const base =
        daily_curve.find((r) => r.date === corresponding)?.actual ?? 80;
      prevYearDays[k] = Math.max(0, Math.round(base * 0.95));
      yd = yd.add(1, "day");
    }

    const targets: TargetsDTO = {
      month: monthTarget,
      weeks: weekRows.map((w) => ({
        bw_idx: w.business_week_index_in_month,
        week_target: w.targets.week,
      })),
      day_weights: { weekday: wWeekday, sat: wSat, sun_hol: wSunHol },
    };

    const header: HeaderDTO = {
      month,
      business_days: {
        total: days.filter((x) => x.is_business_day).length,
        mon_sat: days.filter(
          (x) =>
            x.is_business_day &&
            toDate(x.date).getDay() <= 6 &&
            toDate(x.date).getDay() !== 0,
        ).length,
        sun_holiday: days.filter(
          (x) => x.is_business_day && toDate(x.date).getDay() === 0,
        ).length,
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
      history: {
        m_vs_prev_month: { delta_ton: 0, delta_pct: 0, align_note: "mock" },
        m_vs_prev_year: { delta_ton: 0, delta_pct: 0 },
        m_vs_3yr_avg: { delta_ton: 0, delta_pct: 0 },
      },
      prev_month_daily: prevMonthDays,
      prev_year_daily: prevYearDays,
    };
  }
}
