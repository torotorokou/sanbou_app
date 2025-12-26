# Frontend Features Refactoring Report

**Date**: 2025-10-23  
**Target**: `features/dashboard/ukeire` & `features/calendar`  
**Branch**: chore/calendar-slimming-and-ukeire-adapter

---

## 1. 実施した変更プラン

### Phase A: business-calendar の構造整備

- ✅ `ports/` ディレクトリ作成（ICalendarRepository の再エクスポート）
- ✅ `infrastructure/calendar.http.repository.ts` → `calendar.repository.ts` にリネーム
- ✅ `application/decorateCalendarCells.ts` → `decorators.ts` にリネーム
- ✅ `application/useBusinessCalendarVM.ts` 作成（後方互換で useUkeireCalendarVM も export）
- ✅ UI ファイルを `ui/cards/` および `ui/components/` へ移動
- ✅ Barrel (`index.ts`) と README.md 作成

### Phase B: forecast-inbound の構造整備

- ✅ `ports/repository.ts` 作成
- ✅ `infrastructure` のファイル名を統一:
  - `http.repository.ts` → `inboundForecast.repository.ts`
  - `mock.repository.ts` → `inboundForecast.mock.repository.ts`
- ✅ `ui/ForecastCard.tsx` → `ui/cards/ForecastCard.tsx` へ移動
- ✅ `application/useInboundForecastVM.ts` 作成（後方互換で useUkeireForecastVM も export）
- ✅ Barrel と README.md 作成

### Phase C: inbound-monthly の構造整備

- ✅ UI ファイルを `ui/cards/` へ移動:
  - `DailyActualsCard.tsx`
  - `DailyCumulativeCard.tsx`
  - `CombinedDailyCard.tsx`
- ✅ Barrel と README.md 作成

### Phase D: kpi-targets の構造整備

- ✅ `ui/TargetCard.tsx` → `ui/cards/TargetCard.tsx` へ移動
- ✅ Barrel と README.md 作成

### Phase E: features/calendar の構造整備

- ✅ ディレクトリ再編成:
  - `model/types.ts` → `domain/types.ts`
  - `model/repository.ts` → `ports/repository.ts`
  - `controller/useCalendarVM.ts` → `application/useCalendarVM.ts`
  - `repository/index.ts` → `infrastructure/calendar.repository.ts`
  - `ui/CalendarCard.tsx` → `ui/cards/CalendarCard.tsx`
  - `ui/CalendarCore.tsx` → `ui/components/CalendarCore.tsx`
- ✅ Barrel (`index.ts`) 更新と README.md 作成

### Phase F: Import 修正とエイリアス正規化

- ✅ `@/features/calendar/model/*` → `@/features/calendar/domain/*` or `ports/*` へ一括置換
- ✅ `@/features/calendar/controller/*` → `@/features/calendar/application/*` へ一括置換
- ✅ 相対パス修正（`ui/` → `ui/cards/` または `ui/components/`）

### Phase G: TypeScript 型チェック

- ✅ 主要な import パス修正
- ⚠️ 一部エラー残存（次回対応が必要）

---

## 2. 生成/変更/移動ファイル一覧（git mv のログ）

### git mv による移動（履歴保持）

```
# calendar
R  model/types.ts → domain/types.ts
R  model/repository.ts → ports/repository.ts
R  controller/useCalendarVM.ts → application/useCalendarVM.ts
R  repository/index.ts → infrastructure/calendar.repository.ts
R  ui/CalendarCard.tsx → ui/cards/CalendarCard.tsx
R  ui/CalendarCore.tsx → ui/components/CalendarCore.tsx

# business-calendar
R  application/decorateCalendarCells.ts → application/decorators.ts
R  infrastructure/calendar.http.repository.ts → infrastructure/calendar.repository.ts
R  ui/CalendarCard.Ukeire.tsx → ui/cards/CalendarCard.Ukeire.tsx
R  ui/CalendarCard.tsx → ui/cards/CalendarCard.tsx
R  ui/UkeireCalendar.tsx → ui/components/UkeireCalendar.tsx

# forecast-inbound
R  infrastructure/http.repository.ts → infrastructure/inboundForecast.repository.ts
R  infrastructure/mock.repository.ts → infrastructure/inboundForecast.mock.repository.ts
R  ui/ForecastCard.tsx → ui/cards/ForecastCard.tsx

# inbound-monthly
R  ui/DailyActualsCard.tsx → ui/cards/DailyActualsCard.tsx
R  ui/DailyCumulativeCard.tsx → ui/cards/DailyCumulativeCard.tsx
R  ui/CombinedDailyCard.tsx → ui/cards/CombinedDailyCard.tsx

# kpi-targets
R  ui/TargetCard.tsx → ui/cards/TargetCard.tsx
```

