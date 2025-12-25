# features/csv/controller

## 役割

CSVアップロード機能の操作ロジックを管理します。

## 責務

- ファイルアップロード処理
- バリデーション実行
- エラーハンドリング
- 状態管理

## FSDレイヤー

**features層** - CSV機能のコントローラー

## 想定ファイル

- `useCsvUpload.ts` - アップロードフック
- `useCsvValidation.ts` - バリデーションフック
- `csvController.ts` - コントローラーロジック
