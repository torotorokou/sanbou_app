# sanbou_app Web アプリケーション

本リポジトリは、Vite + React、複数の FastAPI サービス、PostgreSQL、Nginx を
Docker Compose でまとめて起動する Web アプリです。

> **🔒 セキュリティアップデート（2025-12-08）**  
> CVE脆弱性に対応しました。詳細は [docs/security/CVE-2025-fixes-summary.md](docs/security/CVE-2025-fixes-summary.md) を参照してください。

## 環境構成（2025-12-06 更新）

プロジェクトは以下の **3つの主要環境** で運用されます：

1. **local_dev** - ローカル開発環境（ホットリロード有効）
2. **vm_stg** - GCP VM ステージング環境（VPN/Tailscale 経由）
3. **vm_prod** - GCP VM 本番環境（LB + IAP 経由）

詳細は [環境構成マトリクス](docs/20251206_ENV_MATRIX.md) を参照してください。

---

## 1. ローカルで動かす（local_dev）

### 1-1. リポジトリ取得

```bash
git clone <REPO_URL>
cd sanbou_app
```

### 1-2. env ファイルの準備

```bash
# 開発環境用の env をコピー
cp env/.env.example env/.env.local_dev
cp secrets/.env.secrets.template secrets/.env.local_dev.secrets
```

最低限必要な設定（`env/.env.local_dev`）:

```env
# 認証モード
AUTH_MODE=dummy

# DB 設定
POSTGRES_USER=sanbou_app_dev
POSTGRES_DB=sanbou_dev
# POSTGRES_PASSWORD は secrets/.env.local_dev.secrets に記載

# デバッグモード
DEBUG=true
```

secrets ファイル（`secrets/.env.local_dev.secrets`）:

```env
POSTGRES_PASSWORD=your_secure_password
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
```

### 1-3. コンテナ起動

```bash
make up ENV=local_dev
```

アクセス先:

- Frontend: http://localhost:5173
- AI API: http://localhost:8001/docs
- Ledger: http://localhost:8002/docs
- Core API: http://localhost:8003/docs
- RAG: http://localhost:8004/docs
- Manual: http://localhost:8005/docs

よく使うコマンド:

```bash
make down ENV=local_dev      # 停止
make logs ENV=local_dev      # ログ確認
make restart ENV=local_dev   # 再起動
make rebuild ENV=local_dev   # 再ビルド＋再起動
make health ENV=local_dev    # ヘルスチェック
```

### 1-4. DB 初期化（ローカル）

バックアップから復元:

```bash
make restore-from-dump ENV=local_dev DUMP=backups/sanbou_dev_2025-12-05.dump
```

スキーマだけ欲しい場合（空 DB で OK なとき）:

```bash
# DB 起動済みで実行
make al-init-from-schema
# または
make al-up
```

---

## 2. GCP VM で動かす（vm_stg / vm_prod）

### 2-0. 前提

- GCE VM が作成済み（Linux、Docker / Docker Compose v2 / make インストール済み）
- **vm_stg**: VPN/Tailscale 経由でアクセス可能
- **vm_prod**: GCP Load Balancer + IAP が設定済み
- サービスアカウントなど GCP 側の権限設定は別途完了済み

### 2-1. VM 上でリポジトリ取得

VM に SSH してから:

```bash
cd ~
git clone <REPO_URL>
cd sanbou_app
git checkout main  # または特定のタグ/ブランチ
```

### 2-2. env ファイルの準備

#### STG（vm_stg）

```bash
cp env/.env.example env/.env.vm_stg
cp secrets/.env.secrets.template secrets/.env.vm_stg.secrets
```

重要な設定（`env/.env.vm_stg`）:

```env
# 認証モード（VPN 経由固定ユーザー）
AUTH_MODE=vpn_dummy
VPN_USER_EMAIL=stg-admin@example.com
VPN_USER_NAME=STG Administrator

# DB 設定
POSTGRES_USER=sanbou_app_stg
POSTGRES_DB=sanbou_stg

# デバッグモード
DEBUG=false
IAP_ENABLED=false

# PUBLIC_BASE_URL は VPN 内 IP または FQDN
PUBLIC_BASE_URL=http://10.0.0.1
```

#### PROD（vm_prod）

```bash
cp env/.env.example env/.env.vm_prod
cp secrets/.env.secrets.template secrets/.env.vm_prod.secrets
```

