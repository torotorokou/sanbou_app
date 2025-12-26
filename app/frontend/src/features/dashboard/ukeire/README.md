# 受入ダッシュボード (Ukeire Forecast Dashboard)

## 概要

MVC + SOLID原則に基づいて実装された受入予測ダッシュボード機能モジュール。
機能ごとにディレクトリを分割し、保守性とスケーラビリティを向上させています。

## アーキテクチャ（2025-10-23更新）

```
features/dashboard/ukeire/
├── domain/                    # ドメイン層（ビジネスロジック）
│   ├── types.ts               # DTO型定義
│   ├── valueObjects.ts        # 値オブジェクト（日付操作など）
│   ├── constants.ts           # 定数（色、フォント）
│   ├── repository.ts          # Repository抽象インターフェース
│   └── services/              # ドメインサービス（純粋関数）
│       ├── calendarService.ts
│       └── targetService.ts
│
├── shared/                    # 共通UI・スタイル（ukeire内共通）
│   ├── ui/
│   │   ├── ChartFrame.tsx
│   │   └── SingleLineLegend.tsx
│   ├── styles/
│   │   ├── tabsFill.css.ts
│   │   └── useInstallTabsFillCSS.ts
│   └── tokens.ts              # デザイントークン
│
├── business-calendar/         # カレンダー機能
│   ├── application/
│   │   ├── useUkeireCalendarVM.ts
│   │   └── decorateCalendarCells.ts
│   ├── infrastructure/
│   │   ├── calendar.http.repository.ts
│   │   └── calendar.mock.repository.ts
│   └── ui/
│       ├── CalendarCard.tsx
│       ├── CalendarCard.Ukeire.tsx
│       └── UkeireCalendar.tsx
│
├── kpi-targets/               # 目標管理機能
│   ├── application/
│   │   └── useTargetsVM.ts
│   ├── domain/services/       # (将来targetServiceを移動予定)
│   └── ui/
│       └── TargetCard.tsx
│
├── forecast-inbound/          # 予測機能
│   ├── application/
│   │   └── useUkeireForecastVM.ts
│   ├── infrastructure/
│   │   ├── http.repository.ts
│   │   └── mock.repository.ts
│   └── ui/
│       └── ForecastCard.tsx
│
├── inbound-monthly/           # 月次実績機能
│   ├── application/
│   │   └── useInboundMonthlyVM.ts
│   └── ui/
│       ├── DailyActualsCard.tsx
│       ├── DailyCumulativeCard.tsx
│       └── CombinedDailyCard.tsx
│
└── index.ts                   # Public API（後方互換性維持）
```

## 設計原則

### 1. 機能別分割

