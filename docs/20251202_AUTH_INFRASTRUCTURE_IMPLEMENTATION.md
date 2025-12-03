# 認証基盤実装完了レポート

**実装日**: 2025-12-02  
**対象**: sanbou_app - 現在ログインユーザー情報管理基盤

---

## 概要

既存リポジトリに「現在ログインしているユーザー情報を扱う基盤」を追加しました。
開発環境では固定ユーザー（DevAuthProvider）を使用し、本番環境では Google Cloud IAP（IapAuthProvider）に切り替え可能な柔軟な設計となっています。

---

## バックエンド実装内容

### 1. ドメイン層

#### `app/core/domain/auth/entities.py`
- **AuthUser** dataclass を定義
- 不変オブジェクト（`frozen=True`）として実装
- フィールド:
  - `email: str` - ユーザーのメールアドレス（一意識別子）
  - `display_name: str | None` - 表示名（オプション）

### 2. ポート層

#### `app/core/ports/auth/auth_provider.py`
- **IAuthProvider** 抽象インターフェースを定義
- `get_current_user(request: Request) -> AuthUser` メソッド
- 認証方式に依存しない統一的なインターフェース

### 3. インフラ層

#### `app/infra/adapters/auth/dev_auth_provider.py`
- **DevAuthProvider** - 開発用固定ユーザープロバイダ
- 認証チェックなしで常に同じユーザーを返す
- デフォルトユーザー: `dev-user@honest-recycle.co.jp`

#### `app/infra/adapters/auth/iap_auth_provider.py`
- **IapAuthProvider** - Google Cloud IAP 統合プロバイダ
- `X-Goog-Authenticated-User-Email` ヘッダーを読み取り
- `@honest-recycle.co.jp` ドメインのみを許可（ホワイトリスト方式）
- TODO コメント付き（IAP 有効化後の調整用）

### 4. ユースケース層

#### `app/core/usecases/auth/get_current_user.py`
- **GetCurrentUserUseCase** - ユーザー情報取得ユースケース
- IAuthProvider に委譲するシンプルな実装
- Clean Architecture に準拠

### 5. DI 設定

#### `app/config/di_providers.py` - 追加内容
- **get_auth_provider()**: 環境変数 `AUTH_MODE` に応じてプロバイダを切り替え
  - `AUTH_MODE=dev` → DevAuthProvider
  - `AUTH_MODE=iap` → IapAuthProvider
- **get_get_current_user_usecase()**: GetCurrentUserUseCase の DI 提供

### 6. API エンドポイント

#### `app/api/routers/auth.py`
- **GET /auth/me** - 現在ユーザー情報取得エンドポイント
- レスポンス:
  ```json
  {
    "email": "user@honest-recycle.co.jp",
    "display_name": "山田太郎"
  }
  ```
- ステータスコード:
  - 200: 成功
  - 401: 認証失敗（IAP ヘッダーなし等）
  - 403: アクセス拒否（許可されていないドメイン等）

#### `app/app.py`
- auth router を FastAPI アプリケーションに登録
- `/core_api/auth/me` として公開

### 7. 環境変数設定

#### `.env.example` - 追加内容
```dotenv
# Authentication Settings
# AUTH_MODE: Authentication provider mode
#   - "dev": Development mode (fixed dev user)
#   - "iap": Google Cloud IAP mode
AUTH_MODE=dev
```

---

## フロントエンド実装内容

### 1. Feature 構成（FSD）

#### `src/features/authStatus/`
```
authStatus/
├── domain/
│   └── authUser.ts          # AuthUser 型定義
├── ports/
│   └── AuthRepository.ts    # リポジトリインターフェース
├── infrastructure/
│   └── AuthHttpRepository.ts # HTTP 実装
├── model/
│   └── useAuthStatusViewModel.ts # ViewModel Hook
├── ui/
│   └── UserInfoChip.tsx     # UI コンポーネント
└── index.ts                 # エクスポート
```

### 2. ドメイン層

#### `domain/authUser.ts`
- **AuthUser** 型定義
- フィールド:
  - `email: string` - メールアドレス
  - `displayName?: string | null` - 表示名（オプション）

### 3. ポート層

#### `ports/AuthRepository.ts`
- **AuthRepository** インターフェース
- `fetchCurrentUser(): Promise<AuthUser>` メソッド

### 4. インフラ層

#### `infrastructure/AuthHttpRepository.ts`
- **AuthHttpRepository** - HTTP 実装
- `GET /core_api/auth/me` を呼び出し
- 既存の `coreApi` クライアントを使用

### 5. ViewModel 層

