# App Directory Documentation Reorganization Complete

**日付**: 2025-12-06  
**作業者**: システム管理者  
**対象**: app配下の全サービスのdocsディレクトリ

## 📋 概要

app配下の全サービス (backend_shared, core_api, ledger_api, frontend) のdocsディレクトリを整理し、日付プレフィックス規則を統一しました。

## 🎯 実施内容

### 対象サービス

1. **backend_shared** - 共通ライブラリ
2. **core_api** - メインバックエンドAPI
3. **ledger_api** - 帳票生成API
4. **frontend** - フロントエンドアプリケーション
5. **ai_api, manual_api, plan_worker, rag_api** - その他サービス (既に整理済み)

### 日付プレフィックス修正

#### 1. backend_shared/docs (7ファイル)

**修正:**

- `tree.txt` → `20251206_tree.txt`
- `tree_final.txt` → `20251206_tree_final.txt`

**既存維持:**

- `20251128_CLEANUP_COMPLETE.md` ✓
- `20251128_ERROR_HANDLING_GUIDE.md` ✓
- `20251128_REFACTORING_REPORT.md` ✓
- `20251128_REFACTORING_SUMMARY.md` ✓
- `README.md` ✓

#### 2. core_api/docs (44ファイル + サブディレクトリ)

**トップレベル:**

- `未実装エンドポイント一覧.md` → `20251206_未実装エンドポイント一覧.md`
- `20251128_REFACTOR_COMPLETE_CLEAN_ARCHITECTURE.md` ✓
- `README.md` ✓

**api-implementation/ (6ファイル):**
重複日付プレフィックスを修正:

- `20251127_CUSTOMER_CHURN_ANALYSIS_REFACTORING_20251121.md` → `20251121_CUSTOMER_CHURN_ANALYSIS_REFACTORING.md`
- `20251127_MV_AUTO_REFRESH_IMPLEMENTATION_SUMMARY_20251117.md` → `20251117_MV_AUTO_REFRESH_IMPLEMENTATION_SUMMARY.md`
- `20251127_MV_TARGET_CARD_IMPLEMENTATION_20251117.md` → `20251117_MV_TARGET_CARD_IMPLEMENTATION.md`
- `20251127_SALES_TREE_API_IMPLEMENTATION_20251121.md` → `20251121_SALES_TREE_API_IMPLEMENTATION.md`
- `20251127_VIEW_FIX_KING_NET_WEIGHT_DETAIL_20251121.md` → `20251121_VIEW_FIX_KING_NET_WEIGHT_DETAIL.md`
- `20251127_MV_AUTO_REFRESH_ON_UPLOAD_MANUAL_TEST.md` ✓

**csv-processing/ (9ファイル):**
重複日付プレフィックスを修正:

- `20251127_CSV_ASYNC_UPLOAD_IMPLEMENTATION_20251118.md` → `20251118_CSV_ASYNC_UPLOAD_IMPLEMENTATION.md`
- `20251127_CSV_UPLOAD_EMPTY_ROW_IMPLEMENTATION_20251114.txt` → `20251114_CSV_UPLOAD_EMPTY_ROW_IMPLEMENTATION.txt`
- `20251127_CSV_UPLOAD_ERROR_ANALYSIS_20251114.md` → `20251114_CSV_UPLOAD_ERROR_ANALYSIS.md`
- `20251127_CSV_UPLOAD_ERROR_FIX_20251114.md` → `20251114_CSV_UPLOAD_ERROR_FIX.md`
- `20251127_CSV_UPLOAD_STG_COLUMN_LOSS_REPORT_20251114.md` → `20251114_CSV_UPLOAD_STG_COLUMN_LOSS_REPORT.md`
- `20251127_CSV_VALIDATION_REFACTORING_20251118.md` → `20251118_CSV_VALIDATION_REFACTORING.md`
- `20251127_IMPLEMENTATION_SUMMARY_UPLOAD_TRACKING_20251114.md` → `20251114_IMPLEMENTATION_SUMMARY_UPLOAD_TRACKING.md`
- `20251127_総括レポート_将軍CSVアップロード検証_20251114.txt` → `20251114_総括レポート_将軍CSVアップロード検証.txt`
- `20251127_SHOGUN_CSV_UPLOAD_FILE_ID_TRACKING_IMPLEMENTATION.md` ✓

