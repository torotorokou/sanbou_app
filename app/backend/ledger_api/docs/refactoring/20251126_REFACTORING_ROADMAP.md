# ledger_api Clean Architecture リファクタリングロードマップ

作成日: 2025-11-26  
前提: `REFACTORING_ASSESSMENT_REPORT.md` の分析結果に基づく

---

## 全体方針

### ゴール
1. **ledger_api を Clean Architecture / Hexagonal Architecture に段階的に近づける**
2. **小さく・安全に・連続して** リファクタリング（1 コミット = 1 ステップ）
3. **core_api にも適用可能な汎用パターンを確立**

### 原則
- ✅ **既存 API の後方互換性を維持**（URL/Request/Response は変更しない）
- ✅ **段階的移行**（1 エンドポイントずつ）
- ✅ **テストで安全性を担保**（各ステップで既存テストを実行）
- ✅ **SOLID 原則の遵守**（特に SRP, DIP）

---

## ステップ一覧

### フェーズ 1: 基盤整備（準備作業）

#### **ステップ 1: ディレクトリ構造の準備と Port/Adapter の骨格作成**
- **目的**: Clean Architecture のディレクトリ構造を作成し、Port インターフェースの骨格を定義
- **対象ディレクトリ**:
  - 新規作成: `app/core/ports/`, `app/infra/adapters/`
  - 既存維持: `app/api/`, `app/api/services/`
- **変更内容**:
  1. `app/core/ports/` ディレクトリを作成
  2. `app/core/ports/csv_gateway.py` を作成（CSV 読み込みの抽象）
  3. `app/core/ports/report_repository.py` を作成（レポート保存の抽象）
  4. `app/infra/adapters/` ディレクトリを作成
  5. `app/infra/adapters/pandas_csv_gateway.py` を作成（暫定実装）
  6. `app/infra/adapters/filesystem_report_repository.py` を作成（暫定実装）
- **期待効果**:
  - ✅ Port/Adapter パターンの受け皿を用意
  - ✅ 後続ステップで UseCase が Port に依存できる
- **リスク**:
  - ⚠️ まだ使用されていないコードが増える（次ステップで接続）
- **想定コミットメッセージ**: `refactor(infra): introduce port/adapter skeleton for CSV and report storage`

---

#### **ステップ 2: UseCase 層の骨格作成（factory_report 専用）**
- **目的**: 最も利用頻度が高い `factory_report` エンドポイント用の UseCase を作成
- **対象ファイル**:
  - 新規作成: `app/core/usecases/reports/generate_factory_report.py`
  - 既存参照: `app/api/services/report/ledger/factory_report.py`
- **変更内容**:
  1. `app/core/usecases/reports/` ディレクトリを作成
  2. `GenerateFactoryReportUseCase` クラスを定義
     ```python
     class GenerateFactoryReportUseCase:
         def __init__(self, csv_gateway: CsvGateway, report_repo: ReportRepository):
             self.csv_gateway = csv_gateway
             self.report_repo = report_repo
         
         def execute(self, files: Dict[str, UploadFile], period_type: Optional[str] = None) -> ArtifactUrls:
             # 1. CSV 読み込み（Port 経由）
             # 2. 検証
             # 3. ドメインロジック呼び出し（既存 services/report/ledger/factory_report.process）
             # 4. 保存（Port 経由）
             # 5. 署名付き URL 返却
             ...
     ```
  3. 既存の `ReportProcessingService` のロジックを UseCase に移管
- **期待効果**:
  - ✅ アプリケーション層の明確化
  - ✅ Port に依存する設計の実践
- **リスク**:
  - ⚠️ まだエンドポイントから呼ばれていない（次ステップで接続）
- **想定コミットメッセージ**: `refactor(usecases): introduce GenerateFactoryReportUseCase with port dependencies`

---

#### **ステップ 3: factory_report エンドポイントを UseCase 経由に切り替え**
- **目的**: エンドポイントから UseCase を呼び出す形に変更し、動作確認
- **対象ファイル**:
  - 編集: `app/api/endpoints/reports/factory_report.py`
  - 編集: `app/main.py`（DI 設定）
- **変更内容**:
  1. `app/config/di_providers.py` を作成（依存注入ハブ）
     ```python
     def get_factory_report_usecase() -> GenerateFactoryReportUseCase:
         csv_gateway = PandasCsvGateway()
         report_repo = FileSystemReportRepository()
         return GenerateFactoryReportUseCase(csv_gateway, report_repo)
     ```
  2. `factory_report.py` のエンドポイントを書き換え
     ```python
     @router.post("")
     async def generate_factory_report(
         shipment: UploadFile = File(None),
         yard: UploadFile = File(None),
         receive: UploadFile = File(None),
         period_type: Optional[str] = Form(None),
         usecase: GenerateFactoryReportUseCase = Depends(get_factory_report_usecase)
     ) -> Response:
         files = {k: v for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items() if v}
         result = usecase.execute(files, period_type)
         return result.to_response()
     ```
  3. 既存の `ReportProcessingService` 呼び出しを削除
