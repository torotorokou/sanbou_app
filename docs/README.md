# Documentation

プロジェクト全体のドキュメント管理

## 📁 ディレクトリ構成

```
docs/
├── README.md                     # このファイル
├── reports/                      # 日次作業レポート (20251127-20251206)
│   └── YYYYMMDD_*.md            # 日付プレフィックス付きレポート
├── security/                     # セキュリティ関連ドキュメント
│   └── 20251206_GIT_SECURITY_GUIDE.md
├── database/                     # データベース設計・管理
│   ├── 20251204_DATABASE_PERMISSION_FIX.md
│   ├── 20251204_db_user_design.md
│   └── 20251204_db_user_migration_plan.md
├── bugs/                         # バグレポート
│   └── YYYYMMDD_*.md            # バグ調査・修正レポート
├── refactoring/                  # リファクタリング計画・記録
│   └── YYYYMMDD_*.md            # リファクタリング関連ドキュメント
├── logging/                      # ログ仕様・移行ガイド
│   ├── 20251128_logging_spec.md
│   ├── 20251206_MIGRATION_GUIDE.md
│   └── 20251206_logging_spec.md
├── conventions/                  # コーディング規約・ガイドライン
│   ├── backend/                 # バックエンド規約
│   ├── frontend/                # フロントエンド規約
│   ├── db/                      # DB規約・命名辞書
│   ├── 20251206_CONFIG_STRUCTURE_GUIDE.md
│   ├── 20251206_DOCUMENTATION_SECURITY_GUIDELINES.md
│   └── 20251206_refactoring_plan_local_dev.md
├── shared/                       # 共有ドキュメント
│   ├── contracts/               # API契約・OpenAPI定義
│   ├── diagrams/                # ER図・系統図
│   ├── YYYYMMDD_*.md           # フルスタック機能実装記録
│   └── README.md
├── backend/                      # バックエンド実装ドキュメント (空)
├── frontend/                     # フロントエンド実装ドキュメント (空)
├── infrastructure/               # インフラ・デプロイドキュメント
│   ├── MAINTENANCE_MODE.md      # メンテナンスモード運用ガイド（詳細版）
│   ├── MAINTENANCE_QUICKREF.md  # メンテナンスモードクイックリファレンス
│   └── MAKEFILE_GUIDE.md        # Makefile全体ガイド
├── env_templates/                # 環境変数テンプレート
│   └── README.md
└── archive/                      # アーカイブ (過去のドキュメント)
    └── 20251206_*.md            # 古いレポート・参考資料
```

## 📝 ドキュメント命名規則

**すべてのMarkdownファイルは `YYYYMMDD_` プレフィックスで始まる必要があります。**

```
20251206_機能名_レポート種別.md
```

**例:**

- `20251206_GIT_SECURITY_GUIDE.md` - セキュリティガイド
- `20251204_DATABASE_PERMISSION_FIX.md` - DB権限修正レポート
- `20251202_BALANCE_SHEET_DISPOSAL_VALUE_BUG_REPORT.md` - バグレポート

## 🗂️ カテゴリ別ガイド

### 📊 reports/

日々の作業レポート、実装完了レポート、統合レポートなど時系列ドキュメント。

**主なレポート:**

- `20251206_FINAL_REPORT.md` - 最終統括レポート
- `20251206_SCRIPTS_REFACTORING_COMPLETE.md` - スクリプトリファクタリング完了
- `20251206_MULTI_LAYER_SECURITY_IMPLEMENTATION.md` - セキュリティ多層防御実装

### 🔒 security/

セキュリティ関連の恒久的ガイドとベストプラクティス。

**主なドキュメント:**

- `20251206_GIT_SECURITY_GUIDE.md` - Git セキュリティガイド (7層防御システム)

### 🗄️ database/

データベース設計、権限管理、マイグレーション計画。

**主なドキュメント:**

- `20251204_DATABASE_PERMISSION_FIX.md` - DB権限修正記録
- `20251204_db_user_design.md` - DBユーザー設計
- `20251204_db_user_migration_plan.md` - ユーザー移行計画

### 🐛 bugs/

バグレポート、調査記録、修正履歴。

**例:**

- `20251202_BALANCE_SHEET_DISPOSAL_VALUE_BUG_REPORT.md`
- `20251204_db_connection_failure_diagnosis.md`

### 🔧 refactoring/

リファクタリング計画、影響分析、完了レポート。

**主なドキュメント:**

- `20251205_DATABASE_URL_BUILDER_REFACTORING.md`
- `20251204_RAG_API_DATETIME_REFACTORING.md`
- `20251203_CONFIG_CONSOLIDATION_AUDIT.md`

### 📝 logging/

ログ仕様、フォーマット、移行ガイド。

**主なドキュメント:**

- `20251128_logging_spec.md` - ログ仕様
- `20251206_MIGRATION_GUIDE.md` - 移行ガイド

### 📐 conventions/

コーディング規約、アーキテクチャガイドライン、命名規則。

**サブディレクトリ:**

- `backend/` - バックエンド開発規約
- `frontend/` - フロントエンド開発規約
- `db/` - データベース規約、カラム命名辞書

### 🤝 shared/

フロントエンド・バックエンド両方に関わる機能実装ドキュメント。

**サブディレクトリ:**

- `contracts/` - API契約、OpenAPI定義
- `diagrams/` - ER図、系統図 (Mermaid, DrawIO)

**主なドキュメント:**

