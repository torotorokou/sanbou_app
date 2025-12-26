# Phase 3 実行計画

## 概要

機能別コンポーネントを `features/` 配下に移行し、Feature-Sliced Design (FSD) を完成させる

## Phase 3 サブフェーズ

### Phase 3-A: コア機能の移行 (優先度: 高)

1. **Report機能** - レポート生成・管理
2. **Database機能** - CSVアップロード・データ管理
3. **Manual機能** - マニュアル表示・検索

### Phase 3-B: AI/Chat機能の移行 (優先度: 中)

4. **Chat機能** - AI質問応答
5. **AI機能** - AI関連ユーティリティ

### Phase 3-C: その他機能とクリーンアップ (優先度: 低)

6. **Analysis機能** - データ分析
7. **Dashboard機能** - ダッシュボード
8. **古いファイルの削除**
9. **ドキュメント更新**

---

## Phase 3-A 詳細: Report機能

### 移行対象ファイル

#### Components → features/report/

```
src/components/Report/
├── ReportBase.tsx → features/report/ui/ReportBase.tsx
├── common/
│   ├── ReportHeader.tsx → features/report/ui/ReportHeader.tsx
│   ├── ReportSelector.tsx → features/report/ui/ReportSelector.tsx
│   ├── ReportStepperModal.tsx → features/report/ui/ReportStepperModal.tsx
│   ├── ReportStepIndicator.tsx → features/report/ui/ReportStepIndicator.tsx
│   ├── ReportManagePageLayout.tsx → features/report/ui/ReportManagePageLayout.tsx
│   ├── ActionsSection.tsx → features/report/ui/ActionsSection.tsx
│   ├── CsvUploadSection.tsx → features/report/ui/CsvUploadSection.tsx
│   ├── PreviewSection.tsx → features/report/ui/PreviewSection.tsx
│   └── SampleSection.tsx → features/report/ui/SampleSection.tsx
├── interactive/
│   ├── BlockUnitPriceInteractive.tsx → features/report/ui/interactive/
│   ├── BlockUnitPriceInteractiveModal.tsx → features/report/ui/interactive/
│   └── types.ts → features/report/model/interactive.types.ts
└── viewer/
    └── PDFViewer.tsx → features/report/ui/PDFViewer.tsx
```

#### Hooks → features/report/

```
src/hooks/report/
├── useReportActions.ts → features/report/hooks/useReportActions.ts
├── useReportBaseBusiness.ts → features/report/hooks/useReportBaseBusiness.ts
├── useReportLayoutStyles.ts → features/report/hooks/useReportLayoutStyles.ts
└── useReportManager.ts → features/report/hooks/useReportManager.ts

src/hooks/
├── useExcelGeneration.ts → features/report/hooks/useExcelGeneration.ts
└── data/useReportArtifact.ts → features/report/hooks/useReportArtifact.ts
```

#### Types → features/report/

```
src/types/
└── reportBase.ts → features/report/model/report.types.ts
```

#### Constants → features/report/

```
src/constants/
└── reportConfig.ts → features/report/config/reportConfig.ts
```

### 新しいディレクトリ構造

```
features/report/
├── README.md
├── index.ts (公開API)
├── model/
│   ├── report.types.ts
│   └── interactive.types.ts
├── hooks/
│   ├── useReportActions.ts
│   ├── useReportBaseBusiness.ts
│   ├── useReportLayoutStyles.ts
│   ├── useReportManager.ts
│   ├── useExcelGeneration.ts
│   └── useReportArtifact.ts
├── ui/
│   ├── ReportBase.tsx
│   ├── ReportHeader.tsx
│   ├── ReportSelector.tsx
│   ├── ReportStepperModal.tsx
│   ├── ReportStepIndicator.tsx
│   ├── ReportManagePageLayout.tsx
│   ├── ActionsSection.tsx
│   ├── CsvUploadSection.tsx
│   ├── PreviewSection.tsx
│   ├── SampleSection.tsx
│   ├── PDFViewer.tsx
│   └── interactive/
│       ├── BlockUnitPriceInteractive.tsx
│       └── BlockUnitPriceInteractiveModal.tsx
└── config/
    └── reportConfig.ts
```

---

## Phase 3-A 詳細: Database機能

### 移行対象ファイル

#### Components → features/database/