- **shared/**: ukeire内で共通のUI・スタイル
- **business-calendar/**: カレンダー表示・装飾
- **kpi-targets/**: 目標達成率表示
- **forecast-inbound/**: 予測データ表示
- **inbound-monthly/**: 月次実績データ表示

### 2. MVC パターン（各機能内）

- **Model (Domain)**: ビジネスロジック、型定義、ドメインサービス
- **View (UI)**: 純粋コンポーネント、propsのみ受け取り副作用なし
- **Controller (Application)**: ViewModel Hookでデータ取得・整形

### 3. SOLID 原則

- **単一責任**: 各層・各ファイルが明確な責務
- **依存性逆転**: Repository抽象に依存、具象は注入
- **インターフェース分離**: UI propsは最小限、必要な情報のみ
- **開放閉鎖**: 新機能追加時は新ディレクトリを追加

### 4. 純粋性

- Domain層: 副作用なし、テスト容易
- UI層: props駆動、useEffect/fetch不使用
- Application層: データ取得と整形に集約

## 使用方法

### Page での利用（barrel経由）

```tsx
import {
  useUkeireForecastVM,
  MockInboundForecastRepository,
  TargetCard,
  CombinedDailyCard,
  CalendarCardUkeire,
  ForecastCard,
} from "@/features/dashboard/ukeire";

const Page = () => {
  const repository = useMemo(() => new MockInboundForecastRepository(), []);
  const vm = useUkeireForecastVM(repository);

  if (vm.loading || !vm.payload) return <Skeleton />;

  return (
    <>
      <TargetCard {...vm.targetCardProps} />
      <CombinedDailyCard {...vm.combinedDailyProps} />
      <CalendarCardUkeire year={2025} month={10} />
      <ForecastCard {...vm.forecastCardProps} />
    </>
  );
};
```

### Repository 切り替え

```tsx
// 開発環境: Mock
import { MockInboundForecastRepository } from "@/features/dashboard/ukeire";
const repository = new MockInboundForecastRepository();

// 本番環境: HTTP
import { HttpInboundForecastRepository } from "@/features/dashboard/ukeire";
const repository = new HttpInboundForecastRepository(API_BASE_URL);
```

## リファクタリング履歴

### 2025-10-23: 機能別ディレクトリ構造への再編成

- **変更**: application/ui層を機能別に分割
- **追加ディレクトリ**: shared/, business-calendar/, kpi-targets/, forecast-inbound/, inbound-monthly/
- **削除**: 旧application/, ui/構造、未使用mockCalendar.repository.ts
- **後方互換性**: index.tsで全エクスポート維持
- **型チェック**: エラー0件
- **詳細**: `/UKEIRE_REFACTOR_REPORT.md` 参照

## 実装完了項目

- ✅ Domain層: 型定義・値オブジェクト・ドメインサービス
- ✅ Application層: Repository抽象・Mock実装・ViewModel
- ✅ UI層: 全カードコンポーネント・共通コンポーネント
- ✅ Page層: InboundForecastDashboardPage
- ✅ ルーティング: `/dashboard/ukeire`
- ✅ メニュー: サイドバーに追加
- ✅ 型安全性: TypeScriptエラー 0
- ✅ 機能別分割: 5機能ディレクトリに整理
- ✅ 後方互換性: 既存importパス維持

## Follow-up TODO

### 1. HttpRepository 実装

- [ ] `/api/inbound-forecast/:month` エンドポイント実装
- [ ] エラーハンドリング追加
- [ ] リトライロジック追加

### 2. テスト

- [ ] Domain Services 単体テスト
- [ ] ViewModel 単体テスト
- [ ] UI Components Storybook追加
- [ ] E2Eテスト

### 3. パフォーマンス最適化

- [ ] ChartDataメモ化
- [ ] React.memo適用
- [ ] useMemo/useCallback最適化

### 4. 機能拡張

- [ ] CSV/PDFエクスポート
- [ ] 週次・月次比較機能
- [ ] アラート閾値設定

## 差分サマリ

### 作成ファイル (31個)

- Domain: 7ファイル
- Application: 3ファイル
- UI: 14ファイル
- Page: 1ファイル
- Config: 3ファイル (routes.ts, sidebarMenu.tsx, AppRoutes.tsx)
- Docs: 1ファイル (README.md)

### 変更ファイル

- `app/routes/routes.ts`: DASHBOARD_UKEIRE追加
- `app/navigation/sidebarMenu.tsx`: メニュー項目追加
- `app/routes/AppRoutes.tsx`: Route追加

### 削除ファイル

- なし（既存のFactoryDashboard.tsxは保持）

## コミット提案

```bash
# 1. Domain層
git add app/frontend/src/features/dashboard/ukeire/domain/
git commit -m "feat(ukeire/domain): add DTO & pure services

- Add type definitions for MonthPayloadDTO and related types
- Add value objects for date manipulation
- Add domain services for calendar and target calculations
- Add constants for colors and fonts"

# 2. Application層
git add app/frontend/src/features/dashboard/ukeire/application/
git commit -m "feat(ukeire/app): add repository interface & mock

- Define IInboundForecastRepository interface
- Implement MockInboundForecastRepository with synthetic data
- Add HttpInboundForecastRepository scaffold"

# 3. UI層
git add app/frontend/src/features/dashboard/ukeire/ui/
git commit -m "feat(ukeire/ui): extract pure view components

- Extract TargetCard, CalendarCard, CombinedDailyCard, ForecastCard
- Add ChartFrame and SingleLineLegend components
- Add tabs fill CSS utilities
- All components are pure: props-only, no side effects"

# 4. Controller + Page
git add app/frontend/src/features/dashboard/ukeire/application/useUkeireForecastVM.ts
git add app/frontend/src/pages/dashboard/ukeire/InboundForecastDashboardPage.tsx
git commit -m "feat(ukeire/app): add view-model hook & compose page

- Implement useUkeireForecastVM hook for data fetching and transformation
- Create InboundForecastDashboardPage as thin presentation layer
- Connect ViewModel to pure UI components"

# 5. 配線
git add app/frontend/src/features/dashboard/ukeire/index.ts
git commit -m "refactor(ukeire): wire modules & add public API

- Create public API entry point (index.ts)
- Export all domain, application, and UI modules
- Keep legacy FactoryDashboard.tsx for backward compatibility"

# 6. ルーティング
git add app/frontend/src/app/routes/routes.ts
git add app/frontend/src/app/navigation/sidebarMenu.tsx
git add app/frontend/src/app/routes/AppRoutes.tsx
git add app/frontend/src/features/dashboard/ukeire/README.md
git commit -m "chore: wire ukeire dashboard routing and menu

- Add /dashboard/ukeire route
- Add sidebar menu item
- Update AppRoutes with InboundForecastDashboardPage
- Add comprehensive README with architecture docs
- All TypeScript errors resolved (0 errors)"
```

## 備考

- 既存の `FactoryDashboard.tsx` は削除（新実装に完全移行済み）
- 新実装は `/dashboard/ukeire` で独立して動作
- すべてのコンポーネントは型安全で、ESLint/TypeScriptエラーなし
- Repositoryパターンにより、Mock/HTTP実装を簡単に切り替え可能

---

## 🆕 Calendar API駆動化 (2025年リファクタリング)

### 概要

営業カレンダーを **SQL起点（API駆動）** に完全リファクタリング。フロントは表示専用、業務ルールはサーバ側で管理。

### アーキテクチャ変更

#### Before（旧実装）

```
pages/dashboard/ukeire/components/calendar/CalendarGrid.tsx
└─ フロント側でカレンダーロジック（第2日曜判定など）を実装
```

#### After（新実装）

```
shared/ui/calendar/               # 汎用化されたカレンダーUI
├── CalendarGrid.tsx              # 汎用グリッド表示器
├── types.ts                      # API契約型（CalendarPayload, DayDecor）
└── index.ts

features/dashboard/ukeire/
├── domain/repository.ts          # ICalendarRepository追加
├── application/
│   ├── adapters/
│   │   ├── httpCalendar.repository.ts    # /api/calendar呼び出し
│   │   └── mockCalendar.repository.ts    # ローカル開発用モック
│   └── useUkeireCalendarVM.ts            # Calendar用ViewModel
└── ui/
    ├── cards/CalendarCard.tsx            # API駆動版（簡素化）
    └── components/BusinessCalendar.tsx   # shared CalendarGridラッパ
```

### API仕様

**Endpoint**: `GET /api/calendar?month=YYYY-MM`

**Response**:

```json
{
  "month": "2025-10",
  "days": [
    {
      "date": "2025-10-01",
      "status": "business",
      "label": null,
      "color": null
    },
    {
      "date": "2025-10-12",
      "status": "holiday",
      "label": "スポーツの日",
      "color": null
    },
    {
      "date": "2025-10-13",
      "status": "closed",
      "label": "第2日曜 休業",
      "color": "#cf1322"
    }
  ],
  "legend": [
    { "key": "business", "label": "営業日", "color": "#52c41a" },
    { "key": "holiday", "label": "日祝", "color": "#ff85c0" },
    { "key": "closed", "label": "休業日", "color": "#cf1322" }
  ],
  "version": 1
}
```

### SOLID適用

| 原則    | 実装                                                 |
| ------- | ---------------------------------------------------- |
| **SRP** | 表示（shared）・取得（repository）・組立（VM）が分離 |
| **OCP** | ステータス拡張はAPI側で対応、フロント変更最小        |
| **LSP** | Mock ↔ HTTP を透過的に切り替え可能                  |
| **ISP** | Viewは最小限のpropsのみ受け取る                      |
| **DIP** | ViewModelは抽象Repository IFに依存                   |

### メリット

1. **業務ルール集中管理**: 祝日・休業日の判定はSQLで一元管理
2. **フロント簡素化**: 表示専用、ロジックなし（100+ lines削減）
3. **保守性向上**: カレンダールール変更時にフロント変更不要
4. **テスタビリティ**: Mock/HTTP切り替えで単体テスト容易

### 切り替え方法

開発中（Mock使用）:

```typescript
const repository = useMemo(() => new MockCalendarRepository(), []);
```

本番（HTTP使用）:

```typescript
const repository = useMemo(() => new HttpCalendarRepository(), []);
```

### 追加コミット

```bash
# 7. Calendar API駆動化
git add app/frontend/src/shared/ui/calendar/
git commit -m "feat(shared/calendar): add CalendarPayload types and export

- Add CalendarPayload, DayDecor, LegendItem types for API contract
- Migrate CalendarGrid to shared (reusable component)
- Export public API from shared/ui/calendar"

git add app/frontend/src/features/dashboard/ukeire/domain/repository.ts
git commit -m "feat(ukeire/domain): add ICalendarRepository interface

- Define ICalendarRepository for DIP
- Add fetchMonthCalendar method signature"

git add app/frontend/src/features/dashboard/ukeire/application/adapters/*Calendar.repository.ts
git commit -m "feat(ukeire/app): add http/mock calendar repositories

- Implement HttpCalendarRepository for /api/calendar
- Implement MockCalendarRepository for local development
- Both implement ICalendarRepository interface"

git add app/frontend/src/features/dashboard/ukeire/application/useUkeireCalendarVM.ts
git commit -m "feat(ukeire/app): add useUkeireCalendarVM (API-driven)

- Create ViewModel hook for calendar data
- Repository injection (DIP)
- Transform API response to UI props"

git add app/frontend/src/features/dashboard/ukeire/ui/components/BusinessCalendar.tsx
git commit -m "feat(ukeire/ui): add BusinessCalendar wrapper

- Thin wrapper around shared CalendarGrid
- Pass API data directly to view
- No business logic in component"

git add app/frontend/src/features/dashboard/ukeire/ui/cards/CalendarCard.tsx
git add app/frontend/src/pages/dashboard/ukeire/InboundForecastDashboardPage.tsx
git commit -m "refactor(ukeire): migrate CalendarCard to API-driven

- Replace old CalendarCard with API-driven version
- Integrate useUkeireCalendarVM
- Update InboundForecastDashboardPage
- Remove old calendar component directory"

git add app/frontend/src/features/dashboard/ukeire/
git commit -m "chore: lint fixes and remove old calendar files

- Remove pages/dashboard/ukeire/components/calendar
- Fix TypeScript errors in useUkeireForecastVM
- Remove unused imports (countDayTypes)
- 0 TypeScript/ESLint errors"
```
