# 🔐 Git セキュリティ対策ガイド

## 概要

このリポジトリでは、機密ファイル（環境変数、パスワード、秘密鍵）の誤コミット・プッシュを防ぐため、**多層防御システム**を導入しています。

---

## 🛡️ 多層防御の仕組み

### 第1層: .gitignore

**目的**: ファイルシステムレベルでの除外

```gitignore
# env/ と secrets/ ディレクトリ全体を除外
/env/
/secrets/

# ただしテンプレートは許可
!env/.env.example
!env/*.template
!secrets/.env.secrets.template
```

### 第2層: .gitattributes + Git フィルター

**目的**: Git の内部処理レベルでのブロック

```gitattributes
env/.env.*       filter=forbidden
secrets/*.secrets filter=forbidden
*.pem            filter=forbidden
*.key            filter=forbidden
```

Git 設定:

```bash
git config filter.forbidden.clean "echo 'ERROR: このファイルはGitに追加できません' >&2; exit 1"
```

### 第3層: prepare-commit-msg フック

**目的**: コミット準備段階での警告

- env/ や secrets/ のファイル変更を検出
- テンプレートファイルと実設定ファイルを区別して表示

### 第4層: pre-commit フック

**目的**: コミット実行直前の最終チェック

チェック項目:

1. 機密ファイルパターンの検出

   - `env/.env.*` （.example, .template 以外）
   - `secrets/*.secrets`
   - `secrets/gcp-sa*.json`
   - `*.pem`, `*.key`

2. 機密情報パターンの検出
   - `POSTGRES_PASSWORD (パターン検出用)`
   - `-----BEGIN PRIVATE KEY-----`
   - API キーパターン

**エラー時**: コミットを中止し、ファイルを unstage するよう指示

### 第5層: commit-msg フック

**目的**: コミットメッセージ内の機密情報チェック

チェック項目:

- パスワード文字列
- トークン文字列
- API キー
- 秘密鍵
- IP アドレス

**警告時**: ユーザーに確認を求める

### 第6層: pre-push フック

**目的**: リモートプッシュ前の最終防衛線

チェック項目:

1. 機密ファイルの存在（Git 履歴全体）
2. パスワードパターン（全コミット）
3. Git 追跡対象の整合性
4. .gitignore の整合性

**エラー時**: プッシュを中止し、履歴クリーンアップを推奨

### 第7層: GitHub Actions

**目的**: CI/CD パイプラインでの二重チェック

ワークフロー: `.github/workflows/security-check.yml`

チェック項目:

1. 機密ファイルの検出
2. 機密情報パターンのスキャン
3. .gitignore の検証
4. 履歴の変更チェック

**失敗時**: プルリクエストやプッシュをブロック

---

## 🚀 初回セットアップ

### 新規クローン時

```bash
# リポジトリをクローン
git clone https://github.com/torotorokou/sanbou_app.git
cd sanbou_app

# Git フックをセットアップ
bash scripts/setup_git_hooks.sh
```

### 既存リポジトリでの有効化

```bash
# Git フックをセットアップ
bash scripts/setup_git_hooks.sh

# 設定を確認
git config --get filter.forbidden.clean
ls -la .git/hooks/
```

---

## ✅ 動作確認

### テスト 1: .gitignore のテスト

```bash
# env/.env.local_dev を誤って追加しようとする
git add env/.env.local_dev

# 期待結果: .gitignore により無視される
git status  # → env/.env.local_dev は表示されない
```

### テスト 2: pre-commit フックのテスト

```bash
# テスト用ファイルを作成
touch env/.env.test

# 強制的に追加
git add -f env/.env.test
git commit -m "test"

# 期待結果: pre-commit フックがエラーを出す
# ❌ エラー: 機密ファイルを commit しようとしています
#    ファイル: env/.env.test
```

### テスト 3: pre-push フックのテスト

```bash
# 問題のないコミットを作成
git commit --allow-empty -m "test commit"

# プッシュを試みる
git push origin <branch>

# 期待結果: pre-push フックがチェックを実行
# 🚀 Pre-push: リモートプッシュ前の最終セキュリティチェック
# ✅ すべてのセキュリティチェックに合格しました
```

---

## 🚨 エラー対応

### ケース 1: 機密ファイルを誤って add した

