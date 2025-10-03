# Phase 5: Pages Layer Refactoring - Planning Document

**作成日**: 2025-10-03  
**目的**: FSDアーキテクチャに基づいてPages層を整理し、アプリケーション全体の構造を完成させる

## 📊 現状分析

### Pages層の構造

```
src/pages/
├── analysis/
│   └── CustomerListAnalysis.tsx
├── dashboard/
│   ├── CustomerListDashboard.tsx
│   ├── FactoryDashboard.tsx
│   ├── ManagementDashboard.tsx
│   ├── PricingDashboard.tsx
│   └── SalesTreePage.tsx
├── database/
│   ├── RecordListPage.tsx
│   └── UploadDatabasePage.tsx
├── home/
│   ├── NewsPage.tsx
│   └── PortalPage.tsx
├── manual/
│   ├── GlobalManualSearch.tsx
│   ├── ManualList.tsx
│   ├── ManualModal.tsx
│   ├── ManualPage.tsx
│   ├── ShogunManualItemPage.tsx
│   ├── ShogunManualList.tsx
│   └── types.ts
├── navi/
│   └── SolvestNavi.tsx
├── report/
│   ├── LedgerBookPage.tsx
│   ├── ReportFactory.tsx
│   └── ReportManagePage.tsx
├── utils/
│   ├── TestPage.tsx
│   └── TokenPreviewPage.tsx
└── README.md
```

**総ページ数**: 23ページ

### ページ分類

#### 1. Feature Pages (機能ページ) - 14ページ
特定のフィーチャーに紐づくページ:
- **Report**: ReportManagePage, ReportFactory, LedgerBookPage (3)
- **Database**: UploadDatabasePage, RecordListPage (2)
- **Manual**: GlobalManualSearch, ShogunManualList, ManualPage, ManualModal (4)
- **Chat**: SolvestNavi (1)
- **Analysis**: CustomerListAnalysis (1)
- **Dashboard**: ManagementDashboard, FactoryDashboard, PricingDashboard, CustomerListDashboard, SalesTreePage (5) - 未移行
  ※Dashboardは複数フィーチャーを組み合わせるため特殊

#### 2. App Pages (アプリケーションページ) - 2ページ
アプリ全体に関わるページ:
- **Home**: PortalPage, NewsPage (2)

#### 3. Utility Pages (ユーティリティページ) - 2ページ
開発/デバッグ用:
- **Utils**: TestPage, TokenPreviewPage (2)

## 🎯 FSDにおけるPages層の役割

### Pages層の定義
FSDでは、Pages層は以下の責務を持つ:

1. **ルーティングのエントリーポイント**
   - URLとコンポーネントのマッピング
   - ページレベルのレイアウト組み立て

2. **フィーチャーの組み合わせ**
   - 複数のフィーチャーを組み合わせて1つのページを構成
   - フィーチャー間の調整・連携

3. **ページ固有のロジック**
   - ページレベルのstate管理
   - ページ遷移制御

### Pages層が含むべきでないもの
- ❌ ビジネスロジック → Features層
- ❌ UI Components → Features層のui/またはShared層
- ❌ API呼び出し → Features層のapi/
- ❌ 型定義 → Features層のmodel/

## 📋 Phase 5の戦略

### Option A: Pages層をFSD標準構造に移行 ⭐ 推奨

現在の`src/pages/`を`src/pages/`のまま維持しつつ、内部構造を整理:

```
src/pages/
├── report-manage/         # 各ページを独立ディレクトリ化
│   ├── ui/
│   │   └── ReportManagePage.tsx
│   └── index.ts
├── report-factory/
│   ├── ui/
│   │   └── ReportFactoryPage.tsx
│   └── index.ts
├── upload-database/
│   ├── ui/
│   │   └── UploadDatabasePage.tsx
│   └── index.ts
└── ...
```

**メリット**:
- FSD標準に準拠
- ページごとの独立性が高い
- 将来的な拡張が容易

**デメリット**:
- ディレクトリ構造が冗長になる可能性
- 単純なページには過剰

### Option B: 機能グループごとに整理（現状維持＋改善） ⭐⭐ 最推奨

現在の`pages/{feature}/`構造を維持し、内部を整理:

```
src/pages/
├── report/
│   ├── ManagePage.tsx          # ReportManagePageから改名
│   ├── FactoryPage.tsx         # ReportFactoryから改名
│   ├── LedgerBookPage.tsx      # そのまま
│   └── index.ts                # 3ページを公開
├── database/
│   ├── UploadPage.tsx          # UploadDatabasePageから改名
│   ├── RecordListPage.tsx      # そのまま
│   └── index.ts
├── manual/
│   ├── SearchPage.tsx          # GlobalManualSearchから改名
│   ├── ListPage.tsx            # ShogunManualListから改名
│   ├── DetailPage.tsx          # ManualPageから改名
│   ├── DetailModal.tsx         # ManualModalから改名
│   └── index.ts
└── ...
```

