# 日次予測モデル精度劣化問題調査プロンプト

## 問題の概要
日次予測モデルの精度が異常に悪い状態が続いています：
- **現在の精度**: R2=-0.617, MAE=29,918kg（ランダム予測より悪い）
- **期待精度**: R2=0.82程度, MAE=9,935kg程度（旧コンテナ環境）
- **症状**: reserve_sumに台数を使用するよう修正したが、結果が全く変わらない

## 背景
1. **DB設計変更**: 予約データにcustomer_count列（企業数）を追加
2. **修正内容**: preprocess_reserve関数で以下を修正
   - reserve_count: 企業数（total_customer_count）を使用 ✅
   - **reserve_sum: 台数（reserve_trucks）を使用** ← これが重要
   - fixed_ratio: 固定客企業数 / 総企業数 ✅

3. **検証結果**:
   - 単体テスト: 正しく動作（2024-05-01の例: reserve_count=66, reserve_sum=87, fixed_ratio=0.515）
   - E2Eテスト: 結果変わらず（R2=-0.617のまま）

## これまでの対応
1. ✅ preprocess_reserve関数修正（3ファイル: db_loader.py, train_daily_model.py, serve_predict_model_v4_2_4.py）
2. ✅ Pythonキャッシュクリア（.pyc, __pycache__削除）
3. ❌ 結果変わらず

## 重要な情報
- **前のコンテナ**: `python3 ./scripts/retrain_and_eval.py --quick` で正常に動作していた
- **現在のコンテナ**: 同じコマンドで実行しても精度が異常に悪い
- **データの違い**: 前はCSV読み込み、現在はDB直接取得（`--use-db`）

## 調査依頼事項
以下を包括的に調査して、なぜ修正が反映されないのか特定してください：

### 1. データ取得の検証
```bash
# db_loader.pyが正しいデータを返しているか確認
# 特に: reserve_trucks（台数）とtotal_customer_count（企業数）の両方が含まれているか
```
ファイル: `/home/koujiro/work_env/22.Work_React/sanbou_app/app/backend/inbound_forecast_worker/scripts/db_loader.py`
- 関数: `load_reserve_from_db()` (lines 190-230)
- 期待: reserve_trucks, total_customer_count, fixed_customer_count列を全て返す

### 2. 列マッピングの検証
```bash
# _auto_map_columns2関数が正しく列をマッピングしているか
# 特に: "count"列が"台数"ではなく"reserve_trucks"にマッピングされるべき
```
ファイル: `/home/koujiro/work_env/22.Work_React/sanbou_app/app/backend/inbound_forecast_worker/scripts/train_daily_model.py`
- 関数: `preprocess_reserve()` (lines 263-326)
- 行263のcmap変数で列マッピングを確認
- デバッグログを追加済み（行296-299）

### 3. preprocess_reserve関数の実行パスの検証
```bash
# この関数が本当に呼ばれているか確認
# 別のコードパス（古い実装）が使われている可能性はないか
```
- grep検索: `preprocess_reserve`を含む全ての関数定義と呼び出し
- 複数のpreprocess_reserve関数が存在する可能性

### 4. 前のコンテナとの差分
```bash
# 以下のファイルについて、コミットログまたはgit diffで違いを確認
```
- db_loader.py (commit: 348c8b8d)
- train_daily_model.py (commit: 348c8b8d)
- serve_predict_model_v4_2_4.py (commit: 348c8b8d)

### 5. 実行時のデバッグログ取得
```bash
# train_daily_model.pyにデバッグログを追加して実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec inbound_forecast_worker \
  python3 /backend/scripts/retrain_and_eval.py \
    --quick \
    --use-db \
    --db-connection-string "postgresql+psycopg://sanbou_app_dev:rwT8ovWmhwLctRNuPynH4jOoYSwXvVvc2czeGC0Zos4=@db:5432/sanbou_dev" \
    --actuals-start-date 2024-05-01 \
    --actuals-end-date 2025-12-16 \
    --start-date 2025-12-17 \
    --end-date 2025-12-17 \
    --out-dir /backend/output \
    --pred-out-csv /backend/output/tplus1_pred.csv \
    --log /backend/output/retrain_smoke.out 2>&1 | grep -E "(DEBUG|Column mapping|First 3 rows)"
```

### 6. 期待される出力
デバッグログで以下を確認:
```
[DEBUG preprocess_reserve] Column mapping: {'date': '予約日', 'count': 'reserve_trucks', 'fixed': 'fixed_customer_count', 'customer_count': 'total_customer_count'}
```
- `'count': 'reserve_trucks'` となっているべき（台数）
- `'count': '台数'` や `'count': 'total_customer_count'` だと間違い

## 関連ファイル
- `/home/koujiro/work_env/22.Work_React/sanbou_app/app/backend/inbound_forecast_worker/scripts/db_loader.py`
- `/home/koujiro/work_env/22.Work_React/sanbou_app/app/backend/inbound_forecast_worker/scripts/train_daily_model.py`
- `/home/koujiro/work_env/22.Work_React/sanbou_app/app/backend/inbound_forecast_worker/scripts/serve_predict_model_v4_2_4.py`
- `/home/koujiro/work_env/22.Work_React/sanbou_app/app/backend/inbound_forecast_worker/scripts/retrain_and_eval.py`
- `/home/koujiro/work_env/22.Work_React/sanbou_app/docker/docker-compose.dev.yml`

## 最終目標
修正が反映されない根本原因を特定し、R2=0.82程度、MAE=9,935kg程度の精度を達成する。