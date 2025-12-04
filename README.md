# sanbou_app Webアプリ起動手順（ローカル / GCP）

本リポジトリは、Vite + React、複数の FastAPI サービス、PostgreSQL、Nginx を
Docker Compose でまとめて起動する Web アプリです。

ここでは **「ローカル」と「GCP VM」** で立ち上げる最低限の手順だけを示します。

---

## 1. ローカルで動かす（local_dev 前提）

### 1-1. リポジトリ取得（特定タグから）

```bash
git clone --branch v1.1.0-stg.1 --depth 1 <REPO_URL>
cd sanbou_app
```

- `<REPO_URL>` は Git のリポジトリ URL に置き換えてください。
- 別のリリースで立ち上げたい場合は `v1.1.0-stg.1` を別タグ名に変更します。

---

### 1-2. env ファイル作成（local_dev）

```bash
cp env/.env.example env/.env.local_dev
```

最低限こんなイメージの値が入っていれば動きます（必要に応じて調整）:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=sanbou
POSTGRES_PORT=5432

FRONTEND_PORT=5173
AI_API_PORT=8001
LEDGER_API_PORT=8002
SQL_API_PORT=8003
RAG_API_PORT=8004
```

---

### 1-3. コンテナ起動（local_dev）

```bash
make up ENV=local_dev
```

ブラウザ／API の確認:

- Frontend: http://localhost:5173
- AI API:  http://localhost:8001/docs
- Ledger:  http://localhost:8002/docs
- SQL:     http://localhost:8003/docs
- RAG:     http://localhost:8004/docs

よく使うコマンド:

```bash
make down    ENV=local_dev   # 停止
make logs    ENV=local_dev   # ログ確認
make rebuild ENV=local_dev   # 再ビルド＋再起動
```

---

### 1-4. DB 初期化（ローカル用）

既存の .dump を流して「本番に近いデータ」で見たい場合:

```bash
# 例: backups/sanbou_dev_2025-12-03.dump を使う
make restore-from-dump ENV=local_dev   DUMP=backups/sanbou_dev_2025-12-03.dump
```

- `ENV` を `local_stg` などに変えれば、他環境にも同じ要領で流せます。

スキーマだけ欲しい場合（空 DB で OK なとき）:

```bash
# DB 起動済みで実行
make al-init-from-schema
# または
make al-up
```

---

## 2. GCP VM で動かす（vm_stg / vm_prod）

ここでは **Compute Engine VM 上で Docker Compose を使う** 想定です。

### 2-0. 前提

- GCE VM 作成済み（Linux）
- VM 上に Docker / Docker Compose v2 / make がインストール済み
- 80 / 443 または 8080 / 8443 など、公開ポートの設計済み
- サービスアカウントなど GCP 側の権限設定は別途実施済み

---

### 2-1. VM 上でリポジトリ取得（特定タグ）

VM に SSH してから:

```bash
cd ~
git clone --branch v1.1.0-stg.1 --depth 1 <REPO_URL>
cd sanbou_app
```

必要なら別タグ名に置き換えてください。

---

### 2-2. env ファイル作成（vm_stg / vm_prod）

#### STG（vm_stg）の例

```bash
cp env/.env.example env/.env.vm_stg
# 中身を STG 用の値に編集（DB, ドメイン名など）
```

#### 本番（vm_prod）の例

```bash
cp env/.env.example env/.env.vm_prod
# 本番用の値に編集
```

API キーなどの秘密情報は `.env.vm_*` ではなく  
`secrets/.env.vm_stg.secrets` 等に分離して管理する運用でも構いません
（プロジェクト内の運用ルールに合わせてください）。

---

### 2-3. コンテナ起動（vm_stg / vm_prod）

Nginx を有効にして立ち上げる想定です。

#### STG 環境（vm_stg）

```bash
COMPOSE_PROFILES=edge make up ENV=vm_stg
```

アクセス例:

- Health:  http://stg.sanbou-app.jp/health
- アプリ:  http://stg.sanbou-app.jp/

#### 本番環境（vm_prod）

```bash
COMPOSE_PROFILES=edge make up ENV=vm_prod
```

アクセス例:

- Health:  https://sanbou-app.jp/health
- アプリ:  https://sanbou-app.jp/

動かない場合は、VM 上で:

```bash
make logs ENV=vm_stg  S=nginx   # STG の nginx ログ
make logs ENV=vm_prod S=nginx   # 本番の nginx ログ
```

---

### 2-4. DB 初期化（GCP VM 上）

DB も VM 内のコンテナで動かす場合は、ローカルと同じコマンドで  
**ENV だけ vm_stg / vm_prod に変えれば OK** です。

例: STG の DB にダンプを流す

```bash
make restore-from-dump ENV=vm_stg   DUMP=backups/sanbou_stg_2025-12-03.dump
```

スキーマだけ構築したい場合:

```bash
make al-init-from-schema   # または
make al-up
```

---

## 3. どれを使えばいいか簡単まとめ

- **ローカルでとりあえず動かしたい**
  - 1-1〜1-3 (`local_dev`) + 必要なら 1-4 の dump restore
- **GCP 上で STG / 本番を立てたい**
  - 2-1〜2-3（`vm_stg` / `vm_prod`）+ 必要なら 2-4 の dump restore

基本的には、同じ Make ターゲットを **ENV だけ変えて使う** 形になっています。
