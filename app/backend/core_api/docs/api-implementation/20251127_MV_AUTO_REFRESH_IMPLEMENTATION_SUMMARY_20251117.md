# 受入CSV成功時マテビュー自動更新機能 - 実装サマリー

**実装日**: 2025-11-17  
**目的**: 受入CSV（receive）のアップロードが成功したタイミングで、PostgreSQL のマテリアライズドビュー `mart.mv_target_card_per_day` を自動更新する

---

## 📝 実装概要

### 設計方針

- **Clean Architecture & SOLID 原則**に従った実装
- **単一責任の原則（SRP）**: マテビュー更新は専用クラスに分離
- **疎結合**: 既存コードへの影響を最小限に抑える
- **拡張性**: 他の csv_type にも容易に対応可能
- **テスタビリティ**: モックでテスト可能な構造

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│  Presentation Layer (Router)                            │
│  - database/router.py                                   │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Application Layer (UseCase)                            │
│  - upload_syogun_csv_uc.py                             │
│    - execute()                                          │
│    - _update_upload_logs() ★ MV更新呼び出し           │
│    - _refresh_materialized_views() ★ 新規追加         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Infrastructure Layer (Repository)                      │
│  - materialized_view_refresher.py ★ 新規作成          │
│    - refresh_for_csv_type()                            │
│    - _refresh_single_mv()                              │
└─────────────────────────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │   PostgreSQL  │
         │   Database    │
         └───────────────┘
```

---

## 📂 変更・追加ファイル

### 1. 新規作成ファイル

#### ① `app/backend/core_api/app/infra/adapters/materialized_view/materialized_view_refresher.py`
**責務**: マテリアライズドビュー更新専用リポジトリ

**主要メソッド**:
- `refresh_for_csv_type(csv_type: str)`: 指定csv_typeに関連するMVを更新
- `_refresh_single_mv(mv_name: str)`: 単一MVの更新（REFRESH MATERIALIZED VIEW CONCURRENTLY実行）
- `refresh_all_receive_mvs()`: 受入関連MVを一括更新
- `list_available_mvs(csv_type: Optional[str])`: 利用可能なMVリスト取得

**設計ポイント**:
- `MV_MAPPINGS` で csv_type と MV の関連を定義（拡張容易）
- CONCURRENTLY オプションでロック最小化
- エラーログ記録、例外は呼び出し側で処理

#### ② `app/backend/core_api/app/infra/adapters/materialized_view/__init__.py`
パッケージ初期化ファイル（import 簡略化用）

#### ③ `docs/MV_AUTO_REFRESH_ON_UPLOAD_MANUAL_TEST.md`
手動テスト手順とトラブルシューティングガイド

#### ④ `app/backend/core_api/tests/test_mv_refresh.py`
ユニットテスト（MaterializedViewRefresher と UseCase のインテグレーションテスト）

---

### 2. 変更ファイル

#### ① `app/backend/core_api/app/application/usecases/upload/upload_syogun_csv_uc.py`

**変更内容**:

**a. import追加**:
```python
from typing import Dict, Optional, List  # List を追加
from app.infra.adapters.materialized_view.materialized_view_refresher import MaterializedViewRefresher
```

**b. コンストラクタに `mv_refresher` を追加**:
```python
def __init__(
    self,
    raw_writer: IShogunCsvWriter,
    stg_writer: IShogunCsvWriter,
    csv_config: SyogunCsvConfigLoader,
    validator: CSVValidationResponder,
    raw_data_repo: Optional[RawDataRepository] = None,
    mv_refresher: Optional[MaterializedViewRefresher] = None,  # ★ 追加
):
    # ...
    self.mv_refresher = mv_refresher
```

**c. `_update_upload_logs()` メソッドの拡張**:
- 成功した csv_type を記録
- メソッド末尾で `_refresh_materialized_views()` を呼び出し

**d. `_refresh_materialized_views()` メソッドの追加**:
```python
def _refresh_materialized_views(self, csv_types: List[str]) -> None:
    """
    指定されたcsv_typeに関連するマテリアライズドビューを更新
    
    Note:
        - エラーが発生してもアップロード処理全体は失敗させない
        - ログに記録して処理を継続
    """
    # mv_refresher が注入されていない場合はスキップ
    if not self.mv_refresher:
        logger.debug("MaterializedViewRefresher not injected, skipping MV refresh")
        return
    
    for csv_type in csv_types:
        try:
            self.mv_refresher.refresh_for_csv_type(csv_type)
        except Exception as e:
            # エラーログ記録のみ、アップロード処理には影響させない
            logger.error(f"Failed to refresh materialized views for csv_type='{csv_type}': {e}")
