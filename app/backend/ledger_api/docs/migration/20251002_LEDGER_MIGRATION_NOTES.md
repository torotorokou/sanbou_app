# 帳簿系サービス移行ノート（2025-10-02）

移行対象

- factory_report / average_sheet / management_sheet
  変更点
- エントリポイントをフル実装化（st_app依存のラッパー廃止）
- services側 processors/utils へ実装を集約
  互換性
- 既存の呼び出し: `from app.api.services.report.ledger.<name> import process` は不変
  後続対応
- st_app配下の管理表/平均表関連のコード削除
- 境界ケースのテスト拡充
- ドキュメントのAPI仕様更新
