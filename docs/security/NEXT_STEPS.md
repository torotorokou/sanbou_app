# 次のステップ（優先順位順）

## 🔴 最優先（今すぐ実施）

### 1. ローカル統合テスト

```bash
# ブランチ確認
git branch

# コンテナを再ビルド
docker compose -f docker/docker-compose.dev.yml build

# 起動
docker compose -f docker/docker-compose.dev.yml up -d

# ヘルスチェック（各サービスのポート確認）
curl http://localhost:8000/health  # core_api
curl http://localhost:8001/health  # rag_api
curl http://localhost:8002/health  # ledger_api
curl http://localhost:8003/health  # manual_api
curl http://localhost:8004/health  # ai_api

# ログ確認（エラーがないか）
docker compose -f docker/docker-compose.dev.yml logs -f --tail=50

# 動作確認後、停止
docker compose -f docker/docker-compose.dev.yml down
```

**期待される結果:**

- ✅ すべてのサービスが正常起動
- ✅ ヘルスチェックが200 OKを返す
- ✅ エラーログがない

---

## 🟡 高優先（今日中に実施）

### 2. Pull Request作成

```bash
# GitHubのPRページを開く
open https://github.com/torotorokou/sanbou_app/pull/new/security/fix-vulnerabilities-2025-12
```

**PRテンプレート使用:**

- タイトル: `security: Fix CVE vulnerabilities in Python dependencies (Dec 2025)`
- 本文: `.github/PULL_REQUEST_TEMPLATE_SECURITY.md` の内容をコピー
- ラベル: `security`, `dependencies`, `docker`
- レビュアー: チームメンバーをアサイン

### 3. CI/CDパイプライン確認

- GitHub Actionsが自動実行されることを確認
- テストが全て通ることを確認
- ビルドエラーがないことを確認

---

## 🟢 中優先（今週中に実施）

### 4. ステージング環境（vm_stg）でのテスト

PRマージ後:

```bash
# VM_STGにログイン
ssh your-stg-vm

# リポジトリ更新
cd /path/to/sanbou_app
git pull origin main  # またはマージされたブランチ

# コンテナ再ビルド
docker compose -f docker/docker-compose.vm_stg.yml down
docker compose -f docker/docker-compose.vm_stg.yml build --no-cache
docker compose -f docker/docker-compose.vm_stg.yml up -d

# ヘルスチェック
curl http://localhost:8000/health

# E2Eテスト実行（可能であれば）
```

### 5. Artifact Registryでの再スキャン

```bash
# イメージをビルド & プッシュ（本番用）
docker compose -f docker/docker-compose.prod.yml build
docker tag [IMAGE] [REGISTRY]/core_api:latest
docker push [REGISTRY]/core_api:latest
# ... 他のサービスも同様

# GCP Console → Artifact Registry → イメージ選択 → Vulnerabilities タブ
# Python依存関係のCVEが解消されていることを確認
```

**期待される結果:**

- ✅ CVE-2025-62727（high）→ 解消
- ✅ CVE-2025-54121（medium）→ 解消
- ✅ CVE-2024-47081（medium）→ 解消
- ✅ CVE-2025-8869（medium）→ 解消
- ✅ langchain系CVE → 解消

---

## 🔵 低優先（来週以降に実施）

### 6. 本番環境（vm_prod）へのデプロイ

ステージング環境で十分なテスト後:

```bash
# 本番環境デプロイ
# 既存のCI/CDパイプラインに従う
```

### 7. ドキュメントの更新

- [ ] `docs/security/` に今回の対応をアーカイブ
- [ ] `docs/infrastructure/` にセキュリティ方針を追加
- [ ] チームWikiにナレッジ共有

### 8. 自動化の改善

#### 8.1 Dependabot設定

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/app/backend/core_api"
    schedule:
      interval: "weekly"
  - package-ecosystem: "docker"
    directory: "/app/backend/core_api"
    schedule:
      interval: "weekly"
```

#### 8.2 セキュリティスキャンをCI/CDに組み込み

```yaml
# .github/workflows/security-scan.yml
name: Security Scan
on: [push, pull_request]
jobs:
  trivy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          scan-ref: "."
          format: "sarif"
          output: "trivy-results.sarif"
```

### 9. ベースイメージの固定化検討

現在: `python:3.12-slim` (latest patch)
提案: `python:3.12.8-slim` (特定バージョン固定)

**メリット:**

- 再現性の向上
- 予期しないbreaking changeを防ぐ

**デメリット:**

- セキュリティパッチの自動適用がされない
- 定期的な手動更新が必要

**推奨アプローチ:**

- 開発環境: latest patch（現状維持）
- 本番環境: 特定バージョン固定 + 月次更新

---

## 📋 チェックリスト（進捗管理用）

### Phase 1: テストとレビュー（今日）

- [x] ローカルビルドテスト（wheelbuilder）✅
- [x] 依存関係整合性チェック ✅
- [x] GitHubへプッシュ ✅
- [x] PRテンプレート作成 ✅
- [ ] ローカル統合テスト
- [ ] Pull Request作成
- [ ] コードレビュー依頼

### Phase 2: 統合とデプロイ（今週）

- [ ] PR承認 & マージ
- [ ] vm_stg でのテスト
- [ ] Artifact Registry再スキャン
- [ ] 脆弱性解消確認

### Phase 3: 本番とドキュメント（来週）

- [ ] vm_prod デプロイ
- [ ] 本番動作確認
- [ ] ドキュメント更新
- [ ] チームへの共有

### Phase 4: 継続的改善（今月）

- [ ] Dependabot設定
- [ ] CI/CDにセキュリティスキャン追加
- [ ] ベースイメージ戦略の確立
- [ ] 定期更新プロセスの文書化

---

## 🚨 トラブルシューティング

### 問題1: コンテナが起動しない

```bash
# ログ確認
docker compose logs [service_name]

# イメージ再ビルド（キャッシュなし）
docker compose build --no-cache [service_name]

# ネットワーク問題の場合
docker network prune
docker compose down && docker compose up -d
```

### 問題2: 依存関係の競合

```bash
# requirements.txtの依存関係ツリー確認
pip install pipdeptree
pipdeptree -p fastapi -p starlette -p langchain-core
```

### 問題3: ヘルスチェック失敗

```bash
# サービス内部から確認
docker compose exec core_api curl http://localhost:8000/health

# 環境変数確認
docker compose exec core_api env | grep -E "(AUTH_MODE|DB|DEBUG)"
```

---

**次のアクション**: まず「Phase 1」のローカル統合テストを実施してください。
