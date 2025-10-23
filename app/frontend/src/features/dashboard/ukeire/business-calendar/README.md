# Business Calendar Feature

営業日・祝日・休業日のステータスを装飾したカレンダー表示機能。

## 公開API

- **VM**: `useBusinessCalendarVM`, `useUkeireCalendarVM` (後方互換)
- **UI**: `CalendarCard`, `CalendarCardUkeire`, `UkeireCalendar`
- **Ports**: `ICalendarRepository`

## 依存方向

- `@features/calendar` の汎用カレンダー VM を使用
- 装飾ロジック (`decorators.ts`) で業務ステータスを追加
