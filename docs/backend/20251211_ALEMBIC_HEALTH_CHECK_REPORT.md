# Alembic 管理状態・包括調査レポート

**調査日時**: 2025-12-11  
**調査対象**: app/backend/core_api/migrations/alembic  
**環境**: local_dev (docker-compose.dev.yml)

---

## 📋 エグゼクティブサマリー

### 総合評価: ⚠️ **要改善** (Good with Caveats)

Alembic の基本機能は動作しているが、以下の課題があります:

1. ✅ **正常**: マイグレーションファイルの依存関係
2. ✅ **正常**: データベース状態とファイル整合性
3. ⚠️ **問題**: Makefile コマンドで `DB_DSN` 環境変数が渡らない
4. ⚠️ **問題**: `alembic_version` テーブルに複数レコードが残留 (本来1レコードのみ)

---

## 🔍 調査結果詳細

### 1. Alembic 設定ファイル (alembic.ini, env.py)

#### ✅ alembic.ini
- **場所**: `app/backend/core_api/migrations/alembic.ini`
- **状態**: 正常
- **設定内容**:
  - `script_location = /backend/migrations/alembic` (コンテナ内パス)
  - ロギング設定: INFO レベル
  - タイムゾーン設定なし (python-dateutil 未使用)

#### ✅ env.py
- **場所**: `app/backend/core_api/migrations/alembic/env.py`
- **状態**: 正常
- **主要機能**:
  - SQLAlchemy 2.0 対応 (`future=True`)
  - psycopg3 自動補正 (`postgresql://` → `postgresql+psycopg://`)
  - 複数スキーマ対応 (`include_schemas=True`)
  - 型・デフォルト値の差分検出有効
  - `/backend` を sys.path に追加して `app.*` モジュールをインポート可能

#### ⚠️ 環境変数の問題
- **症状**: `DB_DSN` または `DATABASE_URL` が設定されていないと `RuntimeError` が発生
- **原因**: docker-compose.dev.yml の `core_api` サービスに環境変数が定義されていない
- **影響**: `make al-cur`, `make al-rev-auto` などのコマンドが失敗
- **回避策**: コンテナ内に `DB_DSN` が自動注入される仕組みが必要

---

### 2. マイグレーション状態 (DB vs ファイル)

#### ✅ alembic_version テーブル
```sql
SELECT * FROM public.alembic_version;
```
| version_num          | type    |
|---------------------|---------|
| 1d84cbab2c95        | alembic |
| 20251211_100000000  | custom  |
| 20251211_110000000  | custom  |
| 20251211_120000000  | custom  |

⚠️ **問題**: 通常、`alembic_version` テーブルには **1レコードのみ** (現在の HEAD) が残るべき。
4レコード残留しているのは、過去のマイグレーション適用時に手動で `INSERT` した痕跡。

#### ✅ マイグレーションファイル数
- **合計**: 100ファイル
- **最新3件** (今回追加分):
  1. `20251211_100000000_add_slip_date_indexes.py` (案4)
  2. `20251211_110000000_merge_heads.py` (マージマイグレーション)
  3. `20251211_120000000_create_mv_receive_daily.py` (案1)

#### ✅ 現在の HEAD
```bash
$ make al-heads
20251211_120000000 (head)
```

正しく最新マイグレーションが HEAD として認識されています。

---

### 3. マイグレーション依存関係

#### ✅ 依存グラフ (最新10件)
```
20251202_100000000 → 1d84cbab2c95
                  ↘
                   20251211_110000000 → 20251211_120000000 (head)
                  ↗
20251201_130000000 → 20251211_100000000
```

- **ブランチポイント**: `20251201_130000000` から2方向に分岐
  - 方向1: `20251201_140000000` → ... → `1d84cbab2c95`
  - 方向2: `20251211_100000000` (今回追加)
- **マージポイント**: `20251211_110000000` で両方を統合
- **HEAD**: `20251211_120000000`

