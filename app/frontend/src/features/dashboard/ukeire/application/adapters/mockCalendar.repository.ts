/**
 * Mock Calendar Repository
 * ローカル開発用のモックデータ生成
 */

import type { ICalendarRepository } from "../../domain/repository";
import type { MonthISO, CalendarPayload } from "@/shared/ui/calendar/types";
import dayjs from "dayjs";

export class MockCalendarRepository implements ICalendarRepository {
  async fetchMonthCalendar(month: MonthISO): Promise<CalendarPayload> {
    // 実際のAPIコールをシミュレート（300ms遅延）
    await new Promise((resolve) => setTimeout(resolve, 300));

    const first = dayjs(`${month}-01`);
    const daysInMonth = first.daysInMonth();
    
    const days = Array.from({ length: daysInMonth }, (_, i) => {
      const d = first.add(i, "day");
      const dow = d.day();
      const dateStr = d.format("YYYY-MM-DD");
      
      let status: "business" | "holiday" | "closed" = "business";
      let label: string | null = null;
      let color: string | null = null;

      // 日曜日は基本的に休日
      if (dow === 0) {
        status = "holiday";
        label = "日曜日";
      }

      // 第2日曜日は休業日
      const nthSunday = getNthSundayIndex(d);
      if (dow === 0 && nthSunday === 2) {
        status = "closed";
        label = "第2日曜 休業";
        color = "#cf1322";
      }

      // 土曜日は営業
      if (dow === 6) {
        status = "business";
        label = null;
      }

      // モック祝日（例：10/13がスポーツの日の場合）
      if (month === "2025-10" && i === 12) {
        status = "holiday";
        label = "スポーツの日";
      }

      return {
        date: dateStr,
        status,
        label,
        color,
      };
    });

    return {
      month,
      days,
      legend: [
        { key: "business", label: "営業日", color: "#52c41a" },
        { key: "holiday", label: "日祝", color: "#ff85c0" },
        { key: "closed", label: "休業日", color: "#cf1322" },
      ],
      version: 1,
    };
  }
}

/**
 * 月内で何番目の日曜日かを返す（1-indexed）
 */
function getNthSundayIndex(d: dayjs.Dayjs): number {
  if (d.day() !== 0) return 0;
  
  let count = 0;
  let cur = d.startOf("month");
  
  while (cur.isBefore(d) || cur.isSame(d, "day")) {
    if (cur.day() === 0) count++;
    cur = cur.add(1, "day");
  }
  
  return count;
}
