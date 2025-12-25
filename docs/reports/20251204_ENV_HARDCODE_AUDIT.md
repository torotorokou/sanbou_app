# 環境変数化すべきハードコード値の監査レポート

作成日: 2024-12-04  
ブランチ: feature/env-and-shared-refactoring

## 概要

バックエンドコード全体を調査し、`.env` ファイルに移すべきハードコード値を洗い出しました。
セキュリティ、保守性、デプロイ柔軟性の観点から、環境依存値は環境変数化すべきです。

## env に移すべき候補一覧

### 🔴 高優先度（セキュリティ/必須）

| 現在の定数名/値                                   | 種類         | 発見場所                                               | 推奨環境変数名           | 設定先  | メモ                               |
| ------------------------------------------------- | ------------ | ------------------------------------------------------ | ------------------------ | ------- | ---------------------------------- |
| `"honest-recycle.co.jp"`                          | 許可ドメイン | `core_api/infra/adapters/auth/iap_auth_provider.py:63` | `ALLOWED_EMAIL_DOMAIN`   | common  | ホワイトリストの中核値             |
| `"https://www.gstatic.com/iap/verify/public_key"` | IAP公開鍵URL | `core_api/infra/adapters/auth/iap_auth_provider.py:59` | `IAP_PUBLIC_KEY_URL`     | common  | 通常は変更不要だが設定可能にすべき |
| `"change-me-in-production"`                       | シークレット | `ledger_api/app/settings.py:129`                       | `REPORT_ARTIFACT_SECRET` | secrets | 本番では必ず変更                   |

### 🟡 中優先度（デプロイ柔軟性）

| 現在の定数名/値                                                                              | 種類                     | 発見場所                                             | 推奨環境変数名             | 設定先 | メモ                                         |
| -------------------------------------------------------------------------------------------- | ------------------------ | ---------------------------------------------------- | -------------------------- | ------ | -------------------------------------------- |
| `"http://localhost:5173"`                                                                    | フロントエンドURL        | `manual_api/infra/adapters/manuals_repository.py:25` | `MANUAL_FRONTEND_BASE_URL` | 各環境 | 既に実装済みだが、デフォルト値がハードコード |
| `"http://localhost:5173,http://127.0.0.1:5173"`                                              | CORS Origins             | `manual_api/app/main.py:131`                         | `CORS_ORIGINS`             | 各環境 | 既に実装済み、デフォルト値の見直し           |
| `"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"` | Gemini API URL           | `ai_api/infra/adapters/gemini_client.py:14`          | `GEMINI_API_URL`           | common | モデルバージョン変更に対応                   |
| `/backend/secrets`                                                                           | シークレットディレクトリ | `rag_api/shared/env_loader.py:41`                    | `SECRETS_DIR`              | common | 既に実装済み、デフォルト値の文書化           |

### 🟢 低優先度（コード整理）

| 現在の定数名/値                                      | 種類                      | 発見場所                         | 推奨環境変数名             | 設定先 | メモ                       |
| ---------------------------------------------------- | ------------------------- | -------------------------------- | -------------------------- | ------ | -------------------------- |
| `"Asia/Tokyo"`                                       | タイムゾーン              | 複数ファイル                     | `TZ` または `APP_TIMEZONE` | common | 標準的な環境変数 TZ を推奨 |
| `10485760` (10MB)                                    | CSVアップロード最大サイズ | `core_api/config/settings.py:65` | `CSV_UPLOAD_MAX_SIZE`      | common | 既に実装済み               |
| `/tmp/csv_uploads`                                   | CSV一時ディレクトリ       | `core_api/config/settings.py:68` | `CSV_TEMP_DIR`             | common | 既に実装済み               |
| `/backend/config/csv_config/shogun_csv_masters.yaml` | YAML設定パス              | `core_api/config/settings.py:71` | `CSV_MASTERS_YAML_PATH`    | common | 既に実装済み               |

### ⚪ コードに残してよいもの（定数として適切）

