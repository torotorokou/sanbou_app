# PostgreSQL 16 → 17 安全アップグレードガイド

**最終更新**: 2025-10-30  
**対象環境**: Docker Compose (local_dev / local_stg / vm_stg / vm_prod)

---

## 📌 目的

PostgreSQL 16 から 17 へ **論理ダンプ＋リストア方式**で安全に移行します。  
既存のデータボリュームは **完全に保持** し、新規ボリュームに v17 クラスタを構築します。

---

## 🎯 ゴール

- ✅ データ損失ゼロ
- ✅ ロールバック可能（旧ボリューム温存）
- ✅ 拡張機能（PostGIS/pg_trgm/uuid-ossp 等）の維持
- ✅ 再現可能な手順（Makefile ターゲット + スクリプト）

---

## 📐 方針

### 1. **非破壊アプローチ**
- 旧クラスタ（v16）のボリュームは削除しない
- 新規ボリュームに v17 クラスタを新規作成
- `down -v` は **絶対禁止**（ボリューム消去のため）

### 2. **移行ステップ**
1. 旧ボリュームのメジャーバージョン確認（`PG_VERSION` ファイル読み取り）
2. 旧ボリュームの物理バックアップ（tar.gz）
3. 全DB論理ダンプ（`pg_dumpall`）
4. v17 用 Compose オーバーライド作成
5. v17 クラスタ起動（空DB）
6. ダンプをリストア
7. 拡張機能の再有効化
8. 動作確認

### 3. **環境ごとの違い**
| 環境 | ボリューム種別 | 対象ボリューム名 | 注意点 |
|------|---------------|------------------|--------|
| **local_dev** | ホストバインド | `data/postgres` | 物理バックアップが高速 |
| **local_stg** | 名前付きボリューム | `local_stg_db_data` | docker volume コマンド使用 |
| **vm_stg** | 名前付きボリューム | `vm_stg_db_data` | 本番リハーサル推奨 |
| **vm_prod** | 名前付きボリューム | `vm_prod_db_data` | メンテナンスウィンドウ必須 |

---

## 📋 手順サマリ

以下のコマンドは **Makefile ターゲット** として実装済みです（後述）。

```bash
# 0) 旧クラスタのメジャー版確認
make pg.version ENV=local_dev

# 1) 旧ボリュームの物理バックアップ（推奨）
make pg.archive ENV=local_dev

# 2) 全DB論理ダンプ（pg_dumpall）
make pg.dumpall ENV=local_dev

# 3) v17 用 Compose オーバーライド作成
make pg.compose17 ENV=local_dev

# 4) docker-compose.pg17.yml を確認・編集（必要に応じて）
cat docker-compose.pg17.yml

# 5) v17 クラスタ起動（空DB）
make pg.up17 ENV=local_dev

# 6) ダンプをリストア（最新ダンプを指定）
make pg.restore ENV=local_dev SQL=backups/pg/pg_dumpall_YYYYMMDD_HHMMSS.sql

# 7) 拡張機能の再有効化
make pg.extensions ENV=local_dev

# 8) 動作確認
make pg.verify ENV=local_dev
```

---

## 🔧 実装済みツール

### Makefile ターゲット
| ターゲット | 説明 | 引数 |
|-----------|------|------|
| `make pg.version` | 既存ボリュームの PG バージョン確認 | `ENV=<env>` |
| `make pg.archive` | 旧ボリュームの tar.gz バックアップ | `ENV=<env>` |
| `make pg.dumpall` | pg_dumpall で全DB論理ダンプ | `ENV=<env>` |
| `make pg.compose17` | v17 用 Compose オーバーライド生成 | `ENV=<env>` |
| `make pg.up17` | v17 クラスタ起動 | `ENV=<env>` |
| `make pg.restore` | ダンプをリストア | `ENV=<env> SQL=<path>` |
| `make pg.extensions` | 拡張機能再有効化 | `ENV=<env>` |
| `make pg.verify` | 動作確認（version/DB一覧/拡張一覧） | `ENV=<env>` |

### スクリプト
| ファイル | 説明 |
|---------|------|
| `scripts/pg/print_pg_version_in_volume.sh` | ボリューム内の PG_VERSION 読み取り |
| `scripts/pg/archive_volume_tar.sh` | ボリューム全体を tar.gz 化 |
| `scripts/pg/dumpall_from_v16.sh` | v16 コンテナを一時起動して pg_dumpall |
| `scripts/pg/restore_to_v17.sh` | v17 へ SQL リストア |
| `sql/extensions_after_restore.sql` | 拡張再有効化テンプレート |

---

## 🔄 Rollback 手順

