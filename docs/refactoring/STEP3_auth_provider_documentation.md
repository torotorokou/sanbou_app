# Step 3: 認証用の依存関数の整理と `/auth/me` エンドポイントの統一

**目的**: 既存の認証プロバイダー実装を確認し、ドキュメントを整備して、環境ごとの認証切り替えを明確化する。

**作成日**: 2025-12-08

---

## 実施内容

### 1. 既存実装の確認

既存のコードベースを確認した結果、**既に適切な Clean Architecture 構造が実装されていました**：

#### 1.1 認証プロバイダーの実装状況

| プロバイダー | ファイルパス | 環境 | 実装状況 |
|-------------|-------------|------|---------|
| **DevAuthProvider** | `app/infra/adapters/auth/dev_auth_provider.py` | local_dev, local_demo | ✅ 実装済み |
| **VpnAuthProvider** | `app/infra/adapters/auth/vpn_auth_provider.py` | vm_stg | ✅ 実装済み |
| **IapAuthProvider** | `app/infra/adapters/auth/iap_auth_provider.py` | vm_prod | ✅ 実装済み |

#### 1.2 依存性注入の構造

```
app/deps.py
  └─ get_auth_provider() 
       ├─ AUTH_MODE=dummy → DevAuthProvider
       ├─ AUTH_MODE=vpn_dummy → VpnAuthProvider
       └─ AUTH_MODE=iap → IapAuthProvider

app/config/di_providers.py
  └─ get_get_current_user_usecase()
       └─ Depends(get_auth_provider)  # deps.py の関数を使用

app/core/usecases/auth/get_current_user.py
  └─ GetCurrentUserUseCase
       └─ IAuthProvider に委譲

app/api/routers/auth.py
  └─ GET /auth/me
       └─ Depends(get_get_current_user_usecase)
```

#### 1.3 ドメインモデル

```python
# app/core/domain/auth/entities.py
@dataclass(frozen=True)
class AuthUser:
    email: str
    display_name: str | None = None
    user_id: str | None = None
    role: str | None = None
```

✅ **評価**: 不変オブジェクト、認証方式に依存しない抽象的な表現、Clean Architecture のドメイン層として適切。

---

### 2. ドキュメント整備

既存実装は適切でしたが、ドキュメントが古く `IAP_ENABLED` ベースの説明になっていたため、`AUTH_MODE` ベースに更新しました。

#### 2.1 `/auth/me` エンドポイントのドキュメント更新

**app/api/routers/auth.py**:
- API ドキュメント（OpenAPI）を `AUTH_MODE` ベースの説明に更新
- 環境別のレスポンス例を追加（dev/stg/prod）

**変更前**:
```python
description="""
認証方式（Dev / IAP）は環境変数 IAP_ENABLED で切り替え可能です。
- IAP_ENABLED=false: 固定の開発用ユーザーを返す
- IAP_ENABLED=true: Google Cloud IAP のヘッダーから JWT を検証
"""
```

**変更後**:
```python
description="""
**認証方式は AUTH_MODE 環境変数で切り替え可能です：**

- `AUTH_MODE=dummy`: 固定の開発用ユーザーを返す（DevAuthProvider）
  - 使用環境: local_dev, local_demo
  
- `AUTH_MODE=vpn_dummy`: VPN経由の固定ユーザーを返す（VpnAuthProvider）
  - 使用環境: vm_stg（Tailscale/VPN経由）
  - VPN_USER_EMAIL, VPN_USER_NAME 環境変数で設定
  
- `AUTH_MODE=iap`: Google Cloud IAP の JWT を検証（IapAuthProvider）
  - 使用環境: vm_prod（本番環境）
  - IAP_AUDIENCE 環境変数に正しい audience 値の設定が必須
"""
```

#### 2.2 各プロバイダーのモジュールドキュメント更新

**DevAuthProvider** (`dev_auth_provider.py`):
```python
"""
【環境設定】
- AUTH_MODE=dummy
- 使用環境: local_dev, local_demo

【セキュリティ要件】
⚠️ 本番環境（STAGE=prod）では絶対に使用しないでください
   deps.py で起動時にバリデーションを実施しています
"""
```

**VpnAuthProvider** (`vpn_auth_provider.py`):
```python
"""
【環境設定】
- AUTH_MODE=vpn_dummy
- 使用環境: vm_stg
- 必須環境変数:
  - VPN_USER_EMAIL: VPN ユーザーのメールアドレス
  - VPN_USER_NAME: VPN ユーザーの表示名（オプション）

【セキュリティ要件】
⚠️ VPN/Tailscale でのアクセス制御が前提です
   ネットワークレベルで認証済みという前提で動作します
"""
```

