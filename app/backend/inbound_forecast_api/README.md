# Inbound Forecast API

需要予測サービス - 日次/週次/月次の予測を提供するFastAPIアプリケーション。

## ディレクトリ構造

Clean Architecture / Hexagonal Architecture に準拠した構造：

```
app/
  main.py              # アプリケーションエントリーポイント
  api/                 # API層（FastAPI）
    routers/           # FastAPIルーター
      prediction.py    # 予測関連エンドポイント
    schemas/           # リクエスト/レスポンスモデル
      prediction.py    # Pydanticモデル
  core/                # コアビジネスロジック
    domain/            # ドメインエンティティ
      prediction/      # 予測関連ドメイン
    ports/             # 抽象インターフェース
      prediction_port.py
    usecases/          # アプリケーションロジック
      execute_daily_forecast_uc.py
  infra/               # インフラ層
    adapters/          # ポートの具体実装
      prediction/      # 予測実行アダプター
        script_executor.py
    scripts/           # 実行スクリプト（既存）
      daily_tplus1_predict.py
      train_daily_model.py
      retrain_and_eval.py
      ...
  config/              # 設定・DI
    di_providers.py    # DIコンテナ
  shared/              # ローカル共通処理
```

## 構成概要

主なスクリプトと重要ファイルは次の通りです。

- `scripts/retrain_and_eval.py`
   - 日次モデルの再学習→評価→推論を一括で実行するラッパー（短時間の "--quick" モードあり）。
- `scripts/train_daily_model.py`
   - 生データ（`data/input/01_daily_clean.csv` と `data/input/yoyaku_data.csv`）から日次モデルを再学習。
- `scripts/serve_predict_model_v4_2_4.py`, `scripts/daily_tplus1_predict.py`
   - 学習済み日次バンドルから t+1 / t+7 予測を実行。
- `scripts/weekly_allocation/weekly_allocation.py`, `scripts/weekly_allocation/allocate_monthly_to_weekly_from_blend.py`
   - 月次予測（Gamma + ブレンド）の月合計を、過去の月内週別構成比で按分する週次モデル。
- `scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py`
   - 月次着地予測モジュール（Gamma/Poisson版）。
   - 第1〜2週（および21日）実績から月合計を推定します。
   - 詳細は `README_monthly_landing_gamma_poisson.md` を参照。
- `run_monthly_landing_pipeline.sh`
   - 月次着地モデルの一括実行スクリプト（データ作成〜学習〜推論）。
- `scripts/gamma_recency_model/gamma_recency_model.py`
   - Gamma Recency ベースの月次モデル本体（再学習・評価・将来予測）。
- `scripts/gamma_recency_model/blend_lgbm.py`
   - Gamma 出力に対する Ridge/LGBM ブレンドモデル（再学習・評価・将来予測）。

データと出力の配置は次の通りです。

- 入力
   - `data/input/01_daily_clean.csv` : 日次実績データ
   - `data/input/01_daily_clean_with_date.csv` : 日次実績の別バージョン（あれば自動で利用）
   - `data/input/yoyaku_data.csv` : 予約情報
   - `data/input/20240501-20250422.csv` : 月次着地モデル用の生データ
- 出力
   - 日次: `data/output/final_fast_balanced/`
   - 週次: `data/output/gamma_recency_model/weekly_allocated_forecast.csv`
   - 月次 Gamma/ブレンド: `data/output/gamma_recency_model/`

## 前提（実行環境）

- dev container `/works` 内での実行を想定しています。
- `cd /works/data/submission_release_20251027` をカレントディレクトリとしてください。
- Python 依存は本フォルダの `requirements.txt` に準拠している前提です。
   - 必要に応じて `pip install -r requirements.txt` を実行してください。
- Gamma / ブレンド / 月次着地 / 日次モデルは、**本フォルダ配下のスクリプトのみで再学習〜推論まで完結**します。

## 既定設定（重要）

- 週次: 月次（Gamma+ブレンド）の月合計を、過去の月内週別構成比で按分
- 月次着地: Gamma-Poisson モデル（日次累積 + カレンダー要因）。既定は以下
   - 14日時点予測: 月初〜14日までの実績を使用
   - 21日時点予測: 月初〜21日までの実績を使用
   - 評価期間: 2024年以降のバックテスト
   - 精度参考値（14日時点）: MAE ≈ 56.3 ton, MAPE ≈ 2.44%

