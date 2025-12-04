# backend_shared 共通処理集約計画

作成日: 2024-12-04  
ブランチ: feature/env-and-shared-refactoring

## 概要

全バックエンドサービス（ai_api, ledger_api, core_api, manual_api, rag_api, plan_worker）で重複している共通処理を、backend_shared に集約するリファクタリング計画です。

このドキュメントでは、**重複処理の詳細分析**、**集約すべき処理の優先順位付け**、**backend_shared への追加モジュール設計**、および**具体的な移行手順**を提案します。

## 重複処理の詳細分析

### ✅ 1. ロギング初期化（統一済み）

**現状**: 全サービスで `backend_shared.application.logging.setup_logging()` を使用

```python
# 全サービス共通パターン
from backend_shared.application.logging import setup_logging, get_module_logger

setup_logging()
logger = get_module_logger(__name__)
```

**評価**: ✅ 既に完全統一済み、追加作業不要

---

### ⚠️ 2. エラーハンドリング（部分的統一）

#### 現状の実装パターン

| サービス | 実装状況 | コード量 | 備考 |
|---------|---------|---------|------|
| **ledger_api** | ✅ 統一版使用 | 0行（統一版利用） | `backend_shared.infra.frameworks.exception_handlers` を使用 |
| **core_api** | ❌ 独自実装 | 254行 | `app/shared/exception_handlers.py` に独自実装 |
| **ai_api** | ❌ 独自実装 | ~50行 | 基本的なハンドラのみ |
| **manual_api** | ❌ 独自実装 | ~120行 | backend_shared例外に対応済み |
| **rag_api** | ❌ 独自実装 | ~50行 | 基本的なハンドラのみ |
| **plan_worker** | - | 0行 | FastAPI未使用のためN/A |

#### core_api の独自実装（254行）

```python
# app/backend/core_api/app/shared/exception_handlers.py
# 以下のハンドラを独自実装:
# - DomainException系: NotFoundError, ValidationError, BusinessRuleViolation
# - AuthException系: UnauthorizedError, ForbiddenError
# - InfraException系: InfrastructureError, ExternalServiceError
# - DatabaseError
# - HTTPException
# - RequestValidationError
# - 汎用Exception
```

#### backend_shared の統一版

```python
# backend_shared/src/backend_shared/infra/frameworks/exception_handlers.py
def register_exception_handlers(app: FastAPI) -> None:
    """統一例外ハンドラを登録"""
    # 全ドメイン例外に対応済み
    # JSON形式のエラーレスポンスを返す
    # ログ出力を統一フォーマットで行う
```

#### 問題点

1. **core_api の独自実装が254行**: 保守コストが高い
2. **エラーレスポンス形式の不統一**: サービス間で微妙に異なる
3. **ログ出力の不統一**: core_apiは独自ロギング、他は統一版

#### 提案: backend_shared への統一

```python
# 使用例（統一後）
from backend_shared.infra.frameworks.exception_handlers import register_exception_handlers

app = FastAPI(...)
register_exception_handlers(app)  # これだけで全ハンドラ登録完了
```

**削減可能コード量**: 約500行（core_api 254行 + manual_api 120行 + 他）

---

### 🔴 3. 日付/時刻変換（未統一、高優先度）

#### 現状の実装パターン

| サービス | 実装状況 | パターン | 備考 |
|---------|---------|---------|------|
| **rag_api** | ❌ 個別実装 | `ZoneInfo('Asia/Tokyo')` を都度作成 | `dummy_response_service.py`, `ai_response_service.py` |
| **ledger_api** | ❌ 個別実装 | `datetime` の JST 変換を個別実装 | タイムゾーン処理が散在 |
| **core_api** | ⚠️ 一部使用 | SQL内で `AT TIME ZONE 'Asia/Tokyo'` | DBクエリ内でタイムゾーン変換 |

#### rag_api の実装例

```python
# app/backend/rag_api/app/core/usecases/rag/dummy_response_service.py
from zoneinfo import ZoneInfo

jst = ZoneInfo('Asia/Tokyo')
timestamp = datetime.now(jst).strftime('%Y年%m月%d日 %H:%M')
```

