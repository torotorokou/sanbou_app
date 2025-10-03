# Phase 5 Step 1: Report Pages Refactoring - Kickoff

**作成日**: 2025-10-03  
**対象**: Report関連のページコンポーネント  
**予想所要時間**: 30分

## 🎯 目的

Report機能のページコンポーネントを整理し、命名規則の統一とPublic API化を実施します。

## 📊 対象ファイル

### 現状
```
src/pages/report/
├── LedgerBookPage.tsx       # 帳簿ページ
├── ReportFactory.tsx        # 帳票工場ページ
└── ReportManagePage.tsx     # 帳票管理ページ
```

### 移行後
```
src/pages/report/
├── LedgerBookPage.tsx       # そのまま（命名OK）
├── FactoryPage.tsx          # ReportFactory → 改名
├── ManagePage.tsx           # ReportManagePage → 改名
└── index.ts                 # 新規作成（Public API）
```

## 📋 実施内容

### 1. ファイル名変更

#### ReportFactory.tsx → FactoryPage.tsx
- ファイル名: `ReportFactory.tsx` → `FactoryPage.tsx`
- コンポーネント名: `ReportFactory` → `ReportFactoryPage`（内部）
- 理由: ディレクトリ名で`report/`なので、接頭辞`Report`は冗長

#### ReportManagePage.tsx → ManagePage.tsx
- ファイル名: `ReportManagePage.tsx` → `ManagePage.tsx`
- コンポーネント名: `ReportManagePage` → `ReportManagePage`（維持）
- 理由: 同上

### 2. Public API作成

**ファイル**: `src/pages/report/index.ts`

```typescript
// Public API for Report Pages
export { default as ReportManagePage } from './ManagePage';
export { default as ReportFactoryPage } from './FactoryPage';
export { default as LedgerBookPage } from './LedgerBookPage';
```

**ポイント**:
- Export名は元の名前を維持（後方互換性）
- AppRoutesでの import がクリーンになる

### 3. ルーティング更新

**ファイル**: `src/routes/AppRoutes.tsx`

**Before**:
```typescript
const ReportFactory = lazy(() => import('../pages/report/ReportFactory'));
const ReportManagePage = lazy(() => import('../pages/report/ReportManagePage'));
const LedgerBookPage = lazy(() => import('../pages/report/LedgerBookPage'));
```

**After**:
```typescript
const { 
    ReportManagePage, 
    ReportFactoryPage, 
    LedgerBookPage 
} = await import('@/pages/report');
```

または、lazyのまま：
```typescript
const ReportManagePage = lazy(() => import('@/pages/report').then(m => ({ default: m.ReportManagePage })));
const ReportFactoryPage = lazy(() => import('@/pages/report').then(m => ({ default: m.ReportFactoryPage })));
const LedgerBookPage = lazy(() => import('@/pages/report').then(m => ({ default: m.LedgerBookPage })));
```

### 4. ルート定義更新

**Before**:
```typescript
<Route path={ROUTER_PATHS.REPORT_FACTORY} element={<ReportFactory />} />
```

**After**:
```typescript
<Route path={ROUTER_PATHS.REPORT_FACTORY} element={<ReportFactoryPage />} />
```

## 🔍 依存関係確認

### 確認事項
1. 各ページファイルの import/export
2. 他ファイルからの参照
3. テストファイルの有無

## ✅ チェックリスト

- [ ] ReportFactory.tsx → FactoryPage.tsx に改名
- [ ] ReportManagePage.tsx → ManagePage.tsx に改名
- [ ] index.ts を作成し、3ページをエクスポート
- [ ] AppRoutes.tsx の import を更新
- [ ] AppRoutes.tsx の Route要素を更新（ReportFactory → ReportFactoryPage）
- [ ] ビルド検証（`npm run build`）
- [ ] ページ表示確認（可能であれば）

## 📝 手順

### Step 1: ブランチ作成
```bash
git checkout phase4/consolidation
git checkout -b phase5/step1-report-pages
```

### Step 2: ファイル名変更
```bash
cd app/frontend/src/pages/report
git mv ReportFactory.tsx FactoryPage.tsx
git mv ReportManagePage.tsx ManagePage.tsx
```

### Step 3: index.ts作成
```bash
# index.ts を作成し、3ページをエクスポート
```

### Step 4: ルーティング更新
```bash
# AppRoutes.tsx を編集
```

### Step 5: ビルド検証
```bash
cd app/frontend
npm run build
```

### Step 6: コミット
```bash
git add -A
git commit -m "feat(phase5): refactor Report pages naming and structure

- Renamed ReportFactory.tsx → FactoryPage.tsx
- Renamed ReportManagePage.tsx → ManagePage.tsx
- Created index.ts with public exports
- Updated AppRoutes.tsx imports
- Build verification: successful

Phase 5 Step 1 Complete (3 pages, 30min)"
```

## 🎯 期待される成果

1. ✅ ページファイル名が統一されている
2. ✅ Public APIによる明示的なエクスポート
3. ✅ AppRoutesのimportがクリーン
4. ✅ ビルドエラーなし
5. ✅ 既存機能が正常動作

---

**準備完了!** 次のコマンドでPhase 5 Step 1を開始します。
