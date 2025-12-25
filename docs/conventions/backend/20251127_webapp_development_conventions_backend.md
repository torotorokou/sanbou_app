# Webアプリ開発 共通ルール（バックエンド版）

- ファイル名: 20251127_webapp_development_conventions_backend.md
- 日付: 2025-11-27
- 対象: FastAPI バックエンド（core_api / ledger_api / rag_api など）

---

## 1. 基本方針

- フレームワーク: **FastAPI**
- アーキテクチャ: **Clean Architecture / Hexagonal / Ports & Adapters**
- DDD を意識したレイヤー分割を行い、**UseCase と Infrastructure を分離**する

---

## 2. ディレクトリ構成・レイヤー

### 2-1. 代表的構成例

```text
app/
  main.py
  api/
    routers/
    schemas/
  core/
    domain/
      inbound/
        entities.py
        value_objects.py
    ports/
      inbound/
        repositories.py
    usecases/
      inbound/
        calculate_inbound_plan.py
        get_inbound_forecast.py
  infra/
    adapters/
      inbound/
        inbound_repository.py
    db/
      models/                  ← schema（SQLAlchemy、Pydantic）ここ
        inbound_models.py
        sales_models.py
      migrations/              ← Alembic
      db.py
    frameworks/
      http_client.py
      file_storage.py
  config/
    di_providers.py
  shared/
docs/
    20251127_webapp_development_conventions_backend.md
    20251127_webapp_development_conventions_db.md
```

### 2-2. 各層の役割

