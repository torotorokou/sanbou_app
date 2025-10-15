import React from "react";
import dayjs, { type Dayjs } from "dayjs";
import styles from "./CalendarGrid.module.css";

interface CalendarGridProps {
  month: string; // "YYYY-MM"
  rowHeight?: number; // px
  renderCell: (date: Dayjs, inMonth: boolean) => React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

const DOW = ["日", "月", "火", "水", "木", "金", "土"];

const CalendarGrid: React.FC<CalendarGridProps> = ({
  month,
  rowHeight = 28,
  renderCell,
  className,
  style,
}) => {
  const first = dayjs(month + "-01");
  const startDow = first.day();
  const daysInMonth = first.daysInMonth();
  const weeks = Math.ceil((startDow + daysInMonth) / 7);
  const total = weeks * 7;

  const dates: Dayjs[] = [];
  for (let i = 0; i < total; i++) dates.push(first.add(i - startDow, "day"));

  return (
    <div className={className} style={style}>
      {/* Header row: render 8 header cells (W + 7 weekdays) so columns align with grid */}
      <div
        className={styles.headerRow}
        style={{ ...( { ["--row-h"]: `${rowHeight}px` } as React.CSSProperties ) }}
      >
        {[
          "W",
          ...DOW,
        ].map((label, idx) => (
          <div key={idx} className={styles.headerCell}>
            {label}
          </div>
        ))}
      </div>

      {/* Grid: left column week numbers + 7*weeks cells */}
      <div
        className={styles.gridWrapper}
        style={{
          // CSS custom property for row height — cast to CSSProperties to satisfy TS
          ...( { ["--row-h"]: `${rowHeight}px` } as React.CSSProperties ),
        }}
      >
        <div className={styles.weekCol}>
          {Array.from({ length: weeks }).map((_, w) => (
            <div key={w} className={styles.weekCell}>
              {`W${w + 1}`}
            </div>
          ))}
        </div>

        <div className={styles.grid}>
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
    </div>
  );
};

export default CalendarGrid;
