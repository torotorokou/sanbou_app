# Step 1: 現状調査レポート

**日付**: 2025-11-14  
**ステータス**: ✅ 完了

---

## 📊 現状のテーブル構造とYAML定義の比較

### カラム数の比較

| テーブル | YAML定義 | raw層 | stg層 | 差分 |
|---------|----------|-------|-------|------|
| **receive_shogun_flash** | 37カラム | 37カラム | 37カラム | ✅ 一致 |
| **shipment_shogun_flash** | 18カラム | 18カラム | 18カラム | ✅ 一致 |
| **yard_shogun_flash** | 15カラム | 15カラム | 17カラム | ⚠️ stg層に+2カラム |

### yard_shogun_flashの追加カラム確認

stg層のyardテーブルには `id` と `created_at` が追加されています（自動生成カラム）。

---

## 🔍 冗長な接尾辞 `_en_` の使用状況

### 問題のあるカラム名

以下のカラムで `_en_` という冗長な接尾辞が使用されています：

#### shipment
- `client_en_name` → `client_name` にすべき
- `vendor_en_name` → `vendor_name` にすべき
- `site_en_name` → `site_name` にすべき
- `item_en_name` → `item_name` にすべき
- `unit_en_name` → `unit_name` にすべき
- `transport_vendor_en_name` → `transport_vendor_name` にすべき
- `slip_type_en_name` → `slip_type_name` にすべき

#### yard
- `client_en_name` → `client_name` にすべき
- `item_en_name` → `item_name` にすべき
- `unit_en_name` → `unit_name` にすべき
- `sales_staff_en_name` → `sales_staff_name` にすべき
- `vendor_en_name` → `vendor_name` にすべき
- `category_en_name` → `category_name` にすべき

### なぜ `_en_` が冗長なのか

1. **命名規則の不統一**: receiveでは `vendor_name`, `item_name` なのに、shipment/yardでは `vendor_en_name`, `item_en_name`
2. **`en`の意味が不明**: 英語（English）を意味するのか、それとも別の略語なのか不明瞭
3. **不要な冗長性**: 日本語カラム名から英語カラム名への変換で、すでに意味が伝わっているため`_en_`は不要

---

## 📋 修正が必要な項目

### 1. YAML定義の修正
- `_en_` 接尾辞を持つすべてのカラム名を修正
- receive, shipment, yard の3つのセクションで一貫性のある命名に統一

### 2. 既存テーブルのカラム名変更
- stg層とraw層の両方で該当カラム名をリネーム
- マイグレーションファイルで安全に実行

### 3. 不要なカラムの削除
- 現状では、YAML定義とテーブル構造がほぼ一致しているため、大きな削減は不要
- `id` と `created_at` は stg層で必要（主キー・監査用）、raw層では不要

---

## 🎯 次のステップ

### Step 2: YAML設定ファイルの修正
- `_en_` 接尾辞を削除
- 命名規則を統一

### Step 3: マイグレーション作成
- カラム名変更のマイグレーション
- raw層から `id`, `created_at` を削除（shipment/yardのみ）

### Step 4: コード修正
- バックエンドのORM/クエリで使用している古いカラム名を更新
- フロントエンドの型定義を更新

### Step 5: テスト
- CSV アップロード機能の動作確認
- データ整合性の確認

---

## ⚠️ 注意事項

### 破壊的変更
カラム名の変更は**破壊的変更**であり、以下の影響があります：
- 既存のクエリが動作しなくなる可能性
- アプリケーションコードの修正が必要
- 既存データの移行は不要（カラム名だけの変更）

### 推奨アプローチ
1. 開発環境で十分にテスト
2. マイグレーションの前後でバックアップ取得
3. 段階的に実施（まずYAML → 次にDB → 最後にコード）
