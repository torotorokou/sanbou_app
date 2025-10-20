/**
 * UkeireCalendar Component
 * 受入量ドメイン専用のカレンダーラッパー
 * CalendarCore を使って日ごとの受入量データを表示
 */

import React from "react";
import dayjs from "dayjs";
import { CalendarCore, useContainerSize } from "@/features/calendar";
import type { CalendarCell } from "@/features/calendar/model/types";

interface UkeireCell extends CalendarCell {
  value?: number;
  status?: string;
  label?: string | null;
  color?: string | null;
}

export interface UkeireCalendarProps {
  month: string; // "YYYY-MM"
  /**
   * Key: ISO date "YYYY-MM-DD", Value: 受入量
   */
  valuesByDate?: Record<string, number>;
  /**
   * 各日のステータス・色・ラベル情報
   */
  days?: Array<{
    date: string;
    status?: string;
    label?: string | null;
    color?: string | null;
  }>;
  /**
   * 凡例データ（表示用）
   */
  legend?: Array<{
    key: string;
    label: string;
    color?: string | null;
  }>;
  rowHeight?: number;
  onSelect?: (iso: string) => void;
  className?: string;
  style?: React.CSSProperties;
}

export const UkeireCalendar: React.FC<UkeireCalendarProps> = ({
  month,
  valuesByDate,
  days = [],
  legend = [],
  rowHeight: fixedRowHeight,
  onSelect,
  className,
  style,
}) => {
  // 日データをマップ化
  const dayMap = React.useMemo(() => new Map(days.map((d) => [d.date, d])), [days]);

  // コンテナサイズ測定（動的行高さ用）
  const [rootRef, size] = useContainerSize();
  const [computedRowHeight, setComputedRowHeight] = React.useState<number | undefined>(
    fixedRowHeight
  );

  // 行高さ計算
  React.useEffect(() => {
    if (typeof fixedRowHeight === "number") {
      setComputedRowHeight(fixedRowHeight);
      return;
    }

    if (!size) return;

    // legend 要素の高さを取得
    const legendEl = rootRef.current?.querySelector(
      "[data-ukeire-legend]"
    ) as HTMLElement | null;
    const legendH = legendEl ? legendEl.offsetHeight : 0;

    // 週数計算
    const first = dayjs(month + "-01");
    const startDow = first.day();
    const daysInMonth = first.daysInMonth();
    const weeks = Math.ceil((startDow + daysInMonth) / 7);

    // 利用可能な高さから行高さを計算
    const available = size.height - legendH;
    if (available <= 0) return;

    const r = Math.max(20, Math.floor(available / (weeks + 1)));
    setComputedRowHeight(r);
  }, [fixedRowHeight, size, month, rootRef]);

  // セルデータ生成
  const cells = React.useMemo(() => {
    const first = dayjs(month + "-01");
    const startDow = first.day();
    const daysInMonth = first.daysInMonth();
    const weeks = Math.ceil((startDow + daysInMonth) / 7);
    const total = weeks * 7;

    const result: UkeireCell[] = [];
    for (let i = 0; i < total; i++) {
      const d = first.add(i - startDow, "day");
      const iso = d.format("YYYY-MM-DD");
      const inMonth = d.month() === first.month();
      const dayInfo = dayMap.get(iso);

      result.push({
        date: iso,
        inMonth,
        value: valuesByDate?.[iso],
        status: dayInfo?.status ?? undefined,
        label: dayInfo?.label ?? undefined,
        color: dayInfo?.color ?? undefined,
      });
    }
    return result;
  }, [month, valuesByDate, dayMap]);

  return (
    <div 
      ref={rootRef} 
      className={className} 
      style={{ 
        display: "flex", 
        flexDirection: "column", 
        height: "100%", 
        minHeight: 0,
        ...style 
      }}
    >
      {/* 凡例表示 */}
      {legend.length > 0 && (
        <div
          data-ukeire-legend
          style={{
            display: "flex",
            gap: 12,
            justifyContent: "center",
            marginBottom: 8,
            flexWrap: "wrap",
            flexShrink: 0,
          }}
        >
          {(() => {
            const order: Array<"business" | "holiday" | "closed"> = [
              "business",
              "holiday",
              "closed",
            ];
            const legendMap = new Map<string, { label: string; color?: string | null }>();
            legend.forEach((l) => legendMap.set(l.key, { label: l.label, color: l.color }));
            const today = dayjs().format("YYYY-MM-DD");

            return order.map((key) => {
              const info = legendMap.get(key);
              if (!info) return null;

              const total = cells.filter((c) => c.status === key && c.inMonth).length;
              const remaining = cells.filter(
                (c) => c.status === key && c.inMonth && c.date >= today
              ).length;
              const color =
                info.color ??
                (key === "business" ? "#52c41a" : key === "holiday" ? "#ff85c0" : "#cf1322");

              return (
                <span key={key} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                  <i style={{ width: 12, height: 12, borderRadius: 3, background: color }} />
                  <span style={{ color: "#595959", fontSize: 12, fontWeight: 600 }}>
                    {total}日 ({remaining})
                  </span>
                </span>
              );
            });
          })()}
        </div>
      )}

      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        <CalendarCore
          month={month}
          rowHeight={computedRowHeight ?? 28}
          cells={cells}
          renderCell={(cell: UkeireCell) => {
            const d = dayjs(cell.date);
            const isToday = cell.date === dayjs().format("YYYY-MM-DD");
            const bg = isToday
              ? "#fadb14"
              : cell.color ?? defaultColorByStatus(cell.status);
            const fg = isToday ? "#000" : bg ? "#fff" : "#333";
            const dayNum = d.date();

            return (
              <div
                title={cell.label ?? undefined}
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: 6,
                  background: bg ?? "transparent",
                  color: fg,
                  fontSize: 12,
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  opacity: cell.inMonth ? 1 : 0.35,
                }}
              >
                {dayNum}
              </div>
            );
          }}
          onCellClick={onSelect ? (cell) => onSelect(cell.date) : undefined}
        />
      </div>
    </div>
  );
};

function defaultColorByStatus(status?: string): string | undefined {
  if (status === "business") return "#52c41a";
  if (status === "holiday") return "#ff85c0";
  if (status === "closed") return "#cf1322";
  return undefined;
}

export default UkeireCalendar;