- **api/routers/**

  - FastAPI ルーター定義
  - Request → DTO（Pydantic）への変換、UseCase 呼び出し、Response 生成のみ担当
  - ここでは `new` や SQL を書かない（UseCase インスタンスは DI で受け取る）

- **core/usecases/**

  - Application 層
  - 「何をどうするか」の手順を記述する
    - データ読み込み → 検証 → ドメイン操作 → 保存/取得
  - 依存するのは **core/ports/** の抽象のみ
  - infra の実装には依存してはいけない

- **core/domain/**

  - 業務ドメインモデル（Entity / 値オブジェクト / ドメインサービス）
  - 業務ルール・不変条件を表現
  - 外部 I/O（DB, HTTP, 設定）には依存しない

- **core/ports/**

  - UseCase が利用する抽象インターフェース（Repository, Gateway 等）
  - 例: `class InboundRepository(Protocol): ...`

- **infra/adapters/**

  - ports の具体実装
  - DB アクセス（SQLAlchemy / 生 SQL）、外部 API SDK を用いた実処理はここに閉じ込める
  - Domain 型と DB モデル間の変換を行う

- **infra/db/**

  - DB 接続・スキーマ定義・マイグレーション関連
  - `models/` に ORM モデル（schema）、`migrations/` に Alembic スクリプトを配置
  - `db.py` で Engine / SessionLocal を定義する

- **infra/frameworks/**

  - DB 接続 (`db.py`)、ログ設定、その他フレームワーク固有の初期化処理
  - 例: `get_db()` による Session 提供

- **config/di_providers.py**

  - DI コンテナ
  - UseCase / Repository 実装 / DB セッションを組み立てる
  - 環境差分（schema 切替・debug/raw/flash/final 等）はここで吸収する

- **shared（ローカル shared）**
  - コンテナ（サービス）内部で完結する技術的共通処理のみ
  - 他コンテナとは共有しない
  - あくまで「局所的 util や共通部品」を置く軽量スコープ
  - backend_shared のような “プロジェクト横断基盤” ではない
  - 例:
    - 当該サービス専用の小さなユーティリティ（`date_utils.py` など）
    - 特定の API グループだけで使う ResponseBuilder
    - フロントに公開しない内部用変換関数

---

## 3. コーディング規約（バックエンド）

### 3-1. 命名・スタイル

- Python の標準規約（PEP8）に従い、**snake_case**
- クラス名: PascalCase
- モジュール名: snake_case
- Domain 層:
  - ビジネス的な意味がわかる命名を優先（`InboundPlan`, `CustomerLTV` 等）

### 3-2. UseCase の書き方

- Input/Output DTO を明確にする（Pydantic モデル or dataclass）
- 典型的な流れ：

```py
class CalculateInboundPlanUseCase:
    def __init__(self, inbound_repo: InboundRepository, plan_repo: PlanRepository):
        self._inbound_repo = inbound_repo
        self._plan_repo = plan_repo

    def execute(self, params: CalculateInboundPlanInput) -> CalculateInboundPlanOutput:
        # 1. 必要なデータの読み込み
        inbounds = self._inbound_repo.fetch_inbounds(params.period)

        # 2. ドメインロジック呼び出し
        plan = InboundPlanner.calculate(inbounds, params.target)

        # 3. 永続化
        self._plan_repo.save(plan)

        # 4. 結果返却
        return CalculateInboundPlanOutput.from_domain(plan)
```

- UseCase 内で直接 SQL を書かない（Repository 経由）

### 3-3. API Router の書き方

- Router はできるだけ薄く保つ：

```py
@router.post("/inbound/plan")
def calculate_inbound_plan(
    req: CalculateInboundPlanRequest,
    usecase: CalculateInboundPlanUseCase = Depends(get_calculate_inbound_plan_usecase),
):
    result = usecase.execute(req.to_input())
    return result.to_response()
```

- ここでは:
  - Request → Input DTO の変換
  - UseCase 呼び出し
  - Output DTO → Response の変換
    のみ行う

---

## 4. エラーハンドリング・ログ

- 例外は適切に捕捉し、API レイヤーで HTTP エラーコードに変換する
- 予期しない例外は 500 とし、ログに stacktrace を残す
- ログ出力は `logging` 経由で行い、`print` 文は原則禁止
- 共通的なエラーハンドリング方針・レスポンス形式については  
  `ERROR_HANDLING_GUIDE.md` および `backend_shared` のガイドに従う

---

## 5. ドキュメント・命名規約との関係

- DB カラム名は `column_naming_dictionary.md` のルールに従う
- API のフィールド名は基本的に DB（mart）のカラム名に合わせた snake_case とする
- フロントエンドでは camelCase に変換される前提で設計する
- Alembic に関する詳細なルールは DB 版ドキュメント（`20251127_webapp_development_conventions_db.md`）を参照

---

## 6. ドキュメント構造（docs ディレクトリ）

### 6-1. 配置ポリシー

- リポジトリ直下に `docs/` ディレクトリを配置する
- バックエンド共通ルールは `docs/backend/` 配下にまとめる
- サービス固有の仕様は、必要に応じてさらにサブディレクトリを切る

```text
docs/
  backend/
    20251127_webapp_development_conventions_backend.md  ← 本ファイル
    20251127_webapp_development_conventions_db.md       ← DB/スキーマ規約
    api/
      core_api_openapi.md
      ledger_api_openapi.md
      rag_api_openapi.md
    architecture/
      backend_architecture_overview.md
      sequence_diagrams.md
    error_handling/
      ERROR_HANDLING_GUIDE.md
```

### 6-2. ドキュメント分類

- **backend 共通規約**

  - 本ファイル（バックエンド開発規約）
  - DB 規約（スキーマ・マイグレーション・命名ルール）
  - エラーハンドリングガイド
  - ログ出力ポリシー

- **API 仕様**

  - OpenAPI 定義（自動生成 or 抜粋）
  - エンドポイント一覧
  - 代表的なリクエスト/レスポンス例

- **アーキテクチャ**

  - レイヤー構成図（api / core / infra / shared / backend_shared）
  - データフロー / シーケンス図
  - 各コンテナ（core_api / ledger_api / rag_api 等）の役割

- **運用・運用補助**
  - デプロイ手順
  - マイグレーション手順（Alembic 運用ルール）
  - 障害対応フロー

### 6-3. 更新ルール

- 実装と乖離しないように、**大きなリファクタリング・スキーマ変更のたびに docs を更新する**
- 新規サービス（例: 新しい FastAPI コンテナ）を追加する場合は:
  - `docs/backend/api/<service_name>_openapi.md`
  - 必要なら `docs/backend/architecture/<service_name>_overview.md`
    を追加すること

### 6-4. shared / backend_shared との関係

- 各コンテナ内の `app/shared/` に関するルールは本ファイルで定義する
- 複数コンテナで使用する共通基盤（`backend_shared/`）については、  
  別途 `docs/backend/backend_shared_guidelines.md` を作成し、
  - どの機能を backend_shared に置くか
  - 各コンテナからの依存ルール  
    を明文化する

---
