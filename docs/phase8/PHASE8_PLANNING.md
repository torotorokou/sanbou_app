# Phase 8: Entity/Model Layer Migration

## 目標
- hooks/ディレクトリをFSD構造に統合
- data/ディレクトリをFSD構造に統合
- ビジネスロジックとデータモデルの適切な配置

## 現状分析

### hooks/ディレクトリの構造 (33ファイル)
```
hooks/
├── analysis/
│   ├── customer-list-analysis/
│   │   └── useCustomerComparison.ts      # → features/analysis/model/
│   └── index.ts
├── api/
│   └── useFactoryReport.ts               # → features/report/api/ or model/
├── data/
│   ├── useCsvValidation.ts               # → features/database/model/ or features/report/model/
│   ├── useExcelGeneration.ts             # → features/report/model/
│   ├── useReportArtifact.ts              # → features/report/model/
│   ├── useZipFileGeneration.ts           # → features/report/model/
│   ├── useZipProcessing.ts               # → features/report/model/
│   ├── useZipReport.ts                   # → features/report/model/
│   └── index.ts
├── database/
│   ├── useCsvUploadArea.ts               # → features/database/model/
│   ├── useCsvUploadHandler.ts            # → features/database/model/
│   └── index.ts
├── report/
│   ├── useInteractiveBlockUnitPrice.ts   # → features/report/model/
│   ├── useReportActions.ts               # → features/report/model/
│   ├── useReportBaseBusiness.ts          # → features/report/model/
│   ├── useReportLayoutStyles.ts          # → features/report/model/
│   ├── useReportManager.ts               # → features/report/model/
│   └── index.ts
├── ui/
│   ├── useContainerSize.ts               # → shared/hooks/ui/
│   ├── useResponsive.ts                  # → shared/hooks/ui/
│   ├── useScrollTracker.ts               # → shared/hooks/ui/
│   ├── useSidebarDefault.ts              # → shared/hooks/ui/
│   ├── useSidebarResponsive.ts           # → shared/hooks/ui/
│   ├── useWindowSize.ts                  # → shared/hooks/ui/
│   └── index.ts
├── index.ts                              # Root export
└── [legacy files]                        # 7個の古いファイル (削除予定)
    ├── useCsvValidation.ts
    ├── useExcelGeneration.ts
    ├── useReportActions.ts
    ├── useReportBaseBusiness.ts
    ├── useReportLayoutStyles.ts
    ├── useReportManager.ts
    └── useResponsive.ts
```

### data/ディレクトリの構造 (1ファイル)
```
data/
└── analysis/
    └── customer-list-analysis/
        └── customer-dummy-data.ts        # → features/analysis/model/
```

## 移行戦略

### Strategy 1: Feature-specific hooks
ビジネスロジックを含むhooksは各featureのmodelディレクトリに配置

### Strategy 2: Shared hooks
汎用的なUI hooksはshared/hooks/に配置

### Strategy 3: Data models
ダミーデータや定数は各featureのmodelまたはshared/data/に配置

## 実行ステップ

### Step 1: Analysis Feature (2ファイル)
**目標**: analysis関連のhooksとdataを統合

#### 1.1 ディレクトリ作成
```bash
mkdir -p features/analysis/model
```

#### 1.2 ファイル移動
```bash
mv hooks/analysis/customer-list-analysis/useCustomerComparison.ts features/analysis/model/
mv data/analysis/customer-list-analysis/customer-dummy-data.ts features/analysis/model/
```

#### 1.3 Public API作成
`features/analysis/model/index.ts`

#### 1.4 Import参照更新
- `pages/analysis/CustomerListPage.tsx`
- `features/analysis/ui/ComparisonConditionForm.tsx` (if used)
- `features/analysis/ui/CustomerComparisonResultCard.tsx`

---

### Step 2: Report Feature (11ファイル)
**目標**: report関連のhooksを統合

#### 2.1 ディレクトリ作成
```bash
mkdir -p features/report/model
mkdir -p features/report/api
```

