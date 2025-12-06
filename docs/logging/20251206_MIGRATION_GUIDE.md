# ログ基盤移行ガイド

**対象者**: バックエンド開発者  
**作成日**: 2025-12-02  
**適用範囲**: backend_shared v2.1 への移行

---

## 📌 概要

本ガイドは、各マイクロサービスの独自ログ実装から `backend_shared` の統一ログ基盤への移行手順を示します。

---

## 🔄 移行パターン

### Pattern 1: 独自ロガー関数からの移行

#### Before (ledger_api の例)
```python
from app.infra.report_utils import app_logger

logger = app_logger()
logger.info(f"Processing report: {report_id}")
```

#### After (backend_shared 使用)
```python
from backend_shared.application.logging import get_module_logger, create_log_context

logger = get_module_logger(__name__)
logger.info(
    "Processing report",
    extra=create_log_context(
        operation="process_report",
        report_id=report_id
    )
)
```

**変更点:**
- `app_logger()` → `get_module_logger(__name__)`
- f-string → 構造化ログ (`create_log_context`)

---

### Pattern 2: plan_worker の古いロガーからの移行

#### Before
```python
from app.shared.logging.logger import get_logger

logger = get_logger(__name__)
logger.info("Worker started")
```

#### After
```python
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)
logger.info("Worker started")
```

**変更点:**
- インポートパス変更のみ（関数名は同じ）

---

### Pattern 3: f-string ログから構造化ログへ

#### Before
```python
logger.info(f"[BFF Manual] Proxying doc request: {upstream}")
logger.error(f"[BFF Manual] Upstream error: {status_code} - {body}")
```

#### After
```python
logger.info(
    "[BFF Manual] Proxying doc request",
    extra=create_log_context(
        operation="proxy_manual_doc",
        upstream=upstream
    )
)
logger.error(
    "[BFF Manual] Upstream error",
    extra=create_log_context(
        operation="proxy_manual_doc",
        status_code=status_code,
        response_body=body[:200]  # 長すぎる場合は切り詰め
    )
)
```

**メリット:**
- JSONパース可能
- Cloud Logging でフィールド検索可能
- センシティブ情報の自動除外

---

## 🗂️ 削除済みファイル

以下のファイルは backend_shared への移行により不要となり、削除されました:

### core_api
- ~~`app/backend/core_api/app/shared/logging_utils.py`~~ → backend_shared に統合

### plan_worker
- ~~`app/backend/plan_worker/app/shared/logging/`~~ → backend_shared 使用
- ~~`app/backend/plan_worker/src/shared/logging/`~~ → backend_shared 使用

### ledger_api
- `app/backend/ledger_api/app/infra/report_utils/logger.py` → **互換レイヤーとして残存**
  - DeprecationWarning を発行
  - 将来的に削除予定

---

## ⚠️ 互換性レイヤー（一時的）

### ledger_api の app_logger()

`app_logger()` は後方互換性のため残されていますが、非推奨です。

```python
# ⚠️ Deprecated (DeprecationWarning が発行される)
from app.infra.report_utils import app_logger
logger = app_logger()

# ✅ Recommended
from backend_shared.application.logging import get_module_logger
logger = get_module_logger(__name__)
```

**移行タイムライン:**
- **Phase 1 (現在)**: 互換レイヤーで警告を発行
- **Phase 2 (次回リファクタリング)**: 全 20+ 箇所を backend_shared に移行
- **Phase 3 (完了後)**: logger.py 削除

---

## 📊 移行状況

### ✅ 完了
- core_api: 統一ログ基盤使用中
- rag_api: setup_logging + RequestIdMiddleware 実装完了
- manual_api: setup_logging + RequestIdMiddleware 実装完了
- ai_api: setup_logging + RequestIdMiddleware 実装完了
- plan_worker: setup_logging 実装完了

### 🔄 進行中
- ledger_api: app_logger() の互換レイヤー化完了、本体移行は次フェーズ
- core_api/manual router: 一部 f-string ログを構造化ログに変換開始

### 📝 未実施
- 残り 50+ 箇所の f-string ログ変換
- 未適用 UseCase への `@log_usecase_execution` デコレータ追加

---

## 🔍 検証方法

### 1. ログが JSON 形式で出力されるか確認

```bash
# コンテナログを確認
docker compose -f docker/docker-compose.dev.yml logs core_api | head -20
```

**期待される出力:**
```json
{"timestamp": "2025-12-02T10:30:00", "level": "INFO", "logger": "app.api.routers.manual", "request_id": "550e8400-...", "message": "[BFF Manual] Proxying doc request", "operation": "proxy_manual_doc", "upstream": "http://..."}
```

### 2. Request ID がログに付与されているか確認

```bash
# 特定のリクエストを追跡
docker compose -f docker/docker-compose.dev.yml logs | grep "550e8400"
```

### 3. DeprecationWarning の確認（ledger_api）

```bash
# app_logger() 使用時に警告が出るか確認
docker compose -f docker/docker-compose.dev.yml logs ledger_api | grep DeprecationWarning
```

---

## 🚀 次のステップ

1. **f-string ログの構造化変換** (優先度: 高)
   - `create_log_context()` を使った段階的変換
   - 特に頻繁に出力されるログから優先

2. **ledger_api の完全移行** (優先度: 中)
   - 20+ 箇所の `app_logger()` を `get_module_logger()` に置換
   - logger.py の削除

3. **UseCase デコレータの拡大適用** (優先度: 中)
   - sales_tree 系
   - dashboard 系
   - upload 系

4. **ドキュメント最終化** (優先度: 低)
   - ベストプラクティス集
   - Cloud Logging クエリサンプル集

---

## 📚 関連ドキュメント

- [logging_spec.md](./logging_spec.md) - テクニカルログ仕様書
- [backend_shared/application/logging.py](../../app/backend/backend_shared/src/backend_shared/application/logging.py) - 実装コード
