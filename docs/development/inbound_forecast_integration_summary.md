# Inbound Forecast API 統合完了報告

**日付**: 2025-12-15  
**担当**: GitHub Copilot  
**ブランチ**: `feat/integrate-inbound-forecast-api`

## 1. 実装概要

搬入量予測(inbound forecast)機能を既存Docker Compose環境に統合し、Clean Architectureに準拠したWorkerパターンで実装しました。

### 主な成果物

1. **Docker Compose統合** (✅ 完了)
   - `inbound_forecast_api`: 予測APIサービス (ポート8006)
   - `inbound_forecast_worker`: 予測ジョブ実行Worker (プロファイル: `forecast`)

2. **Clean Architecture適用** (✅ 完了)
   - Port/Adapter/UseCaseパターンで実装
   - 既存スクリプトをラップして段階的移行

3. **UseCase実装** (✅ 完了)
   - `RunInboundForecastJobUseCase` (core_api側)
   - `ExecuteDailyForecastUseCase` (inbound_forecast_api側)

4. **API統合** (🔄 部分的完了)
   - `POST /forecast/jobs/{job_id}/execute` エンドポイント追加
   - ジョブ作成エンドポイントに既存の検証バグあり

5. **Makefile targets** (✅ 完了)
   - `make forecast-help`: ヘルプ表示
   - `make forecast-dryrun`: 設定検証
   - `make forecast-run TARGET_DATE=YYYY-MM-DD`: 予測実行

## 2. アーキテクチャ

### ディレクトリ構造

```
app/backend/inbound_forecast_api/
├── app/
│   ├── core/                      # Clean Architecture: コア層
│   │   ├── domain/                # ドメインエンティティ
│   │   ├── ports/                 # 抽象インターフェース
│   │   │   └── prediction_port.py  # IPredictionExecutor
│   │   └── usecases/              # アプリケーションロジック
│   │       └── execute_daily_forecast_uc.py
│   └── infra/                     # インフラ層
│       └── prediction/
│           └── script_executor.py  # ScriptBasedPredictionExecutor
├── scripts/                       # 既存の予測スクリプト (レガシー)
│   └── daily_tplus1_predict.py
├── worker/                        # Worker実装
│   └── main.py                    # UseCase経由で予測実行
├── Dockerfile                     # マルチステージビルド
└── requirements.txt
```

### データフロー

```
[フロントエンド]
    ↓ POST /forecast/jobs/{job_id}/execute
[core_api]
    ↓ RunInboundForecastJobUseCase
[jobs.forecast_jobs テーブル]
    ↓ status: queued → running
[inbound_forecast_worker]
    ↓ ExecuteDailyForecastUseCase
    ↓ ScriptBasedPredictionExecutor
[daily_tplus1_predict.py]
    ↓ CSV出力
[/backend/output/tplus1_pred_*.csv]
    ↓ (TODO: DBへのUPSERT)
[forecast.predictions_daily テーブル]
```

## 3. 変更ファイル一覧

### 新規作成
- `app/backend/inbound_forecast_api/app/` (Clean Architecture層)
  - `__init__.py` (×7ファイル)
  - `core/ports/prediction_port.py`
  - `core/usecases/execute_daily_forecast_uc.py`
  - `infra/prediction/script_executor.py`
- `app/backend/inbound_forecast_api/.gitignore` (CSV出力を除外)
- `app/backend/inbound_forecast_api/worker/` (既存から大幅リファクタ)
  - `main.py` (UseCase使用に変更)
  - `README.md`
- `app/backend/core_api/app/core/usecases/forecast/run_inbound_forecast_job_uc.py`
- `docs/development/inbound_forecast_integration_summary.md` (本ファイル)

### 修正
- `docker/docker-compose.dev.yml` (2サービス追加)
- `env/.env.common` (INBOUND_FORECAST_API_BASE追加)
- `env/.env.local_dev` (DEV_INBOUND_FORECAST_API_PORT追加)
- `makefile` (forecast-*ターゲット追加)
- `app/backend/core_api/app/core/ports/forecast_port.py` (mark_running追加)
- `app/backend/core_api/app/infra/adapters/forecast/job_repository.py` (mark_running実装)
- `app/backend/core_api/app/config/di_providers.py` (get_run_inbound_forecast_job_uc追加)
- `app/backend/core_api/app/api/routers/forecast/router.py` (execute endpoint追加)
- `app/backend/inbound_forecast_api/Dockerfile` (app/コピー、PYTHONPATH設定)

## 4. 動作確認

### ✅ 成功したテスト

1. **Dry-run**
   ```bash
   make forecast-dryrun
   # ✅ Configuration valid
   ```

