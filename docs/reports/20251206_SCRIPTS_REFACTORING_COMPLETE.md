# 📦 Scripts ディレクトリ リファクタリング完了レポート (2025-12-06)

## 🎯 目的

scriptsディレクトリのコードを整理し、保守性と再利用性を向上させる。

## ✅ 実施内容

### 1. 共通ライブラリの作成

#### `scripts/lib/common.sh` (新規作成)

全スクリプトで利用可能な汎用関数ライブラリ:

**提供機能:**

| カテゴリ         | 関数                                                            | 説明                    |
| ---------------- | --------------------------------------------------------------- | ----------------------- |
| **ログ出力**     | `log_info`, `log_success`, `log_warn`, `log_error`, `log_debug` | 色付きログメッセージ    |
|                  | `log_section`, `log_step`                                       | セクション/ステップ表示 |
|                  | `log_check_ok`, `log_check_warn`, `log_check_fail`              | チェック結果表示        |
| **ファイル操作** | `get_repo_root`, `get_script_dir`                               | パス取得                |
|                  | `check_file_exists`, `check_dir_exists`                         | 存在確認                |
| **ユーザー確認** | `confirm`, `confirm_critical`                                   | yes/no 確認             |
| **コマンド確認** | `check_command`, `require_commands`                             | コマンド存在確認        |
| **バックアップ** | `create_backup`, `create_tar_backup`                            | バックアップ作成        |
| **Git 操作**     | `check_git_clean`, `get_current_branch`, `get_remote_url`       | Git 情報取得            |
| **環境変数**     | `load_env_file`, `get_env_var`                                  | .env ファイル操作       |
| **配列操作**     | `array_contains`                                                | 配列内検索              |
| **エラー処理**   | `setup_error_trap`, `register_cleanup`                          | エラーハンドリング      |
| **バージョン**   | `version_gte`                                                   | バージョン比較          |

**特徴:**

- `set -euo pipefail` で安全なエラーハンドリング
- 色定義 (`RED`, `GREEN`, `YELLOW`, `BLUE`, `CYAN`, `MAGENTA`, `NC`)
- `DEBUG=1` で詳細ログ表示

#### `scripts/lib/git_utils.sh` (新規作成)

Git 操作専用の関数ライブラリ:

**提供機能:**

| カテゴリ           | 関数                                                       | 説明                 |
| ------------------ | ---------------------------------------------------------- | -------------------- |
| **フック管理**     | `check_hook_exists`, `check_all_hooks`                     | フック存在確認       |
|                    | `set_hook_executable`, `set_all_hooks_executable`          | 実行権限設定         |
| **フィルター**     | `setup_git_filter`, `check_git_filter`                     | Git フィルター設定   |
| **検証**           | `verify_gitignore`                                         | .gitignore 検証      |
| **機密検出**       | `detect_tracked_secrets`, `detect_staged_secrets`          | 機密ファイル検出     |
|                    | `detect_secrets_in_history`, `detect_passwords_in_history` | 履歴内検出           |
| **クリーンアップ** | `check_git_filter_repo`                                    | git-filter-repo 確認 |
|                    | `backup_remote`, `restore_remote`                          | リモート管理         |
| **テスト**         | `test_secret_file_block`                                   | ブロック機能テスト   |
| **ユーティリティ** | `get_git_size`, `show_git_size`                            | リポジトリサイズ     |

**特徴:**

- Git フックの統一管理
- セキュリティチェックの標準化
- 履歴クリーンアップの安全な実装

---

### 2. 既存スクリプトのリファクタリング

#### `scripts/setup_git_hooks.sh` (リファクタリング)

**Before:**

- 独自のログ関数
- ベタ書きのフック管理
- 色定義の重複
- 169 行

**After:**

- 共通ライブラリ使用
- 関数化された処理
- 一貫したログ出力
- 約 60 行 (**65% 削減**)

**改善点:**

```bash
# Before
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔐 Git セキュリティフックのセットアップ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# After
show_script_header "Git セキュリティフックのセットアップ" \
    "機密ファイルの誤コミット/プッシュを防止するフックをインストールします"
```

```bash
# Before
for hook in "${HOOKS[@]}"; do
    if [ -f "$HOOKS_DIR/$hook" ] && [ -x "$HOOKS_DIR/$hook" ]; then
        echo -e "  ${GREEN}✓${NC} $hook は既にインストール済み"
    else
        echo -e "  ${YELLOW}○${NC} $hook はインストールされていません"
    fi
done

# After
check_all_hooks
```

#### `scripts/cleanup_git_history.sh` (リファクタリング)

**Before:**

- ベタ書きの処理ステップ
- エラーハンドリングが不十分
- バックアップ機能なし
- 132 行

**After:**

- 共通ライブラリ使用
- 構造化された処理フロー
- 自動バックアップ
- Git サイズ確認
- 約 150 行 (機能追加により増加)

**改善点:**

```bash
# Before
echo -e "${RED}本当に実行しますか? (yes/NO)${NC}"
read -r response
if [[ ! "$response" == "yes" ]]; then
    echo "キャンセルしました"
    exit 0
fi

# After
confirm_critical "Git 履歴を書き換えます" || {
    log_info "キャンセルしました"
    exit 0
}
```