#### 2.2 ファイル移動
Report model hooks:
```bash
mv hooks/report/useInteractiveBlockUnitPrice.ts features/report/model/
mv hooks/report/useReportActions.ts features/report/model/
mv hooks/report/useReportBaseBusiness.ts features/report/model/
mv hooks/report/useReportLayoutStyles.ts features/report/model/
mv hooks/report/useReportManager.ts features/report/model/
```

Data hooks (report-related):
```bash
mv hooks/data/useExcelGeneration.ts features/report/model/
mv hooks/data/useReportArtifact.ts features/report/model/
mv hooks/data/useZipFileGeneration.ts features/report/model/
mv hooks/data/useZipProcessing.ts features/report/model/
mv hooks/data/useZipReport.ts features/report/model/
```

API hooks:
```bash
mv hooks/api/useFactoryReport.ts features/report/api/
```

#### 2.3 Public API作成
- `features/report/model/index.ts`
- `features/report/api/index.ts`
- `features/report/index.ts` に追加

#### 2.4 Import参照更新
- Report関連ページ (ManagePage, FactoryPage, LedgerBookPage)
- Report UIコンポーネント

---

### Step 3: Database Feature (3ファイル)
**目標**: database関連のhooksを統合

#### 3.1 ディレクトリ作成
```bash
mkdir -p features/database/model
```

#### 3.2 ファイル移動
```bash
mv hooks/database/useCsvUploadArea.ts features/database/model/
mv hooks/database/useCsvUploadHandler.ts features/database/model/
mv hooks/data/useCsvValidation.ts features/database/model/
```

#### 3.3 Public API作成
`features/database/model/index.ts`

#### 3.4 Import参照更新
- Database関連ページ (UploadPage, RecordListPage)
- Database UIコンポーネント

---

### Step 4: Shared Hooks (6ファイル)
**目標**: 汎用UI hooksをsharedに移動

#### 4.1 ディレクトリ作成
```bash
mkdir -p shared/hooks/ui
```

#### 4.2 ファイル移動
```bash
mv hooks/ui/useContainerSize.ts shared/hooks/ui/
mv hooks/ui/useResponsive.ts shared/hooks/ui/
mv hooks/ui/useScrollTracker.ts shared/hooks/ui/
mv hooks/ui/useSidebarDefault.ts shared/hooks/ui/
mv hooks/ui/useSidebarResponsive.ts shared/hooks/ui/
mv hooks/ui/useWindowSize.ts shared/hooks/ui/
```

#### 4.3 Public API作成
`shared/hooks/ui/index.ts`
`shared/hooks/index.ts`

#### 4.4 Import参照更新
- 各ページやコンポーネントから`@/hooks/ui/` → `@shared/hooks/ui`

---

### Step 5: Legacy Files Cleanup
**目標**: 古い重複ファイルの削除

#### 5.1 重複確認
```bash
# hooks/直下の古いファイル (7個)
hooks/useCsvValidation.ts           # → hooks/data/に移動済み
hooks/useExcelGeneration.ts         # → hooks/data/に移動済み
hooks/useReportActions.ts           # → hooks/report/に移動済み
hooks/useReportBaseBusiness.ts      # → hooks/report/に移動済み
hooks/useReportLayoutStyles.ts      # → hooks/report/に移動済み
hooks/useReportManager.ts           # → hooks/report/に移動済み
hooks/useResponsive.ts              # → hooks/ui/に移動済み
```

#### 5.2 使用箇所確認
```bash
grep -r "from '@/hooks/useCsv" src/
grep -r "from '@/hooks/useExcel" src/
grep -r "from '@/hooks/useReport" src/
grep -r "from '@/hooks/useResponsive" src/
```

#### 5.3 削除実行
使用されていなければ削除

---

### Step 6: Cleanup Empty Directories
**目標**: hooks/とdata/ディレクトリの削除

#### 6.1 空ディレクトリ削除
```bash
rmdir hooks/analysis/customer-list-analysis
rmdir hooks/analysis
rmdir hooks/api
rmdir hooks/data
rmdir hooks/database
rmdir hooks/report
rmdir hooks/ui
rmdir hooks
rmdir data/analysis/customer-list-analysis
rmdir data/analysis
rmdir data
```

#### 6.2 最終検証
```bash
npm run build
```

---

## 期待される成果

