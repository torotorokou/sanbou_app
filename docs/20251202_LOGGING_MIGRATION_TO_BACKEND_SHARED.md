# Logging基盤の完全移行 - 2024-12-02

## 概要
core_apiからbackend_sharedのlogging基盤への完全移行を実施しました。

## 実施内容

### 1. logging.getLogger(__name__) → get_module_logger() への統一

全てのファイルで標準的な `logging.getLogger(__name__)` を `backend_shared.application.logging.get_module_logger()` に統一しました。

#### 移行対象ファイル (一部抜粋)
- `app/backend/core_api/app/app.py`
- `app/backend/core_api/app/api/routers/dashboard/router.py`
- `app/backend/core_api/app/infra/adapters/**/*.py` (全Repository/Adapter)
- `app/backend/core_api/app/infra/clients/**/*.py` (全Client)
- `app/backend/core_api/app/core/usecases/**/*.py` (全UseCase)
- `app/backend/core_api/app/infra/db/dynamic_models.py`
- その他多数

#### 変更例
```python
# Before
import logging
logger = logging.getLogger(__name__)

# After
from backend_shared.application.logging import get_module_logger
logger = get_module_logger(__name__)
```

### 2. 既存の統一logging機能の活用

backend_sharedには以下の機能が既に実装されており、core_apiで活用されています:

#### 2.1 setup_logging()
- `app/app.py` で呼び出し済み
- JSON形式のログ出力
- Request ID自動付与
- Uvicorn統合

#### 2.2 log_usecase_execution デコレータ
以下のUseCaseで既に使用中:
- `BuildTargetCardUseCase`
- `GetUploadStatusUseCase`
- `GetCalendarMonthUseCase`
- `GetUploadCalendarUseCase`
- `DeleteUploadScopeUseCase`
- `FetchSalesTreeSummaryUseCase`
- `FetchSalesTreeDailySeriesUseCase`

#### 2.3 create_log_context()
構造化ログのコンテキスト生成ヘルパー。以下のファイルで使用中:
- `dashboard_target_repository.py`
- `dashboard/router.py`
- `calendar_repository.py`
- `raw_data_repository.py`
- `customer_churn/__init__.py`
- `sales_tree_repository.py`
- その他多数

### 3. backend_shared の logging 機能一覧

#### 3.1 基本機能
- **setup_logging()**: アプリケーション起動時のlogging初期化
- **get_module_logger()**: モジュール用ロガー取得
- **set_request_id()**: Request ID設定 (Middleware用)
- **get_request_id()**: Request ID取得

#### 3.2 構造化ログ
- **create_log_context()**: 構造化ログコンテキスト生成
  - センシティブ情報の自動除外
  - None値の自動スキップ
  
#### 3.3 時間計測
- **TimedOperation**: コンテキストマネージャー形式の時間計測
  ```python
  with TimedOperation("database_query", logger=logger, threshold_ms=1000):
      result = db.execute_slow_query()
  ```

#### 3.4 UseCaseログデコレータ
- **@log_usecase_execution**: UseCase実行ログの自動記録
- **@track_usecase_metrics**: メトリクス収集
- **@combined_usecase_decorator**: ログ+メトリクス統合

#### 3.5 メトリクス
- **UseCaseMetrics**: メトリクス収集クラス (シングルトン)
  - success/error/validation_error カウント
  - スレッドセーフ実装

## 未適用の機能と今後の推奨事項

### 1. TimedOperation の活用推奨箇所

以下の処理で時間計測を追加すると有用:

#### データベースクエリ
```python
# sales_tree_repository.py の fetch_summary() など
with TimedOperation("fetch_sales_tree_summary", logger=logger, threshold_ms=500):
    result = self.db.execute(text(sql), params).fetchall()
```

#### CSV処理
```python
# upload_shogun_csv_uc.py
with TimedOperation("csv_validation", logger=logger) as timer:
    validation_result = validator.validate(df)
    timer.add_context(rows=len(df))
```

#### Materialized View Refresh
```python
# materialized_view_refresher.py
with TimedOperation("mv_refresh", logger=logger, threshold_ms=1000):
    self.db.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv_name}"))
```

### 2. 構造化ログの拡充

現在一部のファイルで `logger.info(f"...")` 形式のログが残っています。
以下のように構造化ログに移行することを推奨:

#### Before
```python
logger.info(f"Saved {len(records)} rows to raw.receive_raw (file_id={file_id})")
```

#### After
```python
logger.info(
    "Saved rows to raw.receive_raw",
    extra=create_log_context(
        operation="save_raw_data",
        table="raw.receive_raw",
        rows_count=len(records),
        file_id=file_id
    )
)
```

### 3. エラーログの構造化

#### Before
```python
logger.error(f"Failed to save raw data: {e}")
```

#### After
```python
logger.error(
    "Failed to save raw data",
    extra=create_log_context(
        operation="save_raw_data",
        error_type=type(e).__name__,
        table="raw.receive_raw"
    ),
    exc_info=True  # スタックトレース付き
)
```

## 残存課題

### 1. Router層のログ
以下のRouterファイルで `logging.getLogger(__name__)` がまだ使用されています:
- `app/api/routers/chat/router.py`
- `app/api/routers/ingest/router.py`
- `app/api/routers/reports/*.py`
- `app/api/routers/block_unit_price/router.py`
- `app/api/routers/external/router.py`
- `app/api/routers/manual/router.py`
- その他

これらは次回の作業で統一します。

### 2. メトリクス収集の未適用
`UseCaseMetrics` と `@track_usecase_metrics` デコレータはまだ活用されていません。
本番環境でのパフォーマンス監視が必要になった際に導入を検討してください。

## 利点

### 1. 統一されたログフォーマット
- JSON形式での構造化ログ
- Request ID による完全なリクエストトレーシング
- 環境変数でログレベル制御可能

### 2. 保守性の向上
- logging設定が1箇所に集約 (`backend_shared/application/logging.py`)
- 全サービスで同じログフォーマット
- センシティブ情報の自動除外

### 3. デバッグの容易性
- Request ID でログをフィルタリング可能
- 構造化ログで検索・集計が容易
- 実行時間の自動計測

### 4. テスタビリティ
- `setup_logging(force=True)` でテスト用に再初期化可能
- モックしやすいインターフェース

## 次のステップ

1. **残りのRouterファイルの移行**: `get_module_logger()` への統一
2. **TimedOperationの導入**: 重い処理への時間計測追加
3. **構造化ログの拡充**: f-string形式からcreate_log_context()への移行
4. **メトリクス収集の検討**: 本番環境でのパフォーマンス監視

## 関連ドキュメント
- `backend_shared/docs/20251128_ERROR_HANDLING_GUIDE.md`: エラーハンドリングガイド
- `backend_shared/src/backend_shared/application/logging.py`: logging基盤実装
- `docs/logging/`: ログ関連ドキュメント (将来追加予定)

## 変更履歴
- 2024-12-02: 初版作成 - core_api全体でget_module_logger()への移行完了