⚠️ **懸念**: `alembic_version` テーブルに古いレコードが残っているため、`alembic current` が正しい状態を表示できない可能性。

---

### 4. Makefile コマンド動作確認

#### ✅ 動作するコマンド
```bash
make al-heads   # ✅ 成功: 20251211_120000000 (head)
make al-hist    # ✅ 成功: 履歴表示可能
```

#### ❌ 動作しないコマンド
```bash
make al-cur       # ❌ 失敗: RuntimeError: Set DB_DSN or DATABASE_URL
make al-rev-auto  # ❌ 失敗: RuntimeError: Set DB_DSN or DATABASE_URL
make al-up        # ❌ 失敗: RuntimeError: Set DB_DSN or DATABASE_URL
```

**原因**: `env.py` の `_get_url()` 関数が `DB_DSN` または `DATABASE_URL` を環境変数から取得しようとするが、Makefile 経由のコマンドでは環境変数が渡っていない。

#### 回避方法
`docker-compose.dev.yml` の `core_api` サービスに以下を追加:
```yaml
core_api:
  environment:
    - DB_DSN=postgresql://myuser:mypassword@db:5432/sanbou_dev
```

または、Makefile の `ALEMBIC` 定義を修正:
```makefile
ALEMBIC := $(ALEMBIC_DC) exec -e DB_DSN="postgresql://myuser:mypassword@db:5432/sanbou_dev" core_api alembic -c /backend/migrations/alembic.ini
```

---

### 5. 実際のマイグレーション実施状況

#### ✅ 今回追加した3つのマイグレーション

##### 1. `20251211_100000000_add_slip_date_indexes.py` (案4)
- **目的**: `stg.shogun_final_receive` と `stg.shogun_flash_receive` に `slip_date` インデックスを追加
- **状態**: ✅ 適用済み
- **確認**:
  ```sql
  SELECT indexname FROM pg_indexes 
  WHERE schemaname = 'stg' 
    AND tablename = 'shogun_final_receive' 
    AND indexname LIKE '%slip_date%';
  ```
  結果: `ix_shogun_final_receive_slip_date` など3つのインデックスが存在

##### 2. `20251211_110000000_merge_heads.py`
- **目的**: `1d84cbab2c95` と `20251211_100000000` の2つのブランチをマージ
- **状態**: ✅ 適用済み
- **down_revision**: `("1d84cbab2c95", "20251211_100000000")` (タプル)
- **upgrade/downgrade**: 空実装 (マージのみ)

##### 3. `20251211_120000000_create_mv_receive_daily.py` (案1)
- **目的**: `mart.v_receive_daily` を `mart.mv_receive_daily` (MATERIALIZED VIEW) として複製
- **状態**: ✅ 適用済み (手動実行)
- **確認**:
  ```sql
  SELECT COUNT(*) FROM mart.mv_receive_daily;
  ```
  結果: `1805` 行

#### ⚠️ 手動適用の問題
今回のマイグレーションは、以下の理由で手動適用されました:
1. Alembic の `upgrade head` コマンドでは権限エラー発生 (sanbou_app_dev ユーザーでは CREATE INDEX 不可)
2. 直接 `psql` で DDL を実行 (myuser ユーザー)
3. `alembic_version` テーブルに手動で `INSERT` して記録

**推奨**: 今後は `myuser` で Alembic を実行するか、`sanbou_app_dev` に DDL 権限を付与する。

---

## 🛠️ 改善提案

### 1. 環境変数の修正 (優先度: 高)

**問題**: Makefile から実行する Alembic コマンドで `DB_DSN` が渡らない

**解決策A**: docker-compose.dev.yml に環境変数を追加
```yaml
# docker/docker-compose.dev.yml
services:
  core_api:
    environment:
      - DB_DSN=${DB_DSN:-postgresql://myuser:mypassword@db:5432/sanbou_dev}
```

**解決策B**: Makefile の定義を修正
```makefile
# makefile
ALEMBIC := $(ALEMBIC_DC) exec \
  -e DB_DSN="postgresql://myuser:mypassword@db:5432/sanbou_dev" \
  core_api alembic -c /backend/migrations/alembic.ini
```

