# レスポンシブブレイクポイント統一：変更後監査

**実施日**: 2025-12-22  
**目的**: Desktop定義≥1281への変更が正しく適用されたことを検証

---

## 監査コマンド一覧（再現可能）

```bash
# 基準ディレクトリ
cd /home/koujiro/work_env/22.Work_React/sanbou_app/app/frontend/src

# 1. window.innerWidth 直接参照
rg -n "window\.innerWidth|innerWidth" --type-add 'ts:*.ts' --type-add 'tsx:*.tsx' -t ts -t tsx

# 2. 境界値ハードコード（767/768/1024/1280/1281）
rg -n "\b(767|768|1024|1280|1281)\b" --type-add 'ts:*.ts' --type-add 'tsx:*.tsx' -t ts -t tsx

# 3. responsive flags 使用総数
rg -n "\bisLaptop\b|\bisTablet\b|\bisMobile\b|\bisDesktop\b" --type-add 'ts:*.ts' --type-add 'tsx:*.tsx' -t ts -t tsx | wc -l

# 4. 1280/1281 具体的使用箇所
rg -n "\b(1280|1281)\b" --type-add 'ts:*.ts' --type-add 'tsx:*.tsx' -t ts -t tsx | head -40

# 5. テスト実行
npm test -- breakpoints.spec.ts
```

---

## 1. window.innerWidth 直接参照（変更なし）

### 結果: ✅ 変更前と同じ
- `shared/hooks/ui/useResponsive.ts:86,99,108` - useResponsiveフック内部実装（正当）
- `shared/utils/responsiveTest.ts:77` - テストユーティリティ内（正当）
- コメント内の言及（4件） - 問題なし

**判定**: ✅ operational codeにwindow.innerWidth直接参照なし

---

## 2. 境界値ハードコード（変更後）

### 2-1. 正当な定義元（更新済み）

**breakpoints.ts**:
```typescript
BP.tabletMax: bp.xl,      // 1280 ★追加
BP.desktopMin: bp.xl + 1, // 1281 ★変更：1280→1281
```

**関数定義**:
```typescript
isTabletOrHalf = (w: number) => w >= BP.tabletMin && w <= BP.tabletMax; // 768–1280 ★変更
isDesktop = (w: number) => w >= BP.desktopMin;                           // ≥1281 ★変更
```

### 2-2. テスト（更新済み）

**breakpoints.spec.ts**（全10テスト成功）:
```typescript
expect(isTabletOrHalf(ANT.xl)).toBe(true);      // 1280 ★変更: true（Tablet上限）
expect(isDesktop(ANT.xl)).toBe(false);          // 1280 ★変更: false（Tablet扱い）
expect(isDesktop(ANT.xl + 1)).toBe(true);       // 1281 ★変更: true（Desktop開始）
expect(makeFlags(1280).isTablet).toBe(true);    // ★変更
expect(makeFlags(1280).isDesktop).toBe(false);  // ★変更
expect(makeFlags(1281).isDesktop).toBe(true);   // ★追加
expect(makeFlags(1280).isNarrow).toBe(true);    // ★変更
expect(makeFlags(1281).isNarrow).toBe(false);   // ★変更
```

### 2-3. useResponsive.ts（更新済み）

```typescript
isTablet: isMd || isLg || (w === bp.xl),  // 768-1280（1280を含む）
isDesktop: w >= bp.xl + 1,                // ≥1281（1280は含まない）
isNarrow: w <= bp.xl,                     // ≤1280
```

### 2-4. useSidebar.ts（コメント更新済み）

```typescript
// - タブレット（768-1280px）: デフォルトで閉じる
// - デスクトップ（≥1281px）: デフォルトで開く
```

### 2-5. cssVars.ts（更新済み）

```typescript
--breakpoint-tablet-max: ${ANT.xl}px;     /* 768–1280 の max */
--breakpoint-auto-collapse: ${ANT.xl + 1}px; /* 1281 Desktop開始 */
```

### 2-6. コメント一括更新（10ファイル）

