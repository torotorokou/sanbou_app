# features/navi/controller

## 役割
ナビゲーション機能の操作ロジックを管理します。

## 責務
- ナビゲーション処理
- ルート探索
- イベントハンドリング
- 状態更新

## FSDレイヤー
**features層** - Navi機能のコントローラー

## 想定ファイル
- `useNavigation.ts` - ナビゲーションフック
- `useRouteSearch.ts` - ルート探索フック
- `naviController.ts` - コントローラーロジック