## 推奨実行順序

1. 日次モデルの再学習
2. 月次 Gamma + ブレンドの再学習＋将来予測
3. 週次モデル（Gamma+ブレンド月次予測の按分）による週次推論
4. 月次着地モデル（第1〜2週から月合計）の評価・単月推論

以下、代表的なコマンドだけを抜粋しています。全コマンドは `コマンド一覧.txt` を参照してください。

### 1. 日次モデル

#### クイック・スモーク実行（低負荷）

```bash
python3 ./scripts/retrain_and_eval.py --quick
```

- bootstrap 回数を絞った短時間の再学習＋評価を実行します。
- ログ出力: `./output/retrain_smoke.out`

#### フル再学習

```bash
python3 ./scripts/retrain_and_eval.py
```

- 十分な計算資源がある場合に使用します。
- オプション: `--bootstrap-iters`, `--n-jobs` など（詳細はスクリプトの `--help` を参照）。

### 2. 月次 Gamma / ブレンドモデル（submission 内で完結）

#### Gamma Recency モデルの再学習＋将来予測

```bash
python3 ./scripts/gamma_recency_model/gamma_recency_model.py
```

#### Gamma 出力に対する Ridge/LGBM ブレンドモデルの再学習＋将来予測

```bash
python3 ./scripts/gamma_recency_model/blend_lgbm.py
```

実行後、`data/output/gamma_recency_model/` に次が生成/更新されます。

- `prediction_results.csv` : Gamma 本体のテスト期間予測と指標
- `future_forecast.csv` : Gamma 本体による将来予測
- `blended_prediction_results.csv` : ブレンドモデルのテスト期間予測と指標
- `blended_future_forecast.csv` : ブレンドモデルによる将来予測

### 3. 週次モデル（Gamma+ブレンド月次予測の按分）

週次モデルは、日次残差スタックではなく **月次予測（Gamma + ブレンド）の月合計を週別構成比で按分する単純化モデル** を採用しています。

1. 上記「月次 Gamma / ブレンドモデル」を実行して、`blended_future_forecast.csv`（将来予測）を生成します。
2. 過去実績から月内週別構成比を推定し、月次予測を週次に按分します。

```bash
./run_weekly_allocation.sh
```

評価時の注意点:

- **週次精度評価は `blended_prediction_results.csv`（実績付き期間）を用います。**
- actual が存在しない将来期間（`blended_future_forecast.csv` のみの範囲）は評価対象に含めません。
- 小さすぎる週を除外して MAPE を安定化させたい場合、
  `scripts/weekly_allocation/evaluate_weekly_allocation.py` の `--min-actual` オプションで
  「weekly_actual が閾値以上の週」に絞って評価できます（例: `--min-actual 100`）。

代表的なコマンドは `コマンド一覧.txt` の[月次モデル]および[週次モデル（按分）]セクションを参照してください。

### 4. 月次着地予測モデル（第1〜2週から月合計を推定）

**最新の Gamma/Poisson モデル** を採用しています。
詳細は `README_monthly_landing_gamma_poisson.md` を参照してください。

#### 一括実行（データ作成・学習・推論）

提出用フォルダ直下のシェルスクリプトで、全工程を一括実行できます。

```bash
./run_monthly_landing_pipeline.sh
```

- **データ作成**: `data/input/01_daily_clean.csv` -> `data/output/monthly_features.csv`
- **学習**: 14日版・21日版モデルを学習し `models/` に保存
- **推論**: 保存済みモデルで推論し `output/` に結果出力

#### 個別実行（スクリプト直接実行）

```bash
# 21日版モデルの学習と保存
python3 scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv data/output/monthly_features.csv \
  --use-a21 \
  --save-model models/monthly_landing_poisson_21d.pkl
```

※ 旧来の線形回帰モデル（`scripts/monthly_landing/`）は `backups/` に退避されています。

## 注意事項

- 単位（kg / ton）の扱いはスクリプト内で統一されていますが、
   評価時には入力 CSV 側の列名・単位が仕様通りであることを確認してください。
- 本パッケージは“最小構成”の配布物です。重いモデル本体（大きな `.pkl` / `.joblib` など）は含めていません。
   - 必要に応じて、学習済みモデルアーティファクトを `data/output/...` に追加してください。

## 問い合わせ

- 本フォルダ内スクリプトのメンテナ（担当者）にお問い合わせください。