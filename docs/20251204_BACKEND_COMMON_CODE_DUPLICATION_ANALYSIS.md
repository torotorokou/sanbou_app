# バックエンドサービス共通処理の重複分析レポート

**作成日**: 2024-12-04  
**対象サービス**: ai_api, ledger_api, core_api, manual_api, rag_api, plan_worker

---

## 📋 Executive Summary

全6サービスのコード調査を実施し、7つのカテゴリで共通処理の重複パターンを特定しました。
- ✅ **既に統一済み**: ロギング初期化、RequestIdミドルウェア
- ⚠️ **部分的に重複**: エラーハンドリング、環境変数読み込み
- 🔴 **完全に重複**: IAP認証（core_apiのみ実装）、日付処理、CORS設定

---

## 1. ロギング初期化

### ✅ 統一状況: **完全に統一済み**

全サービスで `backend_shared.application.logging.setup_logging()` を使用しており、重複なし。

### 実装パターン

**すべてのサービスで同一:**
```python
from backend_shared.application.logging import setup_logging, get_module_logger

setup_logging()
logger = get_module_logger(__name__)
```

### 使用状況

| サービス | 実装箇所 | パターン |
|---------|---------|---------|
| ai_api | `app/main.py:22` | ✅ backend_shared使用 |
| ledger_api | `app/main.py:47` | ✅ backend_shared使用 |
| core_api | `app/app.py:49` | ✅ backend_shared使用 |
| manual_api | `app/main.py:33` | ✅ backend_shared使用 |
| rag_api | `app/main.py:37` | ✅ backend_shared使用 |
| plan_worker | `app/main.py:15` | ✅ backend_shared使用 |

### backend_shared での実装

- **場所**: `backend_shared/application/logging.py`
- **機能**: JSON形式ログ、Request ID付与、Uvicorn統合
- **設定**: 環境変数 `LOG_LEVEL` で制御可能

---

## 2. エラーハンドリング

### ⚠️ 統一状況: **部分的に重複あり**

- **ledger_api**: `backend_shared.infra.adapters.fastapi.register_error_handlers()` 使用 ✅
- **core_api**: 独自実装 (`app/api/middleware/error_handler.py`) 🔴
- **ai_api, manual_api, rag_api**: 個別に例外ハンドラを定義 🔴
- **plan_worker**: N/A（FastAPIなし）

### 実装パターン比較

#### Pattern A: ledger_api（統一版を使用）

```python
# app/main.py
from backend_shared.infra.adapters.fastapi import register_error_handlers

register_error_handlers(app)
```

#### Pattern B: core_api（独自実装）

```python
# app/api/middleware/error_handler.py
from backend_shared.core.domain.exceptions import (
    ValidationError, NotFoundError, BusinessRuleViolation,
    UnauthorizedError, ForbiddenError, InfrastructureError,
    ExternalServiceError, DomainException
)

async def domain_exception_handler(request: Request, exc: DomainException):
    # 各例外ごとに個別ハンドリング
    if isinstance(exc, ValidationError):
        return JSONResponse(status_code=400, content={...})
    if isinstance(exc, NotFoundError):
        return JSONResponse(status_code=404, content={...})
    # ... 他の例外も同様

def register_exception_handlers(app):
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(ExternalServiceError, external_service_exception_handler)
    # ...
```

#### Pattern C: ai_api, manual_api（個別実装）

```python
# ai_api/app/main.py
@app.exception_handler(ExternalServiceError)
async def handle_external_service_error(request: Request, exc: ExternalServiceError):
    status_code = 502 if exc.status_code is None else (504 if exc.status_code >= 500 else 502)
    return JSONResponse(status_code=status_code, content={...})

@app.exception_handler(InfrastructureError)
async def handle_infrastructure_error(request: Request, exc: InfrastructureError):
    return JSONResponse(status_code=503, content={...})
```

```python
# manual_api/app/main.py
@app.exception_handler(NotFoundError)
async def handle_not_found_error(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={...})

@app.exception_handler(ValidationError)
async def handle_validation_error(request: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={...})

# ... 他5つの例外ハンドラも定義
```

#### Pattern D: rag_api（一部の例外のみハンドリング）

