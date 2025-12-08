# Step 1: vm_stg / vm_prod 構成差分の洗い出し

**目的**: stg と prod の構成差分を明確化し、認証以外の設定をできるだけ統一する基盤を作る。

**作成日**: 2025-12-08

---

## 1. 環境変数ファイルの差分

### 1.1 env/.env.vm_stg vs env/.env.vm_prod

| キー名 | vm_stg の値 | vm_prod の値 | 差分の性質 |
|--------|-------------|--------------|-----------|
| **APP_TAG** | `stg` | `prod` | ✅ 環境識別子（妥当な差分） |
| **STAGE** | `stg` | `prod` | ✅ 環境識別子（妥当な差分） |
| **NODE_ENV** | `staging` | `production` | ✅ 環境識別子（妥当な差分） |
| **PUBLIC_BASE_URL** | `https://stg.sanbou-app.jp` | `https://sanbou-app.jp` | ✅ 環境別URL（妥当な差分） |
| **DEBUG** | `false` | `false` | ✅ 共通設定 |
| **IAP_ENABLED** | `true` | `true` | ⚠️ 両方trueだが、stgでは実際にIAP不要 |
| **IAP_AUDIENCE** | （空） | （空） | ⚠️ 両方空だが、prodでは必須のはず |
| **POSTGRES_USER** | `sanbou_app_stg` | `sanbou_app_prod` | ✅ 環境別ユーザー（妥当な差分） |
| **POSTGRES_DB** | `sanbou_stg` | `sanbou_prod` | ✅ 環境別DB（妥当な差分） |
| **RAG_GCS_URI** | `gs://sanbouapp-stg/...` | （空） | ⚠️ 片方のみ設定 |
| **STARTUP_DOWNLOAD_ENABLE** | `True` | （空） | ⚠️ キーの有無が違う |
| **STRICT_STARTUP** | `false` | `false` | ✅ 共通設定 |
| **GCS_LEDGER_BUCKET_xxx** | （全て設定） | （全て設定） | ✅ 共通設定 |
| **STG_NGINX_HTTP_PORT** | `80` | - | ⚠️ stgのみ定義 |
| **STG_NGINX_HTTPS_PORT** | `443` | - | ⚠️ stgのみ定義 |
| **POLL_INTERVAL** | - | `10` | ⚠️ prodのみ定義 |

### 1.2 問題点

1. **IAP_ENABLED の矛盾**:
   - 両方 `true` になっているが、stg は VPN/Tailscale 経由で IAP を使わない想定
   - 実際の認証は `AUTH_MODE` で切り替えている（.env.common で定義）
   - **→ stg では IAP_ENABLED=false に変更すべき**

2. **キー名の不統一**:
   - `STG_NGINX_HTTP_PORT` / `STG_NGINX_HTTPS_PORT` が stg のみ定義
   - **→ 共通化するか、prod でも明示的に定義すべき**

3. **環境判定キーの多重化**:
   - `APP_TAG`, `STAGE`, `NODE_ENV` の3つが環境を表している
   - **→ `STAGE` に統一し、他はオプショナルにする**

---

## 2. docker-compose ファイルの差分

### 2.1 docker/docker-compose.stg.yml vs docker/docker-compose.prod.yml

| 項目 | vm_stg | vm_prod | 差分の性質 |
|------|--------|---------|-----------|
| **イメージソース** | `image: asia-northeast1-docker.pkg.dev/.../stg-latest` | `build: context + target: prod` | ⚠️ stgはpull、prodはbuild |
| **ネットワーク名** | `sanbou_stg_edge` / `sanbou_stg_app` / `sanbou_stg_data` | `sanbou_edge` / `sanbou_app` / `sanbou_data` | ✅ 環境別名前空間（妥当） |
| **nginx ポート** | `${STG_NGINX_HTTP_PORT:-8080}:80` / `${STG_NGINX_HTTPS_PORT:-8443}:443` | `80:80` / `443:443` | ⚠️ キー名が違う |
| **db ポート** | `5432:5432` | `127.0.0.1:5432:5432` | ⚠️ prodは127.0.0.1に制限 |
| **healthcheck test** | `curl -f http://localhost:8000/health` (core_api) | `curl -f http://localhost:8000/api/healthz` | ⚠️ パスが違う |
| **logging** | 全て共通 | 全て共通 | ✅ 共通設定 |
| **depends_on** | 全て `- db` | 全て `- db` | ✅ 共通設定 |
| **POLL_INTERVAL** | - | `'10'` | ⚠️ prodのみ定義 |

### 2.2 問題点

1. **イメージソースの違い**:
   - stg: pre-built image を pull
   - prod: Dockerfile から build
   - **→ 両方とも pre-built image に統一すべき（CI/CD で build）**

2. **healthcheck パスの不統一**:
   - stg: `/health`
   - prod: `/api/healthz`
   - **→ `/health` に統一すべき**

3. **ポートマッピングの差異**:
   - nginx のポート定義方法が違う
   - **→ 環境変数名を統一し、デフォルト値だけを変える**

---

## 3. 認証まわりの差分

### 3.1 現在の認証実装（app/backend/core_api）

#### 3.1.1 認証プロバイダー

| プロバイダー | ファイルパス | 用途 |
|-------------|-------------|------|
| **DevAuthProvider** | `app/infra/adapters/auth/dev_auth_provider.py` | local_dev 用固定ユーザー |
| **VpnAuthProvider** | `app/infra/adapters/auth/vpn_auth_provider.py` | vm_stg 用固定ユーザー（VPN経由） |
| **IapAuthProvider** | `app/infra/adapters/auth/iap_auth_provider.py` | vm_prod 用 IAP JWT 検証 |

