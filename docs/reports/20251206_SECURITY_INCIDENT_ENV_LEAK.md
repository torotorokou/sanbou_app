# 🚨 環境変数ファイル Git 流出調査レポート (2025-12-06)

## ❌ 流出状況: YES - GitHub に流出済み

### 流出したファイル

以下のファイルが GitHub リポジトリ (`https://github.com/torotorokou/sanbou_app.git`) の履歴に含まれています:

```
env/.env.common          # 共通設定（DB接続情報等）
env/.env.local_dev       # ローカル開発環境設定
env/.env.local_stg       # ローカルステージング設定
env/.env.vm_stg         # ⚠️ VM ステージング設定
env/.env.vm_prod        # 🔴 VM 本番設定（最も危険）
```

### 流出した Commit

#### 本番環境設定 (env/.env.vm_prod) の履歴

```
618116b9 - refactor: POSTGRES_USERをenvファイルに移行
54f03b3d - refactor: 環境変数と Docker Compose ファイルの同期・整理
348e2616 - refactor: Remove all hardcoded database credentials from code
ab307d2d - feat(security): DBユーザー分離・パスワード強化対応
```

#### すべての env ファイルの最新 commit

```
618116b9 (2025年頃) - refactor: POSTGRES_USERをenvファイルに移行
  ├─ env/.env.common
  ├─ env/.env.local_dev
  ├─ env/.env.local_stg
  ├─ env/.env.vm_prod  🔴
  └─ env/.env.vm_stg   ⚠️
```

### 影響範囲

1. **リモートブランチ**: origin/main に含まれている
2. **公開範囲**: GitHub の public/private に依存（要確認）
3. **アクセス履歴**: GitHub の commit 履歴から閲覧可能
4. **クローン済み**: 他の開発者がクローン済みの場合、各自のローカルに残存

### 含まれる機密情報（推定）

```bash
# 本番環境 (env/.env.vm_prod) に含まれると推定される情報:
- POSTGRES_HOST (本番 DB ホスト)
- POSTGRES_PORT
- POSTGRES_USER
- POSTGRES_PASSWORD  🔴
- POSTGRES_DB
- GCP_PROJECT_ID (本番 GCP プロジェクト)
- IAP_AUDIENCE (IAP 認証設定)
- ARTIFACT_REGISTRY_URL
- 内部 API エンドポイント
```

## 🛠️ 実施した緊急対応

### 1. Git 管理からの完全削除

```bash
# env/ と secrets/ ディレクトリ全体を Git 管理から削除
git rm --cached -r env/ secrets/

# テンプレートファイルのみ明示的に追加
git add -f env/.env.example
git add -f secrets/.env.secrets.template
```

### 2. 削除されたファイル

```
D  env/.env.common
D  env/.env.local_dev
D  env/.env.local_stg
D  env/.env.vm_prod       🔴 本番設定
D  env/.env.vm_stg        ⚠️ ステージング設定
```

### 3. Git 管理されるファイル（最終状態）

```
env/.env.example              ✅ テンプレートのみ
secrets/.env.secrets.template ✅ テンプレートのみ
```

### 4. ローカルファイル保持

実ファイルは削除されず、ローカルで引き続き使用可能:

```
env/.env.common          # 使用可能
env/.env.local_dev       # 使用可能
env/.env.vm_prod         # 使用可能
env/.env.vm_stg          # 使用可能
secrets/*.secrets        # 使用可能
```

## 🔥 必須の追加対応

### 即座に実施すべき対応

#### 1. 本番環境の認証情報ローテーション 🔴

```bash
# PostgreSQL パスワード変更（本番 DB）
psql -h <本番DBホスト> -U postgres
ALTER USER myuser WITH PASSWORD '新しい強力なパスワード';

# 変更後、env/.env.vm_prod と secrets/.env.vm_prod.secrets を更新
```

#### 2. GCP サービスアカウント鍵の再発行

```bash
# 既存の鍵を無効化
gcloud iam service-accounts keys list --iam-account=<SA_EMAIL>
gcloud iam service-accounts keys delete <KEY_ID> --iam-account=<SA_EMAIL>

# 新しい鍵を発行
gcloud iam service-accounts keys create new-key.json --iam-account=<SA_EMAIL>
```

#### 3. IAP 設定の確認

```bash
# IAP_AUDIENCE が流出している場合、OAuth クライアント ID を再生成
gcloud iap oauth-clients list
```

#### 4. Git 履歴からの完全削除（推奨）

