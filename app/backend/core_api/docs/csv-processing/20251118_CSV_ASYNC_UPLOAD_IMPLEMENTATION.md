# CSVアップロード非同期化実装 - 2024年11月18日

## 概要

CSV アップロード処理を非同期化し、アップロード失敗時に persistent な右上通知を表示するように改修しました。

## 変更内容

### 1. バックエンド (FastAPI / Python)

#### 1.1. Router層 (`app/presentation/routers/database/router.py`)

**変更点:**

- FastAPI の `BackgroundTasks` をインポート
- 各アップロードエンドポイント (`/upload/syogun_csv`, `/upload/syogun_csv_final`, `/upload/syogun_csv_flash`) に `background_tasks: BackgroundTasks` パラメータを追加
- `uc.execute()` から `uc.start_async_upload()` に変更

**動作:**

1. 軽量バリデーション(ファイルタイプ、重複チェック)を実行
2. `log.upload_file` テーブルに `pending` 状態で登録
3. 重い処理(CSV解析・DB保存・ETL)を `BackgroundTasks` に登録
4. 即座に「受付完了」レスポンスを返す(`upload_file_ids` を含む)

#### 1.2. UseCase層 (`app/application/usecases/upload/upload_syogun_csv_uc.py`)

**追加メソッド:**

- **`start_async_upload()`**

  - 受付処理のみを行う(軽量)
  - ファイルタイプ検証、重複チェック、`log.upload_file` への登録
  - ファイル内容を bytes で保持し、バックグラウンドタスクに渡す
  - 即座に `UPLOAD_ACCEPTED` レスポンスを返す

- **`_process_csv_in_background()`**
  - バックグラウンドで実行される重い処理
  - ステータスを `pending` → `processing` に更新
  - CSV読込 → バリデーション → フォーマット → DB保存(raw/stg層)
  - 成功時: ステータスを `success` に更新、マテビュー更新
  - 失敗時: ステータスを `failed` に更新、エラーメッセージを記録

**既存メソッド:**

- `execute()` は互換性のため残し、同期的な処理として維持

#### 1.3. ステータス照会API (`/database/upload/status/{upload_file_id}`)

**新規追加:**

- GET エンドポイントで `upload_file_id` を受け取る
- `log.upload_file` テーブルから該当レコードを取得
- ステータス(`pending`, `processing`, `success`, `failed`)、エラーメッセージ、行数などを返す

**レスポンス例:**

```json
{
  "status": "success",
  "code": "STATUS_OK",
  "detail": "ステータス: success",
  "result": {
    "id": 123,
    "csv_type": "receive",
    "file_name": "receive.csv",
    "processing_status": "success",
    "uploaded_at": "2024-11-18T10:30:00",
    "row_count": 1000,
    "error_message": null
  }
}
```

### 2. フロントエンド (React / TypeScript)

#### 2.1. Repository層 (`features/database/dataset-import/repository/DatasetImportRepositoryImpl.ts`)

**変更点:**

- `notifyPersistent` をインポート
- アップロード失敗時の通知を `notifyError` から `notifyPersistent('error', ...)` に変更
- 成功時のメッセージを「アップロード受付完了」に変更

**persistent 通知の利用:**

```typescript
// 致命的なエラー
notifyPersistent(
  "error",
  "アップロード失敗",
  "CSVアップロード処理に失敗しました。詳細は取込履歴を確認してください。",
);

// ApiError
if (error instanceof ApiError) {
  notifyPersistent(
    "error",
    "アップロードエラー",
    error.userMessage || error.message,
  );
}
```

#### 2.2. 通知機構 (`features/notification`)

**既存の仕組みを活用:**

- `notifyPersistent(type, title, message)`: `duration: null` で自動クローズしない通知を表示
- `NotificationCenterAntd`: 右上に表示、closableで手動クローズ可能
- `useNotificationStore`: Zustand で通知を管理

**persistent 通知の特徴:**