```bash
# エラーメッセージ
❌ エラー: 機密ファイルを commit しようとしています
   ファイル: env/.env.vm_prod

# 対処法
git restore --staged env/.env.vm_prod
```

### ケース 2: 機密ファイルを誤ってコミットした

```bash
# 最新のコミットを取り消す
git reset --soft HEAD~1

# ファイルを unstage
git restore --staged env/.env.vm_prod

# 再度コミット
git commit -m "..."
```

### ケース 3: 機密ファイルを誤ってプッシュした

```bash
# ⚠️ 緊急対応が必要です

# 1. Git 履歴から完全削除
bash scripts/cleanup_git_history.sh

# 2. 強制プッシュ
git push origin --force --all

# 3. チームに通知して再クローンを依頼

# 4. 機密情報のローテーション
# - DB パスワード変更
# - GCP 鍵の再発行
# - API キーの再生成
```

---

## 📋 絶対に Git 管理してはいけないファイル

### ❌ 禁止ファイル

```
env/.env.common           # 共通環境変数
env/.env.local_dev        # ローカル開発環境
env/.env.local_demo       # ローカルデモ環境
env/.env.local_stg        # ローカルステージング環境
env/.env.vm_stg          # VM ステージング環境
env/.env.vm_prod         # VM 本番環境 🔴 最重要

secrets/*.secrets         # すべての secrets ファイル
secrets/gcp-sa*.json     # GCP サービスアカウント鍵
*.pem                    # 秘密鍵
*.key                    # 秘密鍵
```

### ✅ 許可ファイル

```
env/.env.example          # 設定項目のテンプレート
env/*.template           # テンプレートファイル
secrets/.env.secrets.template  # secrets のテンプレート
README.md                # ドキュメント
```

---

## 🔧 メンテナンス

### フックの更新

```bash
# 最新のフックを取得
git pull origin main

# 実行権限を再設定
chmod +x .git/hooks/*

# または
bash scripts/setup_git_hooks.sh
```

### フックの一時的な無効化（⚠️ 非推奨）

```bash
# pre-commit をスキップ（非推奨）
git commit --no-verify -m "..."

# ⚠️ セキュリティリスクが高いため、通常は使用しないでください
```

### フックのデバッグ

```bash
# フックの実行テスト
bash .git/hooks/pre-commit

# 詳細ログ
bash -x .git/hooks/pre-commit
```

---

## 🎯 チェックリスト

### 新規メンバーのオンボーディング

- [ ] リポジトリをクローン
- [ ] `scripts/setup_git_hooks.sh` を実行
- [ ] env/.env.example をコピーして実設定ファイルを作成
- [ ] secrets/.env.secrets.template をコピーして実 secrets を作成
- [ ] `git status` で実設定ファイルが追跡されないことを確認
- [ ] テストコミットで pre-commit フックが動作することを確認

### 定期監査（月次）

- [ ] `git log --all --oneline -- 'env/.env.*'` で履歴を確認
- [ ] `git log --all --oneline -- 'secrets/*'` で履歴を確認
- [ ] GitHub Actions のログを確認
- [ ] .gitignore と .gitattributes の整合性確認

---

## 📚 関連ドキュメント

- [セキュリティインシデントレポート](SECURITY_INCIDENT_20251206_ENV_LEAK.md)
- [Git 履歴クリーンアップレポート](GIT_HISTORY_CLEANUP_REPORT_20251206.md)
- [包括的監査レポート](20251206_ENV_SECRETS_LEAK_COMPREHENSIVE_AUDIT.md)
- [セキュリティアクションプラン](SECURITY_ACTION_PLAN_20251206.md)

---

## 🆘 サポート

### 問題が発生した場合

1. **フックが動作しない**

   - `bash scripts/setup_git_hooks.sh` を再実行
   - 実行権限を確認: `ls -la .git/hooks/`

2. **誤って機密ファイルをコミットした**

   - 直ちに `git reset --soft HEAD~1` を実行
   - セキュリティチームに報告

3. **誤って機密ファイルをプッシュした**
   - 直ちにプッシュを停止
   - セキュリティチームに緊急報告
   - [セキュリティアクションプラン](SECURITY_ACTION_PLAN_20251206.md) を参照

---

**最終更新**: 2025-12-06  
**管理者**: システム管理者  
**重要度**: 🔴 最高
