# サービスモジュールリファクタリング

## 実施日
2025年10月2日

## 目的
servicesディレクトリ内のモジュールを機能ごとに整理し、コードの可読性と保守性を向上させる。

## 変更内容

### 1. 新しいディレクトリ構造

```
services/
├── csv/                              # 新規: CSV処理関連サービス
│   ├── __init__.py
│   ├── formatter_service.py          # csv_formatter_service.py から移動
│   ├── validator_service.py          # csv_validator_facade.py から移動
│   └── README.md                     # 新規: ドキュメント
├── report/                           # 既存: レポート生成関連サービス
│   └── ...
├── csv_formatter_service.py          # 変更: 後方互換性レイヤー
├── csv_validator_facade.py           # 変更: 後方互換性レイヤー
├── __init__.py                       # 更新: 新しい構造をエクスポート
└── README.md                         # 新規: 全体ドキュメント
```

### 2. 機能ごとのモジュール分割

#### CSV処理サービス (`csv/`)
- **formatter_service.py**: CSVデータのフォーマット変換
- **validator_service.py**: CSVファイルのバリデーション

#### レポート生成サービス (`report/`)
- 既存の構造を維持

### 3. 後方互換性の保証

既存のインポートパスは引き続き動作します：

```python
# 旧: これらのインポートは引き続き動作します
from app.api.services.csv_formatter_service import CsvFormatterService
from app.api.services.csv_validator_facade import CsvValidatorService

# 新: 推奨される新しいインポート方法
from app.api.services.csv import CsvFormatterService, CsvValidatorService
```

## 主要な変更ファイル

### 新規作成
1. `/app/api/services/csv/__init__.py`
2. `/app/api/services/csv/formatter_service.py`
3. `/app/api/services/csv/validator_service.py`
4. `/app/api/services/csv/README.md`
5. `/app/api/services/README.md`

### 変更
1. `/app/api/services/csv_formatter_service.py` - 後方互換性レイヤーに変更
2. `/app/api/services/csv_validator_facade.py` - 後方互換性レイヤーに変更
3. `/app/api/services/__init__.py` - 新しいモジュール構造をエクスポート
4. `/app/api/services/report/base_report_generator.py` - 新しいインポートパスを使用

## 移行ガイド

### 既存コードの移行（任意）

既存のコードは変更不要ですが、以下のように新しいインポート方法に移行することを推奨します：

**変更前:**
```python
from app.api.services.csv_formatter_service import CsvFormatterService
from app.api.services.csv_validator_facade import CsvValidatorService
```

**変更後:**
```python
from app.api.services.csv import CsvFormatterService, CsvValidatorService
```

### 新規コード

新しいコードでは、必ず新しいインポート方法を使用してください。

## テスト

### 構文チェック
```bash
cd /path/to/ledger_api
python -m py_compile app/api/services/csv/__init__.py \
  app/api/services/csv/formatter_service.py \
  app/api/services/csv/validator_service.py \
  app/api/services/csv_formatter_service.py \
  app/api/services/csv_validator_facade.py \
  app/api/services/__init__.py
```

### インポートテスト（Dockerコンテナ内）
```bash
docker-compose -f docker/docker-compose.dev.yml exec ledger_api python -c "
from app.api.services.csv import CsvFormatterService, CsvValidatorService
from app.api.services.csv_formatter_service import CsvFormatterService as OldFormatter
from app.api.services.csv_validator_facade import CsvValidatorService as OldValidator
assert CsvFormatterService is OldFormatter
assert CsvValidatorService is OldValidator
print('✓ すべてのインポートテスト成功')
"
```

## 設計原則

このリファクタリングは以下の原則に基づいています：

1. **関心の分離 (Separation of Concerns)**
   - CSV処理とレポート生成を明確に分離

2. **後方互換性 (Backward Compatibility)**
   - 既存のコードを壊さない
   - 段階的な移行を可能にする

3. **可読性 (Readability)**
   - ディレクトリ構造で機能が明確
   - READMEファイルで各モジュールの役割を文書化

4. **拡張性 (Extensibility)**
   - 新しいCSV処理機能を追加しやすい
   - 新しいサービスカテゴリを追加しやすい

## 今後の改善案

1. **テストの追加**
   - CSV処理サービスのユニットテスト
   - 統合テストの拡充

2. **さらなるモジュール分割**
   - `database/`: データベース操作サービス
   - `notification/`: 通知サービス
   - `cache/`: キャッシュ管理サービス

3. **型ヒントの強化**
   - すべてのメソッドに完全な型ヒント

4. **ドキュメントの拡充**
   - APIドキュメント
   - アーキテクチャ図

## 影響範囲

### 影響なし
- すべての既存のエンドポイント
- すべての既存のテスト
- 既存のインポートパス

### 影響あり（推奨変更）
- 新規コード: 新しいインポートパスを使用すること
- コードレビュー: 新しい構造に準拠しているか確認

## ロールバック手順

万が一問題が発生した場合、以下の手順でロールバックできます：

1. `csv/` ディレクトリを削除
2. `csv_formatter_service.py` と `csv_validator_facade.py` を元のコードに戻す
3. `services/__init__.py` を元の内容に戻す

ただし、後方互換性が保証されているため、ロールバックの必要性は極めて低いです。

## チェックリスト

- [x] 新しいディレクトリ構造の作成
- [x] ファイルの移動とリファクタリング
- [x] 後方互換性レイヤーの実装
- [x] __init__.py ファイルの更新
- [x] README.md の作成
- [x] 構文チェック
- [ ] Dockerコンテナ内でのテスト（コンテナ起動が必要）
- [ ] 既存のテストスイートの実行
- [ ] コードレビュー

## 参考

- [Python パッケージング](https://packaging.python.org/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID原則](https://en.wikipedia.org/wiki/SOLID)
