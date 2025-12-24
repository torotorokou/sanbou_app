# Scripts Directory

このディレクトリには、プロジェクトで使用する各種スクリプトが格納されています。

> **📌 データベース権限管理について**  
> 本番環境の権限管理は [ops/db/](../ops/db/) を参照してください。  
> 開発環境用のツール（スキーマダンプ等）のみこのディレクトリに残しています。

## 📁 ディレクトリ構造

```
scripts/
├── README.md                     # このファイル
├── lib/                          # 共通ライブラリ
│   ├── common.sh                # 汎用ユーティリティ関数
│   └── git_utils.sh             # Git 操作専用関数
├── git/                          # Git 関連スクリプト
│   ├── setup_git_hooks.sh       # Git フックセットアップ
│   ├── cleanup_git_history.sh   # Git 履歴クリーンアップ
│   └── gh_env_secrets_sync.sh   # GitHub Secrets 同期
├── db/                           # データベース関連スクリプト（開発用）
│   ├── dump_schema_current.sh   # スキーマダンプ
│   ├── export_schema_baseline_local_dev.sh
│   └── setup_permissions.sh     # 開発環境セットアップ
├── pg/                           # PostgreSQL バージョン管理
│   ├── archive_volume_tar.sh
│   ├── dumpall_from_v16.sh
│   ├── print_pg_version_in_volume.sh
│   └── restore_to_v17.sh
├── sql/                          # SQL ファイル（テスト・開発用）
│   ├── 20251204_alter_current_user_password.sql
│   ├── extensions_after_restore.sql
│   └── test_is_deleted_regression.sql
├── docker/                       # Docker 関連スクリプト
│   └── validate_compose.sh      # Docker Compose 検証
├── test/                         # テストスクリプト
│   ├── test_acceptance.sh       # 受け入れテスト
│   └── test_raw_save.sh         # Raw データ保存テスト
├── refactoring/                  # リファクタリングスクリプト
│   └── apply_soft_delete_refactoring.sh
├── python/                       # Python ユーティリティ
│   ├── apply_yaml_anchors.py    # YAML アンカー適用
│   └── diagnose_pdf_pipeline.py # PDF パイプライン診断
├── data/                         # データ関連スクリプト
│   └── download_master_data.py  # マスタデータダウンロード
└── examples/                     # サンプルファイル
    └── secrets.json
```

## 🔧 共通ライブラリ

### `lib/common.sh`

全てのスクリプトから利用できる汎用関数を提供します。

**主な機能:**

- **ログ出力**: `log_info`, `log_success`, `log_warn`, `log_error`, `log_debug`
- **セクション表示**: `log_section`, `log_step`
- **チェック表示**: `log_check_ok`, `log_check_warn`, `log_check_fail`
- **ファイル操作**: `get_repo_root`, `check_file_exists`, `check_dir_exists`
- **ユーザー確認**: `confirm`, `confirm_critical`
- **コマンド確認**: `check_command`, `require_commands`
- **バックアップ**: `create_backup`, `create_tar_backup`
- **Git 操作**: `check_git_clean`, `get_current_branch`, `get_remote_url`
- **環境変数**: `load_env_file`, `get_env_var`

**使用例:**

```bash
#!/bin/bash
# 共通ライブラリの読み込み
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# 使用
log_info "処理を開始します"
repo_root=$(get_repo_root) || exit 1
confirm "続行しますか?" || exit 0
log_success "完了しました"
```

### `lib/git_utils.sh`

Git 操作専用の関数を提供します。

**主な機能:**

- **Git フック管理**: `check_hook_exists`, `check_all_hooks`, `set_hook_executable`
- **Git フィルター**: `setup_git_filter`, `check_git_filter`
- **検証**: `verify_gitignore`
- **機密ファイル検出**: `detect_tracked_secrets`, `detect_staged_secrets`, `detect_secrets_in_history`
- **履歴クリーンアップ**: `check_git_filter_repo`, `backup_remote`, `restore_remote`
- **テスト**: `test_secret_file_block`
- **ユーティリティ**: `get_git_size`, `show_git_size`

**使用例:**

