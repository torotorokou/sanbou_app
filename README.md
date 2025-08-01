
---

## プロジェクト概要

このリポジトリは、Webアプリケーション「sanbou_app」の開発・運用に必要な各種サービス（フロントエンド、バックエンド、AI API、DB、Nginx等）をDocker Composeで一元管理するための構成です。

---

## ディレクトリ・ファイル構成


### my-project/
### envs/
環境ごとの設定ファイルやサンプル環境変数ファイル（例：`.env.sample`）を管理するディレクトリ。
開発・本番など用途別に環境変数テンプレートや設定例を配置。

アプリ本体のディレクトリ。以下のサブディレクトリを含みます：

- **frontend/**
  - React + ViteベースのフロントエンドSPA。
  - `src/`配下に主要な画面・コンポーネント・ロジックを実装。
  - `public/`には静的ファイル（画像・PDF等）を配置。

- **backend/**
  - FastAPIベースのバックエンドAPI群。
  - AI連携、PDFページ画像生成、質問テンプレートAPIなどを提供。
  - `app/`配下にAPIエンドポイントやビジネスロジックを実装。

- **ledger_api/**
  - 会計データ管理用APIサービス。
  - 独立したDockerfile・設定・`app/`実装を持つ。

- **sql_api/**
  - SQLデータベース連携用APIサービス。
  - DBアクセスやデータ取得APIを提供。

- **rag_api/**
  - Retrieval-Augmented Generation（RAG）型AI APIサービス。
  - ドキュメント検索やAI回答生成を担当。

- **config/**
  - CSVやレポート等の各種設定ファイル群。
  - `csv_config/`や`report_config/`など用途別に整理。

- **dbdata/**
  - DBの永続化データを格納（git管理外）。
  - ローカル開発や本番用のDBデータを保持。

- **nginx/**
  - Nginxのリバースプロキシ設定・SSL証明書等を管理。
  - `conf.d/`に仮想ホスト設定、`certs/`に証明書を配置。

- **shared/**
  - 複数サービスで共通利用するユーティリティや設定。

- **backend_shared/**
  - バックエンド系サービス間で共通利用するモジュールやロジック。
  - 例：CSVバリデータ、共通設定ローダー等。


### .env
環境変数ファイル。APIキーやDB接続情報などを記載。**機密情報は必ずgit管理外**にしてください。


### .gitignore
バージョン管理から除外するファイル・ディレクトリを定義。`.env`や`dbdata/`など機密・一時データを管理。


### docker-compose.yml / docker-compose.override.yml
各サービス（frontend, backend, db, nginx等）を一括起動・停止できるDocker Compose設定ファイル。
`override`は開発用の追加設定等に利用。


### makefile
よく使うDockerコマンドやビルドコマンドをまとめた補助スクリプト。
`make up`や`make down`などで一括操作可能。

---

## 開発の流れ

1. `.env`や`.vscode/`を必要に応じて作成・編集
2. `docker-compose.yml`・`makefile`で各種サービスを一括管理
3. アプリ本体の開発・運用は `my-project/` 配下で実施
4. サービスごとの詳細・技術ドキュメントは `my-project/README.md` などを参照

---

## 注意事項

- `.env`やDBデータ等の**機密情報は必ずgit管理から除外**してください（`.gitignore`で管理）。
- サブディレクトリごとに追加のREADMEや設定ファイルを置くことで、管理・引き継ぎが容易になります。

---

## サポート・問い合わせ

質問や追加要望があれば、プロジェクト管理者・技術担当までご連絡ください。