```python
# rag_api/app/main.py
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={...})

@app.exception_handler(ValidationError)
async def handle_validation_error(request: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={...})

@app.exception_handler(NotFoundError)
async def handle_not_found_error(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={...})

@app.exception_handler(InfrastructureError)
async def handle_infrastructure_error(request: Request, exc: InfrastructureError):
    return JSONResponse(status_code=503, content={...})
```

### backend_shared での実装（統一版）

**場所**: `backend_shared/infra/adapters/fastapi/error_handlers.py`

```python
# ProblemDetails 準拠の統一エラーレスポンス
class DomainError(Exception):
    def __init__(self, code: str, status: int, user_message: str, title: str | None = None):
        ...

async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    pd = ProblemDetails(status=exc.status, code=exc.code, userMessage=exc.user_message)
    return JSONResponse(status_code=exc.status, content=pd.model_dump(by_alias=True))

def register_error_handlers(app):
    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(Exception, handle_unexpected)
```

### 問題点と推奨アクション

🔴 **問題**:
1. **core_api** は独自実装（254行）で `backend_shared` の統一版と重複
2. **ai_api, manual_api, rag_api** は個別実装で、ロジックがほぼ同一なのに分散
3. エラーレスポンス形式が微妙に異なる（ProblemDetails準拠とカスタム形式が混在）

✅ **推奨アクション**:
1. `backend_shared` の `register_error_handlers()` を拡張（全DomainException対応）
2. 全サービスで統一的に使用
3. カスタムエラーレスポンスが必要な場合は、継承・拡張で対応

---

## 3. IAP認証/JWT検証

### 🔴 統一状況: **core_apiのみ実装、他サービスは未実装**

IAP認証は現在 **core_api のみ** が実装しており、他のマイクロサービスは未対応。

### 実装状況

| サービス | IAP認証実装 | 実装パターン |
|---------|-----------|------------|
| core_api | ✅ 実装済み | AuthenticationMiddleware + IapAuthProvider |
| ai_api | ❌ 未実装 | - |
| ledger_api | ❌ 未実装 | - |
| manual_api | ❌ 未実装 | - |
| rag_api | ❌ 未実装 | - |
| plan_worker | N/A | （HTTPサーバーなし） |

### core_apiの実装詳細

**1. AuthenticationMiddleware**

```python
# app/api/middleware/auth_middleware.py
from backend_shared.config.env_utils import is_iap_enabled
from app.deps import get_auth_provider

class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, excluded_paths: List[str] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/healthz", "/docs"]
        self.iap_enabled = is_iap_enabled()
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        if not self.iap_enabled:
            # Dev環境: DevAuthProvider使用
            auth_provider = get_auth_provider()
            user = await auth_provider.get_current_user(request)
            request.state.user = user
            return await call_next(request)
        
        # 本番環境: IAP JWT検証
        try:
            auth_provider = get_auth_provider()
            user = await auth_provider.get_current_user(request)
            request.state.user = user
            return await call_next(request)
        except Exception as e:
            status_code = getattr(e, "status_code", 401)
            return JSONResponse(status_code=status_code, content={...})
```

**2. IapAuthProvider**

```python
# app/infra/adapters/auth/iap_auth_provider.py
from google.auth.transport import requests
from google.oauth2 import id_token

class IapAuthProvider(IAuthProvider):
    IAP_PUBLIC_KEY_URL = "https://www.gstatic.com/iap/verify/public_key"
    
    def __init__(self, allowed_domain: str = "honest-recycle.co.jp"):
        self._allowed_domain = allowed_domain
        self._iap_audience = get_iap_audience()
    
    async def get_current_user(self, request: Request) -> AuthUser:
        jwt_token = request.headers.get("X-Goog-IAP-JWT-Assertion")
        
        if not jwt_token:
            if is_dev:
                return await self._authenticate_from_email_header(request)
            else:
                raise HTTPException(status_code=401, detail="Authentication required")
        
        # JWT署名検証
        decoded_token = await run_in_threadpool(
            id_token.verify_token,
            jwt_token,
            requests.Request(),
            self._iap_audience,
            certs_url=self.IAP_PUBLIC_KEY_URL,
        )
        
        email = decoded_token.get("email")
        user_id = decoded_token.get("sub")
        
        # ドメインチェック
        if not email.endswith(f"@{self._allowed_domain}"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return AuthUser(email=email, user_id=user_id, role="user")
```

