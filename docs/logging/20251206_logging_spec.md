# テクニカルログ仕様書

**作成日**: 2025-12-02  
**最終更新**: 2025-12-02 (Refactoring Phase 5)  
**対象**: 全バックエンドサービス (core_api, ledger_api, rag_api, manual_api, ai_api, plan_worker)  
**ログ基盤**: backend_shared  
**バージョン**: 2.1

---

## 📋 概要

本ドキュメントは、全バックエンドサービスで共通利用する**テクニカルログ基盤**（`backend_shared`）の設計方針と運用ルールを定義します。

### 目的

- GCP Cloud Logging への統合を見据えた構造化ログの実現
- リクエスト単位のトレーシング（Request ID による紐付け）
- マイクロサービス間の統一ログフォーマット
- 本番環境でのトラブルシューティングとパフォーマンス分析
- 監査ログ・業務ログとの明確な分離

### 対象範囲

- **含む**: アプリケーションログ（INFO/WARNING/ERROR/CRITICAL）、リクエスト/レスポンスのトレース
- **含まない**: アクセスログ（nginx で管理）、監査ログ（別途 audit_log テーブルで管理）

### 🆕 Refactoring Phase 5 の変更点

**2025-12-02 実施:**

- ✅ 全マイクロサービスにログ基盤実装完了（ledger_api, rag_api, manual_api, ai_api, plan_worker）
- ✅ 重複ログ機能の統合
  - `core_api/shared/logging_utils.py` → 削除済み（backend_shared使用）
  - `ledger_api/infra/report_utils/logger.py` → 互換レイヤー化（DeprecationWarning付与）
  - `plan_worker/app/shared/logging/` → 削除済み
- ✅ f-stringログの構造化ログ変換（一部開始）

---

## 🏗️ ログ基盤アーキテクチャ

### コンポーネント構成

```
┌─────────────────────────────────────────────────┐
│       FastAPI Application (各マイクロサービス)    │
├─────────────────────────────────────────────────┤
│  Request ID Middleware (backend_shared)         │
│  ↓ (ContextVar に request_id を設定)            │
├─────────────────────────────────────────────────┤
│  UseCase / Domain / Infra Layers                │
│  ↓ (logging.getLogger(__name__) でログ出力)    │
├─────────────────────────────────────────────────┤
│  Logging Infrastructure (backend_shared)        │
│  - Request ID Filter (ContextVar から取得)      │
│  - JSON Formatter (pythonjsonlogger)            │
│  - StreamHandler (stdout)                       │
└─────────────────────────────────────────────────┘
                    ↓
              標準出力 (stdout)
                    ↓
          Docker / GCP Cloud Logging
```

### 主要モジュール（backend_shared）

| ファイルパス                                             | 役割                                                                |
| -------------------------------------------------------- | ------------------------------------------------------------------- |
| `backend_shared/application/logging.py`                  | 統一logging設定、Request ID Filter、JSON Formatter、setup_logging() |
| `backend_shared/infra/adapters/middleware/request_id.py` | Request ID の生成・ContextVar設定・レスポンスヘッダ追加             |

### 各サービスでの使用方法

```python
# app.py または main.py
from backend_shared.application.logging import setup_logging
from backend_shared.infra.adapters.middleware.request_id import RequestIdMiddleware

# 1. logging初期化（アプリ起動時に1回）
setup_logging()

# 2. Middleware登録
app = FastAPI()
app.add_middleware(RequestIdMiddleware)
```

---

## 📝 ログフォーマット

### 構造化ログ（JSON形式）

すべてのログは **JSON形式** で標準出力に出力されます。

```json
{
  "timestamp": "2025-12-02T10:30:45",
  "level": "INFO",
  "logger": "app.core.usecases.upload.upload_shogun_csv_uc",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "CSV upload started (async)",
  "operation": "shogun_csv_upload",
  "file_type": "FLASH",
  "uploaded_by": "user@example.com",
  "csv_types": ["receive", "yard"]
}
```

### 必須フィールド

| フィールド   | 型     | 説明                                                 |
| ------------ | ------ | ---------------------------------------------------- |
| `timestamp`  | string | ISO 8601形式のタイムスタンプ                         |
| `level`      | string | ログレベル (DEBUG/INFO/WARNING/ERROR/CRITICAL)       |
| `logger`     | string | ロガー名（通常はモジュール名）                       |
| `request_id` | string | リクエストID（UUID v4 または X-Request-ID ヘッダー） |
| `message`    | string | ログメッセージ（人間可読）                           |

