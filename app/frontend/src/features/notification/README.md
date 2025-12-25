# features/notification

通知機能を管理する Feature モジュール

## 📁 ディレクトリ構造

```
notification/
├── model/                          # ビジネスロジックと状態管理
│   ├── notification.types.ts      # 型定義
│   └── notification.store.ts      # Zustand ストア
├── controller/                     # 通知の呼び出しAPI
│   └── notify.ts                   # notifySuccess, notifyError など
├── view/                           # UIコンポーネント
│   ├── NotificationCenter.tsx     # 基本的な通知表示
│   └── NotificationCenterAntd.tsx # Ant Design版の通知表示
├── config.ts                       # デフォルト設定（持続時間など）
├── index.ts                        # 公開API
└── README.md                       # このファイル
```

## 🎯 役割

このモジュールは、アプリケーション全体で使用される通知システムを提供します。

### Model (モデル)

- **notification.types.ts**: 通知の型定義

  - `NotificationType`: 'success' | 'error' | 'warning' | 'info'
  - `Notification`: 通知オブジェクトの型
  - `CreateNotificationData`: 通知作成時のデータ型

- **notification.store.ts**: Zustand による状態管理
  - 通知の追加、削除、クリア
  - 自動削除タイマーの管理
  - 重複抑止機能（800ms以内の同じ通知を無視）
  - 最大表示数の制限（5件）

### Controller (コントローラー)

- **notify.ts**: 通知を発行する関数
  - `notifySuccess()`: 成功通知
  - `notifyError()`: エラー通知
  - `notifyInfo()`: 情報通知
  - `notifyWarning()`: 警告通知
  - `notifyPersistent()`: 自動削除されない通知
  - `notifyApiError()`: APIエラーを通知に変換

### View (ビュー)

- **NotificationCenter.tsx**: 基本的な通知表示コンポーネント
- **NotificationCenterAntd.tsx**: Ant Design の Alert を使った通知表示

### Config (設定)

- **config.ts**: デフォルト設定
  - 各通知タイプの表示時間
  - persistent: 自動削除しない設定

## 📖 使用方法

### 基本的な使用

```typescript
import {
  notifySuccess,
  notifyError,
  notifyInfo,
  notifyWarning,
} from "@features/notification";

// 成功通知
notifySuccess("保存完了", "データが正常に保存されました");

// エラー通知
notifyError("保存失敗", "データの保存に失敗しました");

// 情報通知
notifyInfo("お知らせ", "新しい機能が追加されました");

// 警告通知
notifyWarning("注意", "この操作は取り消せません");
```

### カスタム表示時間

```typescript
// 10秒間表示
notifySuccess("保存完了", "データが保存されました", 10000);

// 自動削除しない（手動で閉じるまで表示）
notifyPersistent("error", "重要なエラー", "システム管理者に連絡してください");
```

### APIエラーの通知

```typescript
import { notifyApiError } from "@features/notification";

try {
  await api.save(data);
} catch (error) {
  // RFC7807形式のエラーやApiErrorを自動で通知に変換
  notifyApiError(error, "データの保存に失敗しました");
}
```

### ストアの直接使用

```typescript
import { useNotificationStore } from '@features/notification';

function MyComponent() {
  const { notifications, removeNotification } = useNotificationStore();

  return (
    <div>
      {notifications.map(n => (
        <div key={n.id}>
          {n.title}
          <button onClick={() => removeNotification(n.id)}>閉じる</button>
        </div>
      ))}
    </div>
  );
}
```

### 通知センターの配置

```typescript
import { NotificationCenter } from '@features/notification';
// または
import { NotificationCenterAntd } from '@features/notification';

function App() {
  return (
    <>
      <NotificationCenter />
      {/* アプリケーションのコンテンツ */}
    </>
  );
}
```

## 🔧 設定のカスタマイズ

```typescript
import { NOTIFY_DEFAULTS } from "@features/notification";

// デフォルト設定
// successMs: 4000,
// infoMs: 5000,
// warningMs: 5000,
// errorMs: 6000,
// persistent: null (自動削除しない)
```

## 🧪 テスト

```bash
# テストの実行
npm run test src/stores/notificationStore.test.ts
npm run test src/utils/notify.test.ts
```

## 📝 依存関係

- **依存先**: `shared` レイヤーのみ
- **依存元**: `app`, `pages`, `widgets`, 他の `features` から使用可能

## 🎨 特徴

- ✅ 重複抑止（800ms以内の同じ通知を無視）
- ✅ 自動削除タイマー（通知タイプごとにカスタマイズ可能）
- ✅ 最大表示数の制限（5件まで）
- ✅ TypeScript完全対応
- ✅ Zustand による軽量な状態管理
- ✅ RFC7807 / ApiError の自動変換
- ✅ テストカバレッジ

## 🔄 移行履歴

- 元の場所: `src/stores/notificationStore.ts`, `src/utils/notify.ts`
- 移行先: `src/features/notification/` (FSD構造)
- 互換性: 既存のimportパスは互換性レイヤーでサポート
