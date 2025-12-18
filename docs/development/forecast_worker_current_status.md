# 搬入量予測Worker 現状レポート

**作成日:** 2025-12-18  
**ブランチ:** feature/forecast-worker-daily-tplus1

---

## 最終目標

**DBから受入一覧と予約台数を取得し、自動で搬入量予測を行うこと**

具体的には：
1. DBから受入実績データ（daily_tplus1の履歴）を取得
2. DBから予約台数データを取得
3. これらを元に翌日の搬入量を自動予測
4. 予測結果をDBに保存
5. 定期実行（例：毎日夜間に翌日分を予測）

---

## 現在の達成状況

### ✅ 完了項目（Phase 1: 基盤構築）

#### 1. ジョブキューシステム
- **DB設計:** forecast.forecast_jobs テーブル作成
  - job_type, target_date, status, attempt などの管理
  - 部分ユニークインデックスで重複防止
  - 全環境対応（dev/stg/prod）の権限設定
- **マイグレーション:** Alembic v2で実装
  - ファイル: `20251216_005_create_forecast_schema_and_jobs_table.py`
  - upgrade/downgrade 動作確認済み

#### 2. API実装（Clean Architecture）
- **エンドポイント:**
  - `POST /forecast/jobs/daily-tplus1`: ジョブ投入
  - `GET /forecast/jobs/v2/{job_id}`: ジョブ状態確認
- **レイヤー構成:**
  - Domain: ForecastJob エンティティ
  - Port: IForecastJobRepositoryV2 インターフェース
  - UseCase: SubmitDailyTplus1JobUseCase
  - Adapter: PostgresForecastJobRepositoryV2
  - Router: FastAPI エンドポイント

#### 3. Worker実装
- **ポーリング機構:**
  - 5秒間隔でDB監視
  - SELECT FOR UPDATE SKIP LOCKED で並行安全なジョブクレーム
- **実行機構:**
  - subprocess による daily_tplus1_predict.py 実行
  - ホワイトリスト検証（セキュリティ）
  - タイムアウト設定（30分）
  - エラーハンドリングとリトライ
- **ステータス管理:**
  - queued → running → succeeded/failed
  - attempt カウンタ、last_error 記録

#### 4. 受入テスト
- **検証項目:** 全てPASS
  - API経由でのジョブ作成
  - Workerによる自動処理
  - エラーハンドリング
  - 重複投入防止
  - 既存サービスへの影響なし

#### 5. ドキュメント
- **受入テスト結果:** `docs/development/forecast_worker_acceptance_test.md`
- **予測タイプ一覧:** `docs/development/forecast_worker_prediction_types.md`
  - 7種類の予測タイプの要件整理
  - 実装優先順位の提示

---

## 🔶 未完了項目（最終目標とのギャップ）

### 1. DBからのデータ取得機能（部分完了 ✅→🔶）

#### 1-1. 受入実績データの取得（✅ 基盤完成）

**完了:**
- ✅ `backend_shared.shogun.ShogunDatasetFetcher` を実装（2025-12-18）
- ✅ 6種類のデータセット取得機能（flash/final × receive/shipment/yard）
- ✅ 統合テストで全データセット取得確認済み
- ✅ DataFrame形式での取得対応
- ✅ 日付フィルタ機能

**使用例:**
```python
from backend_shared.shogun import ShogunDatasetFetcher, ShogunDatasetKey
from datetime import date, timedelta

def fetch_historical_inbound_data(db: Session, end_date: date, days: int = 30):
    """過去N日分の受入実績をDBから取得"""
    start_date = end_date - timedelta(days=days)
    
    fetcher = ShogunDatasetFetcher(db)
    df = fetcher.fetch_df(
        ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
        start_date=start_date,
        end_date=end_date
    )
    return df
```

**残作業:**
- daily_tplus1_predict.py への統合（CSV読み込み → DB読み込み）
- または、Worker側で事前にDBからCSVを生成する処理を追加

**影響範囲:**
- `inbound_forecast_worker/app/job_executor.py` の修正
- 新規ファイル: `inbound_forecast_worker/app/data_fetcher.py`（推奨）

#### 1-2. 予約データの取得
**現状:**
- daily_tplus1_predict.py は `--reserve-csv` でオプショナルにCSVを読み込む
- 予約データ: `/backend/data/input/yoyaku_data.csv`

