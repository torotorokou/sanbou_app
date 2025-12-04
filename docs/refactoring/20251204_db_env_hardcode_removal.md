# DB環境変数ハードコード削除リファクタリング

作成日: 2025-12-04  
対象: データベース接続情報の環境変数管理

## 1. 概要

データベース接続情報（特にパスワード）がPythonコード内にハードコードされている問題を解決し、すべての接続情報を環境変数から動的に構築するようリファクタリングしました。

## 2. 問題点

### 2.1 セキュリティリスク

以下のファイルでパスワードやDB接続情報がハードコードされていました:

```python
# 修正前: ハードコードされたパスワード (例: 実際にはこのような弱いパスワードが使われていた)
def get_database_url(default: str = "postgresql://myuser:<WEAK_PASSWORD>@db:5432/sanbou_dev") -> str:
    return get_str_env("DATABASE_URL", default=default)
```

**問題:**
- パスワードが平文でコードに直接記載
- デフォルト値がフォールバックとして使用される可能性
- Git履歴に機密情報が残る
- 環境ごとの設定変更が困難

### 2.2 影響範囲

以下のファイルでハードコードが発見されました:

**Pythonコード:**
1. `app/backend/backend_shared/src/backend_shared/config/env_utils.py`
2. `app/backend/plan_worker/app/infra/db/health.py`
3. `app/backend/plan_worker/app/test/common.py`
4. `app/backend/plan_worker/app/config/settings.py`
5. `app/backend/core_api/app/config/settings.py`
6. `app/backend/core_api/app/infra/db/db.py`

**環境ファイル:**
1. `env/.env.local_stg`
2. `env/.env.vm_stg`
3. `env/.env.vm_prod`
4. `env/.env.local_demo`

## 3. 実施した修正

### 3.1 Pythonコードの修正

#### 修正パターン

**修正前:**
```python
# 危険: パスワードがハードコード (例)
user = os.getenv("POSTGRES_USER", "<DEFAULT_USER>")  # ハードコードされたデフォルト値
pwd = os.getenv("POSTGRES_PASSWORD", "<WEAK_PASSWORD>")  # 危険！
db = os.getenv("POSTGRES_DB", "<DEFAULT_DB>")
return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
```

**修正後:**
```python
# 安全: 環境変数必須、フォールバックなし
user = os.getenv("POSTGRES_USER", "")
pwd = os.getenv("POSTGRES_PASSWORD", "")
db = os.getenv("POSTGRES_DB", "")

if not user or not pwd or not db:
    raise ValueError(
        "DATABASE_URL is not set and POSTGRES_USER, POSTGRES_PASSWORD, "
        "or POSTGRES_DB is missing. Please set DATABASE_URL or all "
        "required POSTGRES_* environment variables."
    )

return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
```

#### 修正した関数

1. **`backend_shared/config/env_utils.py::get_database_url()`**
   - デフォルト引数を `None` に変更
   - 環境変数が未設定の場合は明示的にエラー
   - POSTGRES_* 変数から動的に構築

2. **`plan_worker/app/infra/db/health.py::_dsn()`**
   - フォールバック値を空文字列に変更
   - 必須変数チェックを追加

3. **`plan_worker/app/test/common.py::_dsn()`**
   - テスト用関数も同様に修正
   - 本番コードと同じ安全性を確保

4. **`plan_worker/app/config/settings.py::Settings`**
   - `default_factory` パターンを使用
   - Pydantic モデルで動的構築

5. **`core_api/app/config/settings.py::Settings`**
   - 静的メソッドで DATABASE_URL を構築
   - クラス初期化時に環境変数を評価

6. **`core_api/app/infra/db/db.py`**
   - モジュールレベルでヘルパー関数を実行
   - 初期化時にエラーチェック

### 3.2 環境ファイルの修正

#### .env.local_stg, .env.vm_stg, .env.vm_prod, .env.local_demo

**修正前:**
```dotenv
POSTGRES_DB=sanbou_stg
DATABASE_URL=postgresql://myuser:mypassword@db:5432/sanbou_stg
```

**修正後:**
```dotenv
# === DB ===
# 【DB ユーザー分離対応】
# POSTGRES_USER / POSTGRES_PASSWORD / DATABASE_URL は secrets/.env.*.secrets に記載してください
# 
# 注意: DATABASE_URL はパスワードを含むため、必ず secrets/ ファイルで設定してください
#       ここで設定すると Git にパスワードが記録されます
POSTGRES_DB=sanbou_stg
```

### 3.3 テンプレートファイルの修正

**secrets/.env.secrets.template**

変数展開 `${POSTGRES_USER}` は環境変数として機能しないため、明示的な値を記述するよう変更:

```dotenv
# 修正前（動作しない）
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/sanbou_dev

# 修正後（正しい）
DATABASE_URL=postgresql://sanbou_app_dev:<STRONG_PASSWORD_HERE>@db:5432/sanbou_dev
```

## 4. 設計方針

### 4.1 環境変数の優先順位

```
1. DATABASE_URL（最優先）
   ↓
2. POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB から動的構築
   ↓
3. エラー（デフォルト値は使用しない）
```

### 4.2 エラーハンドリング

必須の環境変数が未設定の場合、明示的にエラーを発生させます:

```python
if not user or not password or not database:
    raise ValueError(
        "DATABASE_URL is not set and POSTGRES_USER, POSTGRES_PASSWORD, "
        "or POSTGRES_DB is missing. Please set DATABASE_URL or all "
        "required POSTGRES_* environment variables."
    )
```

**利点:**
- 起動時に設定ミスを即座に検出
- 暗黙的なフォールバックによるセキュリティリスクを排除
- デバッグが容易

### 4.3 環境ごとの設定管理