**database/ (7ファイル):**
日付プレフィックス追加:

- `README_migrations.md` → `20251206_README_migrations.md`

既に修正済み:

- `20251126_ALEMBIC_SQL_REFERENCE_SURVEY.md` ✓
- `20251127_BACKEND_FIELD_NAME_DICTIONARY.md` ✓
- `20251127_CUSTOMER_LIST_DB_DESIGN.txt` ✓
- `20251127_DATABASE_COLUMN_DICTIONARY.md` ✓
- `20251127_DB_UPGRADE_POSTGRES_15_TO_17.md` ✓
- `20251127_db_migration_policy.md` ✓

**legacy/ (6ファイル):**
バックアップファイルに日付追加:

- `.dockerignore copy` → `20251206_dockerignore.bak`
- `Dockerfile.bak.20251030_093302` → `20251030_Dockerfile.bak`

既存維持:

- `20251006_IMPLEMENTATION_COMPLETE.md` ✓
- `20251027_CSV_UPLOAD_IMPLEMENTATION.md` ✓
- `20251027_YAML_FIRST_ARCHITECTURE.md` ✓
- `20251126_REPOSITORY_NAMING_CONVENTION.md` ✓

**refactoring/ (6ファイル):**
重複日付プレフィックスを修正:

- `20251127_COLUMN_CLEANUP_STEP1_REPORT_20251114.md` → `20251114_COLUMN_CLEANUP_STEP1_REPORT.md`
- `20251127_COLUMN_CLEANUP_STEP2_REPORT_20251114.md` → `20251114_COLUMN_CLEANUP_STEP2_REPORT.md`
- `20251127_COLUMN_CLEANUP_STEP3_REPORT_20251114.md` → `20251114_COLUMN_CLEANUP_STEP3_REPORT.md`
- `20251127_COLUMN_CLEANUP_STEP4_REPORT_20251114.md` → `20251114_COLUMN_CLEANUP_STEP4_REPORT.md`
- `20251127_COLUMN_CLEANUP_STEP5_REPORT_20251114.md` → `20251114_COLUMN_CLEANUP_STEP5_REPORT.md`
- `20251127_SQL_EXTRACTION_REFACTORING_20251117.md` → `20251117_SQL_EXTRACTION_REFACTORING.md`

**reports/ (3ファイル):**
重複日付プレフィックスを修正:

- `20251127_RAW_DATA_SAVE_FAILURE_ANALYSIS_20251114.md` → `20251114_RAW_DATA_SAVE_FAILURE_ANALYSIS.md`
- `20251127_RAW_SHOGUN_FLASH_EMPTY_ANALYSIS_20251114.md` → `20251114_RAW_SHOGUN_FLASH_EMPTY_ANALYSIS.md`
- `20251127_RAW_SHOGUN_FLASH_FIX_COMPLETE_20251114.md` → `20251114_RAW_SHOGUN_FLASH_FIX_COMPLETE.md`

**soft-delete/ (4ファイル):**
重複日付プレフィックスを修正:

- `20251127_BUG_FIX_SOFT_DELETE_20251119.md` → `20251119_BUG_FIX_SOFT_DELETE.md`
- `20251127_SOFT_DELETE_REFACTORING_20251120.md` → `20251120_SOFT_DELETE_REFACTORING.md`

既存維持:

- `20251127_SOFT_DELETE_IMPLEMENTATION_SUMMARY.md` ✓
- `20251127_SOFT_DELETE_QUICKSTART.md` ✓

#### 3. ledger_api/docs (13ファイル + サブディレクトリ)

**トップレベル:**

- `Dockerfile.bak.20251030_093302` → `20251030_Dockerfile.bak`
- `README.md` ✓

**architecture/ (1ファイル):**

- `20250908_ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` ✓

**migration/ (6ファイル):**
すべて既に正しい形式:

- `20251002_COMPLETE_MIGRATION_SUMMARY.md` ✓
- `20251002_DOCKERFILE_MIGRATION_REPORT.md` ✓
- `20251002_FINAL_MIGRATION_REPORT.md` ✓
- `20251002_LEDGER_MIGRATION_NOTES.md` ✓
- `20251002_ST_APP_DELETION_CHECKLIST.md` ✓
- `20251002_ST_APP_MIGRATION_REPORT.md` ✓

