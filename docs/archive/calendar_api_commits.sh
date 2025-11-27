#!/bin/bash
# Calendar API駆動化リファクタリング - 段階的コミット推奨コマンド

echo "=== Calendar API駆動化リファクタリング ==="
echo ""

# 1. shared/ui/calendar
echo "📦 [1/7] shared/ui/calendar - 汎用カレンダーモジュール"
git add app/frontend/src/shared/ui/calendar/
git commit -m "feat(shared/calendar): add CalendarPayload types and export

- Add CalendarPayload, DayDecor, LegendItem, StatusCode types for API contract
- Migrate CalendarGrid.tsx from pages/dashboard/ukeire to shared
- Add CalendarGrid.module.css
- Export public API from shared/ui/calendar/index.ts
- Reusable calendar grid component for any feature"

# 2. domain/repository
echo "🏗️ [2/7] domain/repository - ICalendarRepository追加"
git add app/frontend/src/features/dashboard/ukeire/domain/repository.ts
git commit -m "feat(ukeire/domain): add ICalendarRepository interface

- Define ICalendarRepository for SQL-driven calendar (DIP)
- Add fetchMonthCalendar(month: MonthISO) method signature
- Separate calendar data fetching from inbound forecast"

# 3. adapters
echo "🔌 [3/7] application/adapters - HTTP/Mock Repository実装"
git add app/frontend/src/features/dashboard/ukeire/application/adapters/httpCalendar.repository.ts
git add app/frontend/src/features/dashboard/ukeire/application/adapters/mockCalendar.repository.ts
git commit -m "feat(ukeire/app): add http/mock calendar repositories

- Implement HttpCalendarRepository for GET /api/calendar?month=YYYY-MM
- Implement MockCalendarRepository for local development
- Both implement ICalendarRepository interface
- Mock generates synthetic calendar with business rules (2nd Sunday closed)"

# 4. ViewModel
echo "🎮 [4/7] application/useUkeireCalendarVM - ViewModel Hook"
git add app/frontend/src/features/dashboard/ukeire/application/useUkeireCalendarVM.ts
git commit -m "feat(ukeire/app): add useUkeireCalendarVM (API-driven)

- Create ViewModel hook for calendar data fetching
- Repository injection via DI (Mock/HTTP switchable)
- Transform API response to UI-ready payload
- Handle loading/error states"

# 5. BusinessCalendar
echo "🖼️ [5/7] ui/components/BusinessCalendar - CalendarGridラッパ"
git add app/frontend/src/features/dashboard/ukeire/ui/components/BusinessCalendar.tsx
git commit -m "feat(ukeire/ui): add BusinessCalendar wrapper

- Thin wrapper around shared CalendarGrid
- Pass API data (CalendarPayload) directly to view
- Render legend from API response
- No business logic in component (display-only)"

# 6. CalendarCard integration
echo "🔄 [6/7] CalendarCard - API駆動版に置換"
git add app/frontend/src/features/dashboard/ukeire/ui/cards/CalendarCard.tsx
git add app/frontend/src/pages/dashboard/ukeire/InboundForecastDashboardPage.tsx
git commit -m "refactor(ukeire): migrate CalendarCard to API-driven

- Replace old CalendarCard implementation with API-driven version
- Integrate useUkeireCalendarVM hook
- Update InboundForecastDashboardPage props (remove calendarCardProps)
- Simplify to month prop only"

# 7. Cleanup
echo "🧹 [7/7] Cleanup - 旧ファイル削除とLint修正"
git add app/frontend/src/features/dashboard/ukeire/application/useUkeireForecastVM.ts
git add app/frontend/src/features/dashboard/ukeire/README.md
git rm -r app/frontend/src/pages/dashboard/ukeire/components/calendar/
git commit -m "chore: lint fixes and remove old calendar files

- Remove pages/dashboard/ukeire/components/calendar (migrated to shared)
- Remove calendarCardProps from useUkeireForecastVM
- Remove unused imports (countDayTypes, CalendarCardProps)
- Update README with Calendar API architecture docs
- 0 TypeScript/ESLint errors"

echo ""
echo "✅ 全7コミット完了！"
echo ""
echo "📝 Next Steps:"
echo "  1. Backend: GET /api/calendar?month=YYYY-MM エンドポイント実装"
echo "  2. CalendarCard.tsx: MockCalendarRepository → HttpCalendarRepository に切り替え"
echo "  3. Tests: Repository, ViewModel, BusinessCalendar の単体テスト追加"
