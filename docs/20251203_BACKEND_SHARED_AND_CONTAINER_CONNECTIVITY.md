# バックエンド共通化とコンテナ連携改善 (2025-12-03)

## 概要
バックエンドサービス間の共通コードを`backend_shared`に集約し、フロントエンド・バックエンド間のコンテナ連携を改善しました。

## 実施内容

### 1. backend_shared の共通化確認

#### 現状確認
- ✅ 全てのバックエンドサービスで`backend_shared`が既に適切に実装されていることを確認
- ✅ 各Dockerfileで`backend_shared`をeditable modeでインストール済み
- ✅ 開発環境でホットリロードが正常に動作

#### backend_sharedを使用しているサービス
- `core_api`: ロギング、エラーハンドリング、認証
- `ledger_api`: レポート生成、日付フィルタリング、CSV設定ローダー
- `ai_api`: ロギング、ドメインモデル
- `rag_api`: ロギング、APIレスポンス
- `manual_api`: ロギング
- `plan_worker`: ドメインモデル

#### backend_sharedの主要モジュール
```
backend_shared/
├── application/
│   └── logging/          # 構造化ロギング
├── config/
│   ├── config_loader.py  # YAML設定ローダー
│   └── env_utils.py      # 環境変数ユーティリティ
├── core/
│   ├── domain/           # ドメインモデル
│   └── usecases/         # CSV処理、型パーサー
├── infra/
│   └── adapters/
│       ├── fastapi/      # エラーハンドラー
│       ├── middleware/   # リクエストID
│       └── presentation/ # APIレスポンス
└── utils/
    ├── csv_reader.py     # CSV読み込み
    ├── dataframe_utils.py
    └── date_filter_utils.py
```

### 2. requirements.txtの整理

#### 変更内容
各サービスの`requirements.txt`を以下のように統一:
- バージョン指定を`==`から`>=`に変更(柔軟性向上)
- コメントで`backend_shared`はDockerfileでインストールされることを明記
- 重複パッケージの整理

#### 対象ファイル
- `core_api/requirements.txt`
- `ledger_api/requirements.txt`
- `ai_api/requirements.txt`
- `rag_api/requirements.txt`
- `manual_api/requirements.txt`
- `plan_worker/requirements.txt`

### 3. コンテナ連携の改善

#### 問題点
1. **フロントエンド → バックエンド通信**
   - `vite.config.ts`で環境変数チェックが冗長(`DOCKER === 'true' || IS_DOCKER === 'true'`)
   - プロキシ設定に`secure: false`が不足
   - デバッグログが不十分

2. **環境変数の一貫性**
   - フロントエンド向けAPI URLが不明確
   - 内部通信URLの説明不足

3. **サービス起動順序**
   - DBの健全性チェックを待たずにサービスが起動
   - フロントエンドがバックエンドの準備を待たない

#### 修正内容

##### vite.config.ts
```typescript
// Before
const isDockerEnvironment = process.env.DOCKER === 'true' || process.env.IS_DOCKER === 'true';

// After
const isDockerEnvironment = process.env.DOCKER === 'true';
console.log(`[Vite] Docker environment: ${isDockerEnvironment}`);
console.log(`[Vite] Core API target: ${coreApiTarget}`);
```

プロキシ設定に`secure: false`を追加:
```typescript
'/core_api': {
    target: coreApiTarget,
    changeOrigin: true,
    secure: false,  // 追加
},
```

##### .env.common
フロントエンド → バックエンド通信用の設定を追加:
```bash
# === Frontend to Backend (フロントエンド → バックエンド通信) ===
# フロントエンドからは相対パス /core_api を使用してください
# Vite dev server が Docker 内部ネットワークを使ってプロキシします
CORE_API_INTERNAL_URL=http://core_api:8000
```

##### .env.local_dev
VITE_API_BASE_URLを相対パスに変更:
```bash
# Before
VITE_API_BASE_URL=http://localhost:8003/api

# After
VITE_API_BASE_URL=/core_api
```

##### docker-compose.dev.yml
全てのバックエンドサービスに健全性チェック依存を追加:
```yaml
depends_on:
  db:
    condition: service_healthy
```

フロントエンドにcore_api依存を追加:
```yaml
frontend:
  depends_on:
    core_api:
      condition: service_healthy
```

## アーキテクチャ図

