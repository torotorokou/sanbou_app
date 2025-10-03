# widgets/

## 役割
複数のページで再利用される大きめのUIコンポーネント（ウィジェット）を管理するレイヤー

## 配置するもの
- **複合UIコンポーネント**: ヘッダー、サイドバー、フッターなど
- **ページ横断の機能ブロック**: ダッシュボードウィジェット、通知パネルなど
- **レイアウトコンポーネント**: ページレイアウト、セクションレイアウトなど

## 依存関係
- ✅ features, entities, shared に依存可能
- ❌ app, pages, 他の widgets に依存不可

## 例
```
widgets/
├── header/
│   ├── Header.tsx
│   ├── UserMenu.tsx
│   └── index.ts
├── sidebar/
│   ├── Sidebar.tsx
│   ├── Navigation.tsx
│   └── index.ts
├── footer/
│   ├── Footer.tsx
│   └── index.ts
└── notification-panel/
    ├── NotificationPanel.tsx
    ├── NotificationList.tsx
    └── index.ts
```

## widgets と features の違い
- **widgets**: ページ横断で使われる「UI構成要素」（見た目・レイアウト重視）
- **features**: ビジネス機能の「機能単位」（ドメインロジック重視）