**3. DevAuthProvider（開発環境用）**

```python
# app/infra/adapters/auth/dev_auth_provider.py
class DevAuthProvider(IAuthProvider):
    async def get_current_user(self, request: Request) -> AuthUser:
        # 固定ユーザーを返す（開発環境専用）
        return AuthUser(
            email="dev@honest-recycle.co.jp",
            display_name="Development User",
            user_id="dev_user",
            role="admin"
        )
```

### 問題点と推奨アクション

🔴 **問題**:
1. IAP認証が **core_api にのみ** 実装されている
2. 他のマイクロサービス（ai_api, ledger_api等）は認証なしで直接アクセス可能
3. 認証ロジックが core_api に固有化されており、共通化されていない

✅ **推奨アクション**:
1. **アーキテクチャの明確化**:
   - **Option A**: BFF（core_api）のみが外部公開され、他サービスは内部通信のみ → 現状維持
   - **Option B**: 各マイクロサービスも独立してIAP認証が必要 → 共通化実施

2. **共通化を実施する場合**:
   - `backend_shared/infra/adapters/auth/` に移動:
     - `iap_auth_provider.py`
     - `dev_auth_provider.py`
     - `auth_middleware.py`
   - `backend_shared/core/domain/auth/` に移動:
     - `entities.py` (AuthUser)
     - `auth_provider.py` (IAuthProvider)

3. **環境変数の統一**:
   ```python
   # backend_shared/config/env_utils.py に既に実装済み
   is_iap_enabled()       # IAP_ENABLED
   get_iap_audience()     # IAP_AUDIENCE
   ```

---

## 4. GCS操作

### 🟡 統一状況: **現在使用されていない（廃止済み）**

ledger_api の GCS同期機能は **削除済み** で、現在は Git管理されたローカルファイルを使用。

### 過去の実装（削除済み）

**ledger_api の startup.py**:
```python
# 現在の実装（GCS同期削除済み）
def main() -> None:
    stage = settings.stage
    log(f"stage={stage}: Git管理されたローカルファイルを使用")
```

### 他サービスでの使用状況

| サービス | GCS使用 | 用途 |
|---------|---------|-----|
| ai_api | ❌ なし | - |
| ledger_api | 🗑️ 削除済み | 過去: マスターデータ・テンプレートDL |
| core_api | ❌ なし | - |
| manual_api | ❌ なし | - |
| rag_api | ❌ なし | - |
| plan_worker | ❌ なし | - |

### 推奨アクション

✅ **現状維持**:
- GCS操作は現在不要（Git管理されたファイルを使用）
- 将来的に必要になった場合のみ、`backend_shared` に共通実装を追加

---

## 5. 日付/時刻変換（JST変換）

### 🔴 統一状況: **完全に重複（backend_shared に存在しない）**

JST変換処理が複数サービスで個別実装されており、統一されていない。

### 実装パターン

#### Pattern A: rag_api（ZoneInfo使用）

```python
# rag_api/app/core/usecases/rag/ai_response_service.py
from zoneinfo import ZoneInfo
from datetime import datetime

jst = ZoneInfo("Asia/Tokyo")
timestamp = datetime.now(jst).strftime("%Y%m%d_%H%M%S")
```

```python
# rag_api/app/core/usecases/rag/dummy_response_service.py
from zoneinfo import ZoneInfo
from datetime import datetime

jst = ZoneInfo('Asia/Tokyo')
timestamp = datetime.now(jst).strftime("%Y%m%d_%H%M%S")
```

#### Pattern B: ledger_api（timezone.utc使用）

```python
# ledger_api/app/infra/adapters/file_processing/excel_pdf_zip_utils.py
from datetime import datetime, timezone

"generated_at": datetime.now(timezone.utc).isoformat()
```

```python
# ledger_api/app/infra/adapters/artifact_storage/artifact_builder.py
from datetime import datetime, timezone

"generated_at": datetime.now(timezone.utc).isoformat()
```

#### Pattern C: backend_shared（DB層のみ）

