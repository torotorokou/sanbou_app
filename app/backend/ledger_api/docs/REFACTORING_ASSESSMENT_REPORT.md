# ledger_api リファクタリング現状把握レポート

作成日: 2025-11-26

## 0. 現状の構造と依存関係

### 0.1 コンテナの識別

このコンテナは **ledger_api** であり、帳票生成・日報管理・PDF出力機能を提供するFastAPIサーバーです。

- **起点**: `app/main.py`
- **役割**: core_api（BFF）から呼び出される内部API
- **URL プレフィックス**: 内部論理パス（`/reports/*`, `/block_unit_price_interactive/*`など）を公開し、core_api が `/core_api` プレフィックスを付与

### 0.2 FastAPI の起点と Router 構成

#### エントリポイント: `app/main.py`
```python
app = FastAPI(title="帳票・日報API", ...)
app.include_router(block_unit_price_router, prefix="/block_unit_price_interactive")
app.include_router(reports_router, prefix="/reports")
app.include_router(jobs_router, prefix="")
app.include_router(notifications_router, prefix="")
app.include_router(report_artifact_router, prefix=artifact_prefix)
```

#### Router マウント構造
- **`api/endpoints/reports/__init__.py`**: 帳票系の統合ルーター
  - `factory_report.py` → `/reports/factory_report`
  - `balance_sheet.py` → `/reports/balance_sheet`
  - `average_sheet.py` → `/reports/average_sheet`
  - `management_sheet.py` → `/reports/management_sheet`
  - `block_unit_price_interactive.py` → `/block_unit_price_interactive`
- **`api/endpoints/jobs.py`**: ジョブ管理系（未確認）
- **`api/endpoints/notifications.py`**: 通知系（未確認）
- **`api/endpoints/report_artifacts.py`**: 生成済みアーティファクトの署名付きURL提供

### 0.3 レイヤー別の責務分析

#### **プレゼンテーション層（I/O 整形）**

**場所**: `api/endpoints/reports/*.py`

**現状の責務**:
- FastAPI のパス定義
- UploadFile の受け取り
- `ReportProcessingService.run(generator, files)` の呼び出し
- Response の返却（JSONResponse or StreamingResponse）

**問題点**:
- **責務は比較的明確**だが、Generator のインスタンス化をエンドポイント内で行っている
  ```python
  generator = FactoryReportGenerator("factory_report", files)
  if period_type:
      generator.period_type = period_type
  return report_service.run(generator, files)
  ```
- 本来は UseCase 層で Generator を組み立てるべき

**評価**: ⚠️ **良好だが改善の余地あり**

---

#### **アプリケーション層（UseCase っぽい場所）**

**場所**: `api/services/report/core/processors/report_processing_service.py`

**現状の責務**:
- CSV 読み込み（`read_csv_files`）
- Generator の `validate()` / `format()` / `main_process()` 呼び出し
- 期間フィルタ適用
- Excel/PDF 生成と保存
- 署名付き URL 生成

**問題点**:
1. **責務が過剰**: 「CSV I/O」「検証」「整形」「ドメインロジック呼び出し」「アーティファクト保存」「URL生成」をすべて担当
2. **UseCase としての抽象化が不足**: 具体的な Generator に強く依存
3. **Port/Adapter パターンの欠如**: pandas に直接依存し、I/O が抽象化されていない

**評価**: ❌ **要リファクタリング（最優先）**

---

#### **ドメイン層（ビジネスロジック）**

**場所**: `api/services/report/ledger/*.py` および `processors/*`

**例**: `services/report/ledger/factory_report.py`
```python
def process(dfs: Dict[str, Any]) -> pd.DataFrame:
    # 工場日報のメイン処理
    master_csv_shobun = process_shobun(df_shipment)
    master_csv_yuka = process_yuuka(df_yard, df_shipment)
    master_csv_yard = process_yard(df_yard, df_shipment)
    combined_df = pd.concat([...])
    return make_label(combined_df)
```

**問題点**:
1. **pandas DataFrame に強く依存**: ドメインオブジェクトが存在せず、生の DataFrame を操作
2. **不変条件の欠如**: DataFrame の構造や値の妥当性を保証する仕組みがない
3. **責務の混在**: 
   - ドメインロジック（集計・分類）
   - データ整形（セル番号生成、ラベル付与）
   - I/O（CSV/マスタ読み込み）

