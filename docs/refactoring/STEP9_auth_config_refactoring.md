# Step 9: 認証設定のリファクタリング

**実施日**: 2025-12-08  
**目的**: 認証関連のハードコード値を環境変数に移行し、設定管理を統一化

---

## 実施内容

### 1. 問題点の特定

#### ベタ打ちされていた値

- **DevAuthProvider**: 開発ユーザー情報がハードコード

  - `email="dev-user@example.com"`
  - `display_name="開発ユーザー"`
  - `user_id="dev_001"`
  - `role="admin"`

- **VpnAuthProvider**: デフォルト値がハードコード
  - `VPN_USER_EMAIL` のデフォルト: `"vpn-user@example.com"`

#### 設計上の課題

- テスト環境ごとにユーザー情報を変更できない
- 環境変数の設定場所が不明確
- secrets ファイルに認証設定の記載がない

---

## 2. リファクタリング内容

### 2.1 DevAuthProvider の環境変数化

#### Before

```python
self._dev_user = AuthUser(
    email="dev-user@example.com",
    display_name="開発ユーザー",
    user_id="dev_001",
    role="admin",
)
```

#### After

```python
dev_email = os.getenv("DEV_USER_EMAIL", "dev-user@example.com")
dev_name = os.getenv("DEV_USER_NAME", "開発ユーザー")
dev_id = os.getenv("DEV_USER_ID", "dev_001")
dev_role = os.getenv("DEV_USER_ROLE", "admin")

self._dev_user = AuthUser(
    email=dev_email,
    display_name=dev_name,
    user_id=dev_id,
    role=dev_role,
)
```

**効果**:

- ✅ テスト環境ごとにユーザー情報をカスタマイズ可能
- ✅ デフォルト値は互換性のため維持
- ✅ ログに環境変数ソースを明記

### 2.2 VpnAuthProvider の必須化と強化

#### Before

```python
self._vpn_user_email = os.getenv("VPN_USER_EMAIL", "vpn-user@example.com")
self._vpn_user_display_name = os.getenv("VPN_USER_NAME", "VPN User")
```

#### After

```python
self._vpn_user_email = os.getenv("VPN_USER_EMAIL")
if not self._vpn_user_email:
    raise ValueError(
        "VPN_USER_EMAIL environment variable is required for VPN auth mode. "
        "Please set it in secrets/.env.vm_stg.secrets"
    )

self._vpn_user_display_name = os.getenv("VPN_USER_NAME", "VPN User")
self._vpn_user_id = os.getenv("VPN_USER_ID", "vpn_001")

# AuthUser 生成時に user_id を追加
return AuthUser(
    email=self._vpn_user_email,
    display_name=self._vpn_user_display_name,
    user_id=self._vpn_user_id,  # ← 追加
)
```

**効果**:

- ✅ VPN_USER_EMAIL の明示的な設定を強制（セキュリティ向上）
- ✅ エラーメッセージで設定場所を明示
- ✅ user_id の追加でユーザー識別を一貫化

### 2.3 secrets ファイルの整備

#### secrets/.env.secrets.template

```bash
# === Authentication Settings (環境別設定) ===
# 開発環境（local_dev, local_demo）: AUTH_MODE=dummy
DEV_USER_EMAIL=<YOUR_DEV_EMAIL>
DEV_USER_NAME=<YOUR_DEV_NAME>
DEV_USER_ID=dev_001
DEV_USER_ROLE=admin

# VPN 環境（vm_stg）: AUTH_MODE=vpn_dummy
# 注意: VPN_USER_EMAIL は必須です（secrets/.env.vm_stg.secrets に設定）
VPN_USER_EMAIL=<YOUR_VPN_EMAIL>
VPN_USER_NAME=<YOUR_VPN_NAME>
VPN_USER_ID=vpn_001

# IAP 環境（vm_prod）: AUTH_MODE=iap
# IAP_AUDIENCE は必須です（secrets/.env.vm_prod.secrets に設定）
IAP_AUDIENCE=<YOUR_IAP_AUDIENCE>
```

#### secrets/.env.local_dev.secrets

```bash
# === Authentication Settings ===
DEV_USER_EMAIL=<YOUR_DEV_EMAIL>
DEV_USER_NAME=<YOUR_DEV_NAME>
DEV_USER_ID=dev_001
DEV_USER_ROLE=admin
```

#### secrets/.env.local_demo.secrets

