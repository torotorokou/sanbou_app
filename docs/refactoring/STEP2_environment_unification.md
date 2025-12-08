# Step 2: 環境判定の単純化（STAGE / AUTH_MODE を揃える）

**目的**: 環境判定を `STAGE` に統一し、認証切り替えを `AUTH_MODE` に一本化する。

**作成日**: 2025-12-08

---

## 実施した変更

### 1. 環境変数ファイルの整理

#### 1.1 AUTH_MODE の明示的な定義

全ての環境ファイルに `AUTH_MODE` を明示的に追加しました。

| 環境 | ファイル | AUTH_MODE | 説明 |
|------|---------|-----------|------|
| **local_dev** | `env/.env.local_dev` | `dummy` | 開発用固定ユーザー |
| **local_demo** | `env/.env.local_demo` | `dummy` | デモ用固定ユーザー |
| **vm_stg** | `env/.env.vm_stg` | `vpn_dummy` | VPN経由固定ユーザー |
| **vm_prod** | `env/.env.vm_prod` | `iap` | IAP JWT検証 |

#### 1.2 IAP_ENABLED の整理

`AUTH_MODE` と一致するように `IAP_ENABLED` を調整しました。

| 環境 | AUTH_MODE | IAP_ENABLED | 変更 |
|------|-----------|-------------|------|
| **local_dev** | `dummy` | `false` | ✅ 変更なし |
| **local_demo** | `dummy` | `false` | ✅ 変更なし |
| **vm_stg** | `vpn_dummy` | `false` | 🔧 `true` → `false` に修正 |
| **vm_prod** | `iap` | `true` | ✅ 変更なし |

#### 1.3 VPN認証用の設定追加（vm_stg）

`env/.env.vm_stg` に VPN ユーザー設定のコメントを追加：

```bash
# === VPN Authentication ===
# VPN/Tailscale 経由アクセス用の固定ユーザー設定
# secrets/.env.vm_stg.secrets に以下を設定してください:
# VPN_USER_EMAIL=<YOUR_VPN_EMAIL>
# VPN_USER_NAME=STG Administrator
```

#### 1.4 環境識別子の整理

`STAGE` をプライマリ識別子とし、`APP_TAG` と `NODE_ENV` は派生値として明記：

**変更前**:
```bash
APP_TAG=stg
STAGE=stg
NODE_ENV=staging
```

**変更後**:
```bash
# === Environment Configuration ===
# STAGE: プライマリ環境識別子 (dev/stg/prod)
STAGE=stg
# APP_TAG: Docker タグ用 (STAGE から派生)
APP_TAG=stg
# NODE_ENV: Node.js 環境 (STAGE から派生)
NODE_ENV=staging
```

---

### 2. バックエンドコードの整理

#### 2.1 認証プロバイダーの一本化

**app/config/di_providers.py**:
- `get_auth_provider()` 関数を削除（重複排除）
- `app.deps.get_auth_provider()` を使用するように変更

**変更前**:
```python
# di_providers.py に IAP_ENABLED ベースの get_auth_provider() が存在
# deps.py にも AUTH_MODE ベースの get_auth_provider() が存在
# → 二重管理
```

**変更後**:
```python
# di_providers.py
from app.deps import get_auth_provider  # deps.py の関数を使用

def get_get_current_user_usecase(
    auth_provider: IAuthProvider = Depends(get_auth_provider)
) -> GetCurrentUserUseCase:
    """
    GetCurrentUserUseCase提供
    
    認証プロバイダーは app.deps.get_auth_provider() 経由で取得します。
    AUTH_MODE 環境変数に基づいて適切なプロバイダーを使用します。
    """
    return GetCurrentUserUseCase(auth_provider=auth_provider)
```

#### 2.2 本番環境での安全性チェック強化

**app/deps.py**:
- `get_auth_provider()` に本番環境チェックを追加

```python
def get_auth_provider() -> IAuthProvider:
    """
    環境変数 AUTH_MODE に基づいて適切な認証プロバイダーを返す（シングルトン）
    """
    global _auth_provider_instance
    
    if _auth_provider_instance is None:
        auth_mode = os.getenv("AUTH_MODE", "dummy").lower()
        stage = os.getenv("STAGE", "dev")
        
        # 本番環境での安全性チェック
        if stage == "prod":
            if auth_mode != "iap":
                raise ValueError(
                    f"🔴 SECURITY ERROR: Production must use AUTH_MODE=iap, got '{auth_mode}'"
                )
            iap_audience = os.getenv("IAP_AUDIENCE", "")
            if not iap_audience:
                raise ValueError(
                    "🔴 SECURITY ERROR: IAP_AUDIENCE must be set in production!"
                )
        
        # プロバイダーの生成...
```

