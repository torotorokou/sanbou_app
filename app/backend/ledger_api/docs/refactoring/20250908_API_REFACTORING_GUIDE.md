# backend/docs/API_REFACTORING_GUIDE.md

# 帳票API リファクタリングガイド

## 新しい API エンドポイント構造

### 1. 帳票別専用エンドポイント

各帳票に専用のエンドポイントが用意されました：

#### 工場日報

```
POST /ledger_api/reports/factory_report/
```

#### 工場搬出入収支表

```
POST /ledger_api/reports/balance_sheet/
```

#### ブロック単価計算レポート

```
POST /ledger_api/reports/block_unit_price/
```

### 2. リクエスト例

```bash
# 工場日報生成
curl -X POST "http://localhost:8001/ledger_api/reports/factory_report/" \
  -H "Content-Type: multipart/form-data" \
  -F "shipment=@shipment.csv" \
  -F "yard=@yard.csv"

# 収支表生成
curl -X POST "http://localhost:8001/ledger_api/reports/balance_sheet/" \
  -H "Content-Type: multipart/form-data" \
  -F "shipment=@shipment.csv" \
  -F "yard=@yard.csv" \
  -F "receive=@receive.csv"
```

### 3. レガシーAPI（互換性のため残存）

```
POST /ledger_api/report/manage
```

⚠️ このエンドポイントは旧バージョンとの互換性のために残されていますが、新しい専用エンドポイントの使用を推奨します。

## アーキテクチャ変更点

### Before (単一エンドポイント)

```
POST /report/manage + report_key parameter
└── 全ての帳票処理が一つのエンドポイントに集約
```

### After (帳票別エンドポイント)

```
POST /reports/factory_report/      → 工場日報専用
POST /reports/balance_sheet/       → 収支表専用
POST /reports/block_unit_price/    → ブロック単価専用
```

### 共通化されたコンポーネント

1. **ReportProcessingService** - 共通処理の管理

   - ファイル取得・バリデーション・フォーマット変換
   - Excel・PDF・ZIP生成

2. **BaseReportGenerator** - 帳票生成基底クラス

   - 各帳票固有の `main_process()` 実装

3. **個別Generator** - 帳票別実装クラス
   - FactoryReportGenerator
   - BalanceSheetGenerator
   - BlockUnitPriceGenerator

## 利点

1. **可読性向上**: 各帳票の責務が明確化
2. **保守性向上**: 帳票固有のロジックが分離
3. **拡張性向上**: 新しい帳票追加が容易
4. **テスト性向上**: 帳票別にユニットテストが可能
5. **API設計改善**: RESTful な URL 設計

## マイグレーション方法

1. 既存コードは `/report/manage` エンドポイントで継続動作
2. 新規実装では `/reports/{report_type}/` エンドポイントを使用
3. 段階的に旧エンドポイントから移行