**IapAuthProvider** (`iap_auth_provider.py`):
```python
"""
【環境設定】
- AUTH_MODE=iap
- 使用環境: vm_prod（本番環境）
- 必須環境変数:
  - IAP_AUDIENCE: IAP の audience 値（/projects/.../global/backendServices/... 形式）
  - ALLOWED_EMAIL_DOMAIN: 許可するメールドメイン（デフォルト: honest-recycle.co.jp）

【セキュリティ要件】
✅ 本番環境（STAGE=prod）では必須の認証プロバイダです
   deps.py で起動時に AUTH_MODE=iap と IAP_AUDIENCE の設定を強制します
"""
```

---

## 3. 認証フローの全体像

### 3.1 環境別の認証フロー

#### **local_dev / local_demo** (AUTH_MODE=dummy)
```
1. リクエスト → GET /auth/me
2. deps.py: get_auth_provider() → DevAuthProvider
3. DevAuthProvider.get_current_user(request)
   └─ 認証チェックなし、常に固定ユーザーを返す
4. レスポンス: {
     "email": "<DEV_USER_EMAIL>",
     "display_name": "開発ユーザー",
     "user_id": "dev_001",
     "role": "admin"
   }
```

#### **vm_stg** (AUTH_MODE=vpn_dummy)
```
1. リクエスト → GET /auth/me (VPN/Tailscale 経由)
2. deps.py: get_auth_provider() → VpnAuthProvider
3. VpnAuthProvider.get_current_user(request)
   └─ 環境変数 VPN_USER_EMAIL / VPN_USER_NAME から固定ユーザーを構築
4. レスポンス: {
     "email": "<VPN_USER_EMAIL>",
     "display_name": "STG Administrator",
     "user_id": null,
     "role": null
   }
```

#### **vm_prod** (AUTH_MODE=iap)
```
1. リクエスト → GET /auth/me (LB + IAP 経由)
   ├─ Header: X-Goog-IAP-JWT-Assertion: <JWT>
   └─ Header: X-Goog-Authenticated-User-Email: accounts.google.com:<USER_EMAIL>
2. deps.py: get_auth_provider() → IapAuthProvider
3. IapAuthProvider.get_current_user(request)
   ├─ JWT 署名を検証（IAP 公開鍵で検証）
   ├─ email を抽出
   ├─ ドメインチェック（許可されたドメインのみ）
   └─ AuthUser を構築
4. レスポンス: {
     "email": "<IAP_USER_EMAIL>",
     "display_name": "user",
     "user_id": "iap_user",
     "role": "user"
   }
```

### 3.2 セキュリティチェックポイント

| チェック項目 | 実装場所 | タイミング |
|-------------|---------|----------|
| **STAGE=prod で AUTH_MODE≠iap** | `deps.py:get_auth_provider()` | 起動時（初回呼び出し） |
| **STAGE=prod で IAP_AUDIENCE 未設定** | `deps.py:get_auth_provider()` | 起動時（初回呼び出し） |
| **JWT 署名検証** | `IapAuthProvider.get_current_user()` | リクエスト毎 |
| **メールドメインチェック** | `IapAuthProvider.get_current_user()` | リクエスト毎 |

---

## 4. 変更ファイル一覧

### バックエンドコード
- ✏️ `app/backend/core_api/app/api/routers/auth.py` - `/auth/me` エンドポイントのドキュメント更新
- ✏️ `app/backend/core_api/app/infra/adapters/auth/dev_auth_provider.py` - モジュールドキュメント更新
- ✏️ `app/backend/core_api/app/infra/adapters/auth/vpn_auth_provider.py` - モジュールドキュメント更新
- ✏️ `app/backend/core_api/app/infra/adapters/auth/iap_auth_provider.py` - モジュールドキュメント更新

### ドキュメント
- 📄 `docs/refactoring/STEP3_auth_provider_documentation.md` - 本ドキュメント

---

## 5. 動作確認事項

### ✅ 確認が必要な項目

- [ ] **GET /auth/me のレスポンス確認（local_dev）**
  ```bash
  curl http://localhost:8003/auth/me
  # 期待: {"email": "<DEV_USER_EMAIL>", "display_name": "<DEV_USER_NAME>", ...}
  ```

- [ ] **GET /auth/me のレスポンス確認（vm_stg）**
  ```bash
  # VPN_USER_EMAIL を secrets/.env.vm_stg.secrets に設定
  curl https://stg.sanbou-app.jp/auth/me
  # 期待: {"email": "<VPN_USER_EMAIL>", ...}
  ```

- [ ] **GET /auth/me のレスポンス確認（vm_prod）**
  ```bash
  # IAP 経由でアクセス
  curl https://sanbou-app.jp/auth/me
  # 期待: {"email": "<IAP_USER_EMAIL>", ...}
  ```

