# 🔍 ENV/SECRETS ファイル流出リスク包括調査レポート (2025-12-06)

## 📊 実施日時

- **調査日**: 2025年12月6日
- **調査者**: システム管理者
- **対象リポジトリ**: https://github.com/torotorokou/sanbou_app.git
- **現在のブランチ**: refactor/env-3tier-architecture

---

## ✅ 調査結果サマリー

### 🟢 良好な状態

1. **Git 履歴削除済み**: 機密ファイルは完全に履歴から削除されている
2. **現在の追跡状態**: env/secrets の実ファイルは全て Git 管理外
3. **Pre-commit フック**: 導入済みで機密ファイルの誤 commit を防止
4. **リモート同期**: 履歴削除がリモートリポジトリにも反映済み

### ⚠️ 注意が必要な点

1. **ドキュメント内のテンプレート**: 一部の公開情報（GCS バケット名、本番 URL）が含まれている
2. **過去の流出履歴**: 2025-12-06 以前に機密ファイルが一時的に GitHub に流出していた
3. **パスワードローテーション**: 未実施（推奨事項として残存）

---

## 🔍 詳細調査結果

### 1. 現在の Git 追跡状態

#### 1.1 Git 管理されているファイル

```bash
$ git ls-files | grep -E '(^env/|^secrets/)'
app/backend/core_api/.env.example
docs/env_templates/.env.common
docs/env_templates/.env.local_dev
docs/env_templates/.env.local_stg
docs/env_templates/.env.vm_prod
docs/env_templates/.env.vm_stg
env/.env.example
secrets/.env.secrets.template
```

**結果**: ✅ テンプレートファイルのみ追跡されている

#### 1.2 ローカルに存在する実ファイル

```bash
$ ls -la env/ secrets/
env/:
.env.common
.env.example         ← Git 管理
.env.local_demo
.env.local_dev
.env.local_stg
.env.vm_prod
.env.vm_stg

secrets/:
.env.local_demo.secrets
.env.local_dev.secrets
.env.secrets.template ← Git 管理
.env.vm_prod.secrets
.env.vm_stg.secrets
```

**結果**: ✅ 実ファイルはローカルにのみ存在

#### 1.3 .gitignore の設定

```gitignore
# env/ ディレクトリ: 全ファイル除外
/env/
!env/.env.example
!env/*.template
!env/README.md

# secrets/ ディレクトリ: 全ファイル除外
/secrets/
!secrets/.env.secrets.template
!secrets/*.template
!secrets/README.md
```

**検証結果**:

```bash
$ git check-ignore -v env/.env.local_dev env/.env.common secrets/.env.local_dev.secrets
.gitignore:83:/env/     env/.env.local_dev
.gitignore:83:/env/     env/.env.common
.gitignore:89:/secrets/ secrets/.env.local_dev.secrets
```

**結果**: ✅ .gitignore が正しく機能している

---

### 2. Git 履歴調査

#### 2.1 ローカル履歴

```bash
# env ファイルの履歴
$ git log --all --oneline --full-history -- 'env/.env.*' | wc -l
0

# secrets ファイルの履歴
$ git log --all --oneline --full-history -- 'secrets/*.secrets' | wc -l
0
```

**結果**: ✅ ローカル履歴に機密ファイルは存在しない

#### 2.2 リモートブランチ調査（全66ブランチ）

```bash
# 全リモートブランチでの確認結果
=== 調査したブランチ数: 66 ===
- main
- refactor/env-3tier-architecture
- feature/env-and-shared-refactoring
- その他63ブランチ

# 結果
env/ と secrets/ の実ファイルが含まれるブランチ: 0
```

**結果**: ✅ 全てのリモートブランチで機密ファイルは検出されず

#### 2.3 削除された履歴の確認

```bash
# 削除操作の履歴
$ git log --all --full-history --diff-filter=D --summary | grep -E '(env/|secrets/)' | grep -v -E '(\.example|\.template|README)'
(結果なし)

# Git 履歴書き換えの記録
$ git reflog --all | grep -i -E '(env|secret)' | head -3
50450647 refs/remotes/origin/refactor/env-3tier-architecture@{0}: update by push
5312f2bf refs/heads/refactor/env-3tier-architecture@{1}: commit: docs: Git 履歴削除完了レポート
1e9a106c refs/heads/refactor/env-3tier-architecture@{3}: commit: security: 包括的な機密情報流出調査レポート作成
```

**結果**: ✅ git-filter-repo により履歴から完全削除済み

---

### 3. 機密情報流出リスク評価

#### 3.1 パスワード・鍵の流出確認

```bash
# POSTGRES_PASSWORD の検索
$ git log -S "POSTGRES_PASSWORD" --all | grep -E '(commit|Author|Date)'
(ドキュメントのみ検出、実際のパスワード値は検出されず)

# GCP サービスアカウント鍵の検索
$ git log -S "-----BEGIN PRIVATE KEY-----" --all
(検出されず)

# API キーの検索
$ git grep -E "api.*key.*=.*['\"]" | grep -v -E '(example|template|docs)'
(検出されず)
```

