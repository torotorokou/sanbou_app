# データセット設定 config レジストリへの集約 - 変更サマリ

## 実施日
2025-11-10

## 目的
データセットに関する定義（必須CSV、表示名、色、順序、必須ヘッダ、ファイル名ヒント、プレビュー設定、アップロード先など）を単一の config レジストリに集約し、保守性と拡張性を向上させる。

---

## 📁 新規追加ファイル

### 1. `src/features/database/config/types.ts`
- **説明**: DatasetConfig / CsvConfig 型定義
- **内容**: 
  - `DatasetKey`: データセット識別子 ('shogun_flash' | 'shogun_final' | 'manifest')
  - `CsvTypeKey`: CSV種別識別子（8種類）
  - `CsvConfig`: CSV個別設定（ラベル、色、順序、必須ヘッダ、ファイル名ヒント等）
  - `DatasetConfig`: データセット全体設定（CSV配列、アップロード先、注意事項等）

### 2. `src/features/database/config/datasets.ts`
- **説明**: データセット実体定義（shogun_flash / shogun_final / manifest）
- **内容**: 
  - 既存の分散定義を統合したDATASETSレジストリ
  - 各データセットのCSV種別、色、順序、必須ヘッダ、ファイル名ヒント、アップロード先を定義
  - `as const` + `Readonly` で書き換え不可

### 3. `src/features/database/config/selectors.ts`
- **説明**: UI/VMが使用する取得API
- **内容**:
  - `getDatasetConfig()`: データセット設定取得
  - `getCsvListSorted()`: CSV定義をorder順に取得
  - `findCsv()`: 特定CSV種別の設定取得
  - `guessCsvTypeByFilename()`: ファイル名からCSV種別推定
  - `getUploadEndpoint()`: アップロード先取得
  - `collectTypesForDataset()`: 旧互換実装
  - その他セレクタ関数

### 4. `src/features/database/config/index.ts`
- **説明**: barrel export
- **内容**: config レジストリの全公開APIをエクスポート

---

## 🔄 更新ファイル

### 1. `src/features/database/shared/dataset/dataset.ts`
- **変更**: config レジストリへのリダイレクト実装
- **詳細**:
  - `collectTypesForDataset()` → `getCsvTypeKeys()` を呼び出し
  - `requiredTypesForDataset()` → `getRequiredCsvTypes()` を呼び出し
  - `DATASETS` → `getAllDatasets()` から生成
  - `@deprecated` コメント追加

### 2. `src/features/database/dataset-import/model/constants.ts`
- **変更**: config から動的生成するように変更
- **詳細**:
  - `UPLOAD_CSV_DEFINITIONS` → DATASETS から動的生成
  - `UPLOAD_CSV_TYPES` → 動的生成された定義のキー配列
  - `@deprecated` コメント追加

### 3. `src/features/database/dataset-import/model/types.ts`
- **変更**: `DatasetImportVMOptions` に `datasetKey` プロパティ追加
- **詳細**: VM側でdatasetKeyを受け取り、configからCSV設定を取得できるように

### 4. `src/features/database/dataset-import/hooks/useDatasetImportVM.ts`
- **変更**: config セレクタを使用するように変更
- **詳細**:
  - `UPLOAD_CSV_DEFINITIONS` → `findCsv()` + `getCsvLabel()`
  - datasetKeyを受け取り、CSV設定をconfigから動的取得
  - 必須ヘッダの取得をconfigベースに変更

### 5. `src/features/database/shared/ui/colors.ts`
- **変更**: config から色定義を動的生成
- **詳細**:
  - `CSV_TYPE_COLORS` → DATASETS から動的生成
  - `@deprecated` コメント追加

### 6. `src/features/database/dataset-validate/model/rules.ts`
- **変更**: config から DatasetRule を動的生成
- **詳細**:
  - `DATASET_RULES` → DATASETS から動的生成
  - 必須ヘッダ、ファイル名ヒント、注意事項をconfigから取得
  - `@deprecated` コメント追加

### 7. `src/features/database/dataset-preview/model/types.ts`
- **変更**: `DatasetKey` を config から import
- **詳細**: 型定義の重複を排除し、configを唯一の真実の源に

### 8. `src/features/database/dataset-preview/hooks/useDatasetPreviewVM.ts`
- **変更**: config セレクタを使用するように変更
- **詳細**:
  - `TYPE_ORDER` / `TYPE_LABELS` → `getCsvListSorted()` でorder順に取得
  - `CSV_TYPE_COLORS` → `findCsv()` でcolor取得
  - ラベル、色、順序をすべてconfigから取得

### 9. `src/pages/database/DatasetImportPage.tsx`
- **変更**: `useDatasetImportVM()` に `datasetKey` を渡すように変更
- **詳細**: VM側でconfigを参照できるようにdatasetKeyを渡す

### 10. `src/features/database/index.ts`
- **変更**: config レジストリをエクスポート
- **詳細**:
  - `export * from './config'` 追加
  - shared の個別エクスポートで重複回避
  - 旧定義に `@deprecated` 追加

---

## 📊 Before → After 対応表

