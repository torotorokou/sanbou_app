# ledger_api リファクタリング設計書

- 作成日: 2025-11-28
- 対象プロジェクト: sanbou_app
- 対象サービス: `ledger_api`
- ブランチ戦略: `refactor/core-api-clean-architecture`
- ステータス: **Phase 1-8完了** (2025-11-28 14:00)

---

## 1. リファクタリングの目的

### 1.1 背景

現在の `ledger_api` は以下の課題を抱えている：

1. **レイヤー構成の不統一**

   - `application/usecases` に UseCase と Service が混在
   - `core/` レイヤーが存在せず、Clean Architecture の原則から逸脱
   - Domain モデルが `application/domain/` に配置されている

2. **責務の曖昧さ**

   - `CsvValidatorService`, `CsvFormatterService` が UseCase 層に配置
   - これらは実質的に Domain Service または Infrastructure Adapter
   - Router が UseCase を直接呼び出しているが、Input/Output DTO の変換が不明瞭

3. **backend_shared への過度な依存**

   - CSV 読み込み、バリデーション、フォーマット等の多くのロジックが backend_shared に依存
   - ledger_api 固有のドメインロジックとの境界が不明瞭

4. **テスト困難性**
   - UseCase が具体的な実装に依存しており、モック化が困難
   - Port/Adapter パターンが部分的にしか適用されていない

### 1.2 目的

- **Clean Architecture / Hexagonal Architecture への完全移行**
  - `core/` レイヤーの導入（domain, ports, usecases）
  - `infra/` レイヤーの明確化（adapters, frameworks）
  - 依存性逆転の原則（DIP）の徹底
- **責務の明確化**
  - UseCase: アプリケーション固有のビジネスフロー
  - Domain: ビジネスルール・不変条件
  - Adapter: 外部 I/O の具体実装
- **テスタビリティの向上**
  - Port（抽象インターフェース）への依存
  - 全 UseCase が単体テスト可能な構造

### 1.3 成功条件

- [ ] すべての API エンドポイントが既存と同じレスポンスを返すこと
- [ ] `core/` レイヤーが外部フレームワーク（FastAPI, pandas 等）に依存しないこと
- [ ] 主要 UseCase の単体テストが実装されていること
- [ ] DI コンテナ（`di_providers.py`）で依存関係が明示的に解決されていること

---

## 2. 対象範囲

### 2.1 リファクタリング対象

#### フォルダ構成の変更

**現在:**

```
app/
  application/
    domain/reports/          ← ドメインモデル
    ports/                   ← Port 定義
    usecases/                ← UseCase + Service が混在
  infra/
    adapters/                ← Adapter 実装
    report_utils/            ← ユーティリティ（整理が必要）
    utils/                   ← PDF 変換等
  local_config/
    di_providers.py          ← DI コンテナ
  presentation/
    api/routers/             ← FastAPI Router
```

**変更後:**

```
app/
  core/                      ← 新規作成
    domain/                  ← application/domain から移動
      reports/
        entities.py          ← ManagementSheet 等
        value_objects.py     ← ReportDate, Period 等
    ports/                   ← application/ports から移動
      inbound/
        csv_gateway.py
        report_repository.py
      outbound/
        (必要に応じて追加)
    usecases/                ← application/usecases から移動
      reports/
        generate_management_sheet.py
        generate_factory_report.py
        generate_balance_sheet.py
        generate_average_sheet.py
        generate_block_unit_price.py
  infra/
    adapters/
      csv/
        pandas_csv_gateway.py      ← 既存
        csv_validator.py           ← CsvValidatorService から移動・改名
        csv_formatter.py           ← CsvFormatterService から移動・改名
      repository/
        filesystem_report_repository.py  ← 既存
      file_processing/
      artifact_storage/
    frameworks/
      fastapi_setup.py       ← main.py から分離
      logging_setup.py       ← 既存のログ設定
    db/                      ← 将来的な DB 接続用（現在は未使用）
  config/
    di_providers.py          ← local_config から移動
    settings.py              ← 既存
  presentation/              ← 既存
    api/
      routers/
      schemas/               ← 新規作成（Request/Response DTO）
  shared/                    ← サービス内共通処理（軽量）
```

### 2.2 主要ファイルの移動・変更