| 値                                          | 理由                                                              |
| ------------------------------------------- | ----------------------------------------------------------------- |
| `stg.shogun_flash_receive` などのテーブル名 | ビジネスロジックの一部、DBスキーマ構造に依存                      |
| `IAP_PUBLIC_KEY_URL` のデフォルト値         | Google公式URL、変更の可能性極めて低い（ただし設定可能にはすべき） |
| `placeholder` 画像URL（manual_api）         | テストデータ、実装が完了すれば削除予定                            |
| HTTPステータスコード                        | 標準仕様                                                          |

## 📋 推奨する環境変数の追加

### .env.common に追加すべきもの

```bash
# === Security / Authentication ===
ALLOWED_EMAIL_DOMAIN=honest-recycle.co.jp
IAP_PUBLIC_KEY_URL=https://www.gstatic.com/iap/verify/public_key

# === Application Settings ===
APP_TIMEZONE=Asia/Tokyo
TZ=Asia/Tokyo

# === API URLs (External Services) ===
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent

# === Directory Paths ===
SECRETS_DIR=/backend/secrets
CSV_TEMP_DIR=/tmp/csv_uploads
CSV_MASTERS_YAML_PATH=/backend/config/csv_config/shogun_csv_masters.yaml

# === Upload Limits ===
CSV_UPLOAD_MAX_SIZE=10485760

# === CORS Settings (共通デフォルト) ===
# 各環境で上書き可能
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### secrets/.env.local_dev.secrets に追加すべきもの

```bash
# === ledger_api Report Artifact Secret ===
REPORT_ARTIFACT_SECRET=dev-local-secret-key-12345
```

### secrets/.env.stg.secrets に追加すべきもの

```bash
REPORT_ARTIFACT_SECRET=<strong-random-secret-for-stg>
```

### secrets/.env.prod.secrets に追加すべきもの

```bash
REPORT_ARTIFACT_SECRET=<strong-random-secret-for-prod>
```

## 🏗️ BaseSettings 設計案

### core_api の Settings 拡張

```python
# app/backend/core_api/app/config/settings.py

from pydantic_settings import BaseSettings
from backend_shared.config.env_utils import get_str_env

class Settings(BaseSettings):
    # ... 既存の設定 ...

    # === Authentication / Security ===
    ALLOWED_EMAIL_DOMAIN: str = get_str_env("ALLOWED_EMAIL_DOMAIN", "honest-recycle.co.jp")
    """許可するメールドメイン（IAP認証用ホワイトリスト）"""

    IAP_PUBLIC_KEY_URL: str = get_str_env(
        "IAP_PUBLIC_KEY_URL",
        "https://www.gstatic.com/iap/verify/public_key"
    )
    """IAP JWT検証用の公開鍵URL"""

    # === Application Settings ===
    APP_TIMEZONE: str = get_str_env("APP_TIMEZONE", "Asia/Tokyo")
    """アプリケーション全体で使用するタイムゾーン"""

    # === CORS Settings ===
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in get_str_env(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
    ]
    """CORSで許可するオリジンのリスト"""
```

### ai_api の Settings 作成

```python
# app/backend/ai_api/app/config/settings.py

from pydantic_settings import BaseSettings
from backend_shared.config.env_utils import get_str_env

class Settings(BaseSettings):
    GEMINI_API_KEY: str = get_str_env("GEMINI_API_KEY", "")
    """Gemini API キー（必須）"""

    GEMINI_API_URL: str = get_str_env(
        "GEMINI_API_URL",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    )
    """Gemini API エンドポイントURL"""

    class Config:
        env_file = ".env"
        case_sensitive = True

def get_settings() -> Settings:
    return Settings()
```

### ledger_api の Settings 拡張

```python
# app/backend/ledger_api/app/settings.py

@dataclass(slots=True)
class Settings:
    # ... 既存フィールド ...

    report_artifact_secret: str
    """レポートアーティファクトURL署名用シークレット（必須）"""

def load_settings() -> Settings:
    # ... 既存コード ...

    report_artifact_secret = os.getenv("REPORT_ARTIFACT_SECRET")
    if not report_artifact_secret or report_artifact_secret == "change-me-in-production":
        stage = os.getenv("STAGE", "dev").lower()
        if stage in {"stg", "prod"}:
            raise ValueError(
                "REPORT_ARTIFACT_SECRET must be set to a strong secret in stg/prod environments"
            )

    return Settings(
        # ... 既存引数 ...
        report_artifact_secret=report_artifact_secret or "dev-default-secret",
    )