---

## 変更の効果

### ✅ 達成できたこと

1. **環境判定の統一**:
   - `STAGE` をプライマリ識別子に統一
   - `APP_TAG` と `NODE_ENV` は派生値として明記

2. **認証切り替えの一本化**:
   - `AUTH_MODE` で認証方式を制御
   - `IAP_ENABLED` との二重管理を解消

3. **安全性の向上**:
   - 本番環境で `AUTH_MODE=iap` を強制
   - `IAP_AUDIENCE` の設定を強制

4. **可読性の向上**:
   - 各環境での認証方式が明確
   - コメントで設定意図を明記

### 🔍 残存する差異（妥当な差分）

| 項目 | dev | stg | prod | 理由 |
|------|-----|-----|------|------|
| **STAGE** | `dev` | `stg` | `prod` | 環境識別子 |
| **AUTH_MODE** | `dummy` | `vpn_dummy` | `iap` | 認証方式 |
| **IAP_ENABLED** | `false` | `false` | `true` | IAP使用有無 |
| **IAP_AUDIENCE** | - | - | 必須 | IAP設定 |
| **VPN_USER_*** | - | 設定推奨 | - | VPN認証 |
| **PUBLIC_BASE_URL** | localhost | stg.sanbou-app.jp | sanbou-app.jp | アクセスURL |
| **POSTGRES_USER** | sanbou_app_dev | sanbou_app_stg | sanbou_app_prod | DB分離 |
| **POSTGRES_DB** | sanbou_dev | sanbou_stg | sanbou_prod | DB分離 |

---

## 動作確認事項

### ✅ 確認が必要な項目

- [ ] **local_dev での起動**
  ```bash
  make up ENV=local_dev
  # AUTH_MODE=dummy で起動
  # DevAuthProvider が使用されることを確認
  ```

- [ ] **vm_stg での起動**
  ```bash
  make up ENV=vm_stg
  # AUTH_MODE=vpn_dummy で起動
  # VpnAuthProvider が使用されることを確認
  # secrets/.env.vm_stg.secrets に VPN_USER_EMAIL を設定（実際の値は機密情報のため別途管理）
  ```

- [ ] **vm_prod での起動**
  ```bash
  make up ENV=vm_prod
  # AUTH_MODE=iap で起動
  # IapAuthProvider が使用されることを確認
  # IAP_AUDIENCE が未設定の場合は起動エラー（期待通り）
  ```

- [ ] **本番環境での安全性チェック**
  - `STAGE=prod` かつ `AUTH_MODE≠iap` → 起動エラー ✅
  - `STAGE=prod` かつ `IAP_AUDIENCE` 未設定 → 起動エラー ✅

---

## 次のステップ

✅ **Step 2 完了**: 環境判定の単純化（STAGE / AUTH_MODE を揃える）

次は **Step 3**: 認証用の依存関数を「ダミー用」と「IAP用」に分離

### Step 3 で実施すること

1. `api/dependencies/auth.py` の作成（または既存の整理）
2. 以下の依存関数を定義:
   - `get_current_user_dummy() -> User`
   - `get_current_user_vpn() -> User`
   - `get_current_user_iap(request: Request) -> User`
3. 既存のプロバイダー実装との整合性確認

**注**: 既に `app/deps.py` に `get_current_user()` が実装されているため、Step 3 では既存実装の整理とドキュメント化が中心になります。

---

## 変更ファイル一覧

### 環境変数ファイル
- ✏️ `env/.env.local_dev` - AUTH_MODE 明示、環境識別子整理
- ✏️ `env/.env.local_demo` - AUTH_MODE 明示、環境識別子整理
- ✏️ `env/.env.vm_stg` - AUTH_MODE=vpn_dummy、IAP_ENABLED=false、VPN設定追加
- ✏️ `env/.env.vm_prod` - AUTH_MODE=iap 明示、環境識別子整理

### バックエンドコード
- ✏️ `app/backend/core_api/app/deps.py` - 本番環境チェック追加
- ✏️ `app/backend/core_api/app/config/di_providers.py` - 重複排除、deps.py を使用

### ドキュメント
- 📄 `docs/refactoring/STEP2_environment_unification.md` - 本ドキュメント