2. **Worker経由の予測実行**
   ```bash
   make forecast-run TARGET_DATE=2025-01-15
   # ✅ Job completed successfully: Forecast completed: /backend/output/tplus1_pred_20251215_135922.csv
   ```

3. **Clean Architecture層のインポート**
   ```bash
   docker compose ... run inbound_forecast_worker python -c "from app.core.usecases..."
   # ✅ Import OK
   ```

### 🔄 未完了/検証待ち

1. **ジョブ作成エンドポイント**
   - `POST /forecast/jobs` に既存の検証バグ
   - エラー: "予測期間は最低1日必要です（指定: 0日）"
   - 原因: target_from/target_toの期間計算ロジック
   - **TODO**: 既存UseCaseの検証ロジックを修正

2. **DB保存機能**
   - 現在はCSV出力のみ
   - **TODO**: CSV→`forecast.predictions_daily`へのUPSERT

3. **エンドツーエンドテスト**
   - UI→API→Worker→DB の完全フロー
   - **TODO**: ジョブ作成バグ修正後に実施

## 5. 使用方法

### 開発環境での起動

```bash
# 通常のサービス起動
make al-up

# 予測Worker起動（別ターミナル）
make forecast-run TARGET_DATE=2025-01-20
```

### 本番環境での運用

```bash
# VM_STG環境
TARGET_DATE=2025-01-20 make forecast-run ENV=vm_stg

# VM_PROD環境
TARGET_DATE=2025-01-20 make forecast-run ENV=vm_prod
```

### API経由での実行（修正後）

```bash
# 1. ジョブ作成
curl -X POST http://localhost:8003/core_api/forecast/jobs \
  -H "Content-Type: application/json" \
  -d '{"target_from": "2025-01-20", "target_to": "2025-01-21", "job_type": "daily"}'
# → {"id": 123, "status": "queued", ...}

# 2. ジョブ即座実行
curl -X POST http://localhost:8003/core_api/forecast/jobs/123/execute
# → {"id": 123, "status": "done", ...}
```

## 6. 前提条件・制約

### 必須データ
- `/backend/data/output/final_fast_balanced/model_bundle.joblib`
- `/backend/data/output/final_fast_balanced/res_walkforward.csv`

### 環境変数
- `DEV_INBOUND_FORECAST_API_PORT`: 8006 (local_dev)
- `INBOUND_FORECAST_API_BASE`: `http://inbound_forecast_api:8000`

### Docker Compose プロファイル
- Worker起動には `--profile forecast` が必要
- 通常起動では Worker は起動しない（オンデマンド実行想定）

## 7. 既知の問題

### 1. ジョブ作成エンドポイントの検証バグ
**症状**: target_from=target_toで期間0日エラー  
**影響**: フロントエンドからのジョブ作成が不可  
**回避策**: Worker経由で直接実行  
**修正予定**: 既存UseCaseの日付検証ロジックを修正

### 2. DB保存未実装
**症状**: CSV生成のみ、DBに保存されない  
**影響**: フロントエンドから予測結果を取得できない  
**回避策**: CSVを手動でインポート  
**修正予定**: ScriptBasedPredictionExecutorにDB保存機能追加

## 8. 今後の改善計画

### Phase 1: 基本機能修正（優先度: 高）
- [ ] ジョブ作成エンドポイントの検証バグ修正
- [ ] DB保存機能の実装
- [ ] エンドツーエンドテスト

### Phase 2: スクリプトのモジュール化（優先度: 中）
- [ ] `daily_tplus1_predict.py`をライブラリ化
- [ ] subprocess呼び出しから直接import
- [ ] エラーハンドリングの改善

### Phase 3: パフォーマンス最適化（優先度: 低）
- [ ] 予測結果のキャッシュ
- [ ] 並列処理対応
- [ ] メトリクス記録

## 9. Git コミット履歴

1. `71630d02`: Step 0-3 (調査、UseCase、Port/Repository、DI)
2. `bd0d6a86`: Clean Architecture リファクタリング
3. `1f20b6d7`: Step 4 (execute endpoint追加)

## 10. ロールバック手順

```bash
# ブランチ切り替え
git checkout main

# サービス再起動
make al-down ENV=local_dev
make al-up ENV=local_dev

# マイグレーション戻し（該当する場合）
# make al-db-downgrade-one ENV=local_dev
```

## 11. 参考ドキュメント

- [バックエンド開発規約](../conventions/backend/20251127_webapp_development_conventions_backend.md)
- [Worker README](../../app/backend/inbound_forecast_api/worker/README.md)
- [Forecast Port](../../app/backend/core_api/app/core/ports/forecast_port.py)

---

**次のアクション**:
1. ジョブ作成バグの修正 (別PR推奨)
2. DB保存機能の実装
3. フロントエンドの「予測実行ボタン」実装

**質問・問題があれば**: @koujiro に連絡