**refactoring/ (6ファイル):**
すべて既に正しい形式:

- `20250908_API_REFACTORING_GUIDE.md` ✓
- `20251002_REFACTORING_FINAL.md` ✓
- `20251002_REFACTORING_SERVICES.md` ✓
- `20251002_REFACTORING_SUMMARY.md` ✓
- `20251126_REFACTORING_ASSESSMENT_REPORT.md` ✓
- `20251126_REFACTORING_ROADMAP.md` ✓

#### 4. frontend/docs (29ファイル + サブディレクトリ)

**トップレベル:**
既に正しい形式:

- `20251006_notifications.md` ✓
- `20251127_FRONTEND_TYPESCRIPT_FIELD_DICTIONARY.md` ✓
- `README.md` ✓

**architecture/ (7ファイル):**
すべて既に正しい形式:

- `20250908_api-best-practices.md` ✓
- `20250911_RESPONSIVE_GUIDE.md` ✓
- `20250919_frontend-architecture.md` ✓
- `20251003_ARCHITECTURE.md` ✓
- `20251006_FSD_DEPENDENCY_RULES_SUMMARY.md` ✓
- `20251006_fsd-linting-rules.md` ✓
- `20251127_FSD_ARCHITECTURE_GUIDE.md` ✓

**legacy/ (1ファイル):**

- `20251003_notifications-old.md` ✓

**migration/ (10ファイル):**
すべて既に正しい形式:

- `20251003_IMPORT_REPLACEMENT_PLAN.md` ✓
- `20251003_MIGRATION_PLAN.md` ✓
- `20251003_MIGRATION_STATUS.md` ✓
- `20251003_PHASE2_COMPLETION_REPORT.md` ✓
- `20251003_PHASE3_COMPLETION_REPORT.md` ✓
- `20251003_PHASE3_EXECUTION_PLAN.md` ✓
- `20251003_PHASE3_SIMPLIFIED.md` ✓
- `20251003_PHASE4_KICKOFF.md` ✓
- `20251003_PHASE4_STEP3-1_COMPLETION.md` ✓
- `20251127_FSD_MIGRATION_GUIDE.md` ✓

**refactoring/ (6ファイル):**
重複日付プレフィックスを修正:

- `20251127_FSD_MVVM_REPOSITORY_COMPLETE_20251121.md` → `20251121_FSD_MVVM_REPOSITORY_COMPLETE.md`
- `20251127_SUB_FEATURE_SPLIT_COMPLETE_20251121.md` → `20251121_SUB_FEATURE_SPLIT_COMPLETE.md`

既存維持:

- `20251006_CIRCULAR_DEPENDENCY_RESULTS.md` ✓
- `20251006_circular-dependency-check.md` ✓
- `20251120_FSD_REFACTORING_SUMMARY.md` ✓
- `20251127_FSD_REFACTORING_COMPLETE_REPORT.md` ✓

## 📊 統計

### サービス別ファイル数

| サービス       | ファイル数 | サブディレクトリ | 修正数 |
| -------------- | ---------- | ---------------- | ------ |
| backend_shared | 7          | 0                | 2      |
| core_api       | 44         | 7                | 28     |
| ledger_api     | 13         | 3                | 1      |
| frontend       | 29         | 4                | 2      |
| **合計**       | **93**     | **14**           | **33** |

### 修正種別

| 種別                     | 件数   | 説明                                       |
| ------------------------ | ------ | ------------------------------------------ |
| 重複日付修正             | 28     | `20251127_*_20251114.md` → `20251114_*.md` |
| 日付プレフィックス追加   | 3      | `*.md` → `20251206_*.md`                   |
| バックアップファイル修正 | 2      | `*.bak.*` → `20251030_*.bak`               |
| **合計**                 | **33** |                                            |

## 📁 最終ディレクトリ構造

### backend_shared/docs

```
backend_shared/docs/
├── README.md
├── 20251128_CLEANUP_COMPLETE.md
├── 20251128_ERROR_HANDLING_GUIDE.md
├── 20251128_REFACTORING_REPORT.md
├── 20251128_REFACTORING_SUMMARY.md
├── 20251206_tree.txt
└── 20251206_tree_final.txt
```

### core_api/docs

