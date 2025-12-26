# Environment Variable Consolidation - 環境変数の統合整理

**実施日**: 2025年12月3日  
**関連ブランチ**: `security/iap-authentication`  
**関連イシュー**: Security Audit - IAP Authentication Implementation

## 概要

環境変数ファイル（`.env.*`）とバックエンドコードの環境変数読み込みを整理し、DRY原則に基づいて共通化を実施しました。

## 実施内容

### 1. backend_shared に環境変数ユーティリティを作成

**ファイル**: `app/backend/backend_shared/src/backend_shared/config/env_utils.py`

**提供する機能**:

- `get_bool_env()`: 真偽値の統一的な解釈 (true/false/1/0/yes/no)
- `get_int_env()`: 整数値の取得
- `get_str_env()`: 文字列の取得
- `is_debug_mode()`: DEBUG モードの判定
- `is_iap_enabled()`: IAP 有効化の判定
- `get_iap_audience()`: IAP audience 値の取得
- `get_stage()`: 環境ステージの取得 (dev/stg/prod)
- `is_production()`, `is_development()`: 環境判定
- `get_api_base_url()`: 内部API URLの取得
- `get_database_url()`: DB接続URLの取得
- `get_log_level()`: ログレベルの取得

**メリット**:

- 環境変数読み込みロジックの重複排除
- 型安全性の向上
- 全サービスで一貫した解釈
- テストが容易

### 2. 全バックエンドサービスで共通ユーティリティを使用

**変更したファイル**:

- `app/backend/core_api/app/app.py`
- `app/backend/ai_api/app/main.py`
- `app/backend/ledger_api/app/main.py`
- `app/backend/manual_api/app/main.py`
- `app/backend/rag_api/app/main.py`
- `app/backend/core_api/app/api/middleware/auth_middleware.py`
- `app/backend/core_api/app/infra/adapters/auth/iap_auth_provider.py`

**変更内容**:

```python
# Before
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
IAP_ENABLED = os.getenv("IAP_ENABLED", "false").lower() == "true"
IAP_AUDIENCE = os.getenv("IAP_AUDIENCE")

# After
from backend_shared.config.env_utils import is_debug_mode, is_iap_enabled, get_iap_audience

DEBUG = is_debug_mode()
IAP_ENABLED = is_iap_enabled()
IAP_AUDIENCE = get_iap_audience()
```

### 3. `.env.*` ファイルの整理

**注意**: envファイルは`.gitignore`で管理されているため、手動で更新してください。

#### 3.1 `.env.common` への共通変数の移動

以下の変数を `.env.common` に追加:

```bash
# === Core API: Internal API URLs (共通) ===
# 全環境で Docker Compose 内部ネットワーク名を使用
RAG_API_BASE=http://rag_api:8000
LEDGER_API_BASE=http://ledger_api:8000
MANUAL_API_BASE=http://manual_api:8000
AI_API_BASE=http://ai_api:8000

# === Forecast Worker Settings (共通デフォルト) ===
# ポーリング間隔 (秒)。環境別に上書き可能。
POLL_INTERVAL=5
```

#### 3.2 環境別ファイルから共通変数を削除

以下のファイルから `RAG_API_BASE`, `LEDGER_API_BASE`, `MANUAL_API_BASE`, `AI_API_BASE` を削除:

- `.env.local_dev`
- `.env.local_demo`
- `.env.local_stg`
- `.env.vm_stg`
- `.env.vm_prod`

#### 3.3 欠落していた変数の追加

**`.env.vm_prod`**:

```bash
NODE_ENV=production
PUBLIC_BASE_URL=https://sanbou-app.jp
```

**`.env.vm_stg`**:

```bash
POSTGRES_DB=sanbou_stg  # 明示的に追加
```

**`.env.local_demo`**:

```bash
# === Security / Authentication ===
# デモ環境では IAP 無効、DEBUG モード有効
DEBUG=true
IAP_ENABLED=false
# IAP_AUDIENCE: IAP無効時は設定不要
```

**`.env.local_stg`**:

```bash
# === Security / Authentication ===
# ローカルSTG疑似環境では IAP 無効、DEBUG 無効（本番に近い設定）
DEBUG=false
IAP_ENABLED=false
# IAP_AUDIENCE: IAP無効時は設定不要
```

#### 3.4 環境別 `POLL_INTERVAL` の設定

| 環境       | POLL_INTERVAL | 理由                             |
| ---------- | ------------- | -------------------------------- |
| local_dev  | 3秒           | 開発時の迅速なフィードバック     |
| local_demo | 3秒           | デモ時の迅速なフィードバック     |
| local_stg  | 3秒           | ローカルテスト用                 |
| vm_stg     | 5秒           | `.env.common` のデフォルトを使用 |
| vm_prod    | 10秒          | 本番環境での負荷軽減             |

#### 3.5 コメントの整理

各環境ファイルに以下のコメントを追加:

```bash
# === メモ ===
# ・内部API URL (RAG_API_BASE等) は .env.common から継承
# ・POLL_INTERVAL は .env.common のデフォルト(5秒)を使用
```

## 適用手順

### 1. コードの更新（既に完了）

```bash
git checkout security/iap-authentication
git pull origin security/iap-authentication
```

### 2. 環境変数ファイルの手動更新

各環境の `.env.*` ファイルを上記の変更内容に従って手動で更新してください。

**重要**: 以下の順序で変更してください:

1. `.env.common` に共通変数を追加
2. 各環境ファイル（`.env.local_dev`, `.env.vm_stg` など）から共通変数を削除
3. 欠落していた変数を各環境ファイルに追加
4. コメントを整理

### 3. 動作確認

```bash
# 開発環境で動作確認
docker compose -f docker/docker-compose.dev.yml -p local_dev up -d

# ログで環境変数が正しく読み込まれているか確認
docker compose -f docker/docker-compose.dev.yml -p local_dev logs core_api | grep "initialized"
docker compose -f docker/docker-compose.dev.yml -p local_dev logs ai_api | grep "initialized"
```

期待されるログ出力:

```json
{"timestamp":"2025-12-03T...", "level":"INFO", "message":"Core API initialized (DEBUG=True, docs_enabled=True)", ...}
{"timestamp":"2025-12-03T...", "level":"INFO", "message":"AI API initialized (DEBUG=True, docs_enabled=True)", ...}
{"timestamp":"2025-12-03T...", "level":"INFO", "message":"AuthenticationMiddleware initialized (IAP_ENABLED=False)", ...}
```

## 影響範囲

### 変更あり

- **全バックエンドサービス**: 環境変数読み込みロジックが共通ユーティリティに変更
- **認証ミドルウェア**: `is_iap_enabled()` を使用
- **IapAuthProvider**: `get_iap_audience()`, `get_stage()` を使用

### 変更なし（後方互換性あり）

- 環境変数名は変更なし
- 環境変数の解釈ロジックも同一
- 既存の `.env.*` ファイルはそのまま動作

## メリット

### 1. DRY原則の徹底

- 共通変数は `.env.common` に一元管理
- 環境変数読み込みロジックは `env_utils.py` に集約

### 2. 保守性の向上

- 共通値の変更は1箇所のみで対応可能
- 環境変数の追加・変更が容易

### 3. 一貫性の保証

- 全サービスで同一のロジックを使用
- 真偽値の解釈（true/false/1/0）が統一

### 4. 型安全性

- 明確な型注釈
- IDEの補完サポート

### 5. テスト容易性

- モック化が簡単
- 環境依存のテストが書きやすい

## トラブルシューティング

### 問題: サービスが起動しない

**確認事項**:

1. `.env.common` が正しく読み込まれているか
2. Docker Compose の `env_file` 設定順序が正しいか（`common` → `stage`）
3. 必須の環境変数が設定されているか

**解決方法**:

```bash
# 環境変数を確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api env | grep -E "DEBUG|IAP|API_BASE"

# コンテナを再起動
docker compose -f docker/docker-compose.dev.yml -p local_dev restart
```

### 問題: 環境変数が反映されない

**原因**: Docker のキャッシュ

**解決方法**:

```bash
# コンテナを完全に削除して再ビルド
docker compose -f docker/docker-compose.dev.yml -p local_dev down
docker compose -f docker/docker-compose.dev.yml -p local_dev up -d --build
```

### 問題: IAP認証が動作しない

**確認事項**:

1. `.env.*` ファイルに `IAP_ENABLED` と `IAP_AUDIENCE` が設定されているか
2. 本番環境では `DEBUG=false`, `IAP_ENABLED=true` になっているか

**ログ確認**:

```bash
docker compose logs core_api | grep -i "iap"
```

期待されるログ:

```json
{"level":"INFO", "message":"AuthenticationMiddleware initialized (IAP_ENABLED=True)", ...}
{"level":"INFO", "message":"IapAuthProvider initialized", "has_audience": true, ...}
```

## 関連ドキュメント

- [20251203_IAP_AUTHENTICATION_IMPLEMENTATION.md](./20251203_IAP_AUTHENTICATION_IMPLEMENTATION.md) - IAP認証実装ガイド
- [20251203_SECURITY_AUDIT_REPORT.md](./20251203_SECURITY_AUDIT_REPORT.md) - セキュリティ監査レポート
- [backend_shared/config/env_utils.py](../app/backend/backend_shared/src/backend_shared/config/env_utils.py) - 環境変数ユーティリティのソースコード

## 次のステップ

1. ✅ バックエンドコードの共通化完了
2. ✅ ドキュメント作成完了
3. ⏳ 各環境の `.env.*` ファイルを手動更新
4. ⏳ 動作確認（dev → stg → prod の順）
5. ⏳ mainブランチへのマージ

## 変更履歴

| 日付       | 変更内容                            |
| ---------- | ----------------------------------- |
| 2025-12-03 | 初版作成 - 環境変数の統合整理を実施 |