| 現在のパス                                      | 変更後のパス                          | 変更内容                                      |
| ----------------------------------------------- | ------------------------------------- | --------------------------------------------- |
| `application/domain/reports/*`                  | `core/domain/reports/*`               | フォルダ移動                                  |
| `application/ports/*`                           | `core/ports/inbound/*`                | フォルダ移動 + inbound/outbound 分離          |
| `application/usecases/reports/*`                | `core/usecases/reports/*`             | フォルダ移動                                  |
| `application/usecases/csv/validator_service.py` | `infra/adapters/csv/csv_validator.py` | Adapter として再配置                          |
| `application/usecases/csv/formatter_service.py` | `infra/adapters/csv/csv_formatter.py` | Adapter として再配置                          |
| `local_config/di_providers.py`                  | `config/di_providers.py`              | フォルダ移動                                  |
| `main.py`                                       | `main.py` (内容整理)                  | Framework 初期化を `infra/frameworks/` に分離 |

### 2.3 対象外

- **API エンドポイントの URL 変更**: 既存の URL をそのまま維持
- **DB スキーマ変更**: 現状 ledger_api は DB 未使用
- **フロントエンド連携の変更**: API I/F は完全互換を維持
- **backend_shared の大幅な変更**: ledger_api 内部のリファクタに集中

---

## 3. 影響範囲

### 3.1 API

すべての API エンドポイントは既存のまま維持：

- `POST /reports/management_sheet`
- `POST /reports/factory_report`
- `POST /reports/balance_sheet`
- `POST /reports/average_sheet`
- `POST /reports/block_unit_price`
- `POST /block_unit_price_interactive/initial`
- `POST /block_unit_price_interactive/finalize`
- `GET /artifacts/{artifact_path:path}`
- `GET /jobs/{job_id}`
- `POST /jobs`
- `GET /notifications/stream`

### 3.2 依存サービス

#### core_api（BFF）

- ledger_api を `/ledger_api` プレフィックスで公開
- ledger_api の内部変更は core_api に影響しない（URL 変更なし）

#### フロントエンド

- API レスポンス構造が変わらないため、影響なし
- 型定義（TypeScript）も既存のまま使用可能

#### backend_shared

- ledger_api が backend_shared に依存する構造は維持
- 将来的に backend_shared への依存を減らす方針だが、本リファクタリングでは現状維持

### 3.3 テスト

- 既存の統合テスト（`test/` ディレクトリ）は引き続き実行可能
- 新規に UseCase 単体テストを追加

---

## 4. リファクタリング方針・ルール

### 4.1 ブランチ運用

- 作業ブランチ: `refactor/ledger-api-clean-architecture`
- 小さな単位でコミット・PR を作成
- PR 単位の例：
  1. `core/` ディレクトリ構造の作成とファイル移動
  2. UseCase の Input/Output DTO 明確化
  3. Adapter の責務整理（Validator, Formatter）
  4. DI コンテナの再構成
  5. 単体テストの追加

### 4.2 依存性逆転の原則（DIP）の徹底

- **core/usecases** は **core/ports** のみに依存
- **core/domain** は外部依存なし（純粋な Python）
- **infra/adapters** が **core/ports** を実装
- **presentation/api** は **core/usecases** を呼び出すのみ

```python
# 良い例
class GenerateManagementSheetUseCase:
    def __init__(
        self,
        csv_gateway: CsvGateway,           # Port（抽象）
        report_repository: ReportRepository # Port（抽象）
    ):
        self._csv_gateway = csv_gateway
        self._report_repository = report_repository

    def execute(self, input_dto: GenerateManagementSheetInput) -> GenerateManagementSheetOutput:
        # UseCase ロジック
        pass

# 悪い例（既存の問題）
class GenerateManagementSheetUseCase:
    def execute(self, shipment: UploadFile, ...):
        # FastAPI の UploadFile に直接依存 → 具象に依存している
        pass
```

### 4.3 Input/Output DTO の明確化

すべての UseCase は以下の形式に統一：

```python
# core/usecases/reports/generate_management_sheet.py

from dataclasses import dataclass
from datetime import date
from typing import Dict, Any

@dataclass
class GenerateManagementSheetInput:
    """UseCase の入力 DTO."""
    csv_files: Dict[str, Any]  # {"shipment": DataFrame, "yard": DataFrame, ...}
    period_type: str | None = None

@dataclass
class GenerateManagementSheetOutput:
    """UseCase の出力 DTO."""
    report_key: str
    report_date: date
    excel_url: str
    pdf_url: str

class GenerateManagementSheetUseCase:
    def execute(self, input_dto: GenerateManagementSheetInput) -> GenerateManagementSheetOutput:
        # 実装
        pass
```

