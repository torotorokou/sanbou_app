# Report Feature アーキテクチャ

## 📁 ディレクトリ構成

```
features/report/
├── api/                    # API通信
│   ├── index.ts
│   └── useFactoryReport.ts
│
├── config/                 # 設定ファイル
│   └── CsvDefinition.ts   # CSV定義
│
├── model/                  # ビジネスロジック層
│   ├── index.ts           # Model層の公開API
│   │
│   ├── config/            # レポート設定
│   │   ├── index.ts
│   │   ├── pages/         # ページ別設定
│   │   │   ├── factoryPageConfig.ts
│   │   │   ├── ledgerPageConfig.ts
│   │   │   └── managePageConfig.ts
│   │   └── shared/        # 共通設定
│   │       ├── common.ts
│   │       └── types.ts
│   │
│   ├── report.types.ts           # レポート型定義
│   ├── report-api.types.ts       # API型定義
│   │
│   ├── useReportManager.ts       # レポート管理
│   ├── useReportBaseBusiness.ts  # レポートビジネスロジック
│   ├── useReportActions.ts       # アクション管理
│   ├── useReportLayoutStyles.ts  # レイアウトスタイル
│   ├── useReportArtifact.ts      # レポート成果物管理
│   ├── useExcelGeneration.ts     # Excel生成
│   │
│   ├── useZipFileGeneration.ts   # 🚫 非推奨
│   └── useZipProcessing.ts       # 🚫 非推奨
│
└── ui/                     # UIコンポーネント層
    ├── ReportBase.tsx     # ベースコンポーネント
    │
    ├── common/            # 共通UIコンポーネント
    │   ├── ActionsSection.tsx
    │   ├── ActionsSection_new.tsx
    │   ├── CsvUploadSection.tsx
    │   ├── InteractiveReportModal.tsx
    │   ├── PreviewSection.tsx
    │   ├── ReportHeader.tsx
    │   ├── ReportManagePageLayout.tsx
    │   ├── ReportSelector.tsx
    │   ├── ReportStepIndicator.tsx
    │   ├── ReportStepperModal.tsx
    │   ├── SampleSection.tsx
    │   ├── downloadExcel.ts
    │   └── types.ts
    │
    ├── interactive/       # インタラクティブレポート
    │   ├── BlockUnitPriceInteractive.tsx
    │   ├── BlockUnitPriceInteractiveModal.tsx
    │   ├── BlockUnitPriceInteractiveModal.css
    │   ├── transportNormalization.ts
    │   └── types.ts
    │
    └── viewer/            # ビューア
        ├── PDFViewer.tsx
        └── ReportSampleThumbnail.tsx
```

## 🎯 FSDアーキテクチャ適合状況

### ✅ 適合項目
1. **api/** - API通信専用レイヤー
2. **model/** - ビジネスロジック・フック統合
3. **ui/** - UIコンポーネント専用
4. **config/** - 設定ファイル分離

### ✅ 改善完了項目
1. ❌ `hooks/` ディレクトリを削除（FSD違反）
2. ✅ すべてのフックを`model/`に統合
3. ✅ インポートパスを統一（`../model/*`）
4. ✅ 重複ファイルを削除

## 📦 公開API

### features/report/index.ts
```typescript
// Model (ビジネスロジック)
export { useReportManager } from './model/useReportManager';
export { useReportBaseBusiness } from './model/useReportBaseBusiness';
export { useReportActions } from './model/useReportActions';
export { useReportLayoutStyles } from './model/useReportLayoutStyles';

// Config (設定)
export { reportConfigMap, modalStepsMap, ... } from './model/config';

// Types (型定義)
export type { ReportKey, PageGroupKey, ... } from './model/config';
export type { ReportBaseProps, CsvFiles, ... } from './model/report.types';
```

## 🔄 使用例

### 他の機能からのインポート
```typescript
// ✅ 正しい使用法
import { 
  useReportManager,
  reportConfigMap,
  type ReportKey 
} from '@features/report';

// ❌ 内部パスへの直接アクセスは避ける
import { useReportManager } from '@features/report/model/useReportManager';
```

## 🚫 非推奨機能

以下のフックは非推奨です。代わりに`useReportArtifact`を使用してください：
- `useZipFileGeneration`
- `useZipProcessing`

## 📝 変更履歴

### 2025-10-06: ディレクトリ再構成
- `hooks/` ディレクトリを削除し、`model/`に統合
- 重複ファイルを解消
- FSDアーキテクチャに完全適合
- 循環依存: 0件
- ESLintエラー: 0件
- ビルド時間: 8.90秒
