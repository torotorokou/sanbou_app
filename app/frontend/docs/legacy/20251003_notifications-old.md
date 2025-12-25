# 通知機構（フロントエンド）

本ドキュメントは、実運用向けに強化した通知ストア/ユーティリティの使い方をまとめます。

## 仕様概要

- 種別: `success | error | warning | info`
- データ構造: `Notification { id, type, title, message?, createdAt, duration? }`
- デフォルト秒数は `src/config/notification.ts` に一元化
- ID 返却: すべての追加関数が string の ID を返却
- タイマー後始末: `remove`/`clearAll` 時に必ず `clearTimeout` 実行
- 重複抑止: 800ms 以内の同一内容（type+title+message）は 1 件のみ登録
- 最大件数: 5 件まで（古いものからドロップ）

## 主なファイル

- `src/config/notification.ts` … 既定秒数
- `src/stores/notificationStore.ts` … Zustand ストア（ID返却、重複抑止、max、タイマー管理、便利関数あり）
- `src/utils/notify.ts` … ヘルパ（config参照、ID返却、`notifyApiError` あり）
- `src/presentation/components/NotificationCenter.tsx` … シンプルなUI（任意）

## 使い方

```ts
import {
  notifySuccess,
  notifyApiError,
  notifyPersistent,
} from "@/utils/notify";
import { useNotificationStore } from "@/stores/notificationStore";

async function onCreateLedger(payload: any) {
  const holdId = notifyPersistent(
    "info",
    "帳簿作成中",
    "しばらくお待ちください",
  );

  try {
    await api.createLedger(payload);
    notifySuccess("帳簿作成完了", "ダウンロードを開始します");
  } catch (e) {
    notifyApiError(e, "帳簿作成に失敗しました");
  } finally {
    const { removeNotification } = useNotificationStore.getState();
    removeNotification(holdId);
  }
}
```

## UI の置き場所

アプリルート（`App.tsx` 等）に `<NotificationCenter />` を 1 度だけ配置してください。Ant Design の `Alert` を使う従来の `NotificationContainer` でも動作します。

## テスト

- `vitest` を使用
- `src/stores/notificationStore.test.ts`
  - id 返却、自動削除、タイマー後始末、重複抑止
- `src/utils/notify.test.ts`
  - 各 notify が ID を返す、永続通知、APIエラー→通知

## 注意

- 既存の `ApiError` / `ProblemDetails` 型がある場合は `src/utils/notify.ts` のローカル定義を置き換えてください。
- 直接 `addNotification` を使う場合、`duration` のデフォルトは 3000ms です。ヘルパ関数経由では `config` の値になります。