### Before (Phase 7完了時点)
```
src/
├── hooks/                    # 33ファイル
│   ├── analysis/ (1)
│   ├── api/ (1)
│   ├── data/ (6)
│   ├── database/ (2)
│   ├── report/ (5)
│   ├── ui/ (6)
│   └── [legacy] (7)
├── data/                     # 1ファイル
│   └── analysis/ (1)
└── features/
    └── [6 features]
```

### After (Phase 8完了時点)
```
src/
├── hooks/                    # 🗑️ 削除
├── data/                     # 🗑️ 削除
├── features/
│   ├── analysis/
│   │   ├── ui/
│   │   └── model/            # + 2ファイル (hook + data)
│   ├── report/
│   │   ├── ui/
│   │   ├── model/            # + 10ファイル (hooks)
│   │   └── api/              # + 1ファイル
│   └── database/
│       ├── ui/
│       └── model/            # + 3ファイル (hooks)
└── shared/
    └── hooks/
        └── ui/               # + 6ファイル (UI hooks)
```

## Import参照パターン

### Before
```typescript
// 様々なパターン
import { useCustomerComparison } from '@/hooks/analysis/customer-list-analysis/useCustomerComparison';
import { useReportManager } from '@/hooks/report/useReportManager';
import { useWindowSize } from '@/hooks/ui/useWindowSize';
import { allCustomerData } from '@/data/analysis/customer-list-analysis/customer-dummy-data';
```

### After
```typescript
// FSD準拠パターン
import { useCustomerComparison, allCustomerData } from '@features/analysis/model';
import { useReportManager } from '@features/report/model';
import { useWindowSize } from '@shared/hooks/ui';
```

## メトリクス予測

### ファイル移動数
- Analysis: 2ファイル (1 hook + 1 data)
- Report: 11ファイル (10 hooks + 1 api)
- Database: 3ファイル (3 hooks)
- Shared: 6ファイル (6 UI hooks)
- Legacy削除: 7ファイル
- **合計**: 22ファイル移動 + 7ファイル削除 + 2ディレクトリ削除

### 新規作成ファイル
- features/analysis/model/index.ts
- features/report/model/index.ts
- features/report/api/index.ts
- features/database/model/index.ts
- shared/hooks/ui/index.ts
- shared/hooks/index.ts
- **合計**: 6個のPublic APIs

### Import参照更新予測
- Analysis pages/components: 3-5箇所
- Report pages/components: 10-15箇所
- Database pages/components: 3-5箇所
- Shared hooks: 20-30箇所 (広く使用されている)
- **合計**: 40-55箇所

### 予想所要時間
- Step 1 (Analysis): 10分
- Step 2 (Report): 20分
- Step 3 (Database): 10分
- Step 4 (Shared): 15分
- Step 5 (Legacy): 10分
- Step 6 (Cleanup): 5分
- **合計**: 約70分 (1時間10分)

## リスク管理

### 高リスク
1. **Shared hooks**: 広く使用されている (useWindowSize, useResponsiveなど)
   - 軽減策: grep_searchで全参照を事前調査
   - 段階的に更新

2. **Report hooks**: 複数のhooksが相互依存
   - 軽減策: import順序を維持
   - 内部相対パス参照に注意

### 中リスク
3. **Legacy files**: 使用されているか不明
   - 軽減策: grep確認後に削除判断
   - 未使用確認後に削除

### 低リスク
4. **Analysis/Database**: 使用箇所が限定的
   - 影響範囲: 明確

## 成功基準
- ✅ 全hooksが適切なFSDレイヤーに配置
- ✅ ビルドエラー: 0個
- ✅ hooks/とdata/ディレクトリの削除
- ✅ Import参照が@featuresまたは@sharedに統一
- ✅ ビルド時間: 10秒以内

## Next Phase (Phase 9候補)
1. **Shared Layer拡張**: lib/, api/, config/の整理
2. **Performance最適化**: Chunk size削減
3. **Type Safety強化**: 型定義の集約
4. **Documentation**: アーキテクチャドキュメント整備

---

**Phase 8実行準備完了** ✅  
次のコマンド: Step 1 (Analysis Feature)
