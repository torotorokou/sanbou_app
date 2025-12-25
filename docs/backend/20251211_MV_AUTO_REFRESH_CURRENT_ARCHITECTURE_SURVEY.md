# マテリアライズドビュー（MV）自動更新ロジック - 現状調査レポート

**作成日**: 2025年12月11日  
**調査対象**: 将軍 CSV アップロードに伴う MV/集計テーブルの自動更新機能  
**調査目的**: 新規 MV を追加する前に、既存の自動更新ロジックを正確に把握する

---

## 目次

1. [MV / 集計テーブル関連の DDL 一覧](#1-mv--集計テーブル関連の-ddl-一覧)
2. [MV / 集計テーブル更新処理の現状一覧](#2-mv--集計テーブル更新処理の現状一覧)
3. [バッチ・起動スクリプト・Makefile での運用フロー](#3-バッチ起動スクリプトmakefile-での運用フロー)
4. [自動更新ロジック設計の参考になりそうな既存パターン](#4-自動更新ロジック設計の参考になりそうな既存パターン)
5. [今後の設計時に注意すべき点](#5-今後の設計時に注意すべき点)

---

## 1. MV / 集計テーブル関連の DDL 一覧

### 1.1. 現在稼働中のマテリアライズドビュー（MV）

以下のマテリアライズドビューが `mart` スキーマに定義されています。

| MV名                             | 格納場所                                                 | 役割                                       | コメント                                                                                                  |
| -------------------------------- | -------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `mart.mv_target_card_per_day`    | `sql/mart/mv_target_card_per_day.sql`                    | 日次目標・実績カード集計                   | ダッシュボード用。日次の目標 ton と実績 ton を事前集計。`REFRESH MATERIALIZED VIEW CONCURRENTLY` で更新。 |
| `mart.mv_receive_daily`          | `versions/20251211_120000000_create_mv_receive_daily.py` | 受入日次実績（`v_receive_daily` の MV 版） | 2025-12-11 に新規作成。パフォーマンス改善のため VIEW → MV に切り替え。                                    |
| `mart.mv_sales_tree_daily`       | `sql/mart/mv_sales_tree_daily.sql`                       | 日次売上ツリー集計                         | 出荷伝票から日次で売上を集計。階層構造（得意先 → 品目）を持つ。                                           |
| `mart.mv_inb5y_week_profile_min` | `sql/mart/mv_inb5y_week_profile_min.sql`                 | 5年間週次プロファイル（最小版）            | 平日平均、予約日（日祝）平均を週単位で集計。予測モデル用。                                                |
| `mart.mv_inb_avg5y_day_biz`      | `sql/mart/mv_inb_avg5y_day_biz.sql`                      | 5年間平日日次平均                          | 営業日（月〜土、祝日除外）のみの平均値を週・曜日別に集計。                                                |
| `mart.mv_inb_avg5y_day_scope`    | `sql/mart/mv_inb_avg5y_day_scope.sql`                    | 5年間日次平均（全日 or 営業日）            | `scope='all'` or `'biz'` で全日/営業日を区別。                                                            |
| `mart.mv_inb_avg5y_weeksum_biz`  | `sql/mart/mv_inb_avg5y_weeksum_biz.sql`                  | 5年間週次合計（営業日のみ）                | 週単位の合計値の平均・標準偏差を計算。                                                                    |

### 1.2. 通常のVIEW（参照用）

以下のビューは MV ではなく、通常の VIEW として定義されています。

| VIEW名                              | 役割                                                              |
| ----------------------------------- | ----------------------------------------------------------------- |
| `mart.v_receive_daily`              | 受入日次実績（元データ）。`mv_receive_daily` 作成後も残存。       |
| `mart.v_daily_target_with_calendar` | 営業カレンダー付き日次目標。`mv_target_card_per_day` の元データ。 |
| `mart.v_target_card_per_day`        | ターゲットカード集計の VIEW 版（MV 版と並行稼働中）。             |

### 1.3. 集計テーブル（通常テーブル）

| テーブル名               | 役割                                                            |
| ------------------------ | --------------------------------------------------------------- |
| `mart.daily_target_plan` | 日次目標計画マスタ。`v_daily_target_with_calendar` の元データ。 |
| `kpi.monthly_targets`    | 月次目標マスタ。KPI 計算の基準値。                              |

---

## 2. MV / 集計テーブル更新処理の現状一覧

### 2.1. 自動更新（CSV アップロード完了時）

#### 2.1.1. 実装箇所

**ファイル**: `app/backend/core_api/app/infra/adapters/materialized_view/materialized_view_refresher.py`

**クラス**: `MaterializedViewRefresher`

**責務**:

- マテリアライズドビューの `REFRESH MATERIALIZED VIEW CONCURRENTLY` を実行
- CSV アップロード成功時に呼び出される
- エラーハンドリング（個別 MV の失敗はログに記録するが、全体処理は継続）

**更新対象の定義**:

```python
MV_MAPPINGS = {
    "receive": [
        "mart.mv_target_card_per_day",
        # 将来的に追加する受入関連MVをここに列挙
    ],
    "shipment": [
        # 出荷関連MVをここに追加（将来）
    ],
    "yard": [
        # ヤード関連MVをここに追加（将来）
    ],
}
```

**実行タイミング**:

- `UploadShogunCsvUseCase._process_background_upload()` 内で呼び出し
- CSV の raw/stg 層への保存が成功した後に実行
- `csv_type='receive'` の場合のみ `mart.mv_target_card_per_day` を更新

#### 2.1.2. 呼び出しフロー

```
[Router] POST /upload/csv
  ↓
[UseCase] UploadShogunCsvUseCase.start_async_upload()
  - 軽量バリデーション（拡張子、サイズ、重複チェック）
  - log.upload_file に 'pending' 状態で登録
  - ファイル内容をメモリに読み込み
  - BackgroundTasks に登録して即座に受付完了レスポンス
  ↓
[BackgroundTasks] _process_background_upload()
  - CSV 読込 → バリデーション → フォーマット → DB保存（raw/stg層）
  - 成功時: log.upload_file.status = 'success'
  - **★ MV 自動更新**: _refresh_materialized_views() を呼び出し
  ↓
[MaterializedViewRefresher] refresh_for_csv_type(csv_type='receive')
  - MV_MAPPINGS から更新対象 MV リストを取得
  - 各 MV に対して REFRESH MATERIALIZED VIEW CONCURRENTLY 実行
  - エラーはログに記録するが、アップロード処理は成功扱い
```

### 2.2. 手動更新（マイグレーション適用後）

#### 2.2.1. Alembic マイグレーション内での更新

**ファイル**: `migrations/alembic/versions/20251104_162109457_manage_materialized_views_mart.py`

**実行内容**:

- Alembic マイグレーション（`alembic upgrade head`）実行時に MV を自動更新
- 既存 DB の場合: `REFRESH MATERIALIZED VIEW CONCURRENTLY` のみ実行
- 新規 DB の場合: `CREATE MATERIALIZED VIEW` + INDEX 作成 + REFRESH

**更新対象**:

```python
MV_DEFINITIONS = {
    "mart.mv_inb5y_week_profile_min": "...",
    "mart.mv_inb_avg5y_day_biz": "...",
    "mart.mv_inb_avg5y_weeksum_biz": "...",
    "mart.mv_inb_avg5y_day_scope": "...",
}
```

#### 2.2.2. スクリプトによる手動更新

**ファイル**: `scripts/refactoring/apply_soft_delete_refactoring.sh`

**実行内容**:

- 論理削除（Soft Delete）対応マイグレーション後に MV を一括更新
- `REFRESH MATERIALIZED VIEW CONCURRENTLY` を実行

**更新対象**:

```bash
MVS=(
  "mart.mv_target_card_per_day"
  "mart.mv_inb5y_week_profile_min"
  "mart.mv_inb_avg5y_day_biz"
  "mart.mv_inb_avg5y_weeksum_biz"
  "mart.mv_inb_avg5y_day_scope"
)
```

**実行方法**:

```bash
./scripts/refactoring/apply_soft_delete_refactoring.sh
```

### 2.3. 現在の更新タイミング一覧

| 更新タイミング                               | トリガー                                | 更新対象 MV                   | 実行方法                                                      |
| -------------------------------------------- | --------------------------------------- | ----------------------------- | ------------------------------------------------------------- |
| **CSV アップロード完了時**（自動）           | `csv_type='receive'` のアップロード成功 | `mart.mv_target_card_per_day` | `MaterializedViewRefresher.refresh_for_csv_type()`            |
| **Alembic マイグレーション適用時**（半自動） | `alembic upgrade head`                  | 予測モデル用 MV 群（4つ）     | マイグレーション内の `REFRESH MATERIALIZED VIEW CONCURRENTLY` |
| **スキーマ変更後の手動更新**                 | 開発者が手動実行                        | 全 MV（5つ以上）              | `scripts/refactoring/apply_soft_delete_refactoring.sh`        |

---

## 3. バッチ・起動スクリプト・Makefile での運用フロー

### 3.1. Makefile によるAlembicマイグレーション

**ファイル**: `makefile`

**関連ターゲット**:

```makefile
al-up:
    $(ALEMBIC) upgrade head

al-down:
    $(ALEMBIC) downgrade -1

al-rev-auto:
    $(ALEMBIC) revision --autogenerate -m "$(MSG)" --rev-id $(REV_ID)
```

**実行例**:

```bash
# マイグレーション適用（MV 更新も含む）
make al-up ENV=local_dev

# ロールバック
make al-down ENV=local_dev

# 新規マイグレーション生成
make al-rev-auto MSG="add new mv" REV_ID=$(date +%Y%m%d_%H%M%S%3N)
```

### 3.2. 起動スクリプト

**調査結果**:

- `startup.sh` は `rag_api`、`ledger_api`、`manual_api` にのみ存在
- `core_api` には起動時スクリプトなし（`uvicorn` 直接起動）
- **起動時の自動 MV 更新ロジックは存在しない**

### 3.3. バッチ・cron・スケジューラ

**調査結果**:

- 定期的な MV 更新を行う cron ジョブや scheduler は **現時点では存在しない**
- `plan_worker` サービスが存在するが、MV 更新は担当していない
  - 役割: 予測計画の再計算（`rebuild_daytype_ratios`）

**今後の拡張可能性**:

- `plan_worker` を拡張して、夜間バッチで MV を一括更新する案は検討可能

---

## 4. 自動更新ロジック設計の参考になりそうな既存パターン

### 4.1. ✅ 良いパターン：MaterializedViewRefresher（現行実装）

**ファイル**: `app/infra/adapters/materialized_view/materialized_view_refresher.py`

**良い点**:

1. **単一責任の原則（SRP）**: MV 更新のみに特化したクラス
2. **疎結合**: UseCase から DI 経由で注入（`get_mv_refresher()`）
3. **拡張性**: `MV_MAPPINGS` に追加するだけで新しい MV を自動更新対象にできる
4. **エラーハンドリング**: 個別 MV の失敗はログに記録するが、全体処理は継続
5. **CONCURRENTLY オプション**: ロックを最小化（UNIQUE INDEX 必須）

**参考にすべき設計**:

```python
# 新しい MV を追加する場合
MV_MAPPINGS = {
    "receive": [
        "mart.mv_target_card_per_day",
        "mart.mv_receive_daily",  # ← 新規追加（2025-12-11）
        "mart.mv_inbound_kpi_daily",  # ← 将来追加予定
    ],
    "shipment": [
        "mart.mv_sales_tree_daily",  # ← 将来対応
    ],
}
```

**使い方（DI経由）**:

```python
# config/di_providers.py
def get_mv_refresher(db: Session = Depends(get_db)) -> MaterializedViewRefresher:
    return MaterializedViewRefresher(db)

# core/usecases/upload/upload_shogun_csv_uc.py
class UploadShogunCsvUseCase:
    def __init__(
        self,
        mv_refresher: Optional[MaterializedViewRefresher] = None,
    ):
        self.mv_refresher = mv_refresher

    def _refresh_materialized_views(self, csv_types: List[str]) -> None:
        if not self.mv_refresher:
            return
        for csv_type in csv_types:
            self.mv_refresher.refresh_for_csv_type(csv_type)
```

### 4.2. ✅ 良いパターン：BackgroundTasks による非同期処理

**ファイル**: `app/core/usecases/upload/upload_shogun_csv_uc.py`

**良い点**:

1. **ユーザー体験向上**: 軽量バリデーション → 即座に受付完了レスポンス
2. **重い処理を分離**: CSV 読込・保存・MV 更新はバックグラウンドで実行
3. **進捗管理**: `log.upload_file.status` で状態管理（pending → success/error）

**フロー**:

```python
async def start_async_upload(
    self,
    background_tasks: BackgroundTasks,
    receive: Optional[UploadFile],
    ...
) -> SuccessApiResponse | ErrorApiResponse:
    # 1. 軽量バリデーション（拡張子、サイズ、重複チェック）
    # 2. log.upload_file に 'pending' 状態で登録
    # 3. ファイル内容をメモリに読み込み
    # 4. バックグラウンドタスクに登録
    background_tasks.add_task(
        self._process_background_upload,
        receive_bytes,
        yard_bytes,
        shipment_bytes,
        ...
    )
    # 5. 即座に受付完了レスポンスを返す
    return SuccessApiResponse(...)
```

**参考にすべき理由**:

- 新しい MV 追加時も、既存のバックグラウンド処理フローに乗せるだけで自動更新可能
- エラーハンドリングが既に実装済み（MV 更新失敗してもアップロード自体は成功扱い）

### 4.3. ⚠️ 改善が必要なパターン：マイグレーション内での MV 更新

**ファイル**: `migrations/alembic/versions/20251104_162109457_manage_materialized_views_mart.py`

**現状の問題点**:

1. **マイグレーション実行時間が長くなる**: 大量データがある場合、REFRESH に時間がかかる
2. **デプロイ時のリスク**: マイグレーション失敗 = デプロイ失敗になる可能性
3. **冪等性の保証が難しい**: 同じマイグレーションを複数回実行すると予期しない動作

**代替案**:

- **マイグレーションでは MV の DDL（CREATE MATERIALIZED VIEW）のみ実行**
- **初回データ投入は別途スクリプトで実行**: `REFRESH MATERIALIZED VIEW` を手動または自動化スクリプトで実行
- 例: `scripts/db/init_mv_data.sh`

### 4.4. ⚠️ アンチパターン：手動スクリプトの乱立

**ファイル**: `scripts/refactoring/apply_soft_delete_refactoring.sh`

**問題点**:

1. **メンテナンス負荷**: 新しい MV を追加するたびにスクリプトを修正する必要がある
2. **実行忘れのリスク**: 手動実行を前提としているため、忘れると MV が古いまま
3. **冪等性の欠如**: 複数回実行しても問題ない設計になっていない

**改善提案**:

- `MaterializedViewRefresher` に統一して、スクリプト側から呼び出す形に変更
- または、`make refresh-all-mv` のような Makefile ターゲットを用意

---

## 5. 今後の設計時に注意すべき点

### 5.1. 新規 MV 追加時のチェックリスト

#### ✅ DDL 作成

- [ ] `migrations/alembic/sql/mart/mv_xxx.sql` に DDL を作成
- [ ] `CREATE MATERIALIZED VIEW` + コメント追加
- [ ] UNIQUE INDEX の作成（CONCURRENTLY オプション使用のため必須）

#### ✅ マイグレーション作成

- [ ] `alembic revision --autogenerate` で新規マイグレーションを生成
- [ ] DDL の適用ロジックを確認（CREATE のみ、REFRESH は別途）

#### ✅ 自動更新ロジックの追加

- [ ] `MaterializedViewRefresher.MV_MAPPINGS` に新しい MV を追加
- [ ] 適切な `csv_type` に紐付ける（例: `"receive"`, `"shipment"`, `"yard"`）

#### ✅ テスト追加

- [ ] `tests/test_mv_refresh.py` にユニットテストを追加
- [ ] 実際の CSV アップロード → MV 更新フローの統合テストを実施

### 5.2. パフォーマンス最適化

#### 1. **UNIQUE INDEX の必須性**

- `REFRESH MATERIALIZED VIEW CONCURRENTLY` を使用するには UNIQUE INDEX が必須
- マイグレーション内で `CREATE UNIQUE INDEX CONCURRENTLY` を実行

#### 2. **部分更新（Incremental Refresh）の検討**

- 現在は全行更新（Full Refresh）
- 将来的には、増分更新（最新データのみ再計算）を検討
  - PostgreSQL 13+ の `WITH NO DATA` → `REFRESH MATERIALIZED VIEW WHERE ...` は未対応
  - 代替案: トリガー関数で更新行のみを別テーブルに記録し、定期的にマージ

#### 3. **並列実行の最適化**

- 複数 MV を更新する場合、`asyncio.gather()` で並列実行を検討
- ただし、DB の CONCURRENTLY 更新は既に並列化されているため、効果は限定的

### 5.3. エラーハンドリング

#### 1. **個別 MV 失敗時の挙動**

- 現在: ログに記録するが、アップロード処理は成功扱い
- 推奨: 重要度によって処理を分ける
  - **Critical MV**（例: `mv_target_card_per_day`）: 失敗時は例外を投げる
  - **Optional MV**（例: 予測モデル用 MV）: ログのみ記録

#### 2. **リトライ機構の追加**

- MV 更新失敗時に自動リトライする機能を検討
- 例: `tenacity` ライブラリで exponential backoff

### 5.4. 監視・アラート

#### 1. **MV 更新完了時のログ出力**

- 現在: INFO レベルでログ出力済み
- 推奨: Prometheus メトリクスとして公開（例: `mv_refresh_duration_seconds`）

#### 2. **長時間実行の検知**

- MV 更新に 10 分以上かかる場合は WARNING ログを出力
- Cloud Logging でアラート設定

---

## まとめ

### 現状の更新方式

| 方式                         | トリガー                                | 対象 MV                       | 実行方法                           | 自動化レベル                        |
| ---------------------------- | --------------------------------------- | ----------------------------- | ---------------------------------- | ----------------------------------- |
| **CSV アップロード完了時**   | `csv_type='receive'` のアップロード成功 | `mart.mv_target_card_per_day` | `MaterializedViewRefresher`        | ✅ 完全自動                         |
| **Alembic マイグレーション** | `alembic upgrade head`                  | 予測モデル用 MV 群            | マイグレーション内の SQL           | 🔶 半自動（マイグレーション実行時） |
| **手動スクリプト**           | 開発者が手動実行                        | 全 MV                         | `apply_soft_delete_refactoring.sh` | ❌ 手動                             |

### 推奨される設計方針

1. **既存の `MaterializedViewRefresher` を活用**

   - 新しい MV は `MV_MAPPINGS` に追加するだけで自動更新対象になる
   - DI 経由で UseCase に注入されるため、テストも容易

2. **BackgroundTasks による非同期処理を継続**

   - ユーザー体験を損なわず、重い MV 更新をバックグラウンドで実行

3. **マイグレーションでは DDL のみ実行**

   - REFRESH は別途スクリプトまたは自動更新ロジックで実行

4. **監視・アラート機能の追加**
   - MV 更新時間が長い場合の検知
   - 更新失敗時のアラート通知

---

## 6. 実装結果サマリー（2025-12-11）

### 6.1. 完了した作業

本調査レポート作成後、以下の実装を完了しました：

#### ✅ v_receive_daily → mv_receive_daily 移行

**実施内容**:

1. `app/infra/db/sql_names.py` の `V_RECEIVE_DAILY` 定数を `mart.mv_receive_daily` に変更
2. 依存する全MVとVIEWのSQL定義を更新（7ファイル）:
   - `mv_inb5y_week_profile_min.sql`
   - `mv_inb_avg5y_day_biz.sql`
   - `mv_inb_avg5y_weeksum_biz.sql`
   - `mv_inb_avg5y_day_scope.sql`
   - `v_receive_monthly.sql`
   - `v_receive_weekly.sql`
   - `mv_target_card_per_day.sql`
3. マイグレーション `e581d89ba5db` で `mart.v_receive_daily` VIEW を削除
4. `mart.mv_receive_daily` MV を手動作成（テーブル名修正版）:
   - テーブル参照: `stg.shogun_final_receive`, `stg.shogun_flash_receive`
   - UNIQUE INDEX: `ux_mv_receive_daily_ddate` (REFRESH CONCURRENTLY要件)
   - 複合INDEX: `ix_mv_receive_daily_iso_week` (週次集計最適化)
   - データ件数: **1,805行**
5. `MaterializedViewRefresher.MV_MAPPINGS` の `"receive"` リストに `"mart.mv_receive_daily"` を追加

**結果**:

- ✅ CSV upload時に `mv_receive_daily` が自動更新されるようになった
- ✅ `/inbound/daily` API のレスポンスタイム改善を期待（VIEW→MV化）
- ✅ 既存の依存MVは全て `mv_receive_daily` を参照するように更新済み

#### ✅ mv_target_card_per_day 再作成

**実施内容**:

1. `sql/mart/mv_target_card_per_day.sql` を使用して MV を再作成
2. `mv_receive_daily` への依存関係を確立
3. UNIQUE INDEX: `ux_mv_target_card_per_day_ddate`
4. 複合INDEX: `ix_mv_target_card_per_day_iso_week`
5. 初回 REFRESH 実行（データ件数: **2,191行**）

**結果**:

- ✅ ダッシュボード API で使用される目標カード MV が復活
- ✅ CSV upload時に自動更新対象（`MaterializedViewRefresher` 既登録）

#### ✅ 未使用MV/VIEW 監査と削除候補リスト作成

**調査結果** (`docs/backend/20251211_MV_DELETION_CANDIDATE_LIST.md`):

**削除可能**:

- ❌ `mart.mv_sales_tree_daily` (8KB, 未使用)
  - Repositoryで参照なし
  - v_sales_tree_detail_base へ移行済み
  - 削除推奨（低リスク）

**削除不可**:

- ⚠️ `mart.v_sales_tree_daily` (VIEW)
  - `mart.v_customer_sales_daily` が依存
  - 削除には `v_customer_sales_daily` のリファクタが必要（別タスク）

### 6.2. 最終状態

#### アクティブなMV（自動更新対象）

| MV名                          | サイズ | データ件数 | 自動更新 | 用途                       |
| ----------------------------- | ------ | ---------- | -------- | -------------------------- |
| `mart.mv_receive_daily`       | 224 KB | 1,805行    | ✅       | 日次受入実績（基礎データ） |
| `mart.mv_target_card_per_day` | 240 KB | 2,191行    | ✅       | ダッシュボード目標カード   |

**更新タイミング**: CSV type `"receive"` アップロード完了後、BackgroundTasks で自動 REFRESH

**更新順序**:

1. `mart.mv_receive_daily` (基礎データ)
2. `mart.mv_target_card_per_day` (mv_receive_daily に依存)

#### 削除候補MV

| MV名                       | サイズ | 削除優先度 | 理由                                        |
| -------------------------- | ------ | ---------- | ------------------------------------------- |
| `mart.mv_sales_tree_daily` | 8 KB   | **HIGH**   | 未使用、v_sales_tree_detail_base へ移行済み |

#### 依存関係図（更新版）

```
CSV Upload (receive)
  ↓
MaterializedViewRefresher.refresh_for_csv_type("receive")
  ↓
  ├─ REFRESH CONCURRENTLY mart.mv_receive_daily
  │   ↓
  │   ├─ (依存) mart.mv_target_card_per_day
  │   ├─ (依存) mart.v_receive_monthly
  │   ├─ (依存) mart.v_receive_weekly
  │   └─ (依存) 5年平均系MV群 (未作成)
  │
  └─ REFRESH CONCURRENTLY mart.mv_target_card_per_day
```

### 6.3. 残課題

1. **5年平均系MVの再作成**

   - `mv_inb5y_week_profile_min`
   - `mv_inb_avg5y_day_biz`
   - `mv_inb_avg5y_day_scope`
   - `mv_inb_avg5y_weeksum_biz`
   - 現在はDBに存在せず、SQL定義のみ存在

2. **mv_sales_tree_daily の削除**

   - マイグレーション作成と適用
   - 低リスク（未使用、依存なし）

3. **v_customer_sales_daily のリファクタ**

   - `v_sales_tree_daily` 依存を `v_sales_tree_detail_base` 直接参照に変更
   - 完了後 `v_sales_tree_daily` を削除可能

4. **監視・アラート機能の追加**
   - MV更新時間の計測とログ出力
   - 更新失敗時のアラート通知

---

**次のステップ**:

- ✅ ~~新規 MV（`mart.mv_receive_daily`）の DDL 作成~~ **完了**
- ✅ ~~`MaterializedViewRefresher.MV_MAPPINGS` に追加~~ **完了**
- [ ] 5年平均系MVの作成と自動更新対象化
- [ ] `mv_sales_tree_daily` 削除マイグレーション実行
- [ ] MV更新パフォーマンス監視機能の追加