```

**設計ポイント**:
- `mv_refresher` は Optional → DI されていない場合も動作
- エラー時もアップロード処理は成功扱い（MVはベストエフォート）
- csv_type ごとにループ処理（将来的に複数同時対応）

---

#### ② `app/backend/core_api/app/config/di_providers.py`

**変更内容**:

**a. import追加**:
```python
from app.infra.adapters.materialized_view.materialized_view_refresher import MaterializedViewRefresher
```

**b. `get_mv_refresher()` プロバイダ追加**:
```python
def get_mv_refresher(db: Session = Depends(get_db)) -> MaterializedViewRefresher:
    """
    MaterializedViewRefresher提供
    
    マテリアライズドビュー更新専用リポジトリ。
    CSVアップロード成功時にMVを自動更新するために使用。
    """
    return MaterializedViewRefresher(db)
```

**c. 全 UseCase ファクトリに `mv_refresher` を注入**:
- `get_uc_default()`
- `get_uc_flash()`
- `get_uc_stg_final()`

それぞれに以下を追加:
```python
mv_refresher: MaterializedViewRefresher = Depends(get_mv_refresher)
```

そして、UseCaseインスタンス化時に渡す:
```python
return UploadSyogunCsvUseCase(
    raw_writer=raw_repo,
    stg_writer=stg_repo,
    csv_config=_csv_config,
    validator=_validator,
    raw_data_repo=raw_data_repo,
    mv_refresher=mv_refresher,  # ★ 追加
)
```

**設計ポイント**:
- FastAPI の Depends パターンで DI 実現
- 既存の DI 設定と統一的なスタイル
- テスト時はモックに置き換え可能

---

## 🔄 処理フロー

### 正常系（受入CSV成功時）

```
1. ユーザーが受入CSVをアップロード
   ↓
2. UploadSyogunCsvUseCase.execute()
   - CSVバリデーション
   - raw層保存
   - stg層保存
   ↓
3. _update_upload_logs()
   - csv_type='receive', processing_status='success' を log.upload_file に記録
   - 成功した csv_type を収集: ['receive']
   ↓
4. _refresh_materialized_views(['receive'])
   - mv_refresher.refresh_for_csv_type('receive') を呼び出し
   ↓
5. MaterializedViewRefresher.refresh_for_csv_type('receive')
   - MV_MAPPINGS から対応MV取得: ['mart.mv_target_card_per_day']
   ↓
6. _refresh_single_mv('mart.mv_target_card_per_day')
   - SQL実行: REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_target_card_per_day;
   - commit
   ↓
7. ログ出力: "Successfully refreshed materialized view: mart.mv_target_card_per_day"
   ↓
8. ユーザーに成功レスポンス返却
```

### 異常系（MV更新失敗）

```
1-5. （正常系と同じ）
   ↓
6. _refresh_single_mv() でエラー発生
   - rollback
   - ERROR ログ出力
   - 例外を raise
   ↓
7. _refresh_materialized_views() で例外をキャッチ
   - ERROR ログ記録
   - アップロード処理は継続（失敗させない）
   ↓
8. ユーザーには「アップロード成功」を返却
   （MVエラーは内部で処理済み）
```

---

## 🎯 判定ロジック

### MV更新が実行される条件

```python
# _update_upload_logs() 内の判定
if csv_type == 'receive' and processing_status == 'success':
    mv_refresh_needed.append('receive')