#### `model/useAuthStatusViewModel.ts`
- **useAuthStatusViewModel** カスタムフック
- 状態管理:
  - `user: AuthUser | null` - ユーザー情報
  - `isLoading: boolean` - ローディング状態
  - `error: string | null` - エラーメッセージ
- 初回マウント時に自動フェッチ
- アンマウント時のクリーンアップ対応

### 6. UI 層

#### `ui/UserInfoChip.tsx`
- **UserInfoChip** コンポーネント
- 表示内容:
  - ローディング中: "ユーザー情報取得中..."
  - エラー時: エラーメッセージ（赤色）
  - 未ログイン: "未ログイン"
  - ログイン中: "ログイン中：{表示名 or メールアドレス}"
- Tailwind CSS でスタイリング

### 7. レイアウト統合

#### `app/layout/Sidebar.tsx` - 変更内容
- `UserInfoChip` をインポート
- デスクトップ版: サイドバー上部（折りたたみ時は非表示）
- モバイル版（Drawer）: メニュー上部に表示

---

## アーキテクチャ設計

### バックエンド

**Clean Architecture / Hexagonal / DDD**
- **Domain**: `AuthUser` エンティティ（不変オブジェクト）
- **Ports**: `IAuthProvider` 抽象インターフェース
- **Infrastructure**: `DevAuthProvider`, `IapAuthProvider` 実装
- **UseCase**: `GetCurrentUserUseCase` ビジネスロジック
- **Presentation**: `auth.py` ルーター（HTTP エンドポイント）

### フロントエンド

**Feature-Sliced Design (FSD) + MVVM + Repository パターン**
- **Domain**: 型定義（`AuthUser`）
- **Ports**: リポジトリインターフェース
- **Infrastructure**: HTTP 実装
- **Model**: ViewModel（`useAuthStatusViewModel` Hook）
- **UI**: View（`UserInfoChip` コンポーネント）

---

## 動作フロー

### 1. 初期化フロー

```
ブラウザ起動
  ↓
MainLayout レンダリング
  ↓
Sidebar レンダリング
  ↓
UserInfoChip マウント
  ↓
useAuthStatusViewModel 実行
  ↓
AuthHttpRepository.fetchCurrentUser()
  ↓
GET /core_api/auth/me
  ↓
Backend: get_auth_provider() → DevAuthProvider (AUTH_MODE=dev)
  ↓
Backend: DevAuthProvider.get_current_user()
  ↓
Response: { email: "dev-user@honest-recycle.co.jp", display_name: "開発ユーザー" }
  ↓
UserInfoChip 表示: "ログイン中：開発ユーザー"
```

### 2. 環境切り替えフロー

**開発環境（デフォルト）**
```
AUTH_MODE=dev → DevAuthProvider → 固定ユーザー
```

**本番環境（IAP 有効化後）**
```
AUTH_MODE=iap → IapAuthProvider → X-Goog-Authenticated-User-Email ヘッダー読み取り
```

---

## 使用方法

### 開発環境で起動

```bash
# バックエンド
cd app/backend/core_api
# .env または環境変数で AUTH_MODE=dev を設定（デフォルト）
docker compose up

# フロントエンド
cd app/frontend
npm run dev
```

ブラウザでアクセスすると、サイドバーに「ログイン中：開発ユーザー」と表示されます。

### 本番環境への切り替え

1. Google Cloud で IAP を有効化
2. 環境変数を設定:
   ```bash
   export AUTH_MODE=iap
   ```
3. アプリケーションを再起動
4. IAP ヘッダー `X-Goog-Authenticated-User-Email` が付与されるようになる
5. ヘッダー内容をログで確認し、必要に応じて `IapAuthProvider` を微調整

### API 動作確認

```bash
# 開発環境（AUTH_MODE=dev）
curl http://localhost:8000/core_api/auth/me

# レスポンス
{
  "email": "dev-user@honest-recycle.co.jp",
  "display_name": "開発ユーザー"
}
```

---

## テスト項目

### バックエンド

- [ ] GET /auth/me が 200 OK で応答する
- [ ] レスポンスに email と display_name が含まれる
- [ ] AUTH_MODE=dev の場合、固定ユーザーが返される
- [ ] AUTH_MODE=iap の場合、ヘッダーがない場合に 401 が返される

### フロントエンド

- [ ] サイドバーに UserInfoChip が表示される
- [ ] 初回ロード時に「ユーザー情報取得中...」が表示される
- [ ] ユーザー情報取得後に「ログイン中：開発ユーザー」が表示される
- [ ] モバイル表示（Drawer）でも UserInfoChip が表示される
- [ ] サイドバー折りたたみ時は UserInfoChip が非表示になる

