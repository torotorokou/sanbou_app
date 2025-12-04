# ドキュメント作成時のセキュリティガイドライン

**作成日**: 2025-12-04  
**対象**: すべてのドキュメント作成者・レビュアー

---

## 📋 目的

このガイドラインは、ドキュメント（特に `docs/` ディレクトリ）内に秘匿情報が誤って記載されることを防ぐためのルールを定めます。

---

## 🚫 禁止事項

### 1. 実際のパスワード・APIキーを記載しない

**NG例:**
```bash
POSTGRES_PASSWORD=mypassword123
DATABASE_URL=postgresql://user:secretpass@host:5432/db
GEMINI_API_KEY=AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz
```

**OK例:**
```bash
POSTGRES_PASSWORD=__SET_IN_SECRETS__
DATABASE_URL=postgresql://<USER>:<PASSWORD>@<HOST>:5432/<DB>
GEMINI_API_KEY=<YOUR_API_KEY>
```

### 2. 本番環境の接続文字列を記載しない

**NG例:**
```yaml
environment:
  DATABASE_URL: postgresql://prod_user:RealP@ssw0rd!@prod-db.example.com:5432/production
```

**OK例:**
```yaml
environment:
  DATABASE_URL: ${DATABASE_URL}  # secrets/ で設定
  # または
  DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5432/${POSTGRES_DB}
```

### 3. GCP サービスアカウントキーの内容を記載しない

**NG:**
- キーの JSON 内容をドキュメントにコピペ
- キーファイルのパスワード保護されていないリンク

**OK:**
- ファイルパスの参照のみ: `secrets/stg_key.json`
- Workload Identity の使用を推奨する記述

---

## ✅ 推奨されるパターン

### パターン1: プレースホルダの使用

```bash
# 環境変数の例
POSTGRES_USER=<YOUR_USERNAME>
POSTGRES_PASSWORD=<STRONG_PASSWORD>
API_KEY=<YOUR_API_KEY>
```

### パターン2: 説明と分離

```bash
# 以下を secrets/.env.local_dev.secrets に設定してください:
# POSTGRES_PASSWORD=<32文字以上のランダム文字列>
# 
# 生成方法:
# openssl rand -base64 32
```

### パターン3: 「例」と明示

```markdown
**パスワード設定例:**
```bash
# 例: 以下は実際の値ではありません
POSTGRES_PASSWORD=Ex@mpl3P@ssw0rd  # ← 実際にはもっと強力なものを
```
```

### パターン4: マスク表示

```markdown
実際のパスワード: `fOb1***[マスク済み]`
APIキー: `AIza****[35文字マスク]****xyz`
```

---

## 📝 ドキュメント作成チェックリスト

新しいドキュメントを作成・更新する際は、以下を確認してください:

- [ ] パスワード・APIキーは `<PLACEHOLDER>` 形式で記載
- [ ] 実際の接続文字列は含まれていない
- [ ] 環境変数は `${VAR_NAME}` または `__SET_IN_SECRETS__` 形式
- [ ] 例示する場合は「例:」「サンプル」と明記
- [ ] 本番環境の情報は一切含まれていない
- [ ] `secrets/` ディレクトリへの参照のみ
- [ ] Pre-commit フックでチェック済み

---

## 🔍 レビュー時のチェックポイント

コードレビュー時は以下を確認:

### 高リスク (即座に修正)
- [ ] 実際のパスワードが平文で記載されていないか
- [ ] 本番環境の接続情報が含まれていないか
- [ ] APIキーが生で記載されていないか

### 中リスク (修正推奨)
- [ ] デフォルト値として弱いパスワードが設定されていないか
- [ ] 環境変数のフォールバックにハードコード値がないか
- [ ] Docker Compose ファイルに直接パスワードが書かれていないか

### 低リスク (改善提案)
- [ ] プレースホルダが一貫しているか
- [ ] 設定方法の説明が適切か
- [ ] セキュリティのベストプラクティスに従っているか

---

## 🛠 ツールの活用

### Pre-commit フック

以下のコマンドで Pre-commit フックをセットアップ:

```bash
# インストール (初回のみ)
pip install pre-commit

# セットアップ
pre-commit install

# 手動実行
pre-commit run --all-files
```

### 定期監査

月1回、以下のコマンドで秘匿情報をチェック:

```bash
# docs/ 内のパスワードパターン検索
grep -r -i -E "(password|secret|token|api_key)[:=]\s*[\"'][^$<{][^\"']+[\"']" docs/ \
  --include="*.md" --include="*.yml" --exclude-dir=archive

# 疑わしい文字列パターン検索
grep -r -E "[A-Za-z0-9+/]{40,}={0,2}" docs/ --include="*.md"
```

---

## 📚 参考資料

### 安全なパスワード生成

```bash
# 32文字のランダム文字列
openssl rand -base64 32

# 64文字のランダム文字列 (より強力)
openssl rand -base64 48
```

### 環境変数の優先順位

1. `secrets/.env.*.secrets` (Git管理外、最優先)
2. `env/.env.*` (環境固有、Git管理)
3. `env/.env.common` (全環境共通、Git管理)

### 関連ドキュメント

- [20251203_SECURITY_AUDIT_REPORT.md](../20251203_SECURITY_AUDIT_REPORT.md)
- [20251204_ENV_HARDCODE_AUDIT.md](../20251204_ENV_HARDCODE_AUDIT.md)
- [db/20251204_db_user_design.md](../db/20251204_db_user_design.md)

---

## 🚨 インシデント対応

もし秘匿情報がコミットされてしまった場合:

1. **即座に対応**: そのクレデンシャルを無効化・変更
2. **Git履歴から削除**: `git filter-branch` または BFG Repo-Cleaner を使用
3. **影響範囲の確認**: そのクレデンシャルがどこで使われていたか特定
4. **再発防止**: Pre-commit フックが正しく動作しているか確認
5. **報告**: チームリーダーに状況を報告

---

**最終更新**: 2025-12-04
