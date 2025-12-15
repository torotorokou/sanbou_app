# Inbound Forecast API リファクタリング計画

- 日付: 2025-12-15
- ブランチ: refactor/inbound-forecast-api-structure
- 目的: core_apiと同じClean Architectureパターンへの統一

---

## 1. 現状分析

### 1-1. 現在の構造
```
app/backend/inbound_forecast_api/app/
  core/
    domain/
      __init__.py              ← 空（エンティティが未定義）
    ports/
      prediction_port.py       ← IPredictionExecutor Protocol
    usecases/
      execute_daily_forecast_uc.py  ← ExecuteDailyForecastUseCase
  infra/
    prediction/
      script_executor.py       ← ScriptBasedPredictionExecutor
  worker/
    main.py                    ← エントリーポイント
```

### 1-2. 問題点
1. **domain層が空**: ビジネスルールやエンティティが定義されていない
2. **型定義の欠如**: 予測結果やジョブパラメータの型が不明確
3. **エラーハンドリング**: 汎用的なRuntimeErrorのみ
4. **バリデーション**: 入力パラメータの検証が不十分

---

## 2. リファクタリング計画

### Phase 1: Domain層の整備

#### Step 1-1: 予測リクエストエンティティの作成
**目的**: 予測実行のパラメータを明確に型定義

作成ファイル: `core/domain/prediction/entities.py`

```python
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class DailyForecastRequest(BaseModel):
    """日次予測リクエスト"""
    target_date: Optional[date] = Field(
        default=None,
        description="予測対象日（Noneの場合は明日）"
    )
    model_version: Optional[str] = Field(
        default=None,
        description="使用するモデルバージョン"
    )


class PredictionResult(BaseModel):
    """予測結果"""
    date: date
    y_hat: float = Field(description="予測値")
    y_lo: Optional[float] = Field(default=None, description="信頼区間下限")
    y_hi: Optional[float] = Field(default=None, description="信頼区間上限")
    model_version: Optional[str] = Field(default=None)
```

#### Step 1-2: バリデーションロジックの追加
**目的**: ドメインルールを明確化

作成ファイル: `core/domain/prediction/validators.py`

```python
from datetime import date, timedelta


def validate_forecast_date(target_date: Optional[date]) -> date:
    """
    予測対象日のバリデーション。
    
    Rules:
    - Noneの場合は明日を返す
    - 過去日は許可しない（警告のみ）
    - 未来すぎる日（例: 1年後）は警告
    """
    if target_date is None:
        return date.today() + timedelta(days=1)
    
    # TODO: ビジネスルールに応じて検証を追加
    return target_date
```

### Phase 2: UseCase層の強化

#### Step 2-1: 型安全なUseCase
```python
from app.core.domain.prediction.entities import DailyForecastRequest, PredictionResult

class ExecuteDailyForecastUseCase:
    def execute(self, request: DailyForecastRequest) -> PredictionResult:
        # 型安全な実装
        ...
```

### Phase 3: Adapter層の改善

#### Step 3-1: script_executorの型対応
- DailyForecastRequestを受け取る
- PredictionResultを返す
- エラーハンドリングの改善

---

## 3. 実装ステップ（ベイビーステップ）

### Step 1: Domain層の作成 ✅ COMPLETED (ba9204e5)
- `app/core/domain/prediction/entities.py` 作成
- DailyForecastRequest: target_date, model_version
- PredictionResult: date, y_hat, y_lo, y_hi, model_version (全てvalidation付き)
- PredictionOutput: csv_path, predictions (Optional)
- Pydantic v2使用、frozen=True（イミュータブル）

### Step 2: UseCase更新 ✅ COMPLETED (651bc014)
- `execute_daily_forecast_uc.py` 更新
- DailyForecastRequestを受け取り
- PredictionOutputを返却
- 型ヒントと詳細ドキュメント追加

### Step 3: Port更新 ✅ COMPLETED (651bc014)
- `prediction_port.py` 更新
- IPredictionExecutor Protocolにドメインエンティティ適用
- execute_daily_forecast: DailyForecastRequest → PredictionOutput
- 詳細なDocstringと例を追加

### Step 4: Adapter更新 ✅ COMPLETED (651bc014)
- `script_executor.py` 更新
- DailyForecastRequestからパラメータ取得
- PredictionOutput生成（csv_pathと将来のpredictions）
- 既存スクリプト（daily_tplus1_predict.py）との互換性維持
- DB保存処理は既存のまま維持

### Step 5: Worker更新 ✅ COMPLETED (651bc014)
- `worker/main.py` 更新
- DailyForecastRequest構築
- PredictionOutput処理
- ログ出力の改善

---

## 4. 実装完了サマリー

### 達成した改善
1. **型安全性の向上**
   - プリミティブ型（Optional[date], str）→ドメインエンティティ（DailyForecastRequest, PredictionOutput）
   - Pydanticによる自動バリデーション
   - IDEによる型チェックサポート

