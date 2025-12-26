# features/

## 役割

ビジネス機能を縦割りで管理するレイヤー（通知、帳簿、レポート、マニュアルなど）

## 配置するもの

各機能ごとに以下を含むディレクトリを作成:

- **model/**: ビジネスロジック、状態管理（store）、データフェッチング
- **ui/**: 機能固有のUIコンポーネント（view）
- **api/**: API通信ロジック（controller的役割）
- **types/**: 機能固有の型定義
- **hooks/**: 機能固有のカスタムフック
- **lib/**: 機能固有のユーティリティ

## 依存関係

- ✅ entities, shared に依存可能
- ❌ app, pages, widgets, 他の features に依存不可
- ⚠️ 他の features との連携は shared 層を介して行う

## 例

```
features/
├── notification/
│   ├── model/
│   │   ├── notificationStore.ts
│   │   └── notificationService.ts
│   ├── ui/
│   │   ├── NotificationContainer.tsx
│   │   └── NotificationItem.tsx
│   ├── api/
│   │   └── notificationApi.ts
│   └── index.ts
├── ledger/
│   ├── model/
│   │   ├── ledgerStore.ts
│   │   └── ledgerLogic.ts
│   ├── ui/
│   │   ├── LedgerTable.tsx
│   │   └── LedgerForm.tsx
│   ├── api/
│   │   └── ledgerApi.ts
│   └── index.ts
├── report/
│   ├── model/
│   │   ├── reportStore.ts
│   │   └── reportCalculation.ts
│   ├── ui/
│   │   ├── ReportChart.tsx
│   │   └── ReportSummary.tsx
│   ├── api/
│   │   └── reportApi.ts
│   └── index.ts
└── manual/
    ├── model/
    │   └── manualStore.ts
    ├── ui/
    │   ├── ManualViewer.tsx
    │   └── ManualSearch.tsx
    ├── api/
    │   └── manualApi.ts
    └── index.ts
```

## MVC的な構造

- **Model**: `model/` ディレクトリ（ビジネスロジック、状態管理）
- **View**: `ui/` ディレクトリ（UIコンポーネント）
- **Controller**: `api/` + `model/` ディレクトリ（API通信、データ処理）
