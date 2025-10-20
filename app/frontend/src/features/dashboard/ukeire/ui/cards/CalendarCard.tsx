import React, { useMemo } from "react";
import { Card, Skeleton, Typography } from "antd";
import CalendarCore from "@/features/calendar/ui/CalendarCore";
import { useUkeireCalendarVM } from "@/features/dashboard/ukeire/application/useUkeireCalendarVM";
import { CalendarRepositoryForUkeire } from "@/features/dashboard/ukeire/application/adapters/calendar.http.repository";
import type { ICalendarRepository } from "@/features/calendar/model/repository";
import type { CalendarDayDTO } from "@/features/calendar/model/types";

type Props = {
  year: number;
  month: number;
  repository?: ICalendarRepository;
  title?: string;
  style?: React.CSSProperties;
};

export default function CalendarCard({ year, month, repository, title = "営業カレンダー", style }: Props) {
  const repo = useMemo(() => repository ?? new CalendarRepositoryForUkeire(), [repository]);
  const vm = useUkeireCalendarVM({ year, month, repository: repo });

  const pad = (n: number) => String(n).padStart(2, "0");
  const monthStr = `${year}-${pad(month)}`;

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

  // Flatten grid for CalendarCore
  const cells = vm.grid.flat();

  return (
    <Card title={title} style={style}>
      <CalendarCore
        month={monthStr}
        cells={cells}
        renderCell={(cell: CalendarDayDTO & { inMonth: boolean }) => {
          const day = new Date(cell.date).getDate();
          return (
            <div
              style={{
                backgroundColor: cell.isHoliday ? "#ff85c0" : cell.inMonth ? "#f0f0f0" : "#fafafa",
                padding: "4px",
                borderRadius: "2px",
              }}
            >
              {day}
            </div>
          );
        }}
      />
    </Card>
  );
}

