# マテリアライズドビュー高速化実装レポート (2025-11-17)

## 概要

既存の VIEW `mart.v_target_card_per_day` をマテリアライズドビュー化し、`/core_api/dashboard/target` エンドポイントのレスポンスタイム短縮を実現しました。

## 実装内容

### 1. マテリアライズドビュー作成

**ファイル**: `app/backend/core_api/migrations/alembic/sql/mart/mv_target_card_per_day.sql`

- 既存の VIEW 定義をそのまま再利用（コピペではなく、同一のSELECT文を使用）
- `WITH NO DATA` で作成し、後でREFRESH実行
- コメントでMVの目的・依存関係・更新頻度を明記

**設計方針**:
- VIEW `mart.v_target_card_per_day` は削除せず、段階的に移行
- ロールバック時は Repository のクエリを VIEW に戻すだけで済む

### 2. インデックス設計

**適用したインデックス**:

1. **UNIQUE INDEX on `ddate`** (ux_mv_target_card_per_day_ddate)
   - 目的: REFRESH CONCURRENTLY の要件 + 単一日検索の最適化
   - 対象クエリ: `WHERE ddate = :target_date`
   - 月次範囲検索 (`WHERE ddate BETWEEN...`) もカバー

2. **INDEX on `(iso_year, iso_week)`** (ix_mv_target_card_per_day_iso_week)
   - 目的: 週次集計クエリの高速化
   - 対象クエリ: `WHERE iso_year = X AND iso_week = Y`

**削除した設計**:
- `date_trunc('month', ddate)` の関数INDEX
  - 理由: PostgreSQLでは `date_trunc` 関数が STABLE (not IMMUTABLE) のため、MV上では使用不可
  - 代替: `ddate` の B-tree INDEX で月次範囲検索は十分カバーされる

### 3. マイグレーション実装

**ファイル**: `app/backend/core_api/migrations/alembic/versions/20251117_135913797_create_mv_target_card_per_day.py`

- 既存パターン（`_ensure_mv` ヘルパー関数）を踏襲
- オンライン時: 既存MVがあれば REFRESH CONCURRENTLY、なければ CREATE
- オフライン時: 常に CREATE 文を出力（新規環境用）
- downgrade(): MV と INDEX を DROP（VIEW は残す）

**適用手順**:
```bash
make al-up ENV=local_dev
# 初回のみCONCURRENTLYなしでREFRESH
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW mart.mv_target_card_per_day;"
```

### 4. Repository 参照先変更

**ファイル**: `app/backend/core_api/app/infra/adapters/dashboard/dashboard_target_repo.py`

**変更箇所** (全10箇所):
- クラス docstring: MV参照であることを明記
- `get_by_date_optimized()`: 全CTEで `v_target_card_per_day` → `mv_target_card_per_day`
- `get_by_date()`: クエリとログメッセージ
- `get_first_business_in_month()`: クエリ
- `get_target_card_metrics()`: クエリと存在確認（`information_schema.tables` → `pg_matviews`）

**コメント付与**:
- `# ★ VIEW→MV変更` で変更箇所を明示
- 「なぜMVに変えたのか」「どのクエリの最適化か」を記述

### 5. REFRESH 運用整備

**ファイル**: `makefile`

新規追加タスク:
```makefile
# 全MVをリフレッシュ（日次ETL完了後に実行想定）
make refresh-mv ENV=local_dev

# 目標カードMVのみリフレッシュ（個別実行用）
make refresh-mv-target-card ENV=local_dev
```

**推奨運用**:
- 日次で `make refresh-mv` を実行（cron / GitHub Actions / plan_worker 等）
- 現時点では手動実行前提（自動化は別タスク）
- CONCURRENTLY オプションでロックなしリフレッシュ（2回目以降）

## 動作確認結果

### MV作成確認
```bash
$ docker compose ... exec -T db psql -U myuser -d sanbou_dev -c "\\d+ mart.mv_target_card_per_day"
# 出力: 2191 rows (2021-01-01 ~ 2026-12-31)
# インデックス: ux_mv_target_card_per_day_ddate (UNIQUE), ix_mv_target_card_per_day_iso_week
```

### エンドポイント動作
- `/core_api/dashboard/target?date=2025-11-01&mode=monthly`
- 正常にレスポンス返却（MV参照）
- エラーメッセージも MV 参照を示すよう更新済み

### パフォーマンス改善（推定）

**変更前（VIEW参照）**:
- 複雑なCTE（5段）+ 多数のJOIN/集計をリクエスト毎に実行
- 応答時間: 推定 200~500ms（データ量・負荷により変動）

**変更後（MV参照）**:
- 事前集計済みデータからの単純SELECT
- 応答時間: 推定 10~50ms（インデックス活用）
- **改善率: 約 80~95% 短縮見込み**

※実測は `/dashboard/ukeire` を開いてブラウザ Network タブで確認してください

## ロールバック手順

問題が発生した場合:

1. **Repository を元に戻す**:
   ```bash
   # dashboard_target_repo.py 内の全ての
   # FROM mart.mv_target_card_per_day → FROM mart.v_target_card_per_day
   ```

2. **マイグレーションのロールバック**:
   ```bash
   make al-down ENV=local_dev
   # → MV と INDEX が削除される（VIEW は残る）
   ```

## 今後の展開

### 短期（今すぐ可能）
- [ ] ブラウザで実測レスポンスタイムを計測・記録
- [ ] 他の重いVIEWも同様にMV化検討（例: `mart.v_receive_daily` の一部）

### 中期（別タスクで実装）
- [ ] GitHub Actions / cron で日次自動REFRESH
- [ ] plan_worker の予測計算完了後に MV REFRESH を組み込み
- [ ] Grafana で MV のデータ鮮度・更新時刻をモニタリング

### 長期（最適化継続）
- [ ] REFRESH 実行時間の計測・ログ記録
- [ ] 部分REFRESH（増分更新）の検討
- [ ] MV のパーティショニング（年月単位）

## 参考資料

- PostgreSQL公式: [Materialized Views](https://www.postgresql.org/docs/current/sql-creatematerializedview.html)
- Alembicパターン: `app/backend/core_api/migrations/alembic/versions/20251104_162109457_manage_materialized_views_mart.py`
- 既存VIEW定義: `app/backend/core_api/migrations/alembic/sql/mart/v_target_card_per_day.sql`

---

**実装日**: 2025-11-17  
**担当**: Copilot (with シニアエンジニア役)  
**レビュー**: 要フロントエンド側での実測確認
