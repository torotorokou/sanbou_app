# ledger_api リファクタリング計画

## 目的
帳簿作成機能の構造をシンプルに整理し直し、見通しの良い構造にする。
**既存の機能・挙動・API仕様は壊さない**。

## 現状分析

### 問題点

#### 1. 重複するベースクラス
| ファイル | クラス | 用途 |
|----------|--------|------|
| `core/usecases/reports/base_report_usecase.py` | `BaseReportUseCase` | ✅ 現行版（Clean Architecture） |
| `core/usecases/reports/base_generators/base_report_generator.py` | `BaseReportGenerator` | ⚠️ 旧版（使用中だが非推奨） |
| `core/usecases/reports/concrete_generators.py` | 各Generatorクラス | ⚠️ 旧版（base_generatorsを使用） |

#### 2. ファイル名の重複（同名ファイルが異なるディレクトリに存在）
| ファイル | 内容 |
|----------|------|
| `core/usecases/reports/balance_sheet.py` | `process()` 関数（処理ロジック） |
| `core/domain/reports/balance_sheet.py` | `BalanceSheet` クラス（ドメインモデル） |

同様の重複:
- `factory_report.py`
- `average_sheet.py`
- `management_sheet.py`

#### 3. 責務の配置の問題
- `core/usecases/reports/*.py` の `process()` 関数はビジネスロジックを含むため、本来 `domain` にあるべき

### 現在のアーキテクチャ（理想）

```
api/routers/reports/
  └── balance_sheet.py    # エンドポイント（薄い）
      └── calls GenerateBalanceSheetUseCase.execute()

core/usecases/reports/
  └── generate_balance_sheet.py  # UseCase（オーケストレーション）
      ├── extends BaseReportUseCase
      ├── create_domain_model() → BalanceSheet
      ├── execute_domain_logic() → balance_sheet.process()
      └── generate_excel()

core/domain/reports/
  ├── balance_sheet.py    # ドメインモデル（エンティティ）
  └── processors/         # ドメインロジック（計算処理）
      └── balance_sheet/
```

---

## リファクタリング方針

### フェーズ1: 命名の明確化（低リスク）
1. `core/usecases/reports/balance_sheet.py` を `balance_sheet_processor.py` にリネーム
2. 同様に他のファイルも `*_processor.py` にリネーム
3. インポートパスを更新

### フェーズ2: 旧版クラスの廃止（中リスク）
1. `concrete_generators.py` の使用箇所を確認
2. 未使用であれば削除、使用中であれば `generate_*.py` に移行
3. `base_generators/` ディレクトリを精査

### フェーズ3: ディレクトリ構造の整理（オプション）
- 現状維持でも問題ないが、将来的には:
  - `core/usecases/reports/processors/` → `core/domain/reports/processors/` に統合

---

## ベビーステップ実行計画

### Step 1: 使用状況の確認 ✅ 完了
- [x] `concrete_generators.py` の呼び出し元を特定
- [x] `base_generators/` の使用状況を確認
- [x] 各 `process()` 関数の呼び出し元を確認

### Step 2: 命名の明確化 ✅ 完了
- [x] `balance_sheet.py` → `balance_sheet_processor.py` リネーム
- [x] `factory_report.py` → `factory_report_processor.py` リネーム
- [x] `average_sheet.py` → `average_sheet_processor.py` リネーム
- [x] `management_sheet.py` → `management_sheet_processor.py` リネーム
- [x] インポートパスを全て更新
- [x] インポート確認で動作確認

### Step 3: __init__.py の整理 ✅ 完了
- [x] ドキュメントを充実
- [x] UseCases を先頭に、process関数を後ろに整理
- [x] `__all__` 定義を追加

### Step 4: テストファイルの更新 ✅ 完了
- [x] `test_api_readiness.py` のインポートパスを現在の構造に更新
- [x] UseCaseクラスのテストを追加
- [x] 旧版Generatorクラスのテストを (legacy) マークで保持

### Step 5: 使用状況の精査結果 ✅ 完了

| クラス/ファイル | 本番コード | テストコード | 状態 |
|----------------|----------|-------------|------|
| `GenerateFactoryReportUseCase` | ✅ | ✅ | **推奨** |
| `GenerateBalanceSheetUseCase` | ✅ | ✅ | **推奨** |
| `GenerateAverageSheetUseCase` | ✅ | ✅ | **推奨** |
| `GenerateManagementSheetUseCase` | ✅ | ✅ | **推奨** |
| `FactoryReportGenerator` (旧版) | ❌ | ✅ | 互換性維持 |
| `BalanceSheetGenerator` (旧版) | ❌ | ✅ | 互換性維持 |
| `AverageSheetGenerator` (旧版) | ❌ | ✅ | 互換性維持 |
| `ManagementSheetGenerator` (旧版) | ❌ | ✅ | 互換性維持 |
| `BlockUnitPriceGenerator` (旧版) | ❌ | ❌ | 削除候補 |
| `BaseReportGenerator` | ✅（親クラス） | ✅ | 保持 |
| `InteractiveReportProcessingService` | ✅ | ✅ | 保持 |
| `balance_sheet_base.py` | ✅ | ✅ | 保持 |
| `factory_report_base.py` | ✅ | ❌ | 保持 |

### 次のステップ（オプション）
- [ ] `BlockUnitPriceGenerator` クラスの削除（未使用）
- [ ] 将来的に旧版Generatorを完全廃止する際のマイグレーション計画

---

## ファイル一覧（現状）

### core/usecases/reports/
```
__init__.py
average_sheet.py           # process() - 単価平均表
balance_sheet.py           # process() - 搬出入収支表
balance_sheet_base.py      # build_balance_sheet_base_data()
base_generators/           # 旧版ベースクラス
  ├── __init__.py
  ├── base_report_generator.py
  └── base_interactive_report_generator.py
base_report_usecase.py     # ✅ 現行ベースクラス
concrete_generators.py     # 旧版Generatorクラス群
factory_report.py          # process() - 工場日報
factory_report_base.py     # FactoryReportBase
generate_average_sheet.py  # ✅ UseCase
generate_balance_sheet.py  # ✅ UseCase
generate_block_unit_price.py # ✅ UseCase
generate_factory_report.py # ✅ UseCase
generate_management_sheet.py # ✅ UseCase
interactive/               # インタラクティブ帳簿用
management_sheet.py        # process() - 経営表
processors/                # サブプロセッサ
```

### core/domain/reports/
```
__init__.py
average_sheet.py           # AverageSheet ドメインモデル
balance_sheet.py           # BalanceSheet ドメインモデル
block_unit_price.py        # BlockUnitPrice ドメインモデル
factory_report.py          # FactoryReport ドメインモデル
management_sheet.py        # ManagementSheet ドメインモデル
processors/                # ドメインロジック（計算処理）
report_utils.py            # 共通ユーティリティ
transport_discount.py      # 運搬費値引きロジック
```

---

## 注意事項
- 変更後は必ずテストを実行
- APIレスポンス形式は変更しない
- パフォーマンスに影響する変更は避ける
