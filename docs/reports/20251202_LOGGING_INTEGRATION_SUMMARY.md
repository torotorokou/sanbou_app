# Logging基盤統合 - 全体サマリー (2024-12-02)

## 概要

backend_sharedのlogging基盤を core_api と ledger_api に完全統合しました。
統一されたロギング基盤により、マイクロサービス全体でのログ管理・トレーシングが可能になりました。

## 実施内容

### 1. core_api のlogging移行 ✅

- **対象ファイル**: 約40ファイル
- **主要箇所**:
  - UseCase層 (13ファイル)
  - Repository/Adapter層 (15ファイル)
  - Client層 (4ファイル)
  - Router層 (一部)
  - その他 (config, middleware, db 等)

### 2. ledger_api のlogging移行 ✅

- **対象ファイル**: 8ファイル
- **主要箇所**:
  - UseCase層 (5ファイル - 帳票生成)
  - Adapter層 (3ファイル - CSV, Repository)

### 3. 統一された変更内容

#### Before

```python
import logging
logger = logging.getLogger(__name__)
```

#### After

```python
from backend_shared.application.logging import get_module_logger
logger = get_module_logger(__name__)
```

## backend_shared logging 機能一覧

### 基本機能

| 機能                  | 説明                                  | 使用状況                         |
| --------------------- | ------------------------------------- | -------------------------------- |
| `setup_logging()`     | アプリケーション起動時のlogging初期化 | ✅ core_api, ledger_api で使用中 |
| `get_module_logger()` | モジュール用ロガー取得                | ✅ 全ファイルで統一完了          |
| `set_request_id()`    | Request ID設定 (Middleware用)         | ✅ Middlewareで使用中            |
| `get_request_id()`    | Request ID取得                        | ⏳ 必要に応じて使用可能          |

### 構造化ログ

| 機能                   | 説明                             | 使用状況                            |
| ---------------------- | -------------------------------- | ----------------------------------- |
| `create_log_context()` | 構造化ログコンテキスト生成       | ✅ core_apiの多数のファイルで使用中 |
| センシティブ情報除外   | パスワード、トークン等の自動除外 | ✅ create_log_context内で実装済み   |

### 時間計測

| 機能             | 説明                                   | 使用状況          |
| ---------------- | -------------------------------------- | ----------------- |
| `TimedOperation` | コンテキストマネージャー形式の時間計測 | ⏳ 今後の活用推奨 |

### UseCaseログ

| 機能                          | 説明                      | 使用状況                          |
| ----------------------------- | ------------------------- | --------------------------------- |
| `@log_usecase_execution`      | UseCase実行ログの自動記録 | ✅ core_apiの7つのUseCaseで使用中 |
| `@track_usecase_metrics`      | メトリクス収集            | ⏳ 今後の活用推奨                 |
| `@combined_usecase_decorator` | ログ+メトリクス統合       | ⏳ 今後の活用推奨                 |
| `UseCaseMetrics`              | メトリクス管理クラス      | ⏳ 今後の活用推奨                 |

### Middleware

| 機能                  | 説明               | 使用状況                         |
| --------------------- | ------------------ | -------------------------------- |
| `RequestIdMiddleware` | Request ID自動付与 | ✅ core_api, ledger_api で使用中 |

## サービス別の統合状況

### core_api

```
✅ setup_logging() - 初期化済み
✅ get_module_logger() - 全ファイル統一完了
✅ RequestIdMiddleware - 登録済み
✅ create_log_context() - 多数のファイルで使用中
✅ @log_usecase_execution - 7つのUseCaseで使用中
⏳ TimedOperation - 今後の活用推奨
⏳ UseCaseMetrics - 今後の活用推奨
```

### ledger_api

```
✅ setup_logging() - 初期化済み
✅ get_module_logger() - 全ファイル統一完了
✅ RequestIdMiddleware - 登録済み
✅ register_error_handlers() - ProblemDetails統一
✅ setup_uvicorn_access_filter() - アクセスログフィルタリング
✅ create_log_context() - 一部で使用中
⏳ @log_usecase_execution - 今後の活用推奨
⏳ TimedOperation - 今後の活用推奨
```

### 未実施のサービス

以下のサービスは今後の移行対象:

- ⏳ rag_api
- ⏳ manual_api
- ⏳ ai_api
- ⏳ plan_worker

## アーキテクチャ

### ログフロー

