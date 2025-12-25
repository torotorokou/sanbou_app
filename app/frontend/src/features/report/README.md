# Report Feature

## 概要

レポート生成・管理機能を提供するフィーチャー層

## 責務

- レポートの生成(PDF/Excel)
- CSVデータのアップロードと検証
- レポートプレビュー
- インタラクティブなデータ選択 (ブロック単価等)
- レポート関連のUI/UXコンポーネント

## 構造

### 現在の配置

```
src/
├── components/Report/          # UI Components
│   ├── ReportBase.tsx         # メインコンポーネント
│   ├── common/                # 共通UIコンポーネント
│   │   ├── ReportHeader.tsx
│   │   ├── ReportSelector.tsx
│   │   ├── ActionsSection.tsx
│   │   └── ...
│   ├── interactive/           # インタラクティブフロー
│   └── viewer/                # PDF/Excelビューアー
├── hooks/report/              # Business Logic
│   ├── useReportManager.ts   # メイン管理ロジック
│   ├── useReportActions.ts   # アクション処理
│   └── ...
├── constants/reportConfig.ts  # 設定・型定義
└── pages/report/              # ページコンポーネント
    └── ReportFactory.tsx
```

## 主要コンポーネント

### UI Components

#### ReportBase

- **役割**: レポート生成の中核コンポーネント
- **パス**: `@/components/Report/ReportBase.tsx`
- **Props**:
  - `reportKey`: レポート種別
  - `onGenerateReport`: 生成ハンドラー
  - `onDownloadExcel`: Excelダウンロードハンドラー
  - `onPrintPdf`: PDF印刷ハンドラー

#### ReportHeader

- **役割**: レポート選択とステップ表示
- **パス**: `@/components/Report/common/ReportHeader.tsx`

#### ReportManagePageLayout

- **役割**: レポートページの共通レイアウト
- **パス**: `@/components/Report/common/ReportManagePageLayout.tsx`

### Business Logic Hooks

#### useReportManager

- **役割**: レポート生成フロー全体の状態管理
- **パス**: `@/hooks/report/useReportManager.ts`
- **戻り値**:
  - `selectedReport`: 現在選択中のレポート
  - `changeReport`: レポート切り替え
  - `getReportBaseProps`: ReportBase用props生成

#### useReportActions

- **役割**: レポート操作(生成/ダウンロード/印刷)
- **パス**: `@/hooks/report/useReportActions.ts`

#### useExcelGeneration

- **役割**: Excelファイル生成とダウンロード
- **パス**: `@/hooks/useExcelGeneration.ts`

## 設定 (reportConfig.ts)

### ReportKey (レポート種別)

```typescript
type ReportKey =
  | "factory_report" // 工場レポート
  | "factory_report2" // 工場レポート2
  | "block_unit_price" // ブロック単価
  | "product_cost" // 製品原価計算書
  | "sales_tree" // 売上ツリー
  | "customer_list"; // 顧客名簿
```

### APIエンドポイント

- **getApiEndpoint**: レポート種別からAPIパスを取得
- **例**: `/ledger_api/block-unit-price/generate`

### モーダルステップ設定

- **modalStepsMap**: 各レポートの生成ステップ定義

## 使用例

### 基本的な使い方

```typescript
import { useReportManager } from '@/hooks/report';
import ReportBase from '@/components/Report/ReportBase';
import ReportHeader from '@/components/Report/common/ReportHeader';

function MyReportPage() {
  const reportManager = useReportManager('factory_report2');
  const reportBaseProps = reportManager.getReportBaseProps();

  return (
    <>
      <ReportHeader
        reportKey={reportManager.selectedReport}
        onChangeReportKey={reportManager.changeReport}
        currentStep={reportManager.currentStep}
      />
      <ReportBase {...reportBaseProps} />
    </>
  );
}
```

### レポート生成フロー

1. **CSV アップロード** → ユーザーが必要なCSVをアップロード
2. **データ検証** → CSVの妥当性をチェック
3. **レポート生成** → バックエンドAPIを呼び出し
4. **プレビュー** → 生成されたPDFをプレビュー
5. **ダウンロード/印刷** → Excel/PDFでダウンロード、または印刷

## 依存関係

### 内部依存

- `@shared/infrastructure/http` - API通信
- `@shared/hooks/ui` - UIフック (useWindowSize等)
- `@features/notification` - 通知表示

### 外部依存

- `antd` - UIコンポーネント
- `react-router-dom` - ルーティング

## API仕様

### レポート生成API

```
POST /ledger_api/{report_type}/generate
Content-Type: multipart/form-data

Body:
  - files: CSVファイル群
  - report_key: レポート種別
  - (その他パラメータ)

Response: ReportArtifactResponse
{
  "report_key": string,
  "report_date": string,
  "pdf_url": string,
  "excel_url": string
}
```

## インタラクティブレポート

### Block Unit Price (ブロック単価)

- **特徴**: 3ステップのインタラクティブフロー
- **フロー**:
  1. 初期データ送信
  2. ユーザーが運搬方法を選択
  3. 確認・最終化

### コンポーネント

- `BlockUnitPriceInteractive.tsx` - レガシー実装
- `BlockUnitPriceInteractiveModal.tsx` - モーダルベース実装 (推奨)

## 今後の改善点

### Phase 4 (将来)

- [ ] `features/report/` 配下への完全移行
- [ ] model/controller/view 分離
- [ ] API層の統一 (`features/report/api/`)
- [ ] 型定義の集約 (`features/report/model/`)

### 技術的負債

- [ ] ReportBase の責務過多 → 分割
- [ ] インタラクティブフロー の抽象化
- [ ] CSV検証ロジックの共通化
- [ ] エラーハンドリングの統一

## 関連ドキュメント

- `PHASE2_COMPLETION_REPORT.md` - Phase 2完了レポート
- `PHASE3_SIMPLIFIED.md` - Phase 3簡略版計画
- `src/constants/reportConfig.ts` - 設定詳細

---

**最終更新**: 2025年10月3日  
**メンテナ**: Sanbou App Team
