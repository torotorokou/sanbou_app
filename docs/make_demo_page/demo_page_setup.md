# local_demo デモページ作成手順.me

作成日: 2025-11-27
対象: sanbou_app / sanbou_app_demo プロジェクト
目的: local_dev とは独立した local_demo 環境でデモページを動かす手順をまとめる。

------------------------------------------------------------
1. 前提ディレクトリ構成
------------------------------------------------------------

/home/koujiro/work_env/22.Work_React/
  ├── sanbou_app        … 開発用リポジトリ（stg / feature 用）
  └── sanbou_app_demo   … デモ用リポジトリ（demo-local 用）

- sanbou_app_demo は sanbou_app を単純 clone して作成する。
  例:
    cd /home/koujiro/work_env/22.Work_React
    git clone sanbou_app sanbou_app_demo

------------------------------------------------------------
2. デモ用ブランチ・タグの準備（sanbou_app 側で一度だけ）
------------------------------------------------------------

1) stg の最新コミットに移動

    cd /home/koujiro/work_env/22.Work_React/sanbou_app
    git switch stg
    git pull origin stg

2) デモ用タグの作成（例: demo-local-20251127）

    TAG_NAME="demo-local-20251127"
    git tag -a "$TAG_NAME" -m "Local demo baseline (2025-11-27)"
    git push origin "$TAG_NAME"

3) デモ用ブランチを作成（以後このブランチをデモ用に使う）

    git branch demo-local "$TAG_NAME"
    git push origin demo-local

------------------------------------------------------------
3. sanbou_app_demo 側の準備
------------------------------------------------------------

1) デモ用リポジトリに切り替え

    cd /home/koujiro/work_env/22.Work_React/sanbou_app_demo

2) デモ用ブランチに切り替え

    git switch demo-local
    git pull origin demo-local

3) env / secrets の確認（なければコピー）

    ls env
      -> .env.common / .env.local_dev / .env.local_demo など

    ls secrets
      -> .env.local_dev.secrets / .env.local_demo.secrets など

    足りない場合は sanbou_app からコピー:

    cp ../sanbou_app/env/.env.local_demo env/.env.local_demo
    cp ../sanbou_app/secrets/.env.local_demo.secrets secrets/.env.local_demo.secrets

------------------------------------------------------------
4. demo 用 DB（sanbou_demo）の初期化
------------------------------------------------------------

4-1. demo 用 DB ディレクトリを作成（初回のみ）

    cd /home/koujiro/work_env/22.Work_React/sanbou_app_demo
    mkdir -p data/local_demo/postgres

4-2. demo の db コンテナを一度起動

    docker compose -f docker/docker-compose.local_demo.yml -p local_demo up -d db

4-3. dev の DB（sanbou_dev）を起動（sanbou_app 側）

    cd /home/koujiro/work_env/22.Work_React/sanbou_app
    make up ENV=local_dev   # 既に起動済みなら不要

4-4. demo 側で dev から DB をクローン

    cd /home/koujiro/work_env/22.Work_React/sanbou_app_demo
    make demo-db-clone-from-dev

※ 初回クローン時に `role "app_readonly" does not exist` エラーが出た場合は、
   demo クラスタにロールを作成してから再実行する:

    docker compose -f docker/docker-compose.local_demo.yml -p local_demo exec -T db           psql -U myuser -d postgres -c         "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_readonly') THEN CREATE ROLE app_readonly; END IF; END $$;"

    # その後で再度:
    make demo-db-clone-from-dev

------------------------------------------------------------
5. demo ページ（local_demo）の起動手順
------------------------------------------------------------

1) デモ用リポジトリに移動

    cd /home/koujiro/work_env/22.Work_React/sanbou_app_demo

2) ブランチ確認（demo-local であること）

    git status
      -> On branch demo-local

3) demo 環境を起動

    make demo-up

4) コンテナ状態の確認

    make demo-ps

   - frontend / core_api / ai_api / ledger_api / rag_api / manual_api / db
     が STATUS=Up になっていること

------------------------------------------------------------
6. demo ページの動作確認
------------------------------------------------------------

1) フロントエンド

   ブラウザで開く:
     http://localhost:5174

   確認ポイント:
   - ページが表示される（真っ白でない）
   - エラー画面になっていない
   - F12 → Console で致命的エラーが出ていない

2) 各 API の疎通確認（任意）

    curl -sS http://localhost:8013/docs > /dev/null && echo "core_api OK"
    curl -sS http://localhost:8011/docs > /dev/null && echo "ai_api OK"
    curl -sS http://localhost:8012/docs > /dev/null && echo "ledger_api OK"
    curl -sS http://localhost:8014/docs > /dev/null && echo "rag_api OK"
    curl -sS http://localhost:8015/docs > /dev/null && echo "manual_api OK"

3) DB 確認（任意）

    cd /home/koujiro/work_env/22.Work_React/sanbou_app_demo
    make demo-db-shell

    -- psql 内で:
    \l                         -- sanbou_demo が存在すること
    \dn                        -- mart / stg / raw などのスキーマを確認
    \dt mart.*                 -- mart テーブル一覧を表示
    SELECT COUNT(*) FROM mart.mv_sales_tree_daily;

------------------------------------------------------------
7. 開発とデモの同時運用のイメージ
------------------------------------------------------------

- 開発用（sanbou_app）:
    cd sanbou_app
    git switch stg
    make up ENV=local_dev

  使用ポート:
    - Frontend: 5173
    - Core API: 8003
    - AI API:   8001
    - Ledger:   8002
    - RAG:      8004
    - Manual:   8005
    - DB:       5432 (sanbou_dev)

- デモ用（sanbou_app_demo）:
    cd sanbou_app_demo
    git switch demo-local
    make demo-up

  使用ポート:
    - Frontend: 5174
    - Core API: 8013
    - AI API:   8011
    - Ledger:   8012
    - RAG:      8014
    - Manual:   8015
    - DB:       5433 (sanbou_demo)

これにより、開発とデモを同時に起動してもポート・DB が衝突しない。

------------------------------------------------------------
8. デモ用コード・DB の更新
------------------------------------------------------------

1) コードを更新したい場合:

   - sanbou_app 側で stg を更新
   - デモ用ブランチ demo-local に stg を取り込む

    cd sanbou_app
    git switch demo-local
    git merge stg
    git push origin demo-local

   - sanbou_app_demo 側で pull

    cd sanbou_app_demo
    git switch demo-local
    git pull origin demo-local

2) DB を最新 dev から取り込み直したい場合:

    # dev を起動（sanbou_app 側）
    cd sanbou_app
    make up ENV=local_dev

    # demo 側でクローン（sanbou_app_demo 側）
    cd ../sanbou_app_demo
    make demo-down
    docker compose -f docker/docker-compose.local_demo.yml -p local_demo up -d db
    make demo-db-clone-from-dev

------------------------------------------------------------
以上が、local_demo 用のデモページを構築・起動・確認するまでの手順。