```bash
#!/bin/bash
source "${SCRIPT_DIR}/lib/common.sh"
source "${SCRIPT_DIR}/lib/git_utils.sh"

# Git フックの確認
check_all_hooks

# 機密ファイル検出
detect_tracked_secrets || exit 1

# Git フィルター設定
setup_git_filter
```

## 📜 主要スクリプト

### Git 関連 (`git/`)

#### `git/setup_git_hooks.sh`

Git フックをセットアップし、機密ファイルの誤コミット/プッシュを防止します。

**使用方法:**

```bash
bash scripts/git/setup_git_hooks.sh
```

**機能:**

1. Git フックの存在確認
2. 実行権限の設定
3. Git フィルターの設定
4. .gitignore の検証
5. 動作テスト

**セットアップされるフック:**

- `pre-commit`: コミット前のチェック
- `pre-push`: プッシュ前のチェック
- `commit-msg`: コミットメッセージのチェック
- `prepare-commit-msg`: コミット準備時の警告

#### `git/cleanup_git_history.sh`

Git 履歴から機密ファイルを完全に削除します。

**使用方法:**

```bash
bash scripts/git/cleanup_git_history.sh
```

**警告:**

- Git 履歴を書き換えます
- 実行前に必ずバックアップを取得してください
- チーム全員に通知が必要です
- 実行後、全員が再クローンする必要があります

**処理ステップ:**

1. git-filter-repo の確認
2. バックアップ作成
3. リモートの一時的な変更
4. 削除対象ファイルのリストアップ
5. 履歴削除
6. リモートの復元
7. Git のクリーンアップ
8. サイズ確認

#### `git/gh_env_secrets_sync.sh`

GitHub Environments に環境変数を同期します。

**使用方法:**

```bash
# .env ファイルから同期
./scripts/git/gh_env_secrets_sync.sh \
  --repo torotorokou/sanbou_app --env stg --file env/.env.common

# JSON ファイルから同期
./scripts/git/gh_env_secrets_sync.sh \
  --repo torotorokou/sanbou_app --json scripts/examples/secrets.json
```

**要件:**

- GitHub CLI (`gh`) がインストールされていること
- リポジトリの管理者権限があること
- `jq` (JSON 処理用)

---

### Docker 関連 (`docker/`)

#### `docker/validate_compose.sh`

Docker Compose の構成を検証します。

**使用方法:**

```bash
bash scripts/docker/validate_compose.sh
```

---

### テスト (`test/`)

#### `test/test_acceptance.sh`

受け入れテストを実行します。

**使用方法:**

```bash
bash scripts/test/test_acceptance.sh
```

#### `test/test_raw_save.sh`

Raw データ保存のテストを実行します。

**使用方法:**

```bash
bash scripts/test/test_raw_save.sh
```

---

### データベース (`db/`, `pg/`, `sql/`)

データベース管理、PostgreSQL バージョン管理、SQL ファイルが格納されています。

---

### Python ユーティリティ (`python/`)

#### `python/apply_yaml_anchors.py`

YAML アンカーを適用します。

#### `python/diagnose_pdf_pipeline.py`

PDF パイプラインの診断を実行します。

---

### データ管理 (`data/`)

#### `data/download_master_data.py`

マスタデータをダウンロードします。

## 🎯 スクリプト作成ガイドライン

新しいスクリプトを作成する際は、以下のガイドラインに従ってください。

### 1. 共通ライブラリの使用

```bash
#!/bin/bash
# スクリプトの説明

# 共通ライブラリの読み込み
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# カテゴリディレクトリ内のスクリプトの場合 (git/, db/, docker/ など)
source "${SCRIPT_DIR}/../lib/common.sh"
source "${SCRIPT_DIR}/../lib/git_utils.sh"  # 必要に応じて

# scripts/ 直下のスクリプトの場合
# source "${SCRIPT_DIR}/lib/common.sh"
# source "${SCRIPT_DIR}/lib/git_utils.sh"

# メイン処理
main() {
    show_script_header "スクリプト名" "説明"
    
    # 処理...
    
    log_success "完了しました"
}

# スクリプト実行
main "$@"
```

### 2. エラーハンドリング

```bash
# set オプションは common.sh で設定済み (set -euo pipefail)

# エラーチェック付き実行
repo_root=$(get_repo_root) || exit 1
check_file_exists "$file" || exit 1

# 確認付き実行
confirm "実行しますか?" || exit 0
```

