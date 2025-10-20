/**
 * BusinessCalendar Component
 * shared CalendarGrid に API データを渡す薄いラッパ
 * フロントは表示専用（ロジックなし）
 */

import React from "react";
import dayjs from "dayjs";
import { CalendarGrid } from "@/shared/ui/calendar";
import type { CalendarPayload } from "@/shared/ui/calendar/types";
import type { Dayjs } from "dayjs";

type Props = {
  data: CalendarPayload;
  /**
   * If provided, use fixed row height (px). If undefined, the component
   * will compute a row height to fill the available vertical space.
   */
  rowHeight?: number;
  onSelect?: (iso: string) => void;
  className?: string;
};

export const BusinessCalendar: React.FC<Props> = ({
  data,
  rowHeight,
  onSelect,
  className,
}) => {
  // APIの days を Map化（高速アクセス）
  const dayMap = React.useMemo(
    () => new Map(data.days.map((d) => [d.date, d])),
    [data.days]
  );

  // root ref to measure available height for dynamic row sizing
  const rootRef = React.useRef<HTMLDivElement | null>(null);
  const [computedRowHeight, setComputedRowHeight] = React.useState<number | undefined>(
    rowHeight
  );

  // recompute when size changes (only when rowHeight is not fixed)
  React.useEffect(() => {
    // if caller provided a fixed rowHeight, use it
    if (typeof rowHeight === "number") {
      setComputedRowHeight(rowHeight);
      return;
    }

    const el = rootRef.current;
    if (!el) return;

    const compute = () => {
      const root = rootRef.current;
      if (!root) return;

      // legend is rendered by this component above the grid; mark it with a data attr
      const legendEl = root.querySelector('[data-ukeire-legend]') as HTMLElement | null;
      const legendH = legendEl ? legendEl.offsetHeight : 0;

      // total weeks calculation (mirror CalendarGrid logic)
      const first = dayjs(data.month + "-01");
      const startDow = first.day();
      const daysInMonth = first.daysInMonth();
      const weeks = Math.ceil((startDow + daysInMonth) / 7);

      // available height inside this component for the calendar (including header row)
      const available = root.clientHeight - legendH;
      if (available <= 0) return;

      // header row + weeks rows -> (weeks + 1) rows to divide into
      const r = Math.max(20, Math.floor(available / (weeks + 1)));
      setComputedRowHeight(r);
      // store available height for explicit style to CalendarGrid
      // store on the element with a narrow type to avoid `any`
      (root as HTMLElement & { __ukeire_available?: number }).__ukeire_available = available;
    };

    // initial compute
    compute();

    const ro = new ResizeObserver(() => compute());
    ro.observe(el);
    return () => ro.disconnect();
  }, [rowHeight, data.month, data.days]);

  // helper to get last computed available height
  const getAvailable = () => {
    const root = rootRef.current as HTMLElement | null;
    return root ? (root as HTMLElement & { __ukeire_available?: number }).__ukeire_available : undefined;
  };

  return (
    <div ref={rootRef} className={className} style={{ height: "100%" }}>
      {/* Legend：3つ（business, holiday, closed）を『マーク：日数（残り）』形式で表示 */}
      {(data.legend || []).length >= 0 && (
        <div
          data-ukeire-legend
          style={{
            display: "flex",
            gap: 12,
            justifyContent: "center",
            marginBottom: 8,
            flexWrap: "wrap",
          }}
        >
          {(() => {
            const order: Array<"business" | "holiday" | "closed"> = ["business", "holiday", "closed"];
            const legendMap = new Map<string, { label: string; color?: string | null }>();
            (data.legend || []).forEach((l) => legendMap.set(l.key, { label: l.label, color: l.color }));
            const today = dayjs().format("YYYY-MM-DD");
            return order.map((key) => {
              const info = legendMap.get(key);
              const total = data.days.filter((d) => d.status === key).length;
              const remaining = data.days.filter((d) => d.status === key && d.date >= today).length;
              const color = info?.color ?? (key === "business" ? "#52c41a" : key === "holiday" ? "#ff85c0" : "#cf1322");
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

      <CalendarGrid
        className={"ukeire-calendar-root"}
        month={data.month}
        rowHeight={computedRowHeight}
        style={{ height: getAvailable() ? `${getAvailable()}px` : undefined }}
        renderCell={(d: Dayjs, inMonth: boolean) => {
          const iso = d.format("YYYY-MM-DD");
          const info = dayMap.get(iso);
          // Highlight today in yellow
          const isToday = iso === dayjs().format("YYYY-MM-DD");
          const bg = isToday ? "#fadb14" : (info?.color ?? defaultColorByStatus(info?.status));
          // Use dark text on yellow, white text on colored backgrounds
          const fg = isToday ? "#000" : (bg ? "#fff" : "#333");
          const dayNum = d.date();

          return (
            <div
              title={info?.label ?? undefined}
              onClick={() => onSelect?.(iso)}
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
                opacity: inMonth ? 1 : 0.35,
                cursor: onSelect ? "pointer" : "default",
              }}
            >
              {dayNum}
            </div>
          );
        }}
      />
    </div>
  );
};

/**
 * ステータスに応じたデフォルト色（APIが色を指定しない場合）
 */
function defaultColorByStatus(status?: string): string | undefined {
  if (status === "business") return "#52c41a";
  if (status === "holiday") return "#ff85c0";
  if (status === "closed") return "#cf1322";
  return undefined;
}

export default BusinessCalendar;