### 任意フィールド（extra）

`logger.info(message, extra={...})` で追加情報を付与できます。

**推奨フィールド:**

| フィールド    | 用途例                                                 |
| ------------- | ------------------------------------------------------ |
| `operation`   | 処理名（例: `shogun_csv_upload`, `build_target_card`） |
| `user_id`     | ユーザーID（認証が必要な操作）                         |
| `uploaded_by` | アップロード実行者                                     |
| `file_type`   | ファイル種別（FLASH / FINAL）                          |
| `csv_types`   | 処理対象のCSV種別リスト                                |
| `duration_ms` | 処理時間（ミリ秒）                                     |
| `row_count`   | 処理件数                                               |
| `error`       | エラー内容（例外発生時）                               |

---

## 🎯 ログレベル運用方針

### レベル定義

| レベル       | 用途                                 | 出力タイミング           | 本番環境での扱い |
| ------------ | ------------------------------------ | ------------------------ | ---------------- |
| **DEBUG**    | 詳細なデバッグ情報                   | 開発・調査時のみ         | ❌ 出力しない    |
| **INFO**     | 主要な処理の開始・終了               | 正常系フロー             | ✅ 出力する      |
| **WARNING**  | 想定内だが好ましくない状態           | リトライ成功、軽微な問題 | ✅ 出力する      |
| **ERROR**    | リクエストは失敗したがプロセスは継続 | 例外発生、外部API失敗    | ✅ 出力する      |
| **CRITICAL** | プロセスにとって致命的               | DB接続断、起動失敗       | ✅ 出力する      |

### 環境別ログレベル

| 環境             | 推奨ログレベル | 設定方法          |
| ---------------- | -------------- | ----------------- |
| **開発**         | `DEBUG`        | `LOG_LEVEL=DEBUG` |
| **ステージング** | `INFO`         | `LOG_LEVEL=INFO`  |
| **本番**         | `INFO`         | `LOG_LEVEL=INFO`  |

環境変数 `LOG_LEVEL` で制御します（デフォルト: `INFO`）。

---

## 📍 レイヤー別ログ出力方針

### UseCase 層（推奨）

**出力内容:**

- 処理の開始・終了
- 主要なビジネスロジックの実行結果
- エラー発生時の詳細情報

**例:**

```python
logger.info(
    "CSV upload started (async)",
    extra={
        "operation": "shogun_csv_upload",
        "file_type": file_type,
        "uploaded_by": uploaded_by,
        "csv_types": ["receive", "yard"],
    }
)
```

### Infra 層（最小限）

**出力内容:**

- DB接続エラー、外部API呼び出し失敗
- インフラ層固有のエラー（タイムアウト、リトライ等）

**注意:**

- 大量のクエリログは DEBUG レベルで出力（本番では無効化）

### Domain 層（基本的に出力しない）

**方針:**

- ドメインロジックは logging に依存しない（Pure Python）
- 必要な場合は例外を throw し、UseCase 層でログ出力

---

## 🔍 Request ID（トレーシング）

### 仕組み

1. **Middleware で Request ID を生成 or 継承**

   - `X-Request-ID` ヘッダーがあれば使用
   - なければ UUID v4 を生成

2. **ContextVar に保存**

   - `request_id_var.set(request_id)`
   - 以降の全ログに自動付与

3. **レスポンスヘッダーに追加**
   - `X-Request-ID` ヘッダーとして返却
   - クライアント側でもトレース可能

### 使用例

**フロントエンド:**

```javascript
// リクエスト送信
const response = await fetch("/api/upload", {
  headers: { "X-Request-ID": uuid() },
});

// レスポンスで確認
const requestId = response.headers.get("X-Request-ID");
```

**バックエンドログ:**

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "CSV upload started",
  ...
}
```

---

## 🛠️ 実装ガイド

### 各モジュールでのログ出力

```python
import logging

logger = logging.getLogger(__name__)