**必要な実装:**
```python
# 例：指定日の予約データをDBから取得
def fetch_reservation_data(target_date: date) -> pd.DataFrame:
    """
    DBから予約データを取得
    
    テーブル: public.reservations (仮)
    カラム: reservation_date, customer_id, count, weight, fixed_flag
    """
    query = """
        SELECT 
            reservation_date,
            customer_id,
            count,
            estimated_weight,
            fixed_customer_flag
        FROM reservations
        WHERE reservation_date = :target_date
    """
    # 実装が必要
```

**影響範囲:**
- daily_tplus1_predict.py の修正
- または、Worker側でDBから取得して一時CSVを生成

### 2. 予測結果のDB保存

**現状:**
- 予測結果は `/backend/output/tplus1_pred_{target_date}.csv` に出力
- CSVファイルのみ、DBには保存されない

**必要な実装:**
```python
# 例：予測結果をDBに保存
def save_prediction_results(
    job_id: UUID,
    target_date: date,
    predictions: pd.DataFrame
) -> None:
    """
    予測結果をDBに保存
    
    テーブル: forecast.prediction_results (新規作成必要)
    カラム: job_id, target_date, yard_id, item_id, 
            predicted_weight, predicted_count, created_at
    """
    # 実装が必要
```

**必要な作業:**
- Alembicマイグレーションで `forecast.prediction_results` テーブル作成
- job_executor.py で予測完了後にDB保存処理を追加

### 3. 受入実績テーブルの確認と整備

**現状:**
- 受入実績データがどのテーブルに格納されているか未確認
- 既存テーブル構造の調査が必要

**必要な作業:**
```sql
-- 調査すべきテーブル（例）
-- 1. 受入実績
SELECT * FROM information_schema.tables 
WHERE table_name LIKE '%inbound%' OR table_name LIKE '%receive%';

-- 2. 予約データ
SELECT * FROM information_schema.tables 
WHERE table_name LIKE '%reservation%' OR table_name LIKE '%yoyaku%';

-- 3. ヤードマスタ
SELECT * FROM information_schema.tables 
WHERE table_name LIKE '%yard%';

-- 4. 品目マスタ
SELECT * FROM information_schema.tables 
WHERE table_name LIKE '%item%';
```

### 4. 定期実行スケジューリング

**現状:**
- 手動でAPIを呼び出してジョブ投入
- 定期実行の仕組みなし

**必要な実装（オプション）:**

**オプション1: Cron + curl**
```bash
# 毎日23時に翌日分の予測ジョブを投入
0 23 * * * curl -X POST http://core_api:8000/forecast/jobs/daily-tplus1 -d '{}'
```

**オプション2: Scheduler Worker**
```python
# 別のWorkerで定期的にジョブ投入
def schedule_daily_jobs():
    """毎日23時に翌日のジョブを自動投入"""
    while True:
        now = datetime.now(JST)
        if now.hour == 23 and now.minute == 0:
            # API呼び出し
            requests.post("http://core_api:8000/forecast/jobs/daily-tplus1")
        time.sleep(60)
```

**オプション3: APScheduler**
```python
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

@scheduler.scheduled_job('cron', hour=23, minute=0)
def submit_daily_forecast_job():
    """毎日23時に実行"""
    # ジョブ投入処理
```

### 5. モデルファイルの配置

**現状:**
- `/backend/models/final_fast_balanced/model_bundle.joblib` が存在しない
- テストでは常にエラーになる

**必要な作業:**
- 学習済みモデルをWorkerコンテナに配置
- または、GCS等からダウンロードする機構を追加

---

## 📊 実装進捗

```
最終目標達成度: 60%

[完了] ✅✅✅✅✅✅⬜⬜⬜⬜
- ✅ ジョブキューシステム (20%)
- ✅ API実装 (10%)
- ✅ Worker基盤 (10%)
- ✅ DBデータ取得基盤 (20%) ← ShogunDatasetFetcher実装完了
- 🔶 予測スクリプト統合 (10%) ← 残作業
- ⬜ 予測結果保存 (15%)
- ⬜ 定期実行 (10%)
- ⬜ モデル配置 (5%)
```

