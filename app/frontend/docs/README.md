# Frontend Documentation

フロントエンド（React + TypeScript + Vite）のドキュメント

## ディレクトリ構成

```
docs/
├── architecture/  # アーキテクチャ設計・規約
├── refactoring/   # リファクタリング履歴
├── migration/     # マイグレーション計画・進捗
└── legacy/        # 過去のドキュメント
```

## カテゴリ別概要

### 🏗️ architecture/

アーキテクチャ設計、コーディング規約、ベストプラクティス

- Feature-Sliced Design (FSD) アーキテクチャガイド
- 依存関係ルール・Lintルール
- レスポンシブデザインガイド
- API通信ベストプラクティス

主要ドキュメント:

- `FSD_ARCHITECTURE_GUIDE.md` - FSDアーキテクチャ完全ガイド
- `FSD_DEPENDENCY_RULES_SUMMARY.md` - 依存関係ルールサマリー
- `RESPONSIVE_GUIDE.md` - レスポンシブデザインガイド

### 🔄 refactoring/

コードリファクタリング、品質改善の履歴

- FSDへのリファクタリング完了レポート
- MVVM + Repositoryパターン実装
- サブフィーチャー分割
- 循環依存解消

主要ドキュメント:

- `FSD_REFACTORING_COMPLETE_REPORT.md` - FSDリファクタリング完了レポート
- `FSD_MVVM_REPOSITORY_COMPLETE_20251121.md` - MVVM実装完了
- `SUB_FEATURE_SPLIT_COMPLETE_20251121.md` - サブフィーチャー分割完了

### 📋 migration/

段階的マイグレーション計画と進捗管理

- Phase別実行計画
- マイグレーションステータス
- インポート置換計画

主要ドキュメント:

- `FSD_MIGRATION_GUIDE.md` - FSDマイグレーションガイド
- `MIGRATION_STATUS.md` - マイグレーション進捗状況
- `PHASE*_*.md` - フェーズ別完了レポート

### 🗄️ legacy/

過去のドキュメント・参考資料

## その他のドキュメント

- `FRONTEND_TYPESCRIPT_FIELD_DICTIONARY.md` - TypeScriptフィールド名辞書
- `notifications.md` - 通知機能ドキュメント
