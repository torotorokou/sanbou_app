# Ledger API Logging基盤の完全移行 - 2024-12-02

## 概要
ledger_apiのlogging基盤をbackend_sharedに完全統合しました。
core_apiに続く2つ目のサービスのlogging移行が完了しました。

## 実施内容

### 1. logging.getLogger(__name__) → get_module_logger() への統一

全てのファイルで標準的な `logging.getLogger(__name__)` を `backend_shared.application.logging.get_module_logger()` に統一しました。

#### 移行対象ファイル (全8ファイル)

**UseCase層 (5ファイル)**
- `app/core/usecases/reports/generate_balance_sheet.py`
- `app/core/usecases/reports/generate_block_unit_price.py`
- `app/core/usecases/reports/generate_average_sheet.py`
- `app/core/usecases/reports/generate_management_sheet.py`
- `app/core/usecases/reports/generate_factory_report.py`

**Adapter層 (3ファイル)**
- `app/infra/adapters/filesystem_report_repository.py`
- `app/infra/adapters/repository/filesystem_report_repository.py`
- `app/infra/adapters/csv/pandas_csv_gateway.py`

#### 変更例
```python
# Before
import logging
logger = logging.getLogger(__name__)

# After
from backend_shared.application.logging import get_module_logger, create_log_context
logger = get_module_logger(__name__)
```

### 2. 既存のlogging基盤の確認

ledger_apiは既に以下の機能を使用していました:

#### 2.1 setup_logging()
- `app/main.py` で呼び出し済み
- JSON形式のログ出力
- Request ID自動付与
- Uvicorn統合

```python
# app/main.py より
from backend_shared.application.logging import setup_logging
setup_logging()
```

#### 2.2 RequestIdMiddleware
- Request ID (traceId) の自動付与
- X-Request-ID ヘッダーのフロントエンド公開

```python
from backend_shared.infra.adapters.middleware import RequestIdMiddleware
app.add_middleware(RequestIdMiddleware)
```

#### 2.3 統一エラーハンドリング
- ProblemDetails形式でのエラーレスポンス

```python
from backend_shared.infra.adapters.fastapi import register_error_handlers
register_error_handlers(app)
```

#### 2.4 アクセスログフィルタリング
- `/health` エンドポイントのログ抑制

```python
from backend_shared.infra.frameworks.logging_utils import setup_uvicorn_access_filter
setup_uvicorn_access_filter(excluded_paths=("/health",))
```

### 3. create_log_context() の使用状況

一部のファイルで既に構造化ログのヘルパーを使用:
- `generate_balance_sheet.py` - create_log_context 使用中
- その他のファイルでも今後活用可能

## ledger_api の特徴

### アーキテクチャ
ledger_apiはClean Architectureを採用:
- **Domain層**: ビジネスロジック、エンティティ
- **UseCase層**: アプリケーションフロー (帳票生成、PDF変換)
- **Adapter層**: CSV読み込み、ファイル保存、外部依存の実装
- **Port層**: 抽象インターフェース定義

### 主要機能
1. **帳票生成**
   - 工場日報 (Factory Report)
   - 搬出入収支表 (Balance Sheet)
   - 経営管理表 (Management Sheet)
   - 単価平均表 (Average Sheet)
   - ブロック単価計算 (Block Unit Price)

2. **CSV処理**
   - PandasベースのCSV読み込み
   - 型変換・バリデーション
   - backend_sharedのCSV処理機能を活用

3. **PDF生成**
   - ExcelテンプレートからのPDF変換
   - GCS (Google Cloud Storage) への保存
   - 署名付きURL生成

## 今後の推奨事項

### 1. TimedOperation の活用

帳票生成やPDF変換など時間のかかる処理での計測を推奨:

```python
from backend_shared.application.logging import TimedOperation

# 帳票生成の時間計測
with TimedOperation("generate_factory_report", logger=logger, threshold_ms=1000) as timer:
    result = factory_report_process(...)
    timer.add_context(rows=len(df))
```

