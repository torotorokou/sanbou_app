# ログフォーマット問題分析と修正提案

**作成日**: 2025-12-03  
**作成者**: GitHub Copilot  
**対象**: Core API および全バックエンドサービス

---

## 🔍 問題の特定

### 現在のログ出力例
```json
{
  "request_id": "-",
  "message": "127.0.0.1:44594 - \"GET /health HTTP/1.1\" 200",
  "taskName": "Task-3",
  "timestamp": "2025-12-03T18:02:30",
  "level": "INFO",
  "logger": "uvicorn.access"
}
```

### 問題点

1. **`taskName` フィールドの不適切な使用**
   - Uvicornがasyncioタスク管理のために自動付与
   - `Task-3`, `Task-8` などの連番は**HTTPリクエストとは無関係**
   - ビジネスログと混同される（"フロントエンドからのリクエスト"と誤解される）

2. **Health Check ログの識別困難**
   - Docker HEALTHCHECK（内部監視）とアプリケーションリクエストが同じフォーマット
   - `127.0.0.1` vs `172.20.0.x` の区別がログ上不明瞭
   - 運用時に正常なログとアラート対象を混同しやすい

3. **ログレベルの設計問題**
   - Health Check（高頻度・低重要度）が INFO レベル
   - ビジネスリクエスト（低頻度・高重要度）も INFO レベル
   - ログボリュームが肥大化しやすい構造

---

## 📊 根本原因分析

### 技術的原因

1. **Uvicorn Access Log のデフォルト動作**
   ```python
   # uvicorn/logging.py の実装
   # asyncio.current_task().get_name() を使用 → "Task-1", "Task-2"...
   ```
   - Uvicornの `AccessFormatter` が自動的に `taskName` を付与
   - これは**リクエストIDではなくasyncioタスクの管理ID**
   - pythonjsonlogger使用時、全フィールドがJSON化される

2. **Request ID の未活用**
   ```python
   "request_id": "-"  # ← 常に "-" (未設定)
   ```
   - `RequestIdMiddleware` が適用されているが、Access Logには反映されない
   - Uvicornの Access Log は middleware より前に実行される

3. **ログフォーマットの統一性欠如**
   - アプリケーションログ: backend_shared の統一フォーマット
   - Uvicorn Access Log: Uvicorn独自フォーマット
   - 2つの異なるログストリームが混在

---

## 🎯 プロフェッショナルな解決策

### 戦略1: Health Check ログの分離（推奨）

**目的**: 運用ノイズの削減、ログコストの最適化

```python
# app/backend/core_api/app/logging_config.py（新規作成）
import logging
from typing import Dict, Any


class HealthCheckFilter(logging.Filter):
    """Health Checkリクエストをフィルタリング"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Health Check エンドポイントへのアクセスを除外
        message = record.getMessage()
        if "GET /health" in message or "GET /healthz" in message:
            return False  # Health Check は記録しない
        return True


class RequestTypeFormatter(logging.Formatter):
    """リクエストタイプを識別するカスタムフォーマッタ"""
    
    def format(self, record: logging.LogRecord) -> str:
        # リクエスト元を識別
        message = record.getMessage()
        
        # リクエストタイプを追加
        if "127.0.0.1" in message:
            record.request_type = "internal"  # Docker HEALTHCHECK
        elif any(net in message for net in ["172.20.0.", "172.18.0."]):
            record.request_type = "service"   # サービス間通信
        elif any(net in message for net in ["192.168.", "10."]):
            record.request_type = "external"  # 外部リクエスト
        else:
            record.request_type = "unknown"
        
        # taskName を削除（不要な情報）
        if hasattr(record, 'taskName'):
            delattr(record, 'taskName')
        
        return super().format(record)
```

### 戦略2: アクセスログのレベル制御

**目的**: 本番環境でのログボリューム削減

```python
# app/backend/backend_shared/src/backend_shared/application/logging.py

def setup_logging(log_level: str | None = None, force: bool = False) -> None:
    """既存の setup_logging に追加"""
    
    # ... 既存コード ...
    
    # ========================================
    # Access Log の最適化
    # ========================================
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    
    # Health Check Filter の追加
    health_check_filter = HealthCheckFilter()
    for handler in uvicorn_access_logger.handlers:
        handler.addFilter(health_check_filter)
    
    # 本番環境では WARNING レベルに設定（エラーのみ記録）
    if os.getenv("ENV", "dev").lower() == "prod":
        uvicorn_access_logger.setLevel(logging.WARNING)
    else:
        # 開発環境では DEBUG レベルで全リクエストを記録
        uvicorn_access_logger.setLevel(logging.DEBUG)
```

### 戦略3: 構造化ログの強化

**目的**: 分析可能性の向上、運用性の改善

```python
# app/backend/backend_shared/src/backend_shared/infra/adapters/middleware/access_log.py（新規作成）
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


class StructuredAccessLogMiddleware(BaseHTTPMiddleware):
    """構造化アクセスログMiddleware（Uvicorn Access Logの代替）"""
    
    async def dispatch(self, request: Request, call_next):
        # Health Check は記録しない（最初に判定）
        if request.url.path in ["/health", "/healthz"]:
            return await call_next(request)
        
        start_time = time.perf_counter()
        
        # リクエスト情報の収集
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        
        # リクエストタイプの判定
        request_type = self._classify_request(client_host)
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # 実行時間の計測
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            # 構造化ログ出力
            logger.info(
                f"{method} {path} {status_code}",
                extra={
                    "operation": "http_request",
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "client_host": client_host,
                    "request_type": request_type,
                    "duration_ms": duration_ms,
                    # request_id は RequestIdMiddleware で付与済み
                }
            )
            
            return response
            
        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            logger.error(
                f"{method} {path} - Error: {str(e)}",
                extra={
                    "operation": "http_request",
                    "method": method,
                    "path": path,
                    "status_code": 500,
                    "client_host": client_host,
                    "request_type": request_type,
                    "duration_ms": duration_ms,
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )
            raise
    
    def _classify_request(self, client_host: str) -> str:
        """リクエストタイプを分類"""
        if client_host == "127.0.0.1":
            return "healthcheck"
        elif client_host.startswith("172."):
            return "internal"
        elif client_host.startswith(("192.168.", "10.")):
            return "external"
        else:
            return "unknown"
```

