# CASCADE削除による影響調査レポート

**作成日**: 2025年12月11日  
**調査対象**: `mart.v_receive_daily` VIEW 削除時のCASCADE影響  
**トリガー**: マイグレーション `e581d89ba5db_drop_v_receive_daily_view.py` による `DROP VIEW ... CASCADE`

---

## エグゼクティブサマリー

**問題**: `mart.v_receive_daily` VIEW を削除した際、`CASCADE` オプションにより依存する6つのオブジェクト（VIEW 2つ、MV 4つ）が連鎖削除された。

**影響範囲**:

- ✅ **復元完了**: 全6オブジェクトを再作成し、データも復元済み
- ⚠️ **命名規則違反**: マイグレーションID `e581d89ba5db` を標準形式 `YYYYMMDD_HHMMSS` に修正
- 🔄 **マイグレーション追加**: 3つの新規マイグレーションで復元処理を正式化

**根本原因**: `DROP VIEW IF EXISTS mart.v_receive_daily CASCADE;` の実行により、このVIEWに依存する全オブジェクトが自動削除された。

---

## 1. 削除されたオブジェクト一覧

### 1.1. 削除されたVIEW（2つ）

| オブジェクト名           | 種別 | 用途         | 依存関係                    |
| ------------------------ | ---- | ------------ | --------------------------- |
| `mart.v_receive_weekly`  | VIEW | 週次受入集計 | `FROM mart.v_receive_daily` |
| `mart.v_receive_monthly` | VIEW | 月次受入集計 | `FROM mart.v_receive_daily` |

**削除理由**:

- 両VIEWとも `FROM mart.v_receive_daily` で定義されていたため、親VIEWの削除時にCASCADE削除された

### 1.2. 削除されたMaterialized View（4つ）

| オブジェクト名                   | 種別 | 用途                     | 依存関係                    | データサイズ   |
| -------------------------------- | ---- | ------------------------ | --------------------------- | -------------- |
| `mart.mv_inb5y_week_profile_min` | MV   | 5年間週次プロファイル    | `FROM mart.v_receive_daily` | 32 KB (53行)   |
| `mart.mv_inb_avg5y_day_biz`      | MV   | 5年間平日日次平均        | `FROM mart.v_receive_daily` | 64 KB (312行)  |
| `mart.mv_inb_avg5y_weeksum_biz`  | MV   | 5年間週次合計（営業日）  | `FROM mart.v_receive_daily` | 40 KB (53行)   |
| `mart.mv_inb_avg5y_day_scope`    | MV   | 5年間日次平均（全/営業） | `FROM mart.v_receive_daily` | 184 KB (679行) |

**削除理由**:

- 全MVのCTE定義内で `FROM mart.v_receive_daily` を参照していたため、親VIEWの削除時にCASCADE削除された
- SQL定義ファイル（`sql/mart/mv_inb*.sql`）は既に `mv_receive_daily` 参照に更新済みだったが、DB上のMVは旧定義のまま残っていた

### 1.3. 削除されなかったオブジェクト（正常）

以下のオブジェクトは削除されず、正常に動作継続：

| オブジェクト名                | 種別 | 理由                                                     |
| ----------------------------- | ---- | -------------------------------------------------------- |
| `mart.mv_target_card_per_day` | MV   | 今回の作業で `mv_receive_daily` 参照に更新済み           |
| `mart.mv_receive_daily`       | MV   | 削除対象ではなく、`v_receive_daily` の代替として新規作成 |

---

## 2. CASCADE削除の連鎖メカニズム

### 2.1. 削除コマンド

```sql
DROP VIEW IF EXISTS mart.v_receive_daily CASCADE;
```

### 2.2. CASCADE連鎖図

```
mart.v_receive_daily (VIEW) - DROP CASCADE
  ↓
  ├─ mart.v_receive_weekly (VIEW) ──────────────── CASCADE削除
  ├─ mart.v_receive_monthly (VIEW) ─────────────── CASCADE削除
  ├─ mart.mv_inb5y_week_profile_min (MV) ──────── CASCADE削除
  ├─ mart.mv_inb_avg5y_day_biz (MV) ───────────── CASCADE削除
  ├─ mart.mv_inb_avg5y_weeksum_biz (MV) ──────── CASCADE削除
  └─ mart.mv_inb_avg5y_day_scope (MV) ─────────── CASCADE削除
```

### 2.3. PostgreSQL依存関係検出

