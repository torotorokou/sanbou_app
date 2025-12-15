# Core API ディレクトリ構造リファクタリング

- 日付: 2025-12-15
- ブランチ: refactor/core-api-directory-structure
- 目的: Convention document に準拠したディレクトリ構造への段階的移行

---

## 1. 現状分析

### 1-1. 現在の構造
```
app/backend/core_api/app/
  core/
    domain/
      inbound.py                    ← 移動対象
      sales_tree.py                 ← 移動対象
      sales_tree_detail.py          ← 移動対象
      models.py                     ← 移動対象
      rules.py                      ← 移動対象
      shogun_flash_schemas.py       ← 移動対象
      auth/                         ← 既に整理済み
      csv/                          ← 既に整理済み
      entities/                     ← 既に整理済み
      value_objects/                ← 既に整理済み
      services/                     ← 既に整理済み
    ports/
      calendar_port.py              ← 移動対象
      csv_writer_port.py            ← 移動対象
      customer_churn_port.py        ← 移動対象
      dashboard_query_port.py       ← 移動対象
      external_api_port.py          ← 移動対象
      forecast_port.py              ← 移動対象
      inbound_repository_port.py    ← 移動対象
      ingest_port.py                ← 移動対象
      kpi_port.py                   ← 移動対象
      sales_tree_port.py            ← 移動対象
      upload_status_port.py         ← 移動対象
      auth/                         ← 既に整理済み
    usecases/                       ← 既に整理済み（機能別サブディレクトリ）
  infra/
    adapters/                       ← 既に整理済み（機能別サブディレクトリ）
```

### 1-2. 目標構造（Convention準拠）
```
app/backend/core_api/app/
  core/
    domain/
      inbound/
        entities.py               ← inbound.py の内容
      sales_tree/
        entities.py               ← sales_tree.py の内容
        detail.py                 ← sales_tree_detail.py の内容
      forecast/
        entities.py               ← models.py の forecast関連
      ingest/
        entities.py               ← models.py の ingest関連
      calendar/
        rules.py                  ← rules.py の内容
      csv/                        ← 既存維持
      auth/                       ← 既存維持
      entities/                   ← 既存維持
      value_objects/              ← 既存維持
      services/                   ← 既存維持
    ports/
      inbound/
        repositories.py           ← inbound_repository_port.py
      sales_tree/
        repositories.py           ← sales_tree_port.py
      forecast/
        repositories.py           ← forecast_port.py
      calendar/
        repositories.py           ← calendar_port.py
      csv/
        writer.py                 ← csv_writer_port.py
      customer_churn/
        repositories.py           ← customer_churn_port.py
      dashboard/
        repositories.py           ← dashboard_query_port.py
      external/
        gateways.py               ← external_api_port.py
      ingest/
        repositories.py           ← ingest_port.py
      kpi/
        repositories.py           ← kpi_port.py
      upload/
        repositories.py           ← upload_status_port.py
      auth/                       ← 既存維持
```

---

## 2. 移行ステップ（ベイビーステップ）

### Phase 1: Domain層の整理
- Step 1-1: inbound.py → domain/inbound/entities.py
- Step 1-2: sales_tree.py & sales_tree_detail.py → domain/sales_tree/
- Step 1-3: models.py（forecast関連） → domain/forecast/entities.py
- Step 1-4: models.py（ingest関連） → domain/ingest/entities.py
- Step 1-5: rules.py → domain/calendar/rules.py
- Step 1-6: shogun_flash_schemas.py → domain/external/schemas.py

各ステップ後：
1. インポート文の修正
2. 動作確認（最低限のAPI起動テスト）
3. コミット

### Phase 2: Ports層の整理
- Step 2-1: inbound_repository_port.py → ports/inbound/repositories.py
- Step 2-2: sales_tree_port.py → ports/sales_tree/repositories.py
- Step 2-3: forecast_port.py → ports/forecast/repositories.py
- Step 2-4: 残りのport（calendar, csv, customer_churn等）を順次移行

各ステップ後：
1. インポート文の修正
2. 動作確認
3. コミット

---

## 3. 各ステップの詳細

### Step 1-1: inbound.py の移行

**影響範囲分析**：
```python
# 現在のインポート
from app.core.domain.inbound import InboundDailyRow, CumScope

# 移行後のインポート
from app.core.domain.inbound.entities import InboundDailyRow, CumScope
```

**影響ファイル**：
- app/core/ports/inbound_repository_port.py
- app/core/usecases/inbound/dto.py
- app/infra/adapters/inbound/inbound_repository.py

**作業手順**：
1. ディレクトリ作成: `core/domain/inbound/`
2. ファイル作成: `core/domain/inbound/__init__.py`
3. ファイル移動: `inbound.py` → `core/domain/inbound/entities.py`
4. `__init__.py`でre-exportを追加（後方互換性）
5. 各インポート文を更新
6. 動作確認
7. コミット

---

## 4. リスク軽減策

### 4-1. 後方互換性の維持
各ステップで古い場所に`__init__.py`を残し、新しい場所からre-exportする：

```python
# core/domain/inbound.py（移行後も残す一時ファイル）
"""Backward compatibility - please use core.domain.inbound.entities"""
from app.core.domain.inbound.entities import *

import warnings
warnings.warn(
    "Importing from core.domain.inbound is deprecated. "
    "Use core.domain.inbound.entities instead.",
    DeprecationWarning,
    stacklevel=2
)
```

### 4-2. 段階的なインポート更新
1. 新しい構造のファイルを作成
2. 古い場所からre-export
3. すべてのインポート文を更新
4. 古いファイルを削除

### 4-3. 動作確認方法
各ステップ後に以下を実行：
```bash
# コンテナ再起動
docker compose -f docker/docker-compose.dev.yml up -d --build core_api

# ヘルスチェック
curl http://localhost:8001/health

# 主要エンドポイントのサンプルリクエスト
# - forecast API
# - inbound API
# - sales_tree API
```

---

## 5. ロールバック計画

各コミットは独立して元に戻せるように、1機能ずつ移行：
```bash
# 問題があれば直前のコミットに戻す
git reset --hard HEAD~1

# または特定のコミットに戻す
git reset --hard <commit-hash>
```

---

## 進捗管理

- [ ] Phase 1-1: inbound domain移行
- [ ] Phase 1-2: sales_tree domain移行
- [ ] Phase 1-3: forecast domain移行
- [ ] Phase 1-4: ingest domain移行
- [ ] Phase 1-5: calendar domain移行
- [ ] Phase 1-6: external domain移行
- [ ] Phase 2-1: inbound ports移行
- [ ] Phase 2-2: sales_tree ports移行
- [ ] Phase 2-3: forecast ports移行
- [ ] Phase 2-4: その他ports移行
- [ ] 最終確認・テスト
- [ ] ドキュメント更新
