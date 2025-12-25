/**
 * CalendarCore Component
 * カレンダーグリッドの汎用コア実装（features/calendar に統一）
 *
 * ISO 8601標準に準拠:
 * - 週は月曜日始まり
 * - ISO週番号はバックエンドから取得したデータをそのまま表示
 */

import React from "react";
import dayjs from "dayjs";
import styles from "./calendar.module.css";
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

// ISO 8601標準: 月曜日始まり
const DOW = ["月", "火", "水", "木", "金", "土", "日"];

/**
 * 月曜日始まりのカレンダーグリッド用セル生成
 * @param month "YYYY-MM" 形式
 * @returns グリッド配置用のセル配列（月曜日始まり）
 */
function buildCells<T extends CalendarCell>(month: string): T[] {
  const first = dayjs(month + "-01");
  // dayjs.day(): 0=日曜, 1=月曜, ..., 6=土曜
  // 月曜始まりに変換: (day + 6) % 7 => 0=月曜, 1=火曜, ..., 6=日曜
  const startDow = (first.day() + 6) % 7;
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
  // 月曜始まりに変換
  const startDow = (first.day() + 6) % 7;
  const daysInMonth = first.daysInMonth();
  const weeks = Math.ceil((startDow + daysInMonth) / 7);

  /**
   * ISO週番号の取得（バックエンドデータ優先）
   *
   * 月曜始まりのグリッドなので:
   * - インデックス0 = 月曜日（ISO週の基準日）
   * - 各週の最初のセル（月曜日）のiso_weekを直接使用
   *
   * フォールバックは最小限に抑え、バックエンドデータを信頼
   */
  const weekNumbers = React.useMemo(() => {
    const numbers: string[] = [];

    for (let w = 0; w < weeks; w++) {
      const weekStartIndex = w * 7;

      // 週の最初のセル = 月曜日のiso_weekを取得
      const mondayCell = cells[weekStartIndex] as T & {
        iso_week?: number;
        inMonth?: boolean;
      };

      if (mondayCell?.iso_week) {
        // バックエンドから取得したISO週番号をそのまま表示
        numbers.push(String(mondayCell.iso_week));
      } else if (mondayCell?.inMonth === false) {
        // 月曜日が月外の場合、週内の月内セルから取得
        let weekNum: string | undefined;
        for (let d = 1; d < 7; d++) {
          const cell = cells[weekStartIndex + d] as T & {
            iso_week?: number;
            inMonth?: boolean;
          };
          if (cell?.inMonth && cell?.iso_week) {
            weekNum = String(cell.iso_week);
            break;
          }
        }
        numbers.push(weekNum ?? String(w + 1));
      } else {
        // バックエンドデータがない場合のフォールバック（通常発生しない）
        numbers.push(String(w + 1));
      }
    }
    return numbers;
  }, [cells, weeks]);

  return (
    <div
      className={className}
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
        ...style,
      }}
    >
      {/* Header row: W + 7 weekdays */}
      <div
        className={styles.headerRow}
        style={{
          ...({ ["--row-h"]: `${rowHeight}px` } as React.CSSProperties),
        }}
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
          {weekNumbers.map((weekNum, w) => (
            <div key={w} className={styles.weekCell}>
              {weekNum}
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
