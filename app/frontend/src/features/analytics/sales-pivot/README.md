# Sales Pivot Feature (FSD構成)

売上ピボット分析機能 - Feature-Sliced Design + MVVM + Repository パターン

## 📁 ディレクトリ構造

```
sales-pivot/
├── detail-chart/      # 詳細チャート機能
│   └── ui/
├── export-menu/       # CSV出力メニュー
│   └── ui/
├── filters/           # フィルタ機能
│   ├── model/
│   └── ui/
├── header/            # ヘッダー機能
│   ├── model/
│   └── ui/
├── kpi/               # KPI集計機能
│   ├── model/
│   └── ui/
├── pivot-drawer/      # Pivotドロワー機能
│   ├── model/
│   └── ui/
├── summary-table/     # サマリテーブル機能
│   ├── model/
│   └── ui/
├── shared/            # 共通層
│   ├── api/           # Repository
│   ├── model/         # 型定義・ユーティリティ
│   └── ui/            # 共通UIコンポーネント
├── model/             # スライス横断型ユーティリティ（旧統合ViewModelは削除済み）
└── index.ts           # 公開API
```

## 🎯 アーキテクチャ原則

### FSD (Feature-Sliced Design)
- **機能単位でスライス化**: 8つの独立した機能スライス
- **レイヤー分離**: ui/ (View), model/ (ViewModel), shared/ (共通)
- **明確な依存関係**: 下位層から上位層への一方向依存

### MVVM (Hooks = ViewModel)
- **View**: React コンポーネント (*.tsx)
- **ViewModel**: Custom Hooks (use*.ts)
- **Model**: Repository + 型定義

### Repository パターン
- **Interface**: `SalesPivotRepository`
- **Implementation**: `MockSalesPivotRepository`
- **Singleton**: `salesPivotRepository`

## 📦 スライス一覧

| スライス | 責務 | ViewModel | UI |
|---------|------|-----------|-----|
| **header** | タイトル・CSV出力 | useHeaderViewModel | SalesPivotHeader |
| **filters** | フィルタ管理 | useFiltersViewModel, useMasters | FilterPanel |
| **kpi** | KPI集計 | useKpiViewModel | KpiCards |
| **summary-table** | サマリテーブル | useSummaryViewModel | SummaryTable, ExpandedRow, MetricChart |
| **pivot-drawer** | Pivotドロワー | usePivotViewModel | PivotDrawer, PivotTable |
| **export-menu** | CSV出力メニュー | - | ExportMenu |
| **detail-chart** | 詳細チャート | - | TopNBarChart, DailySeriesChart |
| **shared** | 共通層 | - | SortBadge, MiniBarChart, EmptyStateCard, styles |

## 🔧 使用方法

### 統合ページ（廃止）
旧 `SalesPivotBoardPage` およびその統合ViewModelは分割完了に伴い削除済み（2025-11-20）。
今後は必要なスライスの ViewModel Hook と UI コンポーネントを個別にインポートしてください。

### スライス単位で使用
```tsx
import { 
  SalesPivotHeader,
  useHeaderViewModel,
  FilterPanel,
  useFiltersViewModel,
  KpiCards,
  useKpiViewModel,
  // ...
} from '@/features/analytics/sales-pivot';
```

### 共通UIコンポーネント
```tsx
import { 
  SortBadge, 
  MiniBarChart, 
  EmptyStateCard,
  salesPivotStyles 
} from '@/features/analytics/sales-pivot';
```

## 📊 統計

- **合計ディレクトリ**: 26
- **合計ファイル**: 32
- **スライス数**: 8
- **共通UIコンポーネント**: 4 (SortBadge, MiniBarChart, EmptyStateCard, styles)

## 🎨 レイアウト

ページレイアウトコンポーネントは `pages/analytics/SalesTreePage.tsx` に統合:

```tsx
import { SalesPivotLayout } from '@/pages/analytics/SalesTreePage';
```

## 🚀 リファクタリング履歴

- **2025-11-20**: 8スライス化完了
  - 共通UI層作成 (SortBadge, MiniBarChart, EmptyStateCard, styles)
  - export-menu, detail-chart スライス追加
  - レイアウトをpages層に統合（layoutsディレクトリ削除）
  - 旧統合ページ `SalesPivotBoardPage` 削除（レガシー互換終了）