```
core_api/docs/
├── README.md
├── 20251128_REFACTOR_COMPLETE_CLEAN_ARCHITECTURE.md
├── 20251206_未実装エンドポイント一覧.md
├── api-implementation/      (6 files, 20251117-20251127)
├── csv-processing/          (9 files, 20251114-20251127)
├── database/                (7 files, 20251126-20251206)
├── legacy/                  (6 files, 20251006-20251206)
├── refactoring/             (6 files, 20251114-20251117)
├── reports/                 (3 files, 20251114)
└── soft-delete/             (4 files, 20251119-20251127)
```

### ledger_api/docs

```
ledger_api/docs/
├── README.md
├── 20251030_Dockerfile.bak
├── architecture/            (1 file, 20250908)
├── migration/               (6 files, 20251002)
└── refactoring/             (6 files, 20250908-20251126)
```

### frontend/docs

```
frontend/docs/
├── README.md
├── 20251006_notifications.md
├── 20251127_FRONTEND_TYPESCRIPT_FIELD_DICTIONARY.md
├── architecture/            (7 files, 20250908-20251127)
├── legacy/                  (1 file, 20251003)
├── migration/               (10 files, 20251003-20251127)
└── refactoring/             (6 files, 20251006-20251127)
```

## ✅ 検証

### 命名規則チェック

```bash
# app配下の全docsディレクトリで日付なしファイルを検索
find app/*/docs -name "*.md" ! -name "20??????_*.md" ! -name "README.md" -type f
# → 結果: なし (README.md以外すべて準拠)

# バックアップファイルの形式チェック
find app/*/docs -name "*.bak*" -type f
# → すべて 20YYMMDD_*.bak 形式
```

### Git履歴の確認

```bash
git status --short | grep "^R"
# → すべて git mv で移動、履歴保持確認
```

## 🎯 効果

### 改善点

1. **一貫性の確保**

   - app配下の全サービスで統一された命名規則
   - 重複日付プレフィックスの除去

2. **可読性の向上**

   - ファイル名から作成日が即座に判別可能
   - 日付順のソートで時系列把握が容易

3. **保守性の向上**

   - 既存のサブディレクトリ構造を維持
   - Git履歴を保持したままリネーム

4. **検索性の向上**
   - 日付ベースのファイル検索が容易
   - カテゴリ別のディレクトリ構造維持

## 📝 命名規則

### 標準フォーマット

```
YYYYMMDD_機能名_種別.md
```

### ディレクトリ構造

各サービスのdocsは以下の構造を推奨:

```
docs/
├── README.md                 # サービス説明
├── architecture/             # アーキテクチャ設計
├── migration/                # マイグレーション記録
├── refactoring/              # リファクタリング記録
├── implementation/           # 実装記録
├── database/                 # DB設計・マイグレーション
├── reports/                  # バグレポート・調査
└── legacy/                   # 古いドキュメント
```

## 🔄 今後の運用

### 新規ドキュメント作成時

```bash
# サービスディレクトリで実行
DATE=$(date +%Y%m%d)
SERVICE="core_api"  # または backend_shared, ledger_api, frontend

# カテゴリに応じて作成
touch app/backend/${SERVICE}/docs/implementation/${DATE}_新機能実装.md
touch app/backend/${SERVICE}/docs/reports/${DATE}_バグ調査.md
touch app/backend/${SERVICE}/docs/refactoring/${DATE}_リファクタリング計画.md
```

### ドキュメントレビュー

月次で以下を確認:

1. 全ファイルが `YYYYMMDD_` プレフィックスを持つか (README.md以外)
2. 適切なサブディレクトリに配置されているか
3. 古くなったドキュメントを `legacy/` に移動

## 📚 関連ドキュメント

- [docs/README.md](../../README.md) - プロジェクト全体のドキュメント索引
- [docs/reports/20251206_DOCS_DIRECTORY_REORGANIZATION_COMPLETE.md](./20251206_DOCS_DIRECTORY_REORGANIZATION_COMPLETE.md) - docsディレクトリ整理完了
- [scripts/README.md](../../../scripts/README.md) - スクリプト整理完了

## ✨ 完了

app配下の全サービスのdocsディレクトリ整理が完了しました。93ファイルすべてが日付プレフィックス規則に準拠し、Git履歴も保持されています。

---

**作成日**: 2025-12-06  
**最終更新**: 2025-12-06  
**ステータス**: 完了