- [ ] **OpenAPI ドキュメントの確認**
  - http://localhost:8003/docs にアクセス
  - `/auth/me` エンドポイントのドキュメントが更新されていることを確認

- [ ] **本番環境での安全性チェック**
  - `STAGE=prod` かつ `AUTH_MODE=dummy` → 起動エラー ✅
  - `STAGE=prod` かつ `AUTH_MODE=vpn_dummy` → 起動エラー ✅
  - `STAGE=prod` かつ `IAP_AUDIENCE` 未設定 → 起動エラー ✅

---

## 6. アーキテクチャ評価

### ✅ Clean Architecture への準拠

| レイヤー | 実装 | 評価 |
|---------|------|------|
| **Domain** | `core/domain/auth/entities.py` | ✅ 不変オブジェクト、インフラ非依存 |
| **UseCase** | `core/usecases/auth/get_current_user.py` | ✅ プロバイダーへの委譲のみ、ビジネスロジックなし |
| **Ports** | `core/ports/auth/auth_provider.py` | ✅ インターフェース定義 |
| **Adapters** | `infra/adapters/auth/*_provider.py` | ✅ 各認証方式の具体実装 |
| **DI** | `deps.py`, `config/di_providers.py` | ✅ 環境変数ベースの切り替え |
| **API** | `api/routers/auth.py` | ✅ UseCase への委譲のみ |

### ✅ SOLID 原則への準拠

| 原則 | 評価 |
|-----|------|
| **単一責任原則 (SRP)** | ✅ 各プロバイダーは1つの認証方式のみを担当 |
| **開放閉鎖原則 (OCP)** | ✅ 新しい認証方式の追加は既存コード変更なし（プロバイダー追加のみ） |
| **リスコフの置換原則 (LSP)** | ✅ すべてのプロバイダーが IAuthProvider を実装 |
| **インターフェース分離原則 (ISP)** | ✅ IAuthProvider は最小限のメソッドのみ定義 |
| **依存性逆転原則 (DIP)** | ✅ UseCase はインターフェースに依存、具体実装に依存しない |

---

## 7. 次のステップ

✅ **Step 3 完了**: 認証用の依存関数の整理と `/auth/me` エンドポイントの統一

次は **Step 4**: APP_STAGE に応じて使う依存関数を切り替える

### Step 4 で実施すること

**注**: Step 3 の確認結果、既に適切な実装があるため、Step 4 は「既存実装の確認」が主になります。

1. `deps.py` の `get_auth_provider()` が既に環境変数ベースで切り替えを実装済み
2. 本番環境での安全性チェックも実装済み
3. **Step 4 では主にテストとドキュメント化を実施**:
   - 各環境での動作確認
   - 統合テストの追加（オプション）
   - フロントエンドとの連携確認

---

## 8. まとめ

### 実施済みの項目

✅ 既存の認証プロバイダー実装を確認（適切な Clean Architecture 構造を確認）  
✅ `/auth/me` エンドポイントのドキュメントを AUTH_MODE ベースに更新  
✅ 各プロバイダーのモジュールドキュメントに環境別の使い分けを明記  
✅ セキュリティ要件を明確化（本番環境での強制チェック）  

### 発見事項

1. **既存実装は既に適切な構造**:
   - Clean Architecture に沿った責務分離
   - SOLID 原則への準拠
   - 環境変数ベースの柔軟な切り替え

2. **ドキュメントの古さを解消**:
   - `IAP_ENABLED` ベースの説明 → `AUTH_MODE` ベースに更新
   - 環境別の設定方法を明確化

3. **セキュリティチェックは実装済み**:
   - 本番環境での AUTH_MODE/IAP_AUDIENCE 強制
   - 起動時バリデーション

---

## 付録: 環境変数設定例

### local_dev (.env.local_dev)
```bash
STAGE=dev
AUTH_MODE=dummy
DEBUG=true
```

### vm_stg (.env.vm_stg + secrets/.env.vm_stg.secrets)
```bash
# .env.vm_stg
STAGE=stg
AUTH_MODE=vpn_dummy
IAP_ENABLED=false
DEBUG=false

# secrets/.env.vm_stg.secrets
VPN_USER_EMAIL=<YOUR_VPN_EMAIL>
VPN_USER_NAME=<YOUR_VPN_NAME>
```

### vm_prod (.env.vm_prod + secrets/.env.vm_prod.secrets)
```bash
# .env.vm_prod
STAGE=prod
AUTH_MODE=iap
IAP_ENABLED=true
DEBUG=false

# secrets/.env.vm_prod.secrets
IAP_AUDIENCE=/projects/PROJECT_NUMBER/global/backendServices/SERVICE_ID
ALLOWED_EMAIL_DOMAIN=honest-recycle.co.jp
```