```python
# app/backend/rag_api/app/core/usecases/rag/ai_response_service.py
jst = ZoneInfo("Asia/Tokyo")
timestamp = now.astimezone(jst).strftime("%Y年%m月%d日 %H:%M")
```

#### 問題点

1. **タイムゾーン名のハードコード**: `'Asia/Tokyo'` が複数箇所に散在
2. **ZoneInfo の重複生成**: パフォーマンスに影響（キャッシュされない）
3. **フォーマット文字列の不統一**: `'%Y年%m月%d日'` など複数パターン

#### 提案: backend_shared に統一ユーティリティを追加

```python
# backend_shared/src/backend_shared/utils/datetime_utils.py (新規作成)

import os
from datetime import datetime, date
from zoneinfo import ZoneInfo
from functools import lru_cache

@lru_cache(maxsize=1)
def get_app_timezone() -> ZoneInfo:
    """
    アプリケーションのタイムゾーンを取得（キャッシュ済み）
    
    環境変数 APP_TIMEZONE で設定可能（デフォルト: Asia/Tokyo）
    
    Returns:
        ZoneInfo: アプリケーションのタイムゾーン
    
    Examples:
        >>> tz = get_app_timezone()
        >>> tz
        ZoneInfo(key='Asia/Tokyo')
    """
    tz_name = os.getenv("APP_TIMEZONE", "Asia/Tokyo")
    return ZoneInfo(tz_name)


def now_in_app_timezone() -> datetime:
    """
    アプリケーションタイムゾーンでの現在時刻を取得
    
    Returns:
        datetime: タイムゾーン付き現在時刻
    
    Examples:
        >>> now = now_in_app_timezone()
        >>> now.tzinfo
        ZoneInfo(key='Asia/Tokyo')
    """
    return datetime.now(get_app_timezone())


def to_app_timezone(dt: datetime) -> datetime:
    """
    datetime オブジェクトをアプリケーションタイムゾーンに変換
    
    Args:
        dt: 変換元の datetime（naive または aware）
    
    Returns:
        datetime: アプリケーションタイムゾーンに変換された datetime
    
    Examples:
        >>> utc_time = datetime.now(timezone.utc)
        >>> jst_time = to_app_timezone(utc_time)
    """
    return dt.astimezone(get_app_timezone())


def format_datetime_jp(dt: datetime) -> str:
    """
    datetime を日本語形式にフォーマット
    
    Args:
        dt: フォーマット対象の datetime
    
    Returns:
        str: '2024年12月04日 15:30' 形式の文字列
    
    Examples:
        >>> now = now_in_app_timezone()
        >>> format_datetime_jp(now)
        '2024年12月04日 15:30'
    """
    return dt.strftime('%Y年%m月%d日 %H:%M')


def format_date_jp(d: date) -> str:
    """
    date を日本語形式にフォーマット
    
    Args:
        d: フォーマット対象の date
    
    Returns:
        str: '2024年12月04日' 形式の文字列
    
    Examples:
        >>> today = date.today()
        >>> format_date_jp(today)
        '2024年12月04日'
    """
    return d.strftime('%Y年%m月%d日')
```

#### 使用例（リファクタリング後）

```python
# rag_api/app/core/usecases/rag/dummy_response_service.py (AFTER)
from backend_shared.utils.datetime_utils import now_in_app_timezone, format_datetime_jp

timestamp = format_datetime_jp(now_in_app_timezone())
```

**削減可能コード量**: 約50行

---

### 🟡 4. CORS 設定（未統一、中優先度）

#### 現状の実装パターン

| サービス | CORS Origins | パターン |
|---------|--------------|---------|
| **core_api** | ✅ 環境変数 + デフォルト | `CORS_ORIGINS` 環境変数、複数オリジン対応 |
| **ledger_api** | ✅ 環境変数 | `CORS_ORIGINS` 環境変数 |
| **manual_api** | ✅ 環境変数 + デフォルト | `"http://localhost:5173,http://127.0.0.1:5173"` |
| **ai_api** | ❌ ハードコード | `["*"]` 全許可（セキュリティリスク） |
| **rag_api** | ❌ ハードコード | `["*"]` 全許可（セキュリティリスク） |

