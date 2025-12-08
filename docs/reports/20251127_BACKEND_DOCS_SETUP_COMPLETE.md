# バックエンドサービス ドキュメント整備完了

実施日: 2025年11月27日

## 目的

全バックエンドサービスに統一されたドキュメント構造を整備し、
各サービスの概要、機能、技術スタック、開発ガイドを明確化する。

## 実施内容

### 対象サービス

全7つのバックエンドサービス/ライブラリ:

1. **ai_api** - AI機能（OpenAI GPT連携）
2. **backend_shared** - 共通ライブラリ
3. **core_api** - メインAPI（FastAPI）
4. **ledger_api** - 帳票生成・PDF処理
5. **manual_api** - マニュアル管理
6. **plan_worker** - 計画最適化バッチ
7. **rag_api** - RAG（検索拡張生成）

## 作成物

### 各サービスのREADME.md

全サービスに以下の構成でREADME.mdを作成:

```markdown
# [Service Name] Documentation

## 概要
## ディレクトリ構成
## 主な機能
## 技術スタック
## 開発ガイド
## 関連ドキュメント
## 今後の予定
```

## サービス別概要

### 1. AI API
**パス**: `app/backend/ai_api/docs/`

- OpenAI GPT APIとの連携
- プロンプト管理
- レスポンス処理

**技術**: Python, FastAPI, OpenAI GPT API

### 2. Backend Shared
**パス**: `app/backend/backend_shared/docs/`

- 全サービス共通ライブラリ
- DB基底クラス、リポジトリパターン
- CSV処理、バリデーション
- エラーハンドリング、ログ管理

**主要コンポーネント**:
- adapters/ - FastAPI統合
- db/ - データベース基底
- usecases/ - 共通ユースケース
- utils/ - ユーティリティ

**技術**: Python, SQLAlchemy, Pandas

### 3. Core API ✓
**パス**: `app/backend/core_api/docs/`

すでに詳細なドキュメント構造あり:
- database/
- csv-processing/
- soft-delete/
- api-implementation/
- refactoring/
- reports/

### 4. Ledger API ✓
**パス**: `app/backend/ledger_api/docs/`

すでに詳細なドキュメント構造あり:
- architecture/
- refactoring/
- migration/

### 5. Manual API
**パス**: `app/backend/manual_api/docs/`

- マニュアルカタログ管理
- マニュアル検索
- ベンダー情報管理

**技術**: Python, FastAPI, ファイルシステム

### 6. Plan Worker
**パス**: `app/backend/plan_worker/docs/`

- 需要予測
- 計画スムージング（平準化）
- 在庫最適化
- バッチ処理

**アルゴリズム**:
- シンプルモデル
- ゴーストなしモデル
- 標準モデル（Plus）

**技術**: Python, Pandas, NumPy, PostgreSQL, Click

### 7. RAG API
**パス**: `app/backend/rag_api/docs/`

- PDFドキュメント取り込み
- チャンク分割
- ベクトル検索
- GPT回答生成

**技術**: Python, FastAPI, OpenAI GPT, PDF処理

## ディレクトリ構造

```
app/backend/
├── ai_api/
│   └── docs/
│       └── README.md          ← 新規作成
├── backend_shared/
│   └── docs/
│       └── README.md          ← 新規作成
├── core_api/
│   └── docs/
│       ├── README.md          ← 既存（更新済み）
│       ├── database/
│       ├── csv-processing/
│       ├── soft-delete/
│       ├── api-implementation/
│       ├── refactoring/
│       ├── reports/
│       └── legacy/
├── ledger_api/
│   └── docs/
│       ├── README.md          ← 既存（更新済み）
│       ├── architecture/
│       ├── refactoring/
│       └── migration/
├── manual_api/
│   └── docs/
│       └── README.md          ← 新規作成
├── plan_worker/
│   └── docs/
│       └── README.md          ← 新規作成
└── rag_api/
    └── docs/
        └── README.md          ← 新規作成
```

## Git管理

全てのdocsディレクトリにREADME.mdが配置されたため、Gitで管理可能。
空ディレクトリは`.gitkeep`なしでも追跡される。

## 標準化されたREADME構成

各README.mdは以下のセクションを含む:

1. **概要** - サービスの目的・役割
2. **ディレクトリ構成** - docs内の構造（拡張可能）
3. **主な機能** - 提供する機能リスト
4. **技術スタック** - 使用技術・ライブラリ
5. **開発ガイド** - ローカル開発手順、環境変数
6. **関連ドキュメント** - 他サービス・全体ドキュメントへのリンク
7. **今後の予定** - 拡充予定のドキュメント

## メリット

1. **一貫性**: 全サービスで統一されたドキュメント構造
2. **発見性**: 各サービスの概要を素早く把握可能
3. **オンボーディング**: 新メンバーが各サービスを理解しやすい
4. **拡張性**: 今後のドキュメント追加の基盤が整備
5. **Git管理**: 全ドキュメントがバージョン管理対象

## 次のステップ

### 優先度: 高
- [ ] Core API: 既存ドキュメントの日付整理（完了済み）
- [ ] Ledger API: 既存ドキュメントの日付整理（完了済み）
- [ ] 各サービスのAPI仕様書作成

### 優先度: 中
- [ ] アーキテクチャ図の追加（全サービス）
- [ ] エンドポイント一覧の作成（API系）
- [ ] 利用ガイド・サンプルコード追加

### 優先度: 低
- [ ] パフォーマンスチューニングガイド
- [ ] トラブルシューティングガイド
- [ ] ベストプラクティス集

## 参照

- プロジェクト全体のドキュメント: `/docs/`
- フロントエンド: `/app/frontend/docs/`