```bash
# === Authentication Settings ===
DEV_USER_EMAIL=<YOUR_DEMO_EMAIL>
DEV_USER_NAME=<YOUR_DEMO_NAME>
DEV_USER_ID=demo_001
DEV_USER_ROLE=viewer  # デモは閲覧のみ
```

#### secrets/.env.vm_stg.secrets

```bash
# === Authentication Settings ===
# VPN 環境用ユーザー（AUTH_MODE=vpn_dummy）
VPN_USER_EMAIL=<YOUR_VPN_EMAIL>
VPN_USER_NAME=<YOUR_VPN_NAME>
VPN_USER_ID=vpn_001
```

#### secrets/.env.vm_prod.secrets

```bash
# === Authentication Settings ===
# 本番環境（AUTH_MODE=iap）
IAP_AUDIENCE=
```

---

## 3. リファクタリング設計書への準拠

### 3.1 機能同等性の担保（ルール 3）

| 項目               | 変更前                                 | 変更後       | 互換性                                  |
| ------------------ | -------------------------------------- | ------------ | --------------------------------------- |
| **API I/F**        | `/auth/me`                             | `/auth/me`   | ✅ 変更なし                             |
| **レスポンス構造** | `{email, display_name, user_id, role}` | 同左         | ✅ 変更なし                             |
| **デフォルト動作** | `dev-user@honest-recycle.co.jp`        | 同左         | ✅ 変更なし                             |
| **VPN必須化**      | デフォルト値あり                       | 起動時エラー | ⚠️ **意図的な変更**（セキュリティ向上） |

### 3.2 小さくリファクタリングを行う（ルール 2）

✅ 認証設定のみに限定

- 認証プロバイダー以外のコードは変更なし
- 1 PR で完結可能な規模

### 3.3 セキュリティ強化

| 項目                 | 変更前                 | 変更後                 |
| -------------------- | ---------------------- | ---------------------- |
| **VPN設定**          | デフォルト値で起動可能 | 必須設定化             |
| **エラーメッセージ** | なし                   | 設定ファイル名を明示   |
| **ログ出力**         | user_email のみ        | + user_id, source 追加 |

### 3.4 テスト容易性の向上

```python
# テストで環境変数を差し替え可能
import os
os.environ["DEV_USER_EMAIL"] = "test@example.com"
os.environ["DEV_USER_ROLE"] = "viewer"
provider = DevAuthProvider()
```

---

## 4. 変更ファイル一覧

### バックエンド実装

- ✏️ `app/backend/core_api/app/infra/adapters/auth/dev_auth_provider.py`

  - 環境変数ベースのユーザー情報読み込み
  - ログに metadata 追加

- ✏️ `app/backend/core_api/app/infra/adapters/auth/vpn_auth_provider.py`
  - VPN_USER_EMAIL の必須化
  - VPN_USER_ID の追加
  - AuthUser 生成時に user_id を含める

### 設定ファイル

- ✏️ `secrets/.env.secrets.template`

  - 認証関連環境変数のセクション追加
  - 環境別の設定例を明記

- ✏️ `secrets/.env.local_dev.secrets`

  - DEV*USER*\* 環境変数を追加

- ✏️ `secrets/.env.local_demo.secrets`

  - DEV*USER*\* 環境変数を追加（デモ用カスタマイズ）

- ✏️ `secrets/.env.vm_stg.secrets`

  - VPN*USER*\* 環境変数を追加

- ✏️ `secrets/.env.vm_prod.secrets`
  - IAP_AUDIENCE のコメント追加

---

## 5. 動作確認チェックリスト

### ✅ local_dev 環境

```bash
# 起動確認
make up ENV=local_dev

# 認証テスト
curl http://localhost:8003/auth/me

# 期待値
{
  "email": "<YOUR_DEV_EMAIL>",
  "display_name": "<YOUR_DEV_NAME>",
  "user_id": "dev_001",
  "role": "admin"
}
```

### ✅ local_demo 環境

```bash
make up ENV=local_demo
curl http://localhost:8003/auth/me

# 期待値（デモ用にカスタマイズ）
{
  "email": "<YOUR_DEMO_EMAIL>",
  "display_name": "<YOUR_DEMO_NAME>",
  "user_id": "demo_001",
  "role": "viewer"
}
```

### ✅ vm_stg 環境

```bash
make up ENV=vm_stg
curl http://stg.sanbou-app.jp/auth/me

# 期待値
{
  "email": "<YOUR_VPN_EMAIL>",
  "display_name": "<YOUR_VPN_NAME>",
  "user_id": "vpn_001"
}

# VPN_USER_EMAIL 未設定時
# → ValueError: VPN_USER_EMAIL environment variable is required...
```