### 3. ログ出力

```bash
# 適切なログレベルを使用
log_info "情報メッセージ"
log_success "成功メッセージ"
log_warn "警告メッセージ"
log_error "エラーメッセージ"
log_debug "デバッグメッセージ"  # DEBUG=1 で表示

# セクション区切り
log_section "処理ステップ 1"

# ステップ表示
log_step "ファイルを処理中..."

# チェック結果
log_check_ok "チェック成功"
log_check_warn "チェック警告"
log_check_fail "チェック失敗"
```

### 4. ユーザー確認

```bash
# 通常の確認 (デフォルト: no)
if confirm "続行しますか?"; then
    # 処理
fi

# 重要な確認 ("yes" の入力を要求)
if confirm_critical "データベースを削除します"; then
    # 危険な処理
fi
```

## 🧪 テスト

スクリプトの構文チェック:

```bash
# 単一ファイル (カテゴリ内)
bash -n scripts/git/setup_git_hooks.sh

# 全てのスクリプト
find scripts -name "*.sh" -exec bash -n {} \;
```

デバッグモード:

```bash
DEBUG=1 bash scripts/git/setup_git_hooks.sh
```

## 📚 参考情報

### 色定義

- `RED`: エラーメッセージ
- `GREEN`: 成功メッセージ
- `YELLOW`: 警告メッセージ
- `BLUE`: 情報メッセージ
- `CYAN`: デバッグメッセージ
- `MAGENTA`: 特別な強調
- `NC`: 色のリセット

### ベストプラクティス

1. **冪等性**: スクリプトは何度実行しても同じ結果になるべき
2. **ドライラン**: `--dry-run` オプションを提供する
3. **バックアップ**: 破壊的な操作の前にバックアップを作成
4. **確認**: 重要な操作の前にユーザー確認を求める
5. **ログ**: 適切なログレベルで進捗を表示
6. **エラー処理**: 適切なエラーメッセージと終了コード

## 🔗 関連ドキュメント

- [Git セキュリティガイド](../docs/GIT_SECURITY_GUIDE.md)
- [セキュリティ実装レポート](../docs/20251206_MULTI_LAYER_SECURITY_IMPLEMENTATION.md)
- [包括的監査レポート](../docs/20251206_ENV_SECRETS_LEAK_COMPREHENSIVE_AUDIT.md)
- [Scripts リファクタリング完了レポート](../docs/20251206_SCRIPTS_REFACTORING_COMPLETE.md)

## 🚀 クイックスタート

### 1. Git セキュリティ設定

```bash
# Git フックとフィルターをセットアップ
bash scripts/git/setup_git_hooks.sh

# 動作確認
git status
```

### 2. Docker 環境の検証

```bash
# Docker Compose 設定の検証
bash scripts/docker/validate_compose.sh
```

### 3. テスト実行

```bash
# 受け入れテストの実行
bash scripts/test/test_acceptance.sh
```

## 📝 移行ガイド

### 旧パスから新パスへの変更

スクリプトが再編成されました。以下の対応表を参考にしてください。

| 旧パス | 新パス | カテゴリ |
|--------|--------|----------|
| `scripts/setup_git_hooks.sh` | `scripts/git/setup_git_hooks.sh` | Git |
| `scripts/cleanup_git_history.sh` | `scripts/git/cleanup_git_history.sh` | Git |
| `scripts/gh_env_secrets_sync.sh` | `scripts/git/gh_env_secrets_sync.sh` | Git |
| `scripts/validate_compose.sh` | `scripts/docker/validate_compose.sh` | Docker |
| `scripts/test_acceptance.sh` | `scripts/test/test_acceptance.sh` | Test |
| `scripts/test_raw_save.sh` | `scripts/test/test_raw_save.sh` | Test |

### 既存スクリプトの修正方法

既存のスクリプトで `scripts/` 配下のスクリプトを呼び出している場合は、パスを更新してください。

```bash
# 修正前
bash scripts/setup_git_hooks.sh

# 修正後
bash scripts/git/setup_git_hooks.sh
```

---

**最終更新**: 2025-12-06  
**メンテナー**: システム管理者
