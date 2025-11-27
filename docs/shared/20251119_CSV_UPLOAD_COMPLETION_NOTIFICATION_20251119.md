# CSVアップロード処理完了通知機能 - 実装レポート

**実装日**: 2025年11月19日  
**対応者**: GitHub Copilot  
**関連Issue**: CSVアップロード→処理失敗時の通知機能追加

---

## 📋 概要

CSVアップロード後のバックグラウンド処理の完了/失敗をユーザーに通知する仕組みを実装しました。

### 背景

既存実装では:
- ✅ バックエンドで非同期処理が実装済み（FastAPI BackgroundTasks）
- ✅ ステータス照会API (`/database/upload/status/{upload_file_id}`) が存在
- ❌ フロントエンドでポーリングする仕組みが未実装
- ❌ 処理完了・失敗の通知がユーザーに届かない

### 問題点

1. アップロード受付完了後、処理が成功したか失敗したかわからない
2. バックグラウンド処理でエラーが発生してもユーザーに通知されない
3. 処理完了まで待つ方法がない

---

## 🎯 実装内容

### 1. ステータス照会APIクライアント追加

**ファイル**: `features/database/dataset-import/api/client.ts`

```typescript
export interface UploadStatusResponse {
  status: 'success' | 'error';
  code: string;
  detail: string;
  result?: {
    id: number;
    csv_type: string;
    file_name: string;
    processing_status: 'pending' | 'processing' | 'success' | 'failed';
    uploaded_at: string;
    row_count?: number;
    error_message?: string;
  };
}

// checkStatus メソッドを追加
async checkStatus(uploadFileId: number): Promise<UploadStatusResponse>
```

---

### 2. ポーリングフック作成

**ファイル**: `features/database/dataset-import/hooks/useUploadStatusPolling.ts`

**機能**:
- アップロード後、定期的にステータスをチェック（デフォルト2秒間隔）
- 全ファイルの処理が完了するまでポーリング継続
- 最大試行回数: 30回（合計60秒）

**処理フロー**:
1. `upload_file_ids` がセットされるとポーリング開始
2. 各ファイルのステータスを並列チェック
3. すべて完了 or 失敗 or タイムアウトで停止
4. 結果に応じて通知表示

**通知ルール**:
- ✅ **すべて成功**: `notifySuccess` で処理完了通知（5秒で自動消去）
- ❌ **失敗あり**: `notifyPersistent` でエラー通知（手動クローズ必要）
- ⏰ **タイムアウト**: `notifyPersistent` でタイムアウト通知

---

### 3. useSubmitVM の拡張

**ファイル**: `features/database/dataset-submit/hooks/useSubmitVM.ts`

**変更点**:
- `doUpload` の戻り値を `boolean` → `UploadResult` に変更
- バックエンドから返された `upload_file_ids` を抽出
- アップロード受付完了時の通知文言を変更

```typescript
export interface UploadResult {
  success: boolean;
  uploadFileIds?: Record<string, number>;
}
```

**通知メッセージの変更**:
```typescript
// 旧: "CSVファイルのアップロードが完了しました。データの処理が開始されます。"
// 新: "CSVファイルのアップロードを受け付けました。データ処理中です..."
```

---

### 4. useDatasetImportVM への統合

**ファイル**: `features/database/dataset-import/hooks/useDatasetImportVM.ts`

**変更点**:
1. `uploadFileIds` ステートを追加
2. `useUploadStatusPolling` を統合
3. アップロード成功時に `upload_file_ids` をセットしてポーリング開始
4. 処理完了時のコールバックで状態をクリア

```typescript
// ポーリング統合
useUploadStatusPolling({
  uploadFileIds,
  onComplete: (allSuccess) => {
    console.log('Processing complete:', allSuccess);
    setUploadFileIds(undefined); // ポーリング停止
    
    if (allSuccess) {
      // すべて成功した場合のみファイルをクリア
      setFiles({});
      setStatus({});
      setPreviews({});
      setSkipped({});
    }
  },
});
```

---

## 🔄 処理フロー全体

```
[ユーザー]
   ↓ ファイル選択
[useDatasetImportVM]
   ↓ doUpload()
[useSubmitVM]
   ↓ repo.upload()
[DatasetImportRepositoryImpl]
   ↓ POST /upload/syogun_csv_flash
[バックエンド]
   ├─ 即座にレスポンス (upload_file_ids 含む)
   └─ BackgroundTasks で処理開始
      ├─ log.upload_file.processing_status: pending → processing
      └─ 処理完了時: success or failed

[フロントエンド]
   ← レスポンス受信 (upload_file_ids)
   ↓ setUploadFileIds() でポーリング開始
[useUploadStatusPolling]
   ├─ 2秒ごとに GET /database/upload/status/{id}
   ├─ 処理中: ポーリング継続
   └─ 完了/失敗検知
      ↓
   [通知表示]
      ├─ 成功: notifySuccess (自動消去)
      └─ 失敗: notifyPersistent (手動クローズ)
```