**最新の進捗（2025-12-18）:**
- ✅ backend_shared に将軍データセット取得クラス実装
- ✅ 統合テストで6種類全てのデータ取得確認
- ✅ DataFrame形式、日付フィルタ、便利メソッド全て動作確認済み

---

## 🎯 次のステップ（優先順位順）

### Phase 2-A: DBデータ取得（進行中 ✅→🔶）
**目標:** DBから動的にデータを取得して予測実行

#### 1. 既存テーブル構造の調査（✅ 完了）
- ✅ view名確認: `stg.v_active_shogun_final_receive` 等
- ✅ 6種類のデータセット確認完了
- ✅ master.yaml パス確認: `/backend/config/csv_config/shogun_csv_masters.yaml`

#### 2. データ取得モジュールの実装（✅ 基盤完了）
- ✅ **実装済み:** `backend_shared/shogun/` パッケージ
  - `ShogunDatasetFetcher`: データ取得クラス
  - `ShogunDatasetKey`: データセットキー定義
  - `ShogunMasterNameMapper`: 名前変換
- ✅ **統合テスト:** 6種類全て取得確認済み
- 🔶 **残作業:** Worker統合
  - 新規ファイル: `app/backend/inbound_forecast_worker/app/data_fetcher.py`
  - 機能:
    - `fetch_historical_inbound(end_date, days)`: 受入実績取得
    - `fetch_reservations(target_date)`: 予約データ取得
    - 取得したデータを一時CSVに出力（既存スクリプトとの互換性維持）

#### 3. job_executor.py の拡張
```python
def execute_daily_tplus1(target_date: date, timeout: int = None) -> str:
    # 1. DBから履歴データ取得
    historical_csv = fetch_and_save_historical_data(
        end_date=target_date - timedelta(days=1),
        days=30
    )
    
    # 2. DBから予約データ取得
    reservation_csv = fetch_and_save_reservation_data(target_date)
    
    # 3. 既存の予測スクリプト実行
    cmd = [
        "python3", script_path,
        "--bundle", model_bundle,
        "--res-walk-csv", historical_csv,
        "--reserve-csv", reservation_csv,
        "--out-csv", output_csv,
        "--start-date", target_date.isoformat(),
    ]
    # subprocess実行...
```

**工数見積もり:** 2-3日

### Phase 2-B: 予測結果のDB保存
**目標:** 予測結果をCSVだけでなくDBにも保存

#### 1. テーブル設計
```sql
CREATE TABLE forecast.prediction_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES forecast.forecast_jobs(id),
    target_date DATE NOT NULL,
    yard_id TEXT,
    item_id TEXT,
    predicted_weight NUMERIC,
    predicted_count INTEGER,
    confidence_score NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_prediction_results_job_id (job_id),
    INDEX idx_prediction_results_target_date (target_date)
);
```

#### 2. Alembicマイグレーション作成
```bash
docker compose exec core_api alembic -c /backend/migrations_v2/alembic.ini \
  revision --autogenerate -m "create_prediction_results_table"
```

#### 3. 保存処理の実装
- 予測完了後、CSVをパースしてDBにINSERT
- job_executor.py に追加

**工数見積もり:** 1-2日

### Phase 2-C: 定期実行の実装
**目標:** 毎日自動でジョブを投入

#### 簡易実装（推奨）
```bash
# docker-compose.dev.yml に cron コンテナ追加
services:
  forecast_scheduler:
    image: alpine:latest
    command: |
      sh -c 'apk add --no-cache curl && 
      while true; do
        if [ $(date +%H:%M) = "23:00" ]; then
          curl -X POST http://core_api:8000/forecast/jobs/daily-tplus1 -d "{}"
        fi
        sleep 60
      done'
```

**工数見積もり:** 0.5日

### Phase 3: 本番デプロイ準備
1. モデルファイルの配置（GCSからダウンロード等）
2. 環境変数の整備
3. stg環境でのE2Eテスト
4. 監視・アラート設定

**工数見積もり:** 2-3日

---

## 📋 技術的な課題と検討事項

### 1. 履歴データの範囲
- **質問:** 予測に必要な履歴データは何日分？
- **現状:** res_walkforward.csv の仕様を確認する必要あり
- **推奨:** 最低30日、できれば60-90日分