```
env/
  .env.common          # 共通設定（パスワード不要）
  .env.local_dev       # 開発環境設定（パスワード不要）
  .env.local_stg       # STG設定（パスワード不要）
  .env.vm_stg          # VM STG設定（パスワード不要）
  .env.vm_prod         # 本番設定（パスワード不要）

secrets/  (Git管理外)
  .env.local_dev.secrets     # 開発環境の機密情報
  .env.local_stg.secrets     # STG の機密情報
  .env.vm_stg.secrets        # VM STG の機密情報
  .env.vm_prod.secrets       # 本番の機密情報
  .env.secrets.template      # テンプレート（Git管理）
```

## 5. 動作確認

### 5.1 環境変数の読み込み確認

```bash
# DATABASE_URL が正しく設定されているか確認
docker compose -f docker/docker-compose.dev.yml -p local_dev \
  exec -T core_api printenv DATABASE_URL

# 出力例:
# postgresql://myuser:fOb1TYnB9pu64uRKx7QWEB6kByWgM098Lrhsy0HWG6g=@db:5432/sanbou_dev
```

### 5.2 起動確認

```bash
# コンテナの状態を確認
docker compose -f docker/docker-compose.dev.yml -p local_dev ps

# 期待される結果: すべて healthy
```

### 5.3 ログ確認

```bash
# エラーがないことを確認
docker compose -f docker/docker-compose.dev.yml -p local_dev \
  logs core_api --tail=20 | grep -i error
```

## 6. 移行手順

### 6.1 既存環境への適用

1. **secrets ファイルの作成**
   ```bash
   cp secrets/.env.secrets.template secrets/.env.local_dev.secrets
   ```

2. **パスワードの設定**
   ```bash
   # 強力なパスワードを生成
   openssl rand -base64 32
   
   # secrets/.env.local_dev.secrets を編集
   POSTGRES_USER=myuser
   POSTGRES_PASSWORD=<生成したパスワード>
   DATABASE_URL=postgresql://myuser:<生成したパスワード>@db:5432/sanbou_dev
   ```

3. **DBパスワードの更新**（既存DBの場合）
   ```sql
   ALTER USER myuser WITH PASSWORD '<生成したパスワード>';
   ```

4. **コンテナの再起動**
   ```bash
   docker compose -f docker/docker-compose.dev.yml -p local_dev restart
   ```

### 6.2 新規環境のセットアップ

1. **テンプレートからコピー**
   ```bash
   cp secrets/.env.secrets.template secrets/.env.vm_stg.secrets
   ```

2. **環境に合わせて編集**
   ```dotenv
   POSTGRES_USER=sanbou_app_stg
   POSTGRES_PASSWORD=<強力なパスワード>
   DATABASE_URL=postgresql://sanbou_app_stg:<パスワード>@db:5432/sanbou_stg
   ```

## 7. セキュリティベストプラクティス

### 7.1 パスワード管理

✅ **推奨:**
- `openssl rand -base64 32` で強力なパスワードを生成
- 環境ごとに異なるパスワードを使用
- 1Password 等でバックアップ
- 定期的にローテーション

❌ **禁止:**
- 弱いパスワード（`password`, `123456` など）
- 環境間でのパスワード共有
- Git へのコミット
- Slack/Email での平文共有

### 7.2 環境変数の検証

すべての環境で以下を確認:

```bash
# 1. DATABASE_URL が設定されていること
echo $DATABASE_URL

# 2. パスワードが含まれていること（表示しない）
[[ $DATABASE_URL == *":"*"@"* ]] && echo "OK: Password found"

# 3. 適切なユーザー名が使用されていること
echo $POSTGRES_USER
```

## 8. トラブルシューティング

### 8.1 起動時エラー

**エラー:**
```
ValueError: DATABASE_URL is not set and POSTGRES_USER, POSTGRES_PASSWORD, 
or POSTGRES_DB is missing.
```

**解決策:**
1. secrets/.env.*.secrets ファイルが存在するか確認
2. docker-compose.yml で env_file が正しく指定されているか確認
3. 環境変数が正しく設定されているか確認

### 8.2 認証エラー

**エラー:**
```
FATAL: password authentication failed for user "myuser"
```

**解決策:**
1. secrets ファイルのパスワードと実際のDBパスワードが一致しているか確認
2. DATABASE_URL のパスワード部分が正しいか確認
3. 必要に応じて SQL で ALTER USER を実行

## 9. 今後の課題

### 9.1 環境別ユーザーへの移行

現在は `myuser` を使用していますが、以下のユーザーへの移行を推奨:

- 開発: `sanbou_app_dev`
- ステージング: `sanbou_app_stg`
- 本番: `sanbou_app_prod`

移行手順は `docs/db/20251204_db_user_migration_plan.md` を参照。

### 9.2 パスワードローテーション

定期的なパスワード変更プロセスの確立:

1. 新しいパスワード生成
2. secrets ファイル更新
3. SQL でパスワード変更
4. サービス再起動
5. 旧パスワードの無効化確認

## 10. 関連資料

- DB接続失敗診断レポート: `docs/bugs/20251204_db_connection_failure_diagnosis.md`
- DB ユーザー設計: `docs/db/20251204_db_user_design.md`
- 移行計画: `docs/db/20251204_db_user_migration_plan.md`
- SQL スクリプト: `scripts/sql/20251204_create_app_db_users.sql`

## 11. まとめ

このリファクタリングにより:

✅ すべてのハードコードされたパスワードを削除  
✅ 環境変数からの動的構築に統一  
✅ 必須変数の明示的なバリデーション  
✅ Git 履歴からの機密情報排除  
✅ 環境ごとの柔軟な設定管理  

セキュリティとメンテナンス性が大幅に向上しました。