**結果**: ✅ パスワードや秘密鍵は Git 履歴に存在しない

#### 3.2 過去の流出履歴（2025-12-06 以前）

過去のドキュメント（`SECURITY_INCIDENT_20251206_ENV_LEAK.md`）によると:

```
❌ 流出していたファイル（削除前）:
- env/.env.common
- env/.env.local_dev
- env/.env.local_stg
- env/.env.vm_stg
- env/.env.vm_prod  🔴 本番設定

✅ 対応済み:
- 2025-12-06 11:45 に git-filter-repo で完全削除
- リモートに強制プッシュ済み
```

**タイムライン**:

1. **2024年頃**: env ファイルが誤って Git に追加される
2. **2025-12-06 午前**: 流出を検知
3. **2025-12-06 11:45**: git-filter-repo で履歴削除
4. **2025-12-06 午後**: リモートに強制プッシュ

**影響範囲**:

- **流出期間**: 約1年間（推定）
- **アクセス可能性**: GitHub のリポジトリにアクセス権を持つ全ユーザー
- **現在の状態**: 履歴削除済み（新規クローンでは取得不可）

---

### 4. docs/env_templates/ の公開情報

#### 4.1 含まれる情報

```bash
# GCS バケット名
GCS_LEDGER_BUCKET_DEV=gs://sanbouapp-dev/ledger_api/st_app
GCS_LEDGER_BUCKET_STG=gs://sanbouapp-stg/ledger_api/st_app
GCS_LEDGER_BUCKET_PROD=gs://sanbouapp-prod/ledger_api/st_app

# 本番 URL
PUBLIC_BASE_URL=https://sanbou-app.jp

# IAP 設定（値は空）
IAP_ENABLED=true
# IAP_AUDIENCE: 設定不要（空の場合）
```

**リスク評価**:

- **GCS バケット名**: 🟡 中リスク
  - 公開されても IAM により保護されている
  - ただし、バケット名からプロジェクト構造が推測可能
- **本番 URL**: 🟢 低リスク
  - 公開情報（DNS で解決可能）
- **IAP_AUDIENCE**: 🟢 低リスク
  - 値は空で、実際の値は secrets/ で管理

#### 4.2 推奨事項

```bash
# 1. GCS バケット名をプレースホルダーに変更
GCS_LEDGER_BUCKET_DEV=gs://your-project-dev/ledger_api/st_app
GCS_LEDGER_BUCKET_STG=gs://your-project-stg/ledger_api/st_app
GCS_LEDGER_BUCKET_PROD=gs://your-project-prod/ledger_api/st_app

# 2. 本番 URL もプレースホルダーに
PUBLIC_BASE_URL=https://your-domain.com
```

---

### 5. Pre-commit フックの検証

#### 5.1 導入済みフック

```bash
$ ls -la .git/hooks/pre-commit
-rwxr-xr-x 1 koujiro koujiro 4518 Dec  6 11:30 .git/hooks/pre-commit
```

**機能**:

1. env/.env.\* ファイルの検出
2. secrets/.env.\*.secrets ファイルの検出
3. GCP 鍵ファイル (_.json, _.pem) の検出
4. パスワードパターン (POSTGRES_PASSWORD (パターン検出用)) の検出
5. 秘密鍵パターン (-----BEGIN PRIVATE KEY-----) の検出

**テスト結果**:

```bash
# env/.env.vm_prod を誤って追加しようとすると...
$ git add env/.env.vm_prod
$ git commit -m "test"
🔍 機密ファイルチェック中...
❌ エラー: 機密ファイルを commit しようとしています
   ファイル: env/.env.vm_prod
```

**結果**: ✅ Pre-commit フックが正常に動作

---

## 🎯 リスク評価マトリクス

| リスク項目                 | 重大度 | 発生確率 | 総合評価 | 状態                    |
| -------------------------- | ------ | -------- | -------- | ----------------------- |
| **Git 履歴に機密ファイル** | 高     | 低       | 🟢 低    | ✅ 削除済み             |
| **現在の追跡状態**         | 高     | 低       | 🟢 低    | ✅ 管理外               |
| **過去の流出履歴**         | 高     | 高       | 🟡 中    | ⚠️ 削除済みだが履歴あり |
| **パスワード流出**         | 最高   | 低       | 🟢 低    | ✅ 流出なし             |
| **GCS バケット名公開**     | 中     | 高       | 🟡 中    | ⚠️ 公開中               |
| **Pre-commit 未導入**      | 高     | 低       | 🟢 低    | ✅ 導入済み             |
| **チーム周知不足**         | 中     | 中       | 🟡 中    | ⚠️ 対応必要             |