重要な設定（`env/.env.vm_prod`）:

```env
# 認証モード（IAP ヘッダ検証）
AUTH_MODE=iap
IAP_ENABLED=true
IAP_AUDIENCE=/projects/YOUR_PROJECT_NUMBER/global/backendServices/YOUR_SERVICE_ID

# DB 設定
POSTGRES_USER=sanbou_app_prod
POSTGRES_DB=sanbou_prod

# デバッグモード（必ず false）
DEBUG=false

# PUBLIC_BASE_URL は本番ドメイン
PUBLIC_BASE_URL=https://example.com
```

### 2-3. Docker イメージの準備

VM では **Artifact Registry からイメージを pull** します。

ローカル PC で事前にイメージをビルド & push:

```bash
# STG イメージ
make publish-stg-images STG_IMAGE_TAG=stg-20251206

# PROD イメージ
make publish-prod-images PROD_IMAGE_TAG=prod-20251206
```

VM 側で gcloud 認証:

```bash
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
```

### 2-4. コンテナ起動

#### STG 環境（vm_stg）

```bash
make up ENV=vm_stg
```

アクセス: VPN 経由で `http://10.0.0.x/`（VPN IP）

#### PROD 環境（vm_prod）

```bash
make up ENV=vm_prod
```

### 2-5. ヘルスチェック

```bash
make health ENV=vm_stg   # STG
make health ENV=vm_prod  # PROD
```

動かない場合のログ確認:

```bash
make logs ENV=vm_stg S=nginx     # nginx ログ
make logs ENV=vm_stg S=core_api  # core_api ログ
```

### 2-6. DB 初期化（GCP VM 上）

VM 内のコンテナで DB を動かす場合は、ローカルと同じコマンドで ENV だけ変更:

```bash
# STG の DB にダンプを流す
make restore-from-dump ENV=vm_stg DUMP=backups/sanbou_stg_2025-12-05.dump

# PROD の DB にダンプを流す
make restore-from-dump ENV=vm_prod DUMP=backups/sanbou_prod_2025-12-05.dump
```

---

## 3. よくある質問

### Q: local_stg / local_prod はどこ?

A: **2025-12-06 に廃止されました**。vm_stg / vm_prod で十分に検証可能なため、ローカルでの本番近似構成は不要と判断しました。

### Q: 認証モード（AUTH_MODE）とは?

A: 環境ごとに異なる認証方式を切り替えるための設定です：

- `dummy` - 開発用固定ユーザー（local_dev / local_demo）
- `vpn_dummy` - VPN 経由固定ユーザー（vm_stg）
- `iap` - IAP ヘッダ検証（vm_prod）

詳細は [環境構成マトリクス](docs/20251206_ENV_MATRIX.md) を参照。

### Q: Docker イメージのビルドとデプロイの流れは?

A:

1. ローカル PC で `make publish-stg-images` または `make publish-prod-images`
2. Artifact Registry にイメージが push される
3. VM で `make up ENV=vm_stg` または `make up ENV=vm_prod`
4. VM が Artifact Registry からイメージを pull して起動

### Q: Dockerfile の --target とは?

A: マルチステージビルドのターゲットステージ指定です：

- `--target dev` - ホットリロード対応（local_dev / local_demo）
- `--target stg` - STG 用ランタイム（vm_stg）
- `--target prod` - PROD 用ランタイム（vm_prod）

詳細は各 Dockerfile のコメントを参照。

---

## 4. 参考資料

- [環境構成マトリクス](docs/20251206_ENV_MATRIX.md) - 環境別の詳細設定
- [Makefile](makefile) - コマンド定義と環境マッピング
- [IAP 認証実装](docs/20251203_IAP_AUTHENTICATION_IMPLEMENTATION.md)
- [backend_shared 統合ログ](docs/20251202_LOGGING_INTEGRATION_SUMMARY.md)

---

## 更新履歴

- **2025-12-06**: 環境構成を 3 区分に統一（local_dev / vm_stg / vm_prod）
  - local_stg / local_prod を廃止
  - AUTH_MODE 導入
  - VPN 認証プロバイダー実装
  - docker-compose / Nginx 設定の整理
- **2025-12-03**: IAP 認証実装、env ファイル整理
- **2025-11-27**: backend_shared 統合ログ導入