PostgreSQLは以下の方法で依存関係を検出：

- VIEW定義内の `FROM`, `JOIN` 句に含まれるテーブル/VIEW名
- Materialized View定義内のクエリで参照されるオブジェクト
- `CASCADE` オプション指定時、これらの依存オブジェクトも再帰的に削除

---

## 3. 復元作業の詳細

### 3.1. 復元手順（実施済み）

#### Step 1: v_receive_weekly, v_receive_monthly の再作成

```bash
# SQL定義ファイルを実行（既にmv_receive_daily参照に更新済み）
docker compose exec -T db psql -U myuser -d sanbou_dev \
  < app/backend/core_api/migrations/alembic/sql/mart/v_receive_weekly.sql

docker compose exec -T db psql -U myuser -d sanbou_dev \
  < app/backend/core_api/migrations/alembic/sql/mart/v_receive_monthly.sql
```

**結果**: ✅ 再作成成功

#### Step 2: 5年平均系MVの再作成

```bash
# 4つのMVを順次作成
for mv in mv_inb5y_week_profile_min mv_inb_avg5y_day_biz \
          mv_inb_avg5y_day_scope mv_inb_avg5y_weeksum_biz; do
  docker compose exec -T db psql -U myuser -d sanbou_dev \
    < app/backend/core_api/migrations/alembic/sql/mart/${mv}.sql
done
```

**結果**: ✅ 全MV作成成功（WITH NO DATA）

#### Step 3: UNIQUE INDEXの作成

```sql
-- REFRESH CONCURRENTLY要件のためUNIQUE INDEXを作成
CREATE UNIQUE INDEX mv_inb5y_week_profile_min_pk
  ON mart.mv_inb5y_week_profile_min (iso_week);

CREATE UNIQUE INDEX mv_inb_avg5y_day_biz_pk
  ON mart.mv_inb_avg5y_day_biz (iso_week, iso_dow);

CREATE UNIQUE INDEX mv_inb_avg5y_weeksum_biz_pk
  ON mart.mv_inb_avg5y_weeksum_biz (iso_week);

CREATE UNIQUE INDEX ux_mv_inb_avg5y_day_scope
  ON mart.mv_inb_avg5y_day_scope (scope, iso_week, iso_dow);
```

**結果**: ✅ 全INDEX作成成功

#### Step 4: 初回REFRESH実行

```sql
REFRESH MATERIALIZED VIEW mart.mv_inb5y_week_profile_min;
REFRESH MATERIALIZED VIEW mart.mv_inb_avg5y_day_biz;
REFRESH MATERIALIZED VIEW mart.mv_inb_avg5y_day_scope;
REFRESH MATERIALIZED VIEW mart.mv_inb_avg5y_weeksum_biz;
```

**結果**: ✅ 全MV REFRESH成功、データ復元完了

### 3.2. 復元後の状態確認

```sql
-- Materialized Views
SELECT matviewname,
       pg_size_pretty(pg_total_relation_size('mart.' || matviewname)) AS size
FROM pg_matviews
WHERE schemaname = 'mart';
```

| MV名                        | サイズ | 行数  | 状態                  |
| --------------------------- | ------ | ----- | --------------------- |
| `mv_receive_daily`          | 320 KB | 1,805 | ✅ 正常               |
| `mv_target_card_per_day`    | 344 KB | 2,191 | ✅ 正常               |
| `mv_sales_tree_daily`       | 24 KB  | -     | ⚠️ 未使用（削除候補） |
| `mv_inb5y_week_profile_min` | 32 KB  | 53    | ✅ 復元完了           |
| `mv_inb_avg5y_day_biz`      | 64 KB  | 312   | ✅ 復元完了           |
| `mv_inb_avg5y_weeksum_biz`  | 40 KB  | 53    | ✅ 復元完了           |
| `mv_inb_avg5y_day_scope`    | 184 KB | 679   | ✅ 復元完了           |

```sql
-- Views
SELECT viewname FROM pg_views WHERE schemaname = 'mart';
```

| VIEW名                         | 状態        |
| ------------------------------ | ----------- |
| `v_customer_sales_daily`       | ✅ 正常     |
| `v_daily_target_with_calendar` | ✅ 正常     |
| `v_sales_tree_daily`           | ✅ 正常     |
| `v_sales_tree_detail_base`     | ✅ 正常     |
| `v_receive_weekly`             | ✅ 復元完了 |
| `v_receive_monthly`            | ✅ 復元完了 |