```python
# backend_shared/infra/frameworks/base_model.py
from sqlalchemy import DateTime, func

created_at = Column(DateTime(timezone=True), server_default=func.now())
updated_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 使用状況

| サービス | JST変換実装 | 実装箇所 | パターン |
|---------|-----------|---------|---------|
| rag_api | ✅ あり | `ai_response_service.py`, `dummy_response_service.py` | ZoneInfo("Asia/Tokyo") |
| ledger_api | ✅ あり | `excel_pdf_zip_utils.py`, `artifact_builder.py` | timezone.utc（JSTではない） |
| ai_api | ❌ なし | - | - |
| manual_api | ❌ なし | - | - |
| core_api | ❌ なし | - | - |
| backend_shared | ⚠️ DB層のみ | `base_model.py` | DateTime(timezone=True) |

### 問題点と推奨アクション

🔴 **問題**:
1. JST変換が個別実装されており、パターンが統一されていない
2. `rag_api` は JST、`ledger_api` は UTC を使用（混在）
3. `backend_shared` に汎用的な日付処理ユーティリティが存在しない

✅ **推奨アクション**:
1. `backend_shared/utils/datetime_utils.py` を作成:
   ```python
   from datetime import datetime, timezone
   from zoneinfo import ZoneInfo
   
   JST = ZoneInfo("Asia/Tokyo")
   
   def now_jst() -> datetime:
       """現在時刻をJSTで取得"""
       return datetime.now(JST)
   
   def now_utc() -> datetime:
       """現在時刻をUTCで取得"""
       return datetime.now(timezone.utc)
   
   def to_jst(dt: datetime) -> datetime:
       """datetime を JST に変換"""
       if dt.tzinfo is None:
           dt = dt.replace(tzinfo=timezone.utc)
       return dt.astimezone(JST)
   
   def format_jst_filename(dt: datetime | None = None) -> str:
       """JST タイムスタンプをファイル名形式で取得"""
       if dt is None:
           dt = now_jst()
       return dt.strftime("%Y%m%d_%H%M%S")
   ```

2. 全サービスで統一的に使用:
   ```python
   from backend_shared.utils.datetime_utils import now_jst, format_jst_filename
   
   timestamp = format_jst_filename()
   ```

---

## 6. ミドルウェア（CORS、RequestId）

### ✅ RequestIdMiddleware: **完全に統一済み**

全サービスで `backend_shared.infra.adapters.middleware.RequestIdMiddleware` を使用。

### ⚠️ CORSMiddleware: **個別設定で重複あり**

CORS設定が各サービスで個別に実装されており、設定値が微妙に異なる。

### 実装パターン

#### RequestIdMiddleware（統一済み）

**すべてのサービスで同一:**
```python
from backend_shared.infra.adapters.middleware import RequestIdMiddleware

app.add_middleware(RequestIdMiddleware)
```

**backend_shared での実装**:
```python
# backend_shared/infra/adapters/middleware/request_id.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # ContextVarに設定（ログに自動付与）
        set_request_id(request_id)
        
        # request.stateに保存
        request.state.request_id = request_id
        request.state.trace_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

#### CORSMiddleware（個別設定）

**Pattern A: ai_api, ledger_api（全許可）**

```python
# ai_api/app/main.py, ledger_api/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Pattern B: manual_api, rag_api（環境変数から取得）**

```python
# manual_api/app/main.py
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

```python
# rag_api/app/main.py
default_origins = "http://localhost:5173,http://127.0.0.1:5173"
origins = os.getenv("CORS_ORIGINS", default_origins).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Pattern C: core_api（条件付き有効化）**

```python
# core_api/app/app.py
if os.getenv("ENABLE_CORS", "false").lower() == "true":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

### 使用状況

| サービス | RequestIdMiddleware | CORSMiddleware | CORS設定 |
|---------|---------------------|----------------|---------|
| ai_api | ✅ backend_shared | ✅ あり | `allow_origins=["*"]` |
| ledger_api | ✅ backend_shared | ✅ あり | `allow_origins=["*"]` |
| core_api | ✅ backend_shared | ⚠️ 条件付き | `ENABLE_CORS=true` で有効化 |
| manual_api | ✅ backend_shared | ✅ あり | 環境変数 `CORS_ORIGINS` |
| rag_api | ✅ backend_shared | ✅ あり | 環境変数 `CORS_ORIGINS` |
| plan_worker | N/A | N/A | （HTTPサーバーなし） |

