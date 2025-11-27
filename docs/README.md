# Documentation

プロジェクト全体のドキュメント管理

## ディレクトリ構成

```
docs/
├── shared/   # アプリ全体に関わる共有ドキュメント
└── archive/  # 過去のドキュメント・参考資料
```

## 各コンポーネントのドキュメント

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

## このディレクトリの内容

### shared/
フロントエンド・バックエンドの両方に関わる機能実装ドキュメント
- フルスタック機能実装レポート
- API契約・スキーマ定義
- 命名規則・辞書
- ER図・設計図
- インフラ設定

詳細は [shared/README.md](./shared/README.md) を参照

### archive/
過去のドキュメント・初期の実装記録・参考資料
- 初期BFFアーキテクチャ
- カレンダー機能実装記録
- 初期リファクタリングレポート
- 環境変数設定履歴

## ドキュメント配置ポリシー

1. **フロントエンド専用** → `app/frontend/docs/`
2. **Core API（メインバックエンド）専用** → `app/backend/core_api/docs/`
3. **Ledger API専用** → `app/backend/ledger_api/docs/`
4. **フロント・バック両方に関わる** → `docs/shared/`
5. **古いドキュメント・参考資料** → `docs/archive/`

## 参照ガイド

- フロントエンド開発者 → `app/frontend/docs/` を参照
- バックエンド開発者 → `app/backend/core_api/docs/` を参照
- 帳票機能開発者 → `app/backend/ledger_api/docs/` を参照
- アーキテクト・PM → このディレクトリの `shared/` を参照
