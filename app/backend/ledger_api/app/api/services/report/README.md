# Report Service Module

レポート生成サービスのコアモジュールです。

## ディレクトリ構成

```
report/
├── core/                             # コアコンポーネント
│   ├── base_generators/              # 基底ジェネレータークラス
│   │   ├── __init__.py
│   │   ├── base_report_generator.py           # 通常レポート基底クラス
│   │   └── base_interactive_report_generator.py # インタラクティブレポート基底クラス
│   ├── processors/                   # 処理サービス
│   │   ├── __init__.py
│   │   ├── report_processing_service.py       # 通常レポート処理
│   │   └── interactive_report_processing_service.py # インタラクティブレポート処理
│   ├── concrete_generators.py        # 具体的なレポートジェネレーター
│   └── __init__.py
├── artifacts/                        # アーティファクト管理
│   ├── __init__.py
│   ├── artifact_service.py           # ストレージ・署名URL管理
│   └── artifact_builder.py           # レスポンス構築
├── session/                          # セッション管理
│   ├── __init__.py
│   └── session_store.py              # セッションストア(Redis/メモリ)
├── ledger/                           # 帳簿レポート実装
│   ├── average_sheet.py              # 平均表
│   ├── balance_sheet.py              # 残高表
│   ├── factory_report.py             # 工場レポート
│   ├── management_sheet.py           # 管理表
│   ├── interactive/                  # インタラクティブレポート
│   ├── processors/                   # プロセッサー
│   └── utils/                        # ユーティリティ
├── __init__.py
└── README.md                         # このファイル
```

## モジュール説明

### Core (コア)

レポート生成の基盤となるコンポーネント群です。

#### Base Generators (基底ジェネレーター)

**`base_report_generator.py`**
- すべてのレポート生成クラスの基底クラス
- CSV の検証、フォーマット、Excel/PDF生成の共通処理を提供
- 主要メソッド:
  - `validate()`: CSVバリデーション
  - `format()`: CSVフォーマット変換
  - `main_process()`: メイン処理（サブクラスで実装）
  - `generate_excel_bytes()`: Excel生成

**`base_interactive_report_generator.py`**
- インタラクティブレポート用の基底クラス
- ステップ分割型の処理フロー（initial → apply → finalize）
- セッション状態の管理機能を提供

#### Processors (処理サービス)

**`report_processing_service.py`**
- 通常レポートの処理オーケストレーション
- CSV読込 → 検証 → フォーマット → 処理 → ファイル保存 → URL返却
- エンドポイントから利用される主要サービス

**`interactive_report_processing_service.py`**
- インタラクティブレポートの処理オーケストレーション
- 段階的な処理フロー（initial / apply / finalize）
- セッション管理との統合

#### Concrete Generators (具体的実装)

**`concrete_generators.py`**
- 具体的なレポートジェネレータークラスの実装
- クラス:
  - `FactoryReportGenerator`: 工場レポート
  - `BalanceSheetGenerator`: 残高表
  - `AverageSheetGenerator`: 平均表
  - `ManagementSheetGenerator`: 管理表
  - `BlockUnitPriceGenerator`: ブロック単価（インタラクティブ）

### Artifacts (アーティファクト管理)

レポートファイル（Excel/PDF）の保存と配信を管理します。

**`artifact_service.py`**
- ファイルストレージの管理
- 署名付きURLの生成・検証
- トークンベースのセキュリティ

**`artifact_builder.py`**
- レスポンスペイロードの構築
- Excel/PDF生成とファイル保存の統合
- エラーハンドリング

### Session (セッション管理)

インタラクティブレポートのセッション状態を管理します。

**`session_store.py`**
- セッションデータの永続化
- Redis対応（環境変数 `REDIS_URL` で設定）
- メモリフォールバック
- TTL管理

### Ledger (帳簿レポート実装)

各種帳簿レポートの具体的な処理ロジックを実装しています。
詳細は `ledger/README.md` を参照してください。

## 使用方法

### 基本的な使用例

