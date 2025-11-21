# Customer List Analysis Feature

## 概要
顧客離脱分析機能。今期と前期の期間を指定し、離脱顧客（前期には存在したが今期には存在しない顧客）を特定します。

## アーキテクチャ
FSD (Feature-Sliced Design) + MVVM + Repository パターンに準拠

## ディレクトリ構造

```
customer-list/
├── domain/
│   └── types.ts                             # 共通型定義（CustomerData）
├── model/
│   ├── mockData.ts                          # モックデータ（月別顧客データ）
│   └── useCustomerChurnViewModel.ts         # メインViewModel
├── period-selector/                         # サブフィーチャー: 期間選択
│   ├── domain/types.ts
│   ├── model/
│   │   ├── usePeriodSelector.ts
│   │   └── utils.ts
│   └── ui/PeriodSelectorForm.tsx
├── customer-aggregation/                    # サブフィーチャー: 顧客集約
│   └── model/aggregation.ts
├── customer-comparison/                     # サブフィーチャー: 顧客比較
│   ├── domain/types.ts
│   ├── model/
│   │   ├── comparison.ts
│   │   └── useCustomerComparison.ts
│   └── ui/CustomerComparisonResultCard.tsx
├── data-export/                             # サブフィーチャー: データ出力
│   └── model/
│       ├── csv.ts
│       └── useExcelDownload.ts
├── shared/                                  # 共通UIコンポーネント
│   └── ui/AnalysisProcessingModal.tsx
├── index.ts                                 # Public API
└── README.md
```

## 主要なエクスポート

### 型
- `CustomerData`: 顧客データ型
- `CustomerComparisonResult`: 顧客比較結果型
- `PeriodRange`, `ComparisonPeriods`: 期間選択関連型

### ViewModel / Hooks
- `useCustomerChurnViewModel`: メインViewModel（4つのサブフィーチャーを統合）
- `usePeriodSelector`: 期間選択Hook
- `useCustomerComparison`: 顧客比較Hook
- `useExcelDownload`: Excel出力Hook

### UI Components
- `PeriodSelectorForm`: 期間選択フォーム
- `CustomerComparisonResultCard`: 結果表示テーブル
- `AnalysisProcessingModal`: 処理中モーダル

### 純粋関数
- `aggregateCustomers`: 顧客集約ロジック
- `getExclusiveCustomers`: 排他的顧客抽出
- `buildCustomerCsv`: CSV生成

## 使用例

```typescript
import { useCustomerChurnViewModel } from '@features/analytics/customer-list';

const vm = useCustomerChurnViewModel(apiPostBlob);

// 期間選択
<PeriodSelectorForm {...vm} />

// 分析実行
<Button onClick={vm.handleAnalyze}>分析する</Button>

// 結果表示
<CustomerComparisonResultCard 
  title="離脱顧客"
  data={vm.lostCustomers}
/>

// CSV出力
<Button onClick={vm.handleDownloadLostCustomersCsv}>
  CSVダウンロード
</Button>
```
