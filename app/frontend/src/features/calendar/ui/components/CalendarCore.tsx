/**
 * CalendarCore Component
 * カレンダーグリッドの汎用コア実装（features/calendar に統一）
 */

import React from "react";
import dayjs from "dayjs";
import styles from "../../styles/calendar.module.css";
import type { CalendarCell } from "../../domain/types";

export interface CalendarCoreProps<T extends CalendarCell = CalendarCell> {
  month: string; // "YYYY-MM"
  rowHeight?: number; // px
  cells?: T[]; // 外部から提供される場合
  renderCell: (cell: T) => React.ReactNode;
  onCellClick?: (cell: T) => void;
  style?: React.CSSProperties;
  className?: string;
}

const DOW = ["日", "月", "火", "水", "木", "金", "土"];

function buildCells<T extends CalendarCell>(month: string): T[] {
  const first = dayjs(month + "-01");
  const startDow = first.day();
  const daysInMonth = first.daysInMonth();
  const weeks = Math.ceil((startDow + daysInMonth) / 7);
  const total = weeks * 7;

  const cells: T[] = [];
  for (let i = 0; i < total; i++) {
    const d = first.add(i - startDow, "day");
    const inMonth = d.month() === first.month();
    cells.push({
      date: d.format("YYYY-MM-DD"),
      inMonth,
    } as T);
  }
  return cells;
}

export function CalendarCore<T extends CalendarCell = CalendarCell>({
  month,
  rowHeight = 28,
  cells: externalCells,
  renderCell,
  onCellClick,
  style,
  className,
}: CalendarCoreProps<T>): React.ReactElement {
  const cells = externalCells ?? buildCells<T>(month);

  const first = dayjs(month + "-01");
  const startDow = first.day();
  const daysInMonth = first.daysInMonth();
  const weeks = Math.ceil((startDow + daysInMonth) / 7);

  return (
    <div 
      className={className} 
      style={{ 
        display: "flex", 
        flexDirection: "column", 
        height: "100%", 
        minHeight: 0,
        ...style 
      }}
    >
      {/* Header row: W + 7 weekdays */}
      <div
        className={styles.headerRow}
        style={{ ...({ ["--row-h"]: `${rowHeight}px` } as React.CSSProperties) }}
      >
        {["W", ...DOW].map((label, idx) => (
          <div key={idx} className={styles.headerCell}>
            {label}
          </div>
        ))}
      </div>

      {/* Grid: left column week numbers + 7*weeks cells */}
      <div
        className={styles.gridWrapper}
        style={{
          ...({ ["--row-h"]: `${rowHeight}px` } as React.CSSProperties),
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
          {cells.map((cell, i) => (
            <div
              key={i}
              className={styles.cell}
              onClick={onCellClick ? () => onCellClick(cell) : undefined}
              style={{ cursor: onCellClick ? "pointer" : "default" }}
            >
              {renderCell(cell)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default CalendarCore;
