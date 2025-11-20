# Analysis Feature

## 概要
顧客データの比較分析機能を提供します。

## ディレクトリ構造

```
analysis/
├── domain/
│   ├── types.ts                    # 型定義・ダミーデータ
│   └── services/
│       └── analysisService.ts      # 集計ロジック（useCustomerComparison）
├── ports/
│   └── repository.ts               # リポジトリI/F（将来用プレースホルダー）
├── application/
│   └── useAnalysisVM.ts            # ViewModel（domain/services を再エクスポート）
├── infrastructure/                 # （未使用）
├── ui/
│   ├── cards/
│   │   └── CustomerComparisonResultCard.tsx
│   ├── components/
│   │   ├── ComparisonConditionForm.tsx
│   │   └── AnalysisProcessingModal.tsx
│   └── index.ts
├── index.ts                        # Public API
└── README.md
```

## 主要なエクスポート

- `CustomerData`: 顧客データ型
- `useCustomerComparison`: 顧客比較Hook
- `CustomerComparisonResultCard`: 結果表示カード
- `ComparisonConditionForm`: 比較条件フォーム
- `AnalysisProcessingModal`: 処理中モーダル

## 使用例

```typescript
import { useCustomerComparison, CustomerComparisonResultCard } from '@features/analytics/customer-list';

const { targetCustomers, onlyCompare } = useCustomerComparison(
  ['2024-04', '2024-05'],
  ['2024-02', '2024-03']
);
```