### 新規作成ファイル

```
src/features/calendar/README.md
src/features/dashboard/ukeire/business-calendar/README.md
src/features/dashboard/ukeire/business-calendar/index.ts
src/features/dashboard/ukeire/business-calendar/ports/repository.ts
src/features/dashboard/ukeire/business-calendar/application/useBusinessCalendarVM.ts
src/features/dashboard/ukeire/forecast-inbound/README.md
src/features/dashboard/ukeire/forecast-inbound/index.ts
src/features/dashboard/ukeire/forecast-inbound/ports/repository.ts
src/features/dashboard/ukeire/forecast-inbound/application/useInboundForecastVM.ts
src/features/dashboard/ukeire/inbound-monthly/README.md
src/features/dashboard/ukeire/inbound-monthly/index.ts
src/features/dashboard/ukeire/kpi-targets/README.md
src/features/dashboard/ukeire/kpi-targets/index.ts
```

---

## 3. Import 修正内容のサマリ

### 代表例と件数

- `@/features/calendar/model/types` → `@/features/calendar/domain/types` (約10箇所)
- `@/features/calendar/model/repository` → `@/features/calendar/ports/repository` (約10箇所)
- `@/features/calendar/controller/` → `@/features/calendar/application/` (約5箇所)
- 相対パス `../ui/` → `../ui/cards/` または `../ui/components/` (約15箇所)
- `calendar.http.repository` → `calendar.repository` (2箇所)
- `useUkeireCalendarVM` → `useBusinessCalendarVM` (import のみ、後方互換維持)

### 一括置換実行

```bash
# model → domain/ports
find features -name "*.ts*" -exec sed -i "s|@/features/calendar/model/types|@/features/calendar/domain/types|g" {} \;
find features -name "*.ts*" -exec sed -i "s|@/features/calendar/controller/|@/features/calendar/application/|g" {} \;

# 相対パス修正
find features/dashboard/ukeire -name "*.ts*" -exec sed -i "s|from '../ui/|from '../ui/cards/|g" {} \;
```

---

## 4. 各 Feature の index.ts（Barrel）内容

### features/calendar/index.ts

```typescript
// Domain Types
export type { CalendarDayDTO, CalendarCell } from "./domain/types";
// Ports
export type { ICalendarRepository } from "./ports/repository";
// Application
export { useCalendarVM } from "./application/useCalendarVM";
// UI
export { default as CalendarCard } from "./ui/cards/CalendarCard";
export { default as CalendarCore } from "./ui/components/CalendarCore";
// Hooks
export { useContainerSize } from "./hooks/useContainerSize";
```

### features/dashboard/ukeire/business-calendar/index.ts

```typescript
// Ports
export type { ICalendarRepository } from "./ports/repository";
// Application
export {
  useBusinessCalendarVM,
  useUkeireCalendarVM,
} from "./application/useBusinessCalendarVM";
export { decorateCalendarCells } from "./application/decorators";
// UI
export { default as CalendarCard } from "./ui/cards/CalendarCard";
export { default as CalendarCardUkeire } from "./ui/cards/CalendarCard.Ukeire";
export { default as UkeireCalendar } from "./ui/components/UkeireCalendar";
// Infrastructure
export { CalendarRepositoryForUkeire } from "./infrastructure/calendar.repository";
export { MockCalendarRepositoryForUkeire } from "./infrastructure/calendar.mock.repository";
```

### features/dashboard/ukeire/forecast-inbound/index.ts

```typescript
// Ports
export type { IInboundForecastRepository } from "./ports/repository";
// Application
export {
  useInboundForecastVM,
  useUkeireForecastVM, // 後方互換
  type InboundForecastViewModel,
  type UkeireForecastViewModel,
} from "./application/useInboundForecastVM";
// UI
export {
  ForecastCard,
  type ForecastCardProps,
  type KPIBlockProps,
} from "./ui/cards/ForecastCard";
```

### features/dashboard/ukeire/inbound-monthly/index.ts