### コンテナ通信フロー
```
┌─────────────────────────────────────────────────────────┐
│ ブラウザ                                                 │
└─────────────────────────────────────────────────────────┘
                        │
                        │ localhost:5173
                        ▼
┌─────────────────────────────────────────────────────────┐
│ frontend (Vite dev server)                              │
│ - Docker: true                                          │
│ - Proxy: /core_api → http://core_api:8000              │
│ - Proxy: /api → http://core_api:8000/core_api (Legacy) │
└─────────────────────────────────────────────────────────┘
                        │
                        │ app-net (Docker内部ネットワーク)
                        ▼
┌─────────────────────────────────────────────────────────┐
│ core_api (BFF)                                          │
│ - Port: 8000                                            │
│ - ROOT_PATH: /core_api                                  │
│ - backend_shared: /opt/backend_shared                   │
└─────────────────────────────────────────────────────────┘
         │                │                │
         │ RAG_API_BASE   │ LEDGER_API_BASE│ AI_API_BASE
         ▼                ▼                ▼
    ┌────────┐      ┌────────┐      ┌────────┐
    │rag_api │      │ledger  │      │ai_api  │
    │:8000   │      │_api    │      │:8000   │
    │        │      │:8000   │      │        │
    └────────┘      └────────┘      └────────┘
                          │
                          │ DATABASE_URL
                          ▼
                    ┌────────┐
                    │   db   │
                    │:5432   │
                    └────────┘
```

### backend_shared共有構造
```
┌─────────────────────────────────────────────────────┐
│ app/backend/                                        │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ backend_shared/                              │  │
│  │   src/backend_shared/                        │  │
│  │     ├── application/ (logging)               │  │
│  │     ├── config/ (env_utils, config_loader)   │  │
│  │     ├── core/ (domain, usecases)             │  │
│  │     ├── infra/ (adapters, middleware)        │  │
│  │     └── utils/ (csv, dataframe, date)        │  │
│  └──────────────────────────────────────────────┘  │
│           ▲          ▲          ▲                   │
│           │          │          │                   │
│     ┌─────┴──┐  ┌───┴────┐  ┌──┴────┐              │
│     │core_api│  │ledger  │  │ai_api │  ...         │
│     │        │  │_api    │  │       │              │
│     └────────┘  └────────┘  └───────┘              │
│                                                     │
│  Dockerfile (各サービス):                           │
│    RUN pip install -e /opt/backend_shared          │
│    PYTHONPATH=/backend:/opt/backend_shared/src     │
└─────────────────────────────────────────────────────┘
```

## サービス起動順序

正しい起動順序(depends_onで制御):
```
1. db (PostgreSQL)
   └─ healthcheck: pg_isready
2. backend services (ai_api, ledger_api, core_api, rag_api, plan_worker)
   └─ depends_on: db (service_healthy)
3. frontend
   └─ depends_on: core_api (service_healthy)
```

## 動作確認

### 確認項目
- [ ] `make rebuild` でコンテナが正常にビルド・起動
- [ ] フロントエンド(localhost:5173)が正常にアクセス可能
- [ ] フロントエンド → core_api の通信が正常
- [ ] core_api → 各バックエンドサービスの内部通信が正常
- [ ] backend_sharedの変更がホットリロードで反映
- [ ] ログに適切なリクエストIDが含まれる

### テストコマンド
```bash
# コンテナ起動
make rebuild

# フロントエンドログ確認
docker logs -f local_dev-frontend-1

# Viteプロキシ設定確認
# ログに以下が表示されることを確認:
# [Vite] Docker environment: true
# [Vite] Core API target: http://core_api:8000

# core_apiログ確認
docker logs -f local_dev-core_api-1

# APIテスト
curl http://localhost:5173/core_api/health
curl http://localhost:8003/core_api/health
```

## トラブルシューティング

### フロントエンドがバックエンドに接続できない
1. Viteログで`Docker environment: true`を確認
2. `DOCKER=true`環境変数がdocker-compose.devで設定されているか確認
3. `app-net`ネットワークで全てのサービスが接続されているか確認

### backend_sharedの変更が反映されない
1. Dockerfileで`pip install -e /opt/backend_shared`が実行されているか確認
2. `--reload-dir /opt/backend_shared/src`がuvicornコマンドに含まれているか確認
3. `WATCHFILES_FORCE_POLLING=1`が設定されているか確認

### サービス起動が遅い
1. DBのhealthcheckが正常に動作しているか確認
2. depends_onの条件が適切に設定されているか確認
3. 各サービスのhealthcheckエンドポイントが正常に応答しているか確認

## 今後の改善案

1. **backend_sharedのパッケージ化**
   - PyPIプライベートリポジトリへの公開を検討
   - バージョニングの導入

2. **依存関係の最適化**
   - 各サービスで本当に必要なパッケージのみをインストール
   - 共通パッケージをbackend_sharedに集約

3. **監視・ロギングの強化**
   - OpenTelemetryによる分散トレーシング
   - メトリクス収集(Prometheus)
   - ログ集約(ELK Stack)

4. **セキュリティ**
   - 本番環境での適切な認証・認可
   - シークレット管理の改善(Vault等)

## 関連ドキュメント
- [バックエンドドキュメント整備完了](./20251127_BACKEND_DOCS_SETUP_COMPLETE.md)
- [ロギング統合](./20251202_LOGGING_INTEGRATION_SUMMARY.md)
- [IAP認証実装](./20251203_IAP_AUTHENTICATION_IMPLEMENTATION.md)
- [環境変数統合](./20251203_ENV_CONSOLIDATION.md)
