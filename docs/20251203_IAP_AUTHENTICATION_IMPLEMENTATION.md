# IAP 認証実装完了レポート

**実装日**: 2025-12-03  
**ブランチ**: security/iap-authentication  
**対象**: sanbou_app - Google Cloud IAP 認証統合

---

## 概要

Google Cloud Identity-Aware Proxy (IAP) を使用した認証基盤を実装しました。
本番環境では「Googleアカウントでログインしていないと一切入れない」構成となり、
開発環境では固定ユーザー（DevAuthProvider）を使用して開発を継続できます。

---

## 実装内容

### 1. 環境変数の追加

全環境ファイル（`.env.common`, `.env.local_dev`, `.env.vm_stg`, `.env.vm_prod`）に以下を追加：

```bash
# === Security / Authentication ===
DEBUG=false                    # デバッグモード (本番は false 必須)
IAP_ENABLED=false              # IAP 有効化フラグ
IAP_AUDIENCE=                  # IAP の audience 値（JWT 検証用）
```

**環境別設定:**
- **開発環境** (`local_dev`): `DEBUG=true`, `IAP_ENABLED=false`
- **ステージング** (`vm_stg`): `DEBUG=false`, `IAP_ENABLED=true`
- **本番環境** (`vm_prod`): `DEBUG=false`, `IAP_ENABLED=true`

### 2. IapAuthProvider の強化

**ファイル**: `app/backend/core_api/app/infra/adapters/auth/iap_auth_provider.py`

**強化内容:**
- JWT 署名検証機能を追加（`google-auth` ライブラリ使用）
- `X-Goog-IAP-JWT-Assertion` ヘッダーの検証
- フォールバック: `X-Goog-Authenticated-User-Email` ヘッダー対応
- ドメインホワイトリスト（`@honest-recycle.co.jp`）による認可
- 詳細なロギングとエラーハンドリング

**JWT 検証フロー:**
```python
1. X-Goog-IAP-JWT-Assertion ヘッダーを取得
2. Google の公開鍵で署名を検証
3. audience 値を環境変数 IAP_AUDIENCE と照合
4. JWT から email を抽出
5. ドメインチェック (@honest-recycle.co.jp)
6. AuthUser オブジェクトを返却
```

### 3. FastAPI Dependency の実装

**ファイル**: `app/backend/core_api/app/deps.py`

**追加した依存関係:**

```python
# 認証プロバイダーのファクトリー
def get_auth_provider() -> IAuthProvider:
    """環境変数に基づいて適切な認証プロバイダーを返す"""
    iap_enabled = os.getenv("IAP_ENABLED", "false").lower() == "true"
    return IapAuthProvider() if iap_enabled else DevAuthProvider()

# 必須認証
async def get_current_user(
    request: Request,
    auth_provider: IAuthProvider = Depends(get_auth_provider)
) -> AuthUser:
    """全ての保護されたエンドポイントで使用"""
    return await auth_provider.get_current_user(request)

# オプショナル認証
async def get_optional_user(
    request: Request,
    auth_provider: IAuthProvider = Depends(get_auth_provider)
) -> AuthUser | None:
    """公開エンドポイントで「ログイン済みなら追加情報を返す」用途"""
    try:
        return await auth_provider.get_current_user(request)
    except Exception:
        return None
```

### 4. /docs エンドポイントの保護

全 API サービス（core_api, ai_api, ledger_api, rag_api, manual_api）で
`DEBUG=false` 時に `/docs`, `/redoc`, `/openapi.json` を無効化：

```python
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

app = FastAPI(
    title="Core API",
    # 本番環境（DEBUG=False）では /docs と /redoc を無効化
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    openapi_url="/openapi.json" if DEBUG else None,
)
```

### 5. 認証ミドルウェアの実装

**ファイル**: `app/backend/core_api/app/api/middleware/auth_middleware.py`

**機能:**
- 全リクエストで認証を実施（除外パスを除く）
- 除外パス: `/health`, `/healthz`, `/`, `/docs`, `/redoc`, `/openapi.json`
- `IAP_ENABLED=false` の場合は DevAuthProvider を使用
- 認証済みユーザーを `request.state.user` に保存
- 認証失敗時は 401/403 を返却

**適用方法:**
```python
from app.api.middleware.auth_middleware import AuthenticationMiddleware

app.add_middleware(
    AuthenticationMiddleware,
    excluded_paths=["/health", "/healthz", "/", "/docs", "/redoc", "/openapi.json"]
)
```

### 6. nginx 設定の更新

**ファイル**: `app/nginx/conf.d/_proxy_headers.conf`

IAP ヘッダーをバックエンドに転送する設定を追加：

```nginx
# IAP (Identity-Aware Proxy) headers
proxy_set_header X-Goog-Authenticated-User-Email $http_x_goog_authenticated_user_email;
proxy_set_header X-Goog-Authenticated-User-Id $http_x_goog_authenticated_user_id;
proxy_set_header X-Goog-IAP-JWT-Assertion $http_x_goog_iap_jwt_assertion;
```

---

## GCP IAP セットアップガイド

### 前提条件

- GCP プロジェクトが作成済み
- HTTPS Load Balancer が構成済み
- バックエンドサービスが登録済み

### Step 1: OAuth 同意画面の設定

1. **GCP コンソール** → **APIs & Services** → **OAuth consent screen**
2. **User Type**: Internal（組織内ユーザーのみ）
3. **App information** を入力
4. **Scopes**: デフォルトのまま
5. **Save and Continue**

### Step 2: OAuth 2.0 クライアントの作成

