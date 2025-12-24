# myuser廃止／env統一／権限分離の仕込み - 実装完了レポート

## 実装日
2025-12-24

## ブランチ
`feature/remove-myuser-unify-env`

## コミット
`f9b2c1ee` - feat: Remove myuser hardcoding and unify DB env configuration

---

## 1. 変更したファイル一覧

### 新規作成
1. **`app/backend/backend_shared/src/backend_shared/infra/db/connection_mode.py`**
   - DB接続モード管理（app / migrator）
   - 環境変数の優先順位とフォールバック処理
   - 必須パラメータの検証

2. **`docs/database/roles.md`**
   - データベースユーザー・ロール設計ガイド
   - 推奨ロール設計
   - 権限設定SQL雛形
   - 環境変数設定例
   - 運用ルールとトラブルシューティング

### 更新
3. **`app/backend/backend_shared/src/backend_shared/infra/db/__init__.py`**
   - `connection_mode` モジュールのエクスポート追加

4. **`app/backend/backend_shared/src/backend_shared/infra/db/url_builder.py`**
   - `build_database_url()` に `mode` パラメータ追加
   - DB_USER / DB_PASSWORD を優先、POSTGRES_* は後方互換性として維持
   - DB_MIGRATOR_USER / DB_MIGRATOR_PASSWORD のサポート
   - エラーメッセージの改善

5. **`app/backend/core_api/.env.example`**
   - DB接続設定を大幅に更新
   - DB_USER / DB_PASSWORD / DB_NAME の推奨設定
   - DB_MIGRATOR_USER / DB_MIGRATOR_PASSWORD のオプション設定
   - 詳細なコメント追加

6. **`app/backend/core_api/app/deps.py`**
   - `get_db_session_app()` 追加（アプリ実行用）
   - `get_db_session_migrator()` 追加（マイグレーション用）
   - 将来の分離に対応したインターフェース

7. **`app/backend/core_api/migrations_v2/alembic/env.py`**
   - ALEMBIC_DB_USER を非推奨化（警告付き）
   - DB_MIGRATOR_USER を推奨
   - エラーメッセージの改善

8. **`app/backend/core_api/migrations_legacy/alembic/env.py`**
   - migrations_v2 と同様の変更

9. **`docker/docker-compose.dev.yml`**
   - `ALEMBIC_DB_USER=myuser` を削除
   - コメントを更新

10. **`makefile`**
    - `al-init-from-schema` の myuser 直接使用を環境変数参照に変更

---

## 2. 主要な実装内容

### 2.1 接続設定の単一化

#### 新規モジュール: `connection_mode.py`
```python
def get_db_connection_params(mode: Literal["app", "migrator"] = "app") -> dict[str, str]
```

**機能**:
- mode に応じた接続パラメータを取得
- app: DB_USER / DB_PASSWORD を優先
- migrator: DB_MIGRATOR_USER / DB_MIGRATOR_PASSWORD を優先、未設定時は app にフォールバック
- 必須パラメータ不足時の明確なエラーメッセージ

**環境変数の優先順位**:
1. `DB_USER` / `DB_PASSWORD` / `DB_NAME` (推奨)
2. `DB_MIGRATOR_USER` / `DB_MIGRATOR_PASSWORD` (マイグレーション時)
3. `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` (後方互換性)

### 2.2 app_user / migrator 分離の仕込み

#### DI プロバイダー (`deps.py`)
```python
def get_db_session_app() -> Generator[Session, None, None]:
    """アプリケーション実行用のDBセッション"""
    
def get_db_session_migrator() -> Generator[Session, None, None]:
    """マイグレーション用のDBセッション（DDL操作用）"""
```

**特徴**:
- 現在は両方とも `get_db()` と同じ接続
- 将来的には異なるユーザーで接続可能
- インターフェースは確立済み（呼び出し側の変更不要）

### 2.3 Alembic の更新

**変更点**:
- `ALEMBIC_DB_USER` を非推奨化（DeprecationWarning）
- `DB_MIGRATOR_USER` を推奨
- 未設定時は `DB_USER` にフォールバック
- エラーメッセージに設定方法を含める

**後方互換性**:
- `ALEMBIC_DB_USER` は一時的に動作（警告付き）
- 段階的な移行が可能

