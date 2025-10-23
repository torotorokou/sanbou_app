import React, { useMemo } from "react";
import { Card, Skeleton, Typography } from "antd";
import UkeireCalendar from "./UkeireCalendar";
import { useUkeireCalendarVM } from "../application/useUkeireCalendarVM";
import { CalendarRepositoryForUkeire } from "../infrastructure/calendar.http.repository";
import type { ICalendarRepository } from "@/features/calendar/model/repository";
import type { CalendarDayDTO } from "@/features/calendar/model/types";

type DayDecor = {
  date: string;
  status?: string;
  label?: string | null;
  color?: string | null;
};

type CalendarPayload = {
  month: string;
  days: DayDecor[];
  legend?: Array<{ key: string; label: string; color?: string | null }>;
};

type Props = {
  year: number;
  month: number;
  repository?: ICalendarRepository;
  title?: string;
  style?: React.CSSProperties;
};

/**
 * CalendarDayDTO から CalendarPayload への変換
 */
function convertToPayload(year: number, month: number, days: CalendarDayDTO[]): CalendarPayload {
  const pad = (n: number) => String(n).padStart(2, '0');
  const monthStr = `${year}-${pad(month)}`;
  
  const dayDecors: DayDecor[] = days.map((d): DayDecor => {
    // day_type に基づいてステータスを判定
    // NORMAL: 営業日（緑）
    // RESERVATION: 日曜・祝日（ピンク）
    // CLOSED: 休業日（赤）
    let status: "business" | "holiday" | "closed" = "business";
    let label: string | undefined = undefined;
    
    if (d.day_type === "CLOSED" || d.is_company_closed) {
      status = "closed";
      label = "休業日";
    } else if (d.day_type === "RESERVATION" || d.is_holiday) {
      status = "holiday";
      label = d.is_holiday ? "祝日" : "日曜";
    } else {
      status = "business";
      label = undefined;
    }
    
    return {
      date: d.ddate,
      status,
      label,
      color: undefined,
    };
  });
  
  return {
    month: monthStr,
    days: dayDecors,
    legend: [
      { key: "business", label: "営業日", color: "#52c41a" },
      { key: "holiday", label: "日曜・祝日", color: "#ff85c0" },
      { key: "closed", label: "休業日", color: "#cf1322" },
    ],
  };
}

export default function CalendarCard({ year, month, repository, title = "営業カレンダー", style }: Props) {
  const repo = useMemo(() => repository ?? new CalendarRepositoryForUkeire(), [repository]);
  const vm = useUkeireCalendarVM({ year, month, repository: repo });

  const pad = (n: number) => String(n).padStart(2, "0");
  const monthStr = `${year}-${pad(month)}`;

  const payload = useMemo(() => {
    if (vm.grid.length === 0) {
      return {
        month: monthStr,
        days: [],
        legend: [],
      };
    }
    // grid から実際の月内データを抽出
    const monthDays = vm.grid.flat().filter((d: CalendarDayDTO & { inMonth: boolean }) => d.inMonth);
    return convertToPayload(year, month, monthDays);
  }, [vm.grid, year, month, monthStr]);

  if (vm.loading) {
    return (
      <Card title={title} style={style}>
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    );
  }

  if (vm.error) {
    return (
      <Card title={title} style={style}>
        <Typography.Text type="danger">{vm.error}</Typography.Text>
      </Card>
    );
  }

  return (
    <Card 
      title={title} 
      style={{ 
        height: "100%", 
        display: "flex", 
        flexDirection: "column",
        ...style 
      }}
      bodyStyle={{
        flex: 1,
        minHeight: 0,
        overflow: "hidden",
        padding: 12,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        <UkeireCalendar
          month={payload.month}
          days={payload.days}
          legend={payload.legend}
        />
      </div>
    </Card>
  );
}

