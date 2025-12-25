# CSV Tools Feature

## 概要

CSVファイルのパース、バリデーション、プレビュー機能を提供します。

## ディレクトリ構造

```
csv/
├── domain/
│   ├── config/
│   │   └── CsvDefinition.ts        # CSV定義設定
│   └── services/
│       ├── csvParserService.ts     # CSVパーサー
│       ├── csvValidatorService.ts  # バリデーター
│       └── csvPreviewService.ts    # プレビュー生成
├── ports/
│   └── repository.ts               # リポジトリI/F（将来用）
├── application/
│   └── useCsvToolsVM.ts            # ViewModel（services 再エクスポート）
├── infrastructure/                 # （未使用）
├── ui/                            # （未使用）
└── index.ts                        # Public API
```

## 主要なエクスポート

- CSV パース、バリデーション、プレビュー関数
- CSV 定義設定

## 使用例

```typescript
import { parseCsv, validateCsv, previewCsv } from "@features/csv";
```