**メリット**:
- 現状構造を活かせる
- 関連ページがグループ化される
- シンプルで理解しやすい
- ルーティング定義がスッキリ

**デメリット**:
- FSD標準からは若干逸脱
- 大規模ページには対応しにくい可能性

### Option C: Flat構造（すべてフラット配置）

```
src/pages/
├── ReportManagePage.tsx
├── ReportFactoryPage.tsx
├── UploadDatabasePage.tsx
└── ...
```

**メリット**:
- 最もシンプル
- ファイル検索が容易

**デメリット**:
- スケールしない
- 関連性が不明確

## 🎯 推奨アプローチ: Option B + 段階的移行

### Phase 5-1: ページファイル名の統一
各ページファイルの命名規則を統一:

```
Before:
- pages/report/ReportManagePage.tsx
- pages/database/UploadDatabasePage.tsx
- pages/manual/GlobalManualSearch.tsx

After:
- pages/report/ManagePage.tsx
- pages/database/UploadPage.tsx
- pages/manual/SearchPage.tsx
```

**理由**: グループ名で既に機能が分かるため、冗長な接頭辞を削除

### Phase 5-2: index.tsによる公開API化
各機能グループにindex.tsを追加:

```typescript
// pages/report/index.ts
export { default as ManagePage } from './ManagePage';
export { default as FactoryPage } from './FactoryPage';
export { default as LedgerBookPage } from './LedgerBookPage';
```

ルーティング定義を更新:
```typescript
// routes/AppRoutes.tsx
import { ManagePage, FactoryPage, LedgerBookPage } from '@/pages/report';
```

### Phase 5-3: ページ内部の依存関係整理
各ページコンポーネントから:
- ビジネスロジックを抽出 → Features層へ
- 汎用UIコンポーネントを抽出 → Shared層へ
- ページ固有のUIは維持

### Phase 5-4: Dashboard機能の特別対応
Dashboard系ページは複数フィーチャーを組み合わせるため、別途検討:

```
src/pages/dashboard/
├── ManagementPage.tsx      # 経営ダッシュボード
├── FactoryPage.tsx         # 工場ダッシュボード
├── PricingPage.tsx         # 原価ダッシュボード
├── CustomerListPage.tsx    # 顧客一覧ダッシュボード
├── SalesTreePage.tsx       # 売上ツリー
└── index.ts
```

または、Dashboard自体を1つのFeatureとして扱う選択肢もあり。

## 📊 実施スコープ

### Phase 5で実施する内容

#### Step 1: Report Pages (3 pages) - 30分
- ReportManagePage → ManagePage
- ReportFactory → FactoryPage
- LedgerBookPage → そのまま
- index.ts作成
- AppRoutes更新

#### Step 2: Database Pages (2 pages) - 20分
- UploadDatabasePage → UploadPage
- RecordListPage → そのまま
- index.ts作成
- AppRoutes更新

#### Step 3: Manual Pages (4 pages) - 25分
- GlobalManualSearch → SearchPage
- ShogunManualList → ListPage
- ManualPage → DetailPage
- ManualModal → DetailModal
- types.ts → model/manual-page.types.ts
- index.ts作成
- AppRoutes更新

#### Step 4: Chat Pages (1 page) - 10分
- SolvestNavi → ChatPage
- index.ts作成
- AppRoutes更新

#### Step 5: Analysis Pages (1 page) - 10分
- CustomerListAnalysis → CustomerListPage
- index.ts作成
- AppRoutes更新

#### Step 6: Home Pages (2 pages) - 15分
- PortalPage → そのまま
- NewsPage → そのまま
- index.ts作成
- AppRoutes更新

#### Step 7: Utils Pages (2 pages) - 10分
- TestPage → そのまま
- TokenPreviewPage → そのまま
- index.ts作成
- AppRoutes更新

**合計所要時間**: 約2時間

### Phase 5で実施しない内容

- ❌ Dashboard Pagesの大規模リファクタリング（Phase 6へ延期）
- ❌ ページ内部のビジネスロジック抽出（必要に応じて個別対応）
- ❌ レイアウトコンポーネントの移行（別フェーズで検討）

## 🎯 成功基準

1. ✅ すべてのページファイルが適切に命名されている
2. ✅ 各機能グループにindex.tsが存在する
3. ✅ AppRoutesがクリーンなimport文を使用している
4. ✅ ビルドが成功する（エラー0）
5. ✅ すべてのページが正常に表示される

## 📝 次のアクション

1. Phase 5-1を開始: Report Pages の命名統一
2. 各ステップごとにビルド検証
3. 完了後、Phase 5 Completion Report作成

---

**Phase 5 開始準備完了!**  
「次に進んで」でPhase 5-1（Report Pages）を開始します。