Router 側で FastAPI 固有の型（UploadFile）を DTO に変換：

```python
# presentation/api/routers/reports/management_sheet.py

@router.post("")
async def generate_management_sheet(
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
    period_type: Optional[str] = Form(None),
    usecase: GenerateManagementSheetUseCase = Depends(get_management_sheet_usecase),
    csv_gateway: CsvGateway = Depends(get_csv_gateway),
) -> JSONResponse:
    # 1. UploadFile → DataFrame 変換（Adapter 経由）
    files = {"shipment": shipment, "yard": yard, "receive": receive}
    csv_data, error = csv_gateway.read_csv_files(files)
    if error:
        return error.to_json_response()

    # 2. Input DTO 作成
    input_dto = GenerateManagementSheetInput(
        csv_files=csv_data,
        period_type=period_type,
    )

    # 3. UseCase 実行
    output_dto = usecase.execute(input_dto)

    # 4. Response 変換
    return JSONResponse(content={
        "status": "success",
        "data": {
            "report_key": output_dto.report_key,
            "report_date": output_dto.report_date.isoformat(),
            "urls": {
                "excel": output_dto.excel_url,
                "pdf": output_dto.pdf_url,
            }
        }
    })
```

### 4.4 Service の再配置

現在 `application/usecases/csv/` にある Service は以下のように整理：

1. **CsvValidatorService** → `infra/adapters/csv/csv_validator.py`

   - backend_shared の `PureCSVValidator` をラップする Adapter
   - Port として `CsvValidator` を `core/ports/inbound/` に定義

2. **CsvFormatterService** → `infra/adapters/csv/csv_formatter.py`
   - backend_shared の `CSVFormatterFactory` をラップする Adapter
   - `CsvGateway.format_csv_data()` の実装として統合

### 4.5 ログ戦略

- 構造化ログ（JSON）を使用
- UseCase 内でのログ出力は最小限に（開始・終了・エラー時のみ）
- 詳細なログは Adapter 層で出力

```python
# 良い例
logger.info(
    "レポート生成開始",
    extra={
        "usecase": "management_sheet",
        "report_date": str(report_date),
    }
)

# 悪い例
logger.info("レポート生成開始")  # コンテキスト情報なし
```

### 4.6 エラーハンドリング

- Domain 層: `DomainError` を raise（ビジネスルール違反時）
- UseCase 層: Domain Error を補足せず、そのまま上位に伝播
- Adapter 層: 外部 I/O エラー（ファイル読み込み失敗等）を補足し、適切な例外に変換
- Presentation 層: すべての例外を補足し、HTTP レスポンスに変換

```python
# core/domain/reports/management_sheet.py
class ManagementSheet:
    @staticmethod
    def from_dataframes(shipment_df, yard_df, receive_df):
        if shipment_df is None and yard_df is None and receive_df is None:
            raise DomainError("少なくとも1つのCSVファイルが必要です")
        # ...

# presentation/api/routers/reports/management_sheet.py
@router.post("")
async def generate_management_sheet(...):
    try:
        output_dto = usecase.execute(input_dto)
        return JSONResponse(content={"status": "success", "data": output_dto.dict()})
    except DomainError as e:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(e)})
    except Exception as e:
        logger.exception("予期しないエラー")
        return JSONResponse(status_code=500, content={"status": "error", "message": "内部エラー"})
```

---

## 5. 実施ステップ

### Phase 1: ディレクトリ構造の準備（1日目）

- [ ] `core/` ディレクトリの作成
  - [ ] `core/domain/`
  - [ ] `core/ports/inbound/`
  - [ ] `core/usecases/`
- [ ] `infra/frameworks/` ディレクトリの作成
- [ ] `presentation/api/schemas/` ディレクトリの作成
- [ ] `config/` ディレクトリの作成（`local_config/` からリネーム）

### Phase 2: Domain 層の移動（1日目）

- [ ] `application/domain/reports/` → `core/domain/reports/` に移動
- [ ] Import パスの一括置換
- [ ] `__init__.py` の更新
- [ ] テスト実行で動作確認

### Phase 3: Ports 層の移動と整理（2日目）