### 前提
- 旧ボリュームは削除していないこと
- `down -v` を実行していないこと

### 手順
1. **v17 を停止**
   ```bash
   docker compose -f docker/docker-compose.dev.yml -f docker-compose.pg17.yml down
   ```

2. **元の v16 構成で再起動**
   ```bash
   make up ENV=local_dev
   ```

3. **データ確認**
   ```bash
   make pg.verify ENV=local_dev
   ```

4. **必要に応じて物理バックアップから復元**
   ```bash
   # 旧ボリュームが破損している場合のみ
   docker volume rm local_dev_db_data  # 注意: これは最終手段
   docker volume create local_dev_db_data
   docker run --rm -v local_dev_db_data:/restore -v $(pwd)/backups/pg:/backup busybox \
     tar -xzf /backup/volume_local_dev_db_data_YYYYMMDD_HHMMSS.tgz -C /restore
   ```

---

## 🧩 拡張機能の再有効化

### 確認方法
```sql
-- 旧環境で確認
\dx
```

### 再有効化
`sql/extensions_after_restore.sql` を編集してから実行：

```sql
-- 必要な拡張のみ残してください
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;
```

実行：
```bash
make pg.extensions ENV=local_dev
```

---

## 🚨 トラブルシュート

### 1. 認証エラー (`FATAL: password authentication failed`)
**原因**: `.env` ファイルの `POSTGRES_PASSWORD` が不一致  
**対策**:
```bash
# 環境変数を確認
make config ENV=local_dev | grep POSTGRES_PASSWORD

# 必要に応じて secrets/.env.local_dev.secrets を編集
```

### 2. 権限エラー (`permission denied for schema public`)
**原因**: ダンプに GRANT 文が含まれていない  
**対策**:
```bash
# pg_dumpall に --globals-only を追加
docker exec <container> pg_dumpall -U postgres --globals-only > globals.sql
psql -h localhost -U postgres < globals.sql
```

### 3. 巨大テーブルでリストアが遅い
**対策**: インデックス再作成を後回しに
```bash
# --section オプションで分割
pg_restore --section=pre-data your.dump
pg_restore --section=data your.dump
pg_restore --section=post-data your.dump  # インデックス・制約
```

### 4. PostGIS バージョン不整合
**エラー例**: `postgis is not available for postgres:17`  
**対策**: `docker-compose.pg17.yml` の image を変更
```yaml
services:
  db:
    image: postgis/postgis:17-3.5  # PostGIS 3.5 for PG 17
```

### 5. pg_dumpall が途中で止まる
**原因**: 長時間ロックまたは巨大オブジェクト  
**対策**:
```bash
# 単一DBずつダンプ
pg_dump -U postgres -d sanbou_dev -Fc > sanbou_dev.dump
pg_restore -U postgres -d postgres sanbou_dev.dump
```

---

## 📝 注意事項

### ❌ やってはいけないこと
1. **`docker compose down -v`** を実行（ボリューム削除）
2. 旧ボリュームの上書き（必ず新規ボリュームに移行）
3. バックアップなしでの本番移行

### ✅ 推奨事項
1. **必ず dev 環境でリハーサル**
2. 物理バックアップ + 論理ダンプの **二段構え**
3. メンテナンスウィンドウの確保（本番は30分～2時間想定）
4. ディスク空き容量の確認（データサイズの 3倍以上推奨）

---

## 📚 参考リンク

- [PostgreSQL 17 Release Notes](https://www.postgresql.org/docs/17/release-17.html)
- [pg_upgrade vs pg_dump/restore](https://www.postgresql.org/docs/current/upgrading.html)
- [PostGIS Upgrade Guide](https://postgis.net/docs/manual-3.5/postgis_installation.html#upgrading)

---

## 🎓 追加情報

### なぜ pg_upgrade を使わないのか？
- Docker ボリュームの制約（両バージョンの同時マウントが複雑）
- 拡張機能のバイナリ互換性リスク
- ロールバックの簡便性（論理ダンプは汎用的）

### 本番環境での移行タイミング
1. **事前準備** (1週間前):
   - dev/stg 環境での完全リハーサル
   - データ量に基づく所要時間計測
   - ロールバック手順の確認

2. **当日** (深夜メンテナンス):
   - 全サービス停止
   - 論理ダンプ取得（15分）
   - v17 起動＋リストア（30～90分）
   - 動作確認（15分）
   - サービス再開

3. **翌日**:
   - 監視ログ確認
   - パフォーマンスベースライン再取得

---

**作成者**: AI (GitHub Copilot)  
**更新履歴**:
- 2025-10-30: 初版作成（v16 → v17 対応）
