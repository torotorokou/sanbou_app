# shared/utils/pdf

## 役割
PDF関連のユーティリティ関数を管理します。

## 責務
- PDF生成ユーティリティ
- PDF解析ユーティリティ
- PDFダウンロード処理
- PDF変換処理

## FSDレイヤー
**shared層** - アプリケーション横断的なPDFユーティリティ

## 想定ファイル
- `pdfGenerator.ts` - PDF生成
- `pdfParser.ts` - PDF解析
- `pdfDownload.ts` - ダウンロード処理
- `pdfConverter.ts` - 変換処理

## 依存
- `pdfjs-dist` - PDF.js ライブラリ
- `jspdf` - PDF生成ライブラリ（必要に応じて）
