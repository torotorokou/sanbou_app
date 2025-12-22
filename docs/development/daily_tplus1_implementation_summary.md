# DB→学習→t+1予測 実装完了レポート

**実装日**: 2025-12-18  
**実装者**: AI Assistant  
**目的**: forecast.forecast_jobs に daily_tplus1 を投入すると、DBからデータ取得→retrain_and_eval.py --quick で学習→結果DB保存まで自動実行

---

## 🎯 実装完了サマリー

### ✅ 完了した機能

1. **retrain_and_eval.py の引数拡張**
   - `--raw-csv`, `--reserve-csv`, `--out-dir`, `--pred-out-csv`, `--start-date` を追加
   - 既存挙動は完全に維持（デフォルト値で後方互換性保証）

2. **Ports & Adapters実装（Clean Architecture準拠）**
   - 3つのPort（抽象インターフェース）
   - 3つのAdapter（PostgreSQL実装）
   - core_api に配置、worker から参照

3. **workspace方式のジョブ実行**
   - `/tmp/forecast_jobs/{job_id}/` に作業用ファイル配置
   - raw.csv / reserve.csv 生成
   - retrain_and_eval.py 実行
   - 結果CSV読み込み→DB保存

4. **エラーハンドリング**
   - DB取得失敗 → job failed + last_error
   - 学習失敗 → job failed + run.log末尾を要約
   - 予測CSV不在 → job failed
   - Worker継続（1ジョブ失敗しても次に進む）

5. **E2E動作確認手順書**
   - ジョブ投入SQL
   - Workerログ確認方法
   - DB確認SQL
   - workspace確認コマンド
   - トラブルシューティング

---

## 📂 変更ファイル一覧

### 1. スクリプト変更

| ファイル | 変更内容 | 行数 |
|---------|---------|------|
| [app/backend/inbound_forecast_worker/scripts/retrain_and_eval.py](../app/backend/inbound_forecast_worker/scripts/retrain_and_eval.py) | 引数追加（5個）、パス制御ロジック変更 | +30 |

**追加引数**:
```python
--raw-csv <path>           # 学習入力CSV（伝票日付,品名,正味重量）
--reserve-csv <path>       # 予約CSV（予約日,台数,固定客）
--out-dir <dir>            # 出力ディレクトリ（bundle等）
--pred-out-csv <path>      # t+1予測結果CSV出力先
--start-date <YYYY-MM-DD>  # 予測基準日
```

### 2. core_api Ports（新規作成）

| ファイル | 役割 | 行数 |
|---------|------|------|
| [app/backend/core_api/app/core/ports/inbound_actuals_export_port.py](../app/backend/core_api/app/core/ports/inbound_actuals_export_port.py) | 品目別日次実績エクスポートの抽象化 | 42 |
| [app/backend/core_api/app/core/ports/reserve_export_port.py](../app/backend/core_api/app/core/ports/reserve_export_port.py) | 日次予約エクスポートの抽象化 | 41 |
| [app/backend/core_api/app/core/ports/daily_forecast_result_repository_port.py](../app/backend/core_api/app/core/ports/daily_forecast_result_repository_port.py) | 日次予測結果保存の抽象化 | 50 |

### 3. core_api Adapters（新規作成）

| ファイル | SQL対象 | 役割 | 行数 |
|---------|---------|------|------|
| [app/backend/core_api/app/infra/adapters/forecast/inbound_actuals_exporter.py](../app/backend/core_api/app/infra/adapters/forecast/inbound_actuals_exporter.py) | stg.shogun_final_receive | 品目別データ→CSV（kg→ton変換） | 66 |
| [app/backend/core_api/app/infra/adapters/forecast/reserve_exporter.py](../app/backend/core_api/app/infra/adapters/forecast/reserve_exporter.py) | mart.v_reserve_daily_for_forecast | 予約データ→CSV | 57 |
| [app/backend/core_api/app/infra/adapters/forecast/daily_forecast_result_repository.py](../app/backend/core_api/app/infra/adapters/forecast/daily_forecast_result_repository.py) | forecast.daily_forecast_results | 予測結果INSERT | 82 |

### 4. inbound_forecast_worker UseCase（新規作成）

| ファイル | 役割 | 行数 |
|---------|------|------|
| [app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast_with_training.py](../app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast_with_training.py) | DB→学習→予測のE2E実行 | 227 |

### 5. inbound_forecast_worker Executor（変更）