#### 3.1.2 認証切り替えの仕組み

**app/deps.py**: `get_auth_provider()` 関数

```python
auth_mode = os.getenv("AUTH_MODE", "dummy").lower()

if auth_mode == "dummy":
    return DevAuthProvider()
elif auth_mode == "vpn_dummy":
    return VpnAuthProvider()
elif auth_mode == "iap":
    return IapAuthProvider()
```

**env/.env.common** で定義:
```
AUTH_MODE=dummy  # デフォルト値
```

**各環境での上書き**:
- local_dev: `AUTH_MODE=dummy` （.env.common のデフォルト）
- vm_stg: `AUTH_MODE=vpn_dummy` （.env.vm_stg で上書き必要）
- vm_prod: `AUTH_MODE=iap` （.env.vm_prod で上書き必要）

#### 3.1.3 問題点

1. **AUTH_MODE の明示的な定義が不足**:
   - `.env.vm_stg` / `.env.vm_prod` に `AUTH_MODE` の記載がない
   - デフォルトの `dummy` が使われている可能性がある
   - **→ 各環境ファイルに明示的に記載すべき**

2. **IAP_ENABLED と AUTH_MODE の二重管理**:
   - `IAP_ENABLED=true/false` と `AUTH_MODE=iap/vpn_dummy/dummy` が並存
   - **→ AUTH_MODE に一本化すべき**

3. **di_providers.py の認証ロジックが重複**:
   - `app/config/di_providers.py` の `get_auth_provider()` は IAP_ENABLED ベース
   - `app/deps.py` の `get_auth_provider()` は AUTH_MODE ベース
   - **→ どちらかに統一すべき（deps.py を優先推奨）**

---

## 4. config/di_providers.py の環境判定

### 4.1 STAGE の参照箇所

```python
# 549行目: 本番環境でのバリデーション
if settings.STAGE == "prod":
    if not settings.IAP_ENABLED:
        raise ValueError("IAP_ENABLED must be 'true' in production!")
    if not settings.IAP_AUDIENCE:
        raise ValueError("IAP_AUDIENCE must be set in production!")
```

### 4.2 問題点

1. **STAGE の値**:
   - `.env.vm_stg`: `STAGE=stg`
   - `.env.vm_prod`: `STAGE=prod`
   - ✅ 統一されている

2. **IAP_ENABLED の強制**:
   - prod では IAP_ENABLED=true が必須
   - しかし実際の認証は AUTH_MODE で制御している
   - **→ IAP_ENABLED ロジックは削除し、AUTH_MODE のみで判定すべき**

---

## 5. backend_shared の環境判定

### 5.1 env_utils.py の get_stage()

```python
def get_stage() -> str:
    """
    デプロイ環境を取得（dev/stg/prod）
    
    環境変数 STAGE で設定可能。
    デフォルトは 'dev'。
    """
    return get_str_env("STAGE", default="dev")
```

### 5.2 base_settings.py

```python
class BaseAppSettings(BaseSettings):
    STAGE: str = get_stage()
```

### 5.3 評価

✅ **問題なし**: `STAGE` で統一されている。

---

## 6. フロントエンド側の環境差分

### 6.1 想定される環境変数（要確認）

- `VITE_APP_STAGE` または `VITE_STAGE`
- `VITE_API_BASE_URL`
- `VITE_PUBLIC_BASE_URL`

### 6.2 TODO

- [ ] `app/frontend/.env.*` ファイルを確認
- [ ] stg/prod で異なる環境変数キーがないかチェック
- [ ] `/auth/me` を叩く実装があるか確認

---

## 7. まとめと修正方針

### 7.1 統一すべき点（認証以外）

| 項目 | 現状 | 修正後 |
|------|------|-------|
| **環境判定キー** | `APP_TAG`, `STAGE`, `NODE_ENV` | `STAGE` のみ（他は派生値） |
| **docker-compose イメージソース** | stg=pull, prod=build | 両方 pull（CI/CD で build） |
| **healthcheck パス** | `/health` vs `/api/healthz` | `/health` に統一 |
| **nginx ポート環境変数** | `STG_NGINX_*` vs 直書き | 統一キー名 + デフォルト値 |
| **db ポート制限** | stg=全開放, prod=127.0.0.1 | 両方 127.0.0.1（推奨） |
| **POLL_INTERVAL** | prodのみ定義 | 両方 .env に明示 |

### 7.2 認証で分ける点

| 項目 | dev | stg | prod |
|------|-----|-----|------|
| **AUTH_MODE** | `dummy` | `vpn_dummy` | `iap` |
| **IAP_ENABLED** | `false` | `false` | `true` |
| **IAP_AUDIENCE** | - | - | 必須 |
| **VPN_USER_EMAIL** | - | 設定推奨 | - |
| **依存関数** | DevAuthProvider | VpnAuthProvider | IapAuthProvider |

### 7.3 削除すべき重複ロジック

- [ ] `app/config/di_providers.py` の `get_auth_provider()` → 削除
- [ ] `IAP_ENABLED` による分岐 → `AUTH_MODE` に一本化
- [ ] `APP_TAG`, `NODE_ENV` → `STAGE` から派生させる

---

## 次のステップ

✅ **Step 1 完了**: 差分一覧を作成

次は **Step 2**: 環境判定の単純化（STAGE / AUTH_MODE を揃える）

