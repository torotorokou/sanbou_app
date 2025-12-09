# ドキュメント整理完了レポート

実施日: 2025年11月27日

## 整理の目的

プロジェクト全体のドキュメントを、各コンポーネント（フロントエンド、バックエンド）に適切に配置し、
開発者が必要なドキュメントを素早く見つけられるようにする。

## 実施内容

### 1. プロジェクトルート `docs/` の整理

**変更前:**
```
docs/
├── backend/       (33ファイル - 細分化前)
├── frontend/      (6ファイル)
├── shared/        (10ファイル)
└── archive/       (過去のドキュメント)
```

**変更後:**
```
docs/
├── shared/        # アプリ全体に関わる共有ドキュメントのみ
└── archive/       # 過去のドキュメント・参考資料
```

### 2. Frontend ドキュメント配置

**配置先:** `app/frontend/docs/`

**構成:**
```
frontend/docs/
├── architecture/   # FSDアーキテクチャ、設計規約 (7ファイル)
├── refactoring/    # リファクタリング履歴 (6ファイル)
├── migration/      # マイグレーション記録 (10ファイル)
├── legacy/         # 過去のドキュメント (1ファイル)
├── FRONTEND_TYPESCRIPT_FIELD_DICTIONARY.md
├── notifications.md
└── README.md
```

**合計:** 27ファイル

### 3. Backend - Core API ドキュメント配置

**配置先:** `app/backend/core_api/docs/`

**構成:**
```
core_api/docs/
├── database/           # DB設計・マイグレーション (7ファイル)
├── csv-processing/     # CSV処理 (9ファイル)
├── soft-delete/        # ソフトデリート (4ファイル)
├── api-implementation/ # API実装 (6ファイル)
├── refactoring/        # リファクタリング (6ファイル)
├── reports/            # バグ分析 (3ファイル)
├── legacy/             # 過去のドキュメント (5ファイル)
└── README.md
```

**合計:** 40ファイル

### 4. Backend - Ledger API ドキュメント配置

**配置先:** `app/backend/ledger_api/docs/`

**構成:**
```
ledger_api/docs/
├── architecture/  # アーキテクチャ設計 (1ファイル)
├── refactoring/   # リファクタリング (6ファイル)
├── migration/     # Streamlit App移行 (6ファイル)
└── README.md
```

**合計:** 14ファイル

## ドキュメント配置ポリシー

1. **フロントエンド専用** → `app/frontend/docs/`
2. **Core API（メインバックエンド）専用** → `app/backend/core_api/docs/`
3. **Ledger API専用** → `app/backend/ledger_api/docs/`
4. **フロント・バック両方に関わる** → `docs/shared/`
5. **古いドキュメント・参考資料** → `docs/archive/`

## 各コンポーネントのREADME

以下の場所に詳細なREADMEを配置:

- `docs/README.md` - プロジェクト全体のドキュメント管理
- `app/frontend/docs/README.md` - フロントエンドドキュメント概要
- `app/backend/core_api/docs/README.md` - Core APIドキュメント概要
- `app/backend/ledger_api/docs/README.md` - Ledger APIドキュメント概要

## 開発者向けガイド

### フロントエンド開発者
📁 `app/frontend/docs/` を参照
- アーキテクチャ: `architecture/FSD_ARCHITECTURE_GUIDE.md`
- 実装ガイド: `FRONTEND_TYPESCRIPT_FIELD_DICTIONARY.md`

### バックエンド開発者
📁 `app/backend/core_api/docs/` を参照
- DB設計: `database/DATABASE_COLUMN_DICTIONARY.md`
- API実装: `api-implementation/` ディレクトリ

### 帳票機能開発者
📁 `app/backend/ledger_api/docs/` を参照
- リファクタリング: `refactoring/API_REFACTORING_GUIDE.md`

### アーキテクト・PM
📁 `docs/shared/` を参照
- フルスタック機能実装レポート
- API契約・スキーマ定義

## メリット

1. **関心の分離**: 各コンポーネントのドキュメントが独立
2. **発見性向上**: 開発者が必要なドキュメントを素早く発見
3. **メンテナンス性**: コードとドキュメントの配置が一致
4. **スケーラビリティ**: 新しいサービスを追加しやすい構造

## 次のステップ

- [ ] 各チームメンバーに新しいドキュメント構造を周知
- [ ] CI/CDでドキュメントリンク切れをチェック
- [ ] 定期的なドキュメントレビュー・更新プロセスの確立