| ファイル | 変更内容 | 変更行数 |
|---------|---------|---------|
| [app/backend/inbound_forecast_worker/app/job_executor.py](../app/backend/inbound_forecast_worker/app/job_executor.py) | execute_daily_tplus1()に use_training=True 追加 | +103 |

---

## 🗂️ ディレクトリ構造

```
app/backend/
├── core_api/
│   ├── app/
│   │   ├── core/
│   │   │   └── ports/
│   │   │       ├── inbound_actuals_export_port.py       (新規)
│   │   │       ├── reserve_export_port.py                (新規)
│   │   │       └── daily_forecast_result_repository_port.py (新規)
│   │   └── infra/
│   │       └── adapters/
│   │           └── forecast/                             (新規ディレクトリ)
│   │               ├── __init__.py
│   │               ├── inbound_actuals_exporter.py       (新規)
│   │               ├── reserve_exporter.py               (新規)
│   │               └── daily_forecast_result_repository.py (新規)
│   └── migrations_v2/
│       └── alembic/
│           └── versions/
│               └── 20251218_001_add_daily_forecast_results_table.py (既存)
└── inbound_forecast_worker/
    ├── scripts/
    │   └── retrain_and_eval.py                          (変更)
    └── app/
        ├── application/
        │   └── run_daily_tplus1_forecast_with_training.py (新規)
        └── job_executor.py                               (変更)
```

---

## 📊 生成CSVサンプル

### raw.csv（学習用、日本語ヘッダ）

```csv
伝票日付,品名,正味重量
2024-12-19,混合廃棄物,1.234
2024-12-19,木くず,0.567
2024-12-19,プラスチック類,0.890
2024-12-20,混合廃棄物,2.345
2024-12-20,鉄くず,1.678
```

- **伝票日付**: YYYY-MM-DD形式
- **品名**: item_name
- **正味重量**: ton単位（kg→ton変換済み）

### reserve.csv（予約用、日本語ヘッダ）

```csv
予約日,台数,固定客
2025-11-28,45,30
2025-11-29,50,35
2025-11-30,48,32
2025-12-01,52,36
2025-12-02,47,31
```

- **予約日**: YYYY-MM-DD形式
- **台数**: reserve_trucks
- **固定客**: reserve_fixed_trucks

---

## 🔄 実行フロー図

```
┌─────────────────────────────────────────────────────────────┐
│ 1. ジョブ投入                                                │
│    INSERT INTO forecast.forecast_jobs                       │
│    (job_type='daily_tplus1', target_date=明日, status=...)  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Worker polling                                           │
│    job_poller.claim_next_job()                              │
│    → status: pending → processing                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. workspace作成                                            │
│    /tmp/forecast_jobs/{job_id}/                             │
│    ├── out/                                                 │
│    ├── run.log                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. DB→CSV エクスポート                                       │
│    InboundActualsExporter.export_item_level_actuals()       │
│    → stg.shogun_final_receive → raw.csv                     │
│                                                             │
│    ReserveExporter.export_daily_reserve()                   │
│    → mart.v_reserve_daily_for_forecast → reserve.csv        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. 学習→予測実行                                             │
│    subprocess.run([                                         │
│      "python3", "/backend/scripts/retrain_and_eval.py",     │
│      "--quick",                                             │
│      "--raw-csv", "{ws}/raw.csv",                           │
│      "--reserve-csv", "{ws}/reserve.csv",                   │
│      "--out-dir", "{ws}/out",                               │
│      "--pred-out-csv", "{ws}/tplus1_pred.csv",              │
│      "--start-date", "2025-12-19"                           │
│    ])                                                       │
│    → 処理時間: 約18分（--quickモード）                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. 結果CSV読み込み                                           │
│    pd.read_csv("{ws}/tplus1_pred.csv")                      │
│    → p50 = 45.123 (例)                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. DB保存                                                   │
│    DailyForecastResultRepository.save_result()              │
│    → INSERT INTO forecast.daily_forecast_results            │
│    (target_date, job_id, p50, unit, input_snapshot)         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. ジョブ完了                                                │
│    UPDATE forecast.forecast_jobs                            │
│    SET status='succeeded', completed_at=NOW()               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 E2E実行手順（クイック版）

### 1. ジョブ投入

```bash
cd /home/koujiro/work_env/22.Work_React/sanbou_app
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev <<'EOF'
INSERT INTO forecast.forecast_jobs (
    id, job_type, target_date, status, priority, input_snapshot, created_at
) VALUES (
    gen_random_uuid(), 'daily_tplus1', CURRENT_DATE + 1, 'pending', 10, '{}'::jsonb, CURRENT_TIMESTAMP
)
RETURNING id, job_type, target_date, status;
EOF
```

### 2. Workerログ監視

```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev logs -f inbound_forecast_worker
```

**期待ログ**: 
- `🚀 Starting daily t+1 forecast with training`
- `✅ Exported 12345 actuals`
- `✅ retrain_and_eval completed successfully`
- `✅ Saved prediction result to DB`

### 3. 結果確認

```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev <<'EOF'
SELECT 
    j.job_type,
    j.target_date,
    j.status,
    r.p50,
    r.unit,
    r.generated_at
