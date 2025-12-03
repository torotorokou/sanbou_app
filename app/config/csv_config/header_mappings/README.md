# Header Mappings

## 📁 概要

このディレクトリには、マスターデータCSVのヘッダーマッピング定義が格納されています。

## 📄 ファイル一覧

### `master.yaml`

**目的**: マスターCSV（取引先一覧、業者一覧、品名一覧）の日本語カラム名→英語カラム名のマッピング定義

**内容**:
```yaml
取引先一覧:
    columns:
        取引先CD: client_cd
        取引先名1: client_name1
        # ...

業者一覧:
    columns:
        業者CD: vendor_cd
        業者略称名: vendor_abbr_name
        # ...

品名一覧:
    columns:
        品名CD: item_cd
        品名: item_name
        # ...
```

## ⚠️ 現在の使用状況

**状態**: ❌ **現在使用されていません**

**調査日**: 2025年12月3日

**調査結果**:
- Pythonコード内での参照が見つかりませんでした
- `grep`検索で使用箇所が検出されませんでした
- インポート文も見つかりませんでした

**推測される経緯**:
- 過去のリファクタリングで使用されなくなった可能性
- 計画されていた機能が実装されなかった可能性
- 別の方法（`shogun_csv_masters.yaml`など）で代替されている可能性

## 🔄 今後の対応

以下のいずれかの対応を推奨します:

### オプション1: 削除（推奨）
未使用であることが確認されたため、削除する。

**手順**:
```bash
rm -rf app/config/csv_config/header_mappings/
```

### オプション2: アーカイブ
将来的に参照する可能性があるため、アーカイブディレクトリに移動する。

**手順**:
```bash
mkdir -p app/config/archive/
mv app/config/csv_config/header_mappings app/config/archive/header_mappings_YYYYMMDD
```

### オプション3: 保持
将来的に実装する機能で使用する予定がある場合は、そのまま保持する。

**その場合の対応**:
- 使用予定の機能をこのREADMEに記載する
- チケット/イシュー番号を記載する

## 📚 関連ファイル

### 現在使用されているマスター定義

- `app/config/csv_config/shogun_csv_masters.yaml`
  - 現在、CSVのカラム定義・マッピングに使用されている
  - `ShogunCsvConfigLoader`で読み込まれている
  - すべてのサービス（core_api, backend_shared, ledger_api）で使用

### 類似の役割を持つファイル

現在は`shogun_csv_masters.yaml`が以下の役割を担っています:
- CSV種別ごとのカラム定義
- 日本語名→英語名のマッピング
- データ型定義
- 一意キー定義

## 🔗 参考資料

- [設定ファイル統一化調査レポート](../../../../docs/refactoring/20251203_CONFIG_CONSOLIDATION_AUDIT.md)
- `backend_shared/config/config_loader.py` - `ShogunCsvConfigLoader`

---

**最終更新**: 2025年12月3日  
**調査者**: GitHub Copilot
