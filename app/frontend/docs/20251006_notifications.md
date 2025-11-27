# 通知システム完全ガイド# 通知機構（フロントエンド）



## 目次本ドキュメントは、実運用向けに強化した通知ストア/ユーティリティの使い方をまとめます。



1. [概要](#概要)## 仕様概要

2. [契約（OpenAPI）](#契約openapi)- 種別: `success | error | warning | info`

3. [アーキテクチャ](#アーキテクチャ)- データ構造: `Notification { id, type, title, message?, createdAt, duration? }`

4. [使い方](#使い方)- デフォルト秒数は `src/config/notification.ts` に一元化

5. [エラーコードカタログ](#エラーコードカタログ)- ID 返却: すべての追加関数が string の ID を返却

6. [traceId の扱い](#traceid-の扱い)- タイマー後始末: `remove`/`clearAll` 時に必ず `clearTimeout` 実行

7. [SSE通知](#sse通知)- 重複抑止: 800ms 以内の同一内容（type+title+message）は 1 件のみ登録

8. [ベストプラクティス](#ベストプラクティス)- 最大件数: 5 件まで（古いものからドロップ）

9. [トラブルシューティング](#トラブルシューティング)

## 主なファイル

---- `src/config/notification.ts` … 既定秒数

- `src/stores/notificationStore.ts` … Zustand ストア（ID返却、重複抑止、max、タイマー管理、便利関数あり）

## 概要- `src/utils/notify.ts` … ヘルパ（config参照、ID返却、`notifyApiError` あり）

- `src/presentation/components/NotificationCenter.tsx` … シンプルなUI（任意）

このシステムは、フロントエンド・バックエンド間で統一された通知・エラーハンドリングを提供します。

## 使い方

### 主な機能```ts

import { notifySuccess, notifyApiError, notifyPersistent } from '@/utils/notify';

- ✅ **ProblemDetails（RFC 7807）準拠のエラー形式**import { useNotificationStore } from '@/stores/notificationStore';

- ✅ **エラーコードの一元管理**

- ✅ **通知の自動表示（severity別）**async function onCreateLedger(payload: any) {

- ✅ **トレースID（traceId）による追跡**  const holdId = notifyPersistent('info', '帳簿作成中', 'しばらくお待ちください');

- ✅ **SSE（Server-Sent Events）によるリアルタイム通知**

- ✅ **ジョブの失敗を通知に自動変換**  try {

    await api.createLedger(payload);

---    notifySuccess('帳簿作成完了', 'ダウンロードを開始します');

  } catch (e) {

## 契約（OpenAPI）    notifyApiError(e, '帳簿作成に失敗しました');

  } finally {

すべての契約は `/contracts/notifications.openapi.yaml` で定義されています。    const { removeNotification } = useNotificationStore.getState();

    removeNotification(holdId);

### ProblemDetails  }

}

RFC 7807準拠のエラー情報```



```yaml## UI の置き場所

ProblemDetails:アプリルート（`App.tsx` 等）に `<NotificationCenter />` を 1 度だけ配置してください。Ant Design の `Alert` を使う従来の `NotificationContainer` でも動作します。

  type: object

  required: [status, code, userMessage]## テスト

  properties:- `vitest` を使用

    status:      { type: integer }          # HTTPステータスコード- `src/stores/notificationStore.test.ts`

    code:        { type: string }           # アプリケーション固有のエラーコード  - id 返却、自動削除、タイマー後始末、重複抑止

    userMessage: { type: string }           # ユーザー向けメッセージ- `src/utils/notify.test.ts`

    title:       { type: string }           # エラータイトル  - 各 notify が ID を返す、永続通知、APIエラー→通知

    traceId:     { type: string }           # トレースID

```## 注意

- 既存の `ApiError` / `ProblemDetails` 型がある場合は `src/utils/notify.ts` のローカル定義を置き換えてください。

### NotificationEvent- 直接 `addNotification` を使う場合、`duration` のデフォルトは 3000ms です。ヘルパ関数経由では `config` の値になります。


通知イベント

```yaml
NotificationEvent:
  type: object
  required: [id, severity, title]
  properties:
    id:        { type: string, format: uuid }
    severity:  { type: string, enum: [success, info, warning, error] }
    title:     { type: string }
    message:   { type: string }
    duration:  { type: integer, nullable: true }  # ms / null=自動削除なし
    feature:   { type: string }
    resultUrl: { type: string }
    jobId:     { type: string }
    traceId:   { type: string }
    createdAt: { type: string, format: date-time }
```

---

## アーキテクチャ

### データフロー

```
┌─────────────────────────────────────────────────────────┐
│                      フロントエンド                      │
├─────────────────────────────────────────────────────────┤
│  エラー発生                                             │
│    ↓                                                    │
│  ApiError (httpClient)                                  │
│    ↓                                                    │
│  notifyApiError() ← codeCatalog で code→severity変換   │
│    ↓                                                    │
│  notify{Success|Error|Warning|Info}()                   │
│    ↓                                                    │
│  NotificationCenter に表示                              │
└─────────────────────────────────────────────────────────┘
         ↑
         │ HTTP/SSE
         │
┌─────────────────────────────────────────────────────────┐
│                     バックエンド                         │
├─────────────────────────────────────────────────────────┤
│  DomainError / Exception                                │
│    ↓                                                    │
│  handle_domain_error / handle_unexpected                │
│    ↓                                                    │
│  ProblemDetails (JSON)                                  │
│    ↓                                                    │
│  HTTP Response / SSE Event                              │
└─────────────────────────────────────────────────────────┘
```

---

## 使い方

### フロントエンド

#### API呼び出しとエラーハンドリング

```typescript
import { apiPost } from '@shared/infrastructure/http';
import { notifyApiError, notifySuccess } from '@features/notification';

try {
  const result = await apiPost('/api/upload', formData);
  notifySuccess('アップロード完了', 'ファイルのアップロードが完了しました');
} catch (error) {
  // 自動的に code→severity変換、通知表示
  notifyApiError(error, 'アップロードに失敗しました');
}
```

#### ジョブのポーリング

```typescript
import { pollJob } from '@shared/infrastructure/job';

try {
  const result = await pollJob(
    jobId,
    (progress, message) => {
      console.log(`進捗: ${progress}% - ${message}`);
    }
  );
  // 成功時は自動的に成功通知が表示される
} catch (error) {
  // 失敗時は自動的にエラー通知が表示される（job.error から）
}
```

#### SSE通知の開始

```typescript
// App.tsx など
import { startSSE, stopSSE } from '@features/notification';
import { useEffect } from 'react';

function App() {
  useEffect(() => {
    // SSE接続開始
    startSSE();
    
    return () => {
      // クリーンアップ
      stopSSE();
    };
  }, []);

  return <div>...</div>;
}
```

---

## エラーコードカタログ

エラーコードと通知設定の対応は `/app/frontend/src/features/notification/config.ts` で管理されています。

### 運用ルール

1. **バックエンドで新しいエラーコードを追加したら、フロントエンドの `codeCatalog` にも追加する**
2. **severity は以下の基準で設定する**
   - `success`: 処理成功
   - `info`: 情報提供
   - `warning`: 警告（ユーザーの入力ミスなど、リトライ可能）
   - `error`: エラー（システムエラー、認証エラーなど）

3. **title はユーザーに表示されるため、分かりやすい日本語にする**
4. **userMessage は `ProblemDetails.userMessage` から取得するため、ここでは title のみ定義**

---

## traceId の扱い

### 目的

- **エラーの追跡**: ユーザーからの問い合わせ時に、traceId があればログから詳細を検索できる
- **分散トレーシング**: マイクロサービス間でリクエストを追跡

### UI方針（推奨）

エラー通知に「詳細を表示」ボタンを追加し、クリックするとモーダルで以下を表示:

```
エラー詳細

トレースID: 550e8400-e29b-41d4-a716-446655440000
[コピー]

エラーコード: VALIDATION_ERROR
ステータス: 422
メッセージ: 入力値が不正です

問い合わせ時にトレースIDをお伝えください。
```

---

## SSE通知

### クライアント側（TypeScript）

```typescript
// 自動的に接続・再接続される
import { startSSE, stopSSE } from '@features/notification';

// アプリ起動時
startSSE();

// アプリ終了時
stopSSE();
```

---

## ベストプラクティス

### 1. 通知の duration

```typescript
// 成功: 短め（4秒）
notifySuccess('保存しました', undefined, 4000);

// 警告: 中程度（5秒）
notifyWarning('入力を確認してください', message, 5000);

// エラー: 長め（6秒）
notifyError('エラーが発生しました', message, 6000);

// 重要な情報: 自動削除しない
notifyPersistent('error', '致命的なエラー', message);
```

---

## トラブルシューティング

### 通知が表示されない

1. **NotificationCenter がレンダリングされているか確認**
2. **console.log で notifyApiError が呼ばれているか確認**
3. **codeCatalog にエラーコードが登録されているか確認**

### SSEが接続されない

1. **ブラウザのDevToolsでネットワークタブを確認**
2. **CORS設定を確認**
3. **Nginxのバッファリングを無効化**

---

## まとめ

このシステムにより、以下が実現されます:

✅ フロント/バック統一のエラー形式（ProblemDetails）  
✅ エラーコードの一元管理（codeCatalog）  
✅ 自動的な通知表示（severity別）  
✅ トレースIDによる追跡  
✅ SSEによるリアルタイム通知  
✅ ジョブ失敗の自動通知  

問題が発生した場合は、traceId をログから検索して詳細を確認してください。