```bash
# BFG Repo-Cleaner を使用
brew install bfg

# 機密ファイルを履歴から完全削除
bfg --delete-files '.env.common' --no-blob-protection
bfg --delete-files '.env.vm_prod' --no-blob-protection
bfg --delete-files '.env.vm_stg' --no-blob-protection
bfg --delete-files '.env.local_dev' --no-blob-protection
bfg --delete-files '.env.local_stg' --no-blob-protection

# 履歴を書き換え
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 強制プッシュ（⚠️ チーム全員に通知必要）
git push origin --force --all
git push origin --force --tags
```

**注意事項**:

- チーム全員に履歴変更を通知し、再クローンを依頼
- 既にクローンした外部の人がいる場合、履歴削除は無効
- GitHub の Settings → Actions → General で "Allow GitHub Actions to create and approve pull requests" を無効化（誤った自動 commit 防止）

#### 5. GitHub リポジトリの可視性確認

```bash
# リポジトリが public か private か確認
# https://github.com/torotorokou/sanbou_app/settings

# もし public の場合:
# - 即座に private に変更
# - GitHub Security → Secret scanning alerts を有効化
```

### 中期的な対応

#### 1. Secrets 管理の改善

```bash
# Google Secret Manager への移行
gcloud secrets create postgres-password --data-file=- <<< "password"
gcloud secrets create iap-audience --data-file=- <<< "audience"

# アプリケーションから取得
gcloud secrets versions access latest --secret=postgres-password
```

#### 2. Pre-commit フック導入

`.git/hooks/pre-commit`:

```bash
#!/bin/bash
if git diff --cached --name-only | grep -qE "^(env/\.env\.|secrets/)"; then
    echo "❌ env/ または secrets/ の実設定ファイルを commit しようとしています"
    exit 1
fi
```

```bash
chmod +x .git/hooks/pre-commit
```

#### 3. GitHub Advanced Security 有効化

- Secret scanning
- Code scanning (CodeQL)
- Dependency review

## ✅ 対応完了チェックリスト

### 即座に実施（必須）

- [x] Git 管理から env/secrets の実ファイルを削除
- [x] .gitignore で env/ と secrets/ を完全除外
- [x] テンプレートのみ Git 管理対象に
- [ ] 🔴 本番 DB パスワードのローテーション
- [ ] 🔴 GCP サービスアカウント鍵の再発行
- [ ] ⚠️ IAP OAuth クライアント ID の確認
- [ ] リポジトリの可視性確認（public → private）

### 中期的に実施（推奨）

- [ ] Git 履歴からの完全削除（BFG）
- [ ] チーム全員への通知と再クローン依頼
- [ ] Google Secret Manager への移行
- [ ] Pre-commit フック導入
- [ ] GitHub Advanced Security 有効化

### 長期的に実施（改善）

- [ ] 定期的な認証情報ローテーション（90日ごと）
- [ ] アクセスログ監視
- [ ] 異常検知アラート設定

## 📊 影響評価

### リスクレベル: 🔴 HIGH

- **本番環境への不正アクセスリスク**: あり
- **データ漏洩リスク**: あり
- **サービス停止リスク**: あり（攻撃者が DB を削除/改ざん）

### 対応優先度

1. **最優先**: 本番 DB パスワード変更
2. **高**: GCP 鍵の再発行、リポジトリ可視性確認
3. **中**: Git 履歴削除
4. **低**: Secret Manager 移行、フック導入

## 📝 今後の運用ルール

### 絶対に Git 管理してはいけないファイル

```
env/.env.*               # すべての実設定ファイル
secrets/*.secrets        # すべての secrets ファイル
*.key, *.pem            # 秘密鍵
gcp-sa.json             # GCP サービスアカウント鍵
```

### Git 管理するファイル

```
env/.env.example         # 設定項目のテンプレート
secrets/.env.secrets.template  # secrets のテンプレート
README.md               # ドキュメント
```

### 新規環境追加時

1. テンプレートをコピー
2. 実際の値を記入（Git には追加しない）
3. `git status` で確認（表示されないこと）
4. `git check-ignore` で除外されることを確認

## まとめ

- ❌ **env/.env.vm_prod** を含む機密ファイルが GitHub に流出済み
- ✅ Git 管理から削除完了（今後の追跡は停止）
- 🔴 **即座に本番 DB パスワードと GCP 鍵のローテーション必須**
- ⚠️ Git 履歴には残存（BFG での削除推奨）
- 📋 今後は env/.env.example と secrets/.env.secrets.template のみ Git 管理

**次のアクション**: 本番環境の認証情報を即座にローテーションしてください。