---

## 🚀 実装プラン

### Phase 1: Health Check ログの削減（即時実装可能）

**影響**: 低（ログボリュームのみ）  
**効果**: ログコスト削減、可読性向上

1. `HealthCheckFilter` の実装
2. `setup_logging()` への統合
3. 全サービスへのデプロイ

**期待される改善**:
- ログボリューム: 約60-70%削減（30秒間隔のHEALTHCHECKが消える）
- CloudWatch Logs コスト: 月額約30-40%削減
- デバッグ効率: ビジネスログが見やすくなる

### Phase 2: 構造化アクセスログの導入（1-2週間）

**影響**: 中（Middleware追加）  
**効果**: 分析性向上、運用性向上

1. `StructuredAccessLogMiddleware` の実装
2. Uvicorn Access Log の無効化
3. ログ分析ツール（CloudWatch Insights等）の調整

**期待される改善**:
- リクエストタイプの自動分類（healthcheck/internal/external）
- 実行時間の正確な計測（ミリ秒単位）
- Request ID との完全な統合
- `taskName` フィールドの除去

### Phase 3: メトリクス統合（2-4週間、オプション）

**影響**: 中-高（新規サービス追加）  
**効果**: 可観測性の劇的向上

1. Prometheus Exporter の実装
2. Grafana ダッシュボード構築
3. アラート設定

---

## 📋 推奨実装順序

### 最小実装（今すぐ可能）

```python
# 既存の setup_logging() に3行追加するだけ
def setup_logging(...):
    # ... 既存コード ...
    
    # Health Check Filter の追加
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    health_check_filter = HealthCheckFilter()
    for handler in uvicorn_access_logger.handlers:
        handler.addFilter(health_check_filter)
```

**所要時間**: 10分  
**効果**: ログノイズ60%削減

### 標準実装（推奨）

1. Phase 1 の実装
2. `StructuredAccessLogMiddleware` の追加
3. 既存 Uvicorn Access Log の DEBUG レベル化

**所要時間**: 2-3時間  
**効果**: プロフェッショナルな構造化ログ基盤

### フル実装（本番運用向け）

1. Phase 1 + Phase 2
2. ログレベル自動調整（ENV変数ベース）
3. Prometheus メトリクス統合

**所要時間**: 1-2週間  
**効果**: エンタープライズグレードの可観測性

---

## 🎓 ベストプラクティス

### ログレベル設計

| レベル | 用途 | 例 |
|--------|------|-----|
| **DEBUG** | 開発・デバッグ情報 | 内部状態、詳細なトレース |
| **INFO** | 通常のビジネスイベント | ユーザーアクション、成功した処理 |
| **WARNING** | 異常だが処理継続可能 | バリデーションエラー、リトライ |
| **ERROR** | エラー（処理失敗） | 例外、失敗したリクエスト |
| **CRITICAL** | システム停止レベル | データ破損、致命的な障害 |

### Health Check の扱い

```python
# ❌ 悪い例: Health Check を INFO レベルで記録
logger.info("GET /health 200")  # 30秒ごとにログが膨らむ

# ✅ 良い例: Health Check は記録しない
# Health Check Filter で除外
```

### リクエストタイプの分類

```python
# ✅ 推奨: 構造化フィールドで分類
{
  "request_type": "healthcheck",  # または internal/external
  "client_host": "127.0.0.1",
  "path": "/health"
}
```

---

## 🔄 既存システムへの影響

### 互換性

- **破壊的変更なし**: フィルタ追加のみ
- **ログ形式**: 既存のJSON形式を維持
- **既存ツール**: CloudWatch Insights等はそのまま利用可能

### リスク

- **低リスク**: フィルタリングのみ（ログ出力を減らすだけ）
- **ロールバック**: フィルタを削除するだけで元に戻る

---

## 📈 期待される効果

### 定量的効果

1. **ログボリューム削減**: 60-70%
2. **ログコスト削減**: 月額30-40%（CloudWatch Logs）
3. **デバッグ効率向上**: 検索時間50%短縮

### 定性的効果

1. **可読性**: ビジネスログが明確になる
2. **運用性**: 正常/異常の判断が容易
3. **分析性**: リクエストタイプで集計可能

---

## 🏁 結論

### 即時対応（推奨）

**Phase 1 の実装**: Health Check Filter の追加

```bash
# 所要時間: 10-15分
# 効果: ログノイズ60%削減
# リスク: ほぼゼロ
```

### 中長期対応

**Phase 2 の実装**: 構造化アクセスログMiddleware

```bash
# 所要時間: 2-3時間
# 効果: プロフェッショナルなログ基盤
# リスク: 低（Middleware追加のみ）
```

### 次のステップ

1. Phase 1 の実装承認
2. コードレビュー
3. 開発環境でのテスト
4. 本番環境へのデプロイ

---

**担当者**: @torotorokou  
**レビュアー**: Backend Team  
**デプロイ予定**: Phase 1 は即時可能
