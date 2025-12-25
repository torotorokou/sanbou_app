# リファクタリング Step 18 - Named Export & Barrel Export 最適化

- 実施日: 2025-11-29
- ブランチ: `refactor/frontend-step18-named-exports`
- 対象: フロントエンド全体

---

## 概要

フロントエンド規約に沿った Named Export の推進と Barrel export の最適化を実施。

---

## 実施内容

### 1. 残存 hooks/ ディレクトリの統合 ✅

**対象ファイル:**

- `features/database/dataset-import/hooks/useUploadStatusPolling.ts`

**変更内容:**

- `hooks/` → `model/` に移動
- FSD 規約完全準拠を達成

**理由:**

- FSD では hooks は `model/` に配置する方針
- ViewModel と補助 hooks を同じレイヤーに統一

---

### 2. CalendarCard を Named Export に変更 ✅

**対象ファイル:**

- `features/dashboard/ukeire/business-calendar/ui/cards/CalendarCard.tsx`
- `features/dashboard/ukeire/business-calendar/index.ts`
- `features/dashboard/ukeire/index.ts`

**変更内容:**

```typescript
// Before
export default function CalendarCard(...) { ... }
export { default as CalendarCard } from "./ui/cards/CalendarCard";

// After
export function CalendarCard(...) { ... }
export { CalendarCard } from "./ui/cards/CalendarCard";
```

**影響範囲:**

- 外部からは `UkeireCalendarCard` として再エクスポートされているため、利用側に影響なし

---

### 3. Barrel Export の最適化 ✅

#### 3-1. csv-validation feature

**対象ファイル:**

- `features/csv-validation/index.ts`

**変更内容:**

```typescript
// Before
export * from "./core/csvRowValidator";
export * from "./model/useValidateOnPick";

// After
export { validateRows } from "./core/csvRowValidator";
export { useValidateOnPick } from "./model/useValidateOnPick";
```

**理由:**

- 実装コードは明示的な export を優先（FSD ベストプラクティス）
- 型定義の `export *` は許容

#### 3-2. report feature

**対象ファイル:**

- `features/report/index.ts`

**変更内容:**

```typescript
// Before
export * from "@features/report/selector/model/useReportManager";
export * from "@features/report/actions/model/useReportActions";
export * from "@features/report/base/model/useReportBaseBusiness";
export * from "@features/report/selector/model/useReportLayoutStyles";

// After
export { useReportManager } from "@features/report/selector/model/useReportManager";
export { useReportLayoutStyles } from "@features/report/selector/model/useReportLayoutStyles";
export { useReportActions } from "@features/report/actions/model/useReportActions";
export { useReportBaseBusiness } from "@features/report/base/model/useReportBaseBusiness";
```

**理由:**

- hooks/ViewModel は明示的に export
- コード補完とツリーシェイキングの向上

---

### 4. 小規模 UI コンポーネントの Named Export 化 ✅

**対象ファイル:**

- `features/dashboard/ukeire/shared/ui/InfoTooltip.tsx`
- `features/chat/ui/components/AnswerViewer.tsx`

**変更内容:**

```typescript
// Before
export default InfoTooltip;
export default AnswerViewer;

// After
export { InfoTooltip };
export { AnswerViewer };
```

**影響ファイル:**

- `features/dashboard/ukeire/inbound-monthly/ui/cards/DailyActualsCard.tsx`
- `features/dashboard/ukeire/inbound-monthly/ui/cards/DailyCumulativeCard.tsx`
- `features/chat/ui/cards/ChatAnswerSection.tsx`

**変更内容:**

```typescript
// Before
import InfoTooltip from "@/features/...";
import AnswerViewer from "../components/AnswerViewer";

// After
import { InfoTooltip } from "@/features/...";
import { AnswerViewer } from "../components/AnswerViewer";
```

---

## 成果

### ディレクトリ構造の改善

- ✅ 残存 `hooks/` ディレクトリを完全に削除
- ✅ FSD アーキテクチャ完全準拠達成

### Export スタイルの統一

- ✅ Named Export を基本方針として確立
- ✅ Barrel export の最適化完了
  - 型定義: `export *` 許容
  - 実装コード: 明示的な export

### コード品質の向上

- ✅ TypeScript のコード補完精度向上
- ✅ ツリーシェイキングの最適化
- ✅ import 文の可読性向上

---

## 検証結果

### エラーチェック

```bash
# TypeScript エラーなし
✅ No errors found.
```

### 影響範囲

- **破壊的変更なし** - すべて内部実装の変更
- 外部公開 API は互換性を維持

---

## 今後の方針

### Named Export の継続推進

1. **新規コンポーネント**

   - すべて Named Export で作成

2. **既存コンポーネント**

   - 触る機会があれば段階的に Named Export に移行
   - pages/ 配下の default export は互換性のため許容

3. **Barrel Export**
   - 型定義: `export *` 許容
   - 実装コード: 明示的な export を優先

---

## まとめ

Step 18 では Named Export の推進と Barrel export の最適化により、フロントエンド規約への完全準拠を達成しました。

- ✅ FSD アーキテクチャ完全準拠
- ✅ Export スタイルガイドライン完全準拠
- ✅ コード品質の向上
- ✅ 破壊的変更なし

これにより、コードベースの一貫性と保守性が大幅に向上しました。
