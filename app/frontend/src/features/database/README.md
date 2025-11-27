# Database Feature

## 概要
CSVデータのアップロード・検証・プレビュー機能を提供

## 責務
- CSVファイルのアップロード
- CSVデータの検証とプレビュー
- データベースへの登録
- アップロード状態の管理

## 構造

### 現在の配置
```
src/
├── components/
│   ├── database/              # Database UI Components
│   │   ├── CsvUploadPanel.tsx
│   │   ├── CsvPreviewCard.tsx
│   │   └── UploadInstructions.tsx
│   └── common/csv-upload/     # 汎用CSVコンポーネント
│       ├── CsvUploadCard.tsx
│       └── CsvUploadPanel.tsx
├── hooks/database/            # Business Logic
│   ├── useCsvUploadHandler.ts
│   └── useCsvUploadArea.ts
├── pages/database/            # ページコンポーネント
│   ├── UploadDatabasePage.tsx
│   └── RecordListPage.tsx
└── shared/utils/              # 共有ユーティリティ
    ├── csv/csvPreview.ts
    └── validators/csvValidator.ts
```

## 主要コンポーネント

### UI Components

#### CsvUploadPanel
- **役割**: CSVアップロードエリアの表示
- **パス**: `@/components/database/CsvUploadPanel.tsx`
- **機能**: ドラッグ&ドロップ、ファイル選択、プレビュー

#### CsvPreviewCard
- **役割**: アップロードしたCSVのプレビュー表示
- **パス**: `@/components/database/CsvPreviewCard.tsx`
- **機能**: データ検証結果表示、エラー表示

#### CsvUploadCard
- **役割**: 単一CSV用アップロードカード
- **パス**: `@/components/common/csv-upload/CsvUploadCard.tsx`

### Business Logic Hooks

#### useCsvUploadHandler
- **役割**: CSVアップロード処理
- **パス**: `@/hooks/database/useCsvUploadHandler.ts`
- **機能**:
  - ファイルアップロードAPI呼び出し
  - 成功/エラー通知
  - ローディング状態管理

#### useCsvUploadArea
- **役割**: 複数CSVの状態管理
- **パス**: `@/hooks/database/useCsvUploadArea.ts`
- **機能**:
  - ファイル選択状態
  - CSV種別判定
  - プレビューデータ生成

## CSV種別 (CsvType)

### サポートCSV
```typescript
type CsvType =
  | 'customer'        // 顧客マスタ
  | 'sales'           // 売上データ
  | 'product'         // 製品マスタ
  | 'factory';        // 工場データ
```

### CSV定義
- **パス**: `@/constants/uploadCsvConfig.ts`
- **内容**:
  - 必須カラム定義
  - バリデーションルール
  - サンプルデータ

## 使用例

### 基本的な使い方
```typescript
import { useCsvUploadArea } from '@/hooks/database/useCsvUploadArea';
import { useCsvUploadHandler } from '@/hooks/database/useCsvUploadHandler';
import CsvUploadPanel from '@/components/database/CsvUploadPanel';

function MyUploadPage() {
  const uploadArea = useCsvUploadArea();
  const uploadHandler = useCsvUploadHandler();

  const handleUpload = async () => {
    await uploadHandler.handleUpload(uploadArea.files);
  };

  return (
    <CsvUploadPanel
      files={uploadArea.files}
      onFileChange={uploadArea.handleFileChange}
      onUpload={handleUpload}
      uploading={uploadHandler.uploading}
    />
  );
}
```

### CSVアップロードフロー
1. **ファイル選択** → ドラッグ&ドロップまたはファイル選択
2. **種別判定** → CSVヘッダーから自動判定
3. **プレビュー** → 先頭行をプレビュー表示
4. **検証** → 必須カラム・データ型チェック
5. **アップロード** → バックエンドAPIに送信
6. **完了通知** → 成功/エラーメッセージ表示

## 依存関係

### 内部依存
- `@shared/utils/csv/csvPreview` - CSVプレビュー生成
- `@shared/utils/validators/csvValidator` - CSV検証
- `@features/notification` - 通知表示

### 外部依存
- `antd` - UIコンポーネント (Upload, Table)
- `papaparse` - CSVパース

## API仕様

### CSVアップロードAPI
```
POST /sql_api/upload/syogun_csv
Content-Type: multipart/form-data

Body:
  - customer_csv: File (optional)
  - sales_csv: File (optional)
  - product_csv: File (optional)
  - factory_csv: File (optional)

Response:
{
  "status": "success",
  "detail": "アップロード完了"
}

Error Response:
{
  "status": "error",
  "detail": "エラーメッセージ"
}
```

## CSV検証ルール

### 共通ルール
- ヘッダー行必須
- UTF-8エンコーディング
- カンマ区切り

### 個別ルール (例: customer_csv)
```typescript
{
  requiredColumns: ['customer_id', 'customer_name'],
  columnTypes: {
    customer_id: 'string',
    customer_name: 'string',
    sales_amount: 'number'
  }
}
```

## エラーハンドリング

### エラー種別
1. **ファイル形式エラー**: CSV以外のファイル
2. **ヘッダーエラー**: 必須カラム不足
3. **データ型エラー**: 数値/日付の形式不正
4. **サーバーエラー**: API通信エラー

### 通知方法
- 成功: `notifySuccess()` - 緑色通知
- エラー: `notifyError()` - 赤色通知、詳細メッセージ

## 今後の改善点

### Phase 4 (将来)
- [ ] `features/database/` 配下への完全移行
- [ ] CSV検証ロジックの強化
- [ ] バッチアップロード対応
- [ ] アップロード履歴表示

### 技術的負債
- [ ] CSVパースの非同期処理最適化
- [ ] 大容量CSV対応 (ストリーム処理)
- [ ] プレビュー行数の動的調整
- [ ] エラーメッセージの多言語対応

## 関連ドキュメント
- `PHASE2_COMPLETION_REPORT.md` - Phase 2完了レポート
- `@/constants/uploadCsvConfig.ts` - CSV設定詳細
- `@shared/utils/validators/csvValidator.ts` - 検証ロジック

---

**最終更新**: 2025年10月3日  
**メンテナ**: Sanbou App Team
