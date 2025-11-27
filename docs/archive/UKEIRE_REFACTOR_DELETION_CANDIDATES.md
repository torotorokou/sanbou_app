# Ukeire リファクタリング - 削除候補ファイル一覧

## 概要
機能別ディレクトリ構造への再編成後、以下のファイル・ディレクトリは参照されていないため削除候補です。

## 削除候補ファイル

### 1. 使用されていないリポジトリファイル
- `app/frontend/src/features/dashboard/ukeire/application/adapters/mockCalendar.repository.ts`
  - 理由: コード内からの参照なし（ドキュメント・スクリプトのみ）
  - 検証: `grep -r "mockCalendar.repository" --include="*.ts" --include="*.tsx"` → 0件

### 2. 空ディレクトリ
以下のディレクトリは空で、削除可能です:

- `app/frontend/src/features/dashboard/ukeire/infrastructure/`
  - 理由: 元々空のまま。各機能のinfrastructureサブディレクトリに移行済み

- `app/frontend/src/features/dashboard/ukeire/application/adapters/`
  - 理由: 全ファイル移動済み（mockCalendar.repository.ts以外）

- `app/frontend/src/features/dashboard/ukeire/application/`
  - 理由: サブディレクトリのみで直下にファイルなし

- `app/frontend/src/features/dashboard/ukeire/ui/cards/`
  - 理由: 全カード移動済み

- `app/frontend/src/features/dashboard/ukeire/ui/components/`
  - 理由: 全コンポーネント移動済み

- `app/frontend/src/features/dashboard/ukeire/ui/styles/`
  - 理由: 全スタイル移動済み

- `app/frontend/src/features/dashboard/ukeire/ui/`
  - 理由: 全サブディレクトリが空

- `app/frontend/src/features/dashboard/ukeire/presentation/tokens/`
  - 理由: 元々空のまま（新規shared/tokens.tsを作成済み）

- `app/frontend/src/features/dashboard/ukeire/presentation/`
  - 理由: サブディレクトリが空

- `app/frontend/src/features/dashboard/ukeire/domain/repositories/`
  - 理由: 元々空のまま

- `app/frontend/src/features/dashboard/ukeire/kpi-targets/domain/services/`
  - 理由: 新規作成したが未使用（将来targetServiceを移動予定）

## 削除推奨コマンド

```bash
# ファイル削除
git rm app/frontend/src/features/dashboard/ukeire/application/adapters/mockCalendar.repository.ts

# 空ディレクトリ削除（gitは空ディレクトリを追跡しないため、手動削除不要）
# ただし、明示的に削除する場合:
find app/frontend/src/features/dashboard/ukeire -type d -empty -delete
```

## 注意事項
- `mockCalendar.repository.ts` は一部ドキュメントやスクリプトから参照されていますが、実コードからは参照されていません
- 削除前に最終確認として以下を実行することを推奨:
  ```bash
  git grep -n "mockCalendar.repository" -- '*.ts' '*.tsx'
  ```

## 次のステップ（Phase 2）提案
1. `kpi-targets/domain/services/targetService.ts` を実装（domain/services/targetService.tsから移行）
2. `shared/` 配下のコンポーネントを汎用feature (`features/shared/ui/`) へ昇格
3. tabsFill関連スタイルをpages層へ移設（ページ固有のため）

---
生成日時: 2025-10-23
リファクタリング対象: app/frontend/src/features/dashboard/ukeire
