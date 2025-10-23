# Calendar Feature

汎用カレンダー表示機能。営業日・祝日などの情報を表示する基盤。

## 公開API

- **Domain**: `CalendarDayDTO`
- **Ports**: `ICalendarRepository`
- **VM**: `useCalendarVM`
- **UI**: `CalendarCard`, `CalendarCore`
- **Utils**: `buildCalendarCells`

## 依存方向

- 純粋な汎用カレンダー機能
- 他の feature から参照される基盤
