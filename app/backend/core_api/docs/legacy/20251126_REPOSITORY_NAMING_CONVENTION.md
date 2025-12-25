# Repository 命名規則とディレクトリ構成

## 目的

Clean Architecture (Hexagonal Architecture) における Repository の命名とディレクトリ構成を標準化し、コードベース全体の一貫性を確保します。

## 命名規則

### 1. クラス名

```python
# ✅ 推奨: Repository サフィックス
class CalendarRepository:
    """ICalendarQuery Port の PostgreSQL 実装"""
    pass

class RawDataRepository:
    """IUploadStatusQuery Port の PostgreSQL 実装"""
    pass

# ❌ 非推奨: Repo 短縮形
class ForecastQueryRepo:  # → ForecastQueryRepository に変更予定
    pass

# ✅ 許容: 特殊な役割を持つ場合は Adapter
class ExternalApiAdapter:
    """外部 API クライアントのアダプター"""
    pass
```

### 2. ファイル名

```
✅ 推奨: {domain}_repository.py
- calendar_repository.py
- raw_data_repository.py
- sales_tree_repository.py
- inbound_repository.py  (PgRepository → Repository に統一)

❌ 非推奨: {domain}_repo.py
- forecast_query_repo.py  → forecast_query_repository.py
- dashboard_target_repo.py → dashboard_target_repository.py
- job_repo.py → job_repository.py
- core_repo.py → core_repository.py

✅ 特殊ケース: {purpose}_adapter.py
- external_api_adapter.py  (外部API統合)
- materialized_view_refresher.py (インフラユーティリティ)
```

### 3. ディレクトリ構成

```
app/infra/adapters/
├── calendar/
│   ├── __init__.py
│   └── calendar_repository.py          # CalendarRepository
├── upload/
│   ├── __init__.py
│   ├── raw_data_repository.py          # RawDataRepository
│   └── shogun_csv_repository.py        # ShogunCsvRepository
├── forecast/
│   ├── __init__.py
│   ├── forecast_query_repository.py    # ← forecast_query_repo.py から改名予定
│   └── job_repository.py               # ← job_repo.py から改名予定
├── dashboard/
│   ├── __init__.py
│   └── dashboard_target_repository.py  # ← dashboard_target_repo.py から改名予定
├── inbound/
│   ├── __init__.py
│   └── inbound_repository.py           # ← inbound_pg_repository.py から改名予定
├── sales_tree/
│   ├── __init__.py
│   └── sales_tree_repository.py        # ✅ 既に準拠
├── external/
│   ├── __init__.py
│   └── external_api_adapter.py         # ✅ Adapter として許容
├── materialized_view/
│   ├── __init__.py
│   └── materialized_view_refresher.py  # ✅ インフラツールとして許容
└── misc/
    ├── __init__.py
    └── core_repository.py              # ← core_repo.py から改名予定
```

## Port と Adapter の関係

### Port (インターフェース定義)

```python
# app/domain/ports/calendar_port.py
from typing import Protocol, List, Dict, Any

class ICalendarQuery(Protocol):
    """カレンダーデータ取得の抽象インターフェース"""

    def get_month_calendar(self, *, year: int, month: int) -> List[Dict[str, Any]]:
        """指定年月のカレンダーを取得"""
        ...
```

### Adapter (Port の実装)

```python
# app/infra/adapters/calendar/calendar_repository.py
from app.domain.ports.calendar_port import ICalendarQuery

class CalendarRepository:
    """ICalendarQuery の PostgreSQL 実装"""

    def __init__(self, db: Session):
        self.db = db

    def get_month_calendar(self, *, year: int, month: int) -> List[Dict[str, Any]]:
        # PostgreSQL 実装
        ...
```

## エクスポート規則

### **init**.py でクラスをエクスポート

```python
# app/infra/adapters/calendar/__init__.py
from app.infra.adapters.calendar.calendar_repository import CalendarRepository

__all__ = ["CalendarRepository"]
```

### DI コンテナでの利用

```python
# app/config/di_providers.py
from app.infra.adapters.calendar import CalendarRepository
from app.domain.ports.calendar_port import ICalendarQuery

def get_calendar_repo(db: Session = Depends(get_db)) -> ICalendarQuery:
    """CalendarRepository インスタンスを生成（Port型で返却）"""
    return CalendarRepository(db)
```

## 移行計画

### Phase 1: 命名規則ドキュメント作成 ✅

- このドキュメントの作成
- チーム内での合意形成

### Phase 2: 新規作成時の適用 (進行中)

- 新しく作成する Repository は規則に準拠
- 例: `calendar_repository.py`, `raw_data_repository.py` (既に準拠済み)

### Phase 3: 既存ファイルの段階的リネーム (今後)

1. **低リスク**: 参照が少ないファイルから

   - `core_repo.py` → `core_repository.py`
   - `job_repo.py` → `job_repository.py`

2. **中リスク**: 複数箇所から参照されるファイル

   - `forecast_query_repo.py` → `forecast_query_repository.py`
   - `dashboard_target_repo.py` → `dashboard_target_repository.py`

3. **高リスク**: 広範囲に影響するファイル
   - `inbound_pg_repository.py` → `inbound_repository.py`
   - クラス名も `InboundPgRepository` → `InboundRepository` に変更

### Phase 4: 自動化ツール導入 (将来)

- pre-commit hook で命名規則チェック
- CI/CD でのリンター統合

## チェックリスト

新しい Repository を作成する際は以下を確認:

- [ ] クラス名が `*Repository` で終わる
- [ ] ファイル名が `*_repository.py` (または特殊な場合 `*_adapter.py`)
- [ ] Port インターフェースを実装している (Protocol またはドキュメント化)
- [ ] `__init__.py` でエクスポートされている
- [ ] DI コンテナ (`di_providers.py`) に登録されている
- [ ] ドキュメントコメントが充実している

## 参考リンク

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture (Ports & Adapters) by Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Python typing.Protocol Documentation](https://docs.python.org/3/library/typing.html#typing.Protocol)