#### 問題点

1. **設定方法の不統一**: 環境変数、ハードコード、`["*"]` が混在
2. **セキュリティリスク**: ai_api と rag_api が全オリジン許可
3. **デフォルト値の不統一**: 各サービスで異なるデフォルト値

#### 提案: backend_shared に共通 CORS 設定関数を追加

```python
# backend_shared/src/backend_shared/infra/frameworks/cors_config.py (新規作成)

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def get_cors_origins() -> list[str]:
    """
    CORS許可オリジンのリストを環境変数から取得
    
    環境変数 CORS_ORIGINS をカンマ区切りで読み込みます。
    未設定の場合はローカル開発用のデフォルト値を返します。
    
    Returns:
        list[str]: CORS許可オリジンのリスト
    
    Examples:
        >>> os.environ["CORS_ORIGINS"] = "http://example.com,http://localhost:3000"
        >>> get_cors_origins()
        ['http://example.com', 'http://localhost:3000']
    """
    default_origins = "http://localhost:5173,http://127.0.0.1:5173"
    origins_str = os.getenv("CORS_ORIGINS", default_origins)
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


def setup_cors(app: FastAPI, origins: list[str] | None = None) -> None:
    """
    FastAPIアプリケーションにCORSミドルウェアを設定
    
    Args:
        app: FastAPIアプリケーションインスタンス
        origins: 許可するオリジンのリスト（Noneの場合は環境変数から取得）
    
    Examples:
        >>> app = FastAPI()
        >>> setup_cors(app)  # 環境変数から自動取得
    """
    if origins is None:
        origins = get_cors_origins()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

#### 使用例（リファクタリング後）

```python
# 全サービスで統一
from backend_shared.infra.frameworks.cors_config import setup_cors

app = FastAPI(...)
setup_cors(app)  # これだけでCORS設定完了
```

**削減可能コード量**: 約100行

---

### 🟡 5. 環境変数読み込み（部分的統一、中優先度）

#### 現状の実装パターン

| サービス | Settings実装 | パターン |
|---------|-------------|---------|
| **core_api** | Pydantic BaseSettings | 242行、包括的な設定クラス |
| **ledger_api** | dataclass | 149行、カスタムロジック |
| **ai_api** | ✅ 直接 `os.getenv()` | 5行、シンプル |
| **manual_api** | ❌ 直接 `os.getenv()` | ミドルウェア内で直接読み込み |
| **rag_api** | ✅ 独自 `env_loader` | `load_env_and_secrets()` カスタム実装 |
| **plan_worker** | Pydantic BaseSettings | シンプルな設定クラス |

#### backend_shared の既存ユーティリティ

```python
# backend_shared/src/backend_shared/config/env_utils.py
def get_str_env(key: str, default: str = "") -> str:
def get_int_env(key: str, default: int = 0) -> int:
def get_bool_env(key: str, default: bool = False) -> bool:
def get_stage() -> str:
def get_iap_audience() -> str:
# ... など多数の共通関数
```

#### 問題点

1. **Settings クラスの重複実装**: 各サービスで似たような実装
2. **環境変数読み込みパターンの不統一**: Pydantic、dataclass、直接読み込みが混在
3. **バリデーションロジックの重複**: 各サービスで独自検証

#### 提案: Settings のベースクラスを backend_shared に追加

```python
# backend_shared/src/backend_shared/config/base_settings.py (新規作成)

from pydantic_settings import BaseSettings
from backend_shared.config.env_utils import get_stage

class BaseAppSettings(BaseSettings):
    """
    全サービス共通の基本設定
    
    各サービスはこのクラスを継承して独自設定を追加します。
    """
    
    # === ステージ設定 ===
    STAGE: str = get_stage()
    """デプロイ環境（dev/stg/prod）"""
    
    DEBUG: bool = False
    """デバッグモード（True で /docs 等を公開）"""
    
    # === API基本情報 ===
    API_TITLE: str = "API Service"
    """API タイトル（各サービスで上書き）"""
    
    API_VERSION: str = "1.0.0"
    """API バージョン"""
    
    API_ROOT_PATH: str = ""
    """API ルートパス（BFF経由の場合は /core_api など）"""
    
    # === CORS設定 ===
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    """CORS許可オリジン（カンマ区切り）"""
    
    @property
    def cors_origins_list(self) -> list[str]:
        """CORS許可オリジンをリストで取得"""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # 追加の環境変数を許可


