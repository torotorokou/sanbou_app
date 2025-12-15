# Scripts リファクタリング計画

## 目的

Clean Architectureに準拠し、テスタブルで保守性の高いコードベースを構築する。

## 現状分析

### 問題点
1. CLIとビジネスロジックが混在（train_daily_model.py: 1200行超）
2. subprocess経由の実行による型安全性の欠如
3. テストが困難
4. コードの再利用性が低い

### 既存の主要スクリプト
- `daily_tplus1_predict.py` (94行) - t+1予測のCLIラッパー
- `train_daily_model.py` (1258行) - モデル学習のメインロジック
- `serve_predict_model_v4_2_4.py` - 推論実行
- `retrain_and_eval.py` - 再学習・評価パイプライン

## リファクタリング戦略

### Phase 1: 構造の整理 ✅完了
- api/, config/, shared/ の作成
- infra/adapters/ の整備

### Phase 2: サービス層の抽出 📍推奨
**目的**: ビジネスロジックをCLIから分離

```
infra/
  services/
    prediction/
      daily_prediction_service.py      # 日次予測サービス
      model_training_service.py        # モデル学習サービス
      inference_service.py             # 推論サービス
    gamma_recency/
      gamma_service.py                 # Gammaモデルサービス
    weekly_allocation/
      allocation_service.py            # 週次按分サービス
```

**メリット**:
- テストが容易になる
- 直接import可能（subprocess不要）
- 型安全性の確保
- コードの再利用性向上

**実装例**:
```python
# infra/services/prediction/daily_prediction_service.py
class DailyPredictionService:
    """日次予測の実行ロジック（CLIに依存しない）"""
    
    def __init__(self, model_bundle_path: Path):
        self.model_bundle_path = model_bundle_path
        self.model = None
    
    def load_model(self) -> None:
        """モデルバンドルを読み込む"""
        pass
    
    def predict(
        self, 
        start_date: date,
        future_days: int = 1,
        reserve_data: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """予測を実行して結果を返す"""
        pass
```

**移行パス**:
1. `train_daily_model.py`から`ModelTrainingService`クラスを抽出
2. `serve_predict_model_v4_2_4.py`から`InferenceService`を抽出
3. 既存スクリプトは薄いCLIラッパーとして残す（後方互換性）
4. 新しい`ServiceExecutor`を作成（subprocess不要）

### Phase 3: モデル管理の統合
**目的**: モデルバンドルの管理を一元化

```
infra/
  models/
    model_loader.py          # モデルの読み込みロジック
    model_registry.py        # モデルバージョン管理
    bundle_manager.py        # バンドルファイルの管理
```

### Phase 4: CLI層の最小化
**目的**: スクリプトを薄いエントリーポイントに

```python
# scripts/daily_tplus1_predict.py (リファクタリング後)
def main():
    args = parse_args()
    
    # サービスを使用
    service = DailyPredictionService(
        model_bundle_path=Path(args.bundle)
    )
    service.load_model()
    result = service.predict(
        start_date=args.start_date,
        future_days=1,
        reserve_data=load_reserve_data(args)
    )
    result.to_csv(args.out_csv)
```

## 優先順位

### 高優先度
1. **`train_daily_model.py`のリファクタリング** - 最も大きく複雑
2. **`serve_predict_model_v4_2_4.py`のサービス化** - API化に必須

### 中優先度
3. `gamma_recency_model.py`のサービス化
4. `weekly_allocation.py`のサービス化

### 低優先度（現状維持でOK）
5. 評価スクリプト群（eval_*.py）
6. ユーティリティスクリプト（update_daily_clean.py）

## マイグレーション例

### Before (現在)
```python
# adapter から subprocess で実行
cmd = ["python", "scripts/daily_tplus1_predict.py", ...]
subprocess.run(cmd)
```

### After (Phase 2完了後)
```python
# adapter から直接呼び出し
from app.infra.services.prediction import DailyPredictionService

service = DailyPredictionService(model_bundle_path)
result = service.predict(start_date, future_days=1)
```

## 次のステップ

1. `infra/services/prediction/daily_prediction_service.py` を作成
2. `train_daily_model.py` の主要クラスを抽出
3. 単体テストを作成
4. 既存のCLIスクリプトを薄いラッパーに書き換え
5. `ServiceExecutor` を作成して `ScriptBasedPredictionExecutor` から段階的に移行

## 参考: ディレクトリ構造（Phase 2完了後）

```
app/
  api/
  core/
  infra/
    adapters/
      prediction/
        script_executor.py       # レガシー（subprocess）
        service_executor.py      # 新実装（直接呼び出し）
    services/                    # ← NEW
      prediction/
        daily_prediction_service.py
        model_training_service.py
        inference_service.py
      gamma_recency/
      weekly_allocation/
    scripts/                     # 薄いCLIラッパーに
    models/                      # Phase 3で追加
  config/
  shared/
```