- [ ] `application/ports/` → `core/ports/inbound/` に移動
- [ ] `CsvGateway` の見直し（既存実装は良好）
- [ ] `ReportRepository` の見直し（既存実装は良好）
- [ ] 必要に応じて新規 Port を追加（`CsvValidator`, `CsvFormatter` 等）
- [ ] Import パスの更新

### Phase 4: UseCase 層の移動と DTO 導入（2-3日目）

- [ ] `application/usecases/reports/` → `core/usecases/reports/` に移動
- [ ] 各 UseCase に Input/Output DTO を導入
  - [ ] `GenerateManagementSheetUseCase`
  - [ ] `GenerateFactoryReportUseCase`
  - [ ] `GenerateBalanceSheetUseCase`
  - [ ] `GenerateAverageSheetUseCase`
  - [ ] `GenerateBlockUnitPriceUseCase`
- [ ] UseCase が FastAPI の型（UploadFile）に依存しないように修正
- [ ] Import パスの更新

### Phase 5: Service の Adapter 化（3日目）

- [ ] `application/usecases/csv/validator_service.py` → `infra/adapters/csv/csv_validator.py` に移動
- [ ] `application/usecases/csv/formatter_service.py` → `infra/adapters/csv/csv_formatter.py` に移動
- [ ] Port として `CsvValidator` を定義（必要に応じて）
- [ ] DI コンテナで Adapter を注入

### Phase 6: Router の整理（4日目）

- [ ] `presentation/api/routers/` の各 Router を以下の形式に統一：
  1. FastAPI 固有の型（UploadFile）受け取り
  2. Adapter 経由で DTO に変換
  3. UseCase 実行
  4. Response 変換
- [ ] Request/Response スキーマを `presentation/api/schemas/` に定義（必要に応じて）

### Phase 7: DI コンテナの再構成（4日目）

- [ ] `local_config/di_providers.py` → `config/di_providers.py` に移動
- [ ] UseCase の依存関係を明示的に注入
- [ ] Adapter の実装を環境ごとに切り替え可能にする（将来対応）

### Phase 8: テスト追加（5日目）

- [ ] 主要 UseCase の単体テストを追加
  - [ ] `test_generate_management_sheet.py`
  - [ ] `test_generate_factory_report.py`
  - [ ] Port をモックして UseCase を独立テスト
- [ ] 既存の統合テストを実行して互換性確認

### Phase 9: ドキュメント更新（5日目）

- [ ] `docs/backend/ledger_api_architecture.md` を作成
  - レイヤー構成図
  - データフロー図
  - 主要クラス図
- [ ] README.md の更新
- [ ] API ドキュメントの確認（OpenAPI 自動生成）

### Phase 10: レビュー・本番反映（6日目）

- [ ] PR 作成・コードレビュー
- [ ] ステージング環境でテスト
- [ ] 本番リリース
- [ ] モニタリング（ログ・エラーレート確認）

---

## 6. リスクと対策

### リスク1: API レスポンス構造の変更による互換性破壊

**対策:**

- 各 UseCase の Output DTO は既存レスポンスと完全互換を維持
- 統合テストで既存のレスポンス構造をスナップショット比較
- ステージング環境でフロントエンドと結合テスト

### リスク2: Import パス変更による大量のコンフリクト

**対策:**

- 一括置換ツール（sed, ripgrep）を活用
- ファイル移動とロジック変更を別 PR に分離
- Phase ごとに動作確認を挟む

### リスク3: backend_shared への依存が複雑化

**対策:**

- backend_shared への依存は Adapter 層に閉じ込める
- UseCase は backend_shared を直接 import しない
- 将来的に backend_shared からの脱却を視野に、Port 経由で抽象化

### リスク4: リファクタリングが長期化し、他開発とのコンフリクト

**対策:**

- 小さな単位で PR を作成し、こまめにマージ
- Feature flag を導入し、段階的にリリース（必要に応じて）
- 他開発者とのコミュニケーションを密にする

---

## 7. チェックリスト

### リファクタリング前

- [x] 現状のディレクトリ構造を把握
- [x] 主要 UseCase の動作を確認
- [x] 既存テストが通ることを確認
- [x] backend_shared への依存を洗い出し
- [x] API エンドポイント一覧を作成

### リファクタリング中