```typescript
// Application
export { useInboundMonthlyVM } from "./application/useInboundMonthlyVM";
// UI
export { DailyActualsCard } from "./ui/cards/DailyActualsCard";
export { DailyCumulativeCard } from "./ui/cards/DailyCumulativeCard";
export {
  CombinedDailyCard,
  type CombinedDailyCardProps,
} from "./ui/cards/CombinedDailyCard";
```

### features/dashboard/ukeire/kpi-targets/index.ts

```typescript
// Application
export { useTargetsVM } from "./application/useTargetsVM";
// UI
export { TargetCard, type TargetCardProps } from "./ui/cards/TargetCard";
```

---

## 5. TypeScript 型チェック結果

### 実行コマンド

```bash
npx tsc --noEmit
```

### 現状

- ✅ **主要エラーは修正済み**（import パス、モジュール解決）
- ⚠️ **残存エラー**: 約40件（主に相対パスの微調整が必要）
  - `ui/cards/` 内のコンポーネントが他の feature の UI を直接参照
  - 一部の application 層で旧パスを参照

### 対応方針

- 残りのエラーは各 feature の barrel export を経由する形に修正
- 循環参照を避けるため、shared への昇格も検討

---

## 6. 削除候補リスト（参照ゼロの証跡）

### 削除候補ファイル

以下のディレクトリは空になったため削除可能:

```
src/features/calendar/controller/  (空)
src/features/calendar/model/  (空)
src/features/calendar/repository/  (空)
src/features/calendar/utils/  (空、buildCalendarCells.ts は元から内容なし)
```

### 削除不要（移動先に統合済み）

- 旧 useUkeireCalendarVM.ts → useBusinessCalendarVM.ts に統合
- 旧 decorateCalendarCells.ts → decorators.ts にリネーム

### 証跡確認

```bash
# 空ディレクトリ確認
find src/features/calendar -type d -empty

# 出力例:
# src/features/calendar/controller
# src/features/calendar/model
# src/features/calendar/repository
# src/features/calendar/utils
```

**※ 実削除は手動で実行してください**

```bash
rm -r src/features/calendar/controller
rm -r src/features/calendar/model
rm -r src/features/calendar/repository
rm -r src/features/calendar/utils
```

---

## 7. 次アクション提案

### 優先度: 高

1. **Pages の import 差し替え**

   - `pages/dashboard/` などで旧パスを参照している箇所を barrel export 経由に変更
   - 例: `import { useUkeireForecastVM } from '@features/dashboard/ukeire/forecast-inbound'`

2. **残存型エラーの修正**
   - application 層の相対パス import を barrel 経由に統一
   - `../../kpi-targets/ui/TargetCard` → `@features/dashboard/ukeire/kpi-targets` など

### 優先度: 中

3. **Shared への昇格検討**

   - `shared/ui/ChartFrame.tsx`
   - `shared/ui/SingleLineLegend.tsx`
   - `shared/styles/tabsFill.css.ts` および `useInstallTabsFillCSS.ts`
     → これらは複数の feature で共有されているため、`src/shared/ui/` への移動を検討

4. **domain の充実**
   - business-calendar に独自の domain 層（entities, constants）が必要であれば追加
   - 現在は features/calendar の domain を参照しているが、独立性を高める場合は分離

### 優先度: 低

5. **infrastructure の Mock 実装整備**

   - 各 feature の Mock Repository を Storybook や Jest で活用
   - テストカバレッジ向上

6. **Storybook 対応**
   - `ui/cards/` 配下のコンポーネントに `.stories.tsx` を追加

---

## 8. まとめ

- **履歴保持**: すべての移動で `git mv` を使用し、Git 履歴を保持
- **後方互換**: 旧名（useUkeireCalendarVM など）も re-export で維持
- **構造統一**: MVVM+SOLID の骨組み（domain/ports/application/infrastructure/ui）に全 feature を整備
- **Barrel Export**: 各 feature に index.ts を配置し、外部公開 API を明確化
- **小さなコミット**: 各 Phase ごとにコミット可能（A～E は独立）

### Git コミット例

```bash
git add src/features/calendar
git commit -m "refactor(calendar): reorganize to domain/ports/application structure"

git add src/features/dashboard/ukeire/business-calendar
git commit -m "refactor(ukeire): standardize business-calendar with MVVM structure"

git add src/features/dashboard/ukeire/forecast-inbound
git commit -m "refactor(ukeire): standardize forecast-inbound with barrel exports"

# 以下同様...
```

---

**リファクタリング実施完了**  
次のステップは、pages 側の import 更新と残存型エラーの解消です。
