# レスポンシブブレイクポイント統一：変更前監査

**実施日**: 2025-12-22  
**目的**: Desktop定義を ≥1281 に変更する前の現状を包括的に記録

---

## 監査コマンド一覧（再現可能）

```bash
# 基準ディレクトリ
cd /home/koujiro/work_env/22.Work_React/sanbou_app/app/frontend/src

# 1. window.innerWidth 直接参照
rg -n "window\.innerWidth|innerWidth" --type-add 'ts:*.ts' --type-add 'tsx:*.tsx' -t ts -t tsx

# 2. 境界値ハードコード（767/768/1024/1279/1280/1281）
rg -n "\b(767|768|1024|1279|1280|1281)\b" --type-add 'ts:*.ts' --type-add 'tsx:*.tsx' -t ts -t tsx

# 3. responsive flags 使用総数
rg -n "\bisLaptop\b|\bisTablet\b|\bisMobile\b|\bisDesktop\b" --type-add 'ts:*.ts' --type-add 'tsx:*.tsx' -t ts -t tsx | wc -l

# 4. breakpoints参照
rg -n "BREAKPOINTS|bp\.|BP\." --type-add 'ts:*.ts' --type-add 'tsx:*.tsx' -t ts -t tsx | wc -l

# 5. matchMedia / resize listener
rg -n "matchMedia|addEventListener.*resize" --type-add 'ts:*.ts' --type-add 'tsx:*.tsx' -t ts -t tsx

# 6. 幅関連キーワード
rg -n "\bmodalWidth\b|\bdrawer\b|\bsidebar\b" --type-add 'ts:*.ts' --type-add 'tsx:*.tsx' -t ts -t tsx
```

---

## 1. window.innerWidth 直接参照（8件）

### 1-1. 正当な使用（shared基盤内部のみ）
- `shared/hooks/ui/useResponsive.ts:86,99,108` - useResponsiveフック内部実装（正当）
- `shared/utils/responsiveTest.ts:77` - テストユーティリティ内（正当）

### 1-2. コメント内の言及（4件）
- `features/report/selector/model/useReportLayoutStyles.ts:8`
- `features/report/manage/ui/ReportManagePageLayout.tsx:17`
- `features/report/viewer/ui/ReportSampleThumbnail.tsx:15`
- `features/report/base/ui/ReportHeader.tsx:22`

**判定**: ✅ operational codeにwindow.innerWidth直接参照なし（コメント除く）

---

## 2. 境界値ハードコード（68件）

### 2-1. breakpoints.ts（正当な定義元）
- `shared/constants/breakpoints.ts` 内: 767, 768, 1024, 1280, 1279 の定義（正当）
- `shared/constants/tests/breakpoints.spec.ts` 内: テストでの境界値確認（正当）

### 2-2. コメント内の言及（多数）
以下のファイルで境界値がコメントに記載されている：
- `pages/report/ManagePage.tsx:35` - "768-1279px（1024-1279を含む）"
- `pages/home/PortalPage.tsx:432,561`
- `pages/manual/shogun/index.tsx:48`
- `shared/hooks/ui/useResponsive.ts:11,18,31-41,71`
- `shared/hooks/ui/useSidebar.ts:29,63`
- `shared/theme/cssVars.ts:62-64`
- その他多数のコメント

### 2-3. 運用上の境界値使用
- `plugins/vite-plugin-custom-media.ts:35-40` - CSS custom media定義（ANT定数参照、直書きなし）
- `shared/utils/responsiveTest.ts:18-20,23` - テストデバイス定義（正当）

### 2-4. 無関係な数値
- `features/analytics/customer-list/shared/model/mockData.ts:187` - weight: 1280（重量データ、無関係）
- `features/manual/ui/components/ManualResultList.tsx:62` - size / 1024（KBサイズ計算、無関係）

**判定**: 🟡 コメント内に多数の境界値言及あり。operational codeでの直書きは見当たらず。

---

## 3. Responsive Flags 使用状況（184件）

### 現在の定義（shared/hooks/ui/useResponsive.ts）
```typescript
isMobile: boolean;   // ≤767 (xs or sm)
isTablet: boolean;   // 768–1279 (md or lg) ★1024-1279を含む
isLaptop: boolean;   // 1024–1279 (lg) - 詳細判定用、運用分岐では非推奨
isDesktop: boolean;  // ≥1280 (xl)
isNarrow: boolean;   // <1280 (= isMobile || isTablet)
```