### ✅ vm_prod 環境

```bash
# IAP_AUDIENCE 未設定時
# → ValueError: IAP_AUDIENCE is required in production...
```

---

## 6. 移行ガイド

### 既存環境の移行手順

#### Step 1: secrets ファイルのバックアップ

```bash
cp secrets/.env.local_dev.secrets secrets/.env.local_dev.secrets.bak
cp secrets/.env.vm_stg.secrets secrets/.env.vm_stg.secrets.bak
```

#### Step 2: 認証設定の追加

```bash
# local_dev
cat >> secrets/.env.local_dev.secrets << 'EOF'

# === Authentication Settings ===
DEV_USER_EMAIL=<YOUR_DEV_EMAIL>
DEV_USER_NAME=<YOUR_DEV_NAME>
DEV_USER_ID=dev_001
DEV_USER_ROLE=admin
EOF

# vm_stg
cat >> secrets/.env.vm_stg.secrets << 'EOF'

# === Authentication Settings ===
VPN_USER_EMAIL=<YOUR_VPN_EMAIL>
VPN_USER_NAME=<YOUR_VPN_NAME>
VPN_USER_ID=vpn_001
EOF
```

#### Step 3: 動作確認

```bash
# コンテナ再起動
make down ENV=local_dev
make up ENV=local_dev

# API テスト
curl http://localhost:8003/auth/me
```

---

## 7. ロールバック手順

### 問題が発生した場合

#### Git レベル

```bash
# このコミットをリバート
git revert <commit_hash>
```

#### 設定レベル

```bash
# バックアップから復元
cp secrets/.env.local_dev.secrets.bak secrets/.env.local_dev.secrets

# コンテナ再起動
make restart ENV=local_dev
```

---

## 8. 今後の改善案

### 8.1 環境変数のバリデーション強化

```python
# deps.py での起動時チェック追加
def validate_auth_settings():
    auth_mode = os.getenv("AUTH_MODE")
    stage = os.getenv("STAGE")

    if auth_mode == "dummy":
        if not os.getenv("DEV_USER_EMAIL"):
            logger.warning("DEV_USER_EMAIL not set, using default")

    elif auth_mode == "vpn_dummy":
        if not os.getenv("VPN_USER_EMAIL"):
            raise ValueError("VPN_USER_EMAIL is required for VPN auth mode")
```

### 8.2 設定の一元管理

```python
# config/auth_config.py を導入
@dataclass
class AuthConfig:
    mode: str
    dev_user: Optional[DevUserConfig] = None
    vpn_user: Optional[VpnUserConfig] = None
    iap_config: Optional[IapConfig] = None

    @classmethod
    def from_env(cls) -> "AuthConfig":
        # 環境変数から一括読み込み
        ...
```

### 8.3 テストの自動化

```python
# tests/integration/test_auth_providers.py
@pytest.mark.parametrize("auth_mode,expected_email", [
    ("dummy", "dev-user@honest-recycle.co.jp"),
    ("vpn_dummy", "stg-admin@honest-recycle.co.jp"),
])
def test_auth_provider_from_env(auth_mode, expected_email, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", auth_mode)
    # ...
```

---

## まとめ

### ✅ 達成できたこと

1. **ハードコード削減**

   - 認証ユーザー情報を環境変数化
   - テスト環境ごとのカスタマイズが可能に

2. **セキュリティ強化**

   - VPN_USER_EMAIL の必須化
   - エラーメッセージで設定場所を明示

3. **保守性向上**

   - secrets ファイルに設定が集約
   - テンプレートで設定項目が明確化

4. **テスト容易性向上**
   - 環境変数で動作をカスタマイズ可能
   - モックやスタブでのテストが容易に

### 📊 リファクタリング設計書への準拠

| ルール                     | 評価 | 備考                                   |
| -------------------------- | ---- | -------------------------------------- |
| **ブランチ運用**           | ✅   | feature/auth-magic-link-implementation |
| **小さくリファクタリング** | ✅   | 認証設定のみに限定                     |
| **機能同等性の担保**       | ✅   | API I/F は変更なし                     |
| **テスト戦略**             | ✅   | 動作確認チェックリスト整備             |

---

**リファクタリング完了日**: 2025-12-08  
**次のステップ**: 統合テストの自動化、設定バリデーションの強化