---

## 今後の拡張ポイント

### 1. IAP 本番統合

- IAP 有効化後にヘッダー内容を確認
- `IapAuthProvider` の TODO コメント箇所を微調整
- ログ出力を活用してヘッダー形式を検証

### 2. OAuth2 プロバイダ追加

将来的に自前の OAuth2 認証を追加する場合:
1. `app/infra/adapters/auth/oauth2_auth_provider.py` を作成
2. `get_auth_provider()` に `AUTH_MODE=oauth2` の分岐を追加
3. JWT トークン検証ロジックを実装

### 3. 権限管理（Authorization）

現在は「認証（誰か）」のみ実装。将来的に「認可（何ができるか）」を追加する場合:
1. `AuthUser` に `roles: list[str]` フィールドを追加
2. デコレータ `@require_role("admin")` を実装
3. フロントエンドで権限に応じた UI 表示制御

### 4. ユーザー情報キャッシュ

現在は毎回 API 呼び出し。パフォーマンス改善のため:
1. LocalStorage / SessionStorage にキャッシュ
2. トークンリフレッシュ機構
3. Context API でアプリ全体に共有

---

## 注意事項

### セキュリティ

- **開発用プロバイダは本番環境で使用しないこと**
  - `AUTH_MODE=dev` は開発・テスト専用
  - 本番環境では必ず `AUTH_MODE=iap` を設定
- **IAP ヘッダーの検証**
  - 本番環境では IAP が正しく設定されていることを確認
  - ヘッダー偽装対策として IAP の署名検証を検討
- **ドメインホワイトリスト**
  - `@honest-recycle.co.jp` ドメインのみを許可
  - 必要に応じて `IapAuthProvider.__init__()` で変更可能

### パフォーマンス

- フロントエンド: 初回マウント時のみ API 呼び出し
- バックエンド: 各リクエストごとに認証プロバイダが呼ばれる
  - 将来的にセッションキャッシュを検討

### ログ

- `DevAuthProvider`: INFO レベルで初期化ログ、DEBUG レベルでユーザー返却ログ
- `IapAuthProvider`: INFO レベルで認証成功ログ、WARNING レベルで認証失敗ログ
- 本番環境では個人情報ログに注意（メールアドレスの出力を制限）

---

## ファイル一覧

### バックエンド

```
app/backend/core_api/
├── app/
│   ├── core/
│   │   ├── domain/
│   │   │   └── auth/
│   │   │       ├── __init__.py
│   │   │       └── entities.py
│   │   ├── ports/
│   │   │   └── auth/
│   │   │       ├── __init__.py
│   │   │       └── auth_provider.py
│   │   └── usecases/
│   │       └── auth/
│   │           ├── __init__.py
│   │           └── get_current_user.py
│   ├── infra/
│   │   └── adapters/
│   │       └── auth/
│   │           ├── __init__.py
│   │           ├── dev_auth_provider.py
│   │           └── iap_auth_provider.py
│   ├── api/
│   │   └── routers/
│   │       └── auth.py
│   ├── config/
│   │   └── di_providers.py (変更)
│   └── app.py (変更)
└── .env.example (変更)
```

### フロントエンド

```
app/frontend/src/
├── features/
│   └── authStatus/
│       ├── domain/
│       │   └── authUser.ts
│       ├── ports/
│       │   └── AuthRepository.ts
│       ├── infrastructure/
│       │   └── AuthHttpRepository.ts
│       ├── model/
│       │   └── useAuthStatusViewModel.ts
│       ├── ui/
│       │   └── UserInfoChip.tsx
│       └── index.ts
└── app/
    └── layout/
        └── Sidebar.tsx (変更)
```

---

## まとめ

✅ **実装完了**
- バックエンド: 認証基盤（Domain / Ports / Infrastructure / UseCase / Router）
- フロントエンド: authStatus feature（Domain / Ports / Infrastructure / Model / UI）
- 環境変数: AUTH_MODE による認証方式切り替え
- UI 統合: Sidebar へのユーザー情報表示

✅ **設計品質**
- Clean Architecture / Hexagonal Architecture に準拠
- Feature-Sliced Design (FSD) に準拠
- MVVM + Repository パターン
- 認証方式の抽象化による拡張性の確保

✅ **次のステップ**
- 開発環境で動作確認
- 本番環境で IAP 統合
- 権限管理（Authorization）の追加（将来）

---

**実装者**: GitHub Copilot  
**レビュー**: 必要に応じてコードレビューを実施してください