class MyUseCase:
    def execute(self, input_dto):
        # 開始ログ
        logger.info(
            "Operation started",
            extra={
                "operation": "my_operation",
                "user_id": input_dto.user_id,
            }
        )

        try:
            # 処理
            result = self._process(input_dto)

            # 完了ログ
            logger.info(
                "Operation completed",
                extra={
                    "operation": "my_operation",
                    "duration_ms": 123,
                    "result_count": len(result),
                }
            )

            return result

        except Exception as e:
            # エラーログ
            logger.error(
                "Operation failed",
                extra={
                    "operation": "my_operation",
                    "error": str(e),
                },
                exc_info=True  # スタックトレースを含める
            )
            raise
```

### UseCase デコレータの活用（推奨）

`backend_shared` が提供するデコレータを使用すると、さらに簡潔に書けます:

```python
from backend_shared.application.logging import log_usecase_execution

class MyUseCase:
    @log_usecase_execution(usecase_name="MyOperation", log_args=True)
    def execute(self, input_dto):
        # デコレータが自動的に開始/完了/エラーログを出力
        result = self._process(input_dto)
        return result
```

デコレータが自動で出力する内容:

- 開始ログ: UseCase名、引数（センシティブ情報を除外）
- 完了ログ: UseCase名、実行時間（ms）、結果サイズ
- エラーログ: UseCase名、エラー型、エラーメッセージ、スタックトレース

### ログ出力のベストプラクティス

#### ✅ Good

```python
# 構造化情報を extra で渡す
logger.info("CSV upload completed", extra={
    "operation": "csv_upload",
    "rows": 1000,
    "duration_ms": 456,
})
```

#### ❌ Bad

```python
# 文字列結合で情報を埋め込む（検索しづらい）
logger.info(f"CSV upload completed: rows={1000}, duration={456}ms")
```

---

## 📊 ログ分析・監視

### Cloud Logging でのクエリ例

**特定のリクエストIDでフィルタ:**

```
jsonPayload.request_id="550e8400-e29b-41d4-a716-446655440000"
```

**CSVアップロード処理の一覧:**

```
jsonPayload.operation="shogun_csv_upload"
severity="INFO"
```

**エラーログのみ抽出:**

```
severity >= "ERROR"
```

**処理時間が長いログを検索:**

```
jsonPayload.duration_ms > 5000
```

### アラート設定（推奨）

| アラート名       | 条件                  | 通知先             |
| ---------------- | --------------------- | ------------------ |
| **高頻度エラー** | ERROR が 10件/分 以上 | Slack, Email       |
| **CRITICAL発生** | CRITICAL レベルのログ | Slack（即時）      |
| **処理遅延**     | `duration_ms > 10000` | 監視ダッシュボード |

---

## 🔧 トラブルシューティング

### ログが出力されない場合

1. **環境変数を確認**

   ```bash
   echo $LOG_LEVEL
   # INFO 以上であることを確認
   ```

2. **logging 初期化を確認**

   ```python
   # app/app.py で setup_logging() が呼ばれているか
   from app.config.logging import setup_logging
   setup_logging()
   ```

3. **ログレベルを DEBUG に変更して再起動**
   ```bash
   export LOG_LEVEL=DEBUG
   docker compose restart core_api
   ```

### Request ID が `-` になる場合

- Middleware が登録されていない
- ContextVar の設定タイミングが遅い

**確認:**

```python
# app/app.py
from app.api.middleware.request_id import RequestIdMiddleware
app.add_middleware(RequestIdMiddleware)
```

---

## 📚 関連ドキュメント

- [Clean Architecture 移行ガイド](../CLEAN_ARCHITECTURE_MIGRATION.md)
- [エラーハンドリング仕様](../api-implementation/)
- [CSV アップロード実装](../api-implementation/20251127_CSV_ASYNC_UPLOAD_IMPLEMENTATION_20251118.md)

---

## 🔄 変更履歴

| 日付       | バージョン | 変更内容                                                                                                                                      |
| ---------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 2025-12-02 | 2.0        | **backend_shared への移行完了**<br>- ログ基盤を backend_shared に集約<br>- 全マイクロサービスで共通利用可能に<br>- UseCase デコレータとの統合 |
| 2025-12-02 | 1.0        | 初版作成（Phase 1-4 実装完了）                                                                                                                |

---

## 🎯 今後の拡張予定

- [ ] OpenTelemetry 対応（分散トレーシング）
- [ ] ログの自動サンプリング（高負荷時）
- [ ] ログローテーション（ローカル開発用）
- [ ] 監査ログとの統合（別テーブル連携）
- [ ] Datadog APM 連携

---

**Maintainer**: Backend Team  
**Last Updated**: 2025-12-02
