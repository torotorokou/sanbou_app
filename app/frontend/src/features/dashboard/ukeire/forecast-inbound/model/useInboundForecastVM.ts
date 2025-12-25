/**
 * Inbound Forecast ViewModel
 * 受入予測データを取得して UI props に整形
 */

import { useEffect, useState } from "react";
import dayjs from "dayjs";
import type { IInboundForecastRepository } from "../ports/repository";
import type {
  IsoMonth,
  MonthPayloadDTO,
  DailyCurveDTO,
} from "../../domain/types";
import {
  sum,
  getActualCutoffIso,
  curMonth,
  monthNameJP,
} from "../../domain/valueObjects";
import {
  calculateOneBusinessDayTarget,
  calculateWeekStats,
  getTodayActual,
} from "../../domain/services/targetService";
import type { TargetCardProps } from "../../kpi-targets/ui/cards/TargetCard";
import type { CombinedDailyCardProps } from "../../inbound-monthly/ui/cards/CombinedDailyCard";
import type { ForecastCardProps } from "../ui/cards/ForecastCard";

export type InboundForecastViewModel = {
  month: IsoMonth;
  monthJP: string;
  loading: boolean;
  payload: MonthPayloadDTO | null;
  targetCardProps: TargetCardProps | null;
  combinedDailyProps: CombinedDailyCardProps | null;
  forecastCardProps: ForecastCardProps | null;
  headerProps: {
    todayBadge: string;
  } | null;
};