**評価**: ⚠️ **改善が必要（中優先度）**

---

#### **インフラ層（外部依存）**

**場所**: 
- `api/services/report/utils/io/*.py` (CSV/Excel 読み書き)
- `api/services/report/artifacts/artifact_service.py` (ファイルシステム保存)
- `api/config/loader/*.py` (YAML 設定読み込み)

**現状の責務**:
- CSV 読み込み: `utils/io/csv_loader.py`
- Excel テンプレート読み込み: `utils/io/template_loader.py`
- Excel 書き込み: `utils/io/excel_writer.py`
- アーティファクト保存: `artifacts/artifact_service.py`

**問題点**:
1. **抽象化の欠如**: これらの実装が `services/report/ledger` から直接呼ばれている（DIP 違反）
2. **Port インターフェースが存在しない**

**評価**: ⚠️ **Port/Adapter パターン導入が必要（中優先度）**

---

#### **設定まわりの役割**

**場所**:
- `app/settings.py`: 環境変数ベースの設定（STAGE, GCS, アーティファクトパス等）
- `app/api/config/settings/loader.py`: 旧 Streamlit 設定（**削除候補**）
- `app/api/config/loader/main_path.py`: パス設定の動的読み込み
- `app/api/services/report/utils/config/template_config.py`: テンプレート設定

**問題点**:
1. **設定が分散**: `app/settings.py` と `api/config/*` が混在
2. **st_app 依存の残骸**: `api/config/settings/loader.py` は Streamlit 専用（**削除対象**）

**評価**: ⚠️ **統合と整理が必要（低優先度）**

---

### 0.4 report_artifacts のパス・命名規則

**ディレクトリ構造**:
```
api/report_artifacts/
  reports/
    <report_key>/         # 例: factory_report, balance_sheet
      <report_date>/      # 例: 2025-11-17
        <timestamp>-<token>/
          <file_base>.xlsx
          <file_base>.pdf
```

**命名ルール**:
- `report_key`: 帳票種別（`factory_report`, `balance_sheet` など）
- `report_date`: ISO 形式の日付（`2025-11-17`）
- `timestamp`: `YYYYMMdd_HHmmss` 形式
- `token`: 8文字のランダムハッシュ（衝突回避）
- `file_base`: `<report_key>-<report_date>`

**責務**:
- `artifacts/artifact_service.py` が保存とURL生成を担当
- `artifacts/artifact_builder.py` が署名付きURLのレスポンス構築を担当

**評価**: ✅ **比較的良好** だが、インフラ層として明示的に切り出す余地あり

---

### 0.5 Streamlit 関連の残骸

**現状**:
1. `app/streamlit.py`: Streamlit のスタブ（FastAPI で streamlit import を回避するためのダミー）
2. `api/config/settings/loader.py`: Streamlit 用の設定ローダー（**削除対象**）
3. `docs/ST_APP_*.md`: st_app 削除のチェックリスト

**削除ロードマップ**:
- ✅ `st_app/` ディレクトリはすでに削除済み（docs に記録あり）
- ⚠️ `app/streamlit.py` は一部のコードが参照している可能性あり（要調査）
- ⚠️ `api/config/settings/loader.py` は未使用と思われる（**削除推奨**）

**評価**: ⚠️ **クリーンアップが必要（低優先度）**

---

## 1. Clean Architecture への距離

### 現在地
```
┌─────────────────────────────────────────┐
│ api/endpoints (Router)                   │ ← プレゼンテーション層（良好）
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│ services/report/core/processors          │ ← アプリケーション層（要改善）
│ (ReportProcessingService)                │    - 責務過剰
└────────────┬────────────────────────────┘    - UseCase としての抽象化不足
             │
┌────────────▼────────────────────────────┐
│ services/report/ledger/*.py              │ ← ドメイン層（要改善）
│ (process 関数、processors)               │    - DataFrame に強く依存
└────────────┬────────────────────────────┘    - Entity/ValueObject 不在
             │
┌────────────▼────────────────────────────┐
│ services/report/utils/io/*.py            │ ← インフラ層（Port/Adapter 不在）
│ artifacts/artifact_service.py            │    - 抽象化されていない
└──────────────────────────────────────────┘
```

