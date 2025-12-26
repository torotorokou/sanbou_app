# Backend Documentation

**最終更新**: 2025年12月25日

---

## 📚 ドキュメント一覧

### 通知システム

| ドキュメント                                                                      | 概要                                     | 対象読者                 |
| --------------------------------------------------------------------------------- | ---------------------------------------- | ------------------------ |
| [通知システム完全ガイド](./NOTIFICATION_SYSTEM_GUIDE.md)                          | Email/LINE通知の包括的な実装・運用ガイド | 開発者・運用担当         |
| [通知システム クイックリファレンス](./NOTIFICATION_QUICKREF.md)                   | よく使うコマンド・コード例のチートシート | 全員                     |
| [通知基盤 優先実装タスク](./NOTIFICATION_PRIORITY_TASKS.md)                       | 実装ロードマップとPhase別進捗            | プロジェクトマネージャー |
| [LINE通知基盤 完了報告](../development/notification_line_foundation_COMPLETED.md) | Phase 2実装の詳細報告                    | 開発者                   |

### データベース

- [Reserve Tables Migration](./20251216_RESERVE_TABLES_MIGRATION.md) - 予約テーブルのマイグレーション記録
- [Reservation Delete Logic Report](./RESERVATION_DELETE_LOGIC_REPORT.md) - 論理削除ロジックの実装報告
- [DB Names Implementation Report](./20251211_DB_NAMES_IMPLEMENTATION_REPORT.md) - DB命名規則の実装報告

### その他

- マテリアライズドビュー関連レポート（複数）
- Alembic health check報告
- DB性能調査レポート

---

## 🎯 クイックスタート

### 通知を送信したい

→ [通知システム クイックリファレンス](./NOTIFICATION_QUICKREF.md)

### 通知システムの全体像を理解したい

→ [通知システム完全ガイド](./NOTIFICATION_SYSTEM_GUIDE.md)

### 通知の実装状況を確認したい

→ [通知基盤 優先実装タスク](./NOTIFICATION_PRIORITY_TASKS.md)

### DBマイグレーションを実行したい

→ [Reserve Tables Migration](./20251216_RESERVE_TABLES_MIGRATION.md) または `make al-up-env ENV=local_dev`

---

## 📝 ドキュメント作成ガイドライン

新しいドキュメントを作成する際は以下を含めてください：

- **作成日/最終更新日**
- **対象読者**（開発者/運用担当/全員）
- **概要**（3-5行）
- **目次**（長いドキュメントの場合）
- **参考リンク**（関連ドキュメント）

ファイル命名規則：

- 実装報告: `YYYYMMDD_FEATURE_NAME_REPORT.md`
- ガイド: `FEATURE_NAME_GUIDE.md`
- クイックリファレンス: `FEATURE_NAME_QUICKREF.md`