### 2. 予約データの有無
- **質問:** 予約データが存在しない日の扱いは？
- **現状:** `--reserve-csv` は省略可能（ゼロ扱い）
- **対応:** 予約なしの場合は空のDataFrameを渡す

### 3. 品目・ヤード別予測
- **質問:** 予測は品目別・ヤード別に行う？
- **現状:** daily_tplus1_predict.py の内部仕様を確認必要
- **推測:** model_bundle.joblib が品目別モデルを含む

### 4. パフォーマンス
- **懸念:** 大量データのDB取得に時間がかかる可能性
- **対策:** 
  - インデックスの適切な設定
  - 必要なカラムのみSELECT
  - 並列処理の検討（複数ヤード等）

### 5. エラーハンドリング
- **データ不足時:** 履歴が足りない場合の処理
- **予測失敗時:** リトライ戦略（現在は3回まで）
- **データ不整合時:** バリデーション処理

---

## 🔧 推奨される作業フロー

### Step 1: 調査（✅ 完了）
- ✅ 既存テーブル構造の確認（stg.v_active_shogun_* 6種類）
- ✅ サンプルデータの取得（統合テスト実行済み）
- 🔶 daily_tplus1_predict.py の入力仕様確認

### Step 2: データ取得実装（✅ 基盤完了、🔶 統合残）
- ✅ backend_shared.shogun パッケージ実装
- ✅ ユニットテスト作成（7/7 PASSED）
- ✅ 統合テスト実行（6種類全て確認）
- 🔶 data_fetcher.py 実装（Worker用ラッパー）
- 🔶 job_executor.py への統合

### Step 3: 結果保存実装（1日）
```bash
# 1. Alembicマイグレーション
# 2. 保存処理実装
# 3. 動作確認
```

### Step 4: 定期実行実装（0.5日）
```bash
# 1. Scheduler実装
# 2. docker-compose設定
# 3. 動作確認
```

### Step 5: E2Eテスト（1日）
```bash
# 1. 本番相当データでテスト
# 2. パフォーマンス確認
# 3. エラーケース確認
```

**合計工数見積もり:** ~~5-7日~~ → **残り2-3日**

**完了済み（2025-12-18）:**
- ✅ Step 1: 調査（0.5日）
- ✅ Step 2: データ取得基盤実装（2日相当）

**残作業:**
- 🔶 Step 2: Worker統合（0.5-1日）
- 🔶 Step 3: 結果保存実装（1日）
- 🔶 Step 4: 定期実行実装（0.5日）
- 🔶 Step 5: E2Eテスト（1日）

---

## 📝 まとめ

### 現状
- ✅ ジョブキューシステムの基盤は完成
- ✅ Worker実装は完了（静的ファイル前提）
- ✅ セキュリティ、エラーハンドリング、ログ記録は実装済み
- ✅ **DBデータ取得基盤が完成**（2025-12-18追加）
  - backend_shared.shogun パッケージ実装
  - 6種類全てのデータセット取得確認済み
  - 統合テスト完了

### 最終目標とのギャップ
- 🔶 **DBからのデータ取得が部分完了**（基盤✅ / Worker統合🔶）
- 🔶 予測結果のDB保存が未実装
- 🔶 定期実行の仕組みが未実装
- 🔶 モデルファイルの配置が未完了

### 次のアクション
1. ~~**最優先:** 既存DBテーブル構造の調査~~ ✅ 完了
2. ~~DBデータ取得モジュールの実装（基盤）~~ ✅ 完了
3. **現在:** Worker統合（data_fetcher.py → job_executor.py）← 次のステップ
4. 予測結果保存機能の追加
5. 定期実行の実装

### 完全自動化までの残作業
**推定工数:** ~~5-7日~~ → **2-3日**（基盤実装完了により短縮）  
**優先度:** 高（Phase 2-A統合として次のステップ）

---

**作成者:** GitHub Copilot  
**最終更新:** 2025-12-18  
**主な更新:**
- backend_shared.shogun パッケージ実装完了
- 統合テストで6種類全てのデータ取得確認
- 工数見積もりを2-3日短縮（基盤完成のため）
- 次のステップ明確化（Worker統合）