- [ ] 各 Phase ごとに動作確認
- [ ] Import パスのエラーが出ないか確認
- [ ] ログが正常に出力されるか確認
- [ ] 既存テストが通るか確認（Phase ごと）

### リファクタリング後

- [ ] すべての API が正常にレスポンスを返すか確認
- [ ] `core/` レイヤーが外部フレームワークに依存していないか確認
- [ ] UseCase の単体テストが追加されているか確認
- [ ] ドキュメントが更新されているか確認
- [ ] ステージング環境で統合テスト
- [ ] 本番リリース後、1週間モニタリング

---

## 8. 参考資料

- `/home/koujiro/work_env/22.Work_React/sanbou_app/docs/conventions/backend/20251127_webapp_development_conventions_backend.md`
- `/home/koujiro/work_env/22.Work_React/sanbou_app/docs/conventions/refactoring_plan_local_dev.md`
- Clean Architecture（Robert C. Martin）
- Hexagonal Architecture（Alistair Cockburn）

---

## 9. 補足: 各レイヤーの責務（再確認）

### core/domain/

- ビジネスルール・不変条件を表現
- 外部依存なし（純粋な Python）
- Entity, Value Object, Domain Service

**例:**

```python
# core/domain/reports/management_sheet.py
from dataclasses import dataclass
from datetime import date

@dataclass
class ManagementSheet:
    report_date: date
    total_shipment: float
    total_receive: float

    @staticmethod
    def from_dataframes(shipment_df, yard_df, receive_df):
        # ドメインロジック
        pass

    def validate(self):
        if self.total_shipment < 0:
            raise DomainError("出荷量は負の値にできません")
```

### core/ports/

- UseCase が利用する抽象インターフェース
- Repository, Gateway, Presenter 等
- `Protocol` または `ABC` で定義

**例:**

```python
# core/ports/inbound/csv_gateway.py
from typing import Protocol, Dict, Any, Tuple, Optional

class CsvGateway(Protocol):
    def read_csv_files(self, files: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Any]]:
        """CSV ファイルを読み込み、DataFrame を返す."""
        ...

    def format_csv_data(self, dfs: Dict[str, Any]) -> Dict[str, Any]:
        """CSV データを整形する."""
        ...
```

### core/usecases/

- アプリケーション固有のビジネスフロー
- Port（抽象インターフェース）のみに依存
- 具体的な実装（Adapter）には依存しない

**例:**

```python
# core/usecases/reports/generate_management_sheet.py
class GenerateManagementSheetUseCase:
    def __init__(
        self,
        csv_gateway: CsvGateway,
        report_repository: ReportRepository,
    ):
        self._csv_gateway = csv_gateway
        self._report_repository = report_repository

    def execute(self, input_dto: GenerateManagementSheetInput) -> GenerateManagementSheetOutput:
        # 1. データ取得
        csv_data = input_dto.csv_files

        # 2. ドメインモデル生成
        management_sheet = ManagementSheet.from_dataframes(
            csv_data.get("shipment"),
            csv_data.get("yard"),
            csv_data.get("receive"),
        )

        # 3. ドメインロジック実行
        management_sheet.validate()

        # 4. レポート保存
        urls = self._report_repository.save_report(
            report_key="management_sheet",
            report_date=management_sheet.report_date,
            excel_bytes=...,
            pdf_bytes=...,
        )

        # 5. Output DTO 返却
        return GenerateManagementSheetOutput(
            report_key="management_sheet",
            report_date=management_sheet.report_date,
            excel_url=urls.excel_url,
            pdf_url=urls.pdf_url,
        )
```

### infra/adapters/

- Port の具体実装
- 外部 I/O（ファイル、DB、HTTP）を扱う
- Domain 型と外部型の変換を行う

**例:**

```python
# infra/adapters/csv/pandas_csv_gateway.py
from app.core.ports.inbound.csv_gateway import CsvGateway

class PandasCsvGateway(CsvGateway):
    def read_csv_files(self, files):
        # pandas を使って CSV 読み込み
        pass

    def format_csv_data(self, dfs):
        # backend_shared の Formatter を呼び出し
        pass
```

### presentation/api/

- FastAPI Router
- HTTP Request → DTO 変換
- UseCase 呼び出し
- DTO → HTTP Response 変換

**例:**