### 問題点と推奨アクション

🔴 **問題**:
1. CORS設定が各サービスで個別実装されている
2. デフォルト値が統一されていない（`["*"]` vs 環境変数）
3. 本番環境での制御方法が異なる（`ENABLE_CORS` vs `CORS_ORIGINS`）

✅ **推奨アクション**:
1. `backend_shared/infra/adapters/middleware/cors.py` を作成:
   ```python
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   from backend_shared.config.env_utils import get_bool_env, get_str_env
   
   def setup_cors(app: FastAPI):
       """CORS設定を統一的に追加"""
       if not get_bool_env("ENABLE_CORS", default=True):
           return
       
       origins_str = get_str_env("CORS_ORIGINS", default="http://localhost:5173,http://127.0.0.1:5173")
       origins = [o.strip() for o in origins_str.split(",") if o.strip()]
       
       app.add_middleware(
           CORSMiddleware,
           allow_origins=origins,
           allow_credentials=True,
           allow_methods=["*"],
           allow_headers=["*"],
       )
   ```

2. 全サービスで統一的に使用:
   ```python
   from backend_shared.infra.adapters.middleware import setup_cors
   
   app = FastAPI(...)
   setup_cors(app)
   ```

---

## 7. 環境変数読み込み

### ⚠️ 統一状況: **部分的に統一、個別実装も混在**

- **backend_shared** に `env_utils.py` が存在し、共通関数を提供 ✅
- しかし、各サービスで **Settings クラス** や **env_loader.py** が個別実装されている 🔴

### 実装パターン

#### Pattern A: backend_shared（共通ユーティリティ）

```python
# backend_shared/config/env_utils.py
def get_bool_env(key: str, default: bool = False) -> bool:
    """環境変数を真偽値として取得"""
    value = os.getenv(key, "").lower()
    return value in ("true", "1", "yes", "on") if value else default

def is_debug_mode() -> bool:
    return get_bool_env("DEBUG", default=False)

def is_iap_enabled() -> bool:
    return get_bool_env("IAP_ENABLED", default=False)

def get_stage() -> str:
    return get_str_env("STAGE") or get_str_env("APP_ENV", default="dev")

def get_api_base_url(service_name: str, default_port: int = 8000) -> str:
    env_key = f"{service_name.upper()}_API_BASE"
    default_url = f"http://{service_name.lower()}_api:{default_port}"
    return get_str_env(env_key, default=default_url)
```

**使用サービス**: 全サービスで部分的に使用
- `is_debug_mode()`: 全サービス
- `is_iap_enabled()`: core_api のみ

#### Pattern B: core_api（Pydantic Settings）

```python
# core_api/app/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    @staticmethod
    def _build_database_url() -> str:
        from backend_shared.infra.db.url_builder import build_database_url
        return build_database_url(driver=None, raise_on_missing=True)
    
    DATABASE_URL: str = _build_database_url.__func__()
    CSV_UPLOAD_MAX_SIZE: int = int(os.getenv("CSV_UPLOAD_MAX_SIZE", "10485760"))
    CSV_TEMP_DIR: str = os.getenv("CSV_TEMP_DIR", "/tmp/csv_uploads")
    # ... 他多数のフィールド

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

#### Pattern C: ledger_api（dataclass Settings）

```python
# ledger_api/app/settings.py
from dataclasses import dataclass

@dataclass(slots=True)
class Settings:
    stage: str
    strict_startup: bool
    startup_download_enable_raw: Optional[str]
    gcs_ledger_bucket_override: Optional[str]
    ledger_sync_subdirs: List[str]
    # ... 他多数

def load_settings() -> Settings:
    stage = os.getenv("STAGE", "dev").lower()
    strict_startup = _as_bool(os.getenv("STRICT_STARTUP"), False)
    # ... 環境変数から読み込み
    return Settings(stage=stage, strict_startup=strict_startup, ...)

settings = load_settings()
```

#### Pattern D: rag_api（env_loader.py）

```python
# rag_api/app/shared/env_loader.py
from dotenv import load_dotenv