- **期待効果**:
  - ✅ エンドポイントが UseCase のみに依存
  - ✅ DIP（依存性逆転の原則）の実践
- **テスト**: `test/test_api_readiness.py` を実行し、エンドポイントが正常に動作することを確認
- **想定コミットメッセージ**: `refactor(api): connect factory_report endpoint to UseCase with DI`

---

### フェーズ 2: ドメイン層の整備

#### **ステップ 4: FactoryReport ドメインモデルの抽出**
- **目的**: pandas DataFrame 依存を緩和し、ドメインオブジェクトを導入
- **対象ファイル**:
  - 新規作成: `app/core/domain/reports/factory_report.py`
  - 編集: `app/api/services/report/ledger/factory_report.py`
- **変更内容**:
  1. `FactoryReport` Entity を定義
     ```python
     @dataclass(frozen=True)
     class FactoryReport:
         report_date: date
         shipment_items: List[ShipmentItem]
         yard_items: List[YardItem]
         
         def to_dataframe(self) -> pd.DataFrame:
             # Entity → DataFrame 変換（インフラ層で使用）
             ...
     ```
  2. `ShipmentItem`, `YardItem` など ValueObject を定義
  3. 既存の `process()` 関数を `FactoryReport.from_dataframes()` ファクトリメソッドに移管
- **期待効果**:
  - ✅ ドメインロジックが DataFrame から独立
  - ✅ 不変条件をコンストラクタで保証
- **リスク**:
  - ⚠️ 大きな変更（慎重にテスト）
- **想定コミットメッセージ**: `refactor(domain): introduce FactoryReport entity and value objects`

---

#### **ステップ 5: UseCase を ドメインモデル経由に変更**
- **目的**: UseCase が DataFrame ではなく Entity を扱うように変更
- **対象ファイル**:
  - 編集: `app/core/usecases/reports/generate_factory_report.py`
- **変更内容**:
  1. UseCase 内で `FactoryReport.from_dataframes(dfs)` を呼び出し
  2. `report.to_dataframe()` でテンプレート書き込み用 DataFrame に変換
  3. DataFrame 依存を最小限に抑える
- **期待効果**:
  - ✅ UseCase がドメインロジックに集中
  - ✅ ビジネスルールの可視化
- **想定コミットメッセージ**: `refactor(usecases): use FactoryReport entity instead of raw DataFrame`

---

### フェーズ 3: 水平展開

#### **ステップ 6: balance_sheet エンドポイントを同じパターンで移行**
- **目的**: factory_report で確立したパターンを他の帳票に適用
- **対象ファイル**:
  - 新規作成: `app/core/usecases/reports/generate_balance_sheet.py`
  - 新規作成: `app/core/domain/reports/balance_sheet.py`
  - 編集: `app/api/endpoints/reports/balance_sheet.py`
- **変更内容**: ステップ 2〜5 と同じ流れ
- **期待効果**:
  - ✅ パターンの再利用性確認
  - ✅ 残りの帳票への適用がスムーズに
- **想定コミットメッセージ**: `refactor(api): migrate balance_sheet to UseCase + domain model pattern`

---

#### **ステップ 7: average_sheet / management_sheet の移行**
- **目的**: 残りの帳票エンドポイントを順次移行
- **変更内容**: ステップ 6 と同様
- **想定コミットメッセージ**: 
  - `refactor(api): migrate average_sheet to Clean Architecture pattern`
  - `refactor(api): migrate management_sheet to Clean Architecture pattern`

---

### フェーズ 4: インフラ層の洗練

#### **ステップ 8: Port 実装の抽象化（dev/staging/prod 対応）**
- **目的**: 環境ごとに異なる実装を差し替え可能にする
- **対象ファイル**:
  - 編集: `app/config/di_providers.py`
  - 新規作成: `app/infra/adapters/gcs_report_repository.py`（将来の GCS 対応）
- **変更内容**:
  1. `di_providers.py` で環境変数に応じて実装を切り替え
     ```python
     def get_report_repository() -> ReportRepository:
         if settings.stage == "prod":
             return GcsReportRepository()
         else:
             return FileSystemReportRepository()
     ```
  2. GCS 実装は暫定的に空実装（TODO コメント）
- **期待効果**:
  - ✅ 環境ごとの差し替えが容易
  - ✅ テスト時にモック実装を注入可能
- **想定コミットメッセージ**: `refactor(infra): enable environment-specific repository implementations in DI`

---

#### **ステップ 9: Artifact 保存ロジックの Port 化**
- **目的**: `artifacts/artifact_service.py` を Port/Adapter パターンに準拠させる
- **対象ファイル**:
  - 編集: `app/core/ports/report_repository.py`（メソッド追加）
  - 編集: `app/infra/adapters/filesystem_report_repository.py`
  - 削除候補: `app/api/services/report/artifacts/artifact_service.py`（機能を Adapter に移管）
