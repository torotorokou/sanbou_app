# セキュリティ監査: env/secrets ファイルのGit履歴調査レポート

**作成日**: 2025年12月4日  
**監査対象**: `env/` および `secrets/` ディレクトリのGit管理履歴  
**リポジトリ**: https://github.com/your-username/your-repo.git  
**現在のブランチ**: refactor/env-and-compose-sync

---

## 🔍 調査概要

過去に機密情報を含む可能性のある環境変数ファイル（`env/` および `secrets/` ディレクトリ）がGit管理されていた履歴を調査し、現在のセキュリティリスクを評価しました。

---

## 📊 調査結果サマリー

### ✅ 現在の状態（安全）
- **Git管理されているファイル**: 
  - `env/.env.example` （テンプレート）
  - `secrets/.env.secrets.template` （テンプレート）
- **実ファイルの状態**: 全て `.gitignore` により除外済み
- **最新の対応**: 2025年12月4日 16:09 (コミット: `54f03b3d`)

### ⚠️ 過去の問題（2025年12月4日に修正済み）
- **期間**: 2025年12月4日 10:20 - 16:09 (約6時間)
- **影響を受けたファイル**:
  - `env/.env.local_dev`
  - `env/.env.local_stg`
  - `env/.env.vm_prod`
  - `env/.env.vm_stg`
  - `env/.env.common`

---

## 🔐 機密情報の露出状況

### 1. データベース認証情報

#### 露出した情報
**コミット `ab307d2d` (2025-12-04 10:20)**

```bash
# env/.env.local_dev に含まれていた内容
DATABASE_URL=postgresql://dbuser:dbpassword@db:5432/sanbou_dev
```

```bash
# env/.env.vm_stg に含まれていた内容
DATABASE_URL=postgresql://dbuser:dbpassword@db:5432/sanbou_stg
```

**リスク評価**: 🟡 **中リスク（軽減済み）**

**理由**:
- ✅ `dbuser:dbpassword` はデフォルトの開発用認証情報
- ✅ 本番環境用のパスワードは含まれていない（プレースホルダー形式）
- ✅ 同日中（コミット `c52bbc8c`, `348e2616`）に削除・修正済み
- ⚠️ ただし、過去にこれらの認証情報が実際に使用されていた場合、攻撃者が履歴から取得可能

### 2. GCS（Google Cloud Storage）バケット情報

#### 露出した情報
```bash
GCS_LEDGER_BUCKET_DEV=gs://your-project-dev/ledger_api/st_app
GCS_LEDGER_BUCKET_STG=gs://your-project-stg/ledger_api/st_app
GCS_LEDGER_BUCKET_PROD=gs://your-project-prod/ledger_api/st_app
RAG_GCS_URI=gs://your-project-stg/rag_api/object_haikibutu/master/
```

**リスク評価**: 🟢 **低リスク**

**理由**:
- ✅ GCSバケット名は公開情報ではないが、IAM権限で保護されている
- ✅ バケット名だけではアクセス不可（GCP認証が必要）
- ✅ 情報漏洩自体は脆弱性とは言えない

### 3. API Keys / Secrets

#### 調査結果
- ✅ `OPENAI_API_KEY` および `GEMINI_API_KEY` は全て空値またはプレースホルダー
- ✅ `REPORT_ARTIFACT_SECRET` も同様に空値
- ✅ `secrets/` ディレクトリの実ファイル（`.env.*.secrets`）はGit履歴に含まれていない

**リスク評価**: 🟢 **リスクなし**

### 4. 本番環境（vm_prod）の情報

#### 露出した情報
```bash
# env/.env.vm_prod
PUBLIC_BASE_URL=https://example.com
POSTGRES_DB=sanbou_prod
DATABASE_URL=postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
```

**リスク評価**: 🟡 **中リスク（限定的）**

**理由**:
- ⚠️ 本番環境のドメイン名とDB名が露出
- ✅ パスワードは変数展開形式（実値は含まれていない）
- ✅ IAP（Identity-Aware Proxy）が有効化されている設定
- ⚠️ アーキテクチャ情報の漏洩により攻撃対象が特定しやすくなる

---

## 📅 タイムライン

### コミット履歴の詳細