```python
from app.api.services.report import (
    ReportProcessingService,
    BalanceSheetGenerator,
)

# サービスとジェネレーターのインスタンス化
service = ReportProcessingService()
generator = BalanceSheetGenerator(report_key="balance_sheet", files=files)

# レポート処理の実行
result = await service.process_report(
    files=files,
    start_date=start_date,
    end_date=end_date,
    generator=generator,
)
```

### インタラクティブレポート

```python
from app.api.services.report import (
    InteractiveReportProcessingService,
)
from app.api.services.report.ledger.interactive import (
    BlockUnitPriceInteractive,
)

# サービスとジェネレーターのインスタンス化
service = InteractiveReportProcessingService()
generator = BlockUnitPriceInteractive(report_key="block_unit_price", files=files)

# 初期ステップ
initial_result = await service.initial(generator, df_formatted)

# 中間ステップ（複数回可能）
apply_result = await service.apply(generator, session_data, user_input)

# 最終ステップ
final_result = await service.finalize(generator, session_data)
```

## インポート方法

### 推奨される方法

```python
# メインパッケージから直接インポート
from app.api.services.report import (
    ReportProcessingService,
    InteractiveReportProcessingService,
    BaseReportGenerator,
    BaseInteractiveReportGenerator,
    BalanceSheetGenerator,
    AverageSheetGenerator,
    # ... その他
)
```

### サブモジュールから直接インポート

```python
# コアコンポーネント
from app.api.services.report.core import (
    BaseReportGenerator,
    ReportProcessingService,
)

# アーティファクト管理
from app.api.services.report.artifacts import (
    get_report_artifact_storage,
    ArtifactResponseBuilder,
)

# セッション管理
from app.api.services.report.session import session_store
```

## 設計原則

### 1. 関心の分離 (Separation of Concerns)

各モジュールは明確な単一の責任を持ちます：
- **Core**: レポート生成ロジック
- **Artifacts**: ファイル保存と配信
- **Session**: 状態管理
- **Ledger**: 帳簿固有の処理

### 2. 依存性の注入 (Dependency Injection)

- ジェネレーターは処理サービスに注入される
- テスタビリティとモック化が容易
- 疎結合な設計

### 3. 抽象化とポリモーフィズム

- 基底クラスで共通インターフェースを定義
- サブクラスで具体的な処理を実装
- 新しいレポートタイプの追加が容易

### 4. ステートレス設計

- セッション状態は明示的に管理
- サービスクラスは状態を持たない
- スケーラビリティの確保

## 拡張ガイド

### 新しいレポートタイプの追加

1. `core/concrete_generators.py` に新しいジェネレータークラスを追加
2. `ledger/` に処理ロジックを実装
3. `__init__.py` でエクスポート
4. エンドポイントで使用

```python
# concrete_generators.py
class NewReportGenerator(BaseReportGenerator):
    def main_process(self, df_formatted: Dict[str, Any]) -> pd.DataFrame:
        return process_new_report(df_formatted)
```

### インタラクティブレポートの追加

1. `BaseInteractiveReportGenerator` を継承
2. `initial_step`, `apply_step`, `finalize_step` を実装
3. `ledger/interactive/` に配置

## テスト

```bash
# ユニットテスト
pytest test/test_services_entrypoints.py

# 統合テスト
pytest test/test_api_readiness.py
```

## トラブルシューティング

### インポートエラー

新しい構造に従ってインポートパスを確認してください：

```python
# ❌ 古い（削除されたファイル）
from app.api.services.report.report_processing_service import ReportProcessingService

# ✅ 新しい
from app.api.services.report import ReportProcessingService
```

### セッションエラー

Redis接続エラーの場合、環境変数 `REDIS_URL` が正しく設定されているか確認してください。
Redisが利用できない場合、自動的にメモリフォールバックが使用されます。

## 参考資料

- [サービス全体のREADME](../README.md)
- [帳簿レポートREADME](ledger/README.md)
- [リファクタリング詳細](../../../docs/REFACTORING_SERVICES.md)