---

## 4. マイグレーション命名規則の修正

### 4.1. 問題のあったマイグレーション

**旧ファイル名**: `e581d89ba5db_drop_v_receive_daily_view.py`

- ❌ リビジョンID: `e581d89ba5db` (ランダムな16進数)
- ❌ 命名規則違反: `alembic revision --autogenerate` で自動生成された名前

**標準規則**: `YYYYMMDD_HHMMSSMMM_descriptive_name.py`

- 例: `20251211_120000000_create_mv_receive_daily.py`

### 4.2. 修正後のマイグレーション構成

以下の3つの新規マイグレーションを作成し、正式な復元手順として記録：

#### 1. `20251211_130000000_drop_v_receive_daily_view.py`

**内容**:

```python
def upgrade() -> None:
    # Drop v_receive_daily VIEW (replaced by mv_receive_daily materialized view)
    # CASCADE will drop dependent objects:
    # - mart.v_receive_weekly
    # - mart.v_receive_monthly
    # - mart.mv_inb5y_week_profile_min
    # - mart.mv_inb_avg5y_day_biz
    # - mart.mv_inb_avg5y_weeksum_biz
    # - mart.mv_inb_avg5y_day_scope
    op.execute("DROP VIEW IF EXISTS mart.v_receive_daily CASCADE;")

def downgrade() -> None:
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_receive_daily AS
        SELECT * FROM mart.mv_receive_daily;
    """)
```

**Down revision**: `20251211_120000000`  
**目的**: v_receive_daily VIEW削除とCASCADE影響の記録

#### 2. `20251211_140000000_recreate_v_receive_weekly_monthly.py`

**内容**:

```python
def upgrade() -> None:
    print("[mart] Recreating v_receive_weekly...")
    op.execute(_read_sql("v_receive_weekly.sql"))

    print("[mart] Recreating v_receive_monthly...")
    op.execute(_read_sql("v_receive_monthly.sql"))
```

**Down revision**: `20251211_130000000`  
**目的**: 週次・月次集計VIEWの復元

#### 3. `20251211_150000000_recreate_5year_avg_mvs.py`

**内容**:

```python
def upgrade() -> None:
    # 4つのMVを作成 + UNIQUE INDEX + REFRESH
    for mv in [
        "mv_inb5y_week_profile_min",
        "mv_inb_avg5y_day_biz",
        "mv_inb_avg5y_weeksum_biz",
        "mv_inb_avg5y_day_scope"
    ]:
        op.execute(_read_sql(f"{mv}.sql"))
        op.execute(f"CREATE UNIQUE INDEX {mv}_pk ON mart.{mv} (...);")
        op.execute(f"REFRESH MATERIALIZED VIEW mart.{mv};")
```

**Down revision**: `20251211_140000000`  
**目的**: 5年平均系MVの復元とデータ投入

### 4.3. マイグレーション履歴の更新

```sql
-- alembic_versionテーブルを手動更新
UPDATE alembic_version SET version_num = '20251211_150000000';
```

**理由**: DB上のオブジェクトは既に復元済みのため、マイグレーション履歴のみを最新状態に同期

---

## 5. 影響分析と対策

### 5.1. なぜCASCADE削除が発生したか？

**原因1: SQL定義とDB実体の不一致**

- SQL定義ファイル（`sql/mart/*.sql`）は既に `mv_receive_daily` 参照に更新済み
- しかしDB上のMV/VIEWオブジェクトは旧定義（`v_receive_daily` 参照）のまま残っていた
- `DROP VIEW ... CASCADE` 実行時、DB上の実際の依存関係に基づいて削除が連鎖

**原因2: マイグレーション順序の誤り**

- 正しい順序:
  1. 依存オブジェクト（MV/VIEW）を `mv_receive_daily` 参照に更新
  2. `v_receive_daily` VIEW を削除
- 実際の順序:
  1. SQL定義ファイルのみ更新（DBは未更新）
  2. `v_receive_daily` VIEW を削除 → CASCADE発動

### 5.2. 今回の対策

✅ **実施済み**:

1. 削除された全オブジェクトを再作成（SQL定義ファイルを使用）
2. マイグレーション命名規則違反を修正（`e581d89ba5db` → `20251211_130000000`）
3. 復元手順を正式なマイグレーションとして記録（20251211_140000000, 20251211_150000000）

