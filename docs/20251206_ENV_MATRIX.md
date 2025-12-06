# 環境構成マトリクス（Environment Configuration Matrix）

最終更新: 2025-12-06

## 概要

このドキュメントは、sanbou_app プロジェクトの環境構成を整理したものです。
2025年12月6日のリファクタリングにより、環境を以下の **3つに統一** しました：

1. **local_dev** - ローカル開発環境
2. **vm_stg** - GCP VM ステージング環境（VPN 経由）
3. **vm_prod** - GCP VM 本番環境（LB + IAP 経由）

加えて、**local_demo** 環境も維持されています（local_dev とは完全分離）。

---

## 環境別構成一覧

| 項目 | local_dev | vm_stg | vm_prod | local_demo |
|------|-----------|--------|---------|------------|
| **用途** | ローカル開発 | VPN 内検証 | 本番運用 | デモ・検証 |
| **アクセス方法** | localhost | VPN/Tailscale 経由<br>http://100.x.x.x/ | LB + IAP 経由<br>https://sanbou-app.jp/ | localhost (別ポート) |
| **docker-compose** | `docker-compose.dev.yml` | `docker-compose.stg.yml` | `docker-compose.prod.yml` | `docker-compose.local_demo.yml` |
| **env ファイル** | `.env.local_dev` | `.env.vm_stg` | `.env.vm_prod` | `.env.local_demo` |
| **secrets ファイル** | `.env.local_dev.secrets` | `.env.vm_stg.secrets` | `.env.vm_prod.secrets` | `.env.local_demo.secrets` |
| **AUTH_MODE** | `dummy` | `vpn_dummy` | `iap` | `dummy` |
| **IAP_ENABLED** | `false` | `false` | `true` | `false` |
| **DEBUG** | `true` | `false` | `false` | `true` |
| **STAGE** | `dev` | `stg` | `prod` | `demo` |
| **APP_TAG** | `local_dev` | `stg` | `prod` | `local_demo` |
| **POSTGRES_USER** | `sanbou_app_dev` | `sanbou_app_stg` | `sanbou_app_prod` | `sanbou_app_demo` |
| **POSTGRES_DB** | `sanbou_dev` | `sanbou_stg` | `sanbou_prod` | `sanbou_demo` |
| **DB ポート公開** | `5432:5432` | `5432:5432` | `127.0.0.1:5432:5432`<br>(localhost のみ) | `5433:5432` |
| **nginx ポート** | - | `80:80`, `443:443` | `80:80`, `443:443` | - |
| **イメージソース** | build (local) | Artifact Registry<br>(pull のみ) | Artifact Registry<br>(pull のみ) | build (local) |
| **イメージタグ** | - | `*:stg-latest` | `*:prod-latest` | - |
| **Dockerfile target** | `dev` | `stg` | `prod` | `dev` |
| **ホットリロード** | ✅ 有効 | ❌ 無効 | ❌ 無効 | ✅ 有効 |
| **nginx 設定** | - | `stg.conf` | `app.conf` | - |
| **IAP ヘッダ転送** | - | ❌ 不要 | ✅ 必須 | - |
| **VPN ユーザー** | - | `VPN_USER_EMAIL`<br>`VPN_USER_NAME` | - | - |

---

## 認証モード詳細

### AUTH_MODE の値と動作

| AUTH_MODE | 使用環境 | 動作 | 必要な設定 |
|-----------|----------|------|------------|
| `dummy` | local_dev<br>local_demo | 固定の開発用ユーザーを返す<br>`dev-user@honest-recycle.co.jp` | なし |
| `vpn_dummy` | vm_stg | 環境変数で指定した VPN ユーザーを返す | `VPN_USER_EMAIL`<br>`VPN_USER_NAME` |
| `iap` | vm_prod | IAP ヘッダ（`X-Goog-*`）を検証してユーザーを取得 | `IAP_AUDIENCE`<br>`IAP_PUBLIC_KEY_URL` |

### 認証プロバイダー実装

- `DevAuthProvider` - `AUTH_MODE=dummy` 用
- `VpnAuthProvider` - `AUTH_MODE=vpn_dummy` 用
- `IapAuthProvider` - `AUTH_MODE=iap` 用

実装場所: `app/backend/core_api/app/infra/adapters/auth/`

---

## Makefile コマンド

### 基本操作

```bash
# 起動
make up ENV=local_dev   # ローカル開発環境
make up ENV=vm_stg      # STG 環境（VPN 経由）
make up ENV=vm_prod     # 本番環境（IAP 経由）

# 停止
make down ENV=<ENV>

# 再起動
make restart ENV=<ENV>

# ログ確認
make logs ENV=<ENV> S=core_api

# ヘルスチェック
make health ENV=<ENV>
```

### イメージビルド & Push

