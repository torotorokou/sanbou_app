# pages/

## 役割

ルート（URL）単位の画面を管理するレイヤー

## 配置するもの

- **ページコンポーネント**: 各URLに対応する画面の最上位コンポーネント
- **ページ固有のロジック**: そのページでしか使わない処理
- **レイアウト構成**: widgets と features を組み合わせてページを構成

## 依存関係

- ✅ widgets, features, entities, shared に依存可能
- ❌ app, 他の pages に依存不可
- ❌ 他のレイヤーから依存されない

## 例

```
pages/
├── dashboard/
│   ├── DashboardPage.tsx
│   └── index.ts
├── report/
│   ├── ReportListPage.tsx
│   ├── ReportDetailPage.tsx
│   └── index.ts
├── manual/
│   ├── ManualPage.tsx
│   └── index.ts
└── home/
    ├── HomePage.tsx
    └── index.ts
```

## ページの責務

- URLルートと1:1で対応
- widgets と features を組み合わせてページを構築
- ページレベルのデータフェッチング（必要に応じて）
- ページ固有の状態管理
