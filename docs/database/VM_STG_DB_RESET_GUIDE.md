# VM STG DB完全初期化 & Alembic適用手順

## 概要

vm_stg のDBを完全に初期化し、Alembicマイグレーションを最初からheadまで適用する手順です。

## 実装内容

### 1. 誤爆防止ガード

- `db-reset-volume-env` と `db-reset-db-env` はvm_prodへの実行を厳しく制限
- vm_prodで実行する場合は `FORCE=1` が必要（極めて稀なケース）
- 許可される環境: `vm_stg`, `local_dev`, `local_demo`
- 実行前に5秒間の待機時間を設けて誤操作を防止

### 2. DB完全クリア方法（2種類）

#### 方法A: Volume削除による完全初期化（推奨）

```bash
make db-reset-volume-env ENV=vm_stg
```

- Dockerボリュームごと削除
- 最もクリーンな初期化
- 実装: `docker compose down -v --remove-orphans`

#### 方法B: DROP/CREATE による初期化

```bash
make db-reset-db-env ENV=vm_stg
```

- DBを削除して再作成
- ボリュームは残る
- 既存接続を強制切断してからDROP/CREATE実行

### 3. Schema Dump機能

```bash
make db-dump-schema-env ENV=local_dev OUT=backups/schema_local.sql
make db-dump-schema-env ENV=vm_stg OUT=backups/schema_stg.sql
diff -u backups/schema_local.sql backups/schema_stg.sql | head
```

- schema-only の pg_dump
- local_dev と vm_stg の差分確認に使用

### 4. Bootstrap Roles（既存）

既存の `scripts/db/bootstrap_roles.sql` は冪等性が確保されています：

- `app_readonly` ロールの作成
- スキーマへのUSAGE権限付与（mart, stg）
- テーブルへのSELECT権限付与
- 将来作成されるテーブルへのデフォルト権限設定

### 5. Migration修正

`20251211_140000000_recreate_v_receive_weekly_monthly.py` は既に正しく実装されています：

- `_check_mv_exists()` は `op.get_bind()` で同一コネクション使用
- `to_regclass()` で存在確認
- 問題ない実装

## 運用手順

### vm_stg での完全作り直し（推奨フロー）

```bash
# Step 1: DBを完全クリア（volume削除）
make db-reset-volume-env ENV=vm_stg

# Step 2: コンテナ起動（DBも含む）
make up ENV=vm_stg

# Step 3: Role/権限のブートストラップ
make db-bootstrap-roles-env ENV=vm_stg

# Step 4: Alembicマイグレーション実行
make al-up-env ENV=vm_stg

# Step 5: 現在のリビジョン確認
make al-cur-env ENV=vm_stg

# Step 6: スキーマダンプと比較
make db-dump-schema-env ENV=vm_stg OUT=backups/schema_stg.sql
make db-dump-schema-env ENV=local_dev OUT=backups/schema_local.sql
diff -u backups/schema_local.sql backups/schema_stg.sql | head -50
```

### local_dev での動作確認

```bash
# 同様の手順でlocal_devでも確認可能
make db-reset-volume-env ENV=local_dev
make up ENV=local_dev
make db-bootstrap-roles-env ENV=local_dev
make al-up ENV=local_dev  # または make al-up-env ENV=local_dev
make al-cur ENV=local_dev
```

### vm_prod での実行（極めて稀）

vm_prodへのDB reset は**原則禁止**です。どうしても必要な場合：

```bash
# バックアップを必ず取得
make backup ENV=vm_prod BACKUP_DIR=/path/to/safe/location

# FORCE=1 を付けて実行（警告を理解した上で）
make db-reset-volume-env ENV=vm_prod FORCE=1
```

## エラーハンドリング

### ガードによるエラー

vm_prodで FORCE=1 なしで実行すると：

```
❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌
❌  ERROR: DB reset on vm_prod is BLOCKED
❌
❌  This operation will DESTROY production database!
...
```

### 対応方法

1. ENVパラメータを確認
2. 本当にvm_prodで実行する必要があるか再確認
3. 必要な場合はバックアップ取得後に FORCE=1 を追加

## 変更ファイル一覧

### makefile

追加された箇所（db-bootstrap-roles-env の前に挿入）：

1. **DB Reset セクション**
   - `db-reset-volume-env`: volume削除による完全初期化
   - `db-reset-db-env`: DROP/CREATE による初期化
   - `check_reset_safety`: 誤爆防止ガード関数

2. **DB Schema Dump セクション**
   - `db-dump-schema-env`: schema-only dump

### その他のファイル

- `scripts/db/bootstrap_roles.sql`: 変更なし（既存のまま）
- `app/backend/core_api/migrations/alembic/versions/20251211_140000000_recreate_v_receive_weekly_monthly.py`: 変更なし（既に正しい実装）

## 注意事項

1. **データ破壊**: reset 操作はデータを完全に削除します
2. **本番環境**: vm_prod では原則実行しない
3. **バックアップ**: 重要なデータは必ずバックアップを取得
4. **待機時間**: 誤操作防止のため5秒の待機時間あり（Ctrl+Cでキャンセル可能）
5. **環境確認**: ENV と ENV_CANON の値を必ず確認

## トラブルシューティング

### Migration が途中で止まる場合

1. DBをリセット: `make db-reset-volume-env ENV=vm_stg`
2. コンテナ再起動: `make up ENV=vm_stg`
3. Bootstrap実行: `make db-bootstrap-roles-env ENV=vm_stg`
4. Migration再実行: `make al-up-env ENV=vm_stg`

### スキーマ差分がある場合

```bash
# 差分を確認
diff -u backups/schema_local.sql backups/schema_stg.sql

# 問題があれば、vm_stgを再初期化
make db-reset-volume-env ENV=vm_stg
make up ENV=vm_stg
make db-bootstrap-roles-env ENV=vm_stg
make al-up-env ENV=vm_stg
```

## 成功の確認

以下のコマンドで確認：

```bash
# 1. Alembic の現在のリビジョンを確認
make al-cur-env ENV=vm_stg
# → local_dev と同じ head を指していること

# 2. スキーマダンプで差分がないこと確認
make db-dump-schema-env ENV=vm_stg OUT=backups/schema_stg.sql
make db-dump-schema-env ENV=local_dev OUT=backups/schema_local.sql
diff -u backups/schema_local.sql backups/schema_stg.sql
# → 差分がない、またはコメントやシーケンス値などの無害な差分のみ

# 3. migration履歴確認
make al-hist-env ENV=vm_stg
```

## まとめ

- ✅ vm_prod への誤爆防止ガード実装済み
- ✅ DB完全クリア（2種類の方法）実装済み
- ✅ schema-only dump機能実装済み
- ✅ bootstrap_roles.sql は冪等性確保済み
- ✅ migration は正しい実装（修正不要）

これで vm_stg のDBを安全に初期化し、Alembicをheadまで適用できます。