```
src/components/database/
├── CsvUploadPanel.tsx → features/database/ui/CsvUploadPanel.tsx
├── CsvPreviewCard.tsx → features/database/ui/CsvPreviewCard.tsx
└── UploadInstructions.tsx → features/database/ui/UploadInstructions.tsx

src/components/common/csv-upload/
├── CsvUploadCard.tsx → features/database/ui/CsvUploadCard.tsx
└── CsvUploadPanel.tsx → features/database/ui/CsvUploadPanel.tsx (統合)
```

#### Hooks → features/database/

```
src/hooks/database/
├── useCsvUploadHandler.ts → features/database/hooks/useCsvUploadHandler.ts
└── useCsvUploadArea.ts → features/database/hooks/useCsvUploadArea.ts
```

### 新しいディレクトリ構造

```
features/database/
├── README.md
├── index.ts
├── hooks/
│   ├── useCsvUploadHandler.ts
│   └── useCsvUploadArea.ts
└── ui/
    ├── CsvUploadPanel.tsx
    ├── CsvPreviewCard.tsx
    ├── CsvUploadCard.tsx
    └── UploadInstructions.tsx
```

---

## Phase 3-A 詳細: Manual機能

### 移行対象ファイル

#### Components → features/manual/

```
src/components/manual/
└── (manual関連コンポーネント) → features/manual/ui/
```

#### Services → features/manual/

```
src/services/api/
└── manualsApi.ts → features/manual/api/manualsApi.ts
```

#### Types → features/manual/

```
src/types/
└── manuals.ts → features/manual/model/manual.types.ts
```

### 新しいディレクトリ構造

```
features/manual/
├── README.md
├── index.ts
├── model/
│   └── manual.types.ts
├── api/
│   └── manualsApi.ts
└── ui/
    └── (manual components)
```

---

## Phase 3-B 詳細: Chat機能

### 移行対象ファイル

#### Components → features/chat/

```
src/components/chat/
├── ChatQuestionSection.tsx → features/chat/ui/ChatQuestionSection.tsx
├── ChatSendButtonSection.tsx → features/chat/ui/ChatSendButtonSection.tsx
├── ChatAnswerSection.tsx → features/chat/ui/ChatAnswerSection.tsx
├── PdfPreviewModal.tsx → features/chat/ui/PdfPreviewModal.tsx
└── QuestionPanel.tsx → features/chat/ui/QuestionPanel.tsx
```

#### Services → features/chat/

```
src/services/
└── chatService.ts → features/chat/api/chatService.ts
```

### 新しいディレクトリ構造

```
features/chat/
├── README.md
├── index.ts
├── api/
│   └── chatService.ts
└── ui/
    ├── ChatQuestionSection.tsx
    ├── ChatSendButtonSection.tsx
    ├── ChatAnswerSection.tsx
    ├── PdfPreviewModal.tsx
    └── QuestionPanel.tsx
```

---

## 実行戦略

### ステップ1: Report機能の移行

1. ディレクトリ構造作成
2. ファイルコピー
3. インポートパス更新
4. ビルド確認

### ステップ2: Database機能の移行

1. ディレクトリ構造作成
2. ファイルコピー
3. インポートパス更新
4. ビルド確認

### ステップ3: Manual機能の移行

1. ディレクトリ構造作成
2. ファイルコピー
3. インポートパス更新
4. ビルド確認

### ステップ4: Chat機能の移行

1. ディレクトリ構造作成
2. ファイルコピー
3. インポートパス更新
4. ビルド確認

### ステップ5: クリーンアップ

1. 古いファイル削除
2. 未使用コード削除
3. ドキュメント更新
4. 最終ビルド確認

---

## 成功基準

- ✅ 全機能が `features/` 配下に配置
- ✅ ビルドエラーなし
- ✅ 型エラーなし
- ✅ 各featureが独立したREADME.mdを持つ
- ✅ 公開APIが明確 (index.ts)
- ✅ 循環依存なし
- ✅ テストが通過 (存在する場合)

---

## リスク管理

### 高リスク項目

1. **循環依存**: Report ↔ Database ↔ Manual
2. **大量のインポートパス変更**: 100+ファイルに影響
3. **型定義の分離**: 共有型の取り扱い

### 軽減策

1. 段階的移行 (1機能ずつ)
2. コピー優先 (削除は最後)
3. ビルド確認を各ステップで実施
4. Gitコミットを細かく

---

**開始日**: 2025年10月3日  
**予定完了**: Phase 3-A (本日中)、Phase 3-B/C (次回)