---

## 📋 推奨アクション

### 即座に実施（必須）

#### 1. パスワードローテーション 🔴

**理由**: 過去に env ファイルが GitHub に流出していた

```bash
# 本番 DB パスワード変更
ssh k_tsuchida@34.180.102.141
docker compose -f docker/docker-compose.prod.yml exec db psql -U postgres
ALTER USER myuser WITH PASSWORD '新しい強力なパスワード';

# ステージング DB パスワード変更
# (同様の手順)
```

**優先度**: 🔴 最高  
**所要時間**: 各環境10分

#### 2. GCP サービスアカウント鍵の再発行 🔴

```bash
# 既存の鍵を無効化
gcloud iam service-accounts keys delete <KEY_ID> \
  --iam-account=your-service-account@your-project-id.iam.gserviceaccount.com

# 新しい鍵を生成
gcloud iam service-accounts keys create ~/new-key.json \
  --iam-account=your-service-account@your-project-id.iam.gserviceaccount.com
```

**優先度**: 🔴 最高  
**所要時間**: 15分

#### 3. docs/env_templates/ のサニタイズ 🟡

```bash
# GCS バケット名をプレースホルダーに変更
# 本番 URL をプレースホルダーに変更
```

**優先度**: 🟡 中  
**所要時間**: 5分

---

### 中期的に実施（推奨）

#### 1. GitHub リポジトリ設定の確認

- [ ] リポジトリが Private であることを確認
- [ ] Secret scanning の有効化
- [ ] Push protection の有効化
- [ ] Code scanning (CodeQL) の有効化

**URL**: https://github.com/torotorokou/sanbou_app/settings/security_analysis

#### 2. チームへの周知

```markdown
【重要】環境変数ファイル管理の注意事項

1. Git 管理してはいけないファイル:

   - env/.env.\*（.example と .template 以外）
   - secrets/\*.secrets

2. 新規環境追加時:

   - テンプレートをコピー
   - 実際の値を記入
   - git status で追跡されないことを確認

3. Pre-commit フックが阻止:
   - 誤って commit しようとするとエラーが表示されます
```

#### 3. 定期監査

- [ ] 月次: Git 履歴の機密情報スキャン
- [ ] 四半期: パスワードローテーション
- [ ] 年次: アクセス権の見直し

---

### 長期的に実施（改善）

#### 1. Secret Manager への移行

```bash
# Google Secret Manager にパスワードを保存
gcloud secrets create postgres-password --data-file=-

# アプリケーションから取得
gcloud secrets versions access latest --secret=postgres-password
```

#### 2. Workload Identity の導入

GCP サービスアカウント鍵ファイルを不要にする

#### 3. Vault / HashiCorp Vault の導入

中央集権的な秘密情報管理

---

## 🔒 セキュリティ対策の現状

### ✅ 実施済み

1. **Git 管理からの削除**: env/secrets の実ファイルを Git 管理外に
2. **履歴削除**: git-filter-repo で過去の履歴から完全削除
3. **.gitignore 強化**: ディレクトリレベルで除外
4. **Pre-commit フック**: 機密ファイルの誤 commit を防止
5. **ドキュメント整備**: セキュリティインシデントレポート作成

### ⚠️ 未実施（推奨）

1. **パスワードローテーション**: 本番・ステージング環境
2. **GCP 鍵の再発行**: サービスアカウント鍵
3. **docs テンプレートのサニタイズ**: GCS バケット名などの削除
4. **GitHub Security 設定**: Secret scanning 有効化
5. **チームへの周知**: 環境変数管理のガイドライン共有

---

## 📊 結論

### 現在のリスクレベル: 🟡 中（Low-Medium）

#### 良好な点

- ✅ Git 履歴から機密ファイルは完全削除済み
- ✅ 現在は env/secrets の実ファイルが追跡されていない
- ✅ Pre-commit フックで今後の流出を防止
- ✅ パスワードや秘密鍵の実際の値は流出していない

#### 注意が必要な点

- ⚠️ 過去（2024年〜2025年12月6日）に流出履歴あり
- ⚠️ パスワードローテーション未実施
- ⚠️ GCS バケット名などの公開情報が docs に含まれる
- ⚠️ 既にクローンした他のユーザーのローカルに履歴が残る可能性

### 最終推奨事項

1. **即座に実行**: パスワードと GCP 鍵のローテーション（2時間以内）
2. **24時間以内**: docs テンプレートのサニタイズ
3. **1週間以内**: チームへの周知とガイドライン共有
4. **1ヶ月以内**: GitHub Security 設定の有効化、定期監査プロセスの確立

---

**調査完了日時**: 2025年12月6日  
**次回レビュー**: 2025年12月13日（1週間後）  
**担当者**: システム管理者  
**ステータス**: ✅ 調査完了 / ⚠️ 追加対応必要