def get_base_settings() -> BaseAppSettings:
    """基本設定のシングルトンインスタンスを取得"""
    return BaseAppSettings()
```

#### 使用例（各サービスでの継承）

```python
# ai_api/app/config/settings.py (AFTER)
from backend_shared.config.base_settings import BaseAppSettings

class AiApiSettings(BaseAppSettings):
    API_TITLE: str = "AI_API"
    
    GEMINI_API_KEY: str = ""
    """Gemini API キー（必須）"""
    
    GEMINI_API_URL: str = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    """Gemini API エンドポイント"""

def get_settings() -> AiApiSettings:
    return AiApiSettings()
```

**削減可能コード量**: 約200行（共通部分の重複排除）

---

### 🟢 6. IAP 認証（core_api のみ、低優先度）

#### 現状

- **core_api**: `IapAuthProvider` を独自実装（282行）
- **他サービス**: 認証なし（内部API）

#### 評価

IAP認証は現在 core_api のみで必要であり、他サービスは内部APIとして動作します。
将来的に複数サービスで認証が必要になった場合に backend_shared へ移行を検討します。

**現時点での移行優先度**: 低（将来的な課題）

---

### 🟢 7. GCS 操作（削除済み、対応不要）

#### 現状

ledger_api で過去に使用されていたGCS同期機能は削除済みです。
現在はローカルファイルシステムを使用しています。

**対応不要**

---

## backend_shared 追加モジュール設計

### 新規作成するモジュール

```
backend_shared/src/backend_shared/
├── config/
│   ├── base_settings.py          # NEW: 共通Settings基底クラス
│   └── env_utils.py              # 既存（拡張）
├── infra/
│   └── frameworks/
│       ├── cors_config.py        # NEW: CORS共通設定
│       ├── exception_handlers.py # 既存（全サービスで利用促進）
│       └── ...
└── utils/
    ├── datetime_utils.py         # NEW: 日付時刻ユーティリティ
    └── ...
```

### モジュール別優先度

| モジュール | 優先度 | 削減コード量 | 影響範囲 |
|-----------|-------|-------------|---------|
| `exception_handlers` 統一 | 🔥 高 | ~500行 | core_api, manual_api, ai_api, rag_api |
| `datetime_utils` | 🔥 高 | ~50行 | rag_api, ledger_api |
| `cors_config` | 🟡 中 | ~100行 | 全サービス |
| `base_settings` | 🟡 中 | ~200行 | 全サービス |
| **合計** | - | **~850行** | - |

---

## リファクタリング例

### 例1: エラーハンドリングの統一（core_api）

#### BEFORE

```python
# core_api/app/main.py
from app.shared.exception_handlers import (
    handle_not_found_error,
    handle_validation_error,
    # ... 10個以上のハンドラをインポート
)

app = FastAPI(...)

app.add_exception_handler(NotFoundError, handle_not_found_error)
app.add_exception_handler(ValidationError, handle_validation_error)
# ... 10個以上のハンドラを個別登録
```

```python
# core_api/app/shared/exception_handlers.py (254行)
async def handle_not_found_error(request: Request, exc: NotFoundError):
    # ... 独自実装
async def handle_validation_error(request: Request, exc: ValidationError):
    # ... 独自実装
# ... 10個以上のハンドラ実装
```

#### AFTER

```python
# core_api/app/main.py
from backend_shared.infra.frameworks.exception_handlers import register_exception_handlers

app = FastAPI(...)
register_exception_handlers(app)  # これだけで完了
```

```python
# core_api/app/shared/exception_handlers.py
# ファイル削除（254行削減）
```

---

### 例2: 日付処理の統一（rag_api）

#### BEFORE

```python
# rag_api/app/core/usecases/rag/dummy_response_service.py
from zoneinfo import ZoneInfo