- **変更内容**:
  1. `ReportRepository` に `save_with_signed_url()` メソッドを追加
  2. `FileSystemReportRepository` に既存の artifact_service のロジックを統合
  3. UseCase から `report_repo.save_with_signed_url()` を呼び出す
- **期待効果**:
  - ✅ アーティファクト管理の一元化
  - ✅ Port 抽象への完全移行
- **想定コミットメッセージ**: `refactor(infra): integrate artifact storage into ReportRepository port`

---

### フェーズ 5: クリーンアップ

#### **ステップ 10: 旧 ReportProcessingService の削除**
- **目的**: 移行完了後、使われなくなったコードを削除
- **対象ファイル**:
  - 削除候補: `app/api/services/report/core/processors/report_processing_service.py`
  - 削除候補: `app/api/services/report/core/base_generators/base_report_generator.py`
- **変更内容**:
  1. すべてのエンドポイントが UseCase 経由になっていることを確認
  2. `ReportProcessingService` への参照を grep で検索し、残骸がないことを確認
  3. ファイルを削除
- **期待効果**:
  - ✅ コードベースのスリム化
  - ✅ 混乱の原因となる旧コードの除去
- **想定コミットメッセージ**: `chore: remove deprecated ReportProcessingService after full migration`

---

#### **ステップ 11: Streamlit 残骸のクリーンアップ**
- **目的**: st_app 関連の未使用コードを削除
- **対象ファイル**:
  - 削除候補: `app/api/config/settings/loader.py`（Streamlit 専用設定）
  - 調査: `app/streamlit.py`（まだ使用されているか確認）
  - 調査: `app/api/config/loader/main_path.py`（st_app パスのハードコード）
- **変更内容**:
  1. `grep -r "from app.api.config.settings.loader import"` で使用箇所を確認
  2. 未使用であれば削除
  3. `streamlit.py` の参照箇所を調査し、必要に応じて削除または隔離
- **期待効果**:
  - ✅ st_app 依存の完全除去
  - ✅ コードベースの簡潔化
- **想定コミットメッセージ**: `chore: remove unused Streamlit-related config and stubs`

---

### フェーズ 6: ドキュメント化とテスト拡充

#### **ステップ 12: UseCase 単体テストの追加**
- **目的**: リファクタリング後の安全性を担保
- **対象ファイル**:
  - 新規作成: `test/unit/usecases/test_generate_factory_report.py`
  - 新規作成: `test/unit/domain/test_factory_report.py`
- **変更内容**:
  1. モック Port を使った UseCase のテスト
  2. ドメインオブジェクトの不変条件テスト
- **期待効果**:
  - ✅ リグレッション防止
  - ✅ ドメインロジックの信頼性向上
- **想定コミットメッセージ**: `test: add unit tests for UseCases and domain entities`

---

#### **ステップ 13: core_api 適用ガイドの作成**
- **目的**: ledger_api で確立したパターンを core_api に適用するためのドキュメント化
- **対象ファイル**:
  - 新規作成: `docs/CORE_LEDGER_REFACTORING_PATTERN.md`
- **変更内容**:
  1. ledger_api で行った変更のパターンをまとめる
  2. core_api に適用する際のチェックリストを作成
  3. ディレクトリ構造のテンプレートを提供
- **期待効果**:
  - ✅ core_api への水平展開が容易に
  - ✅ チーム全体での知識共有
- **想定コミットメッセージ**: `docs: add refactoring pattern guide for core_api migration`

---

## 優先度マトリクス

| ステップ | 優先度 | 影響範囲 | リスク | 推定工数 |
|---------|--------|---------|--------|---------|
| 1. Port/Adapter 骨格 | ⭐⭐⭐ | 小 | 低 | 0.5日 |
| 2. UseCase 骨格 | ⭐⭐⭐ | 小 | 低 | 0.5日 |
| 3. factory_report 接続 | ⭐⭐⭐ | 中 | 中 | 1日 |
| 4. ドメインモデル抽出 | ⭐⭐ | 大 | 高 | 2日 |
| 5. UseCase ドメイン対応 | ⭐⭐ | 中 | 中 | 1日 |
| 6-7. 水平展開 | ⭐⭐ | 大 | 中 | 3日 |
| 8. Port 抽象化 | ⭐ | 小 | 低 | 0.5日 |
| 9. Artifact Port化 | ⭐ | 中 | 中 | 1日 |
| 10-11. クリーンアップ | ⭐ | 小 | 低 | 0.5日 |
| 12. テスト拡充 | ⭐⭐ | 中 | 低 | 1日 |
| 13. ドキュメント化 | ⭐ | 小 | 低 | 0.5日 |

**合計推定工数**: 約 11.5 日

---

## 次のアクション

このロードマップに基づき、**ステップ 1: Port/Adapter 骨格の作成** から着手します。

各ステップの実行前に、必ず以下を行います：
1. ✅ 目的の再確認
2. ✅ 変更内容の明示
3. ✅ 期待効果とリスクの確認
4. ✅ テスト実行
5. ✅ コミットメッセージの作成

準備が整い次第、ステップ 1 の実装を開始してください。
