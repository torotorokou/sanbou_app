# features/csv/model

## 役割
CSVアップロード機能のビジネスロジックとデータモデルを管理します。

## 責務
- CSV型定義
- バリデーションロジック
- データ変換ロジック
- ビジネスルール

## FSDレイヤー
**features層** - CSV機能のモデル

## 想定ファイル
- `csv.types.ts` - CSV型定義
- `validation.ts` - バリデーションロジック
- `parser.ts` - パーサーロジック
