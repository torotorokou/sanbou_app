import type { CalendarDayDTO } from "@/features/calendar/domain/types";

type DecoratedCell = CalendarDayDTO & {
  inMonth: boolean;
  status?: "business" | "holiday" | "closed";
  label?: string;
  color?: string;
};

/**
 * Ukeire固有の装飾ロジック
 * 汎用カレンダーのセルに業務ロジック（ステータス・ラベル・色）を追加
 * day_typeに基づいて正確に判定
 */
export function decorateCalendarCells(
  grid: Array<Array<CalendarDayDTO & { inMonth: boolean }>>,
): DecoratedCell[][] {
  return grid.map((row) =>
    row.map((cell) => {
      let status: "business" | "holiday" | "closed";
      let label: string | undefined;
      let color: string;

      // day_type に基づいて正確に判定
      // NORMAL: 通常営業日（緑）
      // RESERVATION: 予約営業日（ピンク）
      // CLOSED: 休業日（赤）
      switch (cell.day_type) {
        case "CLOSED":
          status = "closed";
          label = "休業日";
          color = "#cf1322"; // 赤
          break;
        case "RESERVATION":
          status = "holiday";
          label = cell.is_holiday ? "祝日" : "予約営業日";
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
        ...cell,
        status,
        label,
        color,
      };
    }),
  );
}
