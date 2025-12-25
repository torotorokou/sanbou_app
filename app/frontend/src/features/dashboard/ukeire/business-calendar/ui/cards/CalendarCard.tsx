import React, { useMemo } from "react";
import { Card, Skeleton, Typography, Tooltip } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import UkeireCalendar from "../components/UkeireCalendar";
import { useBusinessCalendarVM } from "../../model/useBusinessCalendarVM";
import { CalendarRepositoryForUkeire } from "../../infrastructure/calendar.repository";
import type { ICalendarRepository } from "@/features/calendar/ports/repository";
import type { CalendarDayDTO } from "@/features/calendar/domain/types";

type DayDecor = {
  date: string;
  status?: string;
  label?: string | null;
  color?: string | null;
  iso_week?: number;
  iso_year?: number;
};

type CalendarPayload = {
  month: string;
  days: DayDecor[];
  legend?: Array<{ key: string; label: string; color?: string | null }>;
};

type Props = {
  year: number;
  month: number;
  /**
   * カレンダーデータのリポジトリ
   *
   * @default CalendarRepositoryForUkeire（バックエンドAPIから取得）
   *
   * 開発・テスト時にMockを使用する場合:
   * ```ts
   * import { MockCalendarRepositoryForUkeire } from "@/features/dashboard/ukeire";
   * <CalendarCard year={2025} month={1} repository={new MockCalendarRepositoryForUkeire()} />
   * ```
   */
  repository?: ICalendarRepository;
  title?: string;
  style?: React.CSSProperties;
};

/**
 * CalendarDayDTO から CalendarPayload への変換
 * day_typeに基づいて正確にステータスを判定
 */
function convertToPayload(
  year: number,
  month: number,
  days: CalendarDayDTO[],
): CalendarPayload {
  const pad = (n: number) => String(n).padStart(2, "0");
  const monthStr = `${year}-${pad(month)}`;

  const dayDecors: DayDecor[] = days.map((d): DayDecor => {
    // day_type に基づいて正確にステータスを判定
    // NORMAL: 通常営業日（緑）
    // RESERVATION: 予約営業日（ピンク）
    // CLOSED: 休業日（赤）
    let status: "business" | "holiday" | "closed";
    let label: string | undefined;
    let color: string;

    switch (d.day_type) {
      case "CLOSED":
        status = "closed";
        label = "休業日";
        color = "#cf1322"; // 赤
        break;
      case "RESERVATION":
        status = "holiday";
        label = d.is_holiday ? "祝日" : "予約営業日";
        color = "#ff85c0"; // ピンク
        break;
      case "NORMAL":
      default:
        status = "business";
        label = undefined;
        color = "#52c41a"; // 緑
        break;
    }

    return {
      date: d.ddate,
      status,
      label,
      color,
      iso_week: d.iso_week,
      iso_year: d.iso_year,
    };
  });

  return {
    month: monthStr,
    days: dayDecors,
    legend: [
      { key: "business", label: "通常営業日", color: "#52c41a" },
      { key: "holiday", label: "予約営業日", color: "#ff85c0" },
      { key: "closed", label: "休業日", color: "#cf1322" },
    ],
  };
}

// カレンダー用ツールチップ文言をモジュール内にまとめて保守性を高める
const CALENDAR_TOOLTIP_TEXTS = {
  business: "営業日（残り日数）",
  holiday: "日曜・祝日（残り日数）",
  closed: "非営業日（残り日数）",
};

const CALENDAR_TOOLTIP_TITLE = (
  <div>
    <div>{CALENDAR_TOOLTIP_TEXTS.business}</div>
    <div>{CALENDAR_TOOLTIP_TEXTS.holiday}</div>
    <div>{CALENDAR_TOOLTIP_TEXTS.closed}</div>
  </div>
);

export function CalendarCard({
  year,
  month,
  repository,
  title = "営業カレンダー",
  style,
}: Props) {
  const repo = useMemo(
    () => repository ?? new CalendarRepositoryForUkeire(),
    [repository],
  );
  const vm = useBusinessCalendarVM({ year, month, repository: repo });

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
    const monthDays = vm.grid
      .flat()
      .filter((d: CalendarDayDTO & { inMonth: boolean }) => d.inMonth);
    return convertToPayload(year, month, monthDays);
  }, [vm.grid, year, month, monthStr]);

  if (vm.loading) {
    return (
      <Card
        title={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Typography.Title level={5} style={{ margin: 0, fontSize: 16 }}>
              {title}
            </Typography.Title>
            <Tooltip title={CALENDAR_TOOLTIP_TITLE}>
              <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
            </Tooltip>
          </div>
        }
        style={style}
      >
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    );
  }

  if (vm.error) {
    return (
      <Card
        title={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Typography.Title level={5} style={{ margin: 0, fontSize: 16 }}>
              {title}
            </Typography.Title>
            <Tooltip title={CALENDAR_TOOLTIP_TITLE}>
              <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
            </Tooltip>
          </div>
        }
        style={style}
      >
        <Typography.Text type="danger">{vm.error}</Typography.Text>
      </Card>
    );
  }

  return (
    <Card
      title={
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Typography.Title level={5} style={{ margin: 0, fontSize: 16 }}>
            {title}
          </Typography.Title>
          <Tooltip title={CALENDAR_TOOLTIP_TITLE}>
            <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
          </Tooltip>
        </div>
      }
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        ...style,
      }}
      styles={{
        body: {
          flex: 1,
          minHeight: 0,
          overflow: "hidden",
          padding: 12,
          display: "flex",
          flexDirection: "column",
        },
      }}
    >
      <div
        style={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <UkeireCalendar
          month={payload.month}
          days={payload.days}
          legend={payload.legend}
        />
      </div>
    </Card>
  );
}