---

## 📦 変更ファイル一覧

### 新規作成
- `features/database/dataset-import/hooks/useUploadStatusPolling.ts`

### 更新
- `features/database/dataset-import/api/client.ts`
- `features/database/dataset-import/hooks/useDatasetImportVM.ts`
- `features/database/dataset-import/index.ts`
- `features/database/dataset-submit/hooks/useSubmitVM.ts`
- `features/database/dataset-submit/index.ts`
- `features/database/dataset-import/repository/DatasetImportRepository.ts`
- `features/database/dataset-import/repository/DatasetImportRepositoryImpl.ts`
- `features/database/shared/types/common.ts`

---

## ✅ 動作確認

### 正常系

1. CSVファイルをアップロード
2. 「アップロード受付完了」通知が表示（3秒で消える）
3. バックグラウンド処理中...
4. 数秒後「処理完了」通知が表示（5秒で消える）
5. ファイル選択がクリアされる

### 異常系（処理失敗）

1. CSVファイルをアップロード
2. 「アップロード受付完了」通知が表示
3. バックグラウンド処理中にエラー発生
4. 「処理失敗」通知が表示（手動クローズ必要）
   - エラー詳細が表示される
   - ファイル選択はクリアされない（再試行可能）

### 異常系（タイムアウト）

1. CSVファイルをアップロード
2. 「アップロード受付完了」通知が表示
3. 60秒経過しても処理が完了しない
4. 「処理タイムアウト」通知が表示（手動クローズ必要）
   - 履歴画面での確認を促す

---

## 🎨 通知デザイン

### 成功通知（自動消去）
```
✓ 処理完了
3件のCSVファイルの処理が完了しました。（10,000行）
```

### エラー通知（手動クローズ）
```
✗ 処理失敗
以下のファイルの処理に失敗しました:
【受入一覧】データベース接続エラー
【出荷一覧】カラム不足
```

### タイムアウト通知（手動クローズ）
```
⚠ 処理タイムアウト
受入一覧 の処理が時間内に完了しませんでした。
履歴画面で確認してください。
```

---

## 🔧 設定可能なパラメータ

### useUploadStatusPolling

```typescript
export interface UploadStatusPollingOptions {
  /** ポーリング対象の upload_file_ids */
  uploadFileIds?: Record<string, number>;
  
  /** ポーリング間隔（ミリ秒）*/
  interval?: number; // デフォルト: 2000
  
  /** 最大試行回数 */
  maxAttempts?: number; // デフォルト: 30（60秒）
  
  /** 完了時のコールバック */
  onComplete?: (allSuccess: boolean) => void;
}
```

---

## 📊 パフォーマンス考慮

### ポーリング負荷
- **間隔**: 2秒（調整可能）
- **最大試行**: 30回（60秒間）
- **並列チェック**: 全ファイルを Promise.all で並列実行
- **自動停止**: 完了・失敗・タイムアウト時に自動停止

### ネットワーク負荷
- 1ファイルあたり最大30リクエスト
- 3ファイル同時アップロード時: 最大90リクエスト/60秒
- APIレスポンスは軽量（JSON）

---

## 🚀 今後の改善案

### 1. Server-Sent Events (SSE)
- ポーリングからプッシュ通知に変更
- リアルタイム性向上、ネットワーク負荷削減

### 2. WebSocket
- 双方向通信で進捗状況をリアルタイム表示
- 処理進捗バー（10%、50%、100%）

### 3. リトライ機能
- 処理失敗時に自動リトライ
- 指数バックオフで負荷分散

### 4. 履歴画面連携
- 通知から履歴画面への遷移ボタン
- 詳細なエラーログ表示

---

## 🎯 まとめ

### 実装前
- ❌ アップロード後、処理状況がわからない
- ❌ エラーが発生してもユーザーに通知されない
- ❌ 処理完了まで待つ方法がない

### 実装後
- ✅ アップロード受付完了を即座に通知
- ✅ バックグラウンド処理の完了・失敗を自動検知
- ✅ 成功時は自動消去、失敗時は手動クローズで適切な通知
- ✅ ポーリングで最大60秒間監視
- ✅ タイムアウト時も適切な通知

---

**実装完了**: すべてのテストケースで正常動作を確認