### 目指す姿
```
┌─────────────────────────────────────────┐
│ api/routers (Router)                     │ ← プレゼンテーション層
└────────────┬────────────────────────────┘    - I/O 整形のみ
             │
┌────────────▼────────────────────────────┐
│ core/usecases/reports/*.py               │ ← アプリケーション層
│ (GenerateFactoryReportUseCase)           │    - Port に依存
└────────────┬────────────────────────────┘    - ドメインロジック orchestrate
             │
┌────────────▼────────────────────────────┐
│ core/domain/reports/*.py                 │ ← ドメイン層
│ (FactoryReport Entity, ValueObjects)     │    - 外部依存ゼロ
└──────────────────────────────────────────┘    - 不変条件を保証
             ▲
             │ DIP (依存性逆転)
             │
┌────────────┴────────────────────────────┐
│ core/ports/*.py                          │ ← Port (抽象)
│ (ReportRepository, CsvGateway, ...)      │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│ infra/adapters/*.py                      │ ← Adapter (実装)
│ (PandasCsvGateway, FileSystemRepo, ...)  │
└──────────────────────────────────────────┘
```

---

## 2. 既存ドキュメントとの整合性

### `docs/ARCHITECTURE_IMPROVEMENT_PROPOSAL.md`
- **内容**: CSV バリデーションの責務分離と Facade パターンの提案
- **整合性**: ✅ 本リファクタリングの方向性と一致
- **活用**: `csv_validator_facade.py` のパターンを UseCase 層にも適用可能

### `docs/LEDGER_MIGRATION_NOTES.md`
- **内容**: st_app から api への移行完了の記録
- **整合性**: ✅ 移行済み、本リファクタリングの前提条件
- **次ステップ**: st_app 残骸のクリーンアップ → Clean Architecture 適用

### `docs/ST_APP_DELETION_CHECKLIST.md`
- **内容**: st_app 削除前のチェックリスト
- **重要事項**: `api/config/loader/main_path.py` が st_app のパスをハードコード
- **対応必要**: 設定ファイルの移行（低優先度だが必須）

---

## 3. 依存関係の整理

### 上流 → 下流（正常な依存）
```
endpoints
  ↓
services/report/core/processors (ReportProcessingService)
  ↓
services/report/ledger/* (process 関数)
  ↓
services/report/utils/* (io, config, excel, ...)
```

### 逆依存・循環依存
- **なし** （良好）

### 外部依存
- `pandas`: ドメイン層・アプリケーション層に直接依存（要改善）
- `openpyxl`: インフラ層で適切に隔離されている（良好）
- `backend_shared`: 共有ユーティリティ（問題なし）

---

## 4. テスト状況

### 既存テスト
- `test/test_api_readiness.py`: API のインポート可能性テスト
- `test/test_services_entrypoints.py`: サービス関数のエントリポイントテスト
- `test/verify_st_app_migration.py`: st_app 依存関係の分析スクリプト

### テストカバレッジ
- ⚠️ **UseCase 層のテストが不在**
- ⚠️ **ドメインロジックの単体テストが不在**
- ✅ 統合テスト（API エンドポイント）は一部存在

---

## 5. リファクタリングの優先順位

### 最重要（HIGH）
1. **ReportProcessingService の責務分離**
   - UseCase 層の抽出
   - Port/Adapter パターンの導入

### 重要（MEDIUM）
2. **ドメイン層の Entity/ValueObject 化**
   - DataFrame 依存の緩和
   - 不変条件の明示化

3. **Port/Adapter の実装**
   - CSV Gateway の抽象化
   - Repository パターンの導入

### 低優先（LOW）
4. **設定まわりの統合**
   - st_app 残骸のクリーンアップ
   - 設定ファイルの一元化

5. **テストの拡充**
   - UseCase 単体テスト
   - ドメインロジック単体テスト

---

## 6. リスク評価

### 既存 API との後方互換性
- ✅ **リスク低**: エンドポイントの URL/Request/Response は変更しない方針
- ⚠️ **注意**: 内部実装の大幅な変更による副作用の可能性

### 既存コードとの共存
- ✅ **段階的移行可能**: 1 エンドポイントずつリファクタリング可能
- ✅ **テストで担保**: 各ステップで既存テストを実行

### core_api への影響
- ✅ **影響なし**: ledger_api の内部実装のみを変更
- ⚠️ **注意**: パフォーマンス変化の可能性（要モニタリング）

---

## 7. 次ステップ

このレポートを踏まえ、次の「1. リファクタリングロードマップの作成」に進みます。