### 2. 構造化ログの拡充

現在一部のUseCaseでf-string形式のログが使われています。構造化ログへの移行を推奨:

#### Before
```python
logger.info(f"工場日報生成開始: files={file_keys}, period={period_type}")
```

#### After
```python
logger.info(
    "工場日報生成開始",
    extra=create_log_context(
        operation="generate_factory_report",
        files=file_keys,
        period_type=period_type
    )
)
```

### 3. エラーログの構造化

```python
logger.error(
    "帳票生成エラー",
    extra=create_log_context(
        operation="generate_report",
        report_type="factory_report",
        error_type=type(e).__name__
    ),
    exc_info=True  # スタックトレース付き
)
```

### 4. UseCase デコレータの活用

`@log_usecase_execution` デコレータで自動ログ記録:

```python
from backend_shared.application.logging import log_usecase_execution

class GenerateFactoryReportUseCase:
    @log_usecase_execution(usecase_name="GenerateFactoryReport", log_args=True)
    def execute(self, shipment, yard, receive, period_type):
        # 自動的にログが記録される
        ...
```

## backend_shared との統合状況

### 既に活用中の機能
✅ `setup_logging()` - ログ基盤初期化
✅ `RequestIdMiddleware` - Request IDトレーシング
✅ `register_error_handlers()` - 統一エラーハンドリング
✅ `setup_uvicorn_access_filter()` - アクセスログフィルタリング
✅ `create_log_context()` - 構造化ログコンテキスト (一部)

### 今後活用可能な機能
⏳ `TimedOperation` - 時間計測コンテキストマネージャー
⏳ `@log_usecase_execution` - UseCaseログデコレータ
⏳ `@track_usecase_metrics` - メトリクス収集
⏳ `UseCaseMetrics` - メトリクス管理

## 利点

### 1. 統一されたログフォーマット
- 全サービス(core_api, ledger_api)で同一のログ形式
- JSON形式での構造化ログ
- Request ID による完全なリクエストトレーシング

### 2. 保守性の向上
- logging設定が1箇所に集約 (`backend_shared/application/logging.py`)
- 設定変更が全サービスに即座に反映
- センシティブ情報の自動除外

### 3. デバッグの容易性
- Request ID でログをフィルタリング可能
- 構造化ログで検索・集計が容易
- サービス間のリクエスト追跡が可能

### 4. マイクロサービス対応
- 複数サービス間での統一ログフォーマット
- 分散トレーシングの基盤として機能

## 残存課題

### 1. 構造化ログへの完全移行
現在、一部のUseCaseでf-string形式のログが残っています。
次回の作業で `create_log_context()` を使った構造化ログに移行します。

### 2. TimedOperation の導入
以下の処理で時間計測を追加すると有用:
- 帳票生成処理 (各 generate_* メソッド)
- PDF変換処理 (`convert_excel_to_pdf`)
- CSV読み込み・検証処理

### 3. UseCaseデコレータの適用
`@log_usecase_execution` を各UseCaseに適用することで、
自動的に実行ログ・エラーログ・実行時間が記録されます。

## 次のステップ

1. **rag_api, manual_api, ai_api への展開**: 残りのマイクロサービスへのlogging移行
2. **TimedOperationの導入**: 重い処理への時間計測追加
3. **構造化ログの拡充**: f-string形式からcreate_log_context()への移行
4. **UseCaseデコレータの適用**: @log_usecase_executionの全UseCase適用

## 関連ドキュメント
- `docs/20251202_LOGGING_MIGRATION_TO_BACKEND_SHARED.md`: core_api logging移行ドキュメント
- `backend_shared/docs/20251128_ERROR_HANDLING_GUIDE.md`: エラーハンドリングガイド
- `backend_shared/src/backend_shared/application/logging.py`: logging基盤実装

## 変更履歴
- 2024-12-02: 初版作成 - ledger_api全体でget_module_logger()への移行完了