---

## 3. 動作確認手順

### 3.1 環境変数の設定

#### ローカル開発環境 (local_dev)

**`env/.env.local_dev`** に以下を追加:
```env
# 推奨設定（新規）
DB_USER=sanbou_app_dev
DB_NAME=sanbou_dev
DB_HOST=db
DB_PORT=5432

# マイグレーション用（オプション、未設定時は DB_USER にフォールバック）
# DB_MIGRATOR_USER=sanbou_migrator_dev

# 後方互換性（非推奨、DB_USER が優先される）
POSTGRES_USER=sanbou_app_dev
POSTGRES_DB=sanbou_dev
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

**`secrets/.env.local_dev.secrets`** に以下を追加:
```env
DB_PASSWORD=<YOUR_PASSWORD>
# DB_MIGRATOR_PASSWORD=<YOUR_PASSWORD>

# 後方互換性
POSTGRES_PASSWORD=<YOUR_PASSWORD>
```

### 3.2 起動確認

```bash
# 1. 環境停止
make down ENV=local_dev

# 2. 環境起動
make up ENV=local_dev

# 3. ログ確認（エラーがないか）
make logs ENV=local_dev S=core_api

# 4. ヘルスチェック
curl http://localhost:8002/health
```

### 3.3 Alembic 動作確認

```bash
# 1. 現在のリビジョン確認
make al-cur-env ENV=local_dev

# 2. マイグレーション実行（テスト）
# make al-up-env ENV=local_dev

# 3. エラーがないか確認
```

### 3.4 エラーメッセージの確認

```bash
# 環境変数を一時的に削除してエラーメッセージを確認
unset DB_USER
unset DB_PASSWORD
unset POSTGRES_USER
unset POSTGRES_PASSWORD

# core_api を起動（エラーになるはず）
docker compose -f docker/docker-compose.dev.yml -p local_dev up core_api