以下のコメントが一括置換済み：
- `pages/report/ManagePage.tsx`
- `pages/home/PortalPage.tsx`
- `pages/manual/shogun/index.tsx`
- `features/report/selector/model/useReportLayoutStyles.ts`
- `features/report/viewer/ui/ReportSampleThumbnail.tsx`
- `features/report/base/ui/ReportHeader.tsx`
- `features/chat/ui/components/ChatMessageCard.tsx`
- `features/report/upload/ui/CsvUploadSection.tsx`
- `features/report/manage/ui/ReportManagePageLayout.tsx`
- `features/dashboard/ukeire/shared/model/useResponsiveLayout.ts`
- `shared/ui/ReportStepIndicator.tsx`

置換内容：
- `"768-1279px"` → `"768-1280px"`
- `"≥1280px"` → `"≥1281px"`

### 2-7. 無関係な数値（問題なし）

- `features/analytics/customer-list/shared/model/mockData.ts:187` - weight: 1280（重量データ）
- `shared/utils/responsiveTest.ts:20` - AndroidTablet: { height: 1280 }（テストデバイス）
- `features/reservation/*/ui/*.tsx` - CSS内の範囲指定（1280-1399px）

**判定**: ✅ 境界値が正しく更新され、operational codeの直書きなし

---

## 3. Responsive Flags 使用状況（変更なし）

### flags使用総数
- **184件** の isMobile/isTablet/isLaptop/isDesktop 使用（変更前と同じ）

### 重要な変更点

#### makeFlags()の境界ロジック
```typescript
// 変更前
isTablet: isMd || isLg,    // 768-1279
isDesktop: isXl,           // ≥1280
isNarrow: w < bp.xl,       // <1280

// 変更後
isTablet: isMd || isLg || (w === bp.xl),  // 768-1280 ★1280含む
isDesktop: w >= bp.xl + 1,                // ≥1281 ★1280含まない
isNarrow: w <= bp.xl,                     // ≤1280 ★1280含む
```

**判定**: ✅ 境界ロジックが正しく更新され、1280pxがTablet扱いに変更

---

## 4. テスト結果

### breakpoints.spec.ts

```bash
✓ src/shared/constants/tests/breakpoints.spec.ts (10 tests) 3ms

Test Files  1 passed (1)
     Tests  10 passed (10)
```

### 重要なテストケース

1. **1280px境界テスト**:
   ```typescript
   expect(makeFlags(1280).isTablet).toBe(true);   // ✅ Tablet扱い
   expect(makeFlags(1280).isDesktop).toBe(false); // ✅ Desktopではない
   ```

2. **1281px境界テスト**:
   ```typescript
   expect(makeFlags(1281).isDesktop).toBe(true);  // ✅ Desktop開始
   expect(makeFlags(1281).isTablet).toBe(false);  // ✅ Tabletではない
   ```

3. **isNarrow境界テスト**:
   ```typescript
   expect(makeFlags(1280).isNarrow).toBe(true);   // ✅ Tabletまで
   expect(makeFlags(1281).isNarrow).toBe(false);  // ✅ Desktopから
   ```

**判定**: ✅ 全10テスト成功。境界値ロジックが正確に機能

---

## 5. サイドバー挙動の期待値

### 変更前
| 画面幅 | Tier | Sidebar | デフォルト状態 |
|--------|------|---------|---------------|
| ≤767 | Mobile | Drawer | 閉じる（強制） |
| 768-1279 | Tablet | 固定 | 閉じる |
| **1280** | **Desktop** | 固定 | **開く** |
| ≥1281 | Desktop | 固定 | 開く |

### 変更後
| 画面幅 | Tier | Sidebar | デフォルト状態 |
|--------|------|---------|---------------|
| ≤767 | Mobile | Drawer | 閉じる（強制） |
| 768-1280 | Tablet | 固定 | 閉じる |
| **1280** | **Tablet** | 固定 | **閉じる** ★変更 |
| ≥1281 | Desktop | 固定 | 開く |

**影響**:
- 1280px幅（多くのノートPC）でサイドバーがデフォルトで閉じるようになった
- ユーザーは手動で開くことができる（forceCollapse=false）

