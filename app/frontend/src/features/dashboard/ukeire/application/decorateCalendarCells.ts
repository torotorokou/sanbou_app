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

      // day_type に基づいて正しく判定
      // NORMAL: 営業日（緑）
      // RESERVATION: 日曜・祝日（ピンク）
      // CLOSED: 休業日（赤）
      if (cell.day_type === "CLOSED" || cell.is_company_closed) {
        status = "closed";
        label = "休業日";
        color = "#cf1322";
      } else if (cell.day_type === "RESERVATION" || cell.is_holiday) {
        status = "holiday";
        label = cell.is_holiday ? "祝日" : "日曜";
        color = "#ff85c0";
      } else {
        status = "business";
        label = undefined;
        color = "#52c41a";
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