def load_env_and_secrets() -> Optional[str]:
    # 1) CONFIG_ENV (.env) をロード
    load_dotenv(dotenv_path=str(CONFIG_ENV), override=False)
    
    # 2) ステージ別 secrets をロード
    stage = os.environ.get("STAGE") or "dev"
    secrets_dir = Path(os.environ.get("SECRETS_DIR", "/backend/secrets"))
    
    candidates = [
        secrets_dir / f".env.local_{stage}.secrets",
        secrets_dir / f".env.{stage}.secrets",
        secrets_dir / ".env.local.secrets",
        secrets_dir / ".env.secrets",
    ]
    
    for p in candidates:
        if p.exists():
            load_dotenv(dotenv_path=str(p), override=True)
            return str(p)
    return None
```

### 使用状況

| サービス | 実装パターン | ファイル | backend_shared使用 |
|---------|------------|---------|-------------------|
| core_api | Pydantic Settings | `app/config/settings.py` | ⚠️ 部分的（DB URL） |
| ledger_api | dataclass Settings | `app/settings.py` | ❌ 未使用 |
| rag_api | env_loader + dotenv | `app/shared/env_loader.py` | ❌ 未使用 |
| ai_api | ❌ なし | - | ✅ `is_debug_mode()` のみ |
| manual_api | ❌ なし | - | ✅ `is_debug_mode()` のみ |
| plan_worker | ❌ なし | - | - |

### 問題点と推奨アクション

🔴 **問題**:
1. 各サービスで **Settings クラスを個別実装** しており、重複が多い
2. 環境変数読み込みのパターンが統一されていない（Pydantic vs dataclass vs dotenv）
3. secrets読み込みロジックが **rag_api のみ** に実装されている

✅ **推奨アクション**:
1. **Option A: Pydantic Settings を統一的に使用**
   - `backend_shared/config/base_settings.py` を作成:
     ```python
     from pydantic_settings import BaseSettings
     
     class BaseAppSettings(BaseSettings):
         """全サービス共通の基本設定"""
         STAGE: str = "dev"
         DEBUG: bool = False
         LOG_LEVEL: str = "INFO"
         IAP_ENABLED: bool = False
         IAP_AUDIENCE: str | None = None
         
         class Config:
             env_file = ".env"
             env_file_encoding = "utf-8"
     ```
   
   - 各サービスは継承して拡張:
     ```python
     from backend_shared.config.base_settings import BaseAppSettings
     
     class CoreApiSettings(BaseAppSettings):
         DATABASE_URL: str
         CSV_UPLOAD_MAX_SIZE: int = 10485760
         # サービス固有の設定を追加
     ```

2. **Option B: env_utils を拡張**
   - `backend_shared/config/env_loader.py` を作成（rag_api の実装を移行）
   - secrets読み込みロジックを共通化

3. **段階的な移行**:
   - Phase 1: 新規サービスは統一設定を使用
   - Phase 2: 既存サービスを順次移行

---

## 📊 統一度スコア（サマリー）

| カテゴリ | 統一度 | backend_sharedに存在 | 重複サービス数 | 優先度 |
|---------|-------|---------------------|--------------|-------|
| 1. ロギング初期化 | ✅ 100% | ✅ あり | 0 | - |
| 2. エラーハンドリング | ⚠️ 40% | ⚠️ 部分的 | 4 | 🔥 高 |
| 3. IAP認証/JWT検証 | ⚠️ core_apiのみ | ❌ なし | 1 | 🟡 中（アーキ次第） |
| 4. GCS操作 | N/A | ❌ なし | 0 | - |
| 5. 日付/時刻変換 | 🔴 0% | ❌ なし | 2 | 🔥 高 |
| 6. ミドルウェア | ✅ RequestId: 100%<br>⚠️ CORS: 0% | ⚠️ RequestIdのみ | 5 (CORS) | 🟡 中 |
| 7. 環境変数読み込み | ⚠️ 30% | ⚠️ 部分的 | 3 | 🟡 中 |

---

## 🎯 優先度別アクションプラン

### 🔥 優先度: 高

1. **エラーハンドリングの統一**
   - `backend_shared/infra/adapters/fastapi/error_handlers.py` を拡張
   - 全DomainExceptionに対応した統一ハンドラを実装
   - core_api, ai_api, manual_api, rag_api の個別実装を置き換え

2. **日付/時刻処理の共通化**
   - `backend_shared/utils/datetime_utils.py` を新規作成
   - JST変換、UTC変換、ファイル名フォーマットを統一
   - rag_api, ledger_api の個別実装を置き換え

### 🟡 優先度: 中

3. **CORS設定の統一**
   - `backend_shared/infra/adapters/middleware/cors.py` を新規作成
   - 環境変数 `CORS_ORIGINS` `ENABLE_CORS` で統一制御
   - 全サービスで統一的に使用

4. **環境変数読み込みの統一**
   - Pydantic Settings ベースの統一設定クラスを作成
   - secrets読み込みロジックを共通化
   - 段階的に各サービスに適用

5. **IAP認証の共通化（必要に応じて）**
   - アーキテクチャ方針を明確化（BFF vs 各サービス認証）
   - 必要であれば `backend_shared/infra/adapters/auth/` に移行

---

## 📝 具体的な実装手順（例: エラーハンドリング統一）

### Step 1: backend_shared の拡張

```python
# backend_shared/infra/adapters/fastapi/error_handlers.py
from backend_shared.core.domain.exceptions import (
    ValidationError, NotFoundError, BusinessRuleViolation,
    UnauthorizedError, ForbiddenError, InfrastructureError,
    ExternalServiceError, DomainException
)

