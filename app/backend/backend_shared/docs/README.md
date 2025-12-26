# Backend Shared Documentation

Backend Shared（共通ライブラリ・ユーティリティ）のドキュメント

## 概要

Backend Sharedは、全バックエンドサービスで共通利用されるライブラリ、ユーティリティ、基底クラスを提供するパッケージです。

## ディレクトリ構成

```
docs/
├── README.md          # このファイル
├── architecture/      # アーキテクチャ設計（今後追加）
├── api/              # 共通API設計（今後追加）
└── guides/           # 利用ガイド（今後追加）
```

## 主要コンポーネント

### adapters/

- **FastAPI統合**: エラーハンドラー、ミドルウェア
- **Presentation層**: レスポンスベース、エラーレスポンス、成功レスポンス

### db/

- **database.py**: データベース接続管理
- **base_model.py**: 共通ベースモデル
- **repository_base.py**: リポジトリ基底クラス
- **utils.py**: DB関連ユーティリティ

### domain/

- **contract.py**: 契約ドメインモデル
- **job.py**: ジョブドメインモデル

### infrastructure/

- **config**: 設定ローダー、パス管理
- **logging_utils**: ログ設定、アクセスログ

### usecases/

- **csv_formatter**: CSVフォーマット処理
- **csv_validator**: CSVバリデーション
- **report_checker**: レポートチェッカー

### utils/

- **csv_reader.py**: CSV読み込み
- **dataframe_utils.py**: DataFrame操作
- **dataframe_validator.py**: DataFrameバリデーション
- **date_filter_utils.py**: 日付フィルタリング

## 技術スタック

- **言語**: Python 3.11+
- **ORM**: SQLAlchemy
- **データ処理**: Pandas
- **テスト**: pytest

## 利用方法

### インストール

```bash
pip install -e app/backend/backend_shared
```

### インポート例

```python
from backend_shared.db.database import get_db
from backend_shared.adapters.presentation import SuccessResponse
from backend_shared.usecases.csv_validator import PureCSVValidator
```

## エラーハンドリング

詳細は [ERROR_HANDLING_GUIDE.md](../ERROR_HANDLING_GUIDE.md) を参照

## 開発ガイドライン

1. **DRY原則**: 複数のAPIで使用される機能はここに集約
2. **依存関係**: 特定のAPIに依存しない汎用的な実装
3. **テスト**: 全機能に対してユニットテストを作成
4. **型ヒント**: 全関数・メソッドに型ヒントを追加

## 関連ドキュメント

- Core API: `/app/backend/core_api/docs/`
- Ledger API: `/app/backend/ledger_api/docs/`
- プロジェクト全体: `/docs/`

## 今後の予定

- [ ] 各コンポーネントの詳細ドキュメント作成
- [ ] 利用ガイド・サンプルコード追加
- [ ] アーキテクチャ図の作成
- [ ] ベストプラクティス集の作成
