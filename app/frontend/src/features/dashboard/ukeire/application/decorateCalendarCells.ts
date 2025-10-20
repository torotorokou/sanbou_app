import type { CalendarDayDTO } from "@/features/calendar/model/types";

type DecoratedCell = CalendarDayDTO & {
  inMonth: boolean;
  status?: "business" | "holiday" | "closed";
  label?: string;
  color?: string;
};

/**
 * Ukeire固有の装飾ロジック
 * 汎用カレンダーのセルに業務ロジック（ステータス・ラベル・色）を追加
 */
export function decorateCalendarCells(
  grid: Array<Array<CalendarDayDTO & { inMonth: boolean }>>
): DecoratedCell[][] {
  return grid.map((row) =>
    row.map((cell) => {
      let status: "business" | "holiday" | "closed" = "business";
      let label: string | undefined;
      let color: string | undefined;

      if (cell.isHoliday) {
        status = "holiday";
        label = "祝日";
        color = "#ff85c0";
      }

      return {
        ...cell,
        status,
        label,
        color,
      };
    })
  );
}