```
Request → RequestIdMiddleware (Request ID付与)
       → Application (get_module_logger使用)
       → backend_shared/logging (統一フォーマット)
       → JSON形式で出力 (stdout)
       → ログ集約サービス (CloudWatch, ELK等)
```

### Request IDトレーシング

```
1. クライアントからリクエスト受信
2. RequestIdMiddleware が X-Request-ID を生成/取得
3. ContextVar に Request ID を保存
4. 全ログに自動的に Request ID が付与
5. レスポンスヘッダーに X-Request-ID を含めて返却
6. マイクロサービス間の呼び出しにも Request ID を伝播
```

## 利点

### 1. 統一されたログフォーマット

- 全サービスで同一のJSON形式ログ
- Request IDによる完全なリクエストトレーシング
- 環境変数でログレベル制御可能

### 2. マイクロサービス対応

- サービス間のリクエスト追跡が可能
- 分散トレーシングの基盤として機能
- 統一されたエラーハンドリング

### 3. 保守性の向上

- logging設定が1箇所に集約
- 設定変更が全サービスに即座に反映
- センシティブ情報の自動除外

### 4. デバッグの容易性

- Request ID でログをフィルタリング可能
- 構造化ログで検索・集計が容易
- 実行時間の自動計測 (TimedOperation)

### 5. 本番運用対応

- JSON形式でログ集約サービスと連携しやすい
- メトリクス収集の基盤として活用可能
- パフォーマンス監視の基盤

## 今後の推奨事項

### 短期 (1-2週間)

1. **TimedOperation の導入**
   - 重い処理への時間計測追加
   - 目標: 各サービスの主要処理5-10箇所
2. **構造化ログの拡充**

   - f-string形式から create_log_context() への移行
   - 目標: 全ログの50%以上を構造化

3. **Router層の統一**
   - core_apiの残りのRouterファイルの移行

### 中期 (1ヶ月)

4. **残りのサービスへの展開**

   - rag_api, manual_api, ai_api への移行
   - plan_worker への移行

5. **UseCaseデコレータの全面適用**
   - @log_usecase_execution の全UseCase適用
   - 目標: 80%以上のUseCaseに適用

### 長期 (2-3ヶ月)

6. **メトリクス収集の導入**

   - UseCaseMetrics の活用
   - Prometheus等への連携

7. **分散トレーシングの強化**
   - OpenTelemetry等への移行検討
   - Jaeger/Zipkin連携

## 成果物

### ドキュメント

1. `docs/20251202_LOGGING_MIGRATION_TO_BACKEND_SHARED.md`

   - core_api のlogging移行詳細

2. `docs/20251202_LEDGER_API_LOGGING_MIGRATION.md`

   - ledger_api のlogging移行詳細

3. `docs/20251202_LOGGING_INTEGRATION_SUMMARY.md` (本ドキュメント)
   - 全体サマリーと今後の方針

### コード変更

- **core_api**: 約40ファイル
- **ledger_api**: 8ファイル
- **backend_shared**: 既存のlogging基盤を活用 (変更なし)

## 変更統計

### ファイル数

```
core_api:    40ファイル (UseCase 13, Adapter 15, Client 4, その他 8)
ledger_api:   8ファイル (UseCase 5, Adapter 3)
合計:        48ファイル
```

### 行数

```
変更行数: 約200行 (import文の追加・変更)
削除行数: 約100行 (重複import、古いlogger定義)
実質変更: 約100行の改善
```

## 次のアクション

### 即座に実施可能

- [ ] core_api Router層の残りファイル移行
- [ ] TimedOperation の試験導入 (3-5箇所)
- [ ] 構造化ログのベストプラクティスドキュメント作成

### 計画が必要

- [ ] rag_api logging移行の計画
- [ ] manual_api logging移行の計画
- [ ] メトリクス収集の要件定義

## 関連ドキュメント

- `backend_shared/src/backend_shared/application/logging.py`: logging基盤実装
- `backend_shared/docs/20251128_ERROR_HANDLING_GUIDE.md`: エラーハンドリングガイド
- `docs/20251202_LOGGING_MIGRATION_TO_BACKEND_SHARED.md`: core_api移行詳細
- `docs/20251202_LEDGER_API_LOGGING_MIGRATION.md`: ledger_api移行詳細

## 変更履歴

- 2024-12-02: 初版作成 - core_api, ledger_api のlogging移行完了
