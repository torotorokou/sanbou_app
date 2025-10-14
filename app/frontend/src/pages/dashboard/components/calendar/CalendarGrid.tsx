import React from "react";
import dayjs, { Dayjs } from "dayjs";
import styles from "./CalendarGrid.module.css";

interface CalendarGridProps {
  month: string; // "YYYY-MM"
  rowHeight?: number; // px
  renderCell: (date: Dayjs, inMonth: boolean) => React.ReactNode;
  className?: string;
}

const DOW = ["日", "月", "火", "水", "木", "金", "土"];

const CalendarGrid: React.FC<CalendarGridProps> = ({
  month,
  rowHeight = 28,
  renderCell,
  className,
}) => {
  const first = dayjs(month + "-01");
  const startDow = first.day();

  const dates: Dayjs[] = [];
  for (let i = 0; i < 42; i++) dates.push(first.add(i - startDow, "day"));

  return (
    <div className={className}>
      <div className={styles.dow}>
        {DOW.map((d) => (
          <div key={d}>{d}</div>
        ))}
      </div>

      <div
        className={styles.grid}
        style={{ ["--row-h" as any]: `${rowHeight}px` }}
      >
        {dates.map((d, i) => {
          const inMonth = d.month() === first.month();
          return (
            <div key={i} className={styles.cell}>
              {renderCell(d, inMonth)}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CalendarGrid;