```

## 🔧 DI Providers での利用例

### core_api の IapAuthProvider

```python
# app/backend/core_api/app/config/di_providers.py

from app.config.settings import get_settings

def provide_auth_provider() -> IAuthProvider:
    """認証プロバイダーを提供"""
    settings = get_settings()

    if settings.IAP_ENABLED:
        return IapAuthProvider(
            allowed_domain=settings.ALLOWED_EMAIL_DOMAIN,
            iap_audience=settings.IAP_AUDIENCE,
            public_key_url=settings.IAP_PUBLIC_KEY_URL,  # 新規追加
        )
    else:
        return DevAuthProvider()
```

### ai_api の Gemini Client

```python
# app/backend/ai_api/app/config/di_providers.py

from app.config.settings import get_settings

def provide_gemini_client() -> GeminiClient:
    """Gemini APIクライアントを提供"""
    settings = get_settings()

    return GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        api_url=settings.GEMINI_API_URL,  # 新規追加
    )
```

### backend_shared の共通ユーティリティ化

```python
# backend_shared/src/backend_shared/config/timezone_utils.py (新規作成)

import os
from zoneinfo import ZoneInfo
from datetime import datetime

def get_app_timezone() -> ZoneInfo:
    """アプリケーションのタイムゾーンを取得"""
    tz_name = os.getenv("APP_TIMEZONE", "Asia/Tokyo")
    return ZoneInfo(tz_name)

def now_in_app_timezone() -> datetime:
    """アプリケーションタイムゾーンでの現在時刻を取得"""
    return datetime.now(get_app_timezone())
```

## 📝 移行手順

### Phase 1: 環境変数の追加（影響なし）

1. `.env.common` に新しい環境変数を追加（デフォルト値は現状維持）
2. `secrets/.env.*.secrets` にシークレット系変数を追加
3. Git にコミット（既存動作に影響なし）

### Phase 2: Settings クラスの拡張

1. 各サービスの `settings.py` に新しいフィールドを追加
2. 既存のハードコード値をデフォルト値として設定（後方互換性維持）
3. ユニットテストで設定値の読み込みを確認

### Phase 3: コード内のハードコード値を Settings 経由に変更

1. `IapAuthProvider` の初期化を Settings 経由に変更
2. `GeminiClient` の初期化を Settings 経由に変更
3. タイムゾーン処理を共通ユーティリティに統一

### Phase 4: 本番環境での secrets 設定

1. ステージング環境で `REPORT_ARTIFACT_SECRET` を強力なランダム値に設定
2. 本番環境で `REPORT_ARTIFACT_SECRET` を強力なランダム値に設定
3. デフォルト値 "change-me-in-production" での起動を禁止する検証を追加

## ⚠️ 注意事項

### セキュリティ

- `ALLOWED_EMAIL_DOMAIN` は本番環境で必ず正しい値を設定すること
- `REPORT_ARTIFACT_SECRET` は推測不可能な強力なランダム文字列を使用すること
- シークレット系の値は必ず `secrets/` ディレクトリで管理し、Git にコミットしないこと

### 後方互換性

- すべての新しい環境変数には適切なデフォルト値を設定
- 既存の動作を変更しない
- デフォルト値は現在のハードコード値と同じにする

### デプロイ

- ステージング環境でまずテストする
- 本番環境では環境変数の設定を事前に準備する
- ロールバック時は環境変数の変更も戻すこと

## 🔗 関連ドキュメント

- [20251203_ENV_CONSOLIDATION.md](./20251203_ENV_CONSOLIDATION.md) - 環境変数統合の設計方針
- [20251203_SECURITY_AUDIT_REPORT.md](./20251203_SECURITY_AUDIT_REPORT.md) - セキュリティ監査レポート
- [backend_shared README](../app/backend/backend_shared/README.md) - 共通ライブラリの使用方法
