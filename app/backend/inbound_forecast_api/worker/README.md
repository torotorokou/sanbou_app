# Inbound Forecast Worker

需要予測ジョブを実行するrun-to-completion型のworkerサービス。

## 📋 概要

- **方式**: run-to-completion（1回実行→終了）
- **入力**: モデルバンドル + 履歴データ
- **出力**: CSV（将来的にDB保存）
- **実行**: `docker compose run --rm inbound_forecast_worker`

## 🚀 実行方法

### 基本コマンド

```bash
# local_dev環境での実行
docker compose -f docker/docker-compose.dev.yml \
  --env-file env/.env.common \
  --env-file env/.env.local_dev \
  run --rm inbound_forecast_worker \
  python -m worker.main --job-type daily --target-date 2025-12-16
```

### Makefile経由（推奨）

```bash
# ヘルプ表示
make forecast-help ENV=local_dev

# 日次予測実行
make forecast-run ENV=local_dev TARGET_DATE=2025-12-16

# dry-run（バリデーションのみ）
make forecast-dryrun ENV=local_dev
```

## 🛠️ オプション

### `--job-type`
- 値: `daily` | `weekly` | `monthly`
- デフォルト: `daily`
- 説明: 予測ジョブの種類

### `--target-date`
- 形式: `YYYY-MM-DD`
- デフォルト: 翌日
- 説明: 予測対象日

### `--future-days`
- 値: 整数
- デフォルト: `1`
- 説明: 予測日数

### `--dry-run`
- 説明: バリデーションのみ実行（実際の予測は行わない）

## 📁 ファイル構成

```
app/backend/inbound_forecast_api/
├── worker/
│   ├── __init__.py
│   └── main.py              # メインエントリポイント
├── scripts/
│   ├── daily_tplus1_predict.py   # 既存の予測スクリプト
│   └── serve_predict_model_v4_2_4.py
├── data/
│   ├── input/               # 入力データ
│   └── output/              # モデルバンドル
│       └── final_fast_balanced/
│           ├── model_bundle.joblib
│           └── res_walkforward.csv
└── output/                  # 予測結果出力先
    └── tplus1_pred_*.csv
```

## 🔍 動作確認

### 1. 設定検証

```bash
docker compose -f docker/docker-compose.dev.yml \
  --env-file env/.env.common \
  --env-file env/.env.local_dev \
  run --rm inbound_forecast_worker \
  python -m worker.main --dry-run
```

**期待される出力:**
```
INFO - ============================================================
INFO - Inbound Forecast Worker Starting
INFO - Job Type: daily
INFO - Target Date: tomorrow
INFO - ============================================================
INFO - Dry run mode - configuration valid
```

### 2. 実際の予測実行

```bash
docker compose -f docker/docker-compose.dev.yml \
  --env-file env/.env.common \
  --env-file env/.env.local_dev \
  run --rm inbound_forecast_worker \
  python -m worker.main --job-type daily --target-date 2025-12-16
```

**期待される出力:**
```
INFO - Starting daily forecast: target_date=2025-12-16, future_days=1
INFO - Executing command: /usr/local/bin/python /backend/scripts/...
INFO - Prediction completed successfully
INFO - ✅ Job completed successfully: Prediction saved to /backend/output/...
```

### 3. 結果確認

```bash
# CSV出力の確認
docker compose -p local_dev exec inbound_forecast_api \
  ls -lh /backend/output/tplus1_pred_*.csv

# 内容確認
docker compose -p local_dev exec inbound_forecast_api \
  head /backend/output/tplus1_pred_<timestamp>.csv
```

## 🔄 既存APIとの関係

| サービス名 | 役割 | 起動方式 | ポート公開 |
|-----------|------|----------|----------|
| `inbound_forecast_api` | FastAPI サーバー（既存） | 常駐 | 8006 |
| `inbound_forecast_worker` | ジョブ実行（新規） | run-to-completion | なし |

- **共存**: 両方のサービスは独立して動作
- **切替**: 将来的にAPIから切り替え可能
- **影響**: 既存APIには影響なし

## ⚙️ 設定

### 必要なファイル
- モデルバンドル: `/backend/data/output/final_fast_balanced/model_bundle.joblib`
- 履歴CSV: `/backend/data/output/final_fast_balanced/res_walkforward.csv`

### 環境変数
- `TZ`: タイムゾーン（デフォルト: Asia/Tokyo）
- `PYTHONPATH`: Python モジュール検索パス（デフォルト: /backend）

## 🐛 トラブルシューティング

### エラー: Model bundle not found

```
ERROR - Configuration validation failed: Model bundle not found: /backend/data/output/...
```

**原因**: モデルファイルが存在しない

**対処**:
1. モデル学習を実行: `python scripts/train_daily_model.py`
2. またはバンドルファイルをボリュームマウント

### エラー: Prediction script timed out

```
ERROR - Prediction script timed out after 5 minutes
```

**原因**: 予測に5分以上かかった

**対処**:
1. タイムアウト値を増やす（`worker/main.py`の`timeout=300`を編集）
2. または軽量モデルに切り替え

## 🚧 今後の拡張

### Phase 1: DB保存（優先度: 高）
- [ ] `forecast.predictions_daily` テーブルにUPSERT
- [ ] Repository パターンで実装
- [ ] 冪等性保証（同じ日付は上書き）

### Phase 2: ジョブキュー連携（優先度: 中）
- [ ] `jobs.forecast_jobs` テーブルと連携
- [ ] ジョブステータス更新（queued → running → done/failed）
- [ ] Plan Worker との統合

### Phase 3: スケジュール実行（優先度: 低）
- [ ] cron または Airflow での定期実行
- [ ] 失敗時のリトライ機構
- [ ] アラート通知

## 📚 参考

- [既存スクリプト README](../README.md)
- [Clean Architecture ガイド](../../docs/conventions/CLEAN_ARCHITECTURE.md)
- [Docker Compose ドキュメント](../../../../docker/README.md)