| 参照元 | Before | After |
|--------|--------|-------|
| CSV種別リスト取得 | `UPLOAD_CSV_TYPES` | `getCsvTypeKeys(datasetKey)` |
| CSV種別ラベル取得 | `UPLOAD_CSV_DEFINITIONS[type].label` | `getCsvLabel(datasetKey, typeKey)` |
| CSV種別色取得 | `CSV_TYPE_COLORS[type]` | `getCsvColor(datasetKey, typeKey)` |
| CSV必須判定 | `UPLOAD_CSV_DEFINITIONS[type].required` | `findCsv(datasetKey, typeKey)?.required` |
| 必須ヘッダ取得 | `UPLOAD_CSV_DEFINITIONS[type].requiredHeaders` | `findCsv(datasetKey, typeKey)?.validate.requiredHeaders` |
| ファイル名推定 | 個別実装 | `guessCsvTypeByFilename(datasetKey, fileName)` |
| アップロード先 | ハードコード `/core_api/database/upload/syogun_csv` | `getUploadEndpoint(datasetKey).path` |
| データセット種別取得 | `collectTypesForDataset(datasetKey)` | `getCsvTypeKeys(datasetKey)` または `collectTypesForDataset(datasetKey)`（互換） |
| タブ順序制御 | `TYPE_ORDER` 定数 | `getCsvListSorted(datasetKey)` の `.order` |
| 必須CSV判定 | `requiredTypesForDataset()` | `getRequiredCsvTypes(datasetKey)` |

---

## ✅ 受け入れ条件の確認

- [x] 既存ページでデータセット切替時、タブ順・ラベル・色が config に一致
- [x] 必須CSVの進捗表示が config.required に基づいて正しくカウント
- [x] 検証の必須ヘッダが config に基づいて照合
- [x] Upload 先が config.upload.path を参照
- [x] 型エラー 0
- [x] `pnpm typecheck` 成功
- [x] `pnpm build` 成功

---

## 📝 TODO（今後の作業）

### 1. 旧定義の削除候補
以下のファイル/定義は deprecated としてマークされており、移行後に削除可能:

- ❌ **削除候補（まだ削除しない）**:
  - `src/features/database/dataset-import/model/constants.ts` - UPLOAD_CSV_DEFINITIONS / UPLOAD_CSV_TYPES
  - `src/features/database/shared/ui/colors.ts` - CSV_TYPE_COLORS（動的生成版は残す）
  - `src/features/database/shared/dataset/dataset.ts` - collectTypesForDataset等の互換実装
  - `src/features/database/dataset-validate/model/rules.ts` - DATASET_RULES

- ⚠️ **段階的削除の手順**:
  1. 全参照箇所が config を直接使用していることを確認
  2. 1-2ヶ月の移行期間を設けて deprecated 警告を運用
  3. 問題がなければ削除PR作成

### 2. 将来の拡張ポイント

#### マニフェストの詳細定義の穴埋め
- 現在は仮のヘッダ定義（'交付日', '排出事業者', '廃棄物種類'）を使用
- 実際のマニフェストCSVフォーマットに基づいて正確なヘッダを定義
- 1次・2次の違いを明確にする

#### ファイル名推定の正規表現追加
- 現在は `filenameHints` による部分一致のみ
- より厳密な判定が必要な場合は `filenameRegex` を追加
- 例: `filenameRegex: "^(受入|receive).*\\.csv$"`

#### D&D自動割当機能の実装
- `SimpleUploadPanel` / `DragDropCsv` で `guessCsvTypeByFilename()` を使用
- ドロップ時にファイル名から自動的にCSV種別を判定して割り当て
- 判定できない場合は未割当として通知

#### 行バリデータの実装
- `csv.validate.rowSchemaName` に基づいた行単位のバリデーション
- `dataset-validate/adapters` 側にレジストリを作成
- 例: `ROW_SCHEMAS['row_shogun_receive_v1'] = (row) => { ... }`

#### プレビュー設定の活用
- `csv.preview.columnWidth` をCsvPreviewCardに渡す
- `csv.preview.stickyHeader` でヘッダー固定を制御
- データセット/CSV種別ごとに最適な表示設定

#### アップロード設定の詳細化
- `upload.payloadShape` を使った送信形式の切り替え
- `upload.maxFiles` による同時アップロード数制限
- データセットごとに異なるエンドポイントへの対応

---

## 🎯 成果

### 保守性の向上
- データセット定義が1箇所（config/datasets.ts）に集約
- 新規データセット追加時の変更箇所が明確
- 定義の漏れや不整合を防止

### 拡張性の向上
- CSV種別の追加が容易（datasets.ts に追加するのみ）
- データセット固有の設定を柔軟に追加可能
- 将来的な機能拡張（D&D自動割当、行バリデーション等）の基盤が整備

### 型安全性の向上
- `DatasetKey` / `CsvTypeKey` による厳密な型付け
- セレクタ関数による型安全なアクセス
- `as const` + `Readonly` で実行時の書き換えを防止

### 後方互換性の維持
- 既存コードは引き続き動作（旧関数は内部でconfigを参照）
- 段階的な移行が可能
- deprecated マーカーで移行を促進

---

## 📦 ファイル変更統計

- **新規作成**: 4ファイル
- **更新**: 10ファイル
- **削除**: 0ファイル（deprecatedマーク付与のみ）

---

## 🔍 検証結果

- **型チェック**: ✅ エラー 0
- **ビルド**: ✅ 成功（10.46s）
- **機能**: ✅ 既存機能への影響なし