```

**必須条件**:
1. `csv_type` が `'receive'`
2. `processing_status` が `'success'`
3. `mv_refresher` が DI されている（Optional だが通常は注入される）

### MV更新が実行されない条件

- `csv_type` が `'yard'` または `'shipment'`（現在MVが未定義）
- `processing_status` が `'failed'` または `'pending'`
- `mv_refresher` が `None`（DI されていない場合）
- アップロード処理自体が途中で失敗した場合

---

## 🧪 テスト

### ユニットテスト

**ファイル**: `app/backend/core_api/tests/test_mv_refresh.py`

**テストケース**:
1. `MaterializedViewRefresher` の初期化
2. MV一覧取得（全体、csv_type指定、未定義型）
3. 単一MV更新（成功、失敗）
4. csv_type指定でのMV更新
5. UseCase統合テスト（モック版）
   - 受入成功時にMV更新呼び出し
   - 失敗時に呼び出されない
   - MVエラーでもアップロード処理は継続

**実行方法**:
```bash
cd /home/koujiro/work_env/22.Work_React/sanbou_app/app/backend/core_api
pytest tests/test_mv_refresh.py -v
```

### 手動テスト

**手順書**: `docs/MV_AUTO_REFRESH_ON_UPLOAD_MANUAL_TEST.md`

**主要ステップ**:
1. マテビューの初期状態確認
2. 受入CSVアップロード
3. ログでMV更新確認
4. マテビュー更新確認
5. upload_file テーブル確認

---

## 📊 拡張性

### 新しい csv_type に MV を追加する方法

`MaterializedViewRefresher.MV_MAPPINGS` に追加するだけです。

**例: shipment 用MVを追加**

```python
MV_MAPPINGS = {
    "receive": [
        "mart.mv_target_card_per_day",
    ],
    "shipment": [
        "mart.mv_shipment_summary",  # ★ 新規追加
    ],
    "yard": [
        # 将来追加
    ],
}
```

**手順**:
1. 新しいマテリアライズドビューを作成（Alembic migration）
2. `MV_MAPPINGS` に追加
3. テスト実行
4. デプロイ

**コード変更不要な箇所**:
- UseCase（`upload_syogun_csv_uc.py`）
- DI設定（`di_providers.py`）
- Router（`database/router.py`）

→ 完全に疎結合な設計を実現

---

### 新しい MV を receive に追加する方法

```python
MV_MAPPINGS = {
    "receive": [
        "mart.mv_target_card_per_day",
        "mart.mv_receive_monthly_summary",  # ★ 追加
    ],
    # ...
}
```

`refresh_for_csv_type('receive')` 実行時に自動的に両方更新されます。

---

## 🚀 今後の改善案

### 短期（すぐ実装可能）

1. **パフォーマンス計測**
   - MV更新にかかる時間をログに記録
   - アップロードAPIのレスポンスタイムへの影響を測定

2. **他の csv_type への対応**
   - shipment 用 MV の作成と登録
   - yard 用 MV の作成と登録

### 中期（別タスクで実装）

1. **非同期実行**
   - Celery / RQ などのバックグラウンドジョブで MV 更新
   - アップロードAPIのレスポンスタイム短縮

2. **スケジューリング**
   - GitHub Actions / cron で日次自動 REFRESH
   - ETL完了後の自動実行組み込み（plan_worker 連携）

3. **モニタリング**
   - Grafana でMVのデータ鮮度・更新時刻を可視化
   - 更新失敗時のアラート設定

### 長期（最適化継続）

1. **部分REFRESH（増分更新）**
   - 全データではなく差分のみ更新
   - パフォーマンス大幅改善

2. **MVのパーティショニング**
   - 年月単位でパーティション分割
   - 更新対象を絞ってさらに高速化

3. **複数MVの並列更新**
   - asyncio / ThreadPoolExecutor で並列実行
   - 複数MVがある場合の高速化

---

## 📚 参考資料

### 実装ファイル

| ファイル | 役割 |
|---------|------|
| `app/infra/adapters/materialized_view/materialized_view_refresher.py` | MV更新専用リポジトリ |
| `app/application/usecases/upload/upload_syogun_csv_uc.py` | CSV アップロード UseCase |
| `app/config/di_providers.py` | DI設定 |
| `migrations/alembic/versions/20251117_135913797_create_mv_target_card_per_day.py` | MV作成マイグレーション |
| `migrations/alembic/sql/mart/mv_target_card_per_day.sql` | MV定義SQL |
| `tests/test_mv_refresh.py` | ユニットテスト |

### ドキュメント

| ドキュメント | 内容 |
|------------|------|
| `docs/MV_AUTO_REFRESH_ON_UPLOAD_MANUAL_TEST.md` | 手動テスト手順 |
| `docs/MV_TARGET_CARD_IMPLEMENTATION_20251117.md` | MV作成時の実装レポート |
| `makefile` | MV手動更新コマンド（`make refresh-mv-target-card`） |

### PostgreSQL公式

- [Materialized Views](https://www.postgresql.org/docs/current/sql-creatematerializedview.html)
- [REFRESH MATERIALIZED VIEW](https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html)

---

## ✅ チェックリスト

- [x] MaterializedViewRefresher 実装
- [x] UploadSyogunCsvUseCase への統合
- [x] DI設定追加
- [x] ユニットテスト作成
- [x] 手動テスト手順書作成
- [x] 実装サマリー作成
- [ ] 手動テスト実施（local_dev環境）
- [ ] フロントエンドでのレスポンスタイム実測
- [ ] 本番環境デプロイ前の負荷テスト

---

**実装完了日**: 2025-11-17  
**実装者**: GitHub Copilot (Senior Backend Engineer role)  
**レビュー**: 要人間レビュー