jst = ZoneInfo('Asia/Tokyo')  # 毎回生成
timestamp = datetime.now(jst).strftime('%Y年%m月%d日 %H:%M')
```

#### AFTER

```python
# rag_api/app/core/usecases/rag/dummy_response_service.py
from backend_shared.utils.datetime_utils import now_in_app_timezone, format_datetime_jp

timestamp = format_datetime_jp(now_in_app_timezone())  # シンプル＆効率的
```

---

## 移行手順（4フェーズ）

### Phase 1: backend_shared に新規モジュールを追加

**目的**: 既存コードに影響を与えずに共通機能を準備

**作業内容**:
1. `backend_shared/src/backend_shared/utils/datetime_utils.py` を作成
2. `backend_shared/src/backend_shared/infra/frameworks/cors_config.py` を作成
3. `backend_shared/src/backend_shared/config/base_settings.py` を作成
4. ユニットテストを作成（`backend_shared/tests/` 配下）
5. backend_shared のバージョンアップ（例: 0.2.0）

**成果物**:
- 新規モジュール3つ
- ユニットテスト
- README更新

**影響**: なし（既存コードは変更しない）

---

### Phase 2: 1サービスで試験導入（rag_api）

**目的**: 新規モジュールの動作確認とフィードバック収集

**作業内容**:
1. rag_api で `datetime_utils` を使用するようリファクタリング
   - `dummy_response_service.py` を修正
   - `ai_response_service.py` を修正
2. rag_api で `cors_config` を使用するようリファクタリング
   - `main.py` のCORS設定を変更
3. 動作確認（ローカル環境）
4. テスト実行

**成果物**:
- rag_api リファクタリング完了
- 動作確認レポート

**削減コード量**: 約20行

---

### Phase 3: 全サービスへの展開

**目的**: 全サービスで共通モジュールを使用

**作業内容**:
1. **エラーハンドリング統一**:
   - core_api の `exception_handlers.py` (254行) を削除
   - manual_api のエラーハンドラを統一版に置き換え
   - ai_api, rag_api のエラーハンドラを統一版に置き換え

2. **日付処理統一**:
   - ledger_api で `datetime_utils` を使用

3. **CORS設定統一**:
   - ai_api, core_api, ledger_api, manual_api で `cors_config` を使用

4. **各サービスで動作確認**

**成果物**:
- 全サービスでリファクタリング完了
- 統合テスト完了

**削減コード量**: 約850行

---

### Phase 4: ドキュメント整備と継続的改善

**目的**: リファクタリング成果の定着と今後の方針策定

**作業内容**:
1. backend_shared の README を更新
   - 新規モジュールの使用方法を記載
   - サンプルコードを追加
2. 各サービスの README を更新
   - backend_shared の利用状況を記載
3. アーキテクチャドキュメントを更新
4. 今後の共通化候補を整理（IAP認証など）

**成果物**:
- 更新されたドキュメント
- 継続的改善計画

---

## 注意事項

### 後方互換性

- 既存の動作を変更しない
- デフォルト値は現状と同じにする
- 段階的に移行し、各フェーズで動作確認

### テスト

- 各フェーズで必ずテストを実行
- 既存のテストが通ることを確認
- 新規機能にはユニットテストを追加

### パフォーマンス

- `@lru_cache` でタイムゾーン情報をキャッシュ
- 不要なオブジェクト生成を避ける

### セキュリティ

- CORS設定は本番環境で必ず適切に設定
- デバッグモードは本番環境で無効化
- 環境変数の検証を強化

---

## 期待される効果

### コード削減

- **約850行のコード削減**
- 保守コストの大幅削減
- テストコードの統一化

### 品質向上

- エラーハンドリングの統一によるユーザー体験向上
- ログ出力の統一による運用性向上
- タイムゾーン処理の一貫性確保

### 開発効率向上

- 新規サービス開発時の初期設定が簡単に
- 共通機能の再利用による開発速度向上
- バグ修正が全サービスに即座に反映

---

## 関連ドキュメント

- [backend_shared README](../app/backend/backend_shared/README.md)
- [20251204_ENV_HARDCODE_AUDIT.md](./20251204_ENV_HARDCODE_AUDIT.md)
- [20251203_ENV_CONSOLIDATION.md](./20251203_ENV_CONSOLIDATION.md)