export const useInboundForecastVM = (
  repository: IInboundForecastRepository,
  initialMonth: IsoMonth = curMonth(),
): InboundForecastViewModel & { setMonth: (m: IsoMonth) => void } => {
  const [month, setMonth] = useState<IsoMonth>(initialMonth);
  const [loading, setLoading] = useState(false);
  const [payload, setPayload] = useState<MonthPayloadDTO | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    repository
      .fetchMonthPayload(month)
      .then((p) => {
        if (alive) setPayload(p);
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [month, repository]);

  const actualCutoff = getActualCutoffIso(month);
  const maskedRows: DailyCurveDTO[] = payload
    ? payload.daily_curve.map((r) => ({
        ...r,
        actual: r.date <= actualCutoff ? r.actual : undefined,
      }))
    : [];

  const mtdMasked = sum(maskedRows.map((r) => r.actual ?? 0));

  const targetCardProps: TargetCardProps | null = payload
    ? {
        rows: [
          {
            key: "month",
            label: "1ヶ月",
            target: payload.targets.month,
            actual: mtdMasked,
          },
          {
            key: "week",
            label: "今週",
            target: calculateWeekStats(
              payload.targets,
              payload.calendar.days,
              maskedRows,
            ).target,
            actual: calculateWeekStats(
              payload.targets,
              payload.calendar.days,
              maskedRows,
            ).actual,
          },
          {
            key: "day",
            label: "1日",
            target: calculateOneBusinessDayTarget(
              payload.targets,
              payload.calendar.days,
            ),
            actual: getTodayActual(maskedRows),
          },
        ],
      }
    : null;

  const combinedDailyProps: CombinedDailyCardProps | null = payload
    ? {
        dailyProps: {
          chartData: maskedRows.map((r) => {
            const prevMonthKey = dayjs(r.date)
              .subtract(1, "month")
              .format("YYYY-MM-DD");
            const prevYearKey = dayjs(r.date)
              .subtract(1, "year")
              .format("YYYY-MM-DD");
            return {
              label: dayjs(r.date).format("DD"),
              actual: typeof r.actual === "number" ? r.actual : undefined,
              dateFull: r.date,
              prevMonth: payload.prev_month_daily
                ? (payload.prev_month_daily[prevMonthKey] ?? null)
                : null,
              prevYear: payload.prev_year_daily
                ? (payload.prev_year_daily[prevYearKey] ?? null)
                : null,
            };
          }),
        },
        cumulativeProps: {
          cumData: (() => {
            let running = 0,
              accPM = 0,
              accPY = 0;
            return maskedRows.map((r) => {
              if (typeof r.actual === "number") running += r.actual;
              const pmKey = dayjs(r.date)
                .subtract(1, "month")
                .format("YYYY-MM-DD");
              const pyKey = dayjs(r.date)
                .subtract(1, "year")
                .format("YYYY-MM-DD");
              const pmVal = payload.prev_month_daily
                ? (payload.prev_month_daily[pmKey] ?? 0)
                : 0;
              const pyVal = payload.prev_year_daily
                ? (payload.prev_year_daily[pyKey] ?? 0)
                : 0;
              accPM += pmVal;
              accPY += pyVal;
              return {
                label: dayjs(r.date).format("DD"),
                yyyyMMdd: r.date,
                actualCumulative: running,
                prevMonthCumulative: accPM,
                prevYearCumulative: accPY,
              };
            });
          })(),
        },
      }
    : null;

  const forecastCardProps: ForecastCardProps | null = payload
    ? (() => {
        const daysInMonth = maskedRows.length;
        const base =
          payload.targets.month && daysInMonth
            ? payload.targets.month / daysInMonth
            : 0;
        const chartData: {
          label: string;
          daily: number;
          dailyForward?: number;
          actual?: number;
        }[] = [];
        const todayDate = dayjs();
        let forwardStartDay =
          todayDate.format("YYYY-MM") === month ? todayDate.date() : 1;
        const forwardEndDay = Math.min(daysInMonth, forwardStartDay + 6);

        for (let idx = 0; idx < maskedRows.length; idx++) {
          const r = maskedRows[idx];
          const i = idx + 1;
          const factor =
            0.9 + 0.2 * (0.5 + Math.sin((i / daysInMonth) * Math.PI * 2) / 2);
          const daily = Math.round(base * factor);
          const dailyForward =
            i >= forwardStartDay && i <= forwardEndDay
              ? Math.round(
                  base *
                    (0.9 +
                      0.2 *
                        (0.5 + Math.sin((i / daysInMonth) * Math.PI * 2) / 2)),
                )
              : 0;
          const actualDay = typeof r.actual === "number" ? r.actual : undefined;
          chartData.push({
            label: String(i).padStart(2, "0"),
            daily,
            dailyForward,
            actual: actualDay,
          });
        }

        let runReverse = 0;
        let runActual = 0;
        const cumData = chartData.map((d) => {
          runReverse += Number(d.daily || 0);
          if (typeof d.actual === "number") runActual += Number(d.actual);
          return { ...d, cumDaily: runReverse, cumActual: runActual };
        });

        const oddDayTicks = Array.from({ length: daysInMonth }, (_, i) =>
          String(i + 1).padStart(2, "0"),
        ).filter((s) => Number(s) % 2 === 1);

        return {
          kpis: [
            {
              title: "当日",
              p50: payload.forecast.today.p50,
              p10: payload.forecast.today.p10,
              p90: payload.forecast.today.p90,
              target: daysInMonth
                ? Math.round(payload.targets.month / daysInMonth)
                : null,
            },
            {
              title: "今週",
              p50: payload.forecast.week.p50,
              p10: payload.forecast.week.p10,
              p90: payload.forecast.week.p90,
              target: daysInMonth
                ? Math.round((payload.targets.month / daysInMonth) * 7)
                : null,
            },
            {
              title: "今月末",
              p50: payload.forecast.month_landing.p50,
              p10: payload.forecast.month_landing.p10,
              p90: payload.forecast.month_landing.p90,
              target: payload.targets.month,
            },
          ],
          chartData,
          cumData,
          oddDayTicks,
        };
      })()
    : null;

  const headerProps = payload
    ? {
        todayBadge: dayjs().format("DD"),
      }
    : null;

  return {
    month,
    monthJP: monthNameJP(month),
    loading,
    payload,
    targetCardProps,
    combinedDailyProps,
    forecastCardProps,
    headerProps,
    setMonth,
  };
};