# 期待されるエラーメッセージ:
# ValueError: Required environment variables are missing: DB_USER, DB_PASSWORD, ...
```

---

## 4. 検索結果サマリー（問題箇所の特定）

### 4.1 myuser の使用箇所（200+ 箇所）

**主な問題箇所**:
- ✅ Docker Compose: `ALEMBIC_DB_USER=myuser` → 削除済み
- ✅ makefile: `psql -U myuser` → `psql -U "$$POSTGRES_USER"` に変更
- ✅ Alembic env.py: ハードコード削除、環境変数参照に変更
- ⚠️ ドキュメント: 説明用の例として残存（問題なし）
- ⚠️ テストコード: モックデータとして使用（問題なし）
- ⚠️ 既存DBのマイグレーションファイル: 履歴として残存（問題なし）

**残存箇所の分類**:
1. **ドキュメント内の説明**: 問題なし（将来削除を推奨）
2. **テストコード**: 問題なし（モックデータ）
3. **マイグレーション履歴**: 問題なし（過去の記録）
4. **アーカイブファイル**: 問題なし（削除推奨）

### 4.2 DATABASE_URL の使用箇所（86 箇所）

**主な箇所**:
- ✅ `url_builder.py`: 環境変数からの構築ロジック実装済み
- ✅ `env.py` (Alembic): url_builder を使用
- ✅ `settings.py`: url_builder を使用
- ✅ `.env.example`: 推奨設定を追加
- ⚠️ ドキュメント: 説明用（問題なし）

### 4.3 POSTGRES_USER の使用箇所（100+ 箇所）

**主な箇所**:
- ✅ `url_builder.py`: DB_USER を優先、POSTGRES_* は後方互換性として維持
- ✅ `connection_mode.py`: フォールバック処理実装
- ✅ Docker Compose: 環境変数として維持（PostgreSQL初期化用）
- ⚠️ makefile: DBコンテナ操作で使用（問題なし）

---

## 5. 受け入れ条件の達成状況

### ✅ 完了した項目

1. ✅ **リポジトリ内に myuser という文字列が DB接続に関して残っていない**
   - コード内のハードコードは完全に削除
   - ドキュメント、テスト、履歴は残存（問題なし）

2. ✅ **バックエンド起動時、DB接続ユーザーは .env の DB_USER が使われる**
   - `url_builder.py` で実装済み
   - DB_USER → POSTGRES_USER の優先順位

3. ✅ **.env 不足時は起動に失敗し、どのenvが足りないか出力される**
   - `connection_mode.py` で実装済み
   - 明確なエラーメッセージ

4. ✅ **DIに app と migrator の接続経路が用意されている**
   - `deps.py` に実装済み
   - `get_db_session_app()` / `get_db_session_migrator()`

5. ✅ **docs が追加されている**
   - `docs/database/roles.md` を作成済み

### 🔄 次のステップ（このPRには含まれない）

1. **実際のDBユーザー作成**
   - `roles.md` のSQL雛形を使用
   - 環境ごとに実行

2. **.env ファイルへの DB_USER / DB_PASSWORD 設定**
   - 各環境の .env ファイルを更新

3. **本番環境での段階的移行**
   - dev → stg → prod の順で適用
   - 十分なテスト期間を設ける

4. **POSTGRES_* 環境変数の段階的廃止**
   - 警告ログの追加
   - 移行期間後に削除

---

## 6. 設計の特徴

### 6.1 後方互換性の維持

- `POSTGRES_*` 環境変数は引き続き動作
- `ALEMBIC_DB_USER` は警告付きで動作
- 既存のコードは変更不要

### 6.2 段階的な移行が可能

1. **Phase 1**: 新しい環境変数を追加（このPR）
2. **Phase 2**: 各環境で DB_USER / DB_PASSWORD を設定
3. **Phase 3**: 実際のDBユーザーを作成
4. **Phase 4**: 動作確認後、POSTGRES_* を削除

### 6.3 将来の拡張性

- `mode` パラメータにより app / migrator を分離可能
- DIインターフェースは確立済み
- 接続ロジックは `connection_mode.py` に集約

---

## 7. トラブルシューティング

### Q1: "Required environment variables are missing" エラー

**原因**: DB_USER / POSTGRES_USER が設定されていない

**解決策**:
```bash
# .env ファイルに追加
echo "DB_USER=sanbou_app_dev" >> env/.env.local_dev
echo "DB_PASSWORD=<PASSWORD>" >> secrets/.env.local_dev.secrets
```

### Q2: "ALEMBIC_DB_USER is deprecated" 警告

**原因**: 古い環境変数を使用している

**解決策**:
```bash
# Docker Compose の環境変数を削除
# docker-compose.dev.yml から ALEMBIC_DB_USER を削除（既に対応済み）
```

### Q3: マイグレーションが失敗する

**原因**: DB_MIGRATOR_USER が設定されていない、または権限不足

**解決策**:
```bash
# 現在は DB_USER にフォールバックするため、特に設定不要
# 将来的に分離する場合のみ設定
echo "DB_MIGRATOR_USER=sanbou_migrator_dev" >> env/.env.local_dev
echo "DB_MIGRATOR_PASSWORD=<PASSWORD>" >> secrets/.env.local_dev.secrets
```

---

## 8. 関連ドキュメント

- [docs/database/roles.md](../database/roles.md): データベースユーザー・ロール設計ガイド
- [docs/conventions/db/20251216_001_alembic_migration_rules.md](../conventions/db/20251216_001_alembic_migration_rules.md): Alembic マイグレーションルール

---

## 9. まとめ

### 達成したこと

1. ✅ DB接続ユーザーのハードコード（myuser等）を完全に排除
2. ✅ 環境変数からのみ接続情報を取得する設計に統一
3. ✅ app_user / migrator 分離の仕込み完了
4. ✅ 後方互換性を維持しながら段階的移行が可能
5. ✅ 明確なエラーメッセージによる安全な失敗
6. ✅ 包括的なドキュメント作成

### 次のアクション

1. **レビュー**: このPRをレビューしてもらう
2. **マージ**: main ブランチにマージ
3. **DBユーザー作成**: `roles.md` のSQL雛形を使用して各環境でユーザー作成
4. **.env 設定**: 各環境の .env ファイルを更新
5. **動作確認**: 各環境で起動確認とマイグレーション確認

---

**作成日**: 2025-12-24  
**作成者**: GitHub Copilot  
**ブランチ**: feature/remove-myuser-unify-env  
**コミット**: f9b2c1ee
