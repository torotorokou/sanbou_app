/**
 * HTTP Calendar Repository
 * SQL起点のカレンダーデータをAPI経由で取得
 */

import type { ICalendarRepository } from "../../domain/repository";
import type { MonthISO, CalendarPayload } from "@/shared/ui/calendar/types";

const API_BASE = "/api";

export class HttpCalendarRepository implements ICalendarRepository {
  async fetchMonthCalendar(month: MonthISO): Promise<CalendarPayload> {
    const url = `${API_BASE}/calendar?month=${encodeURIComponent(month)}`;
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch calendar: ${response.status} ${response.statusText}`);
    }

    const data: CalendarPayload = await response.json();
    
    // 基本的なスキーマバリデーション（zod等を導入する場合はここで）
    if (!data.month || !Array.isArray(data.days)) {
      throw new Error("Invalid calendar payload structure");
    }

    return data;
  }
}