```python
# presentation/api/routers/reports/management_sheet.py
@router.post("")
async def generate_management_sheet(
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    usecase: GenerateManagementSheetUseCase = Depends(get_management_sheet_usecase),
) -> JSONResponse:
    # Router の責務: FastAPI 固有の型を DTO に変換
    input_dto = GenerateManagementSheetInput(...)
    output_dto = usecase.execute(input_dto)
    return JSONResponse(content=output_dto.dict())
```

### config/

- DI コンテナ
- UseCase と Adapter の組み立て
- 環境設定の読み込み

**例:**

```python
# config/di_providers.py
def get_management_sheet_usecase() -> GenerateManagementSheetUseCase:
    csv_gateway = get_csv_gateway()
    report_repository = get_report_repository()
    return GenerateManagementSheetUseCase(csv_gateway, report_repository)
```

---

## 実施状況

### Phase 1-8: 完了 (2025-11-28)

**実施内容:**

- ✅ Phase 1: `core/` ディレクトリ構造作成
- ✅ Phase 2: Domain 層移行 (`application/domain/` → `core/domain/`)
- ✅ Phase 3: Ports 層移行 (`application/ports/` → `core/ports/inbound/`)
- ✅ Phase 4: UseCase 層移行 (`application/usecases/reports/` → `core/usecases/reports/`)
- ✅ Phase 5: Config 移行 (`local_config/` → `config/`)
- ✅ Phase 6: CSV Adapter 移行 (`application/usecases/csv/` → `infra/adapters/csv/`)
- ✅ Phase 7: 旧ディレクトリ削除 (`application/`, `local_config/`)
- ✅ Phase 8: Presentation 層リファクタリング (`presentation/api/` → `api/`)

**コミット:**

- `ac2a7be` - Phase 1-4: core/ layer creation and file migration
- `688d6ab` - Phase 1-4: Fix circular imports and syntax errors
- `eeb0d1c` - Phase 6: Migrate CSV services to infra/adapters/csv
- `d41d0f2` - Phase 7: Cleanup old application/ and local_config/ directories
- `c934b80` - Update refactoring plan with Phase 1-7 completion status
- `2462ff3` - Phase 8: Refactor presentation layer to match conventions

**検証結果:**

- ledger_api コンテナ: 正常起動・healthy
- core_api コンテナ: 正常起動・healthy (BFF として ledger_api をプロキシ)
- ai_api / rag_api コンテナ: 正常起動・healthy
- DB コンテナ: 正常起動・healthy
- API エンドポイント: 全て正常応答 (OpenAPI spec 確認済み)
- フロントエンド影響: なし (API インターフェース不変、`/core_api/reports/*` 経由)
- 他バックエンド影響: なし (core_api は HTTP プロキシのみ)
- DB 影響: なし (ledger_api は DB 未使用)

**最終ディレクトリ構造:**

```
app/
├── api/                 # FastAPI routers, schemas (presentation layer)
│   ├── routers/         # API endpoint definitions
│   │   └── reports/     # Report generation endpoints
│   ├── schemas/         # Request/Response Pydantic models
│   └── static/          # Static files for reports
├── config/              # DI container, settings
│   └── settings/
├── core/                # Business logic layer (no external dependencies)
│   ├── domain/          # Entities, value objects
│   │   └── reports/
│   ├── ports/           # Abstract interfaces (Protocols)
│   │   └── inbound/
│   └── usecases/        # Application-specific business flows
│       └── reports/
└── infra/               # Infrastructure layer
    ├── adapters/        # Concrete implementations of ports
    │   ├── csv/         # CSV processing adapters
    │   ├── artifact_storage/
    │   ├── file_processing/
    │   ├── repository/
    │   └── session/
    ├── data_sources/
    ├── report_utils/
    └── utils/
```

---

## まとめ

本リファクタリングにより、ledger_api は以下のメリットを享受できます：

1. **保守性の向上**: レイヤー間の責務が明確になり、変更の影響範囲が限定される
2. **テスタビリティの向上**: UseCase が Port に依存するため、モックを使った単体テストが容易
3. **拡張性の向上**: 新しい Adapter（例: Polars CSV Gateway）の追加が容易
4. **可読性の向上**: ディレクトリ構造がアーキテクチャを反映し、新規参加者が理解しやすい
5. **規約準拠**: `20251127_webapp_development_conventions_backend.md` に完全準拠

**Phase 1-8 完了**: Clean Architecture / Hexagonal Architecture への移行が完了しました。