FROM forecast.forecast_jobs j
LEFT JOIN forecast.daily_forecast_results r ON j.id = r.job_id
WHERE j.job_type = 'daily_tplus1'
ORDER BY j.created_at DESC
LIMIT 1;
EOF
```

**期待出力**:
```
job_type     | target_date | status    | p50    | unit | generated_at
-------------+-------------+-----------+--------+------+---------------------
daily_tplus1 | 2025-12-19  | succeeded | 45.123 | ton  | 2025-12-18 10:18:29
```

---

## ⚠️ 既知の課題と対応方針

| 課題 | 現状 | 対応方針 |
|------|------|---------|
| **処理時間** | --quick で約18分 | 初期実装はこれで許容、将来は学習を週次バッチ化 |
| **workspace蓄積** | /tmp配下に蓄積 | Phase 5で定期クリーンアップ実装 |
| **p10/p90未実装** | 区間予測なし | retrain_and_eval.py が対応していない、p50のみで運用 |
| **同時実行制御** | 複数ジョブ同時実行可能 | Phase 5でロック機構実装 |
| **データ不足エラー** | stg.shogun_final_receive が空 | 将軍CSVアップロード後に実行 |

---

## 📝 ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [daily_tplus1_db_to_retrain_and_eval_plan.md](daily_tplus1_db_to_retrain_and_eval_plan.md) | 事前調査・設計ドキュメント |
| [daily_tplus1_e2e_execution_guide.md](daily_tplus1_e2e_execution_guide.md) | E2E実行手順・トラブルシューティング |
| このファイル | 実装完了レポート |

---

## 🎓 設計判断の記録

### 1. なぜ core_api に Ports/Adapters を配置したか？

**理由**:
- `stg.shogun_final_receive` や `mart.v_reserve_daily_for_forecast` は core_api が管理
- core_api の DB接続を再利用
- 将来的に core_api の他のユースケースでも使える

### 2. なぜ retrain_and_eval.py を subprocess で呼ぶのか？

**理由**:
- 既存スクリプトの動作実績がある
- Python モジュールとして直接呼ぶと、グローバル変数やファイルI/O の依存が複雑
- Phase 4では「動く」ことを優先

**将来**:
- Phase 5で推論ロジックを Python モジュール化
- subprocess 廃止、メモリ内で完結

### 3. なぜ workspace を /tmp に配置したか？

**理由**:
- コンテナの再起動でクリーンアップされる
- デバッグ時にファイルを確認できる
- NFS等の永続ストレージを避ける（性能）

### 4. なぜ use_training=True をデフォルトにしたか？

**理由**:
- Phase 4の目的が「学習込みE2E」の実現
- 推論のみは既にPhase 3で実装済み
- デフォルトで新しい実装を使う

---

## 🚀 次のアクション

### Dev環境での検証（必須）

1. [ ] ジョブ投入
2. [ ] Workerログ確認
3. [ ] DB結果確認
4. [ ] workspace確認
5. [ ] エラーケース検証（データ不足、タイムアウト等）

### Stg環境での検証

1. [ ] --quick の精度確認
2. [ ] 負荷テスト（複数ジョブ投入）
3. [ ] 失敗時の挙動確認

### Prod運用準備

1. [ ] アラート設定（ジョブ失敗時）
2. [ ] workspaceクリーンアップスクリプト
3. [ ] 週次学習バッチの設計（フル学習）

---

**実装完了日**: 2025-12-18  
**実装バージョン**: Phase 4 - DB to Training E2E  
**次フェーズ**: Phase 5 - 運用改善（クリーンアップ、同時実行制御、区間予測）
