## 🔒 セキュリティ修正 PR

### 概要

Artifact Registry のコンテナイメージスキャンで検出されたPython依存関係の脆弱性を修正しました。

### 修正した主要CVE

| CVE            | 重大度   | パッケージ               | 対応                        |
| -------------- | -------- | ------------------------ | --------------------------- |
| CVE-2025-62727 | 高 (7.5) | starlette                | ✅ FastAPI >=0.115.7 に更新 |
| CVE-2025-54121 | 中 (5.3) | starlette                | ✅ FastAPI >=0.115.7 に更新 |
| CVE-2024-47081 | 中 (5.3) | requests                 | ✅ requests >=2.32.4 に更新 |
| CVE-2025-8869  | 中       | pip                      | ✅ Dockerfileでpip最新化    |
| CVE-2025-6985  | 高       | langchain-text-splitters | ✅ >=0.3.4 に更新           |
| CVE-2025-65106 | 高       | langchain-core           | ✅ >=0.3.28 に更新          |
| CVE-2025-6984  | 高       | langchain-community      | ✅ >=0.3.14 に更新          |

### 変更内容

**1. Python依存関係（6サービス）**

- ✅ core_api: FastAPI, requests更新
- ✅ rag_api: FastAPI, langchain系更新
- ✅ ledger_api: FastAPI更新
- ✅ manual_api: FastAPI更新
- ✅ ai_api: FastAPI, requests更新
- ⏭️ plan_worker: FastAPI未使用のため変更なし

**2. Dockerfile修正（全6サービス）**

- ✅ `apt-get upgrade -y` 追加（OSパッケージのセキュリティ更新）
- ✅ `python -m pip install --upgrade pip` 追加（CVE-2025-8869対応）
- ✅ セキュリティコメント追加

**3. ドキュメント**

- ✅ `docs/security/CVE-2025-fixes-summary.md` - 詳細な変更サマリー
- ✅ `README.md` - セキュリティ更新の通知追加

### テスト状況

- [x] 構文エラーチェック（VSCode + linters）
- [x] Dockerfile構文検証（hadolint）
- [x] Dockerビルドテスト（wheelbuilderステージ）
- [x] 依存関係整合性チェック（pip dry-run）
- [ ] ローカル統合テスト（docker-compose.dev.yml）
- [ ] ヘルスチェック確認（全サービス）
- [ ] ユニットテスト実行
- [ ] Artifact Registryでの脆弱性再スキャン

### 互換性への影響

**✅ 後方互換性あり**

- FastAPI: 0.115.6 → >=0.115.7（マイナーバージョンアップ）
- requests: 2.32.3 → >=2.32.4（パッチバージョンアップ）
- langchain系: マイナーバージョンアップ

**🔒 Clean Architectureへの影響なし**

- ドメインロジック、ユースケース、インフラ層、API層に変更なし
- 外部ライブラリのバージョン更新のみ

### 残存する脆弱性

以下のOS パッケージは現時点で修正パッチなし（ベンダー対応待ち）:

- glibc, systemd, tar, krb5, openldap, curl, sqlite3等

**対応策:**

- ビルド時に `apt-get upgrade` で最新パッチ適用
- ベースイメージ（python:3.12-slim）の定期再ビルド

### デプロイ手順

1. **マージ後、local_devで確認**

   ```bash
   git pull origin main
   docker compose -f docker/docker-compose.dev.yml build
   docker compose -f docker/docker-compose.dev.yml up -d
   ```

2. **ヘルスチェック**

   ```bash
   curl http://localhost:8000/health  # core_api
   curl http://localhost:8001/health  # rag_api
   # ... 他のサービスも同様
   ```

3. **問題なければvm_stg、vm_prodへデプロイ**

### ロールバック手順

万が一問題が発生した場合:

```bash
git checkout refactor/env-3tier-architecture
docker compose -f docker/docker-compose.dev.yml down
docker compose -f docker/docker-compose.dev.yml build
docker compose -f docker/docker-compose.dev.yml up -d
```

### チェックリスト

- [x] コードレビュー依頼済み
- [x] セキュリティドキュメント作成済み
- [ ] ローカルでの動作確認完了
- [ ] ステージング環境でのテスト完了
- [ ] Artifact Registryでの脆弱性スキャン確認

### 参考資料

- [詳細な変更サマリー](../docs/security/CVE-2025-fixes-summary.md)
- [FastAPI Security Advisory](https://github.com/tiangolo/fastapi/security/advisories)
- [Starlette Security Advisory](https://github.com/encode/starlette/security/advisories)

---

**レビュアーへ**:

- 主に `requirements.txt` と `Dockerfile` の変更を確認してください
- アプリケーションロジックには一切変更がありません
- マージ後はArtifact Registryでの再スキャンを推奨します