1. **Credentials** → **Create Credentials** → **OAuth client ID**
2. **Application type**: Web application
3. **Name**: `sanbou-app-iap`
4. **Authorized redirect URIs**: 
   - `https://your-domain.com/_gcp_gatekeeper/authenticate`
5. **Create** → クライアント ID をメモ

### Step 3: IAP の有効化

1. **Security** → **Identity-Aware Proxy**
2. バックエンドサービスの横にある **IAP** トグルをオン
3. OAuth クライアントを選択
4. **Turn On**

### Step 4: アクセス権限の設定

1. IAP ページでバックエンドサービスを選択
2. **Add Principal** をクリック
3. **New principals**: 
   - 個別ユーザー: `user@honest-recycle.co.jp`
   - グループ: `developers@honest-recycle.co.jp`
4. **Role**: `IAP-secured Web App User`
5. **Save**

### Step 5: IAP_AUDIENCE の取得と設定

1. **Security** → **Identity-Aware Proxy**
2. バックエンドサービスの **⋮** → **Edit OAuth Client**
3. **Audience** 値をコピー（形式: `/projects/PROJECT_NUMBER/global/backendServices/SERVICE_ID`）
4. `.env.vm_stg` と `.env.vm_prod` に設定：

```bash
IAP_AUDIENCE=/projects/123456789/global/backendServices/987654321
```

### Step 6: デプロイと検証

1. 環境変数を更新してデプロイ：
```bash
# ステージング環境
make rebuild ENV=vm_stg

# 本番環境
make rebuild ENV=vm_prod
```

2. ブラウザでアクセス:
   - `https://your-domain.com/` → Google ログイン画面が表示される
   - ログイン後、アプリケーションが表示される

3. ログを確認:
```bash
make logs ENV=vm_prod S=core_api | grep "IAP"
```

---

## テスト方法

### 開発環境（IAP 無効）

```bash
# 起動
make up ENV=local_dev

# ヘルスチェック
curl http://localhost:8003/health
# => {"status":"ok"}

# 保護されたエンドポイント（DevAuthProvider が自動適用）
curl http://localhost:8003/api/kpi/overview
# => 正常にデータが返却される
```

### ステージング/本番環境（IAP 有効）

```bash
# IAP ヘッダーなしでアクセス → 401
curl https://stg.sanbou-app.jp/api/kpi/overview
# => {"error":{"code":"AUTHENTICATION_REQUIRED","message":"Authentication required"}}

# IAP ヘッダーありでアクセス（GCP Load Balancer 経由）→ 200
# ブラウザでアクセスすると Google ログイン後に正常動作
```

### JWT 検証のテスト

```bash
# ログで JWT 検証を確認
docker logs <container_id> | grep "IAP JWT"
# => "IAP JWT authentication successful" が表示される
```

---

## トラブルシューティング

### 問題: "Authentication required (IAP headers not found)"

**原因**: IAP ヘッダーが届いていない

**解決策**:
1. IAP が有効化されているか確認
2. nginx の `_proxy_headers.conf` が正しく設定されているか確認
3. Load Balancer → nginx → backend の経路を確認

### 問題: "Invalid IAP token: Audience doesn't match"

**原因**: `IAP_AUDIENCE` が正しく設定されていない

**解決策**:
1. GCP コンソールで正しい audience 値を取得
2. `.env.vm_stg` または `.env.vm_prod` を更新
3. コンテナを再起動

### 問題: "Access denied: Only @honest-recycle.co.jp users are allowed"

**原因**: 許可されていないドメインのユーザーがアクセスしている

**解決策**:
1. `IapAuthProvider` の `allowed_domain` を確認
2. 別ドメインを許可する場合は、コードを修正して再デプロイ

### 問題: /docs が表示されない

**原因**: `DEBUG=false` の場合、意図的に無効化されている

**解決策**:
- 開発環境で確認する: `DEBUG=true` に設定
- 本番環境では `/docs` へのアクセスは不要（セキュリティ上の理由）

---

## セキュリティ考慮事項

### ✅ 実装済み

1. **JWT 署名検証**: Google の公開鍵で署名を検証
2. **ドメインホワイトリスト**: `@honest-recycle.co.jp` のみ許可
3. **/docs の無効化**: 本番環境で API ドキュメントを非公開
4. **IAP ヘッダー転送**: nginx が IAP ヘッダーをバックエンドに転送
5. **認証ミドルウェア**: 全リクエストで認証を実施

### 🔄 今後の改善

1. **ロール・権限管理**: ユーザーロールに基づくアクセス制御
2. **監査ログ**: 認証イベントの詳細ログ記録
3. **レート制限**: API 呼び出しのレート制限実装
4. **CORS 設定**: 本番環境で CORS を適切に制限

---

## 関連ドキュメント

- [認証基盤実装レポート](20251202_AUTH_INFRASTRUCTURE_IMPLEMENTATION.md)
- [セキュリティ監査レポート](20251203_SECURITY_AUDIT_REPORT.md)
- [Google Cloud IAP ドキュメント](https://cloud.google.com/iap/docs)

---

## まとめ

IAP 認証の実装により、以下を達成しました：

✅ **最低ラインのセキュリティ確保**: 「URLを知っていれば誰でもアクセスできる」状態を解消  
✅ **Google アカウント認証**: 組織の Google アカウントでのみアクセス可能  
✅ **開発環境との両立**: 開発時は固定ユーザー、本番時は IAP 認証  
✅ **JWT 署名検証**: なりすまし攻撃への対策  
✅ **ドメインホワイトリスト**: 組織外ユーザーの遮断  

本番公開前に必ず IAP を有効化し、`IAP_AUDIENCE` を正しく設定してください。
