# Plan Worker Documentation

Plan Worker（計画最適化・バッチ処理）のドキュメント

## 概要

Plan Workerは、受注計画の最適化・スムージング処理を行うバッチワーカーサービスです。
需要予測、在庫最適化、生産計画の自動調整などを実行します。

## ディレクトリ構成

```
docs/
├── README.md          # このファイル
├── architecture/      # アーキテクチャ設計（今後追加）
├── algorithms/        # アルゴリズム説明（今後追加）
└── operations/        # 運用ガイド（今後追加）
```

## 主な機能

- **需要予測**: 過去データから需要を予測
- **計画スムージング**: 受注の平準化処理
- **在庫最適化**: 最適在庫レベルの計算
- **バッチ処理**: スケジュール実行

## 技術スタック

- **言語**: Python
- **データ処理**: Pandas, NumPy
- **データベース**: PostgreSQL (SQLAlchemy)
- **CLI**: Click
- **コンテナ**: Docker

## アーキテクチャ

### 主要コンポーネント

```
app/
├── worker.py              # メインワーカー
├── application/           # アプリケーション層
├── domain/
│   ├── predictor.py      # 予測モデル
│   └── services/         # ドメインサービス
├── infrastructure/
│   └── db/               # データベースアクセス
├── interfaces/
│   └── worker/
│       ├── cli.py        # CLIインターフェース
│       └── test_db_connection.py
├── ports/
│   └── repositories.py   # リポジトリインターフェース
└── shared/
    ├── config/           # 設定管理
    └── logging/          # ログ管理
```

## 実行方法

### CLI実行

```bash
cd app/backend/plan_worker
python -m app.interfaces.worker.cli
```

### データベース接続テスト

```bash
python -m app.interfaces.worker.test_db_connection
```

### ヘルスチェック

```bash
python -m app.scripts.db_healthcheck
```

## アルゴリズム

### モデルバリエーション

1. **シンプルモデル**: 基本的な平準化処理
2. **ゴーストなしモデル**: 欠品考慮なし
3. **標準モデル（Plus）**: 高度な最適化

詳細は `app/test/` 配下のノートブックを参照

## 設定

### 環境変数

- `DATABASE_URL` - PostgreSQL接続文字列
- `LOG_LEVEL` - ログレベル
- `WORKER_INTERVAL` - 実行間隔（秒）

## データフロー

1. **データ取得** (step01_fetch.py): DBから受注データ取得
2. **スムージング** (step02_smooth.py): 需要平準化処理
3. **保存** (step03_save.py): 結果をDBに保存
4. **計画計算** (step04_plan_calc.py): 最終計画算出

## 監視・運用

TODO: 運用ガイドを追加

## テスト

```bash
cd app/backend/plan_worker
pytest
```

## 関連ドキュメント

- Core API: データソース連携
- プロジェクト全体: `/docs/`

## 今後の予定

- [ ] アルゴリズム詳細ドキュメントの作成
- [ ] 運用ガイドの追加
- [ ] パフォーマンスチューニングガイド
- [ ] モニタリング設定ガイド
- [ ] アーキテクチャ図の作成