```bash
# STG イメージ (--target stg)
make publish-stg-images STG_IMAGE_TAG=stg-20251206

# PROD イメージ (--target prod)
make publish-prod-images PROD_IMAGE_TAG=prod-20251206
```

### データベース操作

```bash
# バックアップ
make backup ENV=local_dev

# リストア
make restore-from-dump ENV=local_dev DUMP=backups/sanbou_dev_2025-12-05.dump
```

---

## Docker イメージ構成

### Dockerfile のマルチステージ構造

すべてのバックエンドサービスと frontend は以下の構造：

```
wheelbuilder/builder  ← 依存パッケージのビルド
    ↓
base                  ← 共通ランタイムベース（wheelインストール済み）
    ↓
├── dev               ← 開発用（ホットリロード、editable install）
├── stg               ← STG 用（base 継承、ENV APP_ENV=stg）
└── prod              ← PROD 用（base 継承、ENV APP_ENV=prod）
```

### ビルド時の --target 指定

- **local_dev / local_demo**: `--target dev`
- **vm_stg**: `--target stg`
- **vm_prod**: `--target prod`

---

## Nginx 設定

### vm_stg（stg.conf）

- **アクセス経路**: VPN/Tailscale 経由（`http://100.x.x.x/`）
- **ポート**: HTTP 80 のみ
- **IAP ヘッダ**: 不要（VPN で接続制御済み）
- **プロキシヘッダ**: 基本ヘッダのみ（`Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`）

### vm_prod（app.conf）

- **アクセス経路**: GCP Load Balancer + IAP → nginx
- **ポート**: HTTP 80（LB で HTTPS 終端）、HTTPS 443（将来対応）
- **IAP ヘッダ**: 必須（`X-Goog-Authenticated-User-Email`, `X-Goog-IAP-JWT-Assertion` など）
- **プロキシヘッダ**: `_proxy_headers.conf` に定義（IAP ヘッダ含む）

### 共通設定

- upstream 定義は `app.conf` で共通化
- `_proxy_headers.conf` - IAP ヘッダ含む共通ヘッダ
- `_proxy_ws.conf` - WebSocket 対応ヘッダ

---

## ネットワーク構成

### 3層分離（vm_stg / vm_prod）

```
edge-net  ← nginx のみ外部公開
    ↓
app-net   ← frontend/backend API 間通信
    ↓
data-net  ← backend ↔ DB 間通信（内部のみ）
```

---

## 廃止された環境

以下の環境は **2025-12-06 に廃止** されました：

- ❌ `local_stg` - ローカル STG 検証環境
- ❌ `local_prod` - ローカル本番検証環境

**理由**: VM 上の vm_stg / vm_prod で十分に検証可能なため、ローカルでの本番近似構成は不要と判断。

---

## 環境変数スキーマの Source of Truth

**`env/.env.local_dev`** がすべての環境変数定義の基準です。
新しい環境変数を追加する際は、まず `.env.local_dev` に追加し、他の環境ファイルに必要に応じて継承・上書きしてください。

---

## チェックリスト

### 新環境セットアップ時

- [ ] `.env.<ENV>` ファイル作成（`.env.local_dev` をベースに）
- [ ] `secrets/.env.<ENV>.secrets` ファイル作成
- [ ] `AUTH_MODE` を適切に設定
- [ ] DB ユーザー・パスワードを設定
- [ ] （vm_* のみ）Artifact Registry イメージを push
- [ ] （vm_prod のみ）IAP_AUDIENCE を設定
- [ ] `make up ENV=<ENV>` で起動確認
- [ ] `make health ENV=<ENV>` でヘルスチェック

### コード変更時

- [ ] 開発: `ENV=local_dev` でホットリロード確認
- [ ] STG デプロイ: `make publish-stg-images` → VM で `make up ENV=vm_stg`
- [ ] PROD デプロイ: `make publish-prod-images` → VM で `make up ENV=vm_prod`

---

## 参考資料

- [Makefile](/makefile) - 環境マッピングとコマンド定義
- [docker-compose.dev.yml](/docker/docker-compose.dev.yml)
- [docker-compose.stg.yml](/docker/docker-compose.stg.yml)
- [docker-compose.prod.yml](/docker/docker-compose.prod.yml)
- [backend_shared 統合ログ](/docs/20251202_LOGGING_INTEGRATION_SUMMARY.md)
- [IAP 認証実装](/docs/20251203_IAP_AUTHENTICATION_IMPLEMENTATION.md)

---

## 更新履歴

- **2025-12-06**: 環境構成を 3 区分に統一（local_dev / vm_stg / vm_prod）
  - local_stg / local_prod を廃止
  - AUTH_MODE 導入（dummy / vpn_dummy / iap）
  - VpnAuthProvider 実装（vm_stg 用）
  - docker-compose ファイルの重複解消
  - Dockerfile の stg/prod ステージ明確化
  - nginx 設定の vm_stg/vm_prod 分離
  - Makefile の環境マッピング整理
