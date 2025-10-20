/**
 * HTTP Calendar Repository
 * SQL起点のカレンダーデータをAPI経由で取得
 */

import { coreApi } from "@/shared/infrastructure/http";
import type { ICalendarRepository } from "../../domain/repository";

type MonthISO = string;

interface CalendarPayload {
  month: MonthISO;
  days: Array<{
    date: string;
    status?: string;
    label?: string | null;
    color?: string | null;
  }>;
  legend?: Array<{
    key: string;
    label: string;
    color?: string | null;
  }>;
}

export class HttpCalendarRepository implements ICalendarRepository {
  async fetchMonthCalendar(month: MonthISO): Promise<CalendarPayload> {
    const url = `/core_api/calendar?month=${encodeURIComponent(month)}`;
    const data = await coreApi.get<CalendarPayload>(url);
    
    // 基本的なスキーマバリデーション（zod等を導入する場合はここで）
    if (!data.month || !Array.isArray(data.days)) {
      throw new Error("Invalid calendar payload structure");
    }

    return data;
  }
}