### flags使用総数
- **184件** の isMobile/isTablet/isLaptop/isDesktop 使用

### isLaptop 運用使用（Phase 5で除去済み）
以前の監査で isLaptop の operational 使用は完全除去済み。
現在は以下のみ：
- `shared/hooks/ui/useResponsive.ts:39,71` - 定義と makeFlags 内部
- `shared/constants/tests/breakpoints.spec.ts` - テストで検証

**判定**: ✅ isLaptop operational使用なし。3-tier運用が確立済み。

---

## 4. Breakpoints参照（22件）

- `BP.` / `bp.` / `BREAKPOINTS` の使用: 22箇所
- 主に shared/constants/breakpoints.ts の ANT定数参照
- 適切にモジュール化されている

**判定**: ✅ 集約管理されている

---

## 5. matchMedia / addEventListener('resize')（5件）

### 正当な使用（shared基盤内部）
- `shared/constants/breakpoints.ts:40,43` - getMediaQuery実装（正当）
- `shared/hooks/ui/useResponsive.ts:114` - resizeリスナー登録（正当）

### 個別実装
- `features/dashboard/ukeire/shared/ui/ChartFrame.tsx:33` - チャート再描画用resizeリスナー

**判定**: 🟡 ChartFrame.tsxのresizeリスナーは特殊用途（グラフサイズ調整）。responsive判定には無関係。

---

## 6. 幅関連キーワード（drawer/sidebar等、多数）

- `drawer` - 主にAnalytics機能のPivotDrawer（データ分析UI）
- `sidebar` - コメント内のみ、operational codeではuseSidebar経由

**判定**: ✅ drawer関連は分析機能UI。responsive判定とは独立。

---

## 現在の問題点（Desktop定義変更前）

### ⚠️ Critical: Desktop境界定義
現在の定義（変更が必要）：
- `isDesktop: w >= 1280` ← **1280を含んでいる**
- `isTablet: 768–1279` ← **1280を含んでいない**

**新要求**：
- `isDesktop: w >= 1281` ← **1280を除外**
- `isTablet: 768–1280` ← **1280を含む**

### 影響を受けるファイル（予測）
1. **shared/constants/breakpoints.ts**
   - `BP.desktopMin: 1280` → `1281`
   - `isDesktop(w)` 関数の境界条件
   - `isTabletOrHalf(w)` 関数の上限条件

2. **shared/hooks/ui/useResponsive.ts**
   - `makeFlags()` 内の境界値ロジック
   - JSDocコメントの境界値記述

3. **shared/constants/tests/breakpoints.spec.ts**
   - 1280pxのテストケース（現在Desktop、変更後Tablet）
   - 1281pxの新規テストケース追加

4. **shared/theme/cssVars.ts**
   - `--breakpoint-auto-collapse: 1280px` → `1281px`

5. **shared/hooks/ui/useSidebar.ts**
   - サイドバー挙動（1280px時の期待動作変更）

6. **各ページ/コンポーネントのコメント**
   - "768-1279px" → "768-1280px"
   - "≥1280" → "≥1281"

---

## 監査サマリー

| 項目 | 現状 | 判定 |
|------|------|------|
| window.innerWidth直接参照（operational） | 0件 | ✅ |
| 境界値ハードコード（operational） | 0件（コメント除く） | ✅ |
| isLaptop operational使用 | 0件 | ✅ |
| 3-tier運用確立 | isMobile/isTablet/isDesktop | ✅ |
| **Desktop定義** | **≥1280（変更必要）** | ❌ |
| breakpoints集約管理 | breakpoints.ts 1箇所 | ✅ |
| 基盤コード品質 | useResponsive/useSidebar整備済み | ✅ |

---

## 次のアクション

1. **RESPONSIVE_BREAKPOINT_POLICY.md** 更新（Desktop≥1281明記）
2. **RESPONSIVE_DESIGN_GUIDE.md** 新規作成（実装パターン集）
3. **breakpoints.ts** 修正（BP.desktopMin: 1281, tabletMax: 1280追加）
4. **useResponsive.ts** 修正（境界値ロジック調整）
5. **useSidebar.ts** 検証（1280px時の挙動確認）
6. **テスト更新**（1280px=Tablet, 1281px=Desktop）
7. **コメント一斉更新**（境界値記述統一）
8. **変更後監査**（RESPONSIVE_AUDIT_AFTER.md作成）

---

**監査実施者**: GitHub Copilot  
**次フェーズ**: Phase 1 - 方針docs更新
