# Phase 7: Dashboard & Remaining Components Migration

## 目標
- ManagementDashboardを`features/dashboard/`に移行
- csv-uploadを`features/database/ui/`に移行  
- customer-list-analysisを`features/analysis/ui/`に移行
- 残りのcomponentsディレクトリを整理

## 現状の構造分析

### componentsディレクトリの内容
```
components/
├── ManagementDashboard/        # → features/dashboard/
│   ├── index.ts
│   ├── CustomerAnalysis.tsx
│   ├── RevenuePanel.tsx
│   ├── SummaryPanel.tsx
│   ├── BlockCountPanel.tsx
│   └── ProcessVolumePanel.tsx
├── analysis/
│   └── customer-list-analysis/ # → features/analysis/ui/
│       ├── AnalysisProcessingModal.tsx
│       ├── ComparisonConditionForm.tsx
│       └── CustomerComparisonResultCard.tsx
├── common/
│   └── csv-upload/             # → features/database/ui/
│       ├── CsvUploadPanel.tsx
│       ├── CsvUploadCard.tsx
│       └── types.ts
├── rag/
│   └── References.tsx          # → features/chat/ui/ または shared/ui/
├── TokenPreview/
│   └── TokenPreview.tsx        # → pages/utils/ または shared/ui/
└── debug/
    └── ResponsiveDebugInfo.tsx # → shared/ui/ (開発用)
```

**合計**: 15ファイル

## 実行ステップ

### Step 1: Dashboard Feature Migration (5ファイル)
**目標**: ManagementDashboardを完全なFeatureとして移行

#### 1.1 ディレクトリ構造作成
```
features/dashboard/
├── ui/
│   ├── CustomerAnalysis.tsx
│   ├── RevenuePanel.tsx
│   ├── SummaryPanel.tsx
│   ├── BlockCountPanel.tsx
│   ├── ProcessVolumePanel.tsx
│   └── index.ts (Public API)
└── index.ts (Feature Public API)
```

#### 1.2 ファイル移動
```bash
mv components/ManagementDashboard/*.tsx features/dashboard/ui/
```

#### 1.3 Import参照更新
- ManagementDashboardページから: `@/components/ManagementDashboard` → `@features/dashboard`
- 内部相互参照の修正

#### 1.4 Public API作成
- `features/dashboard/ui/index.ts`: 各パネルコンポーネントをexport
- `features/dashboard/index.ts`: UIコンポーネントを再export

#### 1.5 検証
```bash
npm run build
```

### Step 2: CSV Upload Migration (3ファイル)
**目標**: csv-uploadコンポーネントをdatabase featureに統合

#### 2.1 ファイル移動
```bash
mv components/common/csv-upload/* features/database/ui/csv-upload/
```

#### 2.2 Import参照更新
- Database関連ページから: `@/components/common/csv-upload` → `@features/database`
- features/database/ui/index.tsに追加

#### 2.3 検証
```bash
npm run build
```

### Step 3: Customer Analysis Migration (3ファイル)
**目標**: customer-list-analysisをanalysis featureに移行

#### 3.1 features/analysis/ディレクトリ作成
```
features/analysis/
├── ui/
│   ├── ComparisonConditionForm.tsx
│   ├── CustomerComparisonResultCard.tsx
│   ├── AnalysisProcessingModal.tsx
│   └── index.ts
└── index.ts
```

#### 3.2 ファイル移動
```bash
mkdir -p features/analysis/ui
mv components/analysis/customer-list-analysis/* features/analysis/ui/
```

#### 3.3 Import参照更新
- CustomerListPageから: `@/components/analysis/customer-list-analysis` → `@features/analysis`

#### 3.4 Public API作成
- `features/analysis/ui/index.ts`
- `features/analysis/index.ts`

#### 3.5 検証
```bash
npm run build
```

### Step 4: Remaining Components Migration (4ファイル)

#### 4.1 rag/References.tsx
**分析**: RAG機能に関連 → Chat featureに統合
```bash
mv components/rag/References.tsx features/chat/ui/
```