2. **ドメインモデルの明確化**
   - 予測リクエスト、結果の構造を明示的に定義
   - ビジネスロジックとインフラ層の分離

3. **既存コードとの互換性**
   - subprocess経由のスクリプト実行を維持
   - DB保存ロジックは変更なし
   - 段階的移行を可能にする設計

### コミット履歴（Phase 1: Domain層とClean Architecture）
- `ba9204e5`: Domain層作成（entities.py）
- `651bc014`: UseCase, Port, Adapter, Worker更新
- `6560b7dd`: Pydanticフィールド名の衝突解決（date → prediction_date）
- `b62e1360`: script_executor.pyのインポート修正
- `3e708599`: ドキュメント更新

### コミット履歴（Phase 2: Scriptsディレクトリのリファクタリング）
- `196d8489`: Step 1 - app/infra/scripts/作成、後方互換性実装
- `032d4e46`: Step 2 - 全スクリプト移動（18ファイル）
- `f45d9504`: Step 3 - 古いscriptsディレクトリ削除
- `a049f9ee`: Step 4 - Dockerfile修正

### テスト結果
```bash
# 実行コマンド
docker compose -f docker/docker-compose.dev.yml -p local_dev exec inbound_forecast_api \
  python -m worker.main --target-date 2025-01-22

# 結果
✅ CSV generated: /backend/output/tplus1_pred_20251215_152205.csv
✅ Saved prediction to DB: date=2025-01-22, y_hat=91384.19
✅ Job completed successfully
```

### 次のステップ（将来実装）
1. CSV→PredictionResultの変換実装（script_executor.py内のTODO）
2. バリデーションロジックの強化
3. エラーハンドリングの改善
4. テストケースの追加

---

## リファクタリング完了 ✅

### Phase 1: Clean Architecture移行（完了）
- ドメインエンティティによる型安全性の向上
- 既存スクリプトとの互換性維持
- E2Eテスト成功

### Phase 2: Scriptsディレクトリリファクタリング（完了）
- scripts/ → app/infra/scripts/ に移動
- 18ファイル全てを安全に移行
- Dockerfile、worker/main.py を更新
- ベイビーステップで段階的に実施

### 新しいディレクトリ構造
```
app/backend/inbound_forecast_api/
  app/
    core/
      domain/
        prediction/
          entities.py  # Domain層
      ports/
        prediction_port.py  # Port
      usecases/
        execute_daily_forecast_uc.py  # UseCase
    infra/
      prediction/
        script_executor.py  # Adapter
      scripts/  # ★ 新配置
        daily_tplus1_predict.py
        serve_predict_model_v4_2_4.py
        api_server.py
        train_daily_model.py
        update_daily_clean.py
        retrain_and_eval.py
        run_all_fast.sh
        gamma_recency_model/
        monthly_landing_gamma_poisson/
        reserve_forecast/
        weekly_allocation/
  worker/
    main.py  # エントリーポイント
  data/
  models/
  output/
```

---

## 4. テスト戦略

各ステップ後:
```bash
# コンテナ再ビルド
docker compose -f docker/docker-compose.dev.yml up -d --build inbound_forecast_api

# ヘルスチェック（APIサーバーがあれば）
curl http://localhost:8006/health

# Workerの手動実行テスト
docker compose -f docker/docker-compose.dev.yml -p local_dev exec inbound_forecast_api \
  python -m worker.main --target-date 2025-01-22
```

---

## 5. 実装優先度

### 高優先度（✅ 完了）
- [x] Step 1: Domain層の作成 (ba9204e5)
- [x] Step 2: UseCaseの更新 (651bc014)
- [x] Step 3: Portの更新 (651bc014)
- [x] Step 4: Adapterの更新 (651bc014)
- [x] Step 5: Worker更新 (651bc014)

### 中優先度（今後実施）
- [ ] CSV→PredictionResult変換の実装
- [ ] バリデーションロジックの追加
- [ ] エラーハンドリングの改善
- [ ] ログ記録の統一

### 低優先度（将来実施）
- [ ] 単体テストの追加
- [ ] メトリクス収集
- [ ] リトライロジック
- [ ] 非同期実行対応

---

## 6. リスク軽減策

### 後方互換性
- 古いインターフェースを維持しつつ、新しい型を追加
- 段階的に移行

### ロールバック計画
- 各コミットは独立して元に戻せる
- Workerが動作しなくなった場合は即座にrevert

---

## 進捗管理

- [ ] Phase 1: Domain層の整備
  - [ ] Step 1-1: エンティティ作成
  - [ ] Step 1-2: バリデーション追加
- [ ] Phase 2: UseCase層の強化
- [ ] Phase 3: Adapter層の改善
- [ ] 最終テスト・ドキュメント更新