- `duration: null` を指定することで自動削除されない
- ユーザーが「×」ボタンを押すまで表示され続ける
- 致命的なエラーや重要な通知に使用

### 3. データベース (`log.upload_file` テーブル)

**ステータスの遷移:**

```
pending → processing → success / failed
```

**カラム:**

- `id`: プライマリーキー
- `csv_type`: `receive`, `yard`, `shipment`
- `file_name`: ファイル名
- `file_hash`: SHA256ハッシュ(重複チェック用)
- `file_type`: `FLASH` / `FINAL`
- `file_size_bytes`: ファイルサイズ
- `row_count`: 保存行数(成功時のみ)
- `uploaded_at`: アップロード日時
- `uploaded_by`: アップロードユーザー
- `processing_status`: `pending` / `processing` / `success` / `failed`
- `error_message`: エラーメッセージ(失敗時のみ)
- `env`: 環境(`local_dev`, `stg`, `prod`)

## 設計方針

### Clean Architecture / SOLID原則の遵守

1. **単一責任の原則 (SRP)**

   - Router層: HTTP I/O のみ
   - UseCase層: アプリケーションロジック(受付 / バックグラウンド処理)
   - Repository層: DB操作のみ

2. **依存関係逆転の原則 (DIP)**

   - UseCase は Port (interface) に依存
   - Adapter (実装) を DI で注入

3. **既存コードの再利用**
   - 既存の `execute()` メソッドは維持(互換性)
   - 新しい `start_async_upload()` を追加
   - 通知機構(`notificationStore`, `notifyPersistent`)を活用

### FSD (Feature-Sliced Design) + MVVM

**フロントエンド構成:**

- `features/database/dataset-import/`

  - `hooks/`: ViewModel (ビジネスロジック)
  - `repository/`: データアクセス層
  - `api/`: HTTP クライアント
  - `ui/`: View (プレゼンテーション層)

- `features/notification/`
  - `domain/services/`: 通知ストア(Zustand)
  - `infrastructure/`: 通知関数(`notifyPersistent` など)
  - `ui/components/`: 通知UIコンポーネント

## 動作確認手順

### 1. 環境起動

```bash
# バックエンド(Docker Compose)
cd /home/koujiro/work_env/22.Work_React/sanbou_app
docker compose -f docker/docker-compose.dev.yml up -d

# フロントエンド(Vite)
cd app/frontend
npm run dev
```

### 2. 正常系テスト

**手順:**

1. ブラウザで `http://localhost:5173/database/import` を開く
2. 「将軍CSV(速報版)」データセットを選択
3. 受入一覧CSVをアップロード
4. 「受付完了」通知が表示されることを確認
5. 数秒待機
6. ダッシュボードでデータが反映されていることを確認

**期待される動作:**

- アップロード後、即座に「受付完了」通知(自動クローズ)
- バックグラウンドで処理が実行される
- タイムアウトせずに完了する

### 3. エラー系テスト(A: バリデーションエラー)

**手順:**

1. 不正な拡張子のファイル(`.txt`, `.xlsx`)をアップロード
2. または、カラム不足のCSVをアップロード

**期待される動作:**

- 即座に「アップロード失敗」の persistent 通知(手動クローズ必要)
- 通知は右上に表示され、「×」ボタンを押すまで残る

### 4. エラー系テスト(B: DB保存エラー)

**手順:**

1. 正常なCSVをアップロード
2. バックグラウンド処理中にDBを停止(`docker compose stop db`)

**期待される動作:**

- 受付完了通知は表示される
- バックグラウンドでエラーが発生
- `log.upload_file` テーブルの `processing_status` が `failed` に更新
- ステータス照会APIで確認可能

### 5. ステータス照会APIテスト

**curl コマンド:**

```bash
# アップロード後、upload_file_id を取得(例: 123)
curl -X GET "http://localhost:8000/api/database/upload/status/123"
```