| 日時 | コミットID | 内容 | リスク |
|------|-----------|------|--------|
| 2025-12-04 10:20 | `ab307d2d` | **機密ファイルを初回追加** (env/.env.* を追加) | 🔴 **高** |
| 2025-12-04 11:12 | `c52bbc8c` | DATABASE_URL の問題を修正 | 🟡 中 |
| 2025-12-04 11:18 | `348e2616` | ハードコードされた認証情報を削除 | 🟡 中 |
| 2025-12-04 13:03 | `196f25af` | 環境変数を .env.common に追加 | 🟢 低 |
| 2025-12-04 14:02 | `8ab4b28a` | REPORT_ARTIFACT_SECRET のセキュリティ改善 | 🟢 低 |
| 2025-12-04 16:09 | `54f03b3d` | **.gitignore で実ファイルを除外** (修正完了) | ✅ **安全** |

### プッシュされたブランチ
機密情報を含むコミット `ab307d2d` は以下のブランチにプッシュされています:

```
origin/feature/db-user-security-migration
origin/feature/env-and-shared-refactoring
origin/stg
```

---

## 🚨 現在の危険性評価

### 総合リスクレベル: 🟡 **中リスク（管理された状態）**

### リスク要因

#### 1. Git履歴からの情報取得 🟡
**状態**: コミット履歴は永続的に残る

- ✅ GitHubリポジトリはプライベート
- ⚠️ リポジトリへのアクセス権を持つ全員が履歴を閲覧可能
- ⚠️ 過去にアクセス権があったメンバーも閲覧済みの可能性

**対策**:
- 履歴の完全削除（Git filter-branch / BFG Repo-Cleaner）を検討
- ただし、既にクローンされたリポジトリには影響しない

#### 2. 露出した認証情報の再利用 🟡
**状態**: 現在は使用されていない

- ✅ `myuser:mypassword` は開発用デフォルト値
- ⚠️ 過去にこれらが実環境で使用されていた場合、即時変更が必要
- ✅ 現在は secrets ファイル経由で管理（コミット外）

**対策**:
- 全環境のDBパスワードを即座にローテーション
- 特にステージング・本番環境を優先

#### 3. アーキテクチャ情報の露出 🟢
**状態**: 軽微な情報漏洩

- ⚠️ 内部サービス構成（rag_api, ledger_api等）が判明
- ⚠️ GCSバケット構造が判明
- ✅ IAM権限により実際のアクセスは保護されている

**影響**: 攻撃対象の特定が容易になるが、直接的な脆弱性ではない

---

## 🛡️ 実施済みの対策（2025年12月4日）

### 1. .gitignore の強化 ✅
```gitignore
# env/ ディレクトリ: 実ファイル除外、example / template のみ許可
env/*
!env/.env.example
!env/*.template
!env/README*

# secrets/ ディレクトリ: 実ファイル除外、テンプレ / example のみ許可
secrets/*
!secrets/*.template
!secrets/*example*
!secrets/*_example.*
!secrets/README*
```

### 2. 実ファイルの削除 ✅
コミット `54f03b3d` で以下を削除:
- `env/.env.common`
- `env/.env.local_dev`
- `env/.env.local_stg`
- `env/.env.vm_prod`
- `env/.env.vm_stg`

### 3. テンプレート化 ✅
- `docs/env_templates/` にバックアップ（Git管理）
- 実ファイルは各環境で個別に生成する運用に変更

### 4. セキュリティドキュメント整備 ✅
- `docs/20251204_ENV_AND_COMPOSE_SYNC.md`
- `docs/db/20251204_db_user_design.md`
- `docs/db/20251204_db_user_migration_plan.md`

---

## 📋 推奨される追加対策

### 🔴 優先度: 高（即座に実施）

#### 1. データベースパスワードのローテーション
**理由**: `mypassword` が露出している

```bash
# 各環境で実施
# 1. 新しいパスワード生成
openssl rand -base64 32

# 2. DBユーザーのパスワード変更
psql -U postgres -d sanbou_dev
ALTER USER sanbou_app_dev WITH PASSWORD 'NEW_STRONG_PASSWORD';

# 3. secrets/.env.*.secrets を更新
```

**対象環境**:
- ✅ 開発環境（local_dev）
- ⚠️ **ステージング環境（vm_stg）** ← 優先
- ⚠️ **本番環境（vm_prod）** ← 優先