async def handle_validation_error(request: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={
        "error": {"code": "VALIDATION_ERROR", "message": exc.message, "field": exc.field}
    })

async def handle_not_found_error(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={
        "error": {"code": "NOT_FOUND", "message": exc.message, "entity": exc.entity}
    })

# ... 他の例外も同様

def register_error_handlers(app):
    """全DomainExceptionに対応した統一ハンドラを登録"""
    app.add_exception_handler(ValidationError, handle_validation_error)
    app.add_exception_handler(NotFoundError, handle_not_found_error)
    app.add_exception_handler(BusinessRuleViolation, handle_business_rule_violation)
    app.add_exception_handler(UnauthorizedError, handle_unauthorized_error)
    app.add_exception_handler(ForbiddenError, handle_forbidden_error)
    app.add_exception_handler(InfrastructureError, handle_infrastructure_error)
    app.add_exception_handler(ExternalServiceError, handle_external_service_error)
    app.add_exception_handler(Exception, handle_unexpected)
```

### Step 2: 各サービスの移行

**Before（core_api）:**
```python
# core_api/app/api/middleware/error_handler.py (254行)
async def domain_exception_handler(request: Request, exc: DomainException):
    if isinstance(exc, ValidationError):
        # ... 個別実装
    if isinstance(exc, NotFoundError):
        # ... 個別実装
    # ... 他の例外も同様

def register_exception_handlers(app):
    app.add_exception_handler(DomainException, domain_exception_handler)
    # ...
```

**After（core_api）:**
```python
# core_api/app/app.py
from backend_shared.infra.adapters.fastapi import register_error_handlers

app = FastAPI(...)
register_error_handlers(app)  # 1行で完了！
```

**削除ファイル:**
- `core_api/app/api/middleware/error_handler.py` (254行削除)

---

## 📈 期待される効果

### コード削減量（推定）

| カテゴリ | 削減可能行数 | 対象サービス |
|---------|------------|------------|
| エラーハンドリング | ~500行 | core_api, ai_api, manual_api, rag_api |
| 日付処理 | ~50行 | rag_api, ledger_api |
| CORS設定 | ~100行 | 全サービス |
| 環境変数読み込み | ~200行 | ledger_api, rag_api |
| **合計** | **~850行** | - |

### 保守性の向上

- ✅ バグ修正が1箇所で全サービスに反映
- ✅ 新規サービス追加時の実装コストが削減
- ✅ 一貫したエラーレスポンス形式
- ✅ テストコードの共通化

---

## 🔍 次のステップ

1. **優先度の確認**: ステークホルダーと相談し、実装優先度を確定
2. **backend_shared の拡張**: 高優先度の共通処理を実装
3. **段階的な移行**: 1サービスずつ移行し、動作確認
4. **ドキュメント更新**: 共通処理の使用方法をREADMEに記載
5. **CI/CDでの検証**: 移行後の自動テストを実施

---

**報告作成者**: GitHub Copilot  
**レビュー依頼先**: 開発チーム全体
