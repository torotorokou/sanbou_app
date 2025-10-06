# features/manuals/controller

## 役割
マニュアル機能の操作ロジックを管理します。

## 責務
- マニュアル取得処理
- 検索処理
- ページネーション
- 状態管理

## FSDレイヤー
**features層** - マニュアル機能のコントローラー

## 想定ファイル
- `useManualsData.ts` - データ取得フック
- `useManualsSearch.ts` - 検索フック
- `manualsController.ts` - コントローラーロジック