**判定**: ✅ 期待通りの挙動に変更

---

## 6. 例外・残存課題

### 6-1. 許容される例外

以下は正当な使用として許容：
- `shared/hooks/ui/useResponsive.ts` 内の window.innerWidth（内部実装）
- `shared/constants/breakpoints.ts` 内の数値定義（真実の源）
- `shared/constants/tests/breakpoints.spec.ts` 内のテスト境界値
- `shared/utils/responsiveTest.ts` 内のテストデバイス定義

### 6-2. 残存する境界値記述

**コメント内の言及**（多数）:
- ドキュメンテーション目的の境界値記述（例: `// 768-1280px`）
- これらは削除不要（説明として有用）

**CSS範囲指定**:
- `features/reservation/*/ui/*.tsx` 内の `@media (min-width: 1280px) and (max-width: 1399px)`
- これは1280-1399pxの特定範囲指定であり、responsive判定とは独立
- 今回の変更の影響を受けない

### 6-3. 課題なし

**isLaptop operational使用**: 0件（Phase 5で完全除去済み）  
**window.innerWidth operational使用**: 0件（Phase 3で完全除去済み）  
**境界値ハードコード operational使用**: 0件

**判定**: ✅ 残存課題なし。例外は全て正当

---

## 監査サマリー

| 項目 | 変更前 | 変更後 | 判定 |
|------|--------|--------|------|
| **Desktop定義** | ≥1280 | ≥1281 | ✅ 変更成功 |
| **Tablet上限** | 1279 | 1280 | ✅ 変更成功 |
| **1280px扱い** | Desktop | Tablet | ✅ 変更成功 |
| window.innerWidth直接参照（operational） | 0件 | 0件 | ✅ |
| 境界値ハードコード（operational） | 0件 | 0件 | ✅ |
| isLaptop operational使用 | 0件 | 0件 | ✅ |
| breakpoints.ts更新 | - | 完了 | ✅ |
| useResponsive.ts更新 | - | 完了 | ✅ |
| useSidebar.ts更新 | - | 完了 | ✅ |
| cssVars.ts更新 | - | 完了 | ✅ |
| テスト更新 | - | 完了 | ✅ |
| テスト成功 | 10/10 | 10/10 | ✅ |
| コメント更新 | - | 11ファイル | ✅ |

---

## 変更の影響範囲

### 自動的に影響を受けるコンポーネント

以下は useResponsive() / useSidebar() を使用しているため、**自動的に新定義に従う**：

1. **全ページ** - pages/* 配下のすべてのページ
2. **Sidebar使用箇所** - レイアウトコンポーネント
3. **モーダル幅決定** - features/*/ui/* 配下のモーダル
4. **レスポンシブスタイル** - flags.isTablet/isDesktop を使用する全コンポーネント

### 手動確認が必要な箇所

以下は独自のレスポンシブロジックを持つため、動作確認推奨：

1. `features/reservation/reservation-calendar/ui/ReservationMonthlyStats.tsx`
   - CSS内の `@media (min-width: 1280px) and (max-width: 1399px)`
   - 今回の変更の影響は受けないが、念のため確認

2. `features/reservation/reservation-calendar/ui/ReservationHistoryCalendar.tsx`
   - 同上

3. `features/dashboard/ukeire/shared/ui/ChartFrame.tsx`
   - 独自のresizeリスナー（グラフサイズ調整用）
   - responsive判定とは独立だが、念のため確認

---

## 次のアクション

1. ✅ **Phase 4完了**: 変更後監査完了
2. **Phase 5**: 差分レポート作成（before/after比較）
3. **Phase 6**: 品質ゲート実行（ESLint/TypeScript/Build）
4. **Phase 7**: 手動テスト（767/768/1280/1281px境界値）

---

**監査実施者**: GitHub Copilot  
**監査結果**: ✅ 全項目合格。Desktop定義≥1281への変更が正しく適用されている。  
**次フェーズ**: Phase 5 - 差分レポート作成
