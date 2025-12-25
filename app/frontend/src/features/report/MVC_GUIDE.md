# Report Feature - MVC Architecture

## 📁 ディレクトリ構造

```
features/report/
├── api/                    # API Layer - HTTP通信の抽象化
│   ├── index.ts           # APIエクスポート
│   └── reportApi.ts       # レポートAPI呼び出し (coreApi使用)
│
├── model/                 # Model + Controller Layer
│   ├── config/           # 設定・定数
│   │   ├── index.ts
│   │   ├── pages/        # ページ別設定
│   │   └── shared/       # 共通設定・型
│   │
│   ├── index.ts          # Modelエクスポート
│   ├── report.types.ts   # 型定義
│   ├── report-api.types.ts  # API型定義
│   │
│   └── use*.ts           # Controller Hooks (UIロジック)
│       ├── useReportManager.ts       # メインController
│       ├── useReportBaseBusiness.ts  # ビジネスロジック
│       ├── useReportActions.ts       # アクション処理
│       ├── useReportArtifact.ts      # アーティファクト管理
│       └── useReportLayoutStyles.ts  # スタイルロジック
│
└── ui/                   # View Layer - UIコンポーネント
    ├── common/           # 共通コンポーネント
    ├── interactive/      # インタラクティブ帳簿
    ├── viewer/           # ビューワー
    └── ReportBase.tsx    # メインコンポーネント
```

## 🎯 MVC + SOLID 原則

### API Layer (HTTP通信)

- **責務**: HTTP通信の抽象化
- **場所**: `api/reportApi.ts`
- **使用**: `coreApi` クライアント経由で `/core_api/...` にリクエスト

```typescript
import { generateFactoryReport } from "@features/report/api";

const result = await generateFactoryReport("2025-01-15");
```

### Model Layer (データ・型・設定)

- **責務**: データ構造、型定義、設定・定数
- **場所**:
  - `model/report.types.ts` - 型定義
  - `model/report-api.types.ts` - API型定義
  - `model/config/` - 設定・定数

```typescript
import type { ReportBaseProps, ReportKey } from "@features/report";
import { REPORT_API_ENDPOINTS } from "@features/report";
```

### Controller Layer (Hooks)

- **責務**: UIロジック、状態管理、副作用
- **場所**: `model/use*.ts`
- **原則**: UIから分離、再利用可能

```typescript
import { useReportManager, useReportBaseBusiness } from "@features/report";

const { currentReport, csvFiles, setCurrentReport } =
  useReportManager(reportKey);
const { makeUploadProps, artifact } = useReportBaseBusiness(/*...*/);
```

### View Layer (UIコンポーネント)

- **責務**: 表示のみ、イベントハンドラー
- **場所**: `ui/`
- **原則**: ビジネスロジックを持たない、Controller Hooksに依存

```typescript
import { ReportBase, ReportHeader } from '@features/report';

<ReportBase reportKey="factory_report" csvFiles={csvFiles} {...props} />
```

## 🔄 データフロー

```
User Action (View)
    ↓
Controller Hook (useReportManager)
    ↓
API Layer (reportApi)
    ↓
HTTP Client (coreApi) → /core_api/... → core_api(BFF) → ledger_api
    ↓
Response
    ↓
Controller Hook (state update)
    ↓
View (re-render)
```

## ✅ 設計ルール

1. **単一責任の原則 (SRP)**

   - API層: HTTP通信のみ
   - Model層: データ・型・設定のみ
   - Controller層: UIロジック・状態管理のみ
   - View層: 表示・イベントハンドリングのみ

2. **依存性逆転の原則 (DIP)**

   - Viewは Controllerに依存
   - ControllerはAPI層に依存
   - 直接fetchは禁止

3. **開放閉鎖の原則 (OCP)**

   - 新しいレポートタイプは設定追加のみ
   - 既存コードの変更を最小化

4. **インターフェース分離の原則 (ISP)**
   - 各Hooksは明確な責務を持つ
   - 不要な依存を持たない

## 📝 使用例

### 基本的な使い方

```typescript
import { ReportBase, useReportManager } from '@features/report';

const MyReportPage = () => {
  const reportKey = 'factory_report';
  const { csvFiles, setCurrentReport } = useReportManager(reportKey);

  return (
    <ReportBase
      reportKey={reportKey}
      csvFiles={csvFiles}
      onUploadFile={(label, file) => {/* ... */}}
    />
  );
};
```

### API直接呼び出し

```typescript
import { generateFactoryReport } from "@features/report/api";

const handleGenerate = async () => {
  try {
    const result = await generateFactoryReport("2025-01-15", "factory_01");
    console.log("Excel URL:", result.artifact?.excel_download_url);
  } catch (error) {
    console.error("Failed:", error);
  }
};
```

## 🚫 アンチパターン

### ❌ 避けるべきこと

```typescript
// ❌ UI内で直接fetch
const MyComponent = () => {
  const handleClick = async () => {
    const res = await fetch("/core_api/reports/..."); // 禁止！
  };
};

// ❌ ビジネスロジックをUI内に記述
const MyComponent = () => {
  const [data, setData] = useState();
  useEffect(() => {
    // 複雑な計算やAPI呼び出し... // 禁止！
  }, []);
};
```

### ✅ 正しいパターン

```typescript
// ✅ Controller Hookを使用
const MyComponent = () => {
  const { data, handleGenerate } = useReportManager('factory_report');

  return <button onClick={handleGenerate}>Generate</button>;
};

// ✅ API層を使用
import { generateFactoryReport } from '@features/report/api';

const useMyHook = () => {
  const generate = async () => {
    return await generateFactoryReport('2025-01-15');
  };
  return { generate };
};
```

## 🔧 メンテナンスガイド

### 新しいレポートタイプの追加

1. `model/config/` に設定を追加
2. `api/reportApi.ts` にAPI関数を追加
3. 必要に応じてController Hookを拡張
4. UIコンポーネントは既存のものを再利用

### 既存機能の修正

1. API変更 → `api/reportApi.ts`
2. 型変更 → `model/report.types.ts`
3. UIロジック変更 → `model/use*.ts`
4. 表示変更 → `ui/`

## 📚 関連ドキュメント

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 詳細なアーキテクチャ
- [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) - リファクタリング履歴