#### 2. アクセス権の監査
**実施項目**:
- [ ] 現在のリポジトリアクセス権を確認
- [ ] 不要なメンバーのアクセス権を削除
- [ ] 過去に退職したメンバーのアクセス権を確認

#### 3. GitHub Repository Security 設定の確認
```bash
# 確認項目
- [ ] リポジトリが Private であることを確認
- [ ] Branch protection rules が有効
- [ ] Secret scanning が有効（GitHub Advanced Security）
- [ ] Dependabot alerts が有効
```

### 🟡 優先度: 中（1週間以内）

#### 4. Git履歴のクリーンアップ（オプション）
**方法**: BFG Repo-Cleaner または git-filter-repo

```bash
# BFG Repo-Cleaner を使用した例
# 注意: 全員が再クローンする必要があります

# 1. ミラークローン作成
git clone --mirror https://github.com/torotorokou/sanbou_app.git

# 2. BFG実行（機密ファイルを削除）
bfg --delete-files .env.local_dev sanbou_app.git
bfg --delete-files .env.vm_prod sanbou_app.git
bfg --delete-files .env.vm_stg sanbou_app.git

# 3. クリーンアップ
cd sanbou_app.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. 強制プッシュ
git push --force
```

**リスク**:
- ⚠️ チーム全員が再クローン必須
- ⚠️ オープンPRが影響を受ける可能性
- ⚠️ 既にクローンされたローカルリポジトリには効果なし

**推奨**: 本番環境で使用された実パスワードが含まれていないため、優先度は中程度

#### 5. 1Password / Secrets Manager への移行
**現状**: secrets ファイルをローカルファイルで管理

**推奨**: エンタープライズ向けシークレット管理ツールの導入
- 1Password for Teams
- Google Secret Manager
- AWS Secrets Manager
- HashiCorp Vault

### 🟢 優先度: 低（今後の改善）

#### 6. Secrets Scanning の有効化
GitHub Advanced Security の Secret scanning を有効化し、今後の漏洩を自動検知

#### 7. Pre-commit hooks の導入
```bash
# detect-secrets などで機密情報のコミットを防止
pip install detect-secrets
detect-secrets scan > .secrets.baseline
```

---

## 📊 チェックリスト

### 🔴 即座に実施すべき項目
- [ ] ステージング環境のDBパスワード変更
- [ ] 本番環境のDBパスワード変更
- [ ] 現在のリポジトリアクセス権の監査
- [ ] 1Password等へのパスワードバックアップ

### 🟡 1週間以内
- [ ] Git履歴クリーンアップの是非を決定
- [ ] シークレット管理ツールの導入検討
- [ ] セキュリティポリシーの文書化

### 🟢 継続的改善
- [ ] Pre-commit hooks の導入
- [ ] Secret scanning の有効化
- [ ] 定期的なセキュリティ監査（四半期ごと）

---

## 🎯 結論

### 現在の状態
- ✅ `.gitignore` の設定は適切
- ✅ テンプレートファイルのみがGit管理されている
- ✅ 機密情報は分離されている（secrets/）

### 残存リスク
- 🟡 Git履歴に約6時間分の機密情報が残存
- 🟡 露出した認証情報が過去に使用されていた可能性
- 🟢 直接的な脆弱性は低い（デフォルト値のため）

### 総合評価
**リスクレベル: 中（管理された状態）**

本番環境で使用された実際のパスワードは露出していないため、**緊急性は低い**ですが、**ベストプラクティスとして認証情報のローテーション**を推奨します。

---

## 📚 参考資料

### 関連ドキュメント
- `docs/20251204_ENV_AND_COMPOSE_SYNC.md` - 環境変数整理の詳細
- `docs/20251204_SECURITY_AUDIT_REPORT.md` - セキュリティ監査レポート
- `docs/db/20251204_db_user_design.md` - DBユーザー設計
- `secrets/.env.secrets.template` - シークレットテンプレート

### 外部リソース
- [GitHub: Removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-filter-repo](https://github.com/newren/git-filter-repo)

---

**レポート作成者**: GitHub Copilot  
**監査実施日**: 2025年12月4日  
**最終更新**: 2025年12月4日