**期待されるレスポンス:**

```json
{
  "status": "success",
  "code": "STATUS_OK",
  "detail": "ステータス: success",
  "result": {
    "id": 123,
    "csv_type": "receive",
    "file_name": "receive.csv",
    "processing_status": "success",
    "row_count": 1000
  }
}
```

### 6. 大容量CSVテスト

**手順:**

1. 10万行以上の大容量CSVを準備
2. アップロード
3. レスポンスが即座に返ることを確認(タイムアウトしない)
4. バックグラウンド処理の完了を待つ

**期待される動作:**

- 受付は1秒以内に完了
- バックグラウンド処理は数十秒～数分かかる場合がある
- 処理中もブラウザは操作可能

## トラブルシューティング

### 1. persistent 通知が表示されない

**原因:**

- `notifyPersistent` が正しくインポートされていない
- `NOTIFY_DEFAULTS.persistent` が `null` になっていない

**確認:**

```typescript
// features/notification/domain/config.ts
export const NOTIFY_DEFAULTS = {
  persistent: null as number | null, // ← null であること
};
```

### 2. バックグラウンド処理が実行されない

**原因:**

- FastAPI の `BackgroundTasks` が正しく動作していない
- ログに `[BG]` プレフィックスのメッセージが出力されていない

**確認:**

```bash
# core_api のログを確認
docker logs local_dev-core_api-1 --tail 100 -f
```

**期待されるログ:**

```
[BG] Background processing started for upload_file_ids: {'receive': 123}
[BG] Loaded receive: 1000 rows
[BG] Background processing completed successfully for: ['receive']
```

### 3. ステータスが `processing` のまま

**原因:**

- バックグラウンド処理でエラーが発生している
- エラーハンドリングが不適切

**確認:**

```bash
# エラーログを確認
docker logs local_dev-core_api-1 --tail 500 | grep "BG"
```

## まとめ

### 実装のポイント

1. **非同期化**

   - FastAPI `BackgroundTasks` で重い処理をバックグラウンド実行
   - 即座に受付完了レスポンスを返す
   - ユーザー体験の向上(タイムアウトなし)

2. **persistent 通知**

   - `notifyPersistent` で自動クローズしない通知
   - 致命的なエラーに使用
   - ユーザーが手動で閉じるまで表示

3. **既存設計の活用**

   - Clean Architecture / DDD / SOLID 原則を遵守
   - 既存の notification 機構を再利用
   - 最小限の変更で実装

4. **ステータス管理**
   - `log.upload_file` テーブルでステータスを管理
   - ステータス照会APIで進捗確認可能
   - 将来的にポーリングやSSEで進捗表示も可能

### 今後の改善案

1. **フロントエンドでのポーリング**

   - アップロード後、ステータス照会APIをポーリング
   - 処理完了時に通知を表示

2. **SSE (Server-Sent Events)**

   - リアルタイムで進捗を通知
   - より良いユーザー体験

3. **ジョブキュー (Celery / RQ)**

   - より本格的な非同期処理
   - リトライ、優先度制御など

4. **WebSocket**
   - 双方向通信でリアルタイム進捗表示

## 関連ファイル

### バックエンド

- `app/backend/core_api/app/presentation/routers/database/router.py`
- `app/backend/core_api/app/application/usecases/upload/upload_syogun_csv_uc.py`
- `app/backend/core_api/app/infra/adapters/upload/raw_data_repository.py`

### フロントエンド

- `app/frontend/src/features/database/dataset-import/repository/DatasetImportRepositoryImpl.ts`
- `app/frontend/src/features/notification/domain/services/notificationStore.ts`
- `app/frontend/src/features/notification/infrastructure/notify.ts`
- `app/frontend/src/features/notification/ui/components/NotificationCenterAntd.tsx`

### ドキュメント

- `docs/CSV_ASYNC_UPLOAD_IMPLEMENTATION_20251118.md` (本ファイル)