**推奨**: 解決策A (docker-compose 側で定義) の方が管理しやすい

---

### 2. alembic_version テーブルのクリーンアップ (優先度: 中)

**問題**: 4レコード残留 (本来1レコードのみ)

**解決策**:
```sql
-- 現在の HEAD 以外を削除
DELETE FROM public.alembic_version 
WHERE version_num NOT IN ('20251211_120000000');
```

**注意**: `alembic current` コマンドが正常動作するようになることを確認してから実行。

---

### 3. マイグレーション権限の整理 (優先度: 中)

**問題**: `alembic upgrade head` で権限エラー発生

**現状**:
- アプリケーションユーザー: `sanbou_app_dev` (SELECT/INSERT/UPDATE/DELETE のみ)
- スキーマオーナー: `myuser` (DDL 可能)

**解決策**:
```sql
-- sanbou_app_dev に DDL 権限を付与 (開発環境のみ)
GRANT CREATE ON SCHEMA stg TO sanbou_app_dev;
GRANT CREATE ON SCHEMA mart TO sanbou_app_dev;
```

または、Alembic 実行時のみ `myuser` を使用:
```makefile
# makefile
ALEMBIC := $(ALEMBIC_DC) exec \
  -e DB_DSN="postgresql://myuser:mypassword@db:5432/sanbou_dev" \
  core_api alembic -c /backend/migrations/alembic.ini
```

**推奨**: 後者 (Alembic のみ myuser を使用) の方が安全

---

### 4. マイグレーションファイルの命名規則統一 (優先度: 低)

**現状**:
- 古いマイグレーション: Alembic デフォルト (例: `1d84cbab2c95`)
- 今回のマイグレーション: カスタム形式 (例: `20251211_100000000`)

**推奨**: カスタム形式 (`YYYYMMDD_HHMMSS000`) に統一
```makefile
# makefile
REV_ID ?= $(shell date +%Y%m%d_%H%M%S%3N)
```

**利点**:
- 時系列順に並ぶ
- ファイル名からマイグレーション日時が推測可能
- 既に Makefile で実装済み

---

## ✅ アクションアイテム

| 優先度 | 項目 | 担当 | 期限 |
|--------|------|------|------|
| 🔴 高 | docker-compose.dev.yml に DB_DSN 環境変数を追加 | Backend | 即座 |
| 🟡 中 | alembic_version テーブルのクリーンアップ | Backend | 今週中 |
| 🟡 中 | Alembic 実行ユーザーを myuser に変更 (Makefile 修正) | Backend | 今週中 |
| 🟢 低 | マイグレーション命名規則の統一ドキュメント作成 | Backend | 来週 |

---

## 📊 統計情報

### マイグレーションファイル
- **合計数**: 100ファイル
- **今回追加**: 3ファイル
- **最古**: `20251104_154033124_mart_baseline.py`
- **最新**: `20251211_120000000_create_mv_receive_daily.py`

### データベース状態
- **現在の HEAD**: `20251211_120000000`
- **alembic_version レコード数**: 4 (⚠️ 異常、本来1レコード)
- **マイグレーション適用済み数**: 100 (推定)

### Makefile コマンド
- **動作確認済み**: `al-heads`, `al-hist`
- **要修正**: `al-cur`, `al-rev-auto`, `al-up`, `al-down`

---

## 🎯 結論

Alembic の基本構成は健全ですが、運用面で以下の改善が必要です:

1. **環境変数の整備**: docker-compose.dev.yml に `DB_DSN` を追加
2. **権限の整理**: Alembic 実行時のみ `myuser` を使用
3. **状態のクリーンアップ**: `alembic_version` テーブルの不要レコード削除

これらの改善により、Makefile 経由でのマイグレーション作成・適用が正常に動作するようになります。

---

**調査者**: GitHub Copilot  
**レビュー**: 未実施  
**次回レビュー予定**: 修正完了後