#### 4.2 TokenPreview/TokenPreview.tsx
**分析**: ユーティリティページ用コンポーネント
- Option A: `pages/utils/components/` (ページ固有コンポーネント)
- Option B: `shared/ui/` (汎用コンポーネント)
→ ページ固有なのでOption A

#### 4.3 debug/ResponsiveDebugInfo.tsx
**分析**: 開発用デバッグコンポーネント
```bash
mv components/debug/ResponsiveDebugInfo.tsx shared/ui/debug/
```

### Step 5: Cleanup
#### 5.1 空ディレクトリの削除
```bash
rm -rf components/ManagementDashboard
rm -rf components/common/csv-upload
rm -rf components/analysis/customer-list-analysis
rm -rf components/rag
rm -rf components/TokenPreview
rm -rf components/debug
```

#### 5.2 componentsディレクトリの状態確認
```bash
find components -type f
```

#### 5.3 最終ビルド検証
```bash
npm run build
```

## 期待される成果

### Before (Phase 6完了時点)
```
src/
├── components/              # 15ファイル残存
│   ├── ManagementDashboard/ (5)
│   ├── analysis/ (3)
│   ├── common/ (3)
│   ├── rag/ (1)
│   ├── TokenPreview/ (1)
│   └── debug/ (1)
├── features/                # 4 features
│   ├── report/
│   ├── database/
│   ├── manual/
│   └── chat/
└── shared/ui/               # 8コンポーネント
```

### After (Phase 7完了時点)
```
src/
├── components/              # 空または最小化
├── features/                # 6 features
│   ├── report/
│   ├── database/            # + csv-upload
│   ├── manual/
│   ├── chat/                # + References
│   ├── dashboard/           # NEW! (5コンポーネント)
│   └── analysis/            # NEW! (3コンポーネント)
├── pages/
│   └── utils/
│       └── components/      # TokenPreview
└── shared/ui/               # + ResponsiveDebugInfo
```

## メトリクス予測

### ファイル移動数
- Dashboard: 5ファイル
- CSV Upload: 3ファイル
- Analysis: 3ファイル
- Others: 3ファイル
- **合計**: 14ファイル

### 新規作成ファイル
- features/dashboard/ui/index.ts
- features/dashboard/index.ts
- features/analysis/ui/index.ts
- features/analysis/index.ts
- **合計**: 4ファイル (Public APIs)

### Import参照更新予測
- ManagementDashboardページ: 1箇所
- Database関連ページ: 2-3箇所
- CustomerListPage: 3箇所
- Chat関連: 1箇所
- **合計**: 7-8箇所

### 予想所要時間
- Step 1 (Dashboard): 15分
- Step 2 (CSV Upload): 10分
- Step 3 (Analysis): 10分
- Step 4 (Others): 10分
- Step 5 (Cleanup): 5分
- **合計**: 約50分

## リスク管理

### 高リスク
1. **Dashboard移行**: 5個のパネルコンポーネントの相互依存
   - 軽減策: index.tsから段階的にimport

2. **Import参照の漏れ**: 複数箇所での使用
   - 軽減策: grep_searchで全参照を事前調査

### 中リスク
3. **Type定義の移行**: csv-upload/types.ts
   - 軽減策: Public APIで明示的にexport

### 低リスク
4. **Debug componentの移動**: 開発専用
   - 影響範囲: 限定的

## 成功基準
- ✅ 全ファイルが適切なFSDレイヤーに配置
- ✅ ビルドエラー: 0個
- ✅ componentsディレクトリが空または最小化
- ✅ 全Import参照が@featuresまたは@sharedに統一
- ✅ ビルド時間: 10秒以内

## Next Phase (Phase 8)
Phase 7完了後の候補:
1. **Entity Layer**: データモデルとビジネスロジックの抽出
2. **Shared Layer拡張**: lib/, api/, config/の整理
3. **Performance最適化**: Chunk size削減 (現在649KB)
4. **Type Safety強化**: 型定義の集約と最適化

---

**Phase 7実行準備完了** ✅  
次のコマンド: Step 1開始