### 5.3. 今後の予防策

#### 推奨マイグレーション手順（VIEW/MV置換時）

```python
# ❌ 危険: 依存関係を無視した削除
def upgrade():
    op.execute("DROP VIEW old_view CASCADE;")  # 連鎖削除発生！

# ✅ 安全: 段階的な置換
def upgrade():
    # Step 1: 依存オブジェクトをREFRESHで更新（SQL定義は事前に更新済み）
    for mv in dependent_mvs:
        op.execute(f"DROP MATERIALIZED VIEW IF EXISTS {mv};")
        op.execute(_read_sql(f"{mv}.sql"))  # 新定義で再作成
        op.execute(f"CREATE UNIQUE INDEX {mv}_pk ON {mv} (...);")
        op.execute(f"REFRESH MATERIALIZED VIEW {mv};")

    for view in dependent_views:
        op.execute(f"DROP VIEW IF EXISTS {view};")
        op.execute(_read_sql(f"{view}.sql"))  # 新定義で再作成

    # Step 2: 元のVIEWを安全に削除（依存なし）
    op.execute("DROP VIEW IF EXISTS old_view;")  # CASCADEなし
```

#### マイグレーション設計チェックリスト

- [ ] SQL定義ファイル更新とDB更新を同一マイグレーションで実施
- [ ] `DROP ... CASCADE` を使う前に依存関係を明示的に確認
- [ ] 依存オブジェクトは親オブジェクト削除「前」に更新
- [ ] マイグレーションIDは `YYYYMMDD_HHMMSSMMM` 形式を厳守
- [ ] downgrade() で完全なロールバックが可能か確認

---

## 6. 結論と推奨事項

### 6.1. 調査結論

| 項目                         | 結果                                  |
| ---------------------------- | ------------------------------------- |
| **削除されたオブジェクト数** | 6つ（VIEW 2つ、MV 4つ）               |
| **データ損失**               | なし（全て復元可能）                  |
| **復元状態**                 | ✅ 100%復元完了                       |
| **ダウンタイム**             | なし（開発環境のみ）                  |
| **根本原因**                 | SQL定義とDB実体の不一致 + CASCADE削除 |

### 6.2. 推奨事項

#### 短期（今後1週間）

1. ✅ **完了**: 削除された全オブジェクトの復元
2. ✅ **完了**: マイグレーション命名規則の修正
3. ✅ **完了**: 復元手順の正式マイグレーション化
4. 🔄 **次回**: `mv_sales_tree_daily` の削除（未使用MV）

#### 中期（今後1ヶ月）

1. MV/VIEW置換時の標準手順をドキュメント化
2. マイグレーションレビュー時のチェックリスト作成
3. CI/CDパイプラインでマイグレーション命名規則チェックを追加

#### 長期（今後3ヶ月）

1. MVの自動更新ロジックを全対象MVに拡張
2. MV更新パフォーマンス監視の導入
3. PostgreSQL依存関係の可視化ツール導入

---

## 7. 参考情報

### 7.1. 関連ドキュメント

- [MV自動更新アーキテクチャ調査](./20251211_MV_AUTO_REFRESH_CURRENT_ARCHITECTURE_SURVEY.md)
- [MV削除候補リスト](./20251211_MV_DELETION_CANDIDATE_LIST.md)

### 7.2. マイグレーション履歴

```
20251211_110000000 → 20251211_120000000  (create mv_receive_daily)
20251211_120000000 → 20251211_130000000  (drop v_receive_daily CASCADE)
20251211_130000000 → 20251211_140000000  (recreate v_receive_weekly/monthly)
20251211_140000000 → 20251211_150000000  (recreate 5-year avg MVs) ← HEAD
```

### 7.3. PostgreSQL CASCADE削除の仕組み

```sql
-- 依存関係の確認
SELECT
    dependent.relname AS dependent_view,
    referenced.relname AS referenced_view
FROM pg_depend d
JOIN pg_rewrite r ON r.oid = d.objid
JOIN pg_class dependent ON r.ev_class = dependent.oid
JOIN pg_class referenced ON d.refobjid = referenced.oid
WHERE referenced.relname = 'v_receive_daily'
AND dependent.relnamespace::regnamespace::text = 'mart';
```

---

**作成者**: GitHub Copilot  
**最終更新**: 2025年12月11日  
**ステータス**: 全復元完了 ✅