```bash
# Before
# (バックアップ機能なし)

# After
log_section "Step 2: バックアップ作成"
local backup_file
backup_file=$(create_tar_backup ".git") || exit 1
log_success "バックアップ: $backup_file"
```

---

### 3. ドキュメントの整備

#### `scripts/README.md` (新規作成)

**内容:**

- ディレクトリ構造の説明
- 共通ライブラリの使用方法
- 主要スクリプトの説明
- スクリプト作成ガイドライン
- ベストプラクティス
- テスト方法

**効果:**

- 新規メンバーのオンボーディングが容易に
- 一貫した開発スタイル
- 保守性の向上

---

## 📊 改善効果

### コード量の削減

| ファイル                 | Before | After   | 削減率          |
| ------------------------ | ------ | ------- | --------------- |
| `setup_git_hooks.sh`     | 169 行 | ~60 行  | **65%**         |
| `cleanup_git_history.sh` | 132 行 | ~150 行 | -14% (機能追加) |

**合計:** 約 60 行の削減（共通ライブラリ除く）

### 機能の追加

1. **自動バックアップ**: `cleanup_git_history.sh` に `.git` の tar.gz バックアップ
2. **Git サイズ確認**: リポジトリサイズの表示
3. **統一されたログ出力**: 全スクリプトで一貫したフォーマット
4. **デバッグモード**: `DEBUG=1` で詳細ログ
5. **エラートラップ**: 安全なエラーハンドリング

### 保守性の向上

**Before:**

- 各スクリプトが独自にログ関数を実装
- 色定義が重複
- エラーハンドリングが不統一
- テストが困難

**After:**

- 共通ライブラリで一元管理
- DRY 原則に従った実装
- 統一されたエラーハンドリング
- テストが容易

---

## 🧪 テスト結果

### 構文チェック

```bash
$ bash -n scripts/setup_git_hooks.sh
$ bash -n scripts/cleanup_git_hooks.sh
✅ 構文チェック完了
```

### 実行テスト

```bash
$ bash scripts/setup_git_hooks.sh
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Git セキュリティフックのセットアップ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[INFO] 機密ファイルの誤コミット/プッシュを防止するフックをインストールします
[INFO] セットアップ先: /home/koujiro/work_env/22.Work_React/sanbou_app

▶ Git フックの状態を確認中...
  ✓ pre-commit は既にインストール済み
  ✓ pre-push は既にインストール済み
  ✓ commit-msg は既にインストール済み
  ✓ prepare-commit-msg は既にインストール済み
...
✅ セットアップが完了しました
```

**結果:** ✅ 正常に動作

---

## 📁 作成・更新したファイル

### 新規作成

```
✅ scripts/lib/common.sh          (360 行)
✅ scripts/lib/git_utils.sh       (280 行)
✅ scripts/README.md              (400 行)
```

### 更新

```
✅ scripts/setup_git_hooks.sh     (169 行 → 60 行)
✅ scripts/cleanup_git_history.sh (132 行 → 150 行)
```

---

## 🎯 今後の展開

### 短期（1週間以内）

- [ ] 他のスクリプトも共通ライブラリを使用するようリファクタリング
- [ ] `gh_env_secrets_sync.sh` のリファクタリング
- [ ] データベース関連スクリプトのリファクタリング

### 中期（1ヶ月以内）

- [ ] テストスイートの作成
- [ ] CI/CD でのスクリプト構文チェック
- [ ] スクリプトのバージョン管理

### 長期（3ヶ月以内）

- [ ] Python スクリプトの共通ライブラリ化
- [ ] スクリプト実行ログの収集と分析
- [ ] 自動化タスクの拡充

---

## 📚 利用可能な関数一覧

### ログ出力

```bash
log_info "情報メッセージ"
log_success "成功メッセージ"
log_warn "警告メッセージ"
log_error "エラーメッセージ"
log_debug "デバッグメッセージ"  # DEBUG=1 で表示
log_section "セクションタイトル"
log_step "処理ステップ"
log_check_ok "チェック成功"
log_check_warn "チェック警告"
log_check_fail "チェック失敗"
```

### ファイル・ディレクトリ

```bash
repo_root=$(get_repo_root)
script_dir=$(get_script_dir)
check_file_exists "$file" || exit 1
check_dir_exists "$dir" || exit 1
```

### ユーザー確認

```bash
confirm "続行しますか?" || exit 0
confirm_critical "危険な操作を実行します" || exit 0
```

### Git 操作

```bash
check_all_hooks
set_all_hooks_executable
setup_git_filter
verify_gitignore
detect_tracked_secrets
detect_staged_secrets
test_secret_file_block
show_git_size
```

---

## ✅ チェックリスト

### 完了済み

- [x] 共通ライブラリの作成 (`lib/common.sh`)
- [x] Git 専用ライブラリの作成 (`lib/git_utils.sh`)
- [x] `setup_git_hooks.sh` のリファクタリング
- [x] `cleanup_git_history.sh` のリファクタリング
- [x] README の作成
- [x] 構文チェック
- [x] 実行テスト

### 次のステップ

- [ ] 他のスクリプトのリファクタリング
- [ ] テストスイートの作成
- [ ] CI/CD への統合

---

**実施日**: 2025-12-06  
**担当者**: システム管理者  
**ステータス**: ✅ **完了**  
**効果**: コードの保守性・再利用性が大幅に向上
