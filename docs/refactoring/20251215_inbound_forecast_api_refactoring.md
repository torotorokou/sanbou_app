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

### Step 1: Domain層の作成
1. `core/domain/prediction/` ディレクトリ作成
2. `entities.py` 作成（DailyForecastRequest, PredictionResult）
3. `__init__.py` 作成（re-export）

### Step 2: UseCaseの更新
1. UseCaseをDailyForecastRequestを受け取るように修正
2. 戻り値の型を明確化
3. 動作確認

### Step 3: Portの更新
1. IPredictionExecutor の型シグネチャ更新
2. 動作確認

### Step 4: Adapterの更新
1. ScriptBasedPredictionExecutor の型対応
2. 動作確認

### Step 5: Worker統合
1. worker/main.py の更新
2. E2Eテスト

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

### 高優先度（今回実施）
- [x] Step 1: Domain層の作成
- [ ] Step 2: UseCaseの更新
- [ ] Step 3: Portの更新
- [ ] Step 4: Adapterの更新

### 中優先度（今後実施）
- [ ] バリデーションロジックの追加
- [ ] エラーハンドリングの改善
- [ ] ログ記録の統一

### 低優先度（将来実施）
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
