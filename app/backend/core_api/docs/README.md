# Core API Documentation

Core API（FastAPI）のドキュメント

## ディレクトリ構成

```
docs/
├── database/           # データベース設計・マイグレーション
├── csv-processing/     # CSVアップロード・バリデーション
├── soft-delete/        # ソフトデリート機能
├── api-implementation/ # API・ビジネスロジック
├── refactoring/        # コードリファクタリング
├── reports/            # バグ分析・調査レポート
└── legacy/             # 過去のドキュメント
```

## カテゴリ別概要

### 📊 database/

データベーススキーマ設計、Alembicマイグレーション管理

- カラム辞書・フィールド名辞書
- マイグレーションポリシー
- PostgreSQL運用

### 📤 csv-processing/

CSV処理機能（アップロード・バリデーション・エラーハンドリング）

- 非同期アップロード実装
- バリデーションロジック
- エラー対応履歴

### 🗑️ soft-delete/

ソフトデリート（論理削除）機能の実装・運用

- クイックスタートガイド
- 実装詳細・設計思想

### 🔌 api-implementation/

FastAPI エンドポイント、ビジネスロジック、パフォーマンス最適化

- 各種API実装記録
- マテリアライズドビュー最適化

### 🔧 refactoring/

コード品質改善・技術的負債解消

- SQLリファクタリング
- スキーマクリーンアップ

### 📝 reports/

データ不整合調査、バグ分析、RCA レポート

### 🗄️ legacy/

過去のドキュメント・参考資料