- `20251127_LOCAL_DEMO_ENVIRONMENT_SETUP.md`
- `20251119_CSV_CALENDAR_IMPLEMENTATION.md`
- `20251117_ACHIEVEMENT_MODE_IMPLEMENTATION.md`

### 🏗️ infrastructure/

インフラストラクチャ、デプロイ、運用ドキュメント。

**主なドキュメント:**

- `MAINTENANCE_MODE.md` - メンテナンスモード運用ガイド（詳細版）
  - Cloud Runベースのメンテナンスページ
  - LB切替手順（計画/緊急）
  - トラブルシューティング
  - コスト管理
- `MAINTENANCE_QUICKREF.md` - クイックリファレンス
  - 緊急時の即座対応
  - よく使うコマンド集
  - チェックリスト
- `MAKEFILE_GUIDE.md` - Makefile全体ガイド

### 📦 archive/

過去のドキュメント、初期実装記録、参考資料。

**内容:**

- 初期BFFアーキテクチャ設計
- カレンダー機能初期実装
- 古いリファクタリングレポート
- 環境変数バックアップ

## 🎯 各コンポーネントのドキュメント

各アプリケーション/サービスのドキュメントは、それぞれのディレクトリ内に配置されています：

### Frontend

📁 `app/frontend/docs/`

- Feature-Sliced Design アーキテクチャ
- React/TypeScript実装ガイド
- リファクタリング履歴
- マイグレーション記録

### Backend - Core API

📁 `app/backend/core_api/docs/`

- データベース設計・マイグレーション
- CSVアップロード処理
- ソフトデリート実装
- API実装記録
- リファクタリング履歴

### Backend - Ledger API

📁 `app/backend/ledger_api/docs/`

- 帳票生成API
- PDF処理
- Streamlit App移行記録

### Backend - Shared

📁 `app/backend/backend_shared/docs/`

- 共通ライブラリドキュメント
- ログ実装
- 認証・IAP

## 📋 ドキュメント配置ポリシー

1. **日次作業レポート** → `docs/reports/`
2. **セキュリティガイド** → `docs/security/`
3. **データベース設計・管理** → `docs/database/`
4. **バグレポート** → `docs/bugs/`
5. **リファクタリング計画** → `docs/refactoring/`
6. **ログ仕様** → `docs/logging/`
7. **コーディング規約** → `docs/conventions/`
8. **フルスタック機能実装** → `docs/shared/`
9. **フロントエンド専用** → `app/frontend/docs/`
10. **Core API専用** → `app/backend/core_api/docs/`
11. **Ledger API専用** → `app/backend/ledger_api/docs/`
12. **Backend共通** → `app/backend/backend_shared/docs/`
13. **古いドキュメント** → `docs/archive/`

## 🔍 参照ガイド

### 役割別

**フロントエンド開発者:**

- `app/frontend/docs/` - フロントエンド実装
- `docs/conventions/frontend/` - フロントエンド規約
- `docs/shared/contracts/` - API契約

**バックエンド開発者:**

- `app/backend/core_api/docs/` - Core API実装
- `app/backend/ledger_api/docs/` - Ledger API実装
- `app/backend/backend_shared/docs/` - 共通ライブラリ
- `docs/conventions/backend/` - バックエンド規約
- `docs/database/` - DB設計

**DB管理者:**

- `docs/database/` - DB設計・権限管理
- `docs/conventions/db/` - DB規約・命名辞書
- `docs/shared/diagrams/` - ER図

**DevOps/インフラ:**

- `docs/security/` - セキュリティガイド
- `docs/infrastructure/` - インフラドキュメント
- `docs/shared/` - 環境設定

**アーキテクト・PM:**

- `docs/reports/` - プロジェクト進捗レポート
- `docs/shared/` - フルスタック機能実装
- `docs/refactoring/` - 技術的負債管理

### タスク別

**新機能実装:**

1. `docs/shared/contracts/` で API契約確認
2. `docs/conventions/` で規約確認
3. 該当サービスの `docs/` で実装パターン確認

**バグ修正:**

1. `docs/bugs/` で類似バグ検索
2. 該当サービスの `docs/` で実装詳細確認

**リファクタリング:**

1. `docs/refactoring/` で過去の事例確認
2. `docs/conventions/` で新しい規約確認

**セキュリティ対策:**

1. `docs/security/20251206_GIT_SECURITY_GUIDE.md` 必読
2. `docs/conventions/20251206_DOCUMENTATION_SECURITY_GUIDELINES.md` 参照

## 🚀 クイックスタート

### 新しいレポートを作成する

```bash
# 日付プレフィックスを取得
DATE=$(date +%Y%m%d)

# レポート作成
touch docs/reports/${DATE}_新機能名_実装完了.md
```

### ドキュメント検索

```bash
# 日付でレポート検索
ls docs/reports/20251206_*.md

# キーワードでドキュメント検索
grep -r "セキュリティ" docs/ --include="*.md"

# 最近更新されたドキュメント
find docs/ -name "*.md" -mtime -7 -ls
```

## 📚 関連リソース

- [Scripts README](../scripts/README.md) - スクリプト管理ドキュメント
- [Backend Shared Docs](../app/backend/backend_shared/docs/) - 共通ライブラリ
- [Git Security Guide](./security/20251206_GIT_SECURITY_GUIDE.md) - セキュリティ必読

---

**ドキュメント規則更新日**: 2025-12-06  
**メンテナー**: システム管理者
