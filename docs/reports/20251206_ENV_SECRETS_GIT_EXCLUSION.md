# ENV/SECRETS Git 管理除外対応 (2025-12-06)

## 問題点

`env/` および `secrets/` ディレクトリ内の実設定ファイルが誤って Git 管理されていました。

### Git 管理されていたファイル (削除対象)
```
env/.env.common           # 共通設定（DB接続情報等を含む）
env/.env.local_dev        # ローカル開発環境設定
env/.env.local_stg        # ローカルステージング設定（廃止済み環境）
env/.env.vm_stg          # VM ステージング設定
env/.env.vm_prod         # ⚠️ VM 本番設定（最も危険）
```

### セキュリティリスク

これらのファイルには以下の機密情報が含まれます:
- データベース接続情報 (`POSTGRES_HOST`, `POSTGRES_USER` 等)
- GCP プロジェクト ID (`GCP_PROJECT_ID`)
- Artifact Registry URL
- 内部 API エンドポイント
- 認証設定 (`AUTH_MODE`, `IAP_AUDIENCE`)

特に `env/.env.vm_prod` が公開されると本番環境への不正アクセスリスクが高まります。

## 根本原因

`.gitignore` の記載が不十分でした:

### Before (問題あり)
```gitignore
# env/ ディレクトリ: 実ファイル除外、example / template のみ許可
env/*
!env/.env.example
!env/*.template
!env/README*
```

**問題**: `env/*` は「env 配下の全ファイル」を意味するため、`env/` ディレクトリ自体が追跡されず、後から追加されたファイルも除外されません。また、`.env.common` のような example/template でないファイルは除外パターンにマッチしませんでした。

### After (修正後)
```gitignore
# env/ ディレクトリ: 全ファイル除外
env/
!env/.env.example
!env/*.template
!env/README.md

# secrets/ ディレクトリ: 全ファイル除外
secrets/
!secrets/.env.secrets.template
!secrets/README.md
```

**修正点**: 
- `env/*` → `env/` (ディレクトリ自体を除外)
- `secrets/*` → `secrets/` (ディレクトリ自体を除外)
- 許可ファイルを明示的に指定 (`!env/.env.example`, `!env/*.template`)

## 実施した対応

### 1. .gitignore の修正

```bash
# .gitignore を更新してディレクトリレベルで除外
```

### 2. Git キャッシュから削除

```bash
git rm --cached env/.env.common
git rm --cached env/.env.local_dev
git rm --cached env/.env.local_stg
git rm --cached env/.env.vm_stg
git rm --cached env/.env.vm_prod
```

**重要**: `--cached` オプションにより、ファイル自体は削除されず、Git 管理のみ解除されます。

### 3. 検証

```bash
$ git check-ignore -v env/.env.common env/.env.vm_prod secrets/.env.vm_prod.secrets
.gitignore:83:env/      env/.env.common
.gitignore:83:env/      env/.env.vm_prod
.gitignore:89:secrets/  secrets/.env.vm_prod.secrets
```

✅ 全ファイルが正しく `.gitignore` で除外されています。

```bash
$ ls env/
.env.common       # ← ファイルは残存（Git 管理外）
.env.example      # ← Git 管理（テンプレート）
.env.local_demo
.env.local_dev
.env.local_stg
.env.vm_prod
.env.vm_stg
```

✅ 実ファイルは削除されず、ローカルで引き続き使用可能です。

## Git 履歴からの完全削除（推奨）

⚠️ **重要**: 今回の対応では「今後の追跡を停止」しただけで、Git 履歴には残っています。

### 履歴から完全削除する場合

```bash
# BFG Repo-Cleaner を使用（推奨）
brew install bfg  # または適切なインストール方法

# 機密ファイルを履歴から削除
bfg --delete-files '.env.common' --no-blob-protection
bfg --delete-files '.env.vm_prod' --no-blob-protection
bfg --delete-files '.env.vm_stg' --no-blob-protection

# 履歴を書き換え
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 強制プッシュ（全ブランチ）
git push origin --force --all
git push origin --force --tags
```

**注意**: 
- チーム全員に履歴変更を通知
- 全員が `git clone` で再取得が必要
- 公開リポジトリの場合、既にクローンした人の履歴には残る

### 代替案: 秘密情報のローテーション

Git 履歴削除が困難な場合:
1. データベースパスワード変更
2. API キー再発行
3. GCP サービスアカウント鍵再生成
4. IAP 設定の見直し

## 今後の運用ルール

### 許可されるファイル（Git 管理対象）
```
env/.env.example          # 設定項目のサンプル
env/*.template            # テンプレートファイル
env/README.md             # ドキュメント

secrets/.env.secrets.template  # secrets のテンプレート
secrets/README.md              # ドキュメント
```

### 禁止ファイル（Git 管理外）
```
env/.env.*                # 全ての実設定ファイル
env/.env.common           # 共通設定
secrets/.env.*.secrets    # 全ての secrets ファイル
```

### 新規環境追加時の手順

1. **テンプレートをコピー**
   ```bash
   cp env/.env.example env/.env.new_env
   cp secrets/.env.secrets.template secrets/.env.new_env.secrets
   ```

2. **実際の値を記入**（Git には追加しない）

3. **誤って追加しないか確認**
   ```bash
   git status  # env/.env.new_env が表示されないこと
   git check-ignore env/.env.new_env  # .gitignore でマッチすること
   ```

### Pre-commit フック（推奨）

`.git/hooks/pre-commit` を作成:
```bash
#!/bin/bash
# env/*.secrets や実設定ファイルの commit を防止

if git diff --cached --name-only | grep -E "^(env/\.env\.|secrets/\.env\..*\.secrets)"; then
    echo "❌ エラー: env/ または secrets/ の実設定ファイルを commit しようとしています"
    echo "許可されるのは .example と .template のみです"
    exit 1
fi
```

```bash
chmod +x .git/hooks/pre-commit
```

## まとめ

✅ `.gitignore` 修正: `env/*` → `env/` でディレクトリレベル除外  
✅ Git キャッシュ削除: 5ファイルを `git rm --cached`  
✅ 実ファイル保持: ローカル環境で引き続き使用可能  
✅ 検証完了: `git check-ignore` で除外確認  
⚠️ Git 履歴削除: 必要に応じて BFG で対応（チーム調整必要）  
📋 運用ルール: テンプレートのみ Git 管理、実設定は全て除外  

次回コミット時、env/ と secrets/ の実設定ファイルは追跡されません。
