/**
 * CalendarCard Component (DI対応共通版)
 * 営業カレンダーを表示するカード - Repository を Props で受け取る汎用カード
 */

import React, { useMemo } from "react";
import { Card, Typography, Tooltip, Skeleton } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import UkeireCalendar from "@/features/dashboard/ukeire/business-calendar/ui/components/UkeireCalendar";
import { useCalendarVM } from "@/features/calendar/model/useCalendarVM";
import type { ICalendarRepository } from "@/features/calendar/ports/repository";
import type { CalendarDayDTO } from "@/features/calendar/domain/types";

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

export type CalendarCardProps = {
  year: number;
  month: number;
  repository: ICalendarRepository;
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

export const CalendarCard: React.FC<CalendarCardProps> = ({ year, month, repository, style }) => {
  const vm = useCalendarVM({ repository, year, month });
  
  const payload = useMemo(() => {
    if (vm.grid.length === 0) {
      return {
        month: `${year}-${String(month).padStart(2, '0')}`,
        days: [],
        legend: [],
      };
    }
    // grid から実際の月内データを抽出
    const monthDays = vm.grid.flat().filter(d => d.inMonth).map(d => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { inMonth, ...rest } = d;
      return rest;
    });
    return convertToPayload(year, month, monthDays);
  }, [vm.grid, year, month]);

  if (vm.loading) {
    return (
      <Card
        bordered
        size="small"
        style={{ height: "100%", display: "flex", flexDirection: "column", ...(style || {}) }}
        styles={{ body: { display: "flex", flexDirection: "column", padding: 12, gap: 8, flex: 1, minHeight: 0 } }}
      >
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    );
  }

  if (vm.error) {
    return (
      <Card
        bordered
        size="small"
        style={{ height: "100%", display: "flex", flexDirection: "column", ...(style || {}) }}
        styles={{ body: { display: "flex", flexDirection: "column", padding: 12, gap: 8, flex: 1, minHeight: 0 } }}
      >
        <Typography.Text type="danger">{vm.error}</Typography.Text>
      </Card>
    );
  }

  return (
    <Card
      variant="outlined"
      size="small"
      style={{ height: "100%", display: "flex", flexDirection: "column", ...(style || {}) }}
      bodyStyle={{ display: "flex", flexDirection: "column", padding: 12, gap: 8, flex: 1, minHeight: 0 }}
    >
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", position: "relative" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Typography.Title level={5} style={{ margin: 0, fontSize: 16 }}>
            営業カレンダー
          </Typography.Title>
          <Tooltip title="SQL起点のカレンダーデータ。祝日・休業日はサーバ側で管理。">
            <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
          </Tooltip>
        </div>

        {/* right placeholder kept for symmetry if needed */}
        <div style={{ position: "absolute", right: 12 }} />
      </div>

      <div style={{ flex: 1, minHeight: 0, overflow: "hidden", height: "100%" }}>
        <UkeireCalendar
          month={payload.month}
          days={payload.days}
          legend={payload.legend}
        />
      </div>
    </Card>
  );
};

export default CalendarCard;
